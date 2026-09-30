"""LAN replay nil UUIDs must not collapse ten players into one identity."""
from r6stats.parser.models import Player
from r6stats.parser.siege_dissect import normalize
from r6stats.stats.calculate import calculate_match


def test_nil_uuid_uses_replay_username_for_kill_identity():
    nil = "00000000-0000-0000-0000-000000000000"
    assert Player(nil, "Alice", 0).key == "alice"
    raw = {"header": {"matchID": "lan", "timestamp": "2026-02-02T14:17:03Z",
                      "matchType": "CustomGameLocal", "map": {"name": "ClubHouseY10"},
                      "teams": [{"role": "Attack", "won": True},
                                {"role": "Defense", "won": False}],
                      "players": [{"profileID": nil, "username": "Alice", "teamIndex": 0},
                                  {"profileID": nil, "username": "Bob", "teamIndex": 1}]},
           "matchFeedback": [{"type": "Kill", "username": "Alice", "target": "Bob",
                              "timeInSeconds": 60}]}
    match = normalize(raw, round_numbers=[1])
    stats = calculate_match(match)
    assert set(stats) == {"alice", "bob"}
    assert stats["alice"]["kills"] == 1
    assert stats["bob"]["deaths"] == 1
