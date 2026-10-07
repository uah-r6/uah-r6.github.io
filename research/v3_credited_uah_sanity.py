"""Read-only UAH feature/aggregate parity; never train or tune from UAH."""
from collections import defaultdict
from copy import deepcopy
import json
import math
import sqlite3

from credited_late_history_development import immutable_write
from fit_models import predict,FEATURES
from r6stats.credited_refresh import display_stats,load,round_counts
from r6stats.parser.models import Match
from r6stats.stats.calculate import aggregate
from uah_comparison import player_rounds
from v3_final_reserve import ROOT,sha,source_sha


def aggregate_score(model,stats):
    n=stats['rounds']
    if not n:return 0.0
    values=(stats['kills'],stats['teamkills'],stats['multikill_extra'],
        stats['opening_kills']-stats['opening_deaths'],stats['clutches'],stats['kost_rounds'],
        stats['survived'],stats['deaths_traded']-stats['kills_traded'],stats['plants']+stats['disables'])
    return model['intercept']+sum(model['weights_standardized'][f]*(value/n-model['means'][f])/model['scales'][f] for f,value in zip(FEATURES,values))


def main():
    db_path=ROOT/'data/r6stats.sqlite';before=sha(db_path)
    candidate_path=ROOT/'research/v3-credited-candidate.json';model=json.loads(candidate_path.read_text(encoding='utf-8'))['model']
    db=sqlite3.connect(db_path.resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    rows=[];season=defaultdict(list);stats_by_player=defaultdict(list);coverage=[]
    names={r['id']:r['display_name'] for r in db.execute('SELECT id,display_name FROM players WHERE tracked=1')}
    for saved in db.execute('SELECT * FROM maps ORDER BY rowid'):
        match=Match.from_dict(json.loads(saved['normalized_json']));credit=load(db,saved['id'])
        shown=display_stats(match,credit);counts=round_counts(match,credit) if credit else None
        unresolved=[dict(round=r.number,kind=o.kind,reason=o.actor_reason) for r in match.rounds for o in r.objective_occurrences if not o.actor or o.actor_source!=o.actor_reason or o.actor_source!='completing_timer_owner_v1']
        coverage.append(dict(map_id=saved['id'],map=match.map_name,rounds=len(match.rounds),credit_complete=credit is not None,unresolved_objectives=unresolved))
        bindings=db.execute('SELECT DISTINCT rp.player_id,rp.player_key FROM round_players rp JOIN rounds rd ON rd.id=rp.round_id WHERE rd.map_id=? AND rp.player_id IS NOT NULL',(saved['id'],)).fetchall()
        for binding in bindings:
            if binding['player_id'] not in names:continue
            key=binding['player_key'];old=player_rounds(match,key);corrected=deepcopy(old)
            if counts:
                for r in corrected:
                    r['kills']=counts[r['number']][key]
                    r['kost_rounds']=int(bool(r['kills'] or r['plants'] or r['disables'] or r['survived'] or r['deaths_traded']))
            score=predict(model,dict(rounds=corrected),{});value=aggregate_score(model,shown[key])
            if not math.isfinite(score) or abs(score-value)>1e-12:raise ValueError('Round/aggregate model parity failure')
            season[names[binding['player_id']]]+=corrected;stats_by_player[names[binding['player_id']]].append(shown[key])
            rows.append(dict(player=names[binding['player_id']],map_id=saved['id'],map=match.map_name,rounds=len(corrected),
                v3_readonly=score,aggregate_parity_delta=value-score,credit_complete=credit is not None,
                note='Diagnostic only: unresolved whole-map input coverage is explicit; no live Rating/default change'))
    season_rows=[]
    for name,rounds in season.items():
        stats=aggregate(stats_by_player[name],'siege_style_v2');score=predict(model,dict(rounds=rounds),{});value=aggregate_score(model,stats)
        if abs(score-value)>1e-12:raise ValueError('Season aggregate parity failure')
        season_rows.append(dict(player=name,rounds=len(rounds),diagnostic_all_map_v3=score,aggregate_parity_delta=value-score))
    if set(season)!=set(names.values()) or sha(db_path)!=before:raise ValueError('Missing tracked player or database modification')
    result=dict(candidate_sha256=source_sha(candidate_path),database_sha256=before,source_sha256=source_sha(ROOT/'research/v3_credited_uah_sanity.py'),
        model_tuned_from_uah=False,production_changed=False,map_coverage=coverage,rows=rows,season=season_rows)
    immutable_write(ROOT/'data/research/v3-credited-uah-sanity-v1/result.json',result)
    lines=['# Frozen v3 read-only UAH sanity','',
        'UAH is not training/validation truth. All-map scores below are diagnostics only; whole-map credited/objective coverage must be resolved explicitly before deployment. No coefficients, live version, database or generated data changed.','',
        '| Player | Rounds | Diagnostic all-map v3 | Round/aggregate delta |','| --- | ---: | ---: | ---: |']
    lines += [f"| {r['player']} | {r['rounds']} | {r['diagnostic_all_map_v3']:.8f} | {r['aggregate_parity_delta']:.2g} |" for r in season_rows]
    lines += ['','## Map feature coverage','',json.dumps(coverage,indent=2),'','Individual map scores are preserved privately; no NaN or missing tracked player. Exact feature aggregation matches the research predictor within1e-12.']
    (ROOT/'research/output/v3-credited-uah-sanity.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('READ ONLY UAH',season_rows,'COVERAGE',coverage,flush=True)


if __name__=='__main__':main()
