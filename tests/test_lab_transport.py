import pytest

from harmonic_weaver.lab.transport import Transport


def test_loop_seek_and_pause_have_explicit_discontinuity_epochs():
    now = [0.]
    t = Transport(clock=lambda: now[0])
    t.reset(duration_s=2., playing=True)
    epoch = t.epoch
    now[0] = .7
    assert t.position() == pytest.approx(.7) and t.epoch == epoch
    now[0] = 2.1
    assert t.position() == pytest.approx(.1) and t.epoch == epoch + 1
    assert t.position() == pytest.approx(.1) and t.epoch == epoch + 1
    t.seek(1.3)
    assert t.epoch == epoch + 2
    t.play(False)
    now[0] += 50
    assert t.position() == pytest.approx(1.3)
    t.play(True)
    now[0] += .1
    assert t.position() == pytest.approx(1.4)


def test_non_loop_end_pauses_once_and_restart_begins_at_zero():
    now = [0.]
    t = Transport(clock=lambda: now[0])
    t.reset(duration_s=1., playing=True)
    t.loop = False
    now[0] = 2.
    assert t.position() == 1. and not t.playing
    epoch = t.epoch
    assert t.position() == 1. and t.epoch == epoch
    t.play(True)
    assert t.position() == 0.
    with pytest.raises(ValueError):
        t.seek(float("nan"))


def test_fixed_prefix_loops_before_duration_is_known_and_clears_on_source_reset():
    now = [0.]
    t = Transport(clock=lambda: now[0])
    t.loop_end_s = 2.
    t.play(True)
    epoch = t.epoch
    now[0] = 4.1
    assert t.position() == pytest.approx(.1)
    assert t.epoch == epoch + 2
    t.duration_s = 60.  # completing tracking does not silently expand the chosen loop
    now[0] = 6.2
    assert t.position() == pytest.approx(.2)
    t.play(False)
    now[0] = 100.
    assert t.position() == pytest.approx(.2)
    t.seek(3.)
    assert t.position() == 2.
    t.reset(duration_s=10.)
    assert t.loop_end_s is None and t.boundary() == 10.
