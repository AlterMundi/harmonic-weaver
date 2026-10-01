"""R04 prerequisites exercise the production relational estimator."""
import math
import pytest
from harmonic_weaver.lab.analysis_math import RelativeMode
from harmonic_weaver.lab.contracts import AlgorithmSettings


@pytest.mark.parametrize('time,value',[(.2,[float('nan'),1]),(.2,[float('inf'),0]),(.2,[1,2,3]),
    (.2,[[1,2]]),(.2,['x',1]),(float('nan'),[1,2]),(float('inf'),[1,2]),(-1,[1,2]),(True,[1,2])])
def test_invalid_relation_resets_history_and_recovers_without_poison(time,value):
    model=RelativeMode(AlgorithmSettings())
    model.push(0,[1,0]);assert model.push(.1,[2,0])['state']=='observed'
    assert model.push(time,value)['state']=='missing'
    assert not model.history and model.previous is None and not model.slope.samples
    assert model.push(.3,[1,0])['reason']=='warming relationship'
    result=model.push(.4,[2,0])
    assert result['state']=='observed' and result['I']==1
    assert all(math.isfinite(result[key]) for key in ('I','R','A'))
