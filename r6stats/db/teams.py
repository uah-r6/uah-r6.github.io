"""Organization metadata only. Replay sides (0/1) are not organization teams."""
import re
from datetime import date, datetime, timezone


def migrate(db):
    """One atomic, idempotent metadata migration; never rewrite replay rows."""
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='team_schema_version'").fetchone():
        return
    with db:
        db.execute('BEGIN IMMEDIATE')
        # Two first requests may both observe the old schema before either
        # acquires SQLite's write lock. Recheck after acquiring that lock.
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='team_schema_version'").fetchone():
            return
        db.execute("""CREATE TABLE teams(id INTEGER PRIMARY KEY, name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL, primary_color TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
            display_order INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL)""")
        db.execute("""CREATE TABLE team_slug_aliases(slug TEXT PRIMARY KEY,
            team_id INTEGER NOT NULL REFERENCES teams(id))""")
        db.execute("""CREATE TABLE team_memberships(id INTEGER PRIMARY KEY,
            player_id INTEGER NOT NULL REFERENCES players(id), team_id INTEGER NOT NULL REFERENCES teams(id),
            start_date TEXT NOT NULL, end_date TEXT, CHECK(end_date IS NULL OR end_date>start_date))""")
        db.execute("""CREATE TABLE team_seasons(team_id INTEGER NOT NULL REFERENCES teams(id),
            season_id INTEGER NOT NULL REFERENCES seasons(id), PRIMARY KEY(team_id,season_id))""")
        now = datetime.now(timezone.utc).isoformat()
        db.executemany("INSERT INTO teams(name,slug,primary_color,display_order,created_at) VALUES(?,?,?,?,?)",
                       [('UAH Blue', 'blue', '#0058A4', 0, now), ('UAH White', 'white', '#E6EDF5', 1, now)])
        db.execute("ALTER TABLE players ADD COLUMN status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active','Alumni'))")
        db.execute("UPDATE players SET status='Alumni' WHERE tracked=0")
        # SQLite cannot add a non-null default alongside REFERENCES. Seed once,
        # then enforce non-null ownership on all subsequent writes with triggers.
        for table in ('series', 'maps'):
            db.execute(f"ALTER TABLE {table} ADD COLUMN team_id INTEGER REFERENCES teams(id)")
            db.execute(f"UPDATE {table} SET team_id=1")
            for action in ('INSERT', 'UPDATE'):
                db.execute(f"""CREATE TRIGGER {table}_owner_{action.lower()} BEFORE {action} ON {table}
                    WHEN NEW.team_id IS NULL BEGIN SELECT RAISE(ABORT,'Explicit team ownership is required'); END""")
        db.execute("INSERT INTO team_seasons SELECT DISTINCT 1,season_id FROM series")
        # Include inactive historical identities without changing their tracking state.
        db.execute("""INSERT INTO team_memberships(player_id,team_id,start_date)
            SELECT p.id,1,COALESCE((SELECT MIN(COALESCE(m.played_on,s.date)) FROM round_players rp
            JOIN rounds r ON r.id=rp.round_id JOIN maps m ON m.id=r.map_id
            JOIN series s ON s.id=m.series_id WHERE rp.player_id=p.id),'0001-01-01') FROM players p""")
        db.execute("""CREATE TRIGGER map_team_immutable BEFORE UPDATE OF team_id ON maps
            WHEN NEW.team_id!=OLD.team_id BEGIN SELECT RAISE(ABORT,'Map team ownership is immutable'); END""")
        for action in ('INSERT', 'UPDATE'):
            db.execute(f"""CREATE TRIGGER map_series_scope_{action.lower()} BEFORE {action} ON maps
                WHEN NEW.team_id!=(SELECT team_id FROM series WHERE id=NEW.series_id)
                BEGIN SELECT RAISE(ABORT,'Map and series must belong to the same team'); END""")
        db.execute("""CREATE TRIGGER series_scope_immutable BEFORE UPDATE OF team_id,season_id ON series
            WHEN NEW.team_id!=OLD.team_id OR NEW.season_id!=OLD.season_id
            BEGIN SELECT RAISE(ABORT,'Series team and season ownership are immutable'); END""")
        db.execute("""CREATE TRIGGER membership_no_overlap BEFORE INSERT ON team_memberships
            WHEN EXISTS(SELECT 1 FROM team_memberships WHERE player_id=NEW.player_id
            AND start_date<COALESCE(NEW.end_date,'9999-12-31')
            AND NEW.start_date<COALESCE(end_date,'9999-12-31'))
            BEGIN SELECT RAISE(ABORT,'Player membership dates overlap'); END""")
        db.execute("""CREATE TRIGGER membership_edit_no_overlap BEFORE UPDATE ON team_memberships
            WHEN EXISTS(SELECT 1 FROM team_memberships WHERE player_id=NEW.player_id AND id!=OLD.id
            AND start_date<COALESCE(NEW.end_date,'9999-12-31')
            AND NEW.start_date<COALESCE(end_date,'9999-12-31'))
            BEGIN SELECT RAISE(ABORT,'Player membership dates overlap'); END""")
        db.execute("CREATE TABLE team_schema_version(version INTEGER NOT NULL)")
        db.execute("INSERT INTO team_schema_version VALUES(1)")


