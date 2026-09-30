"""The only module aware of siege-dissect's JSON schema and CLI."""
import hashlib
import json
import logging
import re
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from .models import Kill, Match, Objective, Player, Round

LOG = logging.getLogger(__name__)

# siege-dissect's pinned map table predates these current replay map IDs.
# The IDs were checked against objective sites in local Y11S3 replays.
MAP_IDS = {398899676157: "Fortress", 409325881472: "Villa", 436375283234: "Coastline"}
MAP_LABELS = {"ClubHouseY10": "Clubhouse", "BorderY10": "Border",
              "KafeDostoyevskyY10": "Kafe Dostoyevsky", "ChaletY10": "Chalet",
              "LairY10": "Lair", "NighthavenLabsY10": "Nighthaven Labs"}


def parser_executable() -> str | None:
    local = Path(__file__).resolve().parents[2] / ".local-tools/bin/siege-dissect.exe"
    if local.is_file():
        return str(local)
    return shutil.which("siege-dissect")


def label(value):
    return value.get("name", "Unknown") if isinstance(value, dict) else str(value or "Unknown")


def map_label(value):
    name = label(value)
    if isinstance(value, dict) and name.startswith("Map("):
        return MAP_IDS.get(value.get("id"), name)
    return MAP_LABELS.get(name, name)


def physical_round_numbers(files: list[Path]) -> list[int]:
    """Use R01/R02/... sources as round identity, including for renamed folders."""
    numbers = []
    for source in files:
        match = re.search(r"-R(\d+)\.rec$", source.name, re.IGNORECASE)
        if not match:
            raise ValueError(f"Replay round filename has no -R## suffix: {source.name}")
        numbers.append(int(match.group(1)))
    if len(set(numbers)) != len(numbers):
        raise ValueError("Replay contains duplicate physical round sources (-R## filenames).")
    if sorted(numbers) != list(range(1, len(files) + 1)):
        raise ValueError("Replay physical rounds must be complete and start at R01.")
    return numbers


def reject_duplicate_round_contents(files: list[Path]) -> None:
    """Only hash same-sized files; copied .rec rounds cannot count twice."""
    by_size: dict[int, list[Path]] = {}
    for source in files:
        by_size.setdefault(source.stat().st_size, []).append(source)
    for candidates in by_size.values():
        if len(candidates) < 2:
            continue
        seen: set[str] = set()
        for source in candidates:
            digest = hashlib.sha256()
            with source.open("rb") as replay:
                for chunk in iter(lambda: replay.read(1024 * 1024), b""):
                    digest.update(chunk)
            signature = digest.hexdigest()
            if signature in seen:
                raise ValueError("Replay contains duplicate physical .rec file contents.")
            seen.add(signature)


