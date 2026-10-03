"""The additive collector cannot hide actor errors as map quality exclusions."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
import objective_bonus_body_fresh_collection as collection


def fail(message):
    def acquire(*args):raise ValueError(message)
    return acquire


def test_discontinuous_whole_map_is_preserved_without_inventing_predictions(tmp_path,monkeypatch):
    monkeypatch.setattr(collection,'DATA',tmp_path)
    monkeypatch.setattr(collection,'acquire',fail('Incomplete/discontinuous completed score path'))
    monkeypatch.setattr(collection,'source_sha',lambda path:'fixed-source')
    result=collection.acquire_with_quality_record({'official_match_id':123},{})
    saved=json.loads(result['path'].read_text())
    assert result['status']=='whole_map_quality_failure'
    assert not saved['actor_proposals_created'] and not saved['labels_read']
    assert not (tmp_path/'123/replay-predictions.json').exists()
    assert collection.acquire_with_quality_record({'official_match_id':123},{})==result


@pytest.mark.parametrize('message',['Already-resolved actor changed','Actor false positive without verified plant',
                                    'Existing feedback observer differs','Unexpected implementation bug'])
def test_actor_control_or_implementation_failure_never_becomes_a_quality_exclusion(tmp_path,monkeypatch,message):
    monkeypatch.setattr(collection,'DATA',tmp_path);monkeypatch.setattr(collection,'acquire',fail(message))
    with pytest.raises(ValueError,match=message):collection.acquire_with_quality_record({'official_match_id':123},{})
    assert not (tmp_path/'123/whole-map-quality-failure.json').exists()
