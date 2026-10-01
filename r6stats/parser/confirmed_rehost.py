"""Explicit, local competitive-map assembly from ordered replay segments.

Unlike professional score-continuity reconstruction, a local rehost may start
the next physical lobby at 0-0. Only user-selected physical rounds count.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

from r6stats.eligibility import is_custom_game

from .logical_map import LogicalMap, LogicalRoundMapping, PhysicalRound, PhysicalSegment
from .models import Match
from .siege_dissect import parse_match, physical_round_numbers


def physical_segment(match: Match, path: Path, index: int) -> PhysicalSegment:
    """Attach immutable source evidence to a parsed single-folder match."""
    files = sorted(path.glob("*.rec"))
    numbers = physical_round_numbers(files)
    if len(files) != len(match.rounds):
        raise ValueError("Replay source and parsed round counts disagree.")
    physical = []
    score = [0, 0]
    for file, number, round_ in zip(files, numbers, match.rounds):
        if round_.number != number:
            raise ValueError("Physical filename and parsed round numbers disagree.")
        rosters = tuple(tuple(sorted(p.key for p in round_.players if p.team == team))
                        for team in (0, 1))
        before = tuple(score)
        score[round_.winner] += 1
        with file.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        physical.append(PhysicalRound(
            f"segment-{index:02d}", file.name, digest,
            match.replay_id, match.timestamp, number, round_, before, tuple(score), rosters))
    return PhysicalSegment(match, tuple(physical))


def stitch_confirmed(segments: list[PhysicalSegment], *,
                     excluded: dict[tuple[str, int], str],
                     expected_final_scores: tuple[int, int] | None = None) -> LogicalMap:
    """Join explicit rounds; scores are in the first segment's team order."""
    if len(segments) < 2 or any(not segment.rounds for segment in segments):
        raise ValueError("A rehost needs at least two complete replay folders.")
    if expected_final_scores is not None and any(score < 0 for score in expected_final_scores):
        raise ValueError("Final competitive scores cannot be negative.")
    first = segments[0]
    canonical = first.rounds[0].rosters
    if len(set(canonical)) != 2 or any(len(team) == 0 for team in canonical):
        raise ValueError("The first replay has no distinct, identified teams.")
    seen_replays, seen_hashes, seen_folders = set(), set(), set()
    mapping = []
    counted = []
    actual_sources = set()
    score = [0, 0]
    for segment in segments:
        match = segment.match
        if (match.map_name, match.match_type, match.game_mode) != (
                first.match.map_name, first.match.match_type, first.match.game_mode):
            raise ValueError("Rehost segments disagree on map or game type.")
        if len(match.rounds) != len(segment.rounds):
            raise ValueError("Parsed and physical round counts disagree.")
        folder = segment.rounds[0].folder
        if folder in seen_folders or not match.replay_id or match.replay_id in seen_replays:
            raise ValueError("A replay segment was supplied more than once.")
        seen_folders.add(folder)
        seen_replays.add(match.replay_id)
        rosters = segment.rounds[0].rosters
        if set(rosters) != set(canonical):
            raise ValueError("Replay segments have different player identities or teams.")
        remap = {index: canonical.index(team) for index, team in enumerate(rosters)}
        for physical, round_ in zip(segment.rounds, match.rounds):
            key = (physical.folder, physical.physical_number)
            if key in actual_sources or physical.round != round_ or round_.number != physical.physical_number:
                raise ValueError("A physical round is duplicated or mismatched.")
            actual_sources.add(key)
            if physical.sha256 in seen_hashes:
                raise ValueError("A physical replay file was supplied more than once.")
            seen_hashes.add(physical.sha256)
            if any(not set(actual).issubset(set(rosters[index]))
                   for index, actual in enumerate(physical.rosters)):
                raise ValueError("A round contains unrelated player identities.")
            reason = excluded.get(key)
            if key in excluded and not reason.strip():
                raise ValueError("Give each excluded physical round a reason.")
            number = None if key in excluded else len(counted) + 1
            mapping.append(LogicalRoundMapping(physical.folder, physical.filename,
                                               physical.sha256, physical.replay_id,
                                               physical.physical_number, number, reason))
            if number is None:
                continue
            if physical.rosters != rosters:
                raise ValueError("A counting round has incomplete player identities.")
            winner = remap[round_.winner]
            score[winner] += 1
            counted.append(replace(
                round_, number=number, winner=winner,
                players=[replace(player, team=remap[player.team]) for player in round_.players],
                kills=[replace(kill, killer_team=remap.get(kill.killer_team, kill.killer_team),
                               victim_team=remap[kill.victim_team]) for kill in round_.kills],
                objectives=[replace(objective, team=remap[objective.team])
                            for objective in round_.objectives]))
    unknown = set(excluded) - actual_sources
    if unknown:
        raise ValueError(f"Excluded physical round was not found: {sorted(unknown)[0]}")
    if not counted or len(counted) != sum(score) or (
            expected_final_scores is not None and tuple(score) != expected_final_scores):
        raise ValueError(f"Counted rounds give final score {tuple(score)}, not the confirmed "
                         f"score {expected_final_scores}.")
    digest = hashlib.sha256(json.dumps(
        [(item.folder, item.sha256, item.logical_number, item.exclusion_reason)
         for item in mapping], separators=(",", ":")).encode()).hexdigest()
    logical_match = Match(f"logical:{digest[:20]}", first.match.timestamp,
                          first.match.map_name, first.match.match_type,
                          first.match.game_mode, counted)
    return LogicalMap(logical_match, tuple(segments), tuple(mapping), tuple(score))


