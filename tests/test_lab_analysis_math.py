import math

import numpy as np
import pytest

from harmonic_weaver.lab.analysis_math import AngularMode, CausalSlope, RelativeMode, interference
from harmonic_weaver.lab.contracts import AlgorithmSettings


def test_anni_four_discriminating_sequences():
    assert interference([0, 0], [0, 0], .01, .001)["reason"] == "no established mode"
    reduced = interference([1, 0], [-.8, 0], .01, .001)
    assert reduced["I"] == -1
    turning = interference([1, 0], [0, 1], .01, .001)
    assert turning["I"] == 0 and turning["R"] == 1 and turning["angle_deg"] == 90
    assert interference([1, 0], [-.5, 0], .01, .001)["I"] == -1
    assert interference([-1, 0], [-.5, 0], .01, .001)["I"] == 1
    assert interference([1, 0], [0, 0], .01, .001)["reason"] == "no detectable contribution"


def test_relative_history_excludes_new_sample_and_2d_components_are_dependent():
    settings = AlgorithmSettings(noise_delta=.001)
    model = RelativeMode(settings)
    model.push(0., [1., 0.])
    model.push(.05, [1., 0.])
    result = model.push(.1, [-1., 1.])
    assert result["prior_mode"] == [1., 0.]
    assert result["I"] < 0
    assert result["I"]**2 + result["R"]**2 == pytest.approx(1.)
    assert result["delta_per_s"] == pytest.approx([-40., 20.])
    model.push(.15, None)
    assert model.push(.2, [3., 3.])["reason"] == "warming relationship"


@pytest.mark.parametrize("fps", [20, 30, 60])
def test_causal_regression_uses_seconds_and_resets_gaps(fps):
    slope = CausalSlope(window_s=.2)
    results = [slope.push(i/fps, [2*i/fps, -3*i/fps]) for i in range(fps)]
    assert results[-1] == pytest.approx([2., -3.])
    assert slope.push(3., [99., 99.]) is None
    assert slope.push(3.03, None) is None
    assert not slope.samples


def test_angular_unwrap_and_prediction_do_not_see_future():
    model = AngularMode(AlgorithmSettings(derivative_window_s=.12, horizon_s=.1))
    results = []
    for i in range(40):
        t = i/30
        angle = math.radians(170)+t
        results.append(model.push(t, [math.cos(angle), math.sin(angle)]))
    assert results[-1]["angle_deg"] > 180
    assert results[-1]["velocity_deg_s"] == pytest.approx(math.degrees(1.), abs=1e-6)
    assert results[-1]["prediction_error_deg"] == pytest.approx(0., abs=1e-6)
    model.push(2., None)
    assert model.push(2.03, [1., 0.])["velocity_deg_s"] is None
