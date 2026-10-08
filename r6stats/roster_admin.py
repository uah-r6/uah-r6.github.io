"""Transactional unused-player deletion with staged, restorable public exports."""
from pathlib import Path
import tempfile

from r6stats.db import repository as repo
from r6stats.export import export
from r6stats.publishing import validate_public_data


def delete_and_export(db, player_id, confirmation, config, root):
    root = Path(root).resolve()
    public = (root/'web/public/data').resolve()
    data = (root/'data').resolve()
    if not public.is_relative_to(root/'web/public') or not data.is_relative_to(root):
        raise ValueError('Roster export paths must remain inside this project.')
    data.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.roster-delete-', dir=data) as folder:
        stage = Path(folder).resolve()
        if not stage.is_relative_to(data):
            raise ValueError('Roster export staging path is outside this project.')
        generated, parked = stage/'generated/web/public/data', stage/'previous-public'
        installed = False
        def prepare_export():
            nonlocal installed
            export(db, config, generated)
            validate_public_data(stage/'generated')
            public.parent.mkdir(parents=True, exist_ok=True)
            if public.exists():
                public.rename(parked)
            generated.rename(public)
            installed = True
        try:
            repo.roster_delete(db, player_id, confirmation, before_commit=prepare_export)
        except Exception:
            if installed and public.exists():
                public.rename(stage/'failed-public')
            if parked.exists():
                parked.rename(public)
            raise
    return dict(ok=True, message='Mistaken player permanently deleted; aliases and memberships removed. Website data regenerated. Historical matches and players preserved.')
