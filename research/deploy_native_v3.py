"""Backed-up, preview-first deployment of the independently passing frozen v3.

No fitting, final re-evaluation, replay reparse, or historical statistic rewrite.
Run preview, then apply after complete tests/builds. Never publish from here.
"""
from collections import defaultdict
from copy import deepcopy
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from r6stats.db import repository as repo
from r6stats.export import export
from r6stats.parser.models import Match
from r6stats.publishing import validate_public_data
from r6stats.rating_inputs_v3 import digest, load_inputs, prepare, store_objective_evidence
from r6stats.replay_archive import verify
from r6stats.stats.calculate import aggregate
from uah_comparison import player_rounds
from v3_native_order_derive import updated_rows
from v3_native_order_fit import predict
from v3_final_reserve import ROOT, sha
from credited_late_history_development import immutable_write

DATA = ROOT/'data/research/native-v3-deployment-20261007'
INVENTORY = ROOT/'data/research/v3-credited-production-inputs-v1'
ALLOWED = {'rating', 'rating_version', 'rating_rounds', 'rating_maps', 'rating_eligible',
           'rating_exclusion', 'rating_description', 'kill_methodology'}


def state(db):
    tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    return {t: [dict(r) for r in db.execute(f'SELECT * FROM "{t}" ORDER BY rowid')] for t in tables
            if t != 'map_v3_objective_evidence'}


def strip(value):
    if isinstance(value, dict):
        return {k: strip(v) for k, v in value.items() if k not in ALLOWED}
    if isinstance(value, list):
        values = [strip(v) for v in value]
        if values and all(isinstance(v, dict) and ('slug' in v or 'id' in v) for v in values):
            values.sort(key=lambda v: v.get('slug', v.get('id')))
        return values
    return value


def check_public(before_root, after_root):
    before = {p.relative_to(before_root).as_posix(): json.loads(p.read_text(encoding='utf-8')) for p in before_root.rglob('*.json')}
    after = {p.relative_to(after_root).as_posix(): json.loads(p.read_text(encoding='utf-8')) for p in after_root.rglob('*.json')}
    if before.keys() != after.keys():
        raise ValueError('Public document inventory changed.')
    for key in before:
        if strip(before[key]) != strip(after[key]):
            raise ValueError(f'Unexpected public non-Rating change: {key}')
    return len(after)


def install_evidence(db):
    records = json.loads((INVENTORY/'summary.json').read_text(encoding='utf-8'))['maps']
    for record in records:
        if not record['eligible']:
            continue
        r = db.execute('SELECT * FROM maps WHERE id=?', (record['map_id'],)).fetchone()
        if digest(r['normalized_json']) != record['original_normalized_sha256'] or r['fingerprint'] != record['fingerprint']:
            raise ValueError('Supported input inventory changed; new preview required.')
        for path, hash_ in record['sources'].items():
            if sha(ROOT/path) != hash_:
                raise ValueError('Approved objective evidence cache changed.')
        full = json.loads((INVENTORY/'maps'/f"{record['map_id']}.json").read_text(encoding='utf-8'))
        store_objective_evidence(db, r['id'], Match.from_dict(full['evidence_normalized']))


