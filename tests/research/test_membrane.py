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
