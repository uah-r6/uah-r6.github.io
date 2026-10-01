"""Private, map-ID keyed copies of confirmed NECC replay rounds."""

import hashlib
import json
import shutil
import tempfile
from uuid import uuid4
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from r6stats.parser.siege_dissect import (parser_executable, physical_round_numbers,
                                          reject_duplicate_round_contents)

FORMAT_VERSION = 1
REHOST_FORMAT_VERSION = 2


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def replay_fingerprint(files: list[Path]) -> str:
    """Match the existing fingerprint convention without loading rounds into RAM."""
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda file: file.name):
        digest.update(path.name.encode())
        with path.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


@dataclass
class PreparedArchive:
    staging: Path
    source: Path
    original_folder_name: str
    fingerprint: str
    files: list[dict]

    def cleanup(self) -> None:
        if self.staging.exists():
            shutil.rmtree(self.staging)


@dataclass
class PreparedRehostArchive:
    staging: Path
    fingerprint: str
    source_manifest: dict
    segments: list[dict]

    def cleanup(self) -> None:
        if self.staging.exists():
            shutil.rmtree(self.staging)


def prepare(source: str | Path, archive_root: Path, expected_fingerprint: str,
            expected_rounds: int) -> PreparedArchive:
    """Copy verified rounds into an incomplete private staging directory."""
    source = Path(source).expanduser().resolve()
    archive_root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".pending-", dir=archive_root))
    try:
        if source.suffix.lower() == ".zip":
            with zipfile.ZipFile(source) as archive:
                members = [member for member in archive.infolist()
                           if not member.is_dir() and member.filename.lower().endswith(".rec")]
                if len({str(Path(member.filename).parent) for member in members}) != 1:
                    raise ValueError("ZIP must contain one replay folder.")
                if len({Path(member.filename).name.casefold() for member in members}) != len(members):
                    raise ValueError("ZIP contains duplicate replay filenames.")
                folder_name = Path(members[0].filename).parent.name if members else source.stem
                for member in members:
                    name = Path(member.filename).name
                    with archive.open(member) as src, (staging / name).open("wb") as dest:
                        shutil.copyfileobj(src, dest, 1024 * 1024)
        elif source.is_dir():
            folder_name = source.name
            for path in source.glob("*.rec"):
                shutil.copy2(path, staging / path.name)
        else:
            raise ValueError("Select a whole replay folder or ZIP.")
        files = sorted(staging.glob("*.rec"))
        if len(files) != expected_rounds:
            raise ValueError("Archive copy has a different round count from the imported map.")
        numbers = physical_round_numbers(files)
        reject_duplicate_round_contents(files)
        copied_fingerprint = replay_fingerprint(files)
        if copied_fingerprint != expected_fingerprint:
            raise ValueError("Replay changed while copying; no map was archived.")
        entries = [{"filename": path.name, "physical_round_number": number,
                    "size": path.stat().st_size, "sha256": sha256(path)}
                   for path, number in zip(files, numbers)]
        return PreparedArchive(staging, source, folder_name, copied_fingerprint, entries)
    except Exception:
        shutil.rmtree(staging)
        raise


def prepare_rehost(paths: list[Path], archive_root: Path, expected_fingerprint: str,
                   source_manifest: dict) -> PreparedRehostArchive:
    """Stage every physical segment, including excluded rounds, unchanged."""
    from r6stats.parser.confirmed_rehost import manifest_fingerprint

    if manifest_fingerprint(source_manifest) != expected_fingerprint:
        raise ValueError("Rehost identity changed since preview.")
    if len(paths) != len(source_manifest["segments"]):
        raise ValueError("Rehost segment count changed since preview.")
    archive_root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".pending-", dir=archive_root))
    try:
        all_entries = []
        segments = []
        for index, (original, segment) in enumerate(zip(paths, source_manifest["segments"]), start=1):
            source = original.expanduser().resolve()
            if not source.is_dir():
                raise ValueError("Rehost source folder is missing.")
            folder = staging / f"segment-{index:02d}"
            folder.mkdir()
            for path in source.glob("*.rec"):
                shutil.copy2(path, folder / path.name)
            files = sorted(folder.glob("*.rec"))
            numbers = physical_round_numbers(files)
            reject_duplicate_round_contents(files)
            if replay_fingerprint(files) != segment["fingerprint"]:
                raise ValueError("A rehost segment changed while copying.")
            entries = [{"filename": file.name, "physical_round_number": number,
                        "size": file.stat().st_size, "sha256": sha256(file)}
                       for file, number in zip(files, numbers)]
            all_entries.extend((index, entry) for entry in entries)
            segments.append({**segment, "files": entries, "physical_round_count": len(entries)})
        actual = {(index, entry["physical_round_number"]):
                  (entry["filename"], entry["sha256"])
                  for index, entry in all_entries}
        expected = {(item["segment"], item["physical_number"]):
                    (item["filename"], item["sha256"])
                    for item in source_manifest["mapping"]}
        if actual != expected or len(all_entries) != len(source_manifest["mapping"]):
            raise ValueError("Archived physical rounds differ from confirmed rehost mapping.")
        return PreparedRehostArchive(staging, expected_fingerprint, source_manifest, segments)
    except Exception:
        shutil.rmtree(staging)
        raise


