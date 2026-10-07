from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from v3_cnl_pipeline import stitch,canonical_map
from test_verified_objective_actor_adapter import raw_round


def item(n,start,end,flip=False):
    raw=raw_round();raw['objectiveOccurrences']=[]
    for i,t in enumerate(raw['teams']):
        j=1-i if flip else i
        t.update(startingScore=start[j],score=end[j],won=end[j]>start[j])
    if flip:
        for p in raw['players']:p['teamIndex']=1-p['teamIndex']
    return dict(folder='Match-second' if flip else 'Match-first',filename=f'R{n:02d}.rec',physical_round=n,raw=raw)


def test_complete_rehost_keeps_explicit_score_and_player_groups_with_flipped_teams():
    physical=[item(1,(0,0),(1,0)),item(2,(1,0),(1,1)),item(1,(1,1),(2,1),True)]
    match,mapping,excluded,groups,score=stitch(physical,'Villa')
    assert score==(2,1) and not excluded
    assert [r.number for r in match.rounds]==[1,2,3]
    assert [m['physical_round'] for m in mapping]==[1,2,1]
    assert {p.username:p.team for p in match.rounds[0].players}=={p.username:p.team for p in match.rounds[2].players}


def test_only_explicit_zero_score_attempt_is_excluded_without_filling_gaps():
    physical=[item(1,(0,0),(1,0)),item(2,(1,0),(1,0)),item(3,(1,0),(2,0))]
    match,mapping,excluded,_,_=stitch(physical,'Villa')
    assert len(match.rounds)==2 and len(excluded)==1 and excluded[0]['physical_round']==2
    bad=deepcopy(physical);bad[2]['raw']['teams'][0]['startingScore']=0
    with pytest.raises(ValueError,match='discontinuous'):stitch(bad,'Villa')


def test_changed_or_missing_participation_never_stitches():
    physical=[item(1,(0,0),(1,0)),item(2,(1,0),(2,0))]
    physical[1]['raw']['players'][0]['username']='different'
    with pytest.raises(ValueError,match='Roster differs'):stitch(physical,'Villa')


def test_independent_map_labels_are_canonicalized_without_fuzzy_identity():
    assert canonical_map('Club House')==canonical_map('Clubhouse')
    assert canonical_map('Kafe Dostoyevsky')==canonical_map('Kafe')