def source_fingerprint(path: Path) -> str:
    """Use the same physical replay fingerprint as one-folder imports."""
    digest = hashlib.sha256()
    for file in sorted(path.glob("*.rec")):
        digest.update(file.name.encode())
        with file.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


def manifest_fingerprint(manifest: dict) -> str:
    """Stable identity independent of original Windows folder locations."""
    value = {"segments": [(item["replay_id"], item["fingerprint"])
                          for item in manifest["segments"]],
             "mapping": [(item["segment"], item["filename"], item["sha256"],
                          item["logical_number"], item["exclusion_reason"])
                         for item in manifest["mapping"]],
             "final_scores": manifest["final_scores"]}
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def assemble_rehost(paths: list[Path], exclusions: list[dict],
                    final_scores: tuple[int, int] | None = None) -> tuple[LogicalMap, dict, str]:
    """Parse explicit folders and return the logical match plus private provenance."""
    if len(paths) < 2 or len({path.resolve() for path in paths}) != len(paths):
        raise ValueError("Select two or more distinct ordered replay folders.")
    segments = []
    sources = []
    for index, original in enumerate(paths, start=1):
        path = original.expanduser().resolve()
        if not path.is_dir():
            raise ValueError(f"Replay segment is not a folder: {path}")
        match = parse_match(path)
        if not is_custom_game(match.match_type):
            raise ValueError(f"Segment {index} is not a Custom Game replay.")
        segments.append(physical_segment(match, path, index))
        sources.append({"segment": index, "source_path": str(path),
                        "source_name": path.name, "replay_id": match.replay_id,
                        "fingerprint": source_fingerprint(path)})
    excluded = {}
    for item in exclusions:
        index = int(item["segment"])
        number = int(item["physical_number"])
        if not 1 <= index <= len(paths) or number < 1:
            raise ValueError("Excluded round has an invalid segment or physical number.")
        key = (f"segment-{index:02d}", number)
        if key in excluded:
            raise ValueError("The same physical round was excluded twice.")
        excluded[key] = str(item["reason"]).strip()
    logical = stitch_confirmed(segments, excluded=excluded,
                               expected_final_scores=final_scores)
    manifest = {"version": 1, "segments": sources, "final_scores": list(logical.final_scores),
                "mapping": [{"segment": int(item.folder.split("-")[1]),
                             "filename": item.filename, "sha256": item.sha256,
                             "replay_id": item.replay_id,
                             "physical_number": item.physical_number,
                             "logical_number": item.logical_number,
                             "exclusion_reason": item.exclusion_reason}
                            for item in logical.mapping]}
    return logical, manifest, manifest_fingerprint(manifest)
