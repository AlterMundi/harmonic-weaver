from dataclasses import asdict,replace
import math
import pytest
from harmonic_weaver.engine.compiler import RouteRuntime,evaluate_route
from harmonic_weaver.engine.model import HELD,INVALID
from test_capture_derivative import value
from test_transforms_smoothing import _compile


def route(kind,**patch):
    transform={'type':kind,'clock':'source_capture','max_gap_ms':500.}
    if kind=='beat_envelope':transform.update(tau_ms=100.,min_interval_ms=200.)
    elif kind=='peak_detector':transform.update(threshold=.5,refractory_ms=200.)
    else:transform.update(dwell_ms=80.)
    transform.update(patch)
    return _compile([transform])


def read(compiled,runtime,frame,stamp,number,receipt):
    return evaluate_route(compiled,runtime,{'sensor.target':value(frame,stamp,float(number))},receipt)


@pytest.mark.parametrize('kind',['beat_envelope','peak_detector','pad_dwell'])
def test_source_event_response_is_invariant_to_receipt_jitter_and_duplicate(kind):
    numbers={'beat_envelope':[0,1,1,0,1],'peak_detector':[.4,1,.9,1,.9],'pad_dwell':[0,1,1,0,0]}[kind]
    traces=[]
    for receipts in [list(range(5)),[9_000_000,99_000_000,199_000_000,209_000_000,999_000_000]]:
        runtime=RouteRuntime();compiled=route(kind);trace=[]
        for i,(number,receipt) in enumerate(zip(numbers,receipts)):
            stamp=1_000_000+i*(50_000 if kind=='pad_dwell' else 100_000)
            result=read(compiled,runtime,i,stamp,number,receipt)
            trace.append(result[0])
            before=asdict(runtime);before.pop('sample_reason')
            for frame,t in [(i,stamp),(max(0,i-1),stamp+1),(i+1,stamp-1)]:
                assert read(compiled,runtime,frame,t,1,receipt+1000)==(None,'suppress')
                assert runtime.sample_reason=='capture_not_new'
                after=asdict(runtime);after.pop('sample_reason');assert after==before
        traces.append(trace)
    assert traces[0]==traces[1]
    expected={'beat_envelope':[0.,1.,math.exp(-1),math.exp(-2),1.],
              'peak_detector':[0.,0.,1.,0.,1.],'pad_dwell':[0.,0.,1.,1.,0.]}[kind]
    assert traces[0]==pytest.approx(expected)


@pytest.mark.parametrize('kind',['beat_envelope','peak_detector','pad_dwell'])
@pytest.mark.parametrize('loss',['held','invalid','gap','stream'])
def test_events_warm_after_loss_without_fictional_onset_or_peak(kind,loss):
    compiled=route(kind);runtime=RouteRuntime()
    read(compiled,runtime,0,1_000_000,.2,0)
    read(compiled,runtime,1,1_100_000,1.,1)
    if loss in ('held','invalid'):
        sample=replace(value(2,1_150_000,1.),state=HELD if loss=='held' else INVALID)
        assert evaluate_route(compiled,runtime,{'sensor.target':sample},2)==(None,'suppress')
        found=value(3,1_200_000,.9)
    elif loss=='gap':found=value(3,2_000_000,.9)
    else:found=value(0,50_000,.9,stream='new')
    assert evaluate_route(compiled,runtime,{'sensor.target':found},3)[0]==(.9 if kind=='pad_dwell' else 0.)
    # Dropping immediately from a high first sample is not an observed peak.
    again=replace(found,value=.8,captured_at_us=found.captured_at_us+50_000,
                  capture_identity=found.capture_identity[:-1]+(found.capture_identity[-1]+1,))
    assert evaluate_route(compiled,runtime,{'sensor.target':again},4)[0]==(.9 if kind=='pad_dwell' else 0.)


@pytest.mark.parametrize('kind',['beat_envelope','peak_detector','pad_dwell'])
@pytest.mark.parametrize('patch',[{'clock':'wall'},{'max_gap_ms':0.}])
def test_source_event_clock_validation(kind,patch):
    with pytest.raises(Exception):route(kind,**patch)


@pytest.mark.parametrize('kind',['beat_envelope','peak_detector','pad_dwell'])
def test_missing_capture_metadata_breaks_event_history(kind):
    compiled=route(kind);runtime=RouteRuntime()
    read(compiled,runtime,0,1_000_000,.2,0)
    read(compiled,runtime,1,1_100_000,1.,1)
    missing=replace(value(2,1_150_000,.8),capture_identity=None)
    assert evaluate_route(compiled,runtime,{'sensor.target':missing},2)==(None,'suppress')
    assert runtime.sample_reason=='capture_metadata_required'
    assert read(compiled,runtime,3,1_200_000,.8,3)[0]==(.8 if kind=='pad_dwell' else 0.)
