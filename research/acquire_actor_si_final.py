"""Cache one unused official replay series; do not read actor target labels."""
import html
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse,unquote
import urllib.request
import zipfile

from objective_transition_probe import ROOT


def main():
    page = 'https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/7740'
    cache = ROOT/'data/research/diagnostics/si-final-acquisition'
    cache.mkdir(parents=True,exist_ok=True)
    path = cache/'official-page.html'
    if not path.exists():
        request = urllib.request.Request(page,headers={'User-Agent':'Mozilla/5.0'})
        path.write_bytes(urllib.request.urlopen(request,timeout=45).read())
    contents = path.read_text(encoding='utf-8').replace('\\u0026','&').replace('\\/','/')
    links = sorted({html.unescape(url) for url in re.findall(r'https[^\s"<>\\]+\.zip',contents)})
    print('official archive links',links,flush=True)
    if len(links)!=1:
        raise ValueError('Expected one official series archive; inspect cached page structure')
    url = links[0]
    archive = ROOT/'data/research/pro-replays'/unquote(Path(urlparse(url).path).name)
    if not archive.exists():
        partial = archive.with_suffix('.zip.partial')
        subprocess.run(['curl.exe','--fail','--location','--retry','3','--continue-at','-',
                        '--output',str(partial),url],check=True)
        partial.replace(archive)
    extraction = ROOT/'data/research/extracted/actor-si-final-2026-02-15'
    extraction.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        # Every output is checked within the research extraction root.
        for member in bundle.infolist():
            target = (extraction/member.filename).resolve()
            if not target.is_relative_to(extraction.resolve()):
                raise ValueError('ZIP member escapes research extraction directory')
            if member.is_dir():
                target.mkdir(parents=True,exist_ok=True)
            elif not target.exists() or target.stat().st_size!=member.file_size:
                target.parent.mkdir(parents=True,exist_ok=True)
                with bundle.open(member) as source,target.open('wb') as destination:
                    import shutil
                    shutil.copyfileobj(source,destination)
        bad = bundle.testzip()
        if bad:
            raise ValueError('Archive CRC failure: '+bad)
    folders = sorted({str(p.parent.relative_to(extraction)) for p in extraction.rglob('*.rec')})
    provenance = dict(status='replays_acquired_actor_labels_sealed',official_page=page,archive_url=url,
                      siegegg_match_id=3173,event='Six Invitational 2026',archive_bytes=archive.stat().st_size,
                      extraction_folders=folders,rule='No public round actor target read during acquisition')
    (cache/'provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    print('cached/extracted',archive.name,archive.stat().st_size,'folders',folders,flush=True)


if __name__=='__main__':
    main()
