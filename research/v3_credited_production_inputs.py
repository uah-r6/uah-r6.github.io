"""Read-only supported v3 input inventory; cached Go evidence, no reparse."""
from copy import deepcopy
import hashlib
import json
import sqlite3

from credited_late_history_development import immutable_write
from r6stats.credited_refresh import load
from r6stats.parser.models import Match
from r6stats.parser.siege_dissect import normalize,physical_round_numbers
from r6stats.replay_archive import verify
from v3_final_reserve import ROOT,sha

DATA=ROOT/'data/research/v3-credited-production-inputs-v1'


def main():
    db_path=ROOT/'data/r6stats.sqlite';before=sha(db_path)
    old=json.loads((ROOT/'data/research/objective-migration/preview.json').read_text(encoding='utf-8'))
    cached_ids={m['id'] for m in old['maps']};exe=ROOT/'data/research/objective-migration/approved-core.exe'
    if sha(exe)!=old['binary_sha256']:raise ValueError('Approved objective observer binary changed')
    db=sqlite3.connect(db_path.resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    results=[]
    for saved in db.execute('SELECT * FROM maps ORDER BY rowid'):
        match=Match.from_dict(json.loads(saved['normalized_json']));evidence=deepcopy(match);issues=[];sources={}
        archive=verify(db,ROOT/'data/replay-archive',saved['id'])
        if archive['status']!='Healthy':raise ValueError('Archive not healthy')
        if load(db,saved['id']) is None:issues.append('Whole map lacks complete credited-counter evidence')
        if saved['id'] in cached_ids:
            folder=ROOT/'data/replay-archive/fall-2026'/saved['id'];manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
            segments=[(1,folder)] if manifest['archive_format_version']==1 else [(s['segment'],folder/f"segment-{s['segment']:02d}") for s in manifest['segments']]
            for segment,path in segments:
                files=sorted(path.glob('*.rec'));key=hashlib.sha256((sha(exe)+''.join(sha(p) for p in files)).encode()).hexdigest()
                cache=ROOT/'data/research/objective-migration'/(key+'.json')
                if not cache.exists():raise ValueError('Original approved objective cache missing; no automatic reparse')
                sources[cache.relative_to(ROOT).as_posix()]=sha(cache)
                parsed=normalize(json.loads(cache.read_text(encoding='utf-8')),round_numbers=physical_round_numbers(files))
                for r in parsed.rounds:
                    logical=r.number if manifest['archive_format_version']==1 else next(item['logical_number'] for item in manifest['source_manifest']['mapping'] if item['segment']==segment and item['physical_number']==r.number)
                    if logical is None:continue
                    target=next(t for t in evidence.rounds if t.number==logical)
                    # Graft only evidence inventory, not player stats or events.
                    target.objective_occurrences=deepcopy(r.objective_occurrences)
                    for occurrence in target.objective_occurrences:
                        if not occurrence.actor or occurrence.actor_source!=occurrence.actor_reason or occurrence.actor_source!='completing_timer_owner_v1':
                            issues.append(f'Round{logical} {occurrence.kind} objective actor unresolved')
                        else:
                            expected=[o.player for o in target.objectives if o.kind==occurrence.kind]
                            if expected!=[occurrence.actor]:issues.append(f'Round{logical} stored objective differs from approved core actor')
        for r in evidence.rounds:
            verified={(o.kind,o.actor) for o in r.objective_occurrences if o.actor and o.actor_source==o.actor_reason=='completing_timer_owner_v1'}
            if {(o.kind,o.player) for o in r.objectives}!=verified:issues.append(f'Round{r.number} objective credits lack complete core evidence')
            if any(not o.actor or o.actor_source!=o.actor_reason or o.actor_source!='completing_timer_owner_v1' for o in r.objective_occurrences):issues.append(f'Round{r.number} unsupported objective occurrence')
        record=dict(map_id=saved['id'],map=match.map_name,rounds=len(match.rounds),fingerprint=saved['fingerprint'],
            original_normalized_sha256=hashlib.sha256(saved['normalized_json'].encode()).hexdigest(),
            eligible=not issues,issues=sorted(set(issues)),evidence_normalized=evidence.to_dict(),sources=sources,
            parser_source='approved cached Go objective observer for historical maps; verified current normalized import for new maps')
        immutable_write(DATA/'maps'/(saved['id']+'.json'),record);results.append(record)
    if sha(db_path)!=before:raise ValueError('Read-only inventory modified database')
    summary=dict(database_sha256=before,maps=[{k:v for k,v in r.items() if k!='evidence_normalized'} for r in results],
        eligible_maps=sum(r['eligible'] for r in results),eligible_rounds=sum(r['rounds'] for r in results if r['eligible']),
        production_changed=False,no_replay_reparse=True)
    immutable_write(DATA/'summary.json',summary)
    print('SUPPORTED V3 INPUT INVENTORY',summary,flush=True)


if __name__=='__main__':main()
