import math

import pytest

from harmonic_weaver.lab.body_volume import BodyVolume
from harmonic_weaver.lab.contracts import BodyVolumeSettings, Joint, MotionFrame, Person, Preset
from harmonic_weaver.lab.routing import PreparedRoutes
from test_lab_routing import complete_frame


def pose(span, *, factor=1., missing=None, identity="one"):
    positions={5:(-.2,0),6:(.2,0),11:(-.2,1),12:(.2,1),9:(-span/2,.5),10:(span/2,.5)}
    joints=[Joint(index=i,position=[factor*x,factor*y],confidence=1,state="observed")
            for i,(x,y) in positions.items() if i!=missing]
    return MotionFrame(source_id="synthetic",stream_id="same-stream",sequence=0,
        source_time_s=0,available_monotonic_s=0,timestamp_origin="synthetic",width=640,height=480,
        persons=[Person(person_id=identity,joints=joints)])


def test_openness_is_normalized_monotonic_and_only_observed():
    cfg=BodyVolumeSettings(smoothing_s=0)
    body=BodyVolume()
    assert body.update(pose(1),"one",cfg,0)["level"]==0
    assert body.update(pose(2),"one",cfg,.1)["level"]==pytest.approx(.5)
    assert body.update(pose(3),"one",cfg,.2)["level"]==1
    assert body.update(pose(2,factor=2),"one",cfg,.3)["level"]==pytest.approx(.5)
    assert body.update(pose(3,missing=9),"one",cfg,.4)["state"]=="missing"
    assert body.diagnostic['level']==0
    assert body.update(None,"one",cfg,.5)["state"]=="missing"
    assert body.update(pose(11),"one",cfg,.6)["state"]=="missing"


def test_openness_smoothing_and_identity_change_do_not_hold_old_body_level():
    body=BodyVolume();cfg=BodyVolumeSettings(smoothing_s=.2)
    assert body.update(pose(3),"one",cfg,0)["level"]==0
    assert body.update(pose(3),"one",cfg,.2)["level"]==pytest.approx(1-math.exp(-1))
    assert body.update(pose(3,identity="two"),"two",cfg,.3)["level"]==0
    with pytest.raises(ValueError):BodyVolumeSettings(closed_ratio=3,open_ratio=2)


def test_listening_gain_preserves_neutral_and_caps_boosted_targets():
    old=PreparedRoutes(Preset()).evaluate(complete_frame(),0)[0]
    same=PreparedRoutes(Preset(output_gain=1)).evaluate(complete_frame(),0)[0]
    assert same==old
    twice=PreparedRoutes(Preset(output_gain=2)).evaluate(complete_frame(),0)[0]
    assert twice[0].gain==pytest.approx(old[0].gain*2)
    assert all(t.gain==0 for t in PreparedRoutes(Preset(output_gain=0)).evaluate(complete_frame(),0)[0])
    preset=Preset(output_gain=4,master=1)
    assert all(0<=t.gain<=1 for t in PreparedRoutes(preset).evaluate(complete_frame(),0)[0])


def test_aperture_can_scale_motion_or_sustain_pose_and_preserves_missing_mute_and_solo():
    preset=Preset(master=1,body_volume={"enabled":True,"mode":"scale"})
    graph=PreparedRoutes(preset)
    assert graph.evaluate(complete_frame(),0,body_level=.5)[0][0].gain==pytest.approx(.15)
    assert all(t.gain==0 for t in graph.evaluate(complete_frame(),.1,body_level=None)[0])
    preset.body_volume.mode="pose"
    stationary=complete_frame()
    for index in range(1,7):stationary.signals[f"zone.{index}.gain"].value=0
    targets,_=PreparedRoutes(preset).evaluate(stationary,0,body_level=.6)
    assert all(t.gain==pytest.approx(.6) for t in targets)
    preset.voices[3].solo=True
    targets,_=PreparedRoutes(preset).evaluate(stationary,0,body_level=.6)
    assert [t.id for t in targets if t.gain>0]==[4]
    preset.voices[3].muted=True
    assert all(t.gain==0 for t in PreparedRoutes(preset).evaluate(stationary,0,body_level=.6)[0])
    preset.voices[3].muted=False
    stationary.signals['zone.4.gain'].state='missing';stationary.signals['zone.4.gain'].value=None
    assert all(t.gain==0 for t in PreparedRoutes(preset).evaluate(stationary,0,body_level=.6)[0])


def test_pose_volume_does_not_create_sound_in_an_unrouted_voice():
    preset=Preset(body_volume={"enabled":True,"mode":"pose"})
    for route in preset.routes:
        if route.voice==1 and route.target=='gain':route.enabled=False
    assert PreparedRoutes(preset).evaluate(complete_frame(),0,body_level=1)[0][0].gain==0


def test_runtime_open_pose_sustains_available_voices_and_closing_silences(tmp_path):
    from test_lab_camera_selection import setup_runtime, frame
    runtime,camera,audio,store,now=setup_runtime(tmp_path)
    try:
        preset,revision,_=store.configuration()
        preset.body_volume=BodyVolumeSettings(enabled=True,mode='pose',smoothing_s=0)
        store.edit(preset,revision)
        for index in range(12):
            now[0]=10+index/30
            camera.frame=frame(now[0],index,['one'])
            camera.frame.persons[0].joints[9].position=[0.,.4]
            camera.frame.persons[0].joints[10].position=[1.,.4]
            runtime.tick()
        assert runtime.body_volume.diagnostic['state']=='observed'
        assert len([t for t in audio.targets if t.gain>0])==6
        now[0]+=.03
        camera.frame=frame(now[0],13,['one'])
        camera.frame.persons[0].joints[9].position=[.5,.4]
        camera.frame.persons[0].joints[10].position=[.5,.4]
        runtime.tick()
        assert all(t.gain==0 for t in audio.targets)
        camera.frame.persons[0].joints[9].state='missing'
        camera.frame.persons[0].joints[9].position=None
        camera.frame.sequence+=1;now[0]+=.03;runtime.tick()
        assert runtime.body_volume.diagnostic['state']=='missing'
        assert all(t.gain==0 for t in audio.targets)
    finally:store.close()
