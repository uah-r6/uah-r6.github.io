"""Join verified physical replay segments into one competitive map.

The caller supplies ordered segments and their original round score states.
Score continuity, roster identity, replay identity, and final score are checked
before any physical round is excluded. The physical evidence is never mutated.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json

from .models import Match, Round

Roster = tuple[str, ...]


@dataclass(frozen=True)
class PhysicalRound:
    folder: str
    filename: str
    sha256: str
    replay_id: str
    timestamp: str
    physical_number: int
    round: Round
    starting_scores: tuple[int, int]
    ending_scores: tuple[int, int]
    rosters: tuple[Roster, Roster]


@dataclass(frozen=True)
class PhysicalSegment:
    match: Match
    rounds: tuple[PhysicalRound, ...]


@dataclass(frozen=True)
class LogicalRoundMapping:
    folder: str
    filename: str
    sha256: str
    replay_id: str
    physical_number: int
    logical_number: int | None
    exclusion_reason: str | None


@dataclass(frozen=True)
class LogicalMap:
    match: Match
    segments: tuple[PhysicalSegment, ...]
    mapping: tuple[LogicalRoundMapping, ...]
    final_scores: tuple[int, int]


def score_map(physical: PhysicalRound, ending: bool,
              canonical_rosters: tuple[Roster, Roster] | None = None) -> dict[Roster, int]:
    values = physical.ending_scores if ending else physical.starting_scores
    rosters = canonical_rosters or physical.rosters
    if len(set(rosters)) != 2 or any(not roster for roster in rosters):
        raise ValueError("Each round must have two distinct, identified rosters")
    return dict(zip(rosters, values))


def stitch_segments(segments: list[PhysicalSegment], *,
                    expected_final_scores: tuple[int, int] | None = None) -> LogicalMap:
    """Build consecutive logical rounds; exclude only a score-reset suffix.

    expected_final_scores are in the first segment's team-index order. A caller
    must independently map public or user-confirmed score to those rosters.
    """
    if not segments or any(not segment.rounds for segment in segments):
        raise ValueError("At least one nonempty replay segment is required")
    first = segments[0]
    base_rosters = first.rounds[0].rosters
    base_set = set(base_rosters)
    if score_map(first.rounds[0], False) != dict.fromkeys(base_rosters, 0):
        raise ValueError("The first segment must begin at a 0-0 competitive score")
    seen_folders, seen_replays, seen_hashes = set(), set(), set()
    physical_rounds = []
    retained = []
    excluded = {}
    rosters_by_source = {}
    for segment in segments:
        match = segment.match
        if (match.map_name, match.match_type, match.game_mode) != (
                first.match.map_name, first.match.match_type, first.match.game_mode):
            raise ValueError("Replay segments disagree on map or match type")
        if len(match.rounds) != len(segment.rounds):
            raise ValueError("Segment normalized and physical round counts disagree")
        folders = {source.folder for source in segment.rounds}
        replay_ids = {source.replay_id for source in segment.rounds}
        if len(folders) != 1 or len(replay_ids) != 1 or match.replay_id not in replay_ids:
            raise ValueError("Segment source folder or replay identity is inconsistent")
        folder = next(iter(folders))
        replay_id = next(iter(replay_ids))
        if folder in seen_folders or replay_id in seen_replays:
            raise ValueError("The same physical segment was supplied more than once")
        seen_folders.add(folder)
        seen_replays.add(replay_id)
        segment_rosters = segment.rounds[0].rosters
        if set(segment_rosters) != base_set:
            raise ValueError("Replay segments have different roster identities")
        previous = None
        for normalized, source in zip(match.rounds, segment.rounds):
            if source.round != normalized or source.physical_number != normalized.number:
                raise ValueError("Physical and normalized round numbers disagree")
            if any(not set(actual).issubset(set(expected)) for actual, expected
                   in zip(source.rosters, segment_rosters)):
                raise ValueError("A physical round contains an unrelated player identity")
            if source.sha256 in seen_hashes:
                raise ValueError("A physical round file was supplied more than once")
            seen_hashes.add(source.sha256)
            rosters_by_source[(source.folder, source.filename)] = segment_rosters
            start = score_map(source, False, segment_rosters)
            end = score_map(source, True, segment_rosters)
            winning_roster = segment_rosters[normalized.winner]
            if any(end[roster] - start[roster] != int(roster == winning_roster)
                   for roster in base_set):
                raise ValueError("A physical round's score change disagrees with its winner")
            if previous is not None and start != previous:
                raise ValueError("Score discontinuity inside a physical segment")
            previous = end
            physical_rounds.append(source)
        incoming_start = score_map(segment.rounds[0], False, segment_rosters)
        if retained:
            states = ([score_map(first.rounds[0], False, base_rosters)] +
                      [score_map(source, True,
                                 rosters_by_source[(source.folder, source.filename)])
                       for source in retained])
            joins = [index for index, state in enumerate(states) if state == incoming_start]
            if len(joins) != 1:
                raise ValueError("Cannot identify a unique score-continuous rehost boundary")
            keep = joins[0]
            for source in retained[keep:]:
                excluded[(source.folder, source.filename)] = "score_reset_before_next_segment"
            retained = retained[:keep]
        retained.extend(segment.rounds)
    for source in retained:
        canonical = rosters_by_source[(source.folder, source.filename)]
        if source.rosters != canonical:
            raise ValueError("A counting competitive round has incomplete roster identity")
    last = retained[-1]
    final_map = score_map(last, True, rosters_by_source[(last.folder, last.filename)])
    final_scores = tuple(final_map[roster] for roster in base_rosters)
    if expected_final_scores is not None and final_scores != expected_final_scores:
        raise ValueError(f"Logical final score {final_scores} disagrees with confirmed score "
                         f"{expected_final_scores}")
    if len(retained) != sum(final_scores):
        raise ValueError("Logical round count disagrees with final score")
    logical_numbers = {(source.folder, source.filename): number
                       for number, source in enumerate(retained, start=1)}
    mapping = tuple(LogicalRoundMapping(source.folder, source.filename, source.sha256,
                                        source.replay_id, source.physical_number,
                                        logical_numbers.get((source.folder, source.filename)),
                                        excluded.get((source.folder, source.filename)))
                    for source in physical_rounds)
    fingerprint = hashlib.sha256(json.dumps(
        [(item.sha256, item.logical_number) for item in mapping],
        separators=(",", ":")).encode()).hexdigest()[:20]
    logical_match = Match(f"logical:{fingerprint}", first.match.timestamp,
                          first.match.map_name, first.match.match_type,
                          first.match.game_mode,
                          [replace(source.round, number=number)
                           for number, source in enumerate(retained, start=1)])
    return LogicalMap(logical_match, tuple(segments), mapping, final_scores)
