"""Checks for the exploratory research feature and operator-baseline code."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from fit_baseline import features  # noqa: E402
from fit_models import design, operator_baselines  # noqa: E402
from pipeline import canonical_map  # noqa: E402


def make_round(operator, kills=0, side="Attack"):
    return {"operator": operator, "side": side, "kills": kills,
            "teamkills": 0, "opening_kills": 0, "opening_deaths": 0,
            "clutches": 0, "kost_rounds": 0, "survived": 0,
            "deaths_traded": 0, "kills_traded": 0, "plants": 0,
            "disables": 0}


def test_raw_round_design_matches_existing_aggregate_features():
    rounds = [make_round("Ace", 2), make_round("Ace", 1)]
    rounds[0].update(opening_kills=1, kost_rounds=1, survived=1, plants=1)
    rounds[1].update(deaths_traded=1, clutches=1, kost_rounds=1)
    aggregate = {"rounds": 2, "kills": 3, "teamkills": 0,
                 "opening_kills": 1, "opening_deaths": 0,
                 "clutches": 1, "kost_rounds": 2, "survived": 1,
                 "deaths_traded": 1, "kills_traded": 0,
                 "plants": 1, "disables": 0}
    row = {"rounds": rounds, "derived": aggregate}

    assert design(row, {}, "raw") == features(row)


def test_sparse_operator_mean_shrinks_to_side_prior():
    train = [{"rounds": [make_round("Ace", 2), make_round("Ash", 0)]}]
    baseline = operator_baselines(train, prior_rounds=2)

    assert baseline["side"]["Attack"]["mean"][0] == 1
    assert baseline["operators"]["Attack", "Ace"]["n"] == 1
    assert baseline["operators"]["Attack", "Ace"]["mean"][0] == pytest.approx(4 / 3)
    assert baseline["operators"]["Attack", "Ash"]["mean"][0] == pytest.approx(2 / 3)


def test_public_and_replay_kafe_names_match():
    assert canonical_map("Kafe Dostoyevsky") == canonical_map("Kafe")
    assert canonical_map("Bank") != canonical_map("Border")
