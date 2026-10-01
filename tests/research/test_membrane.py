import numpy as np
import pytest
from harmonic_weaver.lab.research.membrane import Membrane, Settings, FieldWindow, RollingFieldWindow


def test_mode_frequency_boundaries_and_nodes():
    model = Membrane(Settings(modes_x=2, modes_y=2))
    assert model.omega[0]/(2*np.pi) == pytest.approx(20*np.sqrt(2))
    assert np.array_equal(model.shapes([0, 1, .5, .5], [.5, .5, 0, 1]), np.zeros((4, 4)))
    # The (2,1) mode has an interior nodal line x=1/2.
    assert abs(model.shapes([.5], [.3])[0, 2]) < 1e-15


def test_constant_force_matches_undamped_analytic_solution():
    model = Membrane(Settings(modes_x=1, modes_y=1, damping_per_s=0,
                              excitation_x=.5, excitation_y=.5, sample_rate=8000))
    result = model.render(np.ones(1000))
    t = np.arange(1, 1001)/8000
    expected = (1-np.cos(model.omega[0]*t))/model.omega[0]**2
    np.testing.assert_allclose(result['modal_displacement'][:, 0], expected, atol=1e-17)


def test_free_decay_partition_reset_and_boundary_excitation():
    cfg = Settings(sample_rate=8000)
    pcm = np.r_[np.ones(100), np.zeros(900)]
    whole = Membrane(cfg).render(pcm)
    split = Membrane(cfg)
    first, second = split.render(pcm[:317]), split.render(pcm[317:])
    np.testing.assert_array_equal(np.concatenate([first['modal_displacement'], second['modal_displacement']]), whole['modal_displacement'])
    assert np.max(np.diff(whole['modal_energy_proxy'][100:])) < 1e-18
    split.reset()
    assert split.sample_index == 0 and not split.state.any()
    boundary = Membrane(cfg.model_copy(update={'excitation_x': 0.}))
    assert not boundary.render(pcm)['modal_displacement'].any()


def test_invalid_input_does_not_advance_state():
    model = Membrane(Settings())
    for pcm in ([np.nan], [[1]], [np.inf]):
        with pytest.raises(ValueError): model.render(pcm)
    assert model.sample_index == 0 and not model.state.any()
    with pytest.raises(ValueError): Settings(width_m=.0001)
    with pytest.raises(ValueError): Settings(modes_x=True)


def test_field_rms_preserves_interference_and_exact_boundary():
    model = Membrane(Settings(modes_x=2, modes_y=1))
    x, y = [.25, 0, 1], [.5, .5, .5]
    shapes = model.shapes(x, y)
    # Opposite modal contributions cancel at this interior point.
    q = np.tile([1., -shapes[0, 0]/shapes[0, 1]], (20, 1))
    field = model.field(q, x, y)
    np.testing.assert_allclose(field, 0., atol=1e-15)
    np.testing.assert_allclose(model.field_rms(q, x, y), 0., atol=1e-15)
    q[:, 1] *= -1
    assert model.field_rms(q, x, y)[0] == pytest.approx(2*shapes[0, 0])
    assert not model.field(q, x, y)[:, 1:].any()


def test_field_contract_and_render_budget_precede_state_changes():
    model = Membrane(Settings(modes_x=16, modes_y=16))
    with pytest.raises(ValueError, match='budget'):
        model.render(np.zeros(32000))
    assert model.sample_index == 0 and not model.state.any()
    with pytest.raises(ValueError): model.field([[np.nan]*256], [.5], [.5])
    with pytest.raises(ValueError): model.field([[0]], [.5], [.5])
    with pytest.raises(ValueError): model.field_rms(np.zeros((0, 256)), [.5], [.5])
    with pytest.raises(ValueError): model.shapes([-.1], [.5])


def test_streaming_window_matches_direct_field_and_declares_clock():
    model = Membrane(Settings(sample_rate=8000))
    q = model.render(np.sin(np.arange(1000)*.07))['modal_displacement']
    window = FieldWindow(model, start_sample=200)
    window.append(q[:317], 200)
    window.append(q[317:], 517)
    x, y = [.1, .4, .8, 0], [.2, .6, .9, 1]
    result = window.report(x, y)
    np.testing.assert_allclose(result['rms'], model.field_rms(q, x, y), rtol=1e-12, atol=1e-18)
    assert result['sample_count'] == 1000
    assert result['stop_sample_exclusive'] == 1200
    assert result['first_output_time_s'] == 201/8000
    assert result['last_output_time_s'] == 1200/8000


def test_window_rejects_gaps_duplicates_nonfinite_without_mutation():
    model = Membrane(Settings(modes_x=1, modes_y=1))
    window = FieldWindow(model)
    with pytest.raises(ValueError): window.report([.5], [.5])
    window.append([[1.]], 0)
    before = window.cross_sum.copy()
    for q, start in (([[1.]], 0), ([[1.]], 2), ([[np.nan]], 1), ([[1e308]], 1)):
        with np.errstate(over='ignore', invalid='ignore'):
            with pytest.raises(ValueError): window.append(q, start)
        np.testing.assert_array_equal(window.cross_sum, before)
        assert window.stop_sample == 1
    with pytest.raises(ValueError): FieldWindow(model, True)


def test_rolling_window_matches_exact_past_support_and_partition():
    model = Membrane(Settings(modes_x=2, modes_y=2, sample_rate=8000))
    q = model.render(np.sin(np.arange(1000)*.1))['modal_displacement']
    rolling = RollingFieldWindow(model, 200)
    rolling.append(q[:100], 0)
    assert rolling.report([.3], [.4])['warmup']
    rolling.append(q[100:317], 100)
    report = rolling.report([.3], [.4])
    assert report['start_sample'] == 117 and report['stop_sample_exclusive'] == 317
    assert not report['warmup']
    np.testing.assert_allclose(report['rms'], model.field_rms(q[117:317], [.3], [.4]), atol=1e-18)
    rolling.append(q[317:], 317)
    whole = RollingFieldWindow(model, 200)
    whole.append(q, 0)
    np.testing.assert_array_equal(rolling.report([.3], [.4])['rms'], whole.report([.3], [.4])['rms'])
    assert rolling.history.shape == (200, 4)


def test_rolling_gap_reset_and_history_ownership():
    model = Membrane(Settings(modes_x=1, modes_y=1))
    rolling = RollingFieldWindow(model, 3)
    values = np.array([[1.], [2.]])
    rolling.append(values, 0)
    values.fill(100)
    np.testing.assert_array_equal(rolling.history[:, 0], [1., 2.])
    for start in (0, 3):
        with pytest.raises(ValueError): rolling.append([[3.]], start)
    assert rolling.stop_sample == 2
    rolling.reset(50)
    with pytest.raises(ValueError): rolling.report([.5], [.5])
    rolling.append([[4.]], 50)
    assert rolling.report([.5], [.5])['start_sample'] == 50
    with pytest.raises(ValueError): RollingFieldWindow(model, True)
    with pytest.raises(ValueError): RollingFieldWindow(model, 8_000_001)
