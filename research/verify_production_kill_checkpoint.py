"""Verify the new authorized seven-map baseline, without rebasing old seals."""
import json
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from apply_current_kill_migration import state_matches
from current_kill_migration import DATA
from r6stats.credited_refresh import load
from r6stats.publishing import validate_public_data
from v3_final_reserve import ROOT,sha,source_sha


def main():
    seal=json.loads((ROOT/'research/production-kill-checkpoint.json').read_text(encoding='utf-8'))
    for path,digest in seal['private_artifacts'].items():
        if sha(ROOT/path)!=digest:raise ValueError(f'Private audit artifact differs: {path}')
    for path,digest in seal['sources'].items():
        if source_sha(ROOT/path)!=digest:raise ValueError(f'Production source differs: {path}')
    before=json.loads((DATA/'before.json').read_text(encoding='utf-8'))
    with sqlite3.connect((ROOT/'data/r6stats.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        state_matches(db,before)
        actual={r[0]:bool(load(db,r[0])) for r in db.execute('SELECT id FROM maps')}
        if actual!=seal['map_credit_complete']:raise ValueError('Whole-map credit eligibility differs')
    for path,digest in before['archive_hashes'].items():
        if sha(ROOT/path)!=digest:raise ValueError('Protected archive differs')
    for path,digest in seal['public_hashes'].items():
        if sha(ROOT/path)!=digest:raise ValueError('Generated public file differs')
    for path,digest in seal['immutable_research'].items():
        if sha(ROOT/path)!=digest:raise ValueError('Frozen historical study differs')
    print('Current seven-map credited overlay, original tables/objectives/operators/v2 snapshots, archives, public files and historical studies verified.',validate_public_data(ROOT),'public documents',flush=True)


if __name__=='__main__':main()
