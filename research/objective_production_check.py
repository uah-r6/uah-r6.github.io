"""Read-only candidate-parser parity check against frozen objective results.

Writes only ignored diagnostics. Does not update derived observations or SQLite.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from r6stats.parser.siege_dissect import normalize, physical_round_numbers
from objective_transition_probe import ROOT, replay_file

CANDIDATE = ROOT/'.local-tools/bin/siege-dissect-objectives.exe'


def candidate(folder, executable=CANDIDATE):
    cache = ROOT/'data/research/diagnostics/objective-production-check'
    cache.mkdir(parents=True,exist_ok=True)
    files = sorted(folder.glob('*.rec'))
    key = hashlib.sha256(executable.read_bytes()+b''.join(
        hashlib.sha256(p.read_bytes()).digest() for p in files)).hexdigest()
    raw_file = cache/(key+'.json')
    if not raw_file.exists():
        subprocess.run([str(executable),'-f','json','-o',str(raw_file),str(folder)],check=True,capture_output=True)
    return normalize(json.loads(raw_file.read_text()),round_numbers=physical_round_numbers(files))


def main():
    diag = ROOT/'data/research/diagnostics'
    development = json.loads((diag/'objective-encoding-validation/occurrence-validation.json').read_text())['results']
    holdout = json.loads((diag/'objective-occurrence-holdout/summary.json').read_text())['results']
    expected = {}
    for row in development:
        rec,_ = replay_file(row['match_id'],row['round'])
        expected[(rec.parent.name,row['round'])] = row['result']
    for row in holdout:
        expected[(row['folder'],row['round'])] = row['result']
    results = []
    for folder_name in sorted({folder for folder,_ in expected}):
        folders = [p for p in (ROOT/'data/research/extracted').rglob(folder_name) if p.is_dir()]
        if len(folders)!=1: raise ValueError('Ambiguous folder')
        parsed = candidate(folders[0])
        baseline = json.loads((ROOT/'data/research/derived'/f'{folder_name}.json').read_text())
        for round_ in parsed.to_dict()['rounds']:
            old = next(r for r in baseline['rounds'] if r['number']==round_['number'])
            key = folder_name,round_['number']
            if key not in expected: continue
            kinds = {o['kind'] for o in round_['objective_occurrences']}
            mismatch = [k for k in ['plant','disable'] if (k in kinds)!=expected[key][k]]
            # Compare gameplay fields independently of new metadata and historic
            # score fields absent in older normalized caches.
            changed = [k for k in ['players','kills','objectives','winner','win_condition','site'] if round_[k]!=old[k]]
            results.append({'folder':folder_name,'round':round_['number'],
                            'occurrence_mismatch':mismatch,'changed_existing_fields':changed,
                            'occurrences':round_['objective_occurrences']})
        print('checked',folder_name,flush=True)
    report = {'maps':len({r['folder'] for r in results}),'rounds':len(results),
              'failures':[r for r in results if r['occurrence_mismatch'] or r['changed_existing_fields']],
              'results':results}
    (diag/'objective-production-check/summary.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))


if __name__=='__main__':
    main()
