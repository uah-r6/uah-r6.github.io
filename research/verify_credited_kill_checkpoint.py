"""Verify the saved development checkpoint without derivation or live writes."""
import hashlib
import json

from objective_oce_consumed_support_verify import main as verify_prior
from uah_guarded_actor_readonly import snapshot
from v3_final_reserve import ROOT, sha, source_sha


def main():
    checkpoint=json.loads((ROOT/'research/credited-kill-checkpoint.json').read_text(encoding='utf-8'))
    for name,digest in checkpoint['source_hashes'].items():
        if source_sha(ROOT/name)!=digest:raise ValueError('Credited checkpoint source changed: '+name)
    for name,digest in checkpoint['result_hashes'].items():
        if sha(ROOT/name)!=digest:raise ValueError('Credited checkpoint result changed: '+name)
    for name,digest in checkpoint['binary_hashes'].items():
        if sha(ROOT/name)!=digest:raise ValueError('Credited checkpoint binary changed: '+name)
    protected=snapshot()
    digest=hashlib.sha256(json.dumps(protected,sort_keys=True).encode()).hexdigest()
    if digest!=checkpoint['protected_inventory_sha256'] or len(protected)!=checkpoint['protected_files']:
        raise ValueError('Protected live inventory changed')
    verify_prior()
    print('Credited development source/binary/result checkpoint verified; no derivation, model fit or live writes')


if __name__=='__main__':main()
