"""Run the preregistered expanded raw development fit, without final-event ratings."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from fit_models import FEATURES, evaluate, fit_ridge, predict

ROOT = Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / "research/expanded-fit-plan.json").read_text(encoding="utf-8"))
OBSERVATIONS = ROOT / "data/research/experiments/player_maps.jsonl"
LOG = ROOT / "research/experiment-log.jsonl"


def select_groups(rows: list[dict], plan: dict) -> tuple[list[dict], list[dict], dict]:
    known = set(plan["train_events"]) | {plan["development_validation_event"],
            plan["historical_final_event"], plan["untouched_final_event"]}
    unknown = {row["event"] for row in rows} - known
    if unknown:
        raise ValueError(f"Unclassified research events: {sorted(unknown)}")
    train = [row for row in rows if row["fit_eligible"] and
             row["event"] in plan["train_events"] and not row["reserved_for_final_test"]]
    validation = [row for row in rows if row["fit_eligible"] and
                  row["event"] == plan["development_validation_event"] and
                  not row["reserved_for_final_test"]]
    if not train or not validation:
        raise ValueError("Training and development validation must both contain clean rows")
    if any(row["reserved_for_final_test"] for row in train + validation):
        raise ValueError("Reserved final event entered model development")
    return train, validation, {event: sum(row["fit_eligible"] for row in rows
                                          if row["event"] == event)
                               for event in (plan["historical_final_event"],
                                             plan["untouched_final_event"])}


def raw_slopes(model: dict) -> dict[str, float]:
    return {name: model["weights_standardized"][name] / model["scales"][name]
            for name in FEATURES}


def main(plan: dict | None = None) -> None:
    plan = plan or PLAN
    content = OBSERVATIONS.read_bytes()
    rows = [json.loads(line) for line in content.splitlines()]
    train, validation, held_out = select_groups(rows, plan)
    previous = next(row for row in map(json.loads, LOG.read_text(encoding="utf-8").splitlines())
                    if row.get("experiment_id") == plan["prior_experiment_id"])
    prior_model = (previous["model"] if "model" in previous else
                   next(row["model"] for row in previous["models"]
                        if row["model"]["method"] == "raw"))
    digest = hashlib.sha256(content).hexdigest()
    if plan.get("expected_dataset_sha256") and digest != plan["expected_dataset_sha256"]:
        raise ValueError("Dataset changed after this development experiment was planned")
    if plan.get("expected_train_rows") and len(train) != plan["expected_train_rows"]:
        raise ValueError("Training row count changed after this experiment was planned")
    if plan.get("expected_validation_rows") and len(validation) != plan["expected_validation_rows"]:
        raise ValueError("Validation row count changed after this experiment was planned")
    if any(row.get("experiment_kind") == plan["name"] and row.get("dataset_sha256") == digest
           for row in map(json.loads, LOG.read_text(encoding="utf-8").splitlines())):
        raise ValueError("This dataset already has an expanded raw fit; do not duplicate the experiment")
    model = fit_ridge(train, {}, "raw", alpha=float(plan.get("alpha", 1.0)))
    validation_metrics = evaluate(validation, [predict(model, row, {}) for row in validation])
    prior_metrics = evaluate(validation, [predict(prior_model, row, {}) for row in validation])
    collegiate = evaluate(validation, [row["derived"]["rating"] for row in validation])
    old_slopes, new_slopes = raw_slopes(prior_model), raw_slopes(model)
    now = datetime.now(timezone.utc)
    record = {
        "experiment_id": now.strftime("expanded-raw-%Y%m%dT%H%M%SZ"),
        "experiment_kind": plan["name"], "created_at": now.isoformat(),
        "dataset_sha256": digest, "train_events": plan["train_events"],
        "train_rows": len(train), "validation_event": plan["development_validation_event"],
        "validation_rows": len(validation), "held_out_clean_rows": held_out,
        "train_teamkill_player_maps": sum(row["derived"]["teamkills"] > 0 for row in train),
        "train_teamkill_events": sum(row["derived"]["teamkills"] for row in train),
        "model": model, "validation": validation_metrics,
        "prior_model_validation": prior_metrics, "collegiate_v1_validation": collegiate,
        "prior_experiment_id": plan["prior_experiment_id"],
        "raw_unit_slopes": new_slopes,
        "prior_raw_unit_slopes": old_slopes,
        "raw_unit_slope_changes": {name: new_slopes[name] - old_slopes[name]
                                   for name in FEATURES},
        "final_test_evaluated": False,
        "note": plan.get("note", "Fixed raw development fit. Both September events excluded. August EWC was previously viewed, so its validation is not an untouched test.")
    }
    with LOG.open("a", encoding="utf-8") as output:
        output.write(json.dumps(record) + "\n")
    print(json.dumps({key: record[key] for key in (
        "experiment_id", "train_rows", "validation_rows", "held_out_clean_rows",
        "train_teamkill_events", "raw_unit_slopes", "raw_unit_slope_changes")}, indent=2))
    print("August development MAE:", round(validation_metrics["mae"], 4),
          "prior:", round(prior_metrics["mae"], 4),
          "collegiate:", round(collegiate["mae"], 4))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=None)
    args = parser.parse_args()
    main(json.loads(args.plan.read_text(encoding="utf-8")) if args.plan else None)
