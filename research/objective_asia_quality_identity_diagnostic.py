"""Consumed 8193 missing-identity diagnostic; no proposals or quality repair."""
from collections import Counter
import json

from objective_bonus_body_asia_identity_review import verify_preserved
from objective_production_check import candidate_raw
from r6stats.parser.siege_dissect import normalize
from v3_final_reserve import ROOT, sha


def main():
    verify_preserved();root=ROOT/'data/research/extracted/bonus-body-asia-8193';rows=[]
    for folder in sorted({p.parent for p in root.rglob('*.rec')}):
        raw=candidate_raw(folder,ROOT/'.local-tools/bin/siege-dissect-actors.exe')
        for rec,r in zip(sorted(folder.glob('*.rec')),raw['rounds']):
            h=r.get('header',r);players=h['players'];n=int(rec.stem.rsplit('-R',1)[1]);normalized=normalize([r],round_numbers=[n]).rounds[0]
            issues=[]
            if len(players)!=10:issues.append('header_player_count_'+str(len(players)))
            if len(normalized.players)!=10:issues.append('normalized_player_count_'+str(len(normalized.players)))
            for p in players:
                if not p.get('id'):issues.append('missing_numeric_uid:'+p['username'])
                if not p.get('profileID') or p['profileID']=='00000000-0000-0000-0000-000000000000':issues.append('missing_profile_uuid:'+p['username'])
            if len({p.get('id') for p in players})!=len(players):issues.append('duplicate_uid')
            if len({p.get('profileID') for p in players})!=len(players):issues.append('duplicate_profile')
            rows.append(dict(folder=folder.name,physical_round=n,replay_sha256=sha(rec),issues=issues,
                             players=[dict(username=p['username'],profile_id=p.get('profileID'),numeric_uid=p.get('id'),team=p.get('teamIndex')) for p in players],
                             score=[dict(start=t['startingScore'],end=t['score']) for t in h['teams']]))
    report=dict(status='consumed_quality_diagnostic_no_repair',rounds=rows,affected=sum(bool(r['issues']) for r in rows),
                reason='Historical whole-map refusal remains immutable; no omitted/reconstructed player or admitted map.')
    destination=ROOT/'data/research/objective-bonus-body-asia/8193/consumed-identity-quality-diagnostic.json'
    if destination.exists():
        if json.loads(destination.read_text(encoding='utf-8'))!=report:raise ValueError('Quality diagnostic differs')
    else:destination.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    lines=['# ASIA 8193 consumed roster quality diagnostic','',report['reason'],'',
           '| Physical folder | Round | Header count | Exact refusal |','| --- | ---: | ---: | --- |']
    for r in rows:lines.append(f'| {r["folder"]} | {r["physical_round"]} | {len(r["players"])} | {", ".join(r["issues"]) or "none"} |')
    lines+=['','The header/normalized inventory is inspected only. Later valid headers do not prove earlier missing account identity. '
            'No raw packet reconstruction, actor label or score-based player association was attempted. The original full-roster safeguard remains unchanged.','']
    (ROOT/'research/output/objective-bonus-body-asia-8193-quality.md').write_text('\n'.join(lines),encoding='utf-8')
    verify_preserved();print('physical rounds',len(rows),'affected',report['affected'])
    for r in rows:
        if r['issues']:print(r['folder'],r['physical_round'],r['issues'])


if __name__=='__main__':main()
