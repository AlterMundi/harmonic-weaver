import json
import math

import pytest

from harmonic_weaver.lab.contracts import Joint, MotionFrame, Person, Preset
from harmonic_weaver.lab.models import MotionModel
from harmonic_weaver.lab.routing import PreparedRoutes


def observation(t, sequence, *, missing=False, identity="one"):
    joints = [Joint(index=i, position=[.4+(i%2)*.2+math.sin(t*(1+i/30))*.1,
                                      .2+(i//2)*.07+math.cos(t*2+i)*.03],
                    confidence=1., state="observed") for i in range(17)]
    return MotionFrame(source_id="test", stream_id="test", sequence=sequence, source_time_s=t,
        available_monotonic_s=t, timestamp_origin="synthetic", width=640, height=480,
        persons=[] if missing else [Person(person_id=identity, joints=joints)])


@pytest.mark.parametrize("algorithm", ["local", "relational", "angular", "collective"])
def test_models_feed_six_voices_and_reset_on_loss_and_seek(algorithm):
    preset = Preset()
    preset.algorithm.id = algorithm
    preset.response.pluck_enabled = False
    model, routes = MotionModel(preset, scale=.2), PreparedRoutes(preset)
    sounded = False
    for i in range(90):
        features = model.observe(observation(i/30, i), "one", i/30)
        json.dumps(features.model_dump(), allow_nan=False)
        voices, _ = routes.evaluate(features, i/30)
        assert len(voices) == 6
        sounded |= any(v.gain > 0 for v in voices)
    assert sounded
    history_length = len(model.kinematics.history)
    impulses = [p.count for p in model.plucks]
    for i in range(10):
        model.tick(3.+i/60)
    assert len(model.kinematics.history) == history_length
    assert [p.count for p in model.plucks] == impulses
    features = model.observe(observation(3., 90, missing=True), "one", 3.)
    assert all(v.gain == 0 for v in routes.evaluate(features, 3.)[0])
    features = model.observe(observation(.1, 3), "one", 4.)
    assert all(v.gain == 0 for v in routes.evaluate(features, 4.)[0])
    assert len(model.kinematics.history) == 1


def test_new_models_require_explicit_scale():
    model = MotionModel(Preset(algorithm={"id":"local"}))
    for i in range(20):
        features = model.observe(observation(i/30, i), "one", i/30)
    assert features.signals["zone.1.speed"].state == "missing"
    assert features.diagnostics["scale"] is None
