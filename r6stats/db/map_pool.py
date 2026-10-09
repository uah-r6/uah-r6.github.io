"""Explicit season-specific competitive pools; independent of replay support."""
from datetime import datetime, timezone

from r6stats.map_catalog import CATALOG

ORDERED_CATALOG = sorted(CATALOG, key=lambda m: m['name'])


def migrate(db):
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='map_pool_schema_version'").fetchone():
        return
    db.execute('BEGIN IMMEDIATE')
    try:
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='map_pool_schema_version'").fetchone():
            db.rollback()
            return
        db.execute('''CREATE TABLE map_pool_catalog (
            map_slug TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE,
            display_order INTEGER NOT NULL UNIQUE CHECK(display_order>=0))''')
        db.execute('''CREATE TABLE season_map_pool_config (
            season_id INTEGER PRIMARY KEY REFERENCES seasons(id) ON DELETE CASCADE,
            origin TEXT NOT NULL CHECK(origin IN ('preserved_visible_catalog_v1','admin_selection')),
            updated_at TEXT NOT NULL)''')
        db.execute('''CREATE TABLE season_map_pool (
            season_id INTEGER NOT NULL REFERENCES season_map_pool_config(season_id) ON DELETE CASCADE,
            map_slug TEXT NOT NULL REFERENCES map_pool_catalog(map_slug),
            PRIMARY KEY(season_id,map_slug))''')
        db.executemany('INSERT INTO map_pool_catalog VALUES(?,?,?)',
                       [(m['slug'], m['name'], i) for i, m in enumerate(ORDERED_CATALOG)])
        # Existing pages showed the full catalog. Preserve that visible set once,
        # not an inferred official competitive pool. New seasons are unconfigured.
        now = datetime.now(timezone.utc).isoformat()
        for season in db.execute('SELECT id FROM seasons').fetchall():
            db.execute('INSERT INTO season_map_pool_config VALUES(?,?,?)',
                       (season['id'], 'preserved_visible_catalog_v1', now))
            db.executemany('INSERT INTO season_map_pool VALUES(?,?)',
                           [(season['id'], m['slug']) for m in ORDERED_CATALOG])
        db.execute('CREATE TABLE map_pool_schema_version(version INTEGER NOT NULL)')
        db.execute('INSERT INTO map_pool_schema_version VALUES(1)')
        db.commit()
    except Exception:
        db.rollback()
        raise


def require_season(db, slug):
    season = db.execute('SELECT id,slug,name FROM seasons WHERE slug=?', (slug,)).fetchone()
    if not season:
        raise ValueError('Season not found.')
    return season


def load(db, slug):
    season = require_season(db, slug)
    config = db.execute('SELECT origin,updated_at FROM season_map_pool_config WHERE season_id=?', (season['id'],)).fetchone()
    members = [dict(r) for r in db.execute('''SELECT c.map_slug AS slug,c.name
        FROM season_map_pool p JOIN map_pool_catalog c ON c.map_slug=p.map_slug
        WHERE p.season_id=? ORDER BY c.display_order''', (season['id'],))]
    return {'season': season['slug'], 'season_name': season['name'],
            'configured': config is not None, 'maps': members,
            'origin': config['origin'] if config else None,
            'updated_at': config['updated_at'] if config else None}


def save(db, slug, map_slugs, confirm_empty=False):
    require_season(db, slug)
    if not isinstance(map_slugs, list) or any(not isinstance(s, str) for s in map_slugs):
        raise ValueError('Map pool must be a list of canonical map slugs.')
    if len(set(map_slugs)) != len(map_slugs):
        raise ValueError('Duplicate map in competitive pool.')
    if set(map_slugs) - {m['slug'] for m in CATALOG}:
        raise ValueError('Unknown map slug; choose a canonical map from the catalog.')
    if not map_slugs and confirm_empty is not True:
        raise ValueError('Confirm the empty competitive map pool before saving.')
    season = require_season(db, slug)
    with db:
        db.execute('''INSERT INTO season_map_pool_config VALUES(?,?,?)
            ON CONFLICT(season_id) DO UPDATE SET origin=excluded.origin,updated_at=excluded.updated_at''',
            (season['id'], 'admin_selection', datetime.now(timezone.utc).isoformat()))
        db.execute('DELETE FROM season_map_pool WHERE season_id=?', (season['id'],))
        db.executemany('INSERT INTO season_map_pool VALUES(?,?)',
                       [(season['id'], s) for s in map_slugs])
    return load(db, slug)


def public_pool(db, period, active_season):
    if period != 'career':
        selected = period
    elif active_season:
        selected = active_season
    else:
        row = db.execute('''SELECT s.slug FROM seasons s JOIN season_map_pool_config c ON c.season_id=s.id
            ORDER BY COALESCE(s.start_date,'') DESC,s.id DESC LIMIT 1''').fetchone()
        selected = row['slug'] if row else None
    if not selected:
        return {'season': None, 'season_name': None, 'configured': False, 'maps': []}
    pool = load(db, selected)
    # Origin, timestamps and local database IDs are admin-only.
    return {k: pool[k] for k in ('season', 'season_name', 'configured', 'maps')}
