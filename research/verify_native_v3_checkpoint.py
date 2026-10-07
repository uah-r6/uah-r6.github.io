"""Current live v3 seal; do not rebase any historical research checkpoint."""
import json
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deploy_native_v3 import DATA, check_public, state
from r6stats.publishing import validate_public_data
from r6stats.rating_inputs_v3 import load_inputs
from r6stats.replay_archive import verify
from v3_final_reserve import ROOT, sha, source_sha


def main():
    seal=json.loads((ROOT/'research/native-v3-production-checkpoint.json').read_text(encoding='utf-8'))
    before=json.loads((DATA/'before.json').read_text(encoding='utf-8'))
    for path, value in seal['sources'].items():
        if source_sha(ROOT/path)!=value:raise ValueError(f'Production source differs: {path}')
    for path, value in seal['private_artifacts'].items():
        if sha(ROOT/path)!=value:raise ValueError('Preserved private artifact differs.')
    for path, value in before['archive_hashes'].items():
        if sha(ROOT/path)!=value:raise ValueError('Protected archive differs.')
    config=json.loads((ROOT/'config/settings.json').read_text(encoding='utf-8'))
    if config['stats']['rating_version']!='siege_style_v3':raise ValueError('V3 not active.')
    with sqlite3.connect((ROOT/'data/r6stats.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        if state(db)!=before['tables']:raise ValueError('Historical tables or v2 snapshots changed.')
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Database integrity failure.')
        actual={r[0]:load_inputs(db,r[0])[0] is not None for r in db.execute('SELECT id FROM maps')}
        if actual!=seal['v3_map_eligibility']:raise ValueError('V3 coverage changed.')
        for mid in actual:
            if verify(db,ROOT/'data/replay-archive',mid)['status']!='Healthy':raise ValueError('Archive not healthy.')
    check_public(DATA/'before-public',ROOT/'web/public/data')
    for path, value in seal['public_hashes'].items():
        if source_sha(ROOT/path)!=value:raise ValueError('Generated public JSON differs.')
    print('Validated native v3, original historical statistics/v2 snapshots, all archives, immutable final and',validate_public_data(ROOT),'private-safe public JSON documents verified.')


if __name__=='__main__':main()
