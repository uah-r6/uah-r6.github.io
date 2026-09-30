"""Reconstruct explicitly declared multi-segment professional maps for research."""
from __future__ import annotations

import json
from pathlib import Path

from r6stats.parser.logical_map import PhysicalRound, PhysicalSegment, stitch_segments
from r6stats.parser.siege_dissect import parse_match

from rehost_audit import inspect_segment


def build(source: dict, mapping: dict, extraction: Path, meta: dict,
          diagnostics: Path):
    segment_names = mapping["segments"]
    if len(segment_names) < 2 or len(set(segment_names)) != len(segment_names):
        raise ValueError("Rehost source needs at least two distinct ordered segments")
    diagnostics.mkdir(parents=True, exist_ok=True)
    segments = []
    for number, name in enumerate(segment_names, start=1):
        folders = [folder for folder in extraction.rglob(name) if folder.is_dir()]
        if len(folders) != 1:
            raise ValueError(f"Expected exactly one physical replay segment {name}")
        folder = folders[0]
        audit = inspect_segment(folder, number, diagnostics)
        if "parser_error" in audit:
            raise ValueError(f"Physical replay segment {name} failed to parse: {audit['parser_error'][-150:]}")
        match = parse_match(folder)
        if len(match.rounds) != len(audit["rounds"]):
            raise ValueError("Raw and normalized physical round counts disagree")
        physical = []
        for normalized, evidence in zip(match.rounds, audit["rounds"]):
            rosters = tuple(tuple(sorted(player.key for player in normalized.players
                                         if player.team == team)) for team in (0, 1))
            physical.append(PhysicalRound(
                folder.name, evidence["physical_file"], evidence["sha256"],
                evidence["replay_id"], evidence["timestamp"], normalized.number,
                normalized,
                tuple(team["startingScore"] for team in evidence["teams"]),
                tuple(team["score"] for team in evidence["teams"]), rosters))
        segments.append(PhysicalSegment(match, tuple(physical)))
    players = source["players"]
    first_players = segments[0].match.rounds[0].players
    if set(players) != {player.username for player in first_players}:
        raise ValueError("Rehost replay roster differs from explicit player mapping")
    by_player = {player["id"]: player["roster_id"] for player in meta["players"]}
    team_to_roster = {}
    for player in first_players:
        roster = by_player[players[player.username]]
        if player.team in team_to_roster and team_to_roster[player.team] != roster:
            raise ValueError("Mixed public rosters on one replay team")
        team_to_roster[player.team] = roster
    if len(team_to_roster) != 2 or team_to_roster[0] == team_to_roster[1]:
        raise ValueError("Two distinct public rosters are required")
    game = next(game for game in meta["games"] if game["id"] == mapping["siegegg_game_id"])
    expected = tuple(game["win_score"] if team_to_roster[team] == game["win_roster_id"]
                     else game["loss_score"] if team_to_roster[team] == game["loss_roster_id"]
                     else -1 for team in (0, 1))
    if -1 in expected:
        raise ValueError("Replay roster IDs disagree with the public game")
    logical = stitch_segments(segments, expected_final_scores=expected)
    observed_excluded = [{"folder": item.folder, "filename": item.filename}
                         for item in logical.mapping if item.logical_number is None]
    if observed_excluded != mapping["excluded_physical_rounds"]:
        raise ValueError("Score-derived excluded rounds differ from source manifest")
    audit_record = {"source": source["label"], "segments": segment_names,
                    "expected_final_scores": expected,
                    "physical_to_logical": [
                        {"folder": item.folder, "filename": item.filename,
                         "sha256": item.sha256, "replay_id": item.replay_id,
                         "physical_number": item.physical_number,
                         "logical_number": item.logical_number,
                         "exclusion_reason": item.exclusion_reason}
                        for item in logical.mapping]}
    (diagnostics / "pipeline-mapping.json").write_text(
        json.dumps(audit_record, indent=2), encoding="utf-8")
    return logical.match
