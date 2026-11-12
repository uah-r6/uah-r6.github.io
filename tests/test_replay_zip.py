from pathlib import Path
import zipfile

import pytest

from r6stats.replay_zip import replay_folder


def test_persistent_zip_snapshot_caches_and_recovers_changed_private_copy(tmp_path):
    archive=tmp_path/'download.zip'
    with zipfile.ZipFile(archive,'w') as z:
        z.writestr('parent/Match/Match-R01.rec',b'round one')
        z.writestr('parent/Match/Match-R02.rec',b'round two')
    before=archive.read_bytes()
    folder=replay_folder(archive,tmp_path/'cache')
    assert folder.is_dir() and (folder/'Match-R01.rec').read_bytes()==b'round one'
    assert replay_folder(archive,tmp_path/'cache')==folder
    (folder/'Match-R01.rec').write_bytes(b'changed')
    repaired=replay_folder(archive,tmp_path/'cache')
    assert repaired!=folder and (repaired/'Match-R01.rec').read_bytes()==b'round one'
    assert archive.read_bytes()==before
    assert replay_folder(repaired,tmp_path/'cache')==repaired


@pytest.mark.parametrize('names',[
    ['../escape.rec'],['C:/escape.rec'],['a/1.rec','b/2.rec'],[],
    ['a/R01.rec','a/r01.rec'],['a/../R01.rec','R01.rec'],
])
def test_invalid_or_ambiguous_zip_cannot_be_a_rehost_segment(tmp_path,names):
    archive=tmp_path/'bad.zip'
    with zipfile.ZipFile(archive,'w') as z:
        for name in names:z.writestr(name,b'replay')
    with pytest.raises(ValueError):replay_folder(archive,tmp_path/'cache')


def test_bad_zip_has_clear_error(tmp_path):
    archive=tmp_path/'incomplete.zip';archive.write_bytes(b'not a zip')
    with pytest.raises(ValueError,match='invalid or incomplete'):
        replay_folder(archive,tmp_path/'cache')


def test_admin_rehost_preview_accepts_two_zip_paths_and_retains_snapshots(tmp_path,monkeypatch):
    import json
    from fastapi.testclient import TestClient
    from r6stats.admin.server import create_app
    from r6stats.db import repository as repo
    from test_teams import seed,settings,replay
    (tmp_path/'config').mkdir()
    (tmp_path/'config/settings.json').write_text(json.dumps(settings()),encoding='utf-8')
    db=repo.connect(tmp_path/'data/r6stats.sqlite');seed(db);db.close()
    paths=[]
    for name in ('first','second'):
        archive=tmp_path/f'{name}.zip'
        with zipfile.ZipFile(archive,'w') as z:
            z.writestr('Match/Match-R01.rec',name)
            z.writestr('Match/Match-R02.rec',name+' round two')
        paths.append(str(archive))
    monkeypatch.setattr('r6stats.parser.confirmed_rehost.parse_match',
                        lambda path,**kwargs:replay((path/'Match-R01.rec').read_text()))
    app=create_app(tmp_path)
    with TestClient(app) as client:
        headers={'X-R6-Admin-Token':client.get('/api/admin/session').json()['token']}
        result=client.post('/api/admin/replays/rehost/preview',headers=headers,
            json={'team_id':1,'season_slug':'fall-2026','segments':[{'path':p} for p in paths]})
        assert result.status_code==200,result.text
        assert result.json()['rounds']==4 and result.json()['score']==[4,0]
        preview=app.state.previews[result.json()['preview_token']]
        assert all(p.is_dir() and p.is_relative_to(tmp_path/'data/private') for p in preview.paths)
    db=repo.connect(tmp_path/'data/r6stats.sqlite')
    assert db.execute('SELECT count(*) FROM maps').fetchone()[0]==0
    db.close()
