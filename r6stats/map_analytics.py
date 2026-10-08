"""Team/period analytics from the same logical round projection published per map."""
from copy import deepcopy

from r6stats.map_catalog import CATALOG, identity


def counts():
    return {'rounds': 0, 'wins': 0, 'losses': 0}


def increment(record, won):
    record['rounds'] += 1
    record['wins' if won else 'losses'] += 1


def empty_map(metadata):
    return {**metadata, 'maps_played': 0, 'map_wins': 0, 'map_losses': 0,
            **counts(), 'attack': counts(), 'defense': counts(), 'unknown_side': counts(),
            'sites': {'Attack': [], 'Defense': [], 'Unknown': []}, 'matches': []}


def build_analytics(team_slug, period, period_name, matches):
    maps = {m['slug']: empty_map(m) for m in CATALOG}
    seen = {}
    site_counts = {}
    for match in matches:
        if match['team_slug'] != team_slug or (period != 'career' and match['season'] != period):
            raise ValueError('Map analytics ownership/period differs from its scope.')
        mid = match['id']
        if mid in seen:
            if seen[mid] != match:
                raise ValueError('Conflicting duplicate logical map in analytics.')
            continue
        seen[mid] = deepcopy(match)
        if match['result'] not in ('WIN', 'LOSS'):
            raise ValueError('Map analytics needs a recorded map result.')
        metadata = identity(match['map'])
        target = maps.setdefault(metadata['slug'], empty_map(metadata))
        target['maps_played'] += 1
        target['map_wins' if match['result'] == 'WIN' else 'map_losses'] += 1
        target['matches'].append({k: match[k] for k in (
            'id', 'series_id', 'season', 'team_slug', 'opponent', 'date',
            'map', 'our_score', 'their_score', 'result')})
        round_numbers = set()
        for round_ in match['rounds']:
            if round_['number'] in round_numbers:
                raise ValueError('Duplicate logical round in map analytics.')
            round_numbers.add(round_['number'])
            if round_['result'] not in ('Win', 'Loss'):
                raise ValueError('Map analytics needs a recorded round result.')
            won = round_['result'] == 'Win'
            increment(target, won)
            side = round_['side'] if round_['side'] in ('Attack', 'Defense') else 'Unknown'
            increment(target[{'Attack': 'attack', 'Defense': 'defense', 'Unknown': 'unknown_side'}[side]], won)
            raw_site = round_.get('site') or ''
            unknown = raw_site.strip().casefold() in ('', 'unknown', 'unknown site')
            # Unknown buckets retain the raw label; no site inferred from other fields.
            key = (metadata['slug'], side, raw_site)
            site = site_counts.setdefault(key, {'site': raw_site, 'unknown': unknown, **counts()})
            increment(site, won)
    for (map_slug, side, _), site in site_counts.items():
        maps[map_slug]['sites'][side].append(site)
    for map_ in maps.values():
        for sites in map_['sites'].values():
            sites.sort(key=lambda s: (-s['rounds'], -s['wins'] / s['rounds'], s['site']))
        map_['matches'].sort(key=lambda m: (m['date'], m['id']), reverse=True)
    return {'schema_version': 1, 'team_slug': team_slug, 'period': period,
            'period_name': period_name, 'catalog_source': 'tracker-supported replay maps',
            'maps': sorted(maps.values(), key=lambda m: (-m['maps_played'], m['name']))}
