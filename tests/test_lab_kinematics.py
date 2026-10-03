import math

import numpy as np
import pytest

from harmonic_weaver.lab.contracts import AlgorithmSettings, Joint, Person, Preset, MotionFrame
from harmonic_weaver.lab.kinematics import Kinematics, coordinates, observed_xy
from harmonic_weaver.lab.legacy import FrozenBaseline, baseline_module


def person(t):
    points = [[.4+(i%2)*.2+math.sin(t)*.04, .2+(i//2)*.07] for i in range(17)]
    return Person(person_id="one", joints=[Joint(index=i, position=p, confidence=1., state="observed") for i,p in enumerate(points)])


def test_torso_reference_removes_rigid_translation_and_rotation():
    raw = observed_xy(person(0))
    settings = AlgorithmSettings(reference="torso")
    first = coordinates(raw, settings, .2)
    angle = .7
    rotation = np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])
    second = coordinates(raw @ rotation.T + [3., -2.], settings, .2)
    assert second == pytest.approx(first)


def test_kinematics_resets_missing_joint_without_poisoning_others():
    model = Kinematics(AlgorithmSettings(), scale=.2)
    for i in range(30):
        output = model.push(i/30, person(i/30))
    assert np.isfinite(output["velocity"]).all()
    p = person(1.)
    p.joints[9].state = "missing"
    p.joints[9].position = None
    output = model.push(1., p)
    assert np.isnan(output["velocity"][9]).all()
    assert np.isfinite(output["velocity"][10]).all()
    output = model.push(1.033, person(1.033))
    assert np.isnan(output["velocity"][9]).all()
    output = model.push(3., person(3.))
    assert np.isnan(output["velocity"]).all()


def test_frozen_adapter_matches_published_controller_and_ticks_without_audio():
    preset = Preset()
    adapter = FrozenBaseline(preset)
    module = baseline_module()
    controls = module.LiveControls()
    reference = module.ConsonanceSession(module.ShaperOut("127.0.0.1",0,40.4,.03,True),controls=controls)
    for i in range(40):
        p = person(i/30)
        frame = MotionFrame(source_id="test",stream_id="test",sequence=i,source_time_s=i/30,
                            available_monotonic_s=i/30,timestamp_origin="synthetic",width=640,height=480,persons=[p])
        result = adapter.observe(frame,"one",i/30)
        reference.update({"stream_id":"test:one","persons":[dict(slot_id=0,focused=True,present=True,
            keypoints=[(*j.position,1.) for j in p.joints],kp_state=[(0,0,0)]*17,captured_at_us=round(i/30*1e6))]},now=i/30)
        for z in reference.state()["zones"]:
            assert result.signals[f'zone.{z["n"]}.gain'].value == pytest.approx(z["gain"])
            assert result.signals[f'zone.{z["n"]}.detune'].value == pytest.approx(z["detune"])
    assert adapter.session.out.sock is None
    history = list(adapter.session.tracker.zones[1].hist)
    adapter.tick(1.4)
    assert list(adapter.session.tracker.zones[1].hist) == history
