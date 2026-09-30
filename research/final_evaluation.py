"""One-time evaluation of the frozen raw candidate on September Stage 2."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json

from fit_models import (OBSERVATIONS, LOG, FINAL_EVENT, evaluate, predict)


def main() -> None:
    records = [json.loads(line) for line in LOG.read_text(encoding="utf-8").splitlines()]
    if any(record["experiment_id"].startswith("final-stage2-") for record in records):
        raise RuntimeError("September final event has already been evaluated; do not tune on it")
    frozen = next(record for record in reversed(records)
                  if record["experiment_id"].startswith("grouped-operator-"))
    if frozen["chosen_by_validation_mae"] != "raw":
        raise ValueError("Frozen selection is not the raw model")
    source = OBSERVATIONS.read_bytes()
    if hashlib.sha256(source).hexdigest() != frozen["dataset_sha256"]:
        raise ValueError("Dataset changed since model selection; final event remains untouched")
    rows = [json.loads(line) for line in source.splitlines()]
    holdout = [row for row in rows if row["fit_eligible"] and
               row["event"] == FINAL_EVENT and row["reserved_for_final_test"]]
    if not holdout:
        raise ValueError("No clean reserved final rows")
    model = next(item["model"] for item in frozen["models"]
                 if item["model"]["method"] == "raw")
    predictions = [predict(model, row, {}) for row in holdout]
    result = evaluate(holdout, predictions)
    collegiate = evaluate(holdout, [row["derived"]["rating"] for row in holdout])
    by_map = {}
    for folder in sorted({row["replay_folder"] for row in holdout}):
        indices = [i for i, row in enumerate(holdout) if row["replay_folder"] == folder]
        by_map[folder] = evaluate([holdout[i] for i in indices], [predictions[i] for i in indices])
    now = datetime.now(timezone.utc)
    record = {"experiment_id": now.strftime("final-stage2-%Y%m%dT%H%M%SZ"),
              "created_at": now.isoformat(), "frozen_model_experiment_id": frozen["experiment_id"],
              "dataset_sha256": frozen["dataset_sha256"], "event": FINAL_EVENT,
              "model": "raw nine-family ridge", "n": len(holdout),
              "candidate": result, "collegiate_v1": collegiate,
              "by_map": by_map, "final_test_evaluated": True,
              "note": "One evaluation only. Do not tune the model using these rows."}
    with LOG.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record) + "\n")
    print(f"September final {len(holdout)} rows across {len(by_map)} maps: "
          f"raw MAE={result['mae']:.4f}, RMSE={result['rmse']:.4f}, "
          f"within .05={result['within_0.05']:.0%}, max={result['max_abs_error']:.4f}; "
          f"collegiate_v1 MAE={collegiate['mae']:.4f}")


if __name__ == "__main__":
    main()
