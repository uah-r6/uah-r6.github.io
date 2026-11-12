"""Private, persistent folder snapshots for ZIPs selected in rehost preview."""
import hashlib
import json
from pathlib import Path, PureWindowsPath
import tempfile
from uuid import uuid4
import zipfile


def replay_folder(source: Path, cache: Path) -> Path:
    source = source.expanduser().resolve()
    if source.suffix.lower() != '.zip':
        return source
    if not source.is_file():
        raise ValueError(f'Replay ZIP not found: {source}')
    with source.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    cache = cache.resolve()
    cache.mkdir(parents=True, exist_ok=True)
    destination = cache/digest
    marker = destination/'snapshot.json'
    if marker.is_file():
        try:
            saved = json.loads(marker.read_text(encoding='utf-8'))
            folder = (destination/saved['folder']).resolve()
            if folder.is_relative_to(destination) and saved['files'] == inventory(folder):
                return folder
        except (OSError, ValueError, KeyError):
            pass
    if destination.exists():
        destination = cache/f'{digest}-{uuid4().hex[:8]}'
    try:
        with tempfile.TemporaryDirectory(prefix='extract-', dir=cache) as temporary:
            staging = Path(temporary)
            with zipfile.ZipFile(source) as archive:
                members = archive.infolist()
                if sum(m.file_size for m in members) > 2*1024**3:
                    raise ValueError('Replay ZIP expands beyond the 2 GiB limit.')
                seen = set()
                for member in members:
                    name = member.filename.replace('\\', '/')
                    target = (staging/name).resolve()
                    if (PureWindowsPath(name).drive or not target.is_relative_to(staging)
                            or str(target).casefold() in seen or (member.external_attr >> 16) & 0o170000 == 0o120000):
                        raise ValueError('Replay ZIP contains an unsafe or duplicate path.')
                    seen.add(str(target).casefold())
                archive.extractall(staging)
            folders = {p.parent for p in staging.rglob('*') if p.is_file() and p.suffix.lower()=='.rec'}
            if len(folders) != 1:
                raise ValueError('Each rehost ZIP must contain exactly one replay folder. Select separate ZIPs for separate segments.')
            folder = folders.pop()
            relative = folder.relative_to(staging)
            payload = inventory(folder)
            # Move only this tool-owned snapshot, retaining a stable source for
            # preview fingerprint validation and the existing archive importer.
            staging.rename(destination)
            (destination/'snapshot.json').write_text(json.dumps({'folder':str(relative),'files':payload}), encoding='utf-8')
            return destination/relative
    except zipfile.BadZipFile as error:
        raise ValueError('The selected replay ZIP is invalid or incomplete.') from error


def inventory(folder):
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.glob('*.rec')) if p.is_file()}