def parity(db):
    model = json.loads((ROOT/'research/v3-native-order-candidate.json').read_text(encoding='utf-8'))['model']
    maps = []; aggregate_rows = defaultdict(list); worst = 0.; comparisons = 0
    for r in db.execute('SELECT * FROM maps ORDER BY rowid'):
        runtime, reason = load_inputs(db, r['id'])
        item = dict(map_id=r['id'], map=r['map_name'], rounds=len(json.loads(r['normalized_json'])['rounds']), eligible=runtime is not None, reason=reason)
        maps.append(item)
        if runtime is None:
            continue
        evidence = json.loads(db.execute('SELECT evidence_json FROM map_v3_objective_evidence WHERE map_id=?', (r['id'],)).fetchone()[0])
        match = Match.from_dict(evidence)
        credit = json.loads(db.execute('SELECT evidence_json FROM map_kill_credit WHERE map_id=?', (r['id'],)).fetchone()[0])
        observations = {c['logical_round']: dict(credit=c['credit'], header={'players': c['credit']['players']}) for c in credit}
        _, rounds = prepare(match, credit)
        binding = defaultdict(set)
        for b in db.execute('''SELECT DISTINCT rp.player_id,rp.player_key FROM round_players rp
            JOIN rounds rd ON rd.id=rp.round_id WHERE rd.map_id=? AND rp.player_id IS NOT NULL''', (r['id'],)):
            binding[b['player_id']].add(b['player_key'])
        item['players'] = []
        for p in db.execute('SELECT * FROM players WHERE tracked=1 ORDER BY display_name'):
            keys = binding[p['id']]
            if not keys or not keys <= runtime.keys():
                raise ValueError('Missing tracked Rating player.')
            research = []; native = []
            for key in sorted(keys):
                name = next(p.username for one in match.rounds for p in one.players if p.key == key)
                old = player_rounds(match, key)
                for one in old:
                    c = next(c for c in credit if c['logical_round'] == one['number'])
                    one['kills'] = next(p['kills'] for p in c['credit']['players'] if p['profileID'] == key)
                    one['kost_rounds'] = int(bool(one['kills'] or one['plants'] or one['disables'] or one['survived'] or one['deaths_traded']))
                prepared, _ = updated_rows(match, [dict(player=name, rounds=old)], observations)
                research += prepared[0]['rounds']; native += rounds[key]
            for a, b in zip(research, native):
                diff = abs(predict(model, dict(rounds=[a])) - aggregate([b], 'siege_style_v3')['rating'])
                worst = max(worst, diff); comparisons += 1
            runtime_total = aggregate([runtime[k] for k in sorted(keys)], 'siege_style_v3')
            prediction = predict(model, dict(rounds=research))
            diff = abs(prediction - runtime_total['rating']); worst=max(worst,diff); comparisons+=1
            if diff > 1e-12:
                raise ValueError('Tracked map predictor parity failed.')
            item['players'].append(dict(player=p['display_name'], rating=prediction, rounds=len(research)))
            aggregate_rows[p['slug']].append(dict(research=research, runtime=runtime_total, name=p['display_name']))
    if sum(m['eligible'] for m in maps) != 4 or sum(m['rounds'] for m in maps if m['eligible']) != 42:
        raise ValueError('Unexpected supported UAH map coverage.')
    totals=[]
    for slug, values in aggregate_rows.items():
        rating=aggregate([v['runtime'] for v in values], 'siege_style_v3')['rating']
        rows=[r for v in values for r in v['research']]
        expected=predict(model, dict(rounds=rows));worst=max(worst,abs(rating-expected));comparisons+=2
        totals.append(dict(slug=slug, name=values[0]['name'], rounds=len(rows), maps=len(values), rating=rating))
    if worst > 1e-12:
        raise ValueError('Runtime parity failed.')
    return dict(maps=maps, players=totals, max_parity_error=worst, parity_comparisons=comparisons,
                historical_display_rounds=82, eligible_rating_rounds=42, model_tuned_on_uah=False)


