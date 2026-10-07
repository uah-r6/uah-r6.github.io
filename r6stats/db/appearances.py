"""Global substitute capability and immutable historical map participation."""
from datetime import date


def migrate(db):
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='appearance_schema_version'").fetchone():
        return
    db.execute('BEGIN IMMEDIATE')
    try:
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='appearance_schema_version'").fetchone():
            db.rollback()
            return
        db.execute('ALTER TABLE players ADD COLUMN substitute_eligible INTEGER NOT NULL DEFAULT 0 CHECK(substitute_eligible IN (0,1))')
        db.execute('''CREATE TABLE map_player_appearances (
            map_id TEXT NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
            player_id INTEGER NOT NULL REFERENCES players(id),
            appearance_role TEXT NOT NULL CHECK(appearance_role IN ('roster','sub')),
            classified_on TEXT NOT NULL,
            regular_team_id INTEGER REFERENCES teams(id),
            PRIMARY KEY(map_id,player_id))''')
        # Original bound participants are the trusted historical import scope.
        db.execute('''INSERT INTO map_player_appearances
            SELECT DISTINCT m.id,rp.player_id,'roster',COALESCE(m.played_on,s.date),m.team_id
            FROM maps m JOIN series s ON s.id=m.series_id JOIN rounds r ON r.map_id=m.id
            JOIN round_players rp ON rp.round_id=r.id WHERE rp.player_id IS NOT NULL''')
        db.execute('''CREATE TRIGGER appearance_immutable BEFORE UPDATE ON map_player_appearances
            BEGIN SELECT RAISE(ABORT,'Historical appearance roles are immutable'); END''')
        db.execute('CREATE TABLE appearance_schema_version(version INTEGER NOT NULL)')
        db.execute('INSERT INTO appearance_schema_version VALUES(1)')
        db.commit()
    except Exception:
        db.rollback()
        raise


def classify(db, player, team_id, on):
    date.fromisoformat(on)
    memberships = db.execute('''SELECT team_id FROM team_memberships WHERE player_id=?
        AND start_date<=? AND (end_date IS NULL OR end_date>?)''', (player['id'], on, on)).fetchall()
    if len(memberships) > 1:
        raise ValueError(f"Membership conflict for {player['display_name']} on {on}.")
    regular_team_id = memberships[0][0] if memberships else None
    if regular_team_id == team_id:
        role = 'roster'
    elif player['substitute_eligible']:
        # Alumni is not silently reactivated; explicit eligibility is independent.
        role = 'sub'
    else:
        raise ValueError(f"Player {player['display_name']} belongs to another team or has no regular roster on {on} and is not substitute eligible. Enable global substitute eligibility or review dated membership before import.")
    return {'player_id': player['id'], 'appearance_role': role,
            'classified_on': on, 'regular_team_id': regular_team_id}


def participants(db, match, team_id, side):
    from r6stats.db.repository import identity_match
    found = {}
    sides = {}
    for round_ in match.rounds:
        round_ids = set()
        for p in round_.players:
            identity = identity_match(db, p)
            if not identity:
                continue  # Unconfigured participants remain untracked.
            if identity['id'] in round_ids:
                raise ValueError(f'Duplicate configured player identity in round {round_.number}: {p.username}. Review aliases.')
            round_ids.add(identity['id'])
            previous = sides.setdefault(identity['id'], p.team)
            if previous != p.team:
                raise ValueError(f"Tracked player {p.username} changed teams across replay rounds.")
            if p.team == side:
                found[identity['id']] = classify(db, identity, team_id, match.timestamp[:10])
    if not found:
        raise ValueError('Selected team has no configured roster members or eligible substitutes.')
    return found


def describe(db, records):
    result = []
    for r in records:
        p = db.execute('SELECT display_name,slug FROM players WHERE id=?', (r['player_id'],)).fetchone()
        team = db.execute('SELECT name,slug FROM teams WHERE id=?', (r['regular_team_id'],)).fetchone()
        result.append({**dict(r), 'name': p['display_name'], 'slug': p['slug'],
                       'regular_team_name': team['name'] if team else None})
    return sorted(result, key=lambda p: p['name'])
