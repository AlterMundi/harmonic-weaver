from dataclasses import replace
import pytest
from harmonic_weaver.engine.compiler import RouteRuntime,evaluate_route
from harmonic_weaver.engine.model import HELD,INVALID
from test_capture_derivative import value
from test_phase_accumulator import _compile as phase_compile,_chain
from test_transforms_slew import _compile as slew_compile,_slew


def scenario(kind):
    if kind=='phase':return phase_compile(_chain(clock='source_capture',max_gap_ms=500.,max_dt_ms=1.)),'sensor.vel',.5,0.,1.5
    return slew_compile(_slew(clock='source_capture',max_gap_ms=500.,max_dt_ms=1.)),'sensor.target',10.,10.,.2


@pytest.mark.parametrize('kind',['phase','slew'])
def test_capture_time_rejects_jitter_duplicate_backward_without_changing_state(kind):
    compiled,address,target,seed,expected=scenario(kind)
    for receipts in [(0,1),(9_000_000,19_000_000)]:
        runtime=RouteRuntime()
        first_target=0. if kind=='slew' else target
        evaluate_route(compiled,runtime,{address:value(1,1_000_000,first_target)},receipts[0])
        assert evaluate_route(compiled,runtime,{address:value(2,1_100_000,target)},receipts[1])[0]==pytest.approx(expected)
        state=dict(runtime.phase_values if kind=='phase' else runtime.slew_values)
        for old in [value(2,1_100_000,target),value(1,1_150_000,target),value(3,1_050_000,target)]:
            assert evaluate_route(compiled,runtime,{address:old},99_000_000)==(None,'suppress')
            assert runtime.sample_reason=='capture_not_new'
        assert (runtime.phase_values if kind=='phase' else runtime.slew_values)==state


@pytest.mark.parametrize('kind',['phase','slew'])
@pytest.mark.parametrize('loss',['held','invalid','gap','stream'])
def test_capture_history_restarts_without_integrating_lost_time(kind,loss):
    compiled,address,target,seed,_=scenario(kind);runtime=RouteRuntime()
    evaluate_route(compiled,runtime,{address:value(1,1_000_000,target)},0)
    evaluate_route(compiled,runtime,{address:value(2,1_100_000,target)},1)
    if loss in ('held','invalid'):
        lost=replace(value(3,1_150_000,target),state=HELD if loss=='held' else INVALID)
        assert evaluate_route(compiled,runtime,{address:lost},2)==(None,'suppress')
        found=value(4,1_200_000,target)
    elif loss=='gap':found=value(3,2_000_000,target)
    else:found=value(1,50_000,target,stream='new')
    assert evaluate_route(compiled,runtime,{address:found},3)[0]==seed


@pytest.mark.parametrize('kind',['phase','slew'])
def test_capture_transforms_require_metadata_and_matching_inputs(kind):
    compiled,address,target,_,_=scenario(kind);runtime=RouteRuntime()
    legacy=replace(value(1,100_000,target),capture_identity=None)
    assert evaluate_route(compiled,runtime,{address:legacy},0)==(None,'suppress')
    assert runtime.sample_reason=='capture_metadata_required'
    compiled=replace(compiled,inputs=(address,'sensor.other'))
    compiled.definition['transforms'].insert(0,{'type':'combine','operator':'mean'})
    assert evaluate_route(compiled,runtime,{address:value(1,100_000,target),'sensor.other':value(2,100_000,target)},0)==(None,'suppress')
    assert runtime.sample_reason=='capture_inputs_not_aligned'


@pytest.mark.parametrize('kind',['phase','slew'])
@pytest.mark.parametrize('patch',[{'clock':'wall'},{'max_gap_ms':0.}])
def test_capture_clock_validation(kind,patch):
    params={'clock':'source_capture','max_gap_ms':500.};params.update(patch)
    with pytest.raises(Exception):
        phase_compile(_chain(**params)) if kind=='phase' else slew_compile(_slew(**params))
