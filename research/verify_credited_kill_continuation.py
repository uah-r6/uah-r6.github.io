"""Verify additive HUD/native-envelope/trade evidence without derivation."""
import json

from verify_credited_kill_checkpoint import main as verify_prior
from v3_final_reserve import ROOT, sha, source_sha


def main():
    checkpoint = json.loads((ROOT / 'research/credited-kill-continuation-checkpoint.json').read_text(encoding='utf-8'))
    for name, digest in checkpoint['source_hashes'].items():
        if source_sha(ROOT / name) != digest:
            raise ValueError('Credited continuation source changed: ' + name)
    for category in ('result_hashes', 'evidence_hashes', 'binary_hashes'):
        for name, digest in checkpoint[category].items():
            if sha(ROOT / name) != digest:
                raise ValueError('Credited continuation artifact changed: ' + name)
    verify_prior()
    print('Separate HUD/native-envelope/trade checkpoint verified; all prior studies/live hashes preserved')


if __name__ == '__main__':
    main()
