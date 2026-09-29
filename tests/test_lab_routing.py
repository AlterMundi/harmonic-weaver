import pytest

from harmonic_weaver.lab.contracts import FeatureFrame, Preset, Signal
from harmonic_weaver.lab.routing import PreparedRoutes


def frame(**signals):
    return FeatureFrame(source_time_s=0.,available_monotonic_s=0.,person_id="a",algorithm_id="local",
                        signals={k:Signal(value=v,unit="deg" if "phase_deg" in k else "1") for k,v in signals.items()})


def complete_frame():
    return frame(**{f"zone.{i}.{k}":v for i in range(1,7) for k,v in (("gain",.3),("detune",.2),("phase_deg",10.))})


def test_all_six_voices_and_explicit_unit_validation():
    preset = Preset()
    graph = PreparedRoutes(preset)
    targets, status = graph.evaluate(complete_frame(), 0.)
    assert len(targets)==6 and not status["invalid_voices"]
    assert targets[5].frequency_hz==pytest.approx(40.4*6.1)
    assert targets[0].gain==pytest.approx(.21)
    preset.routes[0].terms[0].source="global.speed"
    with pytest.raises(ValueError,match="expected unit T/s"):
        PreparedRoutes(preset)
    preset.routes[0].terms[0].input_unit="T/s"
    PreparedRoutes(preset)


def test_missing_held_and_mute_solo_do_not_leave_old_gain():
    preset = Preset()
    graph = PreparedRoutes(preset)
    graph.evaluate(complete_frame(),0.)
    missing = complete_frame()
    missing.signals["zone.1.detune"].state="held"
    targets, status = graph.evaluate(missing,.1)
    assert targets[0].gain==0 and targets[1].gain>0
    assert status["invalid_voices"]==[1]
    preset.voices[3].solo=True
    targets,_=PreparedRoutes(preset).evaluate(complete_frame(),.2)
    assert [t.id for t in targets if t.gain>0]==[4]
    preset.voices[3].muted=True
    assert all(t.gain==0 for t in PreparedRoutes(preset).evaluate(complete_frame(),.3)[0])


def test_mixes_curves_and_smoothing_are_source_rate_independent():
    preset=Preset()
    route=preset.routes[0]
    route.terms.append(route.terms[0].model_copy(update={"weight":-1.,"offset":.8}))
    route.mix="mean"
    graph=PreparedRoutes(preset)
    assert graph.evaluate(complete_frame(),0.)[0][0].gain==pytest.approx(.4*preset.master)
    route.terms=route.terms[:1]
    route.smoothing_s=.2
    graph=PreparedRoutes(preset)
    first=complete_frame();first.signals['zone.1.gain'].value=0.
    graph.evaluate(first,0.)
    target=graph.evaluate(complete_frame(),.2)[0][0]
    import math
    assert target.gain==pytest.approx(.3*(1-math.exp(-1))*.7)
    graph.reset()
    assert graph.evaluate(complete_frame(),.21)[0][0].gain==pytest.approx(.21)


def test_graph_rejects_unknown_signals_and_invalid_pitch_before_apply():
    p=Preset();p.routes[0].terms[0].source="eval('__import__')"
    with pytest.raises(ValueError,match="unknown signal"):
        PreparedRoutes(p)
    p=Preset();p.voices[0].ratio=.1
    with pytest.raises(ValueError,match="non-positive"):
        PreparedRoutes(p)


def test_expression_preserves_tuning_and_silence_with_exact_neutral():
    from dataclasses import replace
    baseline = PreparedRoutes(Preset()).evaluate(complete_frame(), 0.)[0]
    for amount in [-1., 0., 1.]:
        preset = Preset(expression=amount)
        targets, _ = PreparedRoutes(preset).evaluate(complete_frame(), 0.)
        for old, new in zip(baseline, targets):
            assert replace(new, gain=old.gain) == old
            if amount < 0:
                assert 0 < new.gain < old.gain
            elif amount > 0:
                assert old.gain < new.gain <= preset.master
            else:
                assert new == old
        silent = complete_frame()
        for i in range(1, 7):
            silent.signals[f"zone.{i}.gain"].value = 0.
        assert all(t.gain == 0 for t in PreparedRoutes(preset).evaluate(silent, 0.)[0])