def map_record(db, map_id: str):
    return db.execute("""SELECT m.id,m.replay_id,m.fingerprint,m.map_name,m.normalized_json,m.rehost_json,
                        se.slug AS season_slug FROM maps m JOIN series s ON s.id=m.series_id
                        JOIN seasons se ON se.id=s.season_id WHERE m.id=? AND s.demo=0""",
                      (map_id,)).fetchone()


def archive_path(archive_root: Path, row) -> Path:
    # Season slugs and map IDs are generated by this application, but keep the
    # private archive rooted even if an old database contains malformed values.
    target = (archive_root / row["season_slug"] / row["id"]).resolve()
    if not target.is_relative_to(archive_root.resolve()):
        raise ValueError("Invalid archive path in database.")
    return target


def commit(prepared: PreparedArchive, archive_root: Path, db, map_id: str) -> Path:
    row = map_record(db, map_id)
    if not row:
        raise ValueError("Imported NECC map not found for replay archive.")
    if row["fingerprint"] != prepared.fingerprint or len(json.loads(row["normalized_json"])["rounds"]) != len(prepared.files):
        raise ValueError("Archive copy does not match the imported map.")
    target = archive_path(archive_root, row)
    if target.exists():
        raise ValueError("This map already has a replay archive.")
    parser = parser_executable()
    manifest = {"archive_format_version": FORMAT_VERSION, "map_id": map_id,
                "replay_id": row["replay_id"], "replay_fingerprint": row["fingerprint"],
                "original_folder_name": prepared.original_folder_name,
                "original_source_path": str(prepared.source),
                "archived_at": datetime.now(timezone.utc).isoformat(),
                "parser_sha256": sha256(Path(parser)) if parser else None,
                "map_name": row["map_name"], "round_count": len(prepared.files),
                "files": prepared.files}
    (prepared.staging / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    prepared.staging.rename(target)
    return target


def commit_rehost(prepared: PreparedRehostArchive, archive_root: Path, db, map_id: str) -> Path:
    row = map_record(db, map_id)
    if not row or not row["rehost_json"]:
        raise ValueError("Imported rehost map not found for archive.")
    source_manifest = json.loads(row["rehost_json"])
    if (row["fingerprint"] != prepared.fingerprint or
            source_manifest != prepared.source_manifest or
            len(json.loads(row["normalized_json"])["rounds"]) !=
            sum(item["logical_number"] is not None for item in source_manifest["mapping"])):
        raise ValueError("Archive copy does not match the imported logical map.")
    target = archive_path(archive_root, row)
    if target.exists():
        raise ValueError("This map already has a replay archive.")
    parser = parser_executable()
    manifest = {"archive_format_version": REHOST_FORMAT_VERSION, "map_id": map_id,
                "replay_id": row["replay_id"], "replay_fingerprint": row["fingerprint"],
                "map_name": row["map_name"],
                "round_count": len(json.loads(row["normalized_json"])["rounds"]),
                "physical_round_count": sum(len(item["files"]) for item in prepared.segments),
                "source_manifest": source_manifest, "segments": prepared.segments,
                "archived_at": datetime.now(timezone.utc).isoformat(),
                "parser_sha256": sha256(Path(parser)) if parser else None}
    (prepared.staging / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    prepared.staging.rename(target)
    return target


def verify(db, archive_root: Path, map_id: str) -> dict:
    row = map_record(db, map_id)
    if not row:
        raise ValueError("NECC map not found.")
    target = archive_path(archive_root, row)
    result = {"status": "Missing", "message": "Replay archive not found.",
              "rounds": 0, "path": str(target)}
    if not target.is_dir():
        return result
    manifest_path = target / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("archive_format_version") == REHOST_FORMAT_VERSION:
            return _verify_rehost(row, target, manifest, result)
        expected_count = len(json.loads(row["normalized_json"])["rounds"])
        files = manifest["files"]
        if (manifest["archive_format_version"] != FORMAT_VERSION or
            manifest["map_id"] != map_id or manifest["replay_id"] != row["replay_id"] or
            manifest["replay_fingerprint"] != row["fingerprint"] or
            manifest["map_name"] != row["map_name"] or
            manifest["round_count"] != expected_count or len(files) != expected_count or
            len({entry["filename"].casefold() for entry in files}) != len(files) or
            any(Path(entry["filename"]).name != entry["filename"] for entry in files)):
            raise ValueError("Manifest does not match this imported map.")
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        return {**result, "status": "Manifest invalid", "message": str(error)}
    paths = [target / entry["filename"] for entry in files]
    if any(not path.is_file() or not path.resolve().is_relative_to(target) for path in paths):
        return {**result, "status": "Incomplete", "message": "An archived .rec round is missing or unsafe."}
    if {path.name for path in target.glob("*.rec")} != {path.name for path in paths}:
        return {**result, "status": "Incomplete", "message": "Archive .rec file list differs from its manifest."}
    try:
        numbers = physical_round_numbers(paths)
        if any(entry["physical_round_number"] != number for entry, number in zip(files, numbers)):
            raise ValueError("Physical round numbers differ from the manifest.")
    except ValueError as error:
        return {**result, "status": "Incomplete", "message": str(error)}
    for path, entry in zip(paths, files):
        if path.stat().st_size != entry["size"] or sha256(path) != entry["sha256"]:
            return {**result, "status": "Hash mismatch", "message": f"Archived round failed integrity check: {path.name}"}
    if replay_fingerprint(paths) != row["fingerprint"]:
        return {**result, "status": "Hash mismatch", "message": "Archive fingerprint differs from imported map."}
    return {**result, "status": "Healthy", "message": "All archived rounds verified.", "rounds": len(paths)}


def _verify_rehost(row, target: Path, manifest: dict, result: dict) -> dict:
    from r6stats.parser.confirmed_rehost import manifest_fingerprint

    try:
        source = json.loads(row["rehost_json"])
        segments = manifest["segments"]
        mapping = source["mapping"]
        expected_count = len(json.loads(row["normalized_json"])["rounds"])
        if (manifest["map_id"] != row["id"] or manifest["replay_id"] != row["replay_id"] or
            manifest["replay_fingerprint"] != row["fingerprint"] or
            manifest["map_name"] != row["map_name"] or
            manifest["source_manifest"] != source or
            manifest_fingerprint(source) != row["fingerprint"] or
            manifest["round_count"] != expected_count or
            expected_count != sum(item["logical_number"] is not None for item in mapping) or
            len(segments) != len(source["segments"]) or len(segments) < 2 or
            manifest["physical_round_count"] != len(mapping)):
            raise ValueError("Manifest does not match this imported logical map.")
        actual = {}
        for index, (segment, original) in enumerate(zip(segments, source["segments"]), start=1):
            if any(segment.get(key) != original[key] for key in
                   ("segment", "source_path", "source_name", "replay_id", "fingerprint")):
                raise ValueError("Archived segment identity differs from imported map.")
            folder = target / f"segment-{index:02d}"
            if not folder.is_dir():
                return {**result, "status": "Incomplete", "message": f"Segment {index} is missing."}
            entries = segment["files"]
            if segment["physical_round_count"] != len(entries) or len({
                    entry["filename"].casefold() for entry in entries}) != len(entries):
                raise ValueError("Archived segment file list is invalid.")
            files = []
            for entry in entries:
                if Path(entry["filename"]).name != entry["filename"]:
                    raise ValueError("Archived filename is unsafe.")
                file = folder / entry["filename"]
                if not file.is_file() or not file.resolve().is_relative_to(target.resolve()):
                    return {**result, "status": "Incomplete", "message": f"Segment {index} round is missing."}
                files.append(file)
                actual[(index, entry["physical_round_number"])] = (
                    entry["filename"], entry["sha256"])
                if file.stat().st_size != entry["size"] or sha256(file) != entry["sha256"]:
                    return {**result, "status": "Hash mismatch", "message":
                            f"Archived segment {index} round failed integrity check: {file.name}"}
            if {file.name for file in folder.glob("*.rec")} != {file.name for file in files}:
                return {**result, "status": "Incomplete", "message":
                        f"Segment {index} .rec file list differs from manifest."}
            if physical_round_numbers(files) != [entry["physical_round_number"] for entry in entries]:
                raise ValueError("Archived physical round numbers differ from manifest.")
            if replay_fingerprint(files) != segment["fingerprint"]:
                return {**result, "status": "Hash mismatch", "message":
                        f"Archived segment {index} fingerprint differs from imported map."}
        expected = {(item["segment"], item["physical_number"]):
                    (item["filename"], item["sha256"]) for item in mapping}
        if actual != expected or len(actual) != len(mapping):
            raise ValueError("Physical-to-logical mapping differs from archived files.")
        if {item.name for item in target.iterdir() if item.is_dir()} != {
                f"segment-{index:02d}" for index in range(1, len(segments) + 1)}:
            return {**result, "status": "Incomplete", "message": "Archive has unexpected segment folders."}
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        return {**result, "status": "Manifest invalid", "message": str(error)}
    return {**result, "status": "Healthy", "message":
            "All physical segments and logical mapping verified.", "rounds": expected_count}


def delete_map_and_archive(db, archive_root: Path, map_id: str) -> None:
    """Move the archive aside before deleting the map; restore it on DB failure."""
    from r6stats.db import repository as repo

    row = map_record(db, map_id)
    if not row:
        raise ValueError("NECC map not found.")
    target = archive_path(archive_root, row)
    parked = archive_root / f".pending-delete-{uuid4().hex}"
    if target.exists():
        target.rename(parked)
    try:
        repo.match_delete(db, map_id)
    except Exception:
        if parked.exists():
            parked.rename(target)
        raise
    if parked.exists():
        shutil.rmtree(parked)
    if target.parent.is_dir() and not any(target.parent.iterdir()):
        target.parent.rmdir()
