"""Exploratory nine-family raw baseline, grouped by independent events.

This intentionally does not produce a deployable model. The small sample and
missing Y11 operator snapshots make operator-relative baselines untrustworthy.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/research/experiments"
FEATURES = ("kpr", "teamkills", "multikill", "opening", "clutch", "kost",
            "survival", "trade", "objectives")


def features(row: dict) -> list[float]:
    s = row["derived"]
    n = s["rounds"]
    multikill = sum(max(r["kills"] - 1, 0) for r in row["rounds"]) / n
    return [s["kills"] / n, s["teamkills"] / n, multikill,
            (s["opening_kills"] - s["opening_deaths"]) / n,
            s["clutches"] / n, s["kost_rounds"] / n, s["survived"] / n,
            (s["deaths_traded"] - s["kills_traded"]) / n,
            (s["plants"] + s["disables"]) / n]


def solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Small dense Gaussian solve with pivoting; no app dependency on numpy."""
    augmented = [row[:] + [value] for row, value in zip(matrix, vector)]
    size = len(vector)
    for col in range(size):
        pivot = max(range(col, size), key=lambda i: abs(augmented[i][col]))
        augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
        if abs(augmented[col][col]) < 1e-12:
            raise ValueError("Singular design matrix")
        scale = augmented[col][col]
        augmented[col] = [v / scale for v in augmented[col]]
        for row in range(size):
            if row == col:
                continue
            factor = augmented[row][col]
            augmented[row] = [a - factor * b for a, b in zip(augmented[row], augmented[col])]
    return [row[-1] for row in augmented]


def fit(rows: list[dict], alpha: float = 1.0) -> dict:
    xs = [features(r) for r in rows]
    ys = [r["rating"] for r in rows]
    means = [sum(x[j] for x in xs) / len(xs) for j in range(len(FEATURES))]
    scales = [math.sqrt(sum((x[j] - means[j]) ** 2 for x in xs) / len(xs)) or 1.0
              for j in range(len(FEATURES))]
    design = [[1.0] + [(x[j] - means[j]) / scales[j] for j in range(len(FEATURES))]
              for x in xs]
    cols = len(FEATURES) + 1
    gram = [[sum(x[i] * x[j] for x in design) + (alpha if i == j and i else 0.0)
             for j in range(cols)] for i in range(cols)]
    rhs = [sum(x[i] * y for x, y in zip(design, ys)) for i in range(cols)]
    coefficients = solve(gram, rhs)
    return {"alpha": alpha, "intercept_standardized": coefficients[0],
            "weights_standardized": dict(zip(FEATURES, coefficients[1:])),
            "means": dict(zip(FEATURES, means)), "scales": dict(zip(FEATURES, scales))}


def predict(model: dict, row: dict) -> float:
    values = features(row)
    return model["intercept_standardized"] + sum(
        model["weights_standardized"][name] *
        (value - model["means"][name]) / model["scales"][name]
        for name, value in zip(FEATURES, values))


def metrics(rows: list[dict], guesses: list[float]) -> dict:
    errors = [guess - row["rating"] for row, guess in zip(rows, guesses)]
    return {"n": len(rows), "mae": sum(map(abs, errors)) / len(errors),
            "rmse": math.sqrt(sum(e * e for e in errors) / len(errors)),
            "display_exact": sum(round(g, 2) == r["rating"] for r, g in zip(rows, guesses)) / len(rows),
            "within_0_01": sum(abs(e) <= .01 for e in errors) / len(errors),
            "within_0_02": sum(abs(e) <= .02 for e in errors) / len(errors),
            "within_0_05": sum(abs(e) <= .05 for e in errors) / len(errors)}


def main() -> None:
    rows = [json.loads(line) for line in (DATA / "player_maps.jsonl").read_text().splitlines()]
    eligible = [row for row in rows if row["fit_eligible"]]
    train_event = "Asia Pacific Kickoff 2026"
    validation_event = "Six Invitational 2026"
    test_event = "Asia Pacific League Stage 1 2026"
    train = [row for row in eligible if row["event"] == train_event]
    validation = [row for row in eligible if row["event"] == validation_event]
    test = [row for row in eligible if row["event"] == test_event]
    if not train or not validation or not test:
        raise ValueError("Training, validation and independent test events are required")
    model = fit(train)
    experiments = [{"train_events": [train_event], "validation_event": validation_event,
                    "test_event": test_event, "train_n": len(train),
                    "validation": metrics(validation, [predict(model, r) for r in validation]),
                    "test": metrics(test, [predict(model, r) for r in test]),
                    "collegiate_v1_validation": metrics(validation,
                        [r["derived"]["rating"] for r in validation]),
                    "collegiate_v1_test": metrics(test,
                        [r["derived"]["rating"] for r in test]),
                    "model": model}]
    record = {"experiment_id": datetime.now(timezone.utc).strftime("raw-nine-%Y%m%dT%H%M%SZ"),
              "created_at": datetime.now(timezone.utc).isoformat(),
              "dataset_rows": len(rows), "eligible_rows": len(eligible),
              "features": list(FEATURES), "trade_window_seconds": 8,
              "multikill_definition": "sum(max(kills_in_round - 1, 0)) / rounds",
              "clutch_definition": "all successful 1vX clutches / rounds",
              "operator_normalization": "none", "model_type": "ridge, standardized, alpha=1",
              "test_set": test_event, "notes": "Exploratory only: held-out test has five rows from one map. "
                       "Rows require exact public K/D and round count; other metric definitions can differ.",
              "folds": experiments}
    log = DATA / "experiment-log.jsonl"
    with log.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")
    print(f"{record['experiment_id']}: {len(eligible)}/{len(rows)} rows")
    fold = experiments[0]
    for name in ("validation", "test"):
        result = fold[name]
        print(f"  {name} ({result['n']} rows): raw MAE {result['mae']:.3f}; "
              f"collegiate_v1 MAE {fold['collegiate_v1_' + name]['mae']:.3f}; "
              f"within .05 {result['within_0_05']:.0%}")


if __name__ == "__main__":
    main()
