import numpy as np
import pytest
from harmonic_weaver.lab.contracts import AlgorithmSettings, Joint
from harmonic_weaver.lab.joint_filter import JointMotionFilter
from harmonic_weaver.lab.models import MotionModel
from harmonic_weaver.lab.presets import initial_presets
from test_lab_models import observation


def settings(**kw):
    return AlgorithmSettings(tracking_filter_enabled=True, **kw)


def point(frame,index):
    return np.array(next(j.position[:2] for j in frame.persons[0].joints if j.index==index))


def test_disabled_filter_is_exact_passthrough():
    frame=observation(0.,0)
    f=JointMotionFilter(AlgorithmSettings(),.2)
    result,diag=f.push(frame,'one')
    assert result is frame and diag=={'enabled':False}


def test_isolated_label_swap_is_repaired_without_collapsing_the_pelvis_or_mutating_raw():
    f=JointMotionFilter(settings(tracking_smoothing_s=0.,tracking_median_frames=1),.2)
    first=observation(0.,0);f.push(first,'one')
    second=first.model_copy(deep=True);second.source_time_s=1/30;second.sequence=1
    left=second.persons[0].joints[11];right=second.persons[0].joints[12]
    left.position,right.position=right.position,left.position
    raw=second.model_dump()
    fixed,diag=f.push(second,'one')
    assert diag['hip_labels_swapped']
    assert point(fixed,11)==pytest.approx(point(first,11))
    assert point(fixed,12)==pytest.approx(point(first,12))
    assert second.model_dump()==raw


def test_acceleration_limits_are_per_joint_and_use_source_time_with_irregular_cadence():
    limits=[30.]*17;limits[9]=300.
    cfg=settings(tracking_smoothing_s=0.,tracking_median_frames=1,tracking_hip_swap_guard=False,tracking_joint_accel_limits=limits)
    f=JointMotionFilter(cfg,.2);base=observation(0.,0);f.push(base,'one')
    previous={j:point(base,j)/.2 for j in [9,11]};velocity={j:np.zeros(2) for j in [9,11]};t=0.
    for i,dt in enumerate([.02,.04,.03,.02,.05]*4,1):
        t+=dt;frame=base.model_copy(deep=True);frame.source_time_s=t;frame.sequence=i
        for j in [9,11]:frame.persons[0].joints[j].position[0]+=2. if i%2 else -2.
        result,_=f.push(frame,'one')
        for j in [9,11]:
            p=point(result,j)/.2;v=(p-previous[j])/dt
            assert np.linalg.norm(v-velocity[j])/dt<=limits[j]+1e-8
            previous[j],velocity[j]=p,v


def test_real_steady_motion_survives_and_missing_or_held_points_are_never_filled():
    cfg=settings(tracking_smoothing_s=.04,tracking_median_frames=3)
    f=JointMotionFilter(cfg,.2);base=observation(0.,0)
    for i in range(90):
        frame=base.model_copy(deep=True);frame.source_time_s=i/30;frame.sequence=i
        for q in frame.persons[0].joints:q.position[0]+=.04*frame.source_time_s
        result,_=f.push(frame,'one')
    assert abs(point(result,11)[0]-point(frame,11)[0])<.006
    assert not np.allclose(point(result,11),point(base,11))
    frame.source_time_s+=1/30;frame.persons[0].joints[11]=Joint(index=11,state='missing')
    result,_=f.push(frame,'one')
    assert result.persons[0].joints[11].position is None
    assert 11 not in f.states
    frame.source_time_s+=1/30;frame.persons[0].joints[11]=Joint(index=11,state='held',position=[1.,1.])
    result,_=f.push(frame,'one')
    assert result.persons[0].joints[11].state=='held' and 11 not in f.states


