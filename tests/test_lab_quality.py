import pytest
from harmonic_weaver.lab.quality import coverage
from test_lab_models import observation


def test_coverage_reports_missing_duration_and_does_not_stretch_observation():
    a=observation(0.,0)
    a.duration_s=.1
    b=observation(.5,1,missing=True)
    b.duration_s=.1
    report=coverage([a,b],end_s=1.,person_id="one")
    joint=report["persons"]["one"]["joints"][9]
    assert joint["observed_s"]==pytest.approx(.1)
    assert joint["missing_s"]==pytest.approx(.9)
    assert joint["max_gap_s"]==pytest.approx(.9)
    assert joint["observed_fraction"]==pytest.approx(.1)