def require(db, team_id, *, active=False):
    if team_id is None:
        raise ValueError('Select an explicit team before continuing.')
    row = db.execute('SELECT * FROM teams WHERE id=?', (team_id,)).fetchone()
    if not row or (active and not row['active']):
        raise ValueError('Select an existing active team.')
    return row


def save(db, *, name, slug, primary_color, active=True, display_order=0, team_id=None):
    name, slug = name.strip(), slug.strip().lower()
    if not name or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
        raise ValueError('Team name and a URL slug containing letters, numbers and hyphens are required.')
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', primary_color):
        raise ValueError('Team color must be a six-digit hex color.')
    if db.execute('SELECT 1 FROM teams WHERE slug=? AND id!=?', (slug, team_id or -1)).fetchone() or db.execute(
            'SELECT 1 FROM team_slug_aliases WHERE slug=? AND team_id!=?', (slug, team_id or -1)).fetchone():
        raise ValueError('This team slug is already reserved.')
    with db:
        if team_id is None:
            return db.execute('INSERT INTO teams(name,slug,primary_color,active,display_order,created_at) VALUES(?,?,?,?,?,?)',
                              (name, slug, primary_color.upper(), int(active), display_order,
                               datetime.now(timezone.utc).isoformat())).lastrowid
        old = require(db, team_id)
        if old['slug'] != slug:
            db.execute('INSERT OR IGNORE INTO team_slug_aliases VALUES(?,?)', (old['slug'], team_id))
        db.execute('UPDATE teams SET name=?,slug=?,primary_color=?,active=?,display_order=? WHERE id=?',
                   (name, slug, primary_color.upper(), int(active), display_order, team_id))
    return team_id


def member(db, player_id, team_id, on=None):
    on = on or date.today().isoformat()
    return bool(db.execute('''SELECT 1 FROM team_memberships WHERE player_id=? AND team_id=?
        AND start_date<=? AND (end_date IS NULL OR end_date>?)''', (player_id, team_id, on, on)).fetchone())


def move(db, player_id, team_id, effective_date):
    require(db, team_id, active=True)
    date.fromisoformat(effective_date)
    if not db.execute('SELECT 1 FROM players WHERE id=?', (player_id,)).fetchone():
        raise ValueError('Player not found.')
    with db:
        old = db.execute('SELECT * FROM team_memberships WHERE player_id=? AND end_date IS NULL', (player_id,)).fetchone()
        if old:
            if old['team_id'] == team_id:
                raise ValueError('Player already belongs to this team.')
            if effective_date <= old['start_date']:
                raise ValueError('Move date must follow the current membership start date.')
            db.execute('UPDATE team_memberships SET end_date=? WHERE id=?', (effective_date, old['id']))
        db.execute('INSERT INTO team_memberships(player_id,team_id,start_date) VALUES(?,?,?)',
                   (player_id, team_id, effective_date))


def history(db, player_id):
    return [dict(r) for r in db.execute('''SELECT t.slug AS team_slug,t.name AS team_name,
        tm.team_id,tm.start_date,tm.end_date FROM team_memberships tm JOIN teams t ON t.id=tm.team_id
        WHERE tm.player_id=? ORDER BY tm.start_date''', (player_id,))]
