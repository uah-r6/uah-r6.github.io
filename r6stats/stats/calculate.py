"""Pure, replay-derived per-player statistics."""
from collections import Counter, defaultdict

from r6stats.parser.models import Match

RATING_VERSION = "siege_style_v2"
RATING_VERSIONS = ("collegiate_v1", "siege_style_v2")
COUNTS = ("rounds", "kills", "deaths", "headshots", "opening_kills", "opening_deaths",
          "refrag_kills", "deaths_traded", "kills_traded", "untraded_kills",
          "untraded_deaths", "pivot_kills", "pivot_deaths", "plants", "disables",
          "teamkills", "survived", "kost_rounds", "rounds_won", "clutches",
          "clutch_1v1", "clutch_1v2", "clutch_1v3", "clutch_1v4", "clutch_1v5",
          "multikill_extra")


class RatingEngine:
    version = "collegiate_v1"

    @staticmethod
    def calculate(s: dict) -> float:
        r = s["rounds"]
        if not r:
            return 0.0
        rate = lambda key: s[key] / r
        kr = s["kills_traded"] / s["kills"] if s["kills"] else 0
        dr = s["deaths_traded"] / s["deaths"] if s["deaths"] else 0
        value = (0.3110 * rate("kills") + 0.6037 * rate("pivot_kills")
                 + 0.5408 * rate("untraded_kills") - 0.4894 * rate("deaths")
                 - 0.5966 * rate("pivot_deaths") - 0.6596 * rate("untraded_deaths")
                 + 0.1929 * (s["plants"] + s["disables"]) / r
                 + 0.3320 * rate("kost_rounds") - 0.2464 * kr + 0.1564 * dr)
        return value * 1.0698 + 1


class SiegeStyleRating:
    """Exact frozen raw model from research/frozen-rating-candidate.json.

    Research experiment expanded-raw-20260930T202146Z. Objectives have a
    frozen zero coefficient and are deliberately absent from this calculation.
    """
    version = "siege_style_v2"
    intercept = 0.9663210702341137
    terms = (
        # feature, standardized weight, training mean, training scale
        ("kpr", 0.1783383988926295, 0.6872132698219655, 0.31747215388749184),
        ("teamkills", -0.003740958044867889, 0.00290168768429638, 0.018398414065023003),
        ("multikill", 0.043059455454397495, 0.21832020636368463, 0.18957445336423615),
        ("opening", 0.020353508609250837, -0.002118412987978205, 0.13912824673002738),
        ("clutch", 0.019191796943239425, 0.008892315414054544, 0.02869232693914123),
        ("kost", 0.08461564886568967, 0.6169358419358419, 0.16816935710093414),
        ("survival", 0.08714550755803416, 0.2892744936223197, 0.1778316242495531),
        ("trade", 0.0193703683457493, 0.003632116675594936, 0.1365990260330402),
    )

    @classmethod
    def calculate(cls, s: dict) -> float:
        rounds = s["rounds"]
        if not rounds:
            return 0.0
        values = (s["kills"], s["teamkills"], s["multikill_extra"],
                  s["opening_kills"] - s["opening_deaths"], s["clutches"],
                  s["kost_rounds"], s["survived"],
                  s["deaths_traded"] - s["kills_traded"])
        return cls.intercept + sum(
            weight * (value / rounds - mean) / scale
            for value, (_, weight, mean, scale) in zip(values, cls.terms))


def calculate_rating(s: dict, version: str) -> float:
    if version == RatingEngine.version:
        return RatingEngine.calculate(s)
    if version == SiegeStyleRating.version:
        return SiegeStyleRating.calculate(s)
    raise ValueError(f"Configured Rating version is unavailable: {version}")


def empty() -> dict:
    return {**dict.fromkeys(COUNTS, 0), "operators": {"Attack": {}, "Defense": {}},
            "sides": {"Attack": {"rounds": 0, "kills": 0, "deaths": 0},
                      "Defense": {"rounds": 0, "kills": 0, "deaths": 0}}}


def chronological(kills):
    return sorted(kills, key=lambda k: (-k.remaining, k.sequence))