def preview():
    DATA.mkdir(parents=True, exist_ok=True)
    result = json.loads((ROOT/'data/research/v3-native-final-apac-n-stage1/one-shot-result.json').read_text(encoding='utf-8'))
    if not result['passed']:
        raise ValueError('Final did not pass; deployment prohibited.')
    before_path=DATA/'before.sqlite'
    source=sqlite3.connect((ROOT/'data/r6stats.sqlite').resolve().as_uri()+'?mode=ro', uri=True);source.row_factory=sqlite3.Row
    if not (DATA/'before.json').exists():
        archives={p.relative_to(ROOT).as_posix(): sha(p) for p in (ROOT/'data/replay-archive').rglob('*') if p.is_file()}
        snapshot=dict(head=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT,text=True).strip(),
            database_sha256=sha(ROOT/'data/r6stats.sqlite'), tables=state(source), archive_hashes=archives,
            model_sha256=sha(ROOT/'research/v3-native-order-candidate.json'), final_sha256=sha(ROOT/'data/research/v3-native-final-apac-n-stage1/one-shot-result.json'),
            settings_sha256=sha(ROOT/'config/settings.json'))
        with sqlite3.connect(before_path) as target:
            source.backup(target)
            if target.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Backup invalid')
        immutable_write(DATA/'before.json', snapshot)
        shutil.copyfile(ROOT/'config/settings.json', DATA/'before-settings.json')
        shutil.copytree(ROOT/'web/public/data', DATA/'before-public')
    before=json.loads((DATA/'before.json').read_text(encoding='utf-8'))
    if state(source)!=before['tables']:raise ValueError('Production state changed since preview')
    candidate=DATA/'candidate.sqlite'
    with sqlite3.connect(candidate) as target:source.backup(target)
    source.close()
    with repo.connect(candidate) as db:
        install_evidence(db); report=parity(db)
        if state(db)!=before['tables']:raise ValueError('Historical tables modified by preview')
        config=json.loads((ROOT/'config/settings.json').read_text(encoding='utf-8'));config['stats']['rating_version']='siege_style_v3'
        out=DATA/'candidate/web/public/data';export(db,config,out)
        report['public_documents']=check_public(DATA/'before-public',out)
        validate_public_data(DATA/'candidate')
    report.update(candidate_sha256=sha(candidate), public_hashes={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*.json')})
    immutable_write(DATA/'preview.json',report)
    lines=['# Passing v3 UAH deployment review', '', 'No UAH fitting. Historical tables, original v2 snapshots, all display statistics and raw replays are unchanged. V3 requires whole-map credited/core objective/native parity. All 82 historical display rounds remain; only 42 rounds across four maps contribute to Rating.', '',
           f"Runtime/research maximum difference {report['max_parity_error']:.3g}, {report['parity_comparisons']} comparisons (tracked rounds, maps, season and career).", '',
           '| Player | Rating | Eligible rounds | Maps |', '| --- | ---: | ---: | ---: |']
    for p in report['players']:lines.append(f"| {p['name']} | {p['rating']:.9f} | {p['rounds']} | {p['maps']} |")
    lines+=['','## Whole-map eligibility','','| Map | ID | Eligible | Reason |','| --- | --- | --- | --- |']
    for m in report['maps']:lines.append(f"| {m['map']} | {m['map_id']} | {m['eligible']} | {m['reason'] or 'Complete validated inputs'} |")
    lines+=['','No parser or operator/action-start logic change. Native finisher opening is not credited-owner opening. Legacy trades remain frozen at 8 seconds. Larger independent events, precise credited event ownership/timing, and unsupported objective compatibility remain future work.','']
    (ROOT/'research/output/native-v3-deployment-review.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(report['players'], indent=2));print('PREVIEW parity',report['max_parity_error'], 'comparisons',report['parity_comparisons'])


def apply():
    before=json.loads((DATA/'before.json').read_text(encoding='utf-8'))
    report=json.loads((DATA/'preview.json').read_text(encoding='utf-8'))
    if sha(ROOT/'research/v3-native-order-candidate.json')!=before['model_sha256']:
        raise ValueError('Frozen model changed.')
    if sha(ROOT/'config/settings.json')!=before['settings_sha256']:
        raise ValueError('Settings changed; review before applying.')
    for path, value in before['archive_hashes'].items():
        if sha(ROOT/path)!=value:raise ValueError('Archive changed.')
    with repo.connect(ROOT/'data/r6stats.sqlite') as db:
        if state(db)!=before['tables']:raise ValueError('Historical tables changed.')
        install_evidence(db)
        if state(db)!=before['tables']:raise ValueError('Historical tables modified.')
        current=parity(db)
        if current['players']!=report['players']:raise ValueError('Sanity preview changed.')
        config=json.loads((ROOT/'config/settings.json').read_text(encoding='utf-8'));config['stats']['rating_version']='siege_style_v3'
        export(db,config,ROOT/'web/public/data')
        check_public(DATA/'before-public',ROOT/'web/public/data');validate_public_data(ROOT)
        for path, value in report['public_hashes'].items():
            if sha(ROOT/'web/public/data'/path)!=value:raise ValueError('Export differs from reviewed preview.')
        (ROOT/'config/settings.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    immutable_write(DATA/'applied.json',dict(database_sha256=sha(ROOT/'data/r6stats.sqlite'), preview_sha256=sha(DATA/'preview.json'),historical_tables_unchanged=True))
    print('APPLIED validated v3 sidecar/default/export; all historical tables and v2 snapshots preserved.')


if __name__=='__main__':
    if sys.argv[1:] == ['preview']:preview()
    elif sys.argv[1:] == ['apply']:apply()
    else:raise SystemExit('Use preview or apply; apply only after full tests/builds.')
