import numpy as np
import pytest
from harmonic_weaver.lab.research.membrane import Membrane, Settings


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