def calculate_match(match: Match, trade_window_seconds: float = 8,
                    rating_version: str = RATING_VERSION) -> dict[str, dict]:
    if rating_version not in RATING_VERSIONS:
        raise ValueError(f"Configured Rating version is unavailable: {rating_version}")
    if rating_version == SiegeStyleRating.version and trade_window_seconds != 8:
        raise ValueError("siege_style_v2 requires its frozen 8-second trade window.")
    totals = defaultdict(empty)
    for round_ in match.rounds:
        players = {p.key: p for p in round_.players}
        round_stats = defaultdict(empty)
        alive = {p.key for p in round_.players}
        valid = chronological(round_.kills)
        traded_kills = set()
        traded_deaths = set()
        refrags = set()
        processed = set()
        opening_recorded = False
        clutch_candidates = {}
        for i, kill in enumerate(valid):
            if kill.victim not in players or (kill.killer and kill.killer not in players):
                continue
            if kill.victim not in alive:
                continue
            processed.add(kill.sequence)
            if not kill.killer:
                pass
            elif kill.teamkill or kill.killer == kill.victim:
                round_stats[kill.killer]["teamkills"] += 1
            else:
                if not opening_recorded:
                    round_stats[kill.killer]["opening_kills"] += 1
                    round_stats[kill.victim]["opening_deaths"] += 1
                    opening_recorded = True
                round_stats[kill.killer]["kills"] += 1
                if kill.headshot:
                    round_stats[kill.killer]["headshots"] += 1
                own_alive = sum(p.team == kill.killer_team and p.key in alive for p in round_.players)
                foe_alive = sum(p.team == kill.victim_team and p.key in alive for p in round_.players)
                if own_alive <= foe_alive:
                    round_stats[kill.killer]["pivot_kills"] += 1
                    round_stats[kill.victim]["pivot_deaths"] += 1
                # A refrag kills the earlier killer, by a teammate of their victim.
                for j in range(i - 1, -1, -1):
                    prior = valid[j]
                    if (prior.sequence not in processed or prior.teamkill or prior.killer != kill.victim or
                        prior.victim_team != kill.killer_team):
                        continue
                    delta = prior.remaining - kill.remaining
                    if delta < 0 or delta > trade_window_seconds:
                        continue
                    traded_kills.add(prior.sequence)
                    traded_deaths.add(prior.victim)
                    refrags.add(kill.sequence)
            round_stats[kill.victim]["deaths"] += 1
            alive.remove(kill.victim)
            # Only the victim's team can have just become a one-player team.
            # Record its first 1vX state, before later opponent deaths reduce X.
            victim_team = players[kill.victim].team
            teammates = [key for key in alive if players[key].team == victim_team]
            if len(teammates) == 1 and victim_team not in clutch_candidates:
                opponents = sum(players[key].team != victim_team for key in alive)
                if 1 <= opponents <= 5:
                    clutch_candidates[victim_team] = (teammates[0], opponents)
        for kill in valid:
            if kill.sequence not in processed or not kill.killer or kill.teamkill or kill.killer == kill.victim:
                continue
            if kill.sequence in traded_kills:
                round_stats[kill.killer]["kills_traded"] += 1
            else:
                round_stats[kill.killer]["untraded_kills"] += 1
        for s in round_stats.values():
            s["multikill_extra"] = max(s["kills"] - 1, 0)
        for objective in round_.objectives:
            actor = players.get(objective.player)
            expected_side = {"plant": "Attack", "disable": "Defense"}.get(objective.kind)
            if (actor and expected_side and actor.side == expected_side and
                    actor.team == objective.team):
                round_stats[objective.player]["plants" if objective.kind == "plant" else "disables"] += 1
        clutch = clutch_candidates.get(round_.winner)
        if clutch:
            key, opponents = clutch
            round_stats[key]["clutches"] += 1
            round_stats[key][f"clutch_1v{opponents}"] += 1
        for player in round_.players:
            key = player.key
            s = round_stats[key]
            s["rounds"] = 1
            s["survived"] = int(key in alive)
            s["deaths_traded"] = int(key in traded_deaths and s["deaths"] > 0)
            s["untraded_deaths"] = s["deaths"] - s["deaths_traded"]
            s["refrag_kills"] = sum(k.killer == key and k.sequence in refrags for k in valid)
            s["kost_rounds"] = int(bool(s["kills"] or s["plants"] or s["disables"]
                                         or s["survived"] or s["deaths_traded"]))
            s["rounds_won"] = int(player.team == round_.winner)
            if player.side in s["sides"]:
                side = s["sides"][player.side]
                side["rounds"] += 1
                side["kills"] += s["kills"]
                side["deaths"] += s["deaths"]
                if player.operator != "Unknown":
                    ops = s["operators"][player.side]
                    ops[player.operator] = ops.get(player.operator, 0) + 1
            merge(totals[key], s)
    return {key: finalize(value, rating_version) for key, value in totals.items()}


def merge(target: dict, source: dict) -> None:
    for key in COUNTS:
        target[key] += source[key]
    for side in ("Attack", "Defense"):
        for key in ("rounds", "kills", "deaths"):
            target["sides"][side][key] += source["sides"][side][key]
        for op, count in source["operators"][side].items():
            target["operators"][side][op] = target["operators"][side].get(op, 0) + count


def finalize(s: dict, rating_version: str = RATING_VERSION) -> dict:
    r = s["rounds"]
    s["rating"] = calculate_rating(s, rating_version)
    s["kd"] = s["kills"] / s["deaths"] if s["deaths"] else None
    s["kpr"] = s["kills"] / r if r else 0
    s["kost"] = s["kost_rounds"] / r if r else 0
    s["srv"] = s["survived"] / r if r else 0
    s["hs"] = s["headshots"] / s["kills"] if s["kills"] else 0
    s["entry_diff"] = s["opening_kills"] - s["opening_deaths"]
    s["kd_diff"] = s["kills"] - s["deaths"]
    s["objectives"] = s["plants"] + s["disables"]
    for side in s["sides"].values():
        side["kd"] = side["kills"] / side["deaths"] if side["deaths"] else None
        side["kpr"] = side["kills"] / side["rounds"] if side["rounds"] else 0
    return s


def aggregate(stat_rows: list[dict], rating_version: str = RATING_VERSION) -> dict:
    total = empty()
    for row in stat_rows:
        merge(total, row)
    total["maps"] = len(stat_rows)
    return finalize(total, rating_version)
