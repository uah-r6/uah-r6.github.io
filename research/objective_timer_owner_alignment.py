"""Compare already-consumed public labels with packet-owner observations.

Never creates actors or edits labels/results. This is development alignment,
not new validation accuracy. Public label disagreements are retained verbatim.
"""
from collections import Counter
import json

from objective_score_delta_validation import grade
from objective_transition_probe import ROOT


def main():
    base = ROOT/'data/research/diagnostics'
    observed = json.loads((base/'player-component-fields/declared-timer-all-consumed.json').read_text(encoding='utf-8'))
    sources = {s['siegegg_match_id']:s for s in json.loads((ROOT/'research/sources.json').read_text(encoding='utf-8'))['matches'] if s.get('siegegg_match_id')}
    development = json.loads((base/'objective-encoding-validation/summary.json').read_text(encoding='utf-8'))['rounds']
    labels = json.loads((base/'objective-score-delta-validation/summary.json').read_text(encoding='utf-8'))['events']
    records, index = [], 0
    for cohort in ('development','extension'):
        rows = json.loads((base/f'objective-score-structure-{cohort}.json').read_text(encoding='utf-8'))
        for row in rows:
            owner = observed[index]
            index += 1
            keys = ('match_id','game_id','round','kind','build')
            if any(row[k] != owner[k] for k in keys):
                raise ValueError('Observed ownership ledger order/key mismatch')
            if cohort == 'development':
                target_row = next(r for r in development if (r['match_id'],r['round']) == (row['match_id'],row['round']))
                event = next(e for e in target_row['public_objectives'] if e['type'] == row['kind'])
                label = event.get('description',event.get('html',''))
            elif row['match_id'] == 4139:
                label = 'Raid plants defuser'
            else:
                reference = next(r for r in labels if all(r[k] == row[k] for k in ('match_id','game_id','round','kind')))
                label = reference['public_actor']+(' plants ' if row['kind']=='plant' else ' disables ')+'defuser'
            public = json.loads((ROOT/f"data/research/targets/siegegg-match-{row['match_id']}-api.json").read_text(encoding='utf-8'))
            value = owner['packet_owners'][0] if owner['status'] == 'complete_unique_declared_timer_owner' else None
            comparison = grade(value,label,sources[row['match_id']],public)
            alignment = {'correct':'agrees_with_consumed_public_label', 'incorrect':'disagrees_with_consumed_public_label',
                         'unresolved':'ambiguous_packet_owner', 'identity_review':'alias_identity_review'}[comparison]
            records.append({k:row[k] for k in keys} | dict(cohort=cohort,packet_owners=owner['packet_owners'],
                            alignment=alignment,public_label=label,actor=None,actor_reason='research_only_no_attribution'))
    if index != len(observed):
        raise ValueError('Ownership records left unmatched')
    counts = {cohort:{kind:dict(Counter(r['alignment'] for r in records if r['cohort']==cohort and r['kind']==kind))
                      for kind in ('plant','disable')} for cohort in ('development','extension')}
    (base/'player-component-fields/owner-public-label-alignment.json').write_text(json.dumps(dict(counts=counts,records=records),indent=2),encoding='utf-8')
    lines = ['# Consumed public labels versus direct timer owners', '',
             '**This is not actor accuracy or independent validation.** All labels were previously consumed. '
             'Owner observations remain separate from actors; every actor is null. No target or immutable result changed. '
             'Original development and extension overlap at the mandatory 4139/R07 control, deliberately retained in both.', '',
             f'Alignment counts: `{counts}`.', '',
             '| Cohort / match / game / round / kind | Packet owner | Original public label | Alignment |',
             '| --- | --- | --- | --- |']
    for r in records:
        if r['alignment'] != 'agrees_with_consumed_public_label':
            lines.append(f"| {r['cohort']}/{r['match_id']}/{r['game_id']}/R{r['round']:02d}/{r['kind']} | {r['packet_owners']} | {r['public_label']} | {r['alignment']} |")
    lines += ['', '4139/R07 remains actor-unresolved under the explicit user safeguard despite separate official VOD evidence '
              'showing Aiden planting. Bank3563/game6675/R02 remains actor-unresolved: public J9O and observed njr disagree; '
              'the video cuts away before the disable, so neither independent actor confirmation nor a target revision is justified. '
              'The mixed4150/R11 run requires component/state segmentation, not a label-guided threshold. '
              'Other discrepancies require their own packet/video review; agreeing labels do not establish general state semantics.', '']
    (ROOT/'research/output/objective-timer-owner-alignment.md').write_text('\n'.join(lines),encoding='utf-8')
    print(counts)


if __name__ == '__main__':
    main()
