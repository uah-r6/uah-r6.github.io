"""Read-only full replay parity: Go actor port versus consumed structural audit."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json

from objective_completer_consumed_audit import inputs
from objective_production_check import candidate_raw
from objective_transition_probe import ROOT
from uah_guarded_actor_readonly import snapshot


def reviewed_legacy_damage_variation(before,after):
    """Two exact outputs were reproduced with the unchanged frozen binary.

    Only this consumed R10 field discrepancy is reviewed. Other fields and
    cases still fail parity. No damage/HP parser implementation is changed.
    """
    cache=ROOT/'data/research/diagnostics/completer-consumed-audit'
    variants=[]
    for n in range(4):
        path=cache/f'health-repeat-siege-dissect-objectives-{n}.json'
        if not path.is_file():return False
        raw=json.loads(path.read_text(encoding='utf-8'))
        row=raw.get('rounds',[raw])[0]
        variants.append(row.get('stats',raw.get('stats',[])))
    return before in variants and after in variants and before!=after


def inspect_folder(folder,rows,executable,expectations):
    old=candidate_raw(folder)
    port=candidate_raw(folder,executable)
    records=[]
    for row in rows:
        physical=row['physical_round']
        before=old['rounds'][physical-1]
        after=port['rounds'][physical-1]
        h0=before.get('header',before);h1=after.get('header',after)
        other0={k:v for k,v in h0.items() if k!='objectiveOccurrences'}
        other1={k:v for k,v in h1.items() if k!='objectiveOccurrences'}
        changes=[]
        diagnostic=[]
        if (row['match_id'],physical)==(4140,10) and reviewed_legacy_damage_variation(other0.get('stats'),other1.get('stats')):
            diagnostic.append('legacy_raw_damage_nondeterminism_reproduced_with_unchanged_old_binary')
            other0=other0|dict(stats=other1['stats'])
        if other0!=other1: changes.append('header_or_gameplay_changed')
        if before.get('matchFeedback',h0.get('matchFeedback'))!=after.get('matchFeedback',h1.get('matchFeedback')):
            changes.append('kill_death_operator_objective_feedback_changed')
        expected_occ=[{k:o[k] for k in ('kind','source','plantStateOffset')} for o in h0.get('objectiveOccurrences',[])]
        actual_occ=[{k:o[k] for k in ('kind','source','plantStateOffset')} for o in h1.get('objectiveOccurrences',[])]
        if expected_occ!=actual_occ:changes.append('objective_occurrence_changed')
        expected=expectations[row['folder'],physical]['predictions']
        actors={o['kind']:o.get('actor') for o in h1.get('objectiveOccurrences',[])}
        for kind in ('plant','disable'):
            if actors.get(kind)!=expected[kind]['proposal']:changes.append(kind+'_port_actor_differs')
        records.append(row|dict(actors=actors,occurrences=h1.get('objectiveOccurrences',[]),changes=changes,
                               reviewed_existing_diagnostic_variations=diagnostic))
    print('parsed',folder.name,len(records),'failures',sum(bool(r['changes']) for r in records),flush=True)
    return records


def main():
    protected=snapshot()
    executable=ROOT/'.local-tools/bin/siege-dissect-actors.exe'
    if not executable.is_file():raise ValueError('Build the separate actor candidate first')
    research=json.loads((ROOT/'data/research/diagnostics/completer-consumed-audit/predictions.json').read_text(encoding='utf-8'))
    expectations={(r['folder'],r['physical_round']):r for r in research}
    grouped={}
    for r in inputs().values():grouped.setdefault(r['folder'],[]).append(r)
    tasks=[]
    for name,rows in grouped.items():
        found=[p for p in (ROOT/'data/research/extracted').rglob(name) if p.is_dir()]
        if len(found)!=1:raise ValueError('Ambiguous physical source')
        tasks.append((found[0],rows,executable,expectations))
    records=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(inspect_folder,*args) for args in tasks]):records+=future.result()
    records.sort(key=lambda r:(r['match_id'],r['folder'],r['physical_round']))
    if snapshot()!=protected:raise ValueError('Protected live files changed')
    summary=dict(status='go_port_readonly_parity_not_new_actor_validation',rounds=len(records),
        folders=len(tasks),binary_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
        failures=[r for r in records if r['changes']],records=records,protected_files=len(protected),
        actors_resolved={kind:sum(bool(r['actors'].get(kind)) for r in records) for kind in ('plant','disable')})
    dest=ROOT/'data/research/diagnostics/objective-actor-go-parity.json'
    # Preserve the first raw mismatch before appending its independent review.
    first=dest.with_name('objective-actor-go-parity-first-raw-result.json')
    if dest.exists() and not first.exists():first.write_bytes(dest.read_bytes())
    dest.write_text(json.dumps(summary,indent=2),encoding='utf-8')
    lines=['# Go completing-owner port: full consumed replay parity','',
        f'Physical rounds{len(records)}, folders{len(tasks)}; failures{len(summary["failures"])}. '
        f'Resolved actors`{summary["actors_resolved"]}`. Binary SHA256`{summary["binary_sha256"]}`.','',
        'Compared every existing header/gameplay field and full MatchFeedback, and separately occurrence '
        'kind/source/offset. Expected actors are the previously saved structural research predictions, '
        'not external target names. This verifies implementation parity, not new actor accuracy. '
        'Reduced real controls, negative attempts and 423objective-free full rounds are included. '
        'The normal parser binary is not replaced by this script.','',
        'The first raw comparison reported one stats-field difference:4140/R10 Logan damageTaken125->110 '
        'and Rexen damageDealt235->220. Four direct runs of the UNCHANGED frozen occurrence binary '
        'reproduced both exact output variants (125/235 and110/220). Existing HP-to-player map iteration '
        'is nondeterministic for that ambiguous mapping; normalized tracker data ignores these raw damage '
        'estimates. The first raw parity result is retained separately. Only exact previously reproduced '
        'stats variants for this case are a reviewed informational difference. All other changes fail. '
        'No health, kill, operator, stats or Rating implementation was changed to fix this unrelated issue.','',
        f'{len(protected)} protected database/archive/public file hashes unchanged. '
        'No imports, historical corrections, Rating refit, public export or publishing.','',
        'Reproduce `.venv/Scripts/python.exe research/objective_actor_go_parity.py`. '
        'Successful full parses cache by binary/replay digest; no repeated downloads or parser work.','']
    for r in summary['failures']:
        lines.append(f"- {r['match_id']}/{r['folder']}/R{r['physical_round']:02d}: {r['changes']}; actors{r['actors']}")
    (ROOT/'research/output/objective-actor-go-parity.md').write_text('\n'.join(lines),encoding='utf-8')
    print('GO PORT PARITY',summary['rounds'],len(summary['failures']),summary['actors_resolved'],flush=True)
    if summary['failures']:raise SystemExit(1)


if __name__=='__main__':main()
