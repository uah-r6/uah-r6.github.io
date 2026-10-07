"""Publish only roster statistics and match context, never replay identities."""
import json
from collections import defaultdict
from pathlib import Path

from r6stats.parser.models import Match
from r6stats.rating_inputs_v3 import load_inputs as load_v3
from r6stats.manual_kd import apply_display_kd
from r6stats.objective_refresh import rating_stats
from r6stats.credited_refresh import aggregate_display, display_stats, load as load_credit
from r6stats.stats.calculate import RATING_VERSION, RATING_VERSIONS, aggregate, calculate_match


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def export(db, config: dict, root: Path = Path("web/public/data")) -> None:
    version = config.get("stats", {}).get("rating_version", RATING_VERSION)
    if version not in RATING_VERSIONS:
        raise ValueError(f"Configured Rating version is unavailable: {version}")
    if version in ("siege_style_v2", "siege_style_v3") and config["stats"]["trade_window_seconds"] != 8:
        raise ValueError(f"{version} requires its frozen 8-second trade window.")
    # Remove obsolete generated files (for example after clearing demo maps).
    if root.exists():
        for old in root.rglob("*.json"):
            old.unlink()
    seasons = [dict(r) for r in db.execute("SELECT * FROM seasons ORDER BY id DESC")]
    active = next((s["slug"] for s in seasons if s["active"]), None)
    players = [dict(r) for r in db.execute("""SELECT * FROM players p WHERE tracked=1
                 OR EXISTS (SELECT 1 FROM round_players rp WHERE rp.player_id=p.id)
                 ORDER BY display_name""")]
    window = config["stats"]["trade_window_seconds"]
    display_version = "siege_style_v2" if version == "siege_style_v3" else version
    season_stats = defaultdict(lambda: defaultdict(list))
    season_rating_stats = defaultdict(lambda: defaultdict(list))
    season_adjustments = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    season_matches = defaultdict(list)
    player_matches = defaultdict(lambda: defaultdict(list))
    demo_seasons = set()
    rows = db.execute("""SELECT m.*, s.opponent,s.date,s.week,s.notes,s.demo,s.id AS series_public,
                          se.slug AS season_slug FROM maps m JOIN series s ON s.id=m.series_id
                          JOIN seasons se ON se.id=s.season_id
                          ORDER BY COALESCE(m.played_on,s.date) DESC,m.rowid DESC""").fetchall()
    for row in rows:
        match = Match.from_dict(json.loads(row["normalized_json"]))
        stats = calculate_match(match, window, display_version)
        reason = None
        if version == "siege_style_v3":
            rating_inputs, reason = load_v3(db, row["id"], window)
        else:
            rating_inputs = rating_stats(db, row["id"], stats, window, version)
        # Validate frozen Rating inputs against original finish events BEFORE
        # applying independent credited-count display projections.
        stats = display_stats(match, load_credit(db, row['id']), window, display_version)
        bound_keys = defaultdict(set)
        for binding in db.execute("""SELECT DISTINCT rp.player_id,rp.player_key
            FROM round_players rp JOIN rounds rd ON rd.id=rp.round_id
            WHERE rd.map_id=? AND rp.player_id IS NOT NULL""", (row["id"],)):
            bound_keys[binding["player_id"]].add(binding["player_key"])
        corrections = {c["player_id"]: c for c in db.execute(
            "SELECT * FROM map_kd_corrections WHERE map_id=?", (row["id"],))}
        rating_eligible = bool(row["replay_data_complete"]) and not corrections and rating_inputs is not None
        if rating_inputs is None:
            rating_inputs = stats  # Unrated display fallback, never aggregated into Rating.
        public = {"id": row["id"], "series_id": row["series_public"], "season": row["season_slug"],
                  "opponent": row["opponent"], "date": row["played_on"] or row["date"], "week": row["week"],
                  "notes": row["notes"], "map": row["map_name"], "mode": row["game_mode"],
                  "our_score": row["our_score"], "their_score": row["their_score"],
                  "result": "WIN" if row["our_score"] > row["their_score"] else "LOSS",
                  "demo": bool(row["demo"]), "rating_eligible": rating_eligible}
        if version == "siege_style_v3":
            public.update(rating_version=version, rating_exclusion=reason)
        if row["demo"]:
            demo_seasons.add(row["season_slug"])
        public_players = []
        for p in players:
            keys = [key for key in bound_keys[p["id"]] if key in stats]
            if keys:
                raw = stats[keys[0]] if len(keys) == 1 else aggregate_display([stats[key] for key in keys], display_version)
                rating_raw = (rating_inputs[keys[0]] if len(keys) == 1 else
                              aggregate([rating_inputs[key] for key in keys], version))
                if len(keys) > 1:
                    raw.pop("maps", None)
                correction = corrections.get(p["id"])
                shown = (apply_display_kd(raw, correction["final_kills"], correction["final_deaths"])
                         if correction else raw)
                entry = {"slug": p["slug"], "name": p["display_name"], **shown,
                         "rating": rating_raw["rating"] if rating_eligible else None}
                if version == "siege_style_v3":
                    entry.update(rating_rounds=rating_raw["rounds"] if rating_eligible else 0,
                                 rating_maps=int(rating_eligible))
                public_players.append(entry)
                season_stats[row["season_slug"]][p["slug"]].append(raw)
                if rating_eligible:
                    season_rating_stats[row["season_slug"]][p["slug"]].append(rating_raw)
                if correction:
                    adjustment = season_adjustments[row["season_slug"]][p["slug"]]
                    adjustment[0] += correction["final_kills"] - raw["kills"]
                    adjustment[1] += correction["final_deaths"] - raw["deaths"]
                player_matches[p["slug"]][row["season_slug"]].append(
                    {**public, "rating": rating_raw["rating"] if rating_eligible else None})
        rounds = [{"number": r.number, "side": next((p.side for p in r.players if p.team == row["our_team"]), "Unknown"),
                   "result": "Win" if r.winner == row["our_team"] else "Loss", "site": r.site}
                  for r in match.rounds]
        write(root / "matches" / f"{row['id']}.json", {**public, "players": public_players, "rounds": rounds})
        season_matches[row["season_slug"]].append(public)
    for season in seasons:
        slug = season["slug"]
        leaderboard = []
        for p in players:
            raw_total = aggregate_display(season_stats[slug][p["slug"]], display_version)
            delta = season_adjustments[slug][p["slug"]]
            effective = apply_display_kd(raw_total, raw_total["kills"] + delta[0],
                                         raw_total["deaths"] + delta[1])
            effective["rating"] = (aggregate(season_rating_stats[slug][p["slug"]], version)["rating"]
                                   if season_rating_stats[slug][p["slug"]] else None)
            if version == "siege_style_v3":
                effective.update(rating_rounds=sum(s["rounds"] for s in season_rating_stats[slug][p["slug"]]),
                                 rating_maps=len(season_rating_stats[slug][p["slug"]]))
            item = {"slug": p["slug"], "name": p["display_name"],
                    **effective}
            if p["tracked"] or season_stats[slug][p["slug"]]:
                leaderboard.append(item)
            write(root / "players" / p["slug"] / f"{slug}.json",
                  {**item, "season": slug, "matches": player_matches[p["slug"]][slug]})
        leaderboard.sort(key=lambda p: p["rating"] if p["rating"] is not None else float("-inf"), reverse=True)
        matches = season_matches[slug]
        write(root / "seasons" / f"{slug}.json",
              {"slug": slug, "name": season["name"], "start_date": season["start_date"],
               "end_date": season["end_date"], "demo": slug in demo_seasons,
               "maps": len(matches), "wins": sum(m["result"] == "WIN" for m in matches),
               "rounds_won": sum(m["our_score"] for m in matches),
               "rounds": sum(m["our_score"] + m["their_score"] for m in matches),
               "players": leaderboard, "matches": matches, "rating_version": version})
    for p in players:
        all_stats = [s for season in season_stats.values() for s in season[p["slug"]]]
        all_rating_stats = [s for season in season_rating_stats.values() for s in season[p["slug"]]]
        delta_k = sum(season[p["slug"]][0] for season in season_adjustments.values())
        delta_d = sum(season[p["slug"]][1] for season in season_adjustments.values())
        career_raw = aggregate_display(all_stats, display_version)
        career = apply_display_kd(career_raw, career_raw["kills"] + delta_k,
                                  career_raw["deaths"] + delta_d)
        career["rating"] = aggregate(all_rating_stats, version)["rating"] if all_rating_stats else None
        if version == "siege_style_v3":
            career.update(rating_rounds=sum(s["rounds"] for s in all_rating_stats), rating_maps=len(all_rating_stats))
        all_matches = [m for seasons_ in player_matches[p["slug"]].values() for m in seasons_]
        write(root / "players" / p["slug"] / "career.json",
              {"slug": p["slug"], "name": p["display_name"], "season": "career",
               **career, "matches": all_matches})
    write(root / "index.json", {"team": config["team"], "active_season": active,
                                "seasons": [{"slug": s["slug"], "name": s["name"],
                                             "start_date": s["start_date"], "end_date": s["end_date"]} for s in seasons],
                                "players": [{"slug": p["slug"], "name": p["display_name"],
                                             "active": bool(p["tracked"])} for p in players],
                                "rating_version": version})
    write(root / "methodology.json", {"rating_version": version,
                                      "trade_window_seconds": window,
                                      "kill_methodology": "Complete validated maps use Ubisoft credited round counters for kills, K/D, KPR, side kills, multikills and KOST Kill. Unsupported whole maps retain legacy finisher counts; kill_source_rounds reports coverage. Openings, trades, pivots, untraded features and clutch chronology retain legacy event semantics. Headshot percentage uses finisher headshots divided by finisher kills. V2 retains original version inputs; v3 uses verified native finisher opening/clutch chronology and complete credited/core objective inputs on eligible whole maps only.",
                                      "rating_description": (
                                          "Independent raw eight-feature Siege-style Rating. Historical objective upgrades preserve original v2 Rating inputs; displayed objectives and KOST use corrected data."
                                          if version == "siege_style_v2" else
                                          "Independently final-tested nine-feature native-order Rating. Complete credited kills, multikills and KOST Kill; verified core objectives; native first opposing finisher opening and triangular clutch size X(X+1)/2; frozen legacy 8-second trade features. Only eligible maps contribute to Rating; rating_rounds/rating_maps report coverage. Display statistics retain all historical maps and legacy event chronology. Not an official SiegeGG or Ubisoft formula."
                                          if version == "siege_style_v3" else "Collegiate V1 composite Rating.")})
    for path in root.rglob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))
