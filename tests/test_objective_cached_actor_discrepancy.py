"""Keep replay-only prediction separate from a disputed public target label."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research'))
from objective_combined_candidate import combine


def test_chalet_actor_is_unchanged_after_independent_broadcast_review():
    case = json.loads((Path(__file__).parent / 'fixtures/objective-cached-actor-discrepancy.json').read_text(encoding='utf-8'))
    # Official frames show kyno planting; preserve the original contradictory
    # public Fultz label and failed primary grading rather than silently fixing it.
    assert case['original_public_label'] == 'Fultz plants defuser'
    assert case['original_primary_verdict'] == 'incorrect'
    actor, mode, context = combine(**{k:case[k] for k in ('row','deaths','timers','body','full_feedback','previous_state')})
    assert (actor,mode) == ('kyno','standalone_clock_with_body_guard')
    assert context['sole_proposal'] is None
    assert context['score_interval']['state_tick'] == 44