def test_conditioning_shared_by_baseline_and_new_models_resets_at_seek():
    for algorithm in ['baseline','angular','relational','collective']:
        p=next(p for p in initial_presets() if p.algorithm.id==algorithm)
        p.algorithm.tracking_filter_enabled=True
        m=MotionModel(p,.2)
        for i in range(20):z=m.observe(observation(i/30,i),'one',i/30)
        assert z.diagnostics['tracking_filter']['enabled'] and m.conditioned_frame is not None
        first=observation(.1,3);z=m.observe(first,'one',2.)
        assert point(m.conditioned_frame,11)==pytest.approx(point(first,11))
        assert m.joint_filter.states[11]['velocity']==pytest.approx(np.zeros(2))
        assert len(m.joint_filter.states[11]['measurements'])==1


@pytest.fixture
def native_one_euro():
    from pathlib import Path
    import os
    from harmonic_weaver.lab.joint_filter import harmocap_one_euro
    checkout = Path(os.environ.get('HARMOCAP_DIR', Path.home()/'Projects/HarMoCAP'))
    if not (checkout/'src/harmocap/smoothing.py').exists():
        pytest.skip('native HarMoCAP checkout not present')
    return harmocap_one_euro()[0]


def test_native_one_euro_matches_harmocap_without_stacking_other_filters(native_one_euro):
    cfg=settings(tracking_smoother='harmocap_one_euro',tracking_median_frames=9,
                 tracking_joint_accel_limits=[.1]*17)
    f=JointMotionFilter(cfg,.2)
    reference=[native_one_euro() for _ in range(2)]
    base=observation(0.,0)
    for i, t in enumerate([0.,.02,.06,.09,.14,.18]):
        frame=base.model_copy(deep=True);frame.source_time_s=t;frame.sequence=i
        frame.persons[0].joints[11].position[0]+=.03*np.sin(i)
        raw=frame.model_dump()
        out,diag=f.push(frame,'one')
        dt=0 if i==0 else t-last_t
        expected=[ff(x,dt) for ff,x in zip(reference,point(frame,11))]
        assert point(out,11)==pytest.approx(expected)
        assert frame.model_dump()==raw
        assert diag['smoother']=='harmocap_one_euro' and not diag['acceleration_limited_joints']
        last_t=t


def test_native_one_euro_resets_at_missing_held_seek_and_long_gap(native_one_euro):
    f=JointMotionFilter(settings(tracking_smoother='harmocap_one_euro'),.2)
    base=observation(0.,0);f.push(base,'one')
    for state in ['missing','held']:
        lost=base.model_copy(deep=True);lost.source_time_s=.1
        lost.persons[0].joints[11]=Joint(index=11,state=state,position=None if state=='missing' else [9.,9.])
        out,_=f.push(lost,'one')
        assert out.persons[0].joints[11].state==state and 11 not in f.states
        found=base.model_copy(deep=True);found.source_time_s=.2
        found.persons[0].joints[11].position=[.8,.9]
        out,_=f.push(found,'one');assert point(out,11)==pytest.approx([.8,.9])
    for t in [.05, 4.]:
        frame=base.model_copy(deep=True);frame.source_time_s=t
        out,_=f.push(frame,'one');assert point(out,11)==pytest.approx(point(frame,11))


def test_native_one_euro_recovers_missing_person_without_calibration(native_one_euro):
    f=JointMotionFilter(settings(tracking_smoother='harmocap_one_euro'))
    base=observation(0.,0);f.push(base,'one')
    lost=base.model_copy(deep=True);lost.source_time_s=.1;lost.persons=[]
    f.push(lost,'one');assert not f.states
    base.source_time_s=.2
    out,_=f.push(base,'one');assert point(out,11)==pytest.approx(point(base,11))


