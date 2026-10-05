from dataclasses import replace
import math
import pytest
from harmonic_weaver.engine.compiler import RouteRuntime,evaluate_route
from harmonic_weaver.engine.model import HELD,INVALID
from test_capture_derivative import value
from test_transforms_smoothing import _compile,_smooth


def sample(frame,time,number,**kwargs):return value(frame,time,float(number),**kwargs)
def route(kind='one_pole',**kwargs):return _compile(_smooth(kind,time_ms=200.,clock='source_capture',max_gap_ms=500.,**kwargs))


@pytest.mark.parametrize('kind',['one_pole','ramp'])
def test_capture_response_uses_real_delta_and_ignores_receipt_jitter(kind):
    for receipts in [(0,1),(10_000_000,99_000_000)]:
        runtime=RouteRuntime();compiled=route(kind,max_dt_ms=1.)
        evaluate_route(compiled,runtime,{'sensor.target':sample(1,1_000_000,0)},receipts[0])
        result,_=evaluate_route(compiled,runtime,{'sensor.target':sample(2,1_100_000,10)},receipts[1])
        alpha=1-math.exp(-.5) if kind=='one_pole' else .5
        assert result==pytest.approx(10*alpha)
        assert runtime.smooth_at_us[0]==1_100_000
        for stale in (sample(2,1_100_000,9),sample(1,1_150_000,9),sample(3,1_050_000,9)):
            assert evaluate_route(compiled,runtime,{'sensor.target':stale},999_000_000)==(None,'suppress')
            assert runtime.sample_reason=='capture_not_new'
            assert runtime.smooth_values[0]==pytest.approx(result)


@pytest.mark.parametrize('loss',['held','invalid','gap','stream'])
def test_capture_smoothing_restarts_after_loss_or_epoch(loss):
    runtime=RouteRuntime();compiled=route()
    evaluate_route(compiled,runtime,{'sensor.target':sample(1,1_000_000,0)},0)
    evaluate_route(compiled,runtime,{'sensor.target':sample(2,1_100_000,10)},1)
    if loss in ('held','invalid'):
        lost=replace(sample(3,1_150_000,9),state=HELD if loss=='held' else INVALID)
        assert evaluate_route(compiled,runtime,{'sensor.target':lost},2)==(None,'suppress')
        found=sample(4,1_200_000,8)
    elif loss=='gap':found=sample(3,2_000_000,8)
    else:found=sample(1,50_000,8,stream='new-stream')
    assert evaluate_route(compiled,runtime,{'sensor.target':found},3)==(8.,'usable')


def test_capture_smoothing_requires_metadata_and_aligned_inputs():
    compiled=route();runtime=RouteRuntime()
    legacy=replace(sample(1,100_000,1),capture_identity=None)
    assert evaluate_route(compiled,runtime,{'sensor.target':legacy},0)==(None,'suppress')
    assert runtime.sample_reason=='capture_metadata_required'
    compiled=replace(compiled,inputs=('sensor.target','sensor.other'))
    compiled.definition['transforms'].insert(0,{'type':'combine','operator':'mean'})
    assert evaluate_route(compiled,runtime,{'sensor.target':sample(1,100_000,1),'sensor.other':sample(2,100_000,1)},0)==(None,'suppress')
    assert runtime.sample_reason=='capture_inputs_not_aligned'
    assert not runtime.smooth_capture_samples


@pytest.mark.parametrize('patch',[{'clock':'wall'},{'max_gap_ms':0.}])
def test_invalid_capture_clock_settings_rejected(patch):
    params=dict(time_ms=100.,clock='source_capture',max_gap_ms=500.);params.update(patch)
    with pytest.raises(Exception):_compile(_smooth(**params))


def test_capture_smoothing_then_derivative_uses_same_source_clock():
    transforms=_smooth(time_ms=200.,clock='source_capture',max_gap_ms=500.)
    transforms.extend([{'type':'derivative','window_ms':40.,'max_abs':100.,'max_dt_ms':1.,'clock':'source_capture','max_gap_ms':500.},
                       {'type':'scale_range','in':[-100.,100.],'out':[0.,10.],'clamp':True}])
    compiled=_compile(transforms);runtime=RouteRuntime()
    assert evaluate_route(compiled,runtime,{'sensor.target':sample(1,1_000_000,0)},0)[0]==5.
    out=evaluate_route(compiled,runtime,{'sensor.target':sample(2,1_100_000,10)},9_000_000)[0]
    smoothed=10*(1-math.exp(-.5))
    assert out==pytest.approx(5+smoothed/.1/20)
    assert runtime.smooth_at_us[0]==runtime.derivative_at_us[1]==1_100_000
    prior=dict(runtime.smooth_values)
    assert evaluate_route(compiled,runtime,{'sensor.target':sample(2,1_100_000,10)},19_000_000)==(None,'suppress')
    assert runtime.smooth_values==prior


def test_observation_reset_preserves_engine_smoothing_and_drops_capture_smoothing():
    runtime=RouteRuntime(smooth_values={0:3.,1:4.},smooth_at_us={0:1,1:2},
                         smooth_capture_samples={1:(('synthetic',),2)})
    runtime.reset_observation_history()
    assert runtime.smooth_values=={0:3.} and runtime.smooth_at_us=={0:1}
    assert not runtime.smooth_capture_samples
