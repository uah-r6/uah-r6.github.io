"""Controlled, event-held-out comparisons of rating metric definitions.

Select a definition using cross-validation among pre-August events. August is
read once for the selected definition; September ratings remain unused.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from r6stats.parser.models import Match  # noqa: E402
from r6stats.stats.calculate import calculate_match  # noqa: E402
from fit_models import (FEATURES, TRAIN_EVENTS, VALIDATION_EVENT, FINAL_EVENT,
                        OBSERVATIONS, LOG, round_features, means, variances, evaluate)  # noqa: E402
from fit_baseline import solve  # noqa: E402

VARIANTS = ("baseline", "trade_ratio", "trade_refrags", "trade_window_5",
            "trade_window_6", "trade_window_7", "trade_window_10",
            "multikill_binary", "multikill_levels", "opening_separate",
            "clutch_weighted", "objectives_separate")


class FeatureSource:
    def __init__(self) -> None:
        self.matches = {}
        self.stats = {}

    def window_stats(self, row: dict, window: int) -> dict:
        folder = row["replay_folder"]
        if folder not in self.matches:
            self.matches[folder] = Match.from_dict(json.loads(
                (ROOT / "data/research/derived" / f"{folder}.json").read_text(encoding="utf-8")))
        key = (folder, window)
        if key not in self.stats:
            self.stats[key] = calculate_match(self.matches[folder], trade_window_seconds=window)
        player = next(p for p in self.matches[folder].rounds[0].players
                      if p.username == row["player"])
        return self.stats[key][player.key]

    def vector(self, row: dict, variant: str) -> list[float]:
        rounds = row["rounds"]
        n = len(rounds)
        values = means([round_features(round_) for round_ in rounds])
        stats = row["derived"]
        if variant == "baseline":
            pass
        elif variant == "trade_ratio":
            values[7] = (stats["deaths_traded"] / stats["deaths"] if stats["deaths"] else 0) - (
                stats["kills_traded"] / stats["kills"] if stats["kills"] else 0)
        elif variant == "trade_refrags":
            values[7] = (stats["refrag_kills"] - stats["kills_traded"]) / n
        elif variant.startswith("trade_window_"):
            alternate = self.window_stats(row, int(variant.rsplit("_", 1)[1]))
            values[7] = (alternate["deaths_traded"] - alternate["kills_traded"]) / n
        elif variant == "multikill_binary":
            values[2] = sum(round_["kills"] >= 2 for round_ in rounds) / n
        elif variant == "multikill_levels":
            levels = [sum(round_["kills"] == size for round_ in rounds) / n
                      for size in (2, 3, 4, 5)]
            values = values[:2] + levels + values[3:]
        elif variant == "opening_separate":
            values = values[:3] + [stats["opening_kills"] / n, -stats["opening_deaths"] / n] + values[4:]
        elif variant == "clutch_weighted":
            values[4] = sum(size * stats[f"clutch_1v{size}"] for size in range(1, 6)) / n
        elif variant == "objectives_separate":
            values = values[:8] + [stats["plants"] / n, stats["disables"] / n]
        else:
            raise ValueError(variant)
        return values


def ridge(train: list[dict], source: FeatureSource, variant: str) -> dict:
    xs = [source.vector(row, variant) for row in train]
    ys = [row["rating"] for row in train]
    centers = means(xs) if len(xs[0]) == len(FEATURES) else [sum(x[j] for x in xs) / len(xs)
                                                         for j in range(len(xs[0]))]
    scales = [max(math.sqrt(sum((x[j] - centers[j]) ** 2 for x in xs) / len(xs)), 1e-9)
              for j in range(len(centers))]
    matrix = [[1.0] + [(x[j] - centers[j]) / scales[j] for j in range(len(centers))] for x in xs]
    count = len(centers) + 1
    gram = [[sum(x[i] * x[j] for x in matrix) + (1 if i == j and i else 0)
             for j in range(count)] for i in range(count)]
    rhs = [sum(x[i] * y for x, y in zip(matrix, ys)) for i in range(count)]
    solved = solve(gram, rhs)
    return {"variant": variant, "intercept": solved[0], "weights": solved[1:],
            "centers": centers, "scales": scales, "alpha": 1.0}


def predict(model: dict, row: dict, source: FeatureSource) -> float:
    xs = source.vector(row, model["variant"])
    return model["intercept"] + sum(w * (value - center) / scale
                                    for w, value, center, scale in zip(
                                        model["weights"], xs, model["centers"], model["scales"]))


def main() -> None:
    data = OBSERVATIONS.read_bytes()
    rows = [json.loads(line) for line in data.splitlines()]
    early = [r for r in rows if r["fit_eligible"] and r["event"] in TRAIN_EVENTS
             and not r["reserved_for_final_test"]]
    validation = [r for r in rows if r["fit_eligible"] and r["event"] == VALIDATION_EVENT
                  and not r["reserved_for_final_test"]]
    final_n = sum(r["fit_eligible"] and r["event"] == FINAL_EVENT
                  and r["reserved_for_final_test"] for r in rows)
    source = FeatureSource()
    candidates = []
    for variant in VARIANTS:
        folds = []
        for event in TRAIN_EVENTS:
            fit_rows = [r for r in early if r["event"] != event]
            holdout = [r for r in early if r["event"] == event]
            model = ridge(fit_rows, source, variant)
            score = evaluate(holdout, [predict(model, row, source) for row in holdout])
            folds.append({"event": event, "n": len(holdout), "mae": score["mae"],
                          "rmse": score["rmse"]})
        pooled_mae = sum(fold["mae"] * fold["n"] for fold in folds) / len(early)
        candidates.append({"variant": variant, "pooled_cv_mae": pooled_mae, "folds": folds})
        print(f"{variant}: event CV MAE {pooled_mae:.4f}")
    selected = min(candidates, key=lambda item: item["pooled_cv_mae"])
    # The validation event is used only after the definition was selected.
    validated = {}
    for variant in ("baseline", selected["variant"]):
        model = ridge(early, source, variant)
        validated[variant] = {"model": model,
                              "score": evaluate(validation, [predict(model, r, source)
                                                             for r in validation])}
    now = datetime.now(timezone.utc)
    record = {"experiment_id": now.strftime("metric-definitions-%Y%m%dT%H%M%SZ"),
              "created_at": now.isoformat(), "dataset_sha256": hashlib.sha256(data).hexdigest(),
              "train_events": list(TRAIN_EVENTS), "train_rows": len(early),
              "validation_event": VALIDATION_EVENT, "validation_rows": len(validation),
              "reserved_final_event": FINAL_EVENT, "reserved_final_clean_rows": final_n,
              "final_test_evaluated": False, "trade_window_baseline_seconds": 8,
              "candidate_definitions": list(VARIANTS), "selection": "minimum pooled event CV MAE",
              "candidates": candidates, "chosen_variant": selected["variant"],
              "validation_after_selection": validated,
              "notes": "One-family-at-a-time variants. No combination search; September ratings remain unseen."}
    with LOG.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record) + "\n")
    for name, details in validated.items():
        score = details["score"]
        print(f"validation {name}: n={score['n']} MAE={score['mae']:.4f} RMSE={score['rmse']:.4f}")
    print(f"selected {selected['variant']}; final {final_n} rows remain unevaluated")


if __name__ == "__main__":
    main()
