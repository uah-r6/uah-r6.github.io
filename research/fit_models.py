"""Event-grouped raw and operator-relative SiegeGG rating experiments.

The September Stage 2 event is reserved. This script never reads its rating
values into a fit or validation calculation.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

from fit_baseline import FEATURES, solve

ROOT = Path(__file__).resolve().parents[1]
OBSERVATIONS = ROOT / "data/research/experiments/player_maps.jsonl"
LOG = ROOT / "research/experiment-log.jsonl"
TRAIN_EVENTS = (
    "Six Invitational 2026",
    "Asia Pacific Kickoff 2026",
    "Salt Lake City Major 2026",
    "Asia Pacific League Stage 1 2026",
    "Europe MENA League Stage 1 2026",
)
VALIDATION_EVENT = "Esports World Cup 2026"
FINAL_EVENT = "Europe MENA League Stage 2 2026"
PRIOR_ROUNDS = 20


def round_features(round_: dict) -> list[float]:
    return [float(round_["kills"]), float(round_["teamkills"]),
            float(max(round_["kills"] - 1, 0)),
            float(round_["opening_kills"] - round_["opening_deaths"]),
            float(round_["clutches"]), float(round_["kost_rounds"]),
            float(round_["survived"]),
            float(round_["deaths_traded"] - round_["kills_traded"]),
            float(round_["plants"] + round_["disables"])]


def means(samples: list[list[float]]) -> list[float]:
    return [sum(row[j] for row in samples) / len(samples) for j in range(len(FEATURES))]


def variances(samples: list[list[float]], centers: list[float]) -> list[float]:
    return [sum((row[j] - centers[j]) ** 2 for row in samples) / len(samples)
            for j in range(len(FEATURES))]


def operator_baselines(train: list[dict], prior_rounds: int = PRIOR_ROUNDS) -> dict:
    by_side = defaultdict(list)
    by_operator = defaultdict(list)
    for player in train:
        for round_ in player["rounds"]:
            values = round_features(round_)
            by_side[round_["side"]].append(values)
            if round_["operator"] != "Unknown":
                by_operator[(round_["side"], round_["operator"])].append(values)
    side = {}
    for key, samples in by_side.items():
        avg = means(samples)
        side[key] = {"n": len(samples), "mean": avg, "variance": variances(samples, avg)}
    operators = {}
    for key, samples in by_operator.items():
        avg = means(samples)
        var = variances(samples, avg)
        prior = side[key[0]]
        weight = len(samples) / (len(samples) + prior_rounds)
        operators[key] = {"n": len(samples),
                          "mean": [weight * a + (1 - weight) * p
                                   for a, p in zip(avg, prior["mean"])],
                          "variance": [weight * a + (1 - weight) * p
                                       for a, p in zip(var, prior["variance"])]}
    return {"side": side, "operators": operators, "prior_rounds": prior_rounds}


def design(row: dict, baselines: dict, method: str) -> list[float]:
    rounds = row["rounds"]
    n = len(rounds)
    if method == "raw":
        return means([round_features(round_) for round_ in rounds])
    residuals = []
    for round_ in rounds:
        baseline = baselines["operators"].get((round_["side"], round_["operator"]),
                                               baselines["side"][round_["side"]])
        values = round_features(round_)
        centered = [value - mean for value, mean in zip(values, baseline["mean"])]
        if method in {"round_z", "segment_z"}:
            centered = [value / max(math.sqrt(var), .1)
                        for value, var in zip(centered, baseline["variance"])]
        residuals.append(centered)
    if method == "segment_z":
        # Each operator segment contributes its average equally. This tests
        # whether per-operator segments, rather than rounds, are the unit.
        segments = defaultdict(list)
        for round_, values in zip(rounds, residuals):
            segments[(round_["side"], round_["operator"])].append(values)
        return means([means(samples) for samples in segments.values()])
    return [sum(values[j] for values in residuals) / n for j in range(len(FEATURES))]


def fit_ridge(rows: list[dict], baselines: dict, method: str, alpha: float = 1.0) -> dict:
    xs = [design(row, baselines, method) for row in rows]
    ys = [row["rating"] for row in rows]
    centers = means(xs)
    scales = [max(math.sqrt(value), 1e-9) for value in variances(xs, centers)]
    matrix = [[1.0] + [(x[j] - centers[j]) / scales[j] for j in range(len(FEATURES))]
              for x in xs]
    count = len(FEATURES) + 1
    gram = [[sum(x[i] * x[j] for x in matrix) + (alpha if i == j and i else 0)
             for j in range(count)] for i in range(count)]
    rhs = [sum(x[i] * y for x, y in zip(matrix, ys)) for i in range(count)]
    solved = solve(gram, rhs)
    return {"method": method, "alpha": alpha, "intercept": solved[0],
            "weights_standardized": dict(zip(FEATURES, solved[1:])),
            "means": dict(zip(FEATURES, centers)),
            "scales": dict(zip(FEATURES, scales))}


def predict(model: dict, row: dict, baselines: dict) -> float:
    values = design(row, baselines, model["method"])
    return model["intercept"] + sum(
        model["weights_standardized"][name] *
        (value - model["means"][name]) / model["scales"][name]
        for name, value in zip(FEATURES, values))


def evaluate(rows: list[dict], guesses: list[float]) -> dict:
    errors = [guess - row["rating"] for row, guess in zip(rows, guesses)]
    out = {"n": len(rows), "mae": sum(abs(e) for e in errors) / len(errors),
           "rmse": math.sqrt(sum(e * e for e in errors) / len(errors)),
           "display_exact": sum(round(g, 2) == r["rating"] for r, g in zip(rows, guesses)) / len(rows),
           "max_abs_error": max(abs(e) for e in errors)}
    for threshold in (.01, .02, .03, .05, .10):
        out[f"within_{threshold:.2f}"] = sum(abs(e) <= threshold for e in errors) / len(errors)
    out["worst"] = sorted(({"event": r["event"], "map": r["map"], "player": r["player"],
                            "actual": r["rating"], "predicted": round(g, 4),
                            "error": round(e, 4)} for r, g, e in zip(rows, guesses, errors)),
                          key=lambda r: abs(r["error"]), reverse=True)[:8]
    return out


def main() -> None:
    source = OBSERVATIONS.read_bytes()
    rows = [json.loads(line) for line in source.splitlines()]
    train = [r for r in rows if r["fit_eligible"] and r["event"] in TRAIN_EVENTS
             and not r["reserved_for_final_test"]]
    validation = [r for r in rows if r["fit_eligible"] and r["event"] == VALIDATION_EVENT
                  and not r["reserved_for_final_test"]]
    final_count = sum(r["fit_eligible"] and r["event"] == FINAL_EVENT
                      and r["reserved_for_final_test"] for r in rows)
    if not train or not validation or not final_count:
        raise ValueError("Train, validation and reserved final events are required")
    baselines = operator_baselines(train)
    candidates = []
    for method in ("raw", "weighted_operator_mean", "round_z", "segment_z"):
        model = fit_ridge(train, baselines, method)
        score = evaluate(validation, [predict(model, r, baselines) for r in validation])
        candidates.append({"model": model, "validation": score})
        print(f"{method}: validation n={score['n']} MAE={score['mae']:.4f} RMSE={score['rmse']:.4f} "
              f"within .05={score['within_0.05']:.0%}")
    collegiate = evaluate(validation, [r["derived"]["rating"] for r in validation])
    chosen = min(candidates, key=lambda entry: entry["validation"]["mae"])
    now = datetime.now(timezone.utc)
    record = {"experiment_id": now.strftime("grouped-operator-%Y%m%dT%H%M%SZ"),
              "created_at": now.isoformat(), "dataset_sha256": hashlib.sha256(source).hexdigest(),
              "dataset_rows": len(rows), "eligible_rows": sum(r["fit_eligible"] for r in rows),
              "train_events": list(TRAIN_EVENTS), "train_rows": len(train),
              "validation_events": [VALIDATION_EVENT], "validation_rows": len(validation),
              "reserved_final_event": FINAL_EVENT, "reserved_final_clean_rows": final_count,
              "final_test_evaluated": False, "operator_resolution": "0 Unknown rounds",
              "operator_counts": {f"{side}/{operator}": value["n"]
                                  for (side, operator), value in sorted(baselines["operators"].items())},
              "operator_prior_rounds": PRIOR_ROUNDS,
              "feature_definitions": {
                  "kpr": "kills/round", "teamkills": "teamkills/round",
                  "multikill": "sum(max(kills_in_round-1,0))/rounds",
                  "opening": "(opening_kills-opening_deaths)/rounds",
                  "clutch": "successful 1vX rounds/rounds", "kost": "KOST rounds/rounds",
                  "survival": "survived rounds/rounds",
                  "trade": "(deaths_traded-kills_traded)/rounds, 8-second window",
                  "objectives": "(plants+disables)/rounds"},
              "models": candidates, "collegiate_v1_validation": collegiate,
              "chosen_by_validation_mae": chosen["model"]["method"],
              "notes": "Exploratory ridge fits. September Stage 2 ratings reserved for one final evaluation. "
                       "Operator means/variances shrink to side baselines with 20 prior rounds; "
                       "each model is fit only on clean earlier-event rows."}
    with LOG.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record) + "\n")
    print(f"selected {chosen['model']['method']}; collegiate validation MAE={collegiate['mae']:.4f}; "
          f"final {final_count} clean rows remain unevaluated")


if __name__ == "__main__":
    main()
