"""Freeze research selector/adapter dependencies before new disable labels."""
import json

from objective_cached_map_validation import digest
from objective_transition_probe import ROOT


def main():
    destination=ROOT/'research/objective-disable-stage2-freeze.json'
    if destination.exists(): raise ValueError('Existing freeze must never be overwritten')
    original=json.loads((ROOT/'research/objective-combined-freeze.json').read_text(encoding='utf-8'))
    for name,sha in original['sha256'].items():
        if digest(ROOT/name)!=sha: raise ValueError('Original A dependency changed: '+name)
    # Freeze the full existing research Python surface, including imported
    # transitive helpers, rather than an incomplete hand-picked import graph.
    paths=list((ROOT/'research').glob('*.py'))
    paths += [ROOT/name for name in (
        'research/objective-disable-stage2-reserve.json','research/objective-disable-stage2-plan.md',
        'research/sources.json','research/objective-combined-freeze.json',
        'research/actor_feedback_probe.go','research/state_component_probe.go',
        'tests/test_objective_disable_owner_candidate.py','tests/test_objective_disable_owner_real_controls.py',
        'tests/test_objective_disable_stage2_validation.py','tests/fixtures/objective-disable-owner.json',
        'tests/test_objective_player_component_fields.py','tests/test_objective_timer_component_episodes.py',
        'tests/test_objective_timer_real_component_controls.py','tests/fixtures/objective-timer-components.json',
        '.local-tools/bin/siege-dissect.exe','.local-tools/bin/siege-dissect-objectives.exe',
        '.local-tools/bin/actor-feedback-probe.exe','.local-tools/bin/state-component-probe.exe')]
    relative=sorted({p.relative_to(ROOT).as_posix() for p in paths})
    frozen=dict(status='frozen_disable_only_actor_research',
        source_hash_normalization='CRLF to LF for source; exact binary/replay bytes',
        candidate_source_checkpoint='a39c466',consumed_primary_counts=dict(disable=[24,3,0],no_public_disable_proposals=0),
        reviewed_source_discrepancies=['njr/J9O','handyy/VITAKING','Loira/Dias'],
        gates=dict(python_passed=199,python_skipped=1,subtests_passed=6,go_dissect_tests=True,go_vet=True,
                   mandatory_4139_R07='unsupported_plant_unresolved',
                   original_3563_R02='originalA_unresolved_new_primary_source_review_separate'),
        acceptance=dict(minimum_named_disables=5,minimum_named_maps=3,primary_wrong_allowed=0,occurrence_errors_allowed=0),
        original_immutable_results=[f'data/research/diagnostics/{directory}/result.json' for directory in
                                   ('objective-combined-reserve','objective-si-final-validation','objective-cached-map-validation')],
        sha256={name:digest(ROOT/name) for name in relative})
    destination.write_text(json.dumps(frozen,indent=2)+'\n',encoding='utf-8')
    print('Frozen dependency files',len(relative))


if __name__=='__main__':
    main()
