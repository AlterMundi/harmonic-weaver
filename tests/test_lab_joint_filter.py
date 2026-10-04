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
