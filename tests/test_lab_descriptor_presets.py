import math
import pytest
from harmonic_weaver.lab.contracts import FeatureFrame,Joint,MotionFrame,Person,Signal
from harmonic_weaver.lab.models import MotionModel
from harmonic_weaver.lab.presets import initial_presets,seed_presets
from harmonic_weaver.lab.routing import PreparedRoutes
from harmonic_weaver.lab.store import SessionStore


def presets():
    return {p.algorithm.id:p for p in initial_presets() if p.id.startswith('lab-v3-descriptor-')}


def test_angular_speed_does_not_cancel_opposed_distal_rotations_or_fill_missing():
    preset=presets()['angular'];model=MotionModel(preset,scale=.2)
    for i in range(20):
        t=i/30;positions=[[.4+(j%2)*.2,.2+(j//2)*.06] for j in range(17)]
        for elbow,wrist,direction in [(7,9,1),(8,10,-1)]:
            center=[.3 if direction==1 else .7,.5];positions[elbow]=center
            positions[wrist]=[center[0]+.08*math.cos(direction*t),center[1]+.08*math.sin(direction*t)]
        joints=[Joint(index=j,position=xy,confidence=1.,state='observed') for j,xy in enumerate(positions)]
        frame=MotionFrame(source_id='synthetic',stream_id='synthetic',sequence=i,source_time_s=t,
            available_monotonic_s=t,timestamp_origin='synthetic',width=640,height=480,
            persons=[Person(person_id='slot',joints=joints)])
        result=model.observe(frame,'slot',t)
    assert result.signals['zone.6.angular_velocity'].value==pytest.approx(0,abs=1e-8)
    assert result.signals['zone.6.angular_speed'].value==pytest.approx(180/math.pi,rel=.01)
    targets,_=PreparedRoutes(preset).evaluate(result,t)
    assert targets[5].gain>0
    frame.sequence+=1;frame.source_time_s+=1/30
    frame.persons[0].joints[9]=Joint(index=9,state='missing')
    missing=model.observe(frame,'slot',frame.source_time_s)
    assert missing.signals['zone.6.angular_speed'].state=='missing'
    assert PreparedRoutes(preset).evaluate(missing,frame.source_time_s)[0][5].gain==0


@pytest.mark.parametrize('model',['local','relational','angular','collective'])
def test_descriptor_mapping_uses_real_signal_support_preserves_six_ratios(model):
    preset=presets()[model];routes=PreparedRoutes(preset)
    values={'velocity_error':(.04,'T'),'gain':(.2,'1'),'I':(-1.,'1'),'angular_speed':(90.,'deg/s')}
    signals={f'zone.{z}.{name}':Signal(value=value,unit=unit,state='observed')
        for z in range(1,7) for name,(value,unit) in values.items()}
    signals.update({f'collective.mode.{i}':Signal(value=.2,unit='T/s',state='observed') for i in range(1,4)})
    signals.update({key:Signal(value=value,unit=unit,state='observed') for key,value,unit in
        [('collective.residual',.5,'1'),('collective.change',15.,'deg'),('global.speed',.4,'T/s')]})
    frame=FeatureFrame(source_time_s=1.,available_monotonic_s=1.,person_id='synthetic-slot',algorithm_id=model,signals=signals)
    targets,_=routes.evaluate(frame,1.)
    assert len(targets)==6 and all(t.gain>0 for t in targets)
    assert [t.frequency_hz for t in targets]==[preset.fundamental_hz*i for i in range(1,7)]
    assert all(t.phase_deg==0 for t in targets)
    # Removing actual support silences the destination; never substitutes a neutral descriptor.
    first=preset.routes[0].terms[0].source
    frame.signals[first]=Signal(value=None,unit=frame.signals[first].unit,state='missing',reason='controlled gap')
    assert PreparedRoutes(preset).evaluate(frame,2.)[0][0].gain==0
    if model=='relational':
        frame.signals['zone.1.gain']=signals['zone.2.gain'].model_copy()
        frame.signals['zone.1.I'].value=1.
        assert PreparedRoutes(preset).evaluate(frame,2.)[0][0].gain==0


def test_additive_seed_preserves_existing_edits_and_reference(tmp_path):
    store=SessionStore(tmp_path)
    try:
        seed_presets(store);p=store.load('lab-v3-descriptor-angular');p.master=.23;store.save(p)
        current=store.preset.model_dump();seed_presets(store)
        assert store.load(p.id).master==.23 and store.preset.model_dump()==current
        reference=store.load('lab-v2-reference-sustained')
        assert reference.expression==0 and reference.transient_mix==0
        assert len(reference.voices)==6
        assert not any(r.enabled for r in reference.routes if r.target in {'detune','phase_deg'})
    finally:store.close()
