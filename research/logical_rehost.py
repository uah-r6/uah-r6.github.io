"""Build a verified logical map from a cached physical rehost audit.

This is a research admission preflight. It preserves every physical round in
the audit and writes derived logical output only under ignored data/research/.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import sys

from pipeline import DATA, SOURCES, canonical_map
from r6stats.parser.logical_map import PhysicalRound, PhysicalSegment, stitch_segments
from r6stats.parser.siege_dissect import parse_match
from r6stats.stats.calculate import calculate_match


def canonical(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def public_rosters(match, public: list[dict]) -> tuple[int, int]:
    """Map replay teams to public roster IDs using multiple exact visible names."""
    candidates = {index: Counter() for index in (0, 1)}
    for player in match.rounds[0].players:
        replay_name = canonical(player.username.split(".")[0])
        for target in public:
            if replay_name and replay_name in {canonical(target["ign"]),
                                               canonical(target.get("stylized_name") or "")}:
                candidates[player.team][target["roster_id"]] += 1
    choices = []
    for index in (0, 1):
        counts = candidates[index]
        if not counts or counts.most_common(1)[0][1] < 3 or len(counts) != 1:
            raise ValueError(f"Team {index} has insufficient unambiguous public roster evidence: {counts}")
        choices.append(counts.most_common(1)[0][0])
    if choices[0] == choices[1]:
        raise ValueError("Replay teams resolved to the same public roster")
    return tuple(choices)


def player_matches(match, stats: dict, public: list[dict], roster_ids: tuple[int, int]) -> list[dict]:
    matched_ids = set()
    result = []
    verified = [evidence for source in SOURCES
                for evidence in source.get("verified_player_aliases", {}).values()]
    for replay_player in match.rounds[0].players:
        roster = roster_ids[replay_player.team]
        candidates = [target for target in public if target["roster_id"] == roster
                      and canonical(replay_player.username.split(".")[0]) in
                      {canonical(target["ign"]), canonical(target.get("stylized_name") or "")}]
        source = "exact_visible_name"
        if not candidates:
            ids = {evidence["siegegg_player_id"] for evidence in verified
                   if evidence["replay_profile_id"] == replay_player.profile_id}
            candidates = [target for target in public
                          if target["roster_id"] == roster and target["id"] in ids]
            source = "verified_profile_alias"
        if len(candidates) != 1 or candidates[0]["id"] in matched_ids:
            result.append({"replay_player": replay_player.username,
                           "profile_id": replay_player.profile_id,
                           "status": "unresolved_public_identity"})
            continue
        target = candidates[0]
        matched_ids.add(target["id"])
        derived = stats[replay_player.key]
        public_k, public_d = map(int, re.match(r"(\d+)-(\d+)", target["kd"]).groups())
        result.append({"replay_player": replay_player.username,
                       "profile_id": replay_player.profile_id,
                       "public_player_id": target["id"],
                       "public_ign": target["ign"], "source": source,
                       "public_kd": [public_k, public_d],
                       "replay_kd": [derived["kills"], derived["deaths"]],
                       "fit_eligible": (derived["kills"], derived["deaths"]) ==
                                       (public_k, public_d)})
    return result


def recover(match_id: int) -> dict:
    audit = json.loads((DATA / "diagnostics/rehost" / str(match_id) / "audit.json").read_text())
    report = json.loads((DATA / "diagnostics" / f"candidate-{match_id}.json").read_text())
    extraction = DATA / "extracted" / report["extraction_label"]
    target_meta = json.loads((DATA / "targets" /
                              f"siegegg-match-{report['siegegg_match_id']}-api.json").read_text())
    public = [{**player, "kd": next(item["kd"] for item in audit["public_players"]
                                     if item["player_id"] == player["id"])}
              for player in target_meta["players"]
              if any(item["player_id"] == player["id"] for item in audit["public_players"])]
    segments = []
    for segment_audit in audit["segments"]:
        if "parser_error" in segment_audit:
            raise ValueError(f"Unparseable physical segment: {segment_audit['folder']}")
        folder = next(extraction.rglob(segment_audit["folder"]))
        match = parse_match(folder)
        rounds = []
        for normalized, evidence in zip(match.rounds, segment_audit["rounds"]):
            rosters = tuple(tuple(sorted(player.key for player in normalized.players
                                         if player.team == team)) for team in (0, 1))
            rounds.append(PhysicalRound(folder.name, evidence["physical_file"],
                                        evidence["sha256"], evidence["replay_id"],
                                        evidence["timestamp"], normalized.number,
                                        normalized,
                                        tuple(t["startingScore"] for t in evidence["teams"]),
                                        tuple(t["score"] for t in evidence["teams"]),
                                        rosters))
        segments.append(PhysicalSegment(match, tuple(rounds)))
    if canonical_map(segments[0].match.map_name) != canonical_map(audit["public_game"]["map"]):
        raise ValueError("Public and replay maps disagree")
    public_ids = public_rosters(segments[0].match, public)
    game = audit["public_game"]
    expected = tuple(game["win_score"] if roster == game["win_roster_id"]
                     else game["loss_score"] if roster == game["loss_roster_id"] else -1
                     for roster in public_ids)
    if -1 in expected:
        raise ValueError("Public roster IDs do not match public game result")
    logical = stitch_segments(segments, expected_final_scores=expected)
    stats = calculate_match(logical.match)
    by_profile = {player.profile_id: (player.username, player.key)
                  for player in logical.match.rounds[0].players}
    # Per-player public alias matching is a later quality gate; this audit only
    # compares map-wide totals and exact visible-name rows.
    public_kills = sum(int(item["kd"].split("-")[0]) for item in public)
    public_deaths = sum(int(item["kd"].split("-")[1].split(" ")[0]) for item in public)
    replay_kills = sum(item["kills"] for item in stats.values())
    replay_deaths = sum(item["deaths"] for item in stats.values())
    matches = player_matches(logical.match, stats, public, public_ids)
    mapping = [{"folder": item.folder, "filename": item.filename,
                "sha256": item.sha256, "replay_id": item.replay_id,
                "physical_number": item.physical_number,
                "logical_number": item.logical_number,
                "exclusion_reason": item.exclusion_reason}
               for item in logical.mapping]
    destination = DATA / "diagnostics/rehost" / str(match_id)
    (destination / "logical-mapping.json").write_text(json.dumps(mapping, indent=2))
    (destination / "logical-match.json").write_text(json.dumps(logical.match.to_dict(), indent=2))
    (destination / "player-matches.json").write_text(json.dumps(matches, indent=2))
    result = {"match_id": match_id, "physical_rounds": len(mapping),
              "logical_rounds": len(logical.match.rounds),
              "excluded": [(item.folder, item.filename) for item in logical.mapping
                           if item.logical_number is None],
              "final_scores": logical.final_scores, "public_roster_ids": public_ids,
              "public_kd_totals": (public_kills, public_deaths),
              "replay_kd_totals": (replay_kills, replay_deaths),
              "player_profile_count": len(by_profile),
              "identified_players": sum(item.get("public_player_id") is not None for item in matches),
              "clean_players": sum(item.get("fit_eligible", False) for item in matches),
              "unresolved_players": [item["replay_player"] for item in matches
                                     if item.get("status") == "unresolved_public_identity"]}
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: logical_rehost.py UBISOFT_MATCH_ID [...]")
    for value in sys.argv[1:]:
        recover(int(value))
