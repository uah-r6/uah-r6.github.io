"""Read only identity diagnostics from cached new-final headers and primary metadata."""
import argparse
import json

from v3_apac1_pipeline import bind_person,DATA,identity_aliases
from v3_apac1_metadata import nextdata
from v3_cnl_metadata import DATA as METADATA
from v3_cnl_pipeline import candidate_raw,PARSER
from r6stats.parser.siege_dissect import normalize,physical_round_numbers
from v3_final_reserve import ROOT


def main():
    ap=argparse.ArgumentParser();ap.add_argument('official_match_id',type=int);ap.add_argument('siegegg_match_id',type=int);args=ap.parse_args()
    primary=nextdata((METADATA/f'apac1-primary-{args.official_match_id}.html').read_text(encoding='utf-8'))['match']
    people=[p|dict(team_id=t['id']) for g in primary['games'] if g['rounds'] for t in g['teams'] for p in t['players']]
    meta=json.loads((METADATA/f'apac1-metadata-{args.siegegg_match_id}.json').read_text(encoding='utf-8'))
    aliases=identity_aliases()
    folders={p.parent for p in (ROOT/'data/research/extracted'/f'v3-native-apac1-{args.official_match_id}').rglob('*.rec')}
    for folder in sorted(folders):
        raw=candidate_raw(folder,PARSER)['rounds']
        match=normalize(raw,round_numbers=physical_round_numbers(sorted(folder.glob('*.rec'))))
        for player in match.rounds[0].players:
            sp,pp,reason=bind_person(player,meta,people,aliases)
            print(json.dumps(dict(replay=player.username,profile_id=player.profile_id,
                public=(sp['id'],sp['ign']) if sp else None,primary=(pp['id'],pp['name']) if pp else None,reason=reason),ensure_ascii=True),flush=True)
    print('PUBLIC IDENTITIES',json.dumps([(p['id'],p['ign'],p['stylized_name']) for p in meta['players']],ensure_ascii=True))
    print('PRIMARY IDENTITIES',json.dumps([{k:v for k,v in p.items() if k!='stats'} for p in people],ensure_ascii=True))


if __name__=='__main__':main()
