"""Conservative audit of historical references before deleting an unused identity."""
import json

CONFIGURATION = {'aliases', 'team_memberships'}


def quoted(name):
    return '"' + name.replace('"', '""') + '"'


def audit(db, player_id):
    player = db.execute('SELECT * FROM players WHERE id=?', (player_id,)).fetchone()
    if not player:
        raise ValueError('Player not found.')
    names = {player['username'].strip().casefold()}
    names.update(r[0].strip().casefold() for r in db.execute('SELECT username FROM aliases WHERE player_id=?', (player_id,)))
    profile = player['profile_id']
    references = []
    tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    for table in tables:
        if table in CONFIGURATION or table == 'players':
            continue
        columns = {r['name'] for r in db.execute(f'PRAGMA table_info({quoted(table)})')}
        conditions, values = [], []
        for ref in db.execute(f'PRAGMA foreign_key_list({quoted(table)})'):
            if ref['table'] == 'players':
                conditions.append(f'{quoted(ref["from"])}=?')
                values.append(player[ref['to'] or 'id'])
        if 'player_id' in columns and '"player_id"=?' not in conditions:
            conditions.append('"player_id"=?'); values.append(player_id)
        if table == 'round_players':
            for name in sorted(names):
                conditions.append('username=? COLLATE NOCASE'); values.append(name)
            if profile:
                conditions.append('profile_id=?'); values.append(profile)
        if conditions:
            count = db.execute(f'SELECT count(*) FROM {quoted(table)} WHERE '+ ' OR '.join(conditions), values).fetchone()[0]
            if count:
                references.append(dict(table=table, count=count, kind='historical/reference'))
        # Whole-map raw/frozen evidence can retain identities without a direct
        # player FK. Exact usernames/profile IDs are evidence; display names are not.
        for column in sorted(columns & {'normalized_json', 'evidence_json', 'before_json', 'after_json'}):
            count = 0
            for row in db.execute(f'SELECT {quoted(column)} FROM {quoted(table)} WHERE {quoted(column)} IS NOT NULL'):
                try:
                    data = json.loads(row[0])
                except (ValueError, TypeError):
                    # Corrupted historical evidence cannot prove safe deletion.
                    references.append(dict(table=table, column=column, count=1, kind='unreadable historical evidence'))
                    break
                def contains(value):
                    if isinstance(value, dict):
                        if str(value.get('username', '')).strip().casefold() in names:
                            return True
                        if profile and (value.get('profile_id') == profile or value.get('profileID') == profile):
                            return True
                        return any(contains(v) for v in value.values())
                    return isinstance(value, list) and any(contains(v) for v in value)
                count += int(contains(data))
            if count:
                references.append(dict(table=table, column=column, count=count, kind='serialized historical identity'))
    return dict(player_id=player_id, username=player['username'], can_delete=not references,
        references=references, aliases=db.execute('SELECT count(*) FROM aliases WHERE player_id=?', (player_id,)).fetchone()[0],
        memberships=db.execute('SELECT count(*) FROM team_memberships WHERE player_id=?', (player_id,)).fetchone()[0],
        message='No imported match history; aliases and memberships can be removed with this mistaken identity.' if not references else
        'This player cannot be permanently deleted because they appear in imported match history or retained historical evidence. Use "Remove from roster" or "Mark Alumni" instead.')
