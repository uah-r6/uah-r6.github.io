"""Seal browser-retrieved exact-profile history, independent of final stats."""
import json
from credited_late_history_development import immutable_write
from v3_cnl_metadata import DATA
from v3_final_reserve import ROOT,sha


def main():
    uid='db3adff9-afd1-4e16-a201-e9d044a4a799'
    path=DATA/f'apac1-identity-{uid}-browser.json';history=json.loads(path.read_text(encoding='utf-8'))
    if history['profile_id']!=uid or history['source_url'].rsplit('/',1)[1]!=uid or 'OKOMESH' not in history['history_names']:
        raise ValueError('Exact UUID history identity differs')
    meta=json.loads((DATA/'apac1-metadata-3810.json').read_text(encoding='utf-8'))
    persons=[p for p in meta['players'] if p['id']==2769 and p['ign']=='OKOMESH']
    if len(persons)!=1:raise ValueError('Independent exact public IGN binding differs')
    immutable_write(ROOT/'research/v3-native-final-apac1-extra-aliases.json',dict(scope='Only independent exact profile history; no Rating or K/D aliases',aliases={
        'OKOMESSH':dict(replay_profile_id=uid,siegegg_player_id=2769,independently_verified=True,name='OKOMESH',
            profile_history=history['source_url'],observed_names=[history['current_username']]+history['history_names'],
            primary_player_id=1465,primary_roster='https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/8144',
            independent_evidence_sha256=sha(path),evidence='The exact UUID browser history explicitly includes OKOMESSH and OKOMESH. Independent public metadata2769OKOMESH and primary participation1465OKOMESSH establish identity without spelling-distance or statistical inference.')}))
    print('OKOMESSH exact UUID history independently bound to public2769OKOMESH',flush=True)


if __name__=='__main__':main()
