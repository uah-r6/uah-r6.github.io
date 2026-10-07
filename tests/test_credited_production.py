import hashlib
import json
from copy import deepcopy
from uuid import UUID

import pytest

from r6stats.credited_refresh import (LEGACY, aggregate_display, display_stats,
                                     load, round_counts, store, collect_after_import)
from r6stats.db import repository as repo
from r6stats.export import export
from r6stats.kill_credit import SOURCE, validate_map_credit
from r6stats.parser.models import Kill, Match, Objective, Player, Round
from r6stats.stats.calculate import COUNTS, calculate_match


def fixture():
    players = [Player(str(UUID(int=i+1)),f'p{i}',i//5,'Ace' if i<5 else 'Mute','Attack' if i<5 else 'Defense') for i in range(10)]
    rounds = []
    records = []
    for n in (1,2):
        # p1 finishes twice, p0 receives the two credits. p0 is eliminated;
        # its KOST Kill flag matters. Objective and trade components stay intact.
        kills = [Kill(0,90,players[1].key,players[5].key,0,1,True),
                 Kill(1,80,players[1].key,players[6].key,0,1),
                 Kill(2,70,players[7].key,players[0].key,1,0)]
        rounds.append(Round(n,'site',0,'DefuserExploded',deepcopy(players),kills,
                            [Objective('plant',players[2].key,0,40)]))
        report = dict(source=SOURCE,complete=True,players=[])
        for i,p in enumerate(players):
            k = 2 if i==0 else 1 if i==7 else 0
            report['players'].append(dict(uid=i+1,profileID=p.profile_id,username=p.username,team=p.team,
                initial=(n-1)*k,terminal=n*k,kills=k,reason=SOURCE))
        records.append(dict(logical_round=n,physical_round=n,segment='original',credit=report))
    return Match('credited-test','2026-10-06T00:00:00Z','Border','CustomGameOnline','Bomb',rounds), records


def test_whole_map_projection_changes_only_supported_counts_and_preserves_original_rating():
    match, records = fixture()
    before = match.to_dict()
    old = calculate_match(match)
    new = display_stats(match,validate_map_credit(records))
    assert match.to_dict() == before
    for key in old:
        for field in COUNTS:
            if field not in ('kills','multikill_extra','kost_rounds'):
                assert new[key][field] == old[key][field]
        assert new[key]['rating'] == old[key]['rating']
        assert new[key]['operators'] == old[key]['operators']
        assert new[key]['hs'] == old[key]['hs']
        assert new[key]['kill_source_rounds'] == {SOURCE:2}
    a,b = [p.key for p in match.rounds[0].players[:2]]
    assert new[a]['kills']==4 and new[a]['multikill_sizes']=={'2':2,'3':0,'4':0,'5':0}
    assert new[a]['kost_rounds']==2 and old[a]['kost_rounds']==0
    assert new[b]['kills']==0 and new[b]['finisher_kills']==4 and new[b]['hs']==0.5
    assert new[a]['sides']['Attack']['kills']==4


def test_mixed_map_aggregation_keeps_coverage_sizes_and_finisher_headshot_denominator():
    match,records=fixture();key=match.rounds[0].players[1].key
    credit=display_stats(match,validate_map_credit(records))[key]
    legacy=display_stats(match,None)[key]
    total=aggregate_display([credit,legacy],'siege_style_v2')
    assert total['kill_source']=='mixed_whole_map_sources'
    assert total['kill_source_rounds']=={SOURCE:2,LEGACY:2}
    assert total['kills']==4 and total['finisher_kills']==8 and total['headshots']==4 and total['hs']==0.5
    assert total['multikill_sizes']['2']==2


@pytest.mark.parametrize('mutation',['partial','profile','team','rounds'])
def test_refuse_partial_or_mismatched_normalized_evidence(mutation):
    match,records=fixture();credit=validate_map_credit(records)
    if mutation=='partial':credit['complete']=False
    elif mutation=='profile':match.rounds[0].players[0].profile_id=str(UUID(int=50))
    elif mutation=='team':match.rounds[0].players[0].team=1
    else:match.rounds.pop()
    with pytest.raises(ValueError):round_counts(match,credit)


def make_db(tmp_path):
    db=repo.connect(tmp_path/'db.sqlite')
    match,records=fixture()
    repo.season_create(db,'Fall 2026')
    for p in match.rounds[0].players[:5]:
        repo.roster_add(db,p.username,p.username, team_id=1)
    mid=repo.insert_map(db,match,'fingerprint',0,'Opponent','','', organization_team_id=1)
    return db,mid,match,records


def test_persistent_overlay_is_atomic_integrity_checked_and_cascades_only_on_map_delete(tmp_path):
    db,mid,match,records=make_db(tmp_path)
    old=tuple(db.execute('SELECT normalized_json FROM maps').fetchone())
    store(db,mid,records,'parser-sha')
    assert load(db,mid)['complete']
    assert tuple(db.execute('SELECT normalized_json FROM maps').fetchone())==old
    repo.reparse_map(db,mid,match,'fingerprint')
    assert load(db,mid)['complete']
    db.execute("UPDATE map_kill_credit SET evidence_json='[]'")
    with pytest.raises(ValueError,match='integrity'):load(db,mid)
    repo.match_delete(db,mid)
    assert db.execute('SELECT count(*) FROM map_kill_credit').fetchone()[0]==0
    assert db.execute('SELECT count(*) FROM players').fetchone()[0]==5


def test_export_preserves_rating_snapshots_objectives_and_public_identity_privacy(tmp_path):
    db,mid,match,records=make_db(tmp_path)
    payload=json.dumps(match.to_dict())
    db.execute('INSERT INTO rating_input_snapshots VALUES(?,?,?,?)',(mid,'siege_style_v2',payload,hashlib.sha256(payload.encode()).hexdigest()))
    db.commit()
    config={'team':{'name':'Team','short_name':'T','accent':'#000000'},'stats':{'rating_version':'siege_style_v2','trade_window_seconds':8}}
    root=tmp_path/'data';export(db,config,root)
    before=json.loads((root/'matches'/f'{mid}.json').read_text())
    store(db,mid,records,'parser-sha');export(db,config,root)
    after=json.loads((root/'matches'/f'{mid}.json').read_text())
    for a,b in zip(before['players'],after['players']):
        assert a['rating']==b['rating']
        assert a['plants']==b['plants'] and a['disables']==b['disables']
    assert after['players'][0]['kills']==4
    for path in root.rglob('*.json'):
        text=path.read_text()
        assert 'profile_id' not in text and 'counter_samples' not in text
    assert db.execute('SELECT source_sha256 FROM rating_input_snapshots').fetchone()[0]==hashlib.sha256(payload.encode()).hexdigest()


def test_incomplete_whole_map_stays_legacy_and_missing_reader_does_not_lose_import(tmp_path):
    db,mid,match,records=make_db(tmp_path)
    records[1]['credit']['complete']=False
    assert store(db,mid,records,'sha')['complete'] is False
    assert load(db,mid) is None
    assert display_stats(match,load(db,mid))==display_stats(match,None)
    assert db.execute('SELECT count(*) FROM maps').fetchone()[0]==1


def test_secondary_collection_failure_is_reported_without_deleting_valid_map(tmp_path,monkeypatch):
    db,mid,_,_=make_db(tmp_path)
    def fail(*args):raise ValueError('unsupported structure')
    monkeypatch.setattr('r6stats.credited_refresh.collect_archive',fail)
    result=collect_after_import(db,tmp_path,mid)
    assert result['source']==LEGACY and result['reason']=='unsupported structure'
    assert db.execute('SELECT count(*) FROM maps').fetchone()[0]==1
