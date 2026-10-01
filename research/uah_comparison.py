"""Read-only UAH map/season comparison for the exploratory raw model."""
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from r6stats.parser.models import Match  # noqa: E402
from r6stats.stats.calculate import calculate_match  # noqa: E402
from fit_models import FEATURES, design, predict  # noqa: E402

LOG = ROOT / "research/experiment-log.jsonl"
OUTPUT = ROOT / "research/uah_comparison.md"


def contribution(model: dict, row: dict) -> dict[str, float]:
    values = design(row, {}, "raw")
    return {name: model["weights_standardized"][name] *
            (value - model["means"][name]) / model["scales"][name]
            for name, value in zip(FEATURES, values)}


def player_rounds(match: Match, player_key: str) -> list[dict]:
    rows = []
    for round_ in match.rounds:
        participant = next(p for p in round_.players if p.key == player_key)
        stats = calculate_match(Match(match.replay_id, match.timestamp, match.map_name,
                                      match.match_type, match.game_mode, [round_]))[player_key]
        rows.append({"number": round_.number, "operator": participant.operator,
                     "side": participant.side, "winner": participant.team == round_.winner,
                     **{name: stats[name] for name in (
                         "kills", "deaths", "teamkills", "opening_kills", "opening_deaths",
                         "clutches", "clutch_1v1", "clutch_1v2", "clutch_1v3",
                         "clutch_1v4", "clutch_1v5", "kost_rounds", "survived",
                         "kills_traded", "deaths_traded", "plants", "disables")}})
    return rows


def main() -> None:
    experiments = [json.loads(line) for line in LOG.read_text(encoding="utf-8").splitlines()]
    experiment = next(row for row in reversed(experiments)
                      if row["experiment_id"].startswith("grouped-operator-"))
    model = next(row["model"] for row in experiment["models"]
                 if row["model"]["method"] == "raw")
    connection = sqlite3.connect(f"file:{ROOT / 'data/r6stats.sqlite'}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    players = {row["profile_id"]: row["display_name"] for row in connection.execute(
        "SELECT profile_id,display_name FROM players WHERE profile_id IS NOT NULL")}
    maps = list(connection.execute("""SELECT m.id,m.map_name,m.our_team,m.normalized_json,
                                    s.season_id,t.name season_name FROM maps m
                                    JOIN series s ON s.id=m.series_id
                                    JOIN seasons t ON t.id=s.season_id
                                    WHERE s.competition='NECC' AND s.demo=0
                                    ORDER BY m.played_on,m.id"""))
    if not maps:
        raise ValueError("No stored NECC maps")
    all_rounds = defaultdict(list)
    lines = ["# UAH rating comparison — exploratory model", "",
             f"Model: `{experiment['experiment_id']}`. Trained only on professional events; "
             "UAH data was not used to fit or choose coefficients. Ratings below are experimental "
             "and do not change `collegiate_v1` or the public website.", "",
             "| Player | Scope | Rounds | collegiate_v1 | Raw candidate | Difference |",
             "| --- | --- | ---: | ---: | ---: | ---: |"]
    details = []
    for saved in maps:
        match = Match.from_dict(json.loads(saved["normalized_json"]))
        aggregate = calculate_match(match, rating_version="collegiate_v1")
        for participant in match.rounds[0].players:
            if participant.team != saved["our_team"] or participant.profile_id not in players:
                continue
            name = players[participant.profile_id]
            rounds = player_rounds(match, participant.key)
            all_rounds[name].extend(rounds)
            row = {"rounds": rounds}
            candidate = predict(model, row, {})
            current = aggregate[participant.key]["rating"]
            lines.append(f"| {name} | {saved['map_name']} | {len(rounds)} | {current:.3f} | "
                         f"{candidate:.3f} | {candidate-current:+.3f} |")
            details.append((name, saved["map_name"], contribution(model, row)))
    # Calculate season collegiate_v1 from all stored normalized rounds, not
    # from an average of map ratings (its ratio terms are nonlinear).
    combined = Match("uah-combined", "", "Season", "CustomGameLocal", "Bomb",
                     [round_ for saved in maps for round_ in
                      Match.from_dict(json.loads(saved["normalized_json"])).rounds])
    season_stats = calculate_match(combined, rating_version="collegiate_v1")
    for profile_id, name in players.items():
        if name not in all_rounds:
            continue
        rounds = all_rounds[name]
        row = {"rounds": rounds}
        candidate = predict(model, row, {})
        current = season_stats[profile_id]["rating"]
        lines.append(f"| **{name}** | **Season** | **{len(rounds)}** | **{current:.3f}** | "
                     f"**{candidate:.3f}** | **{candidate-current:+.3f}** |")
        details.append((name, "Season", contribution(model, row)))
    lines.extend(["", "## Component contributions", "",
                  "Each contribution is measured relative to the professional training-set mean. "
                  "The model intercept is added to the sum.", "",
                  f"Intercept: **{model['intercept']:.3f}**", "",
                  "| Player | Scope | " + " | ".join(FEATURES) + " |",
                  "| --- | --- | " + " | ".join("---:" for _ in FEATURES) + " |"])
    for name, scope, components in details:
        lines.append(f"| {name} | {scope} | " +
                     " | ".join(f"{components[key]:+.3f}" for key in FEATURES) + " |")
    lines.extend(["", "The candidate is a research comparison only. Operator-adjusted candidates "
                  "performed worse on the August validation event; the September Stage 2 final event "
                  "has not been used for model selection.", ""])
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT}; {len(maps)} maps, {len(all_rounds)} tracked players")


if __name__ == "__main__":
    main()