@pytest.mark.parametrize('algorithm',['baseline','local','relational','angular','collective'])
@pytest.mark.parametrize('guard',[False,True])
def test_native_one_euro_is_shared_by_models_and_resets_at_seek(native_one_euro,algorithm,guard):
    p=next(p for p in initial_presets() if p.algorithm.id==algorithm)
    p.algorithm.tracking_filter_enabled=True
    p.algorithm.tracking_smoother='harmocap_one_euro'
    p.algorithm.tracking_one_euro_hip_swap_guard=guard
    m=MotionModel(p,.2)
    for i in range(8):
        z=m.observe(observation(i/30,i),'one',i/30)
    assert z.diagnostics['tracking_filter']['smoother']=='harmocap_one_euro'
    first=observation(.05,1);m.observe(first,'one',2.)
    assert point(m.conditioned_frame,11)==pytest.approx(point(first,11))


def test_bounded_filter_forgets_omitted_joint_without_filling_reacquisition():
    f = JointMotionFilter(settings(), .2)
    base = observation(0., 0)
    f.push(base, 'one')
    lost = observation(.03, 1)
    lost.persons[0].joints = [q for q in lost.persons[0].joints if q.index != 11]
    out, _ = f.push(lost, 'one')
    assert 11 not in f.states
    assert all(q.index != 11 for q in out.persons[0].joints)
    found = observation(.06, 2)
    found.persons[0].joints[11].position = [.9,.8]
    out, _ = f.push(found, 'one')
    assert point(out, 11) == pytest.approx([.9,.8])
    assert f.states[11]['velocity'] == pytest.approx(np.zeros(2))


def test_native_optional_hip_repair_matches_unswapped_reference_and_keeps_other_joints(native_one_euro):
    cfg=settings(tracking_smoother='harmocap_one_euro',tracking_one_euro_hip_swap_guard=True)
    repaired=JointMotionFilter(cfg,.2)
    reference=JointMotionFilter(settings(tracking_smoother='harmocap_one_euro'),.2)
    for i in range(12):
        expected_frame=observation(i/30,i)
        raw=expected_frame.model_copy(deep=True)
        # Both a persistent mislabeled run and return to the original labels.
        if 3 <= i <= 8:
            a,b=raw.persons[0].joints[11:13]
            a.position,b.position=b.position,a.position
            a.confidence,b.confidence=.4,.9
        before=raw.model_dump()
        out,diag=repaired.push(raw,'one')
        expected,_=reference.push(expected_frame,'one')
        assert diag['hip_labels_swapped']==(3 <= i <= 8)
        assert not diag['acceleration_limited_joints']
        for index in range(17):assert point(out,index)==pytest.approx(point(expected,index))
        if 3 <= i <= 8:
            assert out.persons[0].joints[11].confidence==.9
        assert raw.model_dump()==before


@pytest.mark.parametrize('loss',['missing','held','omitted','seek','gap'])
def test_native_hip_repair_does_not_reuse_assignment_across_lost_support(native_one_euro,loss):
    f=JointMotionFilter(settings(tracking_smoother='harmocap_one_euro',tracking_one_euro_hip_swap_guard=True),.2)
    base=observation(0.,0);f.push(base,'one')
    found=base.model_copy(deep=True);found.source_time_s=.1
    if loss in ('missing','held','omitted'):
        lost=base.model_copy(deep=True);lost.source_time_s=.03
        if loss=='omitted':lost.persons[0].joints=[q for q in lost.persons[0].joints if q.index!=11]
        else:lost.persons[0].joints[11]=Joint(index=11,state=loss,position=None if loss=='missing' else [1.,1.])
        f.push(lost,'one')
    elif loss=='seek':found.source_time_s=0.
    else:found.source_time_s=3.
    a,b=found.persons[0].joints[11:13];a.position,b.position=b.position,a.position
    out,diag=f.push(found,'one')
    assert not diag['hip_labels_swapped']
    assert point(out,11)==pytest.approx(point(found,11))


def test_native_guard_option_is_portable_and_defaults_off():
    from harmonic_weaver.lab.contracts import Preset
    preset=Preset()
    assert not preset.algorithm.tracking_one_euro_hip_swap_guard
    preset.algorithm.tracking_one_euro_hip_swap_guard=True
    assert Preset.model_validate_json(preset.model_dump_json()).algorithm.tracking_one_euro_hip_swap_guard
