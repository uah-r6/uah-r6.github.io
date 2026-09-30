"""Replay eligibility is based only on the Siege match type.

NECC is application metadata assigned after a user confirms an eligible map.
"""


def is_custom_game(match_type: str) -> bool:
    normalized = "".join(character for character in match_type.casefold() if character.isalnum())
    return normalized in {"custom", "customgame", "customgamelocal", "customgameonline"}


def scan_label(match_type: str) -> str:
    if is_custom_game(match_type):
        normalized = "".join(character for character in match_type.casefold() if character.isalnum())
        display = {"customgamelocal": "Custom Game (Local)",
                   "customgameonline": "Custom Game (Online)"}.get(normalized, "Custom Game")
        return f"{display} - eligible for manual NECC import"
    return f"INELIGIBLE - {match_type}"


def rejection_message(match_type: str) -> str:
    if match_type.strip().casefold() == "ranked":
        return "Import rejected. This replay is a Ranked match. No statistics were changed."
    return (f"Import rejected. This replay is {match_type}, not a Custom Game. "
            "Only manually confirmed Custom Game replays can be labeled NECC. "
            "No statistics were changed.")
