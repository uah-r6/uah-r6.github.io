"""Actual consumed packet evidence, reduced without replay bytes or targets."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research'))
from objective_clock_candidate import candidate

CASES = json.loads((Path(__file__).parent / 'fixtures/objective-clock-cases.json').read_text())


@pytest.mark.parametrize('case', CASES, ids=[c['case'] for c in CASES])
def test_actual_disputed_actor_and_later_kill_collisions(case):
    # 4139 R07 must abstain, while actor-kill R04 and teammate-kill 4150 R07
    # retain the earlier standalone increment outside the later kill interval.
    assert candidate(case['row'], case['deaths'])[:2] == (case['expected'], case['reason'])


def test_unknown_death_offset_abstains_instead_of_assuming_eligibility():
    clean = next(c for c in CASES if c['expected'])
    assert candidate(clean['row'], [{'offset': 0}])[1] == 'unknown_death_offset'


def test_multiple_score_sources_cannot_silently_be_subtracted():
    clean = next(c for c in CASES if c['expected'])
    row = deepcopy(clean['row'])
    score = next(e for e in row['all_changes'] if e['counter'] == 'score')
    row['all_changes'].append({**score, 'offset': score['offset'] + 1, 'delta': 120})
    assert candidate(row, clean['deaths'])[1] == 'not_single_standalone_increment'
