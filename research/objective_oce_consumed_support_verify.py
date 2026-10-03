"""Verify additive OCE support evidence without collection or reevaluation."""
import json

from objective_bonus_body_oce_review import verify_prelabel
from objective_oce_consumed_identity_review import verify as verify_identities
from objective_bonus_body_asia_identity_review import verify_preserved
from v3_final_pipeline import verify as verify_v3_first
from v3_corrected_final_pipeline import verify as verify_v3_second
from v3_consumed_cohort_integrity import PERMANENT_RESULTS
from v3_final_reserve import ROOT, sha, source_sha
from uah_guarded_actor_readonly import snapshot


def main():
    frozen, _, _ = verify_prelabel()
    verify_identities()
    verify_preserved()
    verify_v3_first()
    verify_v3_second()
    for name, digest in PERMANENT_RESULTS.items():
        if sha(ROOT/name) != digest:
            raise ValueError('Permanent failed final result changed')
    for filename in ('research/objective-oce-consumed-lifecycle-checkpoint.json',
                     'research/objective-oce-consumed-hud-checkpoint.json'):
        checkpoint = json.loads((ROOT/filename).read_text(encoding='utf-8'))
        for name, digest in checkpoint['result_hashes'].items():
            if sha(ROOT/name) != digest:
                raise ValueError('Consumed support output changed: '+name)
        for name, digest in checkpoint['source_hashes'].items():
            if source_sha(ROOT/name) != digest:
                raise ValueError('Consumed support source/labels changed: '+name)
    permanent = json.loads((ROOT/'research/objective-bonus-body-oce-permanent-result-checkpoint.json').read_text(encoding='utf-8'))
    if sha(ROOT/'data/research/objective-bonus-body-oce-cohort/one-shot-primary-result.json') != permanent['result_sha256']:
        raise ValueError('Permanent OCE result changed')
    protected = snapshot()
    if protected != frozen['protected_hashes']:
        raise ValueError('Protected live files changed')
    print('Verified additive consumed support, all frozen actor/v3 sources/binaries/results, and',
          len(protected), 'protected SQLite/archive/public files; no collection/evaluation/write')


if __name__ == '__main__':
    main()
