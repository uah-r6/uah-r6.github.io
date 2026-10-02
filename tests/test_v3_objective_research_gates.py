"""Research split/missing-data gates prevent final leakage and invented zeros."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from v3_objective_fit import development_groups


def test_missing_actor_map_never_enters_development_as_zero():
    rows=[dict(event='train',reserved_for_final_test=False,fit_eligible=True,objective_map_complete=False)]
    with pytest.raises(ValueError,match='Missing objective actors'):
        development_groups(rows,dict(train_events=['train'],development_event='dev'))


@pytest.mark.parametrize('event,reserved',[('final',False),('train',True),('dev',True)])
def test_final_events_and_reserved_rows_are_rejected_before_fit(event,reserved):
    rows=[dict(event=event,reserved_for_final_test=reserved,fit_eligible=True,objective_map_complete=True)]
    with pytest.raises(ValueError,match='Final/reserved'):
        development_groups(rows,dict(train_events=['train'],development_event='dev'))
