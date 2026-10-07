"""Additive public series projections; frozen map inputs remain authoritative."""
from collections import defaultdict

from r6stats.credited_refresh import aggregate_display
from r6stats.manual_kd import apply_display_kd
from r6stats.stats.calculate import aggregate


def player_total(records, version):
    """Each record is one logical played map, already bound to an internal ID."""
    if len({r['map_id'] for r in records}) != len(records):
        raise ValueError('Duplicate logical map in series player inputs.')
    display_version = 'siege_style_v2' if version == 'siege_style_v3' else version
    shown = aggregate_display([r['display'] for r in records], display_version)
    shown = apply_display_kd(shown, shown['kills'] + sum(r['delta'][0] for r in records),
                             shown['deaths'] + sum(r['delta'][1] for r in records))
    eligible = [r['rating'] for r in records if r['rating'] is not None and version == 'siege_style_v3']
    # Re-evaluate the existing model on additive trusted counts, never average
    # rounded/displayed map Ratings. Null is a real eligibility abstention.
    shown.update(rating=aggregate(eligible, 'siege_style_v3')['rating'] if eligible else None,
                 rating_maps=len(eligible), rating_rounds=sum(r['rounds'] for r in eligible))
    return shown


class SeriesProjection:
    def __init__(self, version):
        self.version = version
        self.metadata = {}
        self.maps = defaultdict(list)
        self.inputs = defaultdict(lambda: defaultdict(list))

    def add(self, metadata, public_map, participants):
        sid = metadata['id']
        if sid in self.metadata and self.metadata[sid] != metadata:
            raise ValueError('Series metadata differs across logical maps.')
        if any(public_map[k] != metadata[k] for k in ('series_id', 'team_slug', 'team_name', 'season', 'opponent', 'week', 'notes')):
            raise ValueError('Series team/season/opponent metadata differs.')
        if any(m['id'] == public_map['id'] for m in self.maps[sid]):
            raise ValueError('Duplicate logical series map.')
        self.metadata[sid] = metadata
        self.maps[sid].append(public_map)
        for player_id, record in participants.items():
            self.inputs[sid][player_id].append(record)

    def documents(self, identities):
        documents = []
        for sid, metadata in self.metadata.items():
            maps = self.maps[sid]
            players = [{**identities[player_id], **player_total(records, self.version)}
                       for player_id, records in self.inputs[sid].items()]
            players.sort(key=lambda p: p['rating'] if p['rating'] is not None else -float('inf'), reverse=True)
            documents.append({**metadata, 'rating_version': self.version, 'maps': maps,
                              'rounds': sum(m['our_score'] + m['their_score'] for m in maps),
                              'recorded_maps': {'count': len(maps),
                                                'wins': sum(m['result'] == 'WIN' for m in maps),
                                                'losses': sum(m['result'] == 'LOSS' for m in maps)},
                              'players': players})
        return documents


def player_series(document, player):
    """Small, public-only player-specific series history for season/career charts."""
    return {**{k: document[k] for k in ('id', 'series_id', 'team_slug', 'team_name', 'season',
                                      'season_name', 'opponent', 'date', 'recorded_maps', 'rating_version')},
            **{k: player[k] for k in ('rating', 'rating_maps', 'rating_rounds', 'maps', 'rounds')}}
