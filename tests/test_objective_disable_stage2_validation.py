"""A small/all-abstain reserve cannot imply sufficient production evidence."""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from objective_disable_stage2_validation import acceptance


def rows(n=5):
    return [dict(proposal='player',verdict='correct',game_id=i%3) for i in range(n)]


def test_insufficient_named_or_map_coverage():
    assert acceptance([],[])[1]=='insufficient_named_disables_or_maps'
    assert acceptance(rows(4),[])[1]=='insufficient_named_disables_or_maps'
    assert not acceptance([r|dict(game_id=1) for r in rows()],[])[0]


def test_wrong_actor_and_occurrence_mismatch_fail_even_with_coverage():
    assert acceptance(rows()+[dict(proposal='wrong',verdict='incorrect',game_id=4)],[])[1]=='primary_actor_disagreement_or_identity_unknown'
    assert acceptance(rows(),[dict(error='extra')])[1]=='occurrence_mismatch'
    assert acceptance(rows()+[dict(proposal='unknown',verdict='identity_review',game_id=4)],[])[0] is False


def test_valid_coverage_is_research_gate_only():
    assert acceptance(rows(),[])==(True,'predeclared_research_gate_met_not_production_approval')