def normalize(raw, *, round_numbers: list[int] | None = None) -> Match:
    """Normalize the CLI's match array (or a round object for fixture testing)."""
    rows = raw if isinstance(raw, list) else raw.get("rounds", [raw])
    if not rows:
        raise ValueError("Parser returned no rounds.")
    if round_numbers is not None and len(round_numbers) != len(rows):
        raise ValueError("Parser round count differs from .rec file count; no import was made.")
    result = []
    match_ids = set()
    types = set()
    maps = set()
    for ordinal, source in enumerate(rows, 1):
        row = source.get("header", source)
        if row.get("matchID") or row.get("matchId"):
            match_ids.add(str(row.get("matchID") or row.get("matchId")))
        types.add(label(row.get("matchType")))
        maps.add(map_label(row.get("map") or row.get("mapName")))
        raw_players = row.get("players") or []
        if len(raw_players) < 2 or len(row.get("teams") or []) != 2:
            raise ValueError(f"Round {ordinal} lacks two teams or player identities.")
        players = []
        for p in raw_players:
            team = int(p["teamIndex"])
            side = label(row["teams"][team].get("role"))
            operator = label(p.get("operator"))
            # A Y11 initial selection can precede attacker repick. The local
            # parser must explicitly confirm the action-start selection.
            if str(row.get("gameVersion") or "").startswith("Y11") and side == "Attack":
                if (not row.get("actionPhaseDetected") or
                        p.get("operatorSource") != "action_start_header" or
                        not p.get("operatorSeenBeforeAction")):
                    operator = "Unknown"
            players.append(Player(str(p.get("profileID") or ""), str(p.get("username") or ""),
                                  team, operator, side))
        names = {}
        for p in players:
            key = p.username.strip().casefold()
            if key in names:
                raise ValueError(f"Round {ordinal} has ambiguous username {p.username!r}.")
            names[key] = p
        kills = []
        objectives = []
        for seq, event in enumerate(source.get("matchFeedback") or row.get("matchFeedback") or []):
            kind = label(event.get("type")).casefold()
            remaining = float(event.get("timeInSeconds") or 0)
            if kind == "kill":
                killer = names.get(str(event.get("username") or "").strip().casefold())
                victim = names.get(str(event.get("target") or "").strip().casefold())
                if not killer or not victim:
                    raise ValueError(f"Round {ordinal} has a kill with an unresolved participant; no import was made.")
                kills.append(Kill(seq, remaining, killer.key, victim.key, killer.team,
                                  victim.team, bool(event.get("headshot"))))
            elif kind == "death":
                victim = names.get(str(event.get("username") or event.get("target") or "").strip().casefold())
                if victim:
                    kills.append(Kill(seq, remaining, "", victim.key, -1, victim.team))
            elif kind in {"defuserplantcomplete", "defuserdisablecomplete", "plant", "disable"}:
                actor = names.get(str(event.get("username") or "").strip().casefold())
                if actor:
                    objectives.append(Objective("plant" if "plant" in kind else "disable",
                                                actor.key, actor.team, remaining))
                else:
                    LOG.warning("Skipping objective without known actor in round %s", ordinal)
            elif kind not in {"other", "downbutnotout", "objective", "defuserplantstart", "defuserdisablestart", "locateobjective", "operatorswap", "battleye", "playerleave"}:
                LOG.debug("Unrecognized feedback type: %s", kind)
        teams = row["teams"]
        wins = [i for i, t in enumerate(teams) if t.get("won") is True]
        if len(wins) != 1:
            raise ValueError(f"Round {ordinal} has no unambiguous winner.")
        # The parser field is zero-based in current replays; physical filenames
        # identify rounds during real imports. Fixtures without files use order.
        number = round_numbers[ordinal - 1] if round_numbers is not None else ordinal
        result.append(Round(number, str(row.get("site") or "Unknown"), wins[0],
                            str(teams[wins[0]].get("winCondition") or "Unknown"),
                            players, kills, objectives))
    if len(types) != 1 or len(maps) != 1 or len(match_ids) > 1:
        raise ValueError("Replay rounds disagree on match type, map, or match ID.")
    numbers = [r.number for r in result]
    if len(set(numbers)) != len(numbers):
        raise ValueError("Replay contains duplicate physical round numbers.")
    timestamp = str((rows[0].get("header", rows[0])).get("timestamp") or "")
    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Replay has no valid timestamp.") from exc
    return Match(next(iter(match_ids), ""), timestamp, next(iter(maps)), next(iter(types)),
                 label((rows[0].get("header", rows[0])).get("gamemode")),
                 sorted(result, key=lambda r: r.number))


def parse_match(path: str | Path, *, allow_incomplete: bool = False) -> Match:
    source = Path(path).expanduser()
    if source.suffix.lower() == ".rec":
        raise ValueError("Select the whole match folder or its ZIP, not one .rec round.")
    if not source.exists():
        raise ValueError(f"Replay path does not exist: {source}")
    executable = parser_executable()
    if not executable:
        raise ValueError("siege-dissect was not found. Run scripts/setup.ps1 to build the local parser.")
    with tempfile.TemporaryDirectory() as tmp:
        target = source
        if source.suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(source) as archive:
                    for member in archive.infolist():
                        dest = (Path(tmp) / member.filename).resolve()
                        if not dest.is_relative_to(Path(tmp).resolve()):
                            raise ValueError("ZIP contains an unsafe path.")
                    archive.extractall(tmp)
            except zipfile.BadZipFile as exc:
                raise ValueError("The selected ZIP is not a valid replay archive.") from exc
            folders = [p for p in Path(tmp).rglob("*") if p.is_dir() and list(p.glob("*.rec"))]
            if len(folders) != 1:
                raise ValueError("ZIP must contain exactly one complete replay folder.")
            target = folders[0]
        files = sorted(target.glob("*.rec")) if target.is_dir() else []
        if not files or (len(files) < 2 and not allow_incomplete):
            raise ValueError("A whole match folder with multiple .rec rounds is required.")
        numbers = physical_round_numbers(files)
        reject_duplicate_round_contents(files)
        output = Path(tmp) / "match.json"
        try:
            process = subprocess.run([executable, str(target), "-o", str(output)],
                                     capture_output=True, text=True, timeout=180)
        except subprocess.TimeoutExpired as exc:
            raise ValueError("siege-dissect timed out while parsing this match.") from exc
        if process.returncode or not output.exists():
            lines = (process.stderr or process.stdout).strip().splitlines()
            reason = next((line.strip() for line in lines if line.strip().startswith(("panic:", "ERR", "error:"))),
                          lines[0].strip() if lines else "no JSON was produced")
            raise ValueError(f"siege-dissect cannot parse {target.name}: {reason}")
        try:
            match = normalize(json.loads(output.read_text(encoding="utf-8")), round_numbers=numbers)
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ValueError(f"Could not normalize siege-dissect output: {exc}") from exc
        return match
