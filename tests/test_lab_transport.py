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
