"""Deterministic synthetic maps kept separate from real season data."""
import hashlib
import random
from datetime import datetime, timedelta, timezone

from r6stats.db import repository as repo
from r6stats.export import export
from r6stats.parser.models import Kill, Match, Objective, Player, Round


def run(db, config, clear=False):
    if clear:
        with db:
            db.execute("DELETE FROM maps WHERE series_id IN (SELECT id FROM series WHERE demo=1)")
            db.execute("DELETE FROM series WHERE demo=1")
            db.execute("DELETE FROM aliases WHERE player_id IN (SELECT id FROM players WHERE username LIKE 'DemoPlayer%' AND profile_id LIKE 'demo-ours-%')")
            db.execute("DELETE FROM players WHERE username LIKE 'DemoPlayer%' AND profile_id LIKE 'demo-ours-%'")
            db.execute("UPDATE players SET profile_id=NULL WHERE profile_id LIKE 'demo-ours-%'")
            db.execute("DELETE FROM seasons WHERE name='Demo Season' AND NOT EXISTS (SELECT 1 FROM series WHERE season_id=seasons.id)")
            if not db.execute("SELECT 1 FROM seasons WHERE active=1").fetchone():
                db.execute("UPDATE seasons SET active=1 WHERE id=(SELECT max(id) FROM seasons)")
        export(db, config)
        print("Demo maps cleared. Real statistics were preserved.")
        return
    if db.execute("SELECT 1 FROM series WHERE demo=0 LIMIT 1").fetchone():
        raise ValueError("Demo data cannot be mixed with real match data. Use a fresh database.")
    if db.execute("SELECT 1 FROM series WHERE demo=1 LIMIT 1").fetchone():
        raise ValueError("Demo data already exists. Run demo --clear first.")
    season = db.execute("SELECT id FROM seasons WHERE active=1").fetchone()
    if not season:
        repo.season_create(db, "Demo Season")
    own = [dict(row) for row in db.execute("SELECT * FROM players WHERE tracked=1 ORDER BY id LIMIT 5")]
    if len(own) < 5:
        for i in range(len(own), 5):
            repo.roster_add(db, f"DemoPlayer{i+1}", team_id=1)
        own = [dict(row) for row in db.execute("SELECT * FROM players WHERE tracked=1 ORDER BY id LIMIT 5")]
    randomizer = random.Random(41)
    for map_index, (map_name, opponent) in enumerate([("Clubhouse", "North College"), ("Bank", "East University"),
                                                       ("Chalet", "Western Tech"), ("Border", "South State")]):
        rounds = []
        for number in range(1, 12):
            side = "Attack" if number <= 6 else "Defense"
            players = [Player(f"demo-ours-{i}", p["username"], 0,
                              randomizer.choice(["Buck", "Ash", "Nomad"] if side == "Attack" else ["Wamai", "Azami", "Jager"]), side)
                       for i, p in enumerate(own)]
            players += [Player(f"demo-enemy-{i}", f"DemoEnemy{i+1}", 1,
                               "Unknown", "Defense" if side == "Attack" else "Attack") for i in range(5)]
            kills = []
            remaining = 160
            alive = [list(range(5)), list(range(5, 10))]
            for sequence in range(randomizer.randint(5, 9)):
                attacking = randomizer.randrange(2)
                defending = 1 - attacking
                if not alive[attacking] or not alive[defending]:
                    break
                killer = players[randomizer.choice(alive[attacking])]
                victim_index = randomizer.choice(alive[defending])
                victim = players[victim_index]
                kills.append(Kill(sequence, remaining, killer.key, victim.key, attacking, defending,
                                  randomizer.random() < 0.42))
                alive[defending].remove(victim_index)
                remaining -= randomizer.randint(3, 19)
            winner = randomizer.choices([0, 1], weights=[0.57, 0.43])[0]
            objectives = []
            if side == "Attack" and randomizer.random() < 0.25:
                planter = randomizer.choice(players[:5])
                objectives.append(Objective("plant", planter.key, 0, 32))
            rounds.append(Round(number, randomizer.choice(["2F Gym", "1F Kitchen", "B Arsenal"]),
                                winner, "KilledOpponents", players, kills, objectives))
        timestamp = (datetime(2026, 9, 10, tzinfo=timezone.utc) + timedelta(days=map_index*7)).isoformat()
        match = Match(f"demo-match-{map_index}", timestamp, map_name, "Custom Game", "Bomb", rounds)
        repo.insert_map(db, match, hashlib.sha256(match.replay_id.encode()).hexdigest(), 0,
                        opponent, str(map_index + 1), "Synthetic demonstration", demo=True, organization_team_id=1)
    export(db, config)
    print("Created four clearly labeled synthetic NECC maps. Run demo --clear before real imports.")
