import numpy as np
import pytest
from harmonic_weaver.lab.research.membrane_transfer import Request,compare


def test_comparison_repeat_same_medium_and_raw_differences():
    request=Request(x=[0.,.3],y=[.5,.4],frequencies_hz=[0.,40.4])
    result=compare(request)
    assert result==compare(request)
    before=None
    for row in result['conditions']:
        value=np.array(row['real'])+1j*np.array(row['imag'])
        assert not value[:,0].any()
        if before is not None:
            np.testing.assert_allclose(row['difference_magnitude_vs_previous'],np.abs(value-before))
            assert all(r[0] is None for r in row['phase_difference_rad_vs_previous'])
        before=value


@pytest.mark.parametrize('bad',[{'resolutions':[{'modes_x':4,'modes_y':4},{'modes_x':2,'modes_y':8}]},
 {'frequencies_hz':[24000]}, {'membrane':{'damping_per_s':0}}, {'x':[.2,.3],'y':[.4]},
 {'resolutions':[{'modes_x':2,'modes_y':2},{'modes_x':2,'modes_y':2}]}])
def test_invalid_comparison_rejected(bad):
    with pytest.raises(ValueError):Request.model_validate(bad)
