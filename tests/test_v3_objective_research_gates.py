"""Research split/missing-data gates prevent final leakage and invented zeros."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from v3_objective_fit import development_groups


def test_missing_actor_map_never_enters_development_as_zero():
    rows=[dict(event='train',reserved_for_final_test=False,fit_eligible=True,objective_map_complete=False)]
    with pytest.raises(ValueError,match='Missing objective actors'):
        development_groups(rows,dict(train_events=['train'],development_event='dev'))


@pytest.mark.parametrize('event,reserved',[('final',False),('train',True),('dev',True)])
def test_final_events_and_reserved_rows_are_rejected_before_fit(event,reserved):
    rows=[dict(event=event,reserved_for_final_test=reserved,fit_eligible=True,objective_map_complete=True)]
    with pytest.raises(ValueError,match='Final/reserved'):
        development_groups(rows,dict(train_events=['train'],development_event='dev'))


@pytest.mark.parametrize('complete,ambiguous,expected',[(True,False,10),(False,False,0),(True,True,0)])
def test_final_quality_uses_identity_and_completeness_never_rating(tmp_path,monkeypatch,complete,ambiguous,expected):
    import json
    import v3_final_pipeline as final
    monkeypatch.setattr(final,'DATA',tmp_path)
    out=tmp_path/'1';out.mkdir()
    players=[dict(player=f'p{i}.TEAM',team=i//5,derived=dict(kills=2,deaths=3,rounds=10)) for i in range(10)]
    pred=dict(players=players,map='Villa',score=[7,3],objective_complete=complete)
    (out/'replay-predictions.json').write_text(json.dumps(pred))
    public=[dict(id=i,ign=f'p{i}',stylized_name=f'p{i}',roster_id=i//5) for i in range(10)]
    if ambiguous:public[1]['ign']='p0';public[1]['stylized_name']='p0'
    meta=dict(competition_id=189,date='2026-09-05T09:00:00Z',players=public,
        games=[dict(id=2,map=dict(name='Villa'),win_score=7,loss_score=3)])
    # Invalid numeric Rating proves quality never attempts to parse it.
    targets={'2':{str(i):dict(kd='2-3 (-1)',rounds=10,rating='SEALED_DO_NOT_PARSE') for i in range(10)}}
    (out/'siegegg-api-sealed.json').write_text(json.dumps(meta))
    (out/'siegegg-player-stats-sealed.json').write_text(json.dumps(targets))
    result=final.quality(dict(official_match_id=1,siegegg_match_id=2,date='2026-09-05T09:00:00Z'),pred,dict(siegegg_competition_id=189))
    assert sum(d['eligible'] for d in result['decisions'])==expected
    assert result['ratings_inspected'] is False


def test_final_refuses_repeated_target_open_after_interrupted_evaluation(tmp_path,monkeypatch):
    import v3_final_pipeline as final
    monkeypatch.setattr(final,'DATA',tmp_path)
    monkeypatch.setattr(final,'RESULT',tmp_path/'one-shot-result.json')
    (tmp_path/'rating-targets-opened.json').write_text('{}')
    with pytest.raises(ValueError,match='already opened'):
        final.evaluate({},dict(matches=[]))
