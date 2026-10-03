"""Fixed cohort selection and isolated collection context safeguards."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
import objective_bonus_body_oce_cohort as study


def event(ids):
    return dict(competition=dict(id=507),phaseDetails=dict(steps=[dict(matches=[
        dict(id=i,date=f'2026-06-{i:02d}',replayLink=f'https://example.com/{i}.zip',
             teams=[dict(id=1),dict(id=2)],games=[dict(teams=[dict(score=7),dict(score=3)])]) for i in ids])]))


def test_all_linked_sources_selected_deterministically_without_outcomes():
    sources=study.select_events([event([3,1,2])],set())
    assert [s['official_match_id'] for s in sources]==[1,2,3]
    assert all('actor' not in s for s in sources)


def test_consumed_match_cannot_be_reserved_again():
    with pytest.raises(ValueError,match='Consumed'):study.select_events([event([1,2])],{1})


def test_event_ceiling_is_not_outcome_adaptive():
    with pytest.raises(ValueError,match='event ceiling'):study.select_events([event([1]),event([2]),event([3])],set())


def test_duplicate_metadata_not_an_extra_map():
    with pytest.raises(ValueError,match='unique'):study.select_events([event([1]),event([1])],set())


def test_collection_context_restores_globals_even_on_error(tmp_path):
    before=(study.collector.DATA,study.collector.FREEZE)
    with pytest.raises(RuntimeError):
        with study.collection_context(tmp_path,tmp_path/'freeze.json'):
            assert study.collector.DATA==tmp_path
            raise RuntimeError('diagnostic')
    assert (study.collector.DATA,study.collector.FREEZE)==before


def test_cannot_use_consumed_asia_output():
    with pytest.raises(ValueError,match='ASIA'):
        with study.collection_context(study.collector.DATA,Path('new-freeze')):pass
