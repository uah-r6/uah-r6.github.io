"""Fixed occurrence-only validation extension; excludes the reserved NA event.

The six match IDs / 12 physical maps below are locked before inspecting results.
They have Rating development history, but were not used in the 291-round
state-property discovery. No Rating targets or actor labels are evaluated here.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from objective_encoding_probe import inherited_state_events
from objective_occurrence_validation import occurrences
from objective_transition_probe import ROOT, PARSER

MATCHES = (3579, 3563, 4283, 6157, 6158, 6277)


def main():
    sources = json.loads((ROOT/'research/sources.json').read_text())['matches']
    cache = ROOT/'data/research/diagnostics/objective-occurrence-holdout'
    signature = hashlib.sha256(Path(__file__).with_name('objective_encoding_probe.py').read_bytes()
                               + PARSER.read_bytes()).hexdigest()
    reports = []
    with tempfile.TemporaryDirectory() as temp:
        dump = Path(temp)/'round.dump'
        for mid in MATCHES:
            source = next(s for s in sources if s.get('siegegg_match_id') == mid)
            assert 'North America League Stage 2' not in source['event']
            target = json.loads((ROOT/f'data/research/targets/siegegg-match-{mid}-api.json').read_text())
            for mapping in source['maps']:
                folders = [p for p in (ROOT/'data/research/extracted').rglob(mapping['folder']) if p.is_dir()]
                if len(folders) != 1:
                    raise ValueError('Ambiguous physical replay folder')
                normalized = json.loads((ROOT/'data/research/derived'/f"{mapping['folder']}.json").read_text())
                game = next(g for g in target['games'] if g['id'] == mapping['siegegg_game_id'])
                files = sorted(folders[0].glob('*.rec'))
                if len(files) != len(normalized['rounds']) or len(files) != len(game['rounds']):
                    raise ValueError('Round count disagreement')
                for rec in files:
                    number = int(re.search(r'-R(\d+)\.rec$',rec.name).group(1))
                    dest = cache/mapping['folder']/f'R{number:02d}.json'
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    key = signature+hashlib.sha256(rec.read_bytes()).hexdigest()
                    parsed = json.loads(dest.read_text()) if dest.exists() else {}
                    if parsed.get('signature') != key:
                        subprocess.run([str(PARSER),'--dump','-o',str(dump),str(rec)],check=True,capture_output=True)
                        parsed = {'signature':key,'events':inherited_state_events(dump.read_bytes())}
                        dest.write_text(json.dumps(parsed))
                    round_ = next(r for r in normalized['rounds'] if r['number']==number)
                    sides = {p['side'] for p in round_['players'] if p['team']==round_['winner']}
                    side = next(iter(sides)) if len(sides)==1 else None
                    result = occurrences(parsed['events'],side,normalized['game_mode'])
                    # Public labels are used only after replay-only classification.
                    labels = game['rounds'][number-1]['events']
                    expected = {k: any(e['type']==k for e in labels) for k in ['plant','disable']}
                    reports.append({'match_id':mid,'game_id':game['id'],'round':number,
                        'folder':mapping['folder'],'winner_side':side,'events':parsed['events'],
                        'result':result,'expected':expected})
                print('completed',mid,game['id'],len(files),flush=True)
    output = {'rounds':len(reports), 'maps':len({r['folder'] for r in reports}),
              'counts': {k: {'candidate':sum(r['result'][k] for r in reports),
                             'public':sum(r['expected'][k] for r in reports)} for k in ['plant','disable']},
              'mismatches':[r for r in reports if any(r['expected'][k]!=r['result'][k] for k in ['plant','disable'])],
              'results':reports}
    (cache/'summary.json').write_text(json.dumps(output,indent=2))
    print(json.dumps({k:v for k,v in output.items() if k!='results'},indent=2))


if __name__=='__main__':
    main()
