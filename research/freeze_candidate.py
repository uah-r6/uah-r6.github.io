"""Write exact selected research model before the reserved final evaluation."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from expanded_fit import ROOT, OBSERVATIONS, LOG, PLAN as SPLIT, select_groups
from fit_models import predict, evaluate

OUTPUT = ROOT/'research/frozen-rating-candidate.json'
BASELINE = 'expanded-raw-20260930T202146Z'
CV = 'group-cv-20260930T202147Z'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUTPUT.exists():
        raise ValueError('Candidate already frozen; do not overwrite')
    content = OBSERVATIONS.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    records = list(map(json.loads, LOG.read_text().splitlines()))
    baseline = next(r for r in records if r['experiment_id'] == BASELINE)
    cv = next(r for r in records if r['experiment_id'] == CV)
    if digest != baseline['dataset_sha256'] or digest != cv['dataset_sha256']:
        raise ValueError('Dataset/model/CV hashes differ')
    train, dev, held = select_groups(list(map(json.loads, content.splitlines())), SPLIT)
    if (len(train), len(dev), held) != (299, 32, {'Europe MENA League Stage 2 2026': 16,
                                                 'North America League Stage 2 2026': 60}):
        raise ValueError('Unexpected source split')
    model = baseline['model']
    if model['method'] != 'raw' or model['alpha'] != 1 or model['weights_standardized']['objectives'] != 0:
        raise ValueError('Selected model is not the intended raw eight-family baseline')
    august = evaluate(dev, [predict(model, r, {}) for r in dev])
    if abs(august['mae'] - baseline['validation']['mae']) > 1e-12:
        raise ValueError('Saved baseline predictions failed parity')
    record = {
        'name': 'siege-style-raw-v2-research-frozen',
        'status': 'frozen_before_reserved_final_evaluation',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'baseline_experiment_id': BASELINE, 'cv_experiment_id': CV,
        'dataset_sha256': digest,
        'source_manifest_sha256': sha(ROOT/'research/sources.json'),
        'parser_binary_sha256': sha(ROOT/'.local-tools/bin/siege-dissect.exe'),
        'python_adapter_sha256': sha(ROOT/'r6stats/parser/siege_dissect.py'),
        'normalized_observation_code_sha256': sha(ROOT/'research/pipeline.py'),
        'train_events': SPLIT['train_events'], 'train_rows': len(train),
        'development_event': SPLIT['development_validation_event'], 'development_rows': len(dev),
        'excluded_historical_event': SPLIT['historical_final_event'],
        'excluded_reserved_final_event': SPLIT['untouched_final_event'],
        'excluded_event_clean_counts': held,
        'quality_gates': ['complete replay map/score/roster', 'exact public per-player K/D',
                          'matching public round count', 'verified alias where necessary',
                          'no reserved final row in fit or development'],
        'model': model,
        'effective_features': {
            'kpr': 'opponent kills / rounds',
            'teamkills': 'teamkills / rounds',
            'multikill': 'sum(max(opponent kills in round - 1, 0)) / rounds',
            'opening': '(opening opponent kills - opening deaths) / rounds',
            'clutch': 'successful first-sole-survivor 1vX rounds / rounds, X=1..5',
            'kost': 'rounds with kill OR verified player objective OR survival OR traded death / rounds',
            'survival': 'rounds survived / rounds',
            'trade': '(deaths traded - kills traded) / rounds, 8-second inclusive window'},
        'objectives': 'Unavailable: zero player credits in clean training cohort. Saved ninth model coefficient is exactly zero; no public actor labels are inputs.',
        'operator_normalization': 'none; earlier event folds favored raw features',
        'regularization': 'standardize on training rows; ridge alpha=1, unpenalized intercept',
        'development': {'pooled_event_cv': cv['pooled']['raw'], 'august': august},
        'known_limits': ['objective-positive public rows underpredicted in development',
                         'sparse teamkills and 1v3+ clutches',
                         'only four August development maps',
                         '153 of 560 observed rows fail quality gates'],
        'final_test_evaluated': False,
        'selection_report': 'research/output/pre-freeze-review.md'
    }
    OUTPUT.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    print(f"Frozen {BASELINE}, train={len(train)}, August={len(dev)}, NA clean={held[SPLIT['untouched_final_event']]} (ratings not evaluated)")


if __name__ == '__main__':
    main()
