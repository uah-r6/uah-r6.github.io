"""Frozen predictor parity, native reset order and whole-map abstentions."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

from r6stats.export import export
from r6stats.parser.models import Kill, Match, ObjectiveOccurrence
from r6stats.rating_inputs_v3 import (load_inputs, native_state, prepare,
                                     store_objective_evidence)
from r6stats.credited_refresh import store
from r6stats.stats.calculate import aggregate, calculate_match, COUNTS
from r6stats.stats.rating_v3 import SiegeStyleV3Rating
from test_credited_production import fixture, make_db

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'research'))
from v3_native_order_fit import predict  # noqa: E402


def evidence(match, records):
    for r, observed in zip(match.rounds, records):
        names = {p.key: p.username for p in r.players}
        observed['credit']['finishes'] = [dict(offset=1000+k.sequence*100, feedback=dict(
            type={'name': 'Kill' if k.killer else 'Death'}, username=names[k.killer or k.victim],
            target=names[k.victim], timeInSeconds=k.remaining, headshot=k.headshot)) for k in r.kills]
        r.objective_occurrences = [ObjectiveOccurrence(o.kind, 'defuser_state_v1', 2000,
            o.player, 3, 'completing_timer_owner_v1', 'completing_timer_owner_v1') for o in r.objectives]
    return match, records


def test_full_precision_frozen_coefficients_and_all_consumed_rows_predictor_parity():
    model = json.loads((ROOT/'research/v3-native-order-candidate.json').read_text())['model']
    assert SiegeStyleV3Rating.intercept == model['intercept']
    for name, w, mean, scale in SiegeStyleV3Rating.terms:
        assert (w, mean, scale) == (model['weights_standardized'][name], model['means'][name], model['scales'][name])
    # Optional private cohort: targets are never evaluated/regraded here.
    data = ROOT/'data/research/v3-native-order-development-v1/dataset.json'
    rows = json.loads(data.read_text(encoding='utf-8'))['rows'] if data.exists() else []
    match, records = evidence(*fixture())
    _, rounds = prepare(match, records)
    rows += [dict(rounds=r) for r in rounds.values()]
    for row in rows:
        totals = {key: sum(r[key] for r in row['rounds']) for key in
                  ('kills', 'teamkills', 'opening_kills', 'opening_deaths', 'clutches',
                   'kost_rounds', 'survived', 'deaths_traded', 'kills_traded', 'plants', 'disables',
                   'clutch_1v1', 'clutch_1v2', 'clutch_1v3', 'clutch_1v4', 'clutch_1v5')}
        totals.update(rounds=len(row['rounds']), multikill_extra=sum(max(r['kills']-1, 0) for r in row['rounds']))
        assert SiegeStyleV3Rating.calculate(totals) == pytest.approx(predict(model, row), abs=1e-12)


def test_native_order_plant_reset_keeps_first_1v3_and_actual_winner():
    match, records = fixture(); r=match.rounds[0]; p=[p.key for p in r.players]
    pairs=[(1,5),(2,6),(7,1),(7,2),(7,3),(7,4),(0,7),(0,8),(0,9)]
    times=[16,15,14,13,12,11,40,39,38]
    r.kills=[Kill(i,t,p[a],p[b],a//5,b//5) for i,((a,b),t) in enumerate(zip(pairs,times))]
    match, records=evidence(match, records)
    before=deepcopy(match.to_dict())
    opening, clutch=native_state(r,records[0]['credit'])
    assert opening==(p[1],p[5]) and clutch==(p[0],3)
    assert calculate_match(Match('m','','Border','CustomGame','Bomb',[r]))[p[0]]['clutches']==0
    r.winner=1
    assert native_state(r,records[0]['credit'])[1] != (p[0],3)
    r.winner=0
    assert match.to_dict()==before


@pytest.mark.parametrize('kind',['offset','parity','identity','objective','partial','duplicate'])
def test_whole_map_refuses_uncertain_evidence(kind):
    m, records=evidence(*fixture())
    if kind=='offset': records[0]['credit']['finishes'][0]['offset']=0
    elif kind=='parity': records[0]['credit']['finishes'][0]['feedback']['timeInSeconds']=99
    elif kind=='identity': records[0]['credit']['players'][0]['username']='other'
    elif kind=='objective': m.rounds[0].objective_occurrences=[]
    elif kind=='partial': records[1]['credit']['complete']=False
    else: m.rounds[0].kills[1].sequence=0
    with pytest.raises(ValueError): prepare(m,records)


def test_export_eligible_only_preserves_history_and_v2_snapshot_and_invalidates_reparse(tmp_path):
    db,mid,m,records=make_db(tmp_path)
    evidence(m,records)
    store(db,mid,records,'binary')
    original=db.execute('SELECT normalized_json FROM maps').fetchone()[0]
    store_objective_evidence(db,mid,m)
    snapshots=[tuple(r) for r in db.execute('SELECT * FROM rating_input_snapshots')]
    assert load_inputs(db,mid)[0] is not None
    config={'team':{},'stats':{'rating_version':'siege_style_v3','trade_window_seconds':8}}
    root=tmp_path/'web/public/data';export(db,config,root)
    doc=json.loads((root/'matches'/f'{mid}.json').read_text())
    assert doc['rating_eligible'] and doc['rating_version']=='siege_style_v3'
    assert all(p['rating_rounds']==2 for p in doc['players'])
    old=calculate_match(Match.from_dict(json.loads(original)))
    for p in doc['players']:
        key=next(x.key for x in m.rounds[0].players if x.username==p['name'])
        for field in COUNTS:
            if field not in ('kills','multikill_extra','kost_rounds'):
                assert p[field]==old[key][field]
    assert [tuple(r) for r in db.execute('SELECT * FROM rating_input_snapshots')]==snapshots
    # Metadata change leaves eligibility intact; raw reparse changes invalidate
    # the old evidence seal and abstain when new data lacks core occurrences.
    db.execute("UPDATE maps SET normalized_json=normalized_json || ' '")
    assert load_inputs(db,mid)[0] is None
    export(db,config,root)
    assert json.loads((root/'matches'/f'{mid}.json').read_text())['players'][0]['rating'] is None
    with pytest.raises(ValueError,match='8-second'): load_inputs(db,mid,5)


def test_supported_rounds_aggregate_and_v3_requires_guarded_map_input():
    m, records=evidence(*fixture()); stats, rounds=prepare(m,records)
    for key, values in rounds.items():
        assert aggregate(values,'siege_style_v3')['rating']==stats[key]['rating']
    with pytest.raises(ValueError,match='validated whole-map'): calculate_match(m,8,'siege_style_v3')
