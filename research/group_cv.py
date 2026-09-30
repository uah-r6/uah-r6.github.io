"""Development-only leave-one-event-out checks on pre-August events."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json

from expanded_fit import LOG, OBSERVATIONS, PLAN, select_groups
from fit_models import evaluate, fit_ridge, operator_baselines, predict

METHODS = ("raw", "weighted_operator_mean", "round_z", "segment_z")


def main() -> None:
    content = OBSERVATIONS.read_bytes()
    rows = [json.loads(line) for line in content.splitlines()]
    development, _, held_out = select_groups(rows, PLAN)
    digest = hashlib.sha256(content).hexdigest()
    kind = "pre-august-leave-one-event-out"
    if any(row.get("experiment_kind") == kind and row.get("dataset_sha256") == digest
           for row in map(json.loads, LOG.read_text(encoding="utf-8").splitlines())):
        raise ValueError("This dataset already has the grouped development check")
    folds = []
    pooled = {method: {"rows": [], "predictions": []} for method in METHODS}
    for event in PLAN["train_events"]:
        validation = [row for row in development if row["event"] == event]
        train = [row for row in development if row["event"] != event]
        if not train or not validation:
            raise ValueError(f"Missing group for event {event}")
        baselines = operator_baselines(train)
        known_operators = set(baselines["operators"])
        unseen_operator_rounds = sum(
            (round_["side"], round_["operator"]) not in known_operators
            for row in validation for round_ in row["rounds"])
        results = {}
        for method in METHODS:
            model = fit_ridge(train, baselines, method, alpha=1.0)
            guesses = [predict(model, row, baselines) for row in validation]
            results[method] = evaluate(validation, guesses)
            pooled[method]["rows"].extend(validation)
            pooled[method]["predictions"].extend(guesses)
        folds.append({"event": event, "train_rows": len(train),
                      "validation_rows": len(validation),
                      "train_teamkill_events": sum(row["derived"]["teamkills"] for row in train),
                      "unseen_operator_rounds": unseen_operator_rounds,
                      "validation_operator_rounds": sum(len(row["rounds"]) for row in validation),
                      "models": results})
    pooled_results = {method: evaluate(values["rows"], values["predictions"])
                      for method, values in pooled.items()}
    full_baselines = operator_baselines(development)
    operator_counts = Counter(value["n"] < 20 for value in full_baselines["operators"].values())
    now = datetime.now(timezone.utc)
    record = {"experiment_id": now.strftime("group-cv-%Y%m%dT%H%M%SZ"),
              "experiment_kind": kind, "created_at": now.isoformat(),
              "dataset_sha256": digest, "development_events": PLAN["train_events"],
              "development_rows": len(development), "held_out_clean_rows": held_out,
              "methods": METHODS, "operator_prior_rounds": 20,
              "full_train_operator_counts": {
                  "total": len(full_baselines["operators"]),
                  "under_20_rounds": operator_counts[True],
                  "at_least_20_rounds": operator_counts[False]},
              "folds": folds, "pooled": pooled_results,
              "final_test_evaluated": False,
              "note": "Every fold trains and derives operator baselines on six pre-August events and validates on the seventh. August and both September events are never scored here."}
    with LOG.open("a", encoding="utf-8") as output:
        output.write(json.dumps(record) + "\n")
    print(json.dumps({"experiment_id": record["experiment_id"],
                      "development_rows": len(development),
                      "held_out_clean_rows": held_out,
                      "operator_counts": record["full_train_operator_counts"],
                      "pooled_mae": {method: score["mae"] for method, score in pooled_results.items()},
                      "fold_mae": {fold["event"]: {method: score["mae"]
                                                       for method, score in fold["models"].items()}
                                   for fold in folds}}, indent=2))


if __name__ == "__main__":
    main()
