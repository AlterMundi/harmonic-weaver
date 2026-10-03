import copy
import math
import numpy as np
import pytest
from harmonic_weaver.lab.research.activation_spectrum import Accumulator
from harmonic_weaver.lab.research.activation_bank import Settings, probe
from harmonic_weaver.lab.research.activation_artifacts import validate_report
from research.test_activation_bank import config


def test_analytic_dc_and_sine_coefficients_on_after_step_clock():
    kernel = Accumulator({"frequencies_hz": [0, 10]}, 1000, 1000, 1000)
    time = (np.arange(1000) + 1) / 1000
    output = 3 + 2 * np.sin(2 * np.pi * 10 * time)
    kernel.add(0, output[:317])
    kernel.add(317, output[317:])
    result = kernel.finish([0, 100, 200, 300])
    dc, tone = result["rows"]
    assert dc["event_real"] == 0.004 and dc["event_imag"] == 0
    assert dc["output_real"] == pytest.approx(3)
    assert tone["output_real"] == pytest.approx(0, abs=1e-14)
    assert tone["output_imag"] == pytest.approx(-1)
    assert tone["output_coefficient_squared"] == pytest.approx(1)


def test_optional_probe_changes_no_audio_metrics_and_has_declared_support():
    base = probe(config())
    for window, count in [("excitation", 800), ("tail", 800), ("complete", 1600)]:
        settings = config(
            spectral_probe={"frequencies_hz": [0, 40.4, 80.8], "window": window}
        )
        report = probe(settings)
        validate_report(report, Settings.model_validate(settings))
        assert report == probe(settings)
        for name, condition in report["conditions"].items():
            assert condition["metrics"] == base["conditions"][name]["metrics"]
            assert condition["trace"] == base["conditions"][name]["trace"]
            spectrum = condition["spectral_probe"]
            assert spectrum["sample_count"] == count
            assert spectrum["rows"][0]["event_real"] == (
                0 if window == "tail" else 8 / count
            )
        partition = probe({**settings, "block_size": 317})
        for name in report["conditions"]:
            for a, b in zip(
                report["conditions"][name]["spectral_probe"]["rows"],
                partition["conditions"][name]["spectral_probe"]["rows"],
            ):
                for key in ("output_real", "output_imag", "output_coefficient_squared"):
                    assert a[key] == pytest.approx(b[key], rel=1e-12, abs=1e-14)


def test_probe_propagates_across_phase_medium_and_seed_controls():
    settings = config(
        spectral_probe={"frequencies_hz": [0, 40.4]},
        phase_controls=[[0, 1, 2, 3, 4, 5]],
        medium_controls=[{"sample_rate": 8000}],
        replicate_seeds=[18],
    )
    report = probe(settings)
    validate_report(report, Settings.model_validate(settings))
    base = report["conditions"]["phi"]["spectral_probe"]
    phase = report["phase_controls"][0]["report"]["conditions"]["phi"]["spectral_probe"]
    assert [r["event_coefficient_squared"] for r in phase["rows"]] == [
        r["event_coefficient_squared"] for r in base["rows"]
    ]
    assert (
        phase["rows"][1]["output_coefficient_squared"]
        != base["rows"][1]["output_coefficient_squared"]
    )
    assert report["replicates"][0]["report"]["phase_controls"][0]["report"][
        "medium_controls"
    ][0]["conditions"]["random"]["spectral_probe"]["rows"]


@pytest.mark.parametrize(
    "mutation", ["window", "frequency", "input", "power", "missing"]
)
def test_probe_contract_rejects_structural_and_analytic_corruption(mutation):
    settings = config(spectral_probe={"frequencies_hz": [0, 40.4]})
    report = probe(settings)
    bad = copy.deepcopy(report)
    spectral = bad["conditions"]["phi"]["spectral_probe"]
    if mutation == "window":
        spectral["start_sample"] = 1
    elif mutation == "frequency":
        spectral["rows"][0]["frequency_hz"] = 1
    elif mutation == "input":
        spectral["rows"][0]["event_real"] += 1
    elif mutation == "power":
        spectral["rows"][0]["output_coefficient_squared"] += 1
    else:
        del bad["conditions"]["phi"]["spectral_probe"]
    with pytest.raises(ValueError):
        validate_report(bad, Settings.model_validate(settings))


def test_invalid_probe_and_budget_are_explicit_legacy_omits_field():
    for frequencies in [[], [2, 1], [0, 0], [-1], [4000], [math.nan]]:
        with pytest.raises(ValueError):
            Settings.model_validate(
                config(spectral_probe={"frequencies_hz": frequencies})
            )
    with pytest.raises(ValueError, match="nonempty"):
        Settings.model_validate(
            config(tail_s=0, spectral_probe={"frequencies_hz": [1], "window": "tail"})
        )
    with pytest.raises(ValueError, match="frequency-sample"):
        Settings.model_validate(
            {
                "spectral_probe": {"frequencies_hz": list(range(32))},
                "phase_controls": [[0] * 6] * 4,
                "replicate_seeds": [18],
            }
        )
    assert "spectral_probe" not in Settings.model_validate(config()).model_dump()


def test_streaming_probe_rejects_gaps_duplicates_and_nonfinite_output():
    acc = Accumulator({"frequencies_hz": [0]}, 1000, 10, 10)
    acc.add(0, np.ones(5))
    for start, values in [(0, np.ones(5)), (6, np.ones(4)), (5, np.array([math.nan]))]:
        with pytest.raises(ValueError, match="contiguous finite"):
            acc.add(start, values)
    with pytest.raises(ValueError, match="incomplete"):
        acc.finish([])
    acc.add(5, np.ones(5))
    assert acc.finish([])["rows"][0]["output_real"] == 1
