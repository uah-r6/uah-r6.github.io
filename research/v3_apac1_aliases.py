"""Reuse sealed independently bound profile identities, never new final Ratings."""
import json

from credited_late_history_development import immutable_write
from v3_cnl_metadata import DATA
from v3_credited_derive import map_inputs
from v3_final_reserve import ROOT,sha


def main():
    wanted={'7c0e21d8-7463-4d65-9ce9-fcdf0b9fbc47':('Demic164',1139,'Demic'),
        '2c7fa52d-19c2-4a50-aa9e-0d8f524ace77':('Nina666.SCARZ',3072,'Nina')}
    evidence={uid:[] for uid in wanted}
    for m in map_inputs():
        for player in m['match'].rounds[0].players:
            if player.profile_id not in wanted:continue
            username,pid,name=wanted[player.profile_id]
            bound=[r for r in m['rows'] if r['player']==player.username and r['player_id']==pid]
            if len(bound)!=1:raise ValueError('Historical independently bound identity differs')
            if player.username.split('.')[0].casefold()!=name.casefold():continue
            api_paths=[ROOT/p for p in m['inputs'] if p.endswith('siegegg-api-sealed.json')]
            if len(api_paths)!=1:raise ValueError('Require sealed independent metadata API')
            meta=json.loads(api_paths[0].read_text(encoding='utf-8'))
            persons=[p for p in meta['players'] if p['id']==pid and name.casefold() in {p['ign'].casefold(),p['stylized_name'].casefold()}]
            if len(persons)!=1:raise ValueError('Historical exact IGN/ID identity differs')
            evidence[player.profile_id].append(dict(map=m['key'],username=player.username,profile_id=player.profile_id,
                siegegg_player_id=pid,independent_metadata_sha256=sha(api_paths[0]),independent_metadata_path=api_paths[0].relative_to(ROOT).as_posix(),
                sealed_source_inputs=m['inputs']))
    if any(not entries for entries in evidence.values()):raise ValueError('Missing independent exact profile binding')
    private=DATA/'apac1-independent-profile-bindings.json';immutable_write(private,evidence)
    aliases={}
    for uid,(username,pid,name) in wanted.items():
        aliases[username]=dict(replay_profile_id=uid,siegegg_player_id=pid,independently_verified=True,name=name,
            observed_names=sorted({e['username'] for e in evidence[uid]}|{username}),independent_evidence_sha256=sha(private),
            evidence='Exact same nonnil Ubisoft profile ID was independently bound by exact IGN and public player ID in sealed older APACStage2 metadata/header records. No digit stripping, K/D selection or remaining-player inference.',
            profile_history='https://stats.cc/siege/'+username+'/'+uid,
            retrieval_limit='StatsCC direct HTTP403; Demic browser history corroborates Demic.TMT/Demic164. Binding above relies on sealed exact profile/metadata evidence, not an unrecorded HTTP page.')
    record=dict(scope='Previously sealed independent nonnil profile/IGN bindings plus current primary participation, no outcome or Rating alias selection',aliases=aliases)
    immutable_write(ROOT/'research/v3-native-final-apac1-aliases.json',record)
    print('Demic164 and Nina666 exact existing profile bindings independently sealed',flush=True)


if __name__=='__main__':main()
