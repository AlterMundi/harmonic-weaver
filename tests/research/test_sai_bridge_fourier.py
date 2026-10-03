import hashlib
import importlib
from pathlib import Path

import numpy as np
import pytest

from research.laboratory.sai_bridge.adapter import read_models
from research.laboratory.sai_bridge.fourier import (
    FourierConfig, common_three, frames_from_channels, phase_surrogate,
    scenario, spectral_checks,
)
from research.laboratory.sai_bridge.run import source_hashes


@pytest.mark.parametrize("samples", [127, 128])
@pytest.mark.parametrize("shared", [True, False])
def test_fourier_preserves_individual_spectrum_dc_and_nyquist(samples, shared):
    x = np.random.default_rng(2).normal(size=(samples, 5)) + np.arange(5)
    y = phase_surrogate(x, seed=7, shared=shared)
    assert y.shape == x.shape and np.isfinite(y).all()
    a, b = np.fft.rfft(x, axis=0), np.fft.rfft(y, axis=0)
    np.testing.assert_allclose(abs(a), abs(b), atol=1e-12)
    np.testing.assert_allclose(a[0], b[0], atol=1e-12)
    if samples % 2 == 0:
        np.testing.assert_allclose(a[-1], b[-1], atol=1e-12)
    np.testing.assert_allclose(np.var(x, axis=0), np.var(y, axis=0), atol=1e-12)
    for lag in (0, 1, 17):
        np.testing.assert_allclose(np.sum(x*np.roll(x, lag, axis=0), axis=0),
                                   np.sum(y*np.roll(y, lag, axis=0), axis=0), atol=1e-10)
    np.testing.assert_array_equal(y, phase_surrogate(x, seed=7, shared=shared))


def test_shared_preserves_complex_cross_spectra_and_circular_lag_covariance():
    x, _ = scenario("coupled_multitone")
    y = phase_surrogate(x, seed=7, shared=True)
    checks = spectral_checks(x, y)
    assert checks["cross_spectrum_max_relative_change"] < 1e-12
    for lag in (0, 1, 17, 200):
        np.testing.assert_allclose(x.T @ np.roll(x, lag, axis=0),
                                   y.T @ np.roll(y, lag, axis=0), atol=1e-12)
    # Shared phases are not a general preservation of higher-order structure.
    assert abs(np.mean(x[:, 0]**3)-np.mean(y[:, 0]**3)) > 1e-7


@pytest.mark.parametrize("seed", [7, 19, 41])
def test_independent_preserves_power_but_breaks_this_coupled_cross_spectrum(seed):
    x, _ = scenario("coupled_multitone")
    y = phase_surrogate(x, seed=seed, shared=False)
    checks = spectral_checks(x, y)
    assert checks["power_max_relative_error"] < 1e-12
    assert checks["cross_spectrum_max_relative_change"] > .1


def test_single_channel_and_static_are_nondiscriminating_controls():
    for name in ("single_channel", "static"):
        x, channel_map = scenario(name, FourierConfig(samples=120))
        shared = phase_surrogate(x, seed=7, shared=True)
        independent = phase_surrogate(x, seed=7, shared=False)
        np.testing.assert_array_equal(shared, independent)
        frames = frames_from_channels(shared, channel_map)
        records = read_models(frames, algorithms=("relational",))["relational"]
        summary = common_three({"original": records, "shared": records,
                                "independent": records}, "zone.6.I")
        if name == "static":
            assert summary["common_observed"] == 0
            assert summary["conditions"]["original"]["common_mean"] is None


def test_common_support_is_three_way_and_reports_missing_not_zero():
    def row(t, state, value):
        return {"source_id": "s", "stream_id": "e", "person_id": "p", "source_time_s": t,
                "signals": {"I": {"state": state, "value": value, "unit": "1"}}}
    records = {"original": [row(0, "observed", 2), row(1, "observed", 100)],
               "shared": [row(0, "observed", 3), row(1, "missing", None)],
               "independent": [row(0, "observed", 4), row(1, "observed", -100)]}
    result = common_three(records, "I")
    assert result["common_observed"] == 1
    assert result["conditions"]["original"]["common_mean"] == 2
    assert result["common_mae_from_original"]["independent"] == 2


def test_existing_descriptors_discriminate_coupling_but_are_not_all_invariants():
    x, channel_map = scenario("coupled_multitone")
    conditions = {"original": x, "shared": phase_surrogate(x, seed=7, shared=True),
                  "independent": phase_surrogate(x, seed=7, shared=False)}
    records = {name: read_models(frames_from_channels(values, channel_map),
               algorithms=("relational",))["relational"] for name, values in conditions.items()}
    collective = common_three(records, "collective.residual")
    assert collective["common_observed"] > 400
    assert collective["conditions"]["original"]["common_mean"] < .02
    assert collective["conditions"]["shared"]["common_mean"] < .02
    assert collective["conditions"]["independent"]["common_mean"] > .2
    local = common_three(records, "zone.6.I")
    assert local["common_observed"] > 200
    # Second-order preservation does not preserve finite-window nonlinear I.
    assert local["common_mae_from_original"]["shared"] > .2


def test_effective_provenance_reads_imported_module_not_bridge_checkout(monkeypatch, tmp_path):
    module = importlib.import_module("harmonic_weaver.lab.models")
    alternate = tmp_path / "models.py"
    alternate.write_text("# alternate imported source\n")
    monkeypatch.setattr(module, "__file__", str(alternate))
    entry = source_hashes()[module.__name__]
    assert entry["path"] == str(alternate.resolve())
    assert entry["sha256"] == hashlib.sha256(alternate.read_bytes()).hexdigest()
    for name, entry in source_hashes().items():
        assert Path(entry["path"]) == Path(importlib.import_module(name).__file__).resolve()


@pytest.mark.parametrize("bad", [np.zeros(4), np.zeros((3, 2)), [[1, float("nan")]]*4])
def test_reject_invalid_or_missing_samples(bad):
    with pytest.raises(ValueError):
        phase_surrogate(bad, seed=7, shared=True)


def test_offline_surrogate_is_not_prefix_causal():
    x, _ = scenario("coupled_multitone")
    # The finite Fourier basis itself changes with record duration. Availability
    # clocks on emitted fixtures do not make this preprocessing a live operation.
    full = phase_surrogate(x, seed=7, shared=True)
    prefix = phase_surrogate(x[:240], seed=7, shared=True)
    assert np.max(abs(full[:240]-prefix)) > .001
    changed_future = x.copy()
    changed_future[240:] *= 2
    altered = phase_surrogate(changed_future, seed=7, shared=True)
    assert np.max(abs(full[:240]-altered[:240])) > .001
