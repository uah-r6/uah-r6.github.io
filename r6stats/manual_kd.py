"""Auditable final-map K/D overrides; replay-derived round statistics stay intact."""
import json
from collections import defaultdict
from datetime import datetime, timezone

from r6stats.parser.models import Match
from r6stats.stats.calculate import calculate_match
from r6stats.credited_refresh import display_stats, load as load_credit


def map_players(db, map_id: str, trade_window_seconds: float) -> list[dict]:
    row = db.execute("SELECT normalized_json FROM maps WHERE id=?", (map_id,)).fetchone()
    if not row:
        raise ValueError("NECC map not found.")
    stats = display_stats(Match.from_dict(json.loads(row["normalized_json"])), load_credit(db, map_id), trade_window_seconds)
    players = db.execute("""SELECT DISTINCT p.id,p.display_name,p.tracked,rp.player_key
        FROM round_players rp JOIN rounds r ON r.id=rp.round_id
        JOIN players p ON p.id=rp.player_id WHERE r.map_id=? ORDER BY p.display_name""", (map_id,))
    grouped = defaultdict(lambda: {"keys": set(), "name": "", "tracked": False})
    for p in players:
        group = grouped[p["id"]]
        group["keys"].add(p["player_key"])
        group["name"] = p["display_name"]
        group["tracked"] = bool(p["tracked"])
    results = []
    for player_id, group in grouped.items():
        correction = db.execute("SELECT * FROM map_kd_corrections WHERE map_id=? AND player_id=?",
                                (map_id, player_id)).fetchone()
        raw_k = sum(stats[key]["kills"] for key in group["keys"] if key in stats)
        raw_d = sum(stats[key]["deaths"] for key in group["keys"] if key in stats)
        final_k = correction["final_kills"] if correction else raw_k
        final_d = correction["final_deaths"] if correction else raw_d
        results.append({"player_id": player_id, "name": group["name"],
                        "tracked": group["tracked"], "replay_kills": raw_k,
                        "replay_deaths": raw_d, "final_kills": final_k,
                        "final_deaths": final_d, "kill_adjustment": final_k - raw_k,
                        "death_adjustment": final_d - raw_d,
                        "reason": correction["reason"] if correction else "",
                        "note": correction["note"] if correction else "",
                        "updated_at": correction["updated_at"] if correction else None,
                        "corrected": bool(correction)})
    return results


def save(db, map_id: str, player_id: int, final_kills: int, final_deaths: int,
         reason: str, note: str, trade_window_seconds: float) -> dict:
    if min(final_kills, final_deaths) < 0:
        raise ValueError("Final kills and deaths cannot be negative.")
    if not reason.strip():
        raise ValueError("A correction reason is required.")
    player = next((p for p in map_players(db, map_id, trade_window_seconds)
                   if p["player_id"] == player_id), None)
    if not player:
        raise ValueError("Choose a tracked player who participated in this map.")
    stamp = datetime.now(timezone.utc).isoformat()
    with db:
        db.execute("""INSERT INTO map_kd_corrections
            (map_id,player_id,replay_kills,replay_deaths,final_kills,final_deaths,reason,note,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(map_id,player_id) DO UPDATE SET
            replay_kills=excluded.replay_kills,replay_deaths=excluded.replay_deaths,
            final_kills=excluded.final_kills,final_deaths=excluded.final_deaths,
            reason=excluded.reason,note=excluded.note,updated_at=excluded.updated_at""",
            (map_id, player_id, player["replay_kills"], player["replay_deaths"],
             final_kills, final_deaths, reason.strip(), note.strip(), stamp))
        db.execute("UPDATE maps SET replay_data_complete=0 WHERE id=?", (map_id,))
    return next(p for p in map_players(db, map_id, trade_window_seconds) if p["player_id"] == player_id)


def remove(db, map_id: str, player_id: int) -> None:
    with db:
        result = db.execute("DELETE FROM map_kd_corrections WHERE map_id=? AND player_id=?",
                            (map_id, player_id))
        if not result.rowcount:
            raise ValueError("No manual K/D correction exists for this player and map.")
    # Incompleteness is an independent audit fact: removing a correction does not
    # silently claim that missing replay rounds have been recovered.


def apply_display_kd(stats: dict, final_kills: int, final_deaths: int) -> dict:
    result = {**stats, "kills": final_kills, "deaths": final_deaths}
    if (final_kills, final_deaths) != (stats['kills'], stats['deaths']):
        result['kill_source'] = 'manual_final_kd_over_round_sources'
    result["kd"] = final_kills / final_deaths if final_deaths else None
    result["kd_diff"] = final_kills - final_deaths
    return result
