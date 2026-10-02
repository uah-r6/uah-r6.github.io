"""Freeze validation plumbing for six cached actor maps; candidate A unchanged."""
import json

from objective_combined_reserve import digest
from objective_transition_probe import ROOT


def main():
    original = json.loads((ROOT/'research/objective-combined-freeze.json').read_text())
    for name,expected in original['sha256'].items():
        if digest(ROOT/name)!=expected:
            raise ValueError('Original frozen dependency changed: '+name)
    src = (ROOT/'research/objective_combined_reserve.py').read_text()
    src = src.replace('objective-combined-reserve','objective-cached-map-validation')
    src = src.replace('objective-combined-freeze.json','objective-cached-map-freeze.json')
    src = src.replace('objective-actor-reserve.json','objective-cached-map-reserve.json')
    src = src.replace('sealed five-map reserve','sealed six-map cached actor reserve')
    src = src.replace('    records,occurrence_errors = [],[]',
                      "    for mid,aliases in reserve['player_aliases_by_match'].items():\n"
                      "        sources[int(mid)] = dict(players=aliases)\n"
                      '    records,occurrence_errors = [],[]')
    src = src.replace("                    physical = int(rec.stem.rsplit('-R',1)[1])",
                      "                    expected_hash = next(f['sha256'] for f in mapping['exact_replay_sha256'] if f['folder']==segment['folder'] and f['filename']==filename)\n"
                      "                    if digest(rec)!=expected_hash:\n"
                      "                        raise ValueError('Reserved physical replay changed')\n"
                      "                    physical = int(rec.stem.rsplit('-R',1)[1])")
    src = src.replace('Five maps,60 rounds.','Six maps,61 rounds.')
    src = src.replace('Eight plants/two disables is a small actor validation sample. Zero wrong credits on this ',
                      'This is fresh actor evidence in six cached maps within studied SLC/EWC events. Prior K/D, multikill or occurrence metadata may have been examined; it is not new event-disjoint Rating data. Zero wrong credits on this ')
    adapter = ROOT/'research/objective_cached_map_validation.py'
    freeze = ROOT/'research/objective-cached-map-freeze.json'
    if adapter.exists() or freeze.exists():
        raise ValueError('Do not overwrite a frozen cached-map adapter')
    adapter.write_text(src,encoding='utf-8')
    manifest = dict(original_candidate_freeze_commit='cd28f76c7f22b6dc76af0a8afdbebb984e5232a1',
                    status='frozen_unchanged_actor_candidate_cached_map_extension',
                    independent_sole_wrapper_used=False,actor_labels_opened=False,
                    sha256=original['sha256'] | {
                        'research/objective_cached_map_validation.py':digest(adapter),
                        'research/objective-cached-map-reserve.json':digest(ROOT/'research/objective-cached-map-reserve.json')})
    freeze.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(adapter,freeze)


if __name__=='__main__':
    main()
