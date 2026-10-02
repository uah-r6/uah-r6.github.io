"""Observe the consumed 9734089 health class without changing frozen helpers."""
from collections import Counter,defaultdict
import hashlib
import json
import subprocess

from objective_actor_liveness import feedback
from objective_state_components import probe
from objective_transition_probe import ROOT


def main():
    base = ROOT/'data/research/diagnostics/health-class-variant'
    base.mkdir(parents=True,exist_ok=True)
    source = (ROOT/'research/state_component_probe.go').read_text()
    original = 'hex.EncodeToString(data[i+21:i+25]) == "0c98c63f"'
    if source.count(original)!=1:
        raise ValueError('Frozen observer source shape changed')
    variant = source.replace(original,'('+original+' || hex.EncodeToString(data[i+21:i+25]) == "b529300b")')
    path = base/'state_component_variant_probe.go'
    exe = ROOT/'.local-tools/bin/state-component-variant-probe.exe'
    if not path.exists() or path.read_text()!=variant or not exe.exists():
        path.write_text(variant)
        subprocess.run([str(ROOT/'.local-tools/go/bin/go.exe'),'build','-o',str(exe),str(path)],
                       cwd=ROOT/'third_party/siege-dissect',check=True)
    reports = []
    folder = next((ROOT/'data/research/extracted').rglob('Match-2026-06-18_16-24-16-18868'))
    for number in (3,4,6):
        rec = next(folder.glob(f'*-R{number:02d}.rec'))
        key = hashlib.sha256(exe.read_bytes()+rec.read_bytes()).hexdigest()
        dest = base/(key+'.json')
        if not dest.exists():
            run = subprocess.run([str(exe),str(rec)],check=True,capture_output=True,text=True)
            dest.write_text(json.dumps(json.loads(run.stdout)[0]))
        raw = json.loads(dest.read_text())
        deaths = feedback(rec)
        if raw['feedback']!=probe(rec)['feedback']:
            raise ValueError('Variant observer changed feedback')
        expected = [e for e in raw['feedback'] if e['type']['name'] in ('Kill','Death')]
        if expected!=[d['feedback'] for d in deaths['events']]:
            raise ValueError('Variant observer changed death feedback')
        players = []
        for player in raw['header']['players']:
            uid = {p['entity'] for p in raw['properties'] if p['kind']=='numeric_uid' and p['value']==player['id']}
            links = [d for d in raw['declarations'] if d['owner'] in uid and
                     (d['slot_hash'],d['class_hash'])==('4154dcc4','b529300b')]
            entities = {d['component'] for d in links}
            fields = [p for p in raw['properties'] if p['entity'] in entities and p['hash']=='e788f6a5']
            hp = [p for p in raw['properties'] if p['entity'] in entities and p['kind']=='health']
            death = [d for d in deaths['events'] if d['feedback'].get('target')==player['username']
                     or (d['feedback']['type']['name']=='Death' and d['feedback'].get('username')==player['username'])]
            samples = []
            for d in death:
                prior = [p for p in fields if 0<p['offset']<d['offset']]
                samples.append(dict(death_offset=d['offset'],last_state=prior[-1] if prior else None))
            players.append(dict(player=player['username'],uid_owners=sorted(uid),components=sorted(entities),
                                state_values=sorted({p['value'] for p in fields}),state_fields=fields,health_samples=hp,death_samples=samples))
        reports.append(dict(round=number,build=raw['header']['codeVersion'],players=players))
    counts = Counter(d['last_state']['value'] if d['last_state'] else None for r in reports for p in r['players'] for d in p['death_samples'])
    (base/'summary.json').write_text(json.dumps(dict(observer_source_sha256=hashlib.sha256(variant.encode()).hexdigest(),
                                                  observer_exe_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
                                                  state_before_death_counts=dict(counts),rounds=reports),indent=2))
    lines = ['# Consumed build9734089 health-class observation','',
             'Original frozen cd28f76 helper/candidate preserved byte-for-byte. A separate generated ignored '
             'Go helper also observes declared class b529300b on slot4154dcc4. This broadens raw field capture '
             'only; no player actor resolver or production class allowlist changed. No targets used.', '',
             f'State before existing Kill/Death envelopes: `{dict(counts)}`.', '',
             '| Physical round/player | UID owners | Health components | Raw states | HP samples |',
             '| --- | --- | --- | --- | --- |']
    for r in reports:
        for p in r['players']:
            lines.append(f"| R{r['round']:02d}/{p['player']} | {p['uid_owners']} | {p['components']} | {p['state_values']} | {len(p['health_samples'])} |")
    lines += ['', 'This consumed observation may justify another separately frozen diagnostic after '
              'state semantics, unique identity and independent HUD evidence are checked. It cannot '
              'retroactively increase the recorded first-reserve result or turn it fresh again.', '']
    (ROOT/'research/output/objective-health-class-variant.md').write_text('\n'.join(lines),encoding='utf-8')
    print('rounds',len(reports),'linked players',sum(bool(p['state_fields']) for r in reports for p in r['players']),
          'state before death',dict(counts))


if __name__=='__main__':
    main()
