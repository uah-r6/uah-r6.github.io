"""Cache the new Go credit validator's output; reuse existing decoded evidence.

Old parser binaries/caches/final study inputs are never replaced. An optional
actual replay run checks the new reader against the same structural evidence.
"""
import hashlib
import json
import subprocess

from objective_player_component_fields import observe
from objective_actor_liveness import feedback
from v3_final_reserve import ROOT, sha

EXE = ROOT / '.local-tools/bin/siege-kill-credit.exe'
DATA = ROOT / 'data/research/credited-kills-v1'


def numeric_hash(value):
    return int.from_bytes(bytes.fromhex(value), 'little')


def structural_evidence(rec):
    state, _, _, fields = observe(rec)
    properties = [dict(offset=p['offset'], entity=p['entity'], tag=numeric_hash(p['hash']),
                       size=p['size'], bits=p['value'])
                  for p in fields if p['hash'] in ('eed445c8', '1cd2b19d')
                  and type(p['value']) is int]
    return dict(header=state['header'], declarations=[dict(offset=d['offset'], owner=d['owner'],
        slot=numeric_hash(d['slot_hash']), component=d['component'],
        **{'class': numeric_hash(d['class_hash'])}) for d in state['declarations']],
        properties=properties, finishes=feedback(rec)['events'])


def inspect(rec, *, actual_replay=False):
    evidence = None if actual_replay else structural_evidence(rec)
    mode = 'replay' if actual_replay else 'cached-structure'
    payload = b'' if evidence is None else json.dumps(evidence, sort_keys=True).encode()
    key = hashlib.sha256(EXE.read_bytes()+bytes.fromhex(sha(rec))+mode.encode()+payload).hexdigest()
    cache = DATA / 'observations'; cache.mkdir(parents=True, exist_ok=True)
    destination = cache / (key+'.json')
    if destination.exists():
        return json.loads(destination.read_text(encoding='utf-8'))
    if evidence is None:
        command = [str(EXE), str(rec)]
    else:
        input_path = cache / (key+'.evidence.json')
        input_path.write_text(json.dumps(evidence), encoding='utf-8')
        command = [str(EXE), '--evidence', str(input_path)]
    run = subprocess.run(command, check=True, capture_output=True, text=True)
    result = json.loads(run.stdout)
    result.update(replay_sha256=sha(rec), executable_sha256=sha(EXE), mode=mode)
    destination.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    return result
