import copy
import math
import numpy as np
import pytest
from harmonic_weaver.lab.research.activation_bank import Settings, probe, run
from harmonic_weaver.lab.research.activation_artifacts import validate_report, verify
from harmonic_weaver.lab.research.resonators import Resonators
from harmonic_weaver.lab.cache import atomic_json, sha256_file
from research.test_activation_bank import config


def test_zero_phase_reproduces_base_and_rotation_preserves_isolated_norm():
    phases = [i * math.pi / 3 for i in range(6)]
    settings = config(phase_controls=[[0.0] * 6, phases])
    report = probe(settings)
    validate_report(report, Settings.model_validate(settings))
    assert report == probe(settings)
    assert report["phase_controls"][0]["report"]["conditions"] == report["conditions"]
    rotated = report["phase_controls"][1]["report"]
    assert rotated["excitation_phases_rad"] == phases
    assert any(
        rotated["conditions"][name]["metrics"]["rms"]
        != report["conditions"][name]["metrics"]["rms"]
        for name in report["conditions"]
    )
    for name, condition in rotated["conditions"].items():
        base = report["conditions"][name]
        assert condition["event_samples"] == base["event_samples"]
        assert condition["input_squared_norm"] == base["input_squared_norm"]
        assert [r["sample_index"] for r in condition["trace"]] == [
            r["sample_index"] for r in base["trace"]
        ]
        for metric in ["state_norm_time_integral", "final_state_norm_squared"]:
            assert condition["metrics"][metric] == pytest.approx(
                base["metrics"][metric], rel=1e-12, abs=1e-12
            )
    partitioned = probe({**settings, "block_size": 317})
    assert (
        partitioned["phase_controls"][1]["report"]["conditions"]["phi"]["trace"]
        == rotated["conditions"]["phi"]["trace"]
    )


def test_phase_groups_include_medium_controls_seeds_and_descriptive_summary():
    settings = config(
        phase_controls=[[0.0] * 6, [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]],
        medium_controls=[
            {"sample_rate": 8000, "topology": "ring", "coupling_per_s": 2}
        ],
        replicate_seeds=[18],
        interval_shuffle=True,
    )
    report = probe(settings)
    validate_report(report, Settings.model_validate(settings))
    assert len(report["phase_controls"][1]["report"]["medium_controls"]) == 1
    assert (
        report["replicates"][0]["report"]["phase_controls"][1]["phases_rad"]
        == settings["phase_controls"][1]
    )
    assert (
        report["phase_replicate_summary"]["1"]["control_0"]["random"]["rms"]["count"]
        == 2
    )
    bad = copy.deepcopy(report)
    bad["phase_replicate_summary"]["1"]["base"]["random"]["rms"]["mean"] += 1
    with pytest.raises(ValueError, match="summary"):
        validate_report(bad, Settings.model_validate(settings))


@pytest.mark.parametrize("mutation", ["phase", "inventory", "dose", "delta"])
def test_verifier_rejects_changed_phase_control_even_when_rehashed(tmp_path, mutation):
    settings = config(phase_controls=[[0.0, 1.0, 2.0, 3.0, 4.0, 5.0]])
    run(settings, tmp_path / "run")
    verify(tmp_path / "run")
    import json

    path = tmp_path / "run/result.json"
    report = json.loads(path.read_text())
    control = report["phase_controls"][0]
    if mutation == "phase":
        control["report"]["excitation_phases_rad"][0] = 0.5
    elif mutation == "inventory":
        report["phase_controls"] = []
    elif mutation == "dose":
        control["report"]["conditions"]["phi"]["input_squared_norm"] += 1
    else:
        control["metric_difference_vs_base"]["phi"]["rms"] += 1
    atomic_json(path, report)
    manifest_path = tmp_path / "run/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["output_sha256"] = sha256_file(path)
    atomic_json(manifest_path, manifest)
    with pytest.raises(ValueError):
        verify(tmp_path / "run")


def test_invalid_vector_budget_and_legacy_serialization():
    for phases in [[], [[0] * 5], [[math.nan] * 6], [[1001] * 6]]:
        with pytest.raises(ValueError):
            Settings.model_validate(config(phase_controls=phases))
    with pytest.raises(ValueError, match="aggregate"):
        Settings.model_validate(
            {
                "phase_controls": [[0] * 6] * 4,
                "trace_stride": 10,
                "replicate_seeds": [18],
            }
        )
    assert "phase_controls" not in Settings.model_validate(config()).model_dump()
    kernel = Resonators({"sample_rate": 8000})
    for phases in [[0] * 5, [math.inf] * 6]:
        with pytest.raises(ValueError):
            kernel.render(np.zeros((2, 6)), excitation_phases_rad=phases)
