from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
import v3_corrected_final_pipeline as sal
import v3_final_pipeline as apac


def test_distinct_final_storage_cannot_overwrite_original_failed_event():
    assert sal.DATA!=apac.DATA
    assert sal.RESULT!=apac.RESULT
    assert sal.FREEZE!=apac.FREEZE
    assert sal.RESERVE!=apac.RESERVE


def test_separate_final_refuses_repeated_target_open_after_interruption(tmp_path,monkeypatch):
    monkeypatch.setattr(sal,'DATA',tmp_path)
    monkeypatch.setattr(sal,'RESULT',tmp_path/'one-shot-result.json')
    (tmp_path/'rating-targets-opened.json').write_text('{}')
    with pytest.raises(ValueError,match='already opened'):
        sal.evaluate({},dict(matches=[]))
