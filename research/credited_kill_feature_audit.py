"""Consumed SAL independent deaths/opening/multikill controls, no new Rating fit."""
from collections import Counter
from html import unescape
import json
import re

from uah_guarded_actor_readonly import snapshot
from v3_final_reserve import ROOT, sha


def public_multikills(game):
    events=[]
    for number,round_ in enumerate(game['rounds'],1):
        for e in round_['events']:
            if e['type']!='multikill': continue
            match=re.search(r'</a>\s*([^<]+?) gets a ([2-5])k\s*$',e['html'])
            if not match: raise ValueError('Unsupported public multikill event format')
            events.append(dict(round=number,name=unescape(match[1]).strip(),kills=int(match[2])))
    return events


def main():
    protected=snapshot(); rows=[]; event_checks=[]; first_finish_controls=[];counts=Counter()
    DATA=ROOT/'data/research/v3-corrected-final-sal-stage2'
    official_audit=json.loads((DATA/'independent-kd-audit.json').read_text(encoding='utf-8'))['rows']
    for path in sorted((ROOT/'data/research/diagnostics/v3-sal-kill-credit').glob('*.json')):
        if not path.stem.isdigit():continue
        old=json.loads(path.read_text(encoding='utf-8'));mid=old['official_match_id']
        pred=json.loads((DATA/str(mid)/'replay-predictions.json').read_text(encoding='utf-8'))
        api=json.loads((DATA/str(mid)/'siegegg-api-sealed.json').read_text(encoding='utf-8'))
        public=json.loads((DATA/str(mid)/'siegegg-player-stats-sealed.json').read_text(encoding='utf-8'))
        html=ROOT/f'data/research/diagnostics/v3-sal-official-kd/{mid}.html'
        primary=json.loads(re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',html.read_text(encoding='utf-8'),re.S)[1])['props']['pageProps']['pageData']['match']
        people=[dict(p,team_id=t['id']) for t in primary['games'][0]['teams'] for p in t['players']]
        if primary['id']!=mid or len(primary['games'])!=1 or len(people)!=10: raise ValueError('Primary map/roster mismatch')
        game=api['games'][0]; public_events=public_multikills(game)
        if len(game['rounds'])!=len(old['rounds']): raise ValueError('Public round inventory differs')
        bindings={}; public_bindings={}
        for p in pred['players']:
            audited=next(r for r in official_audit if r['official_match_id']==mid and r['player']==p['player'])
            candidates=audited['primary_identity_candidates']
            if len(candidates)!=1:raise ValueError('No exact previously verified primary binding')
            primary_player=[q for q in people if q['name']==candidates[0]['name'] and q['team_id']==candidates[0]['team_id']]
            if len(primary_player)!=1:raise ValueError('Cached official identity differs')
            bindings[p['player']]=primary_player[0]
            target=[(k,v) for k,v in public[str(game['id'])].items() if int(k) in {q['id'] for q in api['players'] if q['ign'].casefold() in audited['identity_spellings_considered'] or q['stylized_name'].casefold() in audited['identity_spellings_considered']}]
            if len(target)!=1:
                # Reuse the independent public player ID in frozen quality,
                # not an outcome or a guessed spelling.
                quality_paths=sorted((DATA/str(mid)).glob('quality-decisions-*.json'))
                quality=json.loads(quality_paths[-1].read_text(encoding='utf-8'))
                decision=next(d for d in quality['decisions'] if d['player']==p['player'])
                pid=str(decision['player_id']); target=[(pid,public[str(game['id'])][pid])]
            public_bindings[p['player']]=next(q for q in api['players'] if q['id']==int(target[0][0]))
            stats=primary_player[0]['stats']; credits=[r['players'][p['player']]['delta'] for r in old['rounds']]
            finishes=[r['kills'] for r in p['rounds']]
            credited_buckets={size:credits.count(size) for size in (2,3,4,5)}
            official_buckets=dict(zip((2,3,4,5),(stats[k] for k in ('doubleKills','tripleKills','quadKills','aces'))))
            public_ok=list(map(int,re.match(r'(\d+)-(\d+)',target[0][1]['ok']).groups()))
            row=dict(official_match_id=mid,player=p['player'],deaths=p['derived']['deaths'],official_deaths=stats['deaths']['count'],
                finisher_opening=[p['derived']['opening_kills'],p['derived']['opening_deaths']],
                official_opening=[stats['openingKills']['count'],stats['openingDeaths']['count']],public_opening=public_ok,
                credited_multikill_sizes=credited_buckets,official_multikill_sizes=official_buckets,
                finisher_multikill_sizes={size:finishes.count(size) for size in (2,3,4,5)},
                official_source_sha256=sha(html))
            rows.append(row);counts['player_maps']+=1
            counts['deaths_match']+=row['deaths']==row['official_deaths']
            counts['opening_official_match']+=row['finisher_opening']==row['official_opening']
            counts['opening_public_match']+=row['finisher_opening']==public_ok
            counts['credited_multikill_official_match']+=credited_buckets==official_buckets
            counts['finisher_multikill_official_match']+=row['finisher_multikill_sizes']==official_buckets
        for number,r in enumerate(old['rounds'],1):
            opening=next((p for p in pred['players'] if p['rounds'][number-1]['opening_kills']),None)
            if opening and r['players'][opening['player']]['delta']==0:
                first_finish_controls.append(dict(official_match_id=mid,round=number,
                    first_finisher=opening['player'],round_credit=0,
                    interpretation='First elimination finisher has no credited kills this round; round-specific official opening owner unavailable.'))
            expected={p['player']:r['players'][p['player']]['delta'] for p in pred['players'] if r['players'][p['player']]['delta']>=2}
            observed={}
            for e in [e for e in public_events if e['round']==number]:
                matched=[name for name,p in public_bindings.items() if e['name'].casefold() in (p['ign'].casefold(),p['stylized_name'].casefold())]
                if len(matched)!=1 or matched[0] in observed:raise ValueError('Public multikill identity ambiguous')
                observed[matched[0]]=e['kills']
            event_checks.append(dict(official_match_id=mid,round=number,credited=expected,public=observed,match=expected==observed))
    counts['rounds']=len(event_checks);counts['public_multikill_rounds_match']=sum(r['match'] for r in event_checks)
    result=dict(counts=dict(counts),player_maps=rows,round_multikills=event_checks,
                first_finisher_zero_credit=first_finish_controls,protected_hashes=protected,
                scope='Consumed independent feature evidence, not new Rating evaluation or input replacement.')
    out=ROOT/'data/research/credited-kills-v1/feature-audit.json';out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=['# Credited-kill downstream feature evidence — consumed SAL','',str(dict(counts)), '',
        'Official player identities reuse the independently verified primary name/team bindings from the prior K/D audit. '
        'Public multikill names bind only to the exact cached SiegeGG player ID/ign/stylized name. No counter value chooses identity. '
        'Deaths come from the original victim-elimination statistics; DBNO is not an extra death.','',
        '| Official map / player | Deaths / official | Finisher opening K-D | Official opening | Public opening | Credited 2/3/4/5K | Official 2/3/4/5K |',
        '| --- | --- | --- | --- | --- | --- | --- |']
    for r in rows:
        if r['finisher_opening']!=r['official_opening'] or r['credited_multikill_sizes']!=r['finisher_multikill_sizes'] or r['deaths']!=r['official_deaths']:
            lines.append(f"| {r['official_match_id']}/{r['player']} | {r['deaths']}/{r['official_deaths']} | {r['finisher_opening']} | {r['official_opening']} | {r['public_opening']} | {list(r['credited_multikill_sizes'].values())} | {list(r['official_multikill_sizes'].values())} |")
    lines+=['','## First finisher without round credit','',str(first_finish_controls),'',
        'Map-level opening agreement cannot identify which DBNO-causing player should own an individual opening. '
        'Cached public round events contain plants, disables, multikills and clutches, not a full kill-by-kill/opening ledger. '
        'Do not resolve victims or DBNO timing from these aggregates. Opening/trade/pivot/untraded production definitions remain unchanged.', '',
        'Multikill count buckets may be migrated only through the separate validated credited-round path; frozen v2 '
        'must retain original finisher-derived multikill/KOST/KPR inputs. No formula fit, final regrading or historical write.', '']
    (ROOT/'research/output/credited-kill-feature-audit.md').write_text('\n'.join(lines),encoding='utf-8')
    if snapshot()!=protected:raise ValueError('Protected state changed')
    print(dict(counts));print('first finisher zero credit',first_finish_controls)


if __name__=='__main__':main()
