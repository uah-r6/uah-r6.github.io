"""Write the exact dependency manifest before the local diagnostic freeze."""
import json

from objective_combined_reserve import digest
from objective_transition_probe import ROOT


FILES = [
    'research/objective_combined_candidate.py','research/objective_combined_reserve.py',
    'research/objective_clock_candidate.py','research/objective_disable_structure.py',
    'research/objective_actor_liveness.py','research/objective_timer_audit.py',
    'research/objective_score_structure.py','research/objective_score_identity.py',
    'research/objective_score_ledger.py','research/objective_encoding_probe.py',
    'research/objective_production_check.py','research/objective_transition_probe.py',
    'research/objective_state_components.py','research/objective_score_delta_validation.py',
    'research/state_component_probe.go','research/score_structure_probe.go','research/actor_feedback_probe.go',
    'research/objective-actor-reserve.json','research/objective-combined-plan.md',
    '.local-tools/bin/siege-dissect.exe','.local-tools/bin/siege-dissect-objectives.exe',
    '.local-tools/bin/state-component-probe.exe','.local-tools/bin/score-structure-probe.exe',
    '.local-tools/bin/actor-feedback-probe.exe',
]


if __name__=='__main__':
    path = ROOT/'research/objective-combined-freeze.json'
    if path.exists():
        raise SystemExit('An existing freeze manifest cannot be overwritten')
    path.write_text(json.dumps(dict(status='frozen_for_local_diagnostic_validation',
                                   source_hash_normalization='CRLF to LF; binary hashes use exact bytes',
                                   consumed_counts=dict(development=dict(plant=[39,0,22],disable=[1,0,7]),
                                                        extension=dict(plant=[25,0,7],disable=[3,0,9])),
                                   gates=dict(python_passed=144,python_skipped=1,subtests_passed=6,
                                              go_dissect_tests=True,go_vet=True,research_component_tests=True,
                                              control_4139_R07='unresolved',control_3563_6675_R02='unresolved'),
                                   sha256={name:digest(ROOT/name) for name in FILES}),indent=2)+'\n',encoding='utf-8')
    print(path)
