"""Validated scoreboard credit, separate from immutable replay finish events.

Opt-in migration preparation only. The existing import/export and frozen rating
engine do not call this module. No SQLite or filesystem writes occur here.
"""
from collections import Counter
from uuid import UUID

SOURCE = "stable_uid_scoreboard_delta_v1"


def identity(player: dict) -> str:
    """Profile identity across rehosts; numeric UID for a single LAN segment."""
    try:
        profile = UUID(player.get("profileID") or "")
        if profile.int:
            return str(profile)
    except (ValueError, TypeError, AttributeError):
        pass
    return f"uid:{player['uid']}"


def validate_map_credit(records: list[dict]) -> dict:
    """Accept complete consecutive physical sources, never bridge an unknown gap.

    A new folder/R01/all-zero baseline resets only with the same ten distinct
    nonzero profiles. Reconnect/component changes are refused pending evidence;
    missing participation is retained, never synthesized from official totals.
    """
    issues, resets, rounds = [], [], []
    seen_sources = set()
    previous = None
    for ordinal, record in enumerate(records, 1):
        logical = record["logical_round"]
        report = record["credit"]
        source = (record["segment"], record["physical_round"])
        if logical != ordinal or source in seen_sources or record["physical_round"] < 1:
            raise ValueError("Credit sources must be unique and logically consecutive.")
        seen_sources.add(source)
        if report.get("source") != SOURCE:
            raise ValueError("Unsupported credited-kill evidence source.")
        players = report["players"]
        current = {identity(p): p for p in players}
        valid = (report.get("complete") is True and len(current) == len(players) == 10
                 and all(type(p.get("uid")) is int and p["uid"] > 0 for p in players)
                 and len({p["uid"] for p in players}) == 10
                 and Counter(p["team"] for p in players) == Counter({0: 5, 1: 5}))
        for p in players:
            values = (p.get("initial"), p.get("terminal"), p.get("kills"))
            if (any(type(v) is not int for v in values) or
                    not 0 <= values[0] <= values[1] <= 250 or
                    not 0 <= values[2] <= 5 or values[1] - values[0] != values[2]):
                valid = False
        if not valid:
            issues.append({"round": logical, "reason": "incomplete_or_invalid_round_counters",
                           "players": [{"player": p["username"], "reason": p["reason"]}
                                       for p in players if p.get("kills") is None]})
        if previous is not None:
            previous_record, prior, prior_valid = previous
            if not prior_valid or not valid:
                issues.append({"round": logical, "reason": "continuity_through_unresolved_round"})
            else:
                same_profiles = (prior.keys() == current.keys() and
                                 all(not key.startswith("uid:") for key in current))
                reset = (same_profiles and source[0] != previous_record["segment"]
                         and source[1] == 1 and all(p["initial"] == 0 for p in players))
                if reset:
                    resets.append({"round": logical, "segment": source[0],
                                   "reason": "new_R01_same_ten_profiles_all_zero"})
                elif prior.keys() != current.keys():
                    issues.append({"round": logical, "reason": "participation_or_identity_changed"})
                else:
                    for key, p in current.items():
                        if p["initial"] != prior[key]["terminal"]:
                            issues.append({"round": logical, "player": p["username"],
                                           "reason": "unexplained_counter_discontinuity",
                                           "previous": prior[key]["terminal"], "initial": p["initial"]})
        rounds.append({"number": logical, "valid": valid, "players": current,
                       "segment": source[0], "physical_round": source[1]})
        previous = record, current, valid
    totals = Counter()
    for r in rounds:
        if r["valid"]:
            totals.update({key: p["kills"] for key, p in r["players"].items()})
    complete = bool(rounds) and not issues
    return {"source": SOURCE, "complete": complete, "issues": issues,
            "resets": resets, "rounds": rounds,
            "totals": dict(totals) if complete else None,
            "observed_valid_round_totals": dict(totals)}


def project_credited_counts(match, credit: dict) -> dict:
    """Prepare simple K/KD/KPR and side counts without changing rating inputs.

    A complete evidence map and exact normalized participation are required.
    Raw Kill rows remain finisher/elimination records. No headshot, opening,
    trade, pivot, KOST or rating feature is silently recomputed from credit.
    """
    if not credit["complete"]:
        raise ValueError("Incomplete credited-kill evidence cannot replace map statistics.")
    if [r.number for r in match.rounds] != [r["number"] for r in credit["rounds"]]:
        raise ValueError("Normalized and credited round inventories differ.")
    from r6stats.stats.calculate import calculate_match

    original = calculate_match(match)
    totals, sides, participation = Counter(), {}, Counter()
    multikills, kill_rounds = {}, Counter()
    for normalized, observed in zip(match.rounds, credit["rounds"]):
        # Nonzero profiles are essential for joining normalized identities;
        # LAN UID-only evidence requires an explicit adapter identity map.
        try:
            canonical = {str(UUID(p.profile_id)): p.key for p in normalized.players
                         if UUID(p.profile_id).int}
        except (ValueError, TypeError, AttributeError):
            raise ValueError("Normalized/counter participation identity mismatch.") from None
        if len(canonical) != len(normalized.players) or canonical.keys() != observed["players"].keys():
            raise ValueError("Normalized/counter participation identity mismatch.")
        team_pairs = {(observed["players"][key]["team"],
                       next(p.team for p in normalized.players if p.key == normalized_key))
                      for key, normalized_key in canonical.items()}
        # Confirmed replay stitching can flip raw team indices at a rehost.
        # Accept only a complete bijection between the two stable profile groups.
        if team_pairs not in ({(0, 0), (1, 1)}, {(0, 1), (1, 0)}):
            raise ValueError("Normalized/counter team mismatch.")
        for p in normalized.players:
            row = observed["players"][str(UUID(p.profile_id))]
            totals[p.key] += row["kills"]
            kill_rounds[p.key] += int(row["kills"] > 0)
            buckets = multikills.setdefault(p.key, dict.fromkeys((2, 3, 4, 5), 0))
            if row["kills"] >= 2:
                buckets[row["kills"]] += 1
            participation[p.key] += 1
            side = sides.setdefault(p.key, {}).setdefault(p.side, {"kills": 0, "rounds": 0})
            side["kills"] += row["kills"]
            side["rounds"] += 1
    return {key: {"source": SOURCE, "kills": totals[key], "deaths": s["deaths"],
                  "kd": totals[key] / s["deaths"] if s["deaths"] else None,
                  "kpr": totals[key] / participation[key], "sides": sides[key],
                  "credited_kill_rounds": kill_rounds[key],
                  "credited_multikill_sizes": multikills[key],
                  "credited_multikill_extra": sum((size-1)*count for size, count in multikills[key].items()),
                  "original_finisher_statistics": s,
                  "rating_input_semantics": "siege_style_v2_original_finisher_inputs"}
            for key, s in original.items()}
