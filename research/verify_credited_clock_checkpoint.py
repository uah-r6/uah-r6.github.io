"""Verify later clock-scope/UAH sensitivity evidence and both prior seals."""
import json

from verify_credited_kill_continuation import main as verify_prior
from v3_final_reserve import ROOT, sha, source_sha


def main():
    record = json.loads((ROOT / 'research/credited-clock-checkpoint.json').read_text(encoding='utf-8'))
    for name, digest in record['source_hashes'].items():
        if source_sha(ROOT / name) != digest:
            raise ValueError('Clock checkpoint source changed: ' + name)
    for category in ('result_hashes', 'input_hashes'):
        for name, digest in record[category].items():
            if sha(ROOT / name) != digest:
                raise ValueError('Clock checkpoint input/result changed: ' + name)
    verify_prior()
    print('Clock epoch and UAH sensitivity checkpoint verified; no derived Ratings or live changes')


if __name__ == '__main__':
    main()
