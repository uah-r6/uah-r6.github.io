"""Adapt frozen validation plumbing to the unused SI manifest; actor unchanged."""
import json

from objective_combined_reserve import digest
from objective_transition_probe import ROOT


def main():
    original = json.loads((ROOT/'research/objective-combined-freeze.json').read_text())
    for name,expected in original['sha256'].items():
        if digest(ROOT/name)!=expected:
            raise ValueError('Original frozen dependency changed: '+name)
    src = (ROOT/'research/objective_combined_reserve.py').read_text()
    src = src.replace('objective-combined-reserve','objective-si-final-validation')
    src = src.replace('objective-combined-freeze.json','objective-si-final-freeze.json')
    src = src.replace('objective-actor-reserve.json','objective-si-final-reserve.json')
    src = src.replace('sealed five-map reserve','sealed four-map SI final reserve')
    src = src.replace('ALL replay predictions','ALL replay predictions')
    src = src.replace("    records,occurrence_errors = [],[]", "    sources[3173] = dict(players=reserve['player_aliases'])\n    records,occurrence_errors = [],[]")
    src = src.replace("                    physical = int(rec.stem.rsplit('-R',1)[1])",
                      "                    expected_hash = next(f['sha256'] for f in mapping['exact_replay_sha256'] if f['folder']==segment['folder'] and f['filename']==filename)\n"
                      "                    if digest(rec)!=expected_hash:\n"
                      "                        raise ValueError('Reserved physical replay changed')\n"
                      "                    physical = int(rec.stem.rsplit('-R',1)[1])")
    src = src.replace('Five maps,60 rounds.','Four maps,58 rounds.')
    src = src.replace('Eight plants/two disables is a small actor validation sample. Zero wrong credits on this ',
                      'This is a separate unused actor series, within the previously studied SI event. Zero wrong credits on this ')
    adapter = ROOT/'research/objective_si_final_validation.py'
    freeze = ROOT/'research/objective-si-final-freeze.json'
    if adapter.exists() or freeze.exists():
        raise ValueError('Do not overwrite an existing frozen SI adapter')
    adapter.write_text(src,encoding='utf-8')
    manifest = dict(original_candidate_freeze_commit='cd28f76c7f22b6dc76af0a8afdbebb984e5232a1',
                    status='frozen_unchanged_actor_candidate_new_series',
                    changes='Validation cache/manifest/report paths, alias metadata and exact physical replay digest verification only. Actor logic unchanged.',
                    actor_labels_opened=False,sha256=original['sha256'] | {
                        'research/objective_si_final_validation.py':digest(adapter),
                        'research/objective-si-final-reserve.json':digest(ROOT/'research/objective-si-final-reserve.json')})
    freeze.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(adapter,freeze)


if __name__=='__main__':
    main()
