import copy

import numpy as np
import pytest

from harmonic_weaver.lab.research.membrane_readout import Dataset, calculate, snapshot


def fixture():
    cases = []
    for i, amplitude in enumerate([1.0, 2.0, 3.0, 4.0, 1.5, 3.5]):
        cases.append(
            {
                "id": f"case-{i}",
                "role": "train" if i < 4 else "test",
                "recording_id": f"recording-{i}",
                "subject_group": f"group-{i}",
                "targets": [amplitude],
                "pcm_sha256": f"{i + 1:064x}",
                "projection_sha256": f"{i + 10:064x}",
                "start_sample": 0,
                "stop_sample_exclusive": 800,
                "sample_rate": 8000,
                "rms": (amplitude * np.array([1.0, 2.0, 3.0, 4.0])).tolist(),
            }
        )
    return {
        "provider": "synthetic",
        "reservation": "take",
        "attribute_ids": ["amplitude"],
        "attribute_units": ["dimensionless"],
        "grid_x": 2,
        "grid_y": 2,
        "medium_sha256": "a" * 64,
        "settings": {"ridge": 0.001},
        "cases": cases,
    }


def test_repeat_common_support_and_magnitude_confound():
    data = fixture()
    result = calculate(data)
    assert result == calculate(data)
    assert result["common_count"] == 2
    assert result["reserved_case_ids"] == ["case-4", "case-5"]
    assert len(result["rows"][0]["predictions"]) == 7
    errors = result["mean_squared_error"]
    assert errors["rms_full"][0] < 1e-5
    assert errors["rms_magnitude"][0] < 1e-5
    # Shape carries no amplitude here, including floating-point roundoff.
    assert errors["rms_shape"][0] == pytest.approx(errors["training_mean"][0])
    assert errors["rms_full_training_shuffle"][0] > errors["rms_full"][0]


def test_test_targets_and_test_features_never_change_fitted_models():
    data = fixture()
    first = calculate(data)
    for case in data["cases"]:
        if case["role"] == "test":
            case["targets"] = [100.0]
            case["rms"] = [100.0, 0.0, 100.0, 0.0]
    second = calculate(data)
    assert first["models"] == second["models"]
    assert first["training_shuffle_case_ids"] == second["training_shuffle_case_ids"]
    assert first["rows"] != second["rows"]


def test_shape_recovers_spatial_attribute_without_magnitude_difference():
    data = fixture()
    for case, theta in zip(data["cases"], [0.1, 0.3, 0.5, 0.7, 0.2, 0.6]):
        case["targets"] = [theta]
        case["rms"] = [float(np.cos(theta)), float(np.sin(theta)), 0.0, 0.0]
    result = calculate(data)
    errors = result["mean_squared_error"]
    assert errors["rms_shape"][0] < errors["training_mean"][0] / 100
    assert errors["rms_magnitude"][0] == pytest.approx(errors["training_mean"][0])


def test_zero_fields_and_multiattribute_units():
    data = fixture()
    data["attribute_ids"] += ["frequency"]
    data["attribute_units"] += ["Hz"]
    for case in data["cases"]:
        case["targets"] += [40.4]
        case["rms"] = [0.0] * 4
    result = calculate(data)
    for row in result["rows"]:
        assert row["predictions"]["rms_shape"] == [2.5, 40.4]
    assert result["attribute_units"] == ["dimensionless", "Hz"]


@pytest.mark.parametrize(
    "mutation",
    [
        "pcm",
        "recording",
        "projection",
        "subject",
        "dimension",
        "negative",
        "bool",
        "nonfinite",
    ],
)
def test_invalid_inventory_and_split_rejected(mutation):
    data = fixture()
    train, test = data["cases"][0], data["cases"][-1]
    if mutation == "pcm":
        test["pcm_sha256"] = train["pcm_sha256"]
    elif mutation == "recording":
        test["recording_id"] = train["recording_id"]
    elif mutation == "projection":
        test["projection_sha256"] = train["projection_sha256"]
    elif mutation == "subject":
        data["reservation"] = "subject"
        test["subject_group"] = train["subject_group"]
    elif mutation == "dimension":
        test["targets"] += [0.0]
    elif mutation == "negative":
        test["rms"][0] = -1.0
    elif mutation == "bool":
        test["rms"][0] = True
    else:
        test["targets"][0] = float("nan")
    with pytest.raises(ValueError):
        calculate(data)


def test_within_take_embargo_and_same_pcm_clock():
    data = fixture()
    data["reservation"] = "within_take"
    test = data["cases"][-1]
    test["pcm_sha256"] = data["cases"][0]["pcm_sha256"]
    test["recording_id"] = data["cases"][0]["recording_id"]
    test["stop_sample_exclusive"] = 801
    with pytest.raises(ValueError, match="embargo"):
        Dataset.model_validate(data)
    test["start_sample"] = 4800
    test["stop_sample_exclusive"] = 5600
    Dataset.model_validate(data)
    test["sample_rate"] = 16000
    with pytest.raises(ValueError, match="clocks"):
        Dataset.model_validate(data)


def test_different_renders_need_source_origins_for_within_take_embargo():
    data = fixture()
    data["reservation"] = "within_take"
    train, test = data["cases"][0], data["cases"][-1]
    test["recording_id"] = train["recording_id"]
    test["start_sample"] = 4800
    test["stop_sample_exclusive"] = 5600
    with pytest.raises(ValueError, match="origins"):
        Dataset.model_validate(data)
    train["source_origin_s"] = 10.0
    test["source_origin_s"] = 0.0
    with pytest.raises(ValueError, match="embargo"):
        Dataset.model_validate(data)
    test["source_origin_s"] = 11.0
    Dataset.model_validate(data)


def test_snapshot_verified_sound_figures_without_target_injection(tmp_path):
    from harmonic_weaver.lab.research.membrane_run import run, verify
    from test_resonator_artifacts import fixture as source_fixture

    source = tmp_path / "source"
    source_fixture(source)
    folders = {}
    selections = []
    for i in range(6):
        ident = f"{i + 1:032x}"
        folder = tmp_path / ident
        run(
            source,
            {
                "membrane": {"sample_rate": 8000},
                "grid_x": 3,
                "grid_y": 3,
                "start_sample": i * 200 if i < 4 else 1600 + (i - 4) * 400,
                "stop_sample_exclusive": (i + 1) * 200
                if i < 4
                else 2000 + (i - 4) * 400,
            },
            folder,
        )
        folders[ident] = folder
        selections.append(
            {
                "id": f"case-{i}",
                "projection_run_id": ident,
                "role": "train" if i < 4 else "test",
                "recording_id": "same-recording",
                "subject_group": "synthetic",
                "targets": [float(i)],
            }
        )

    class Service:
        def artifact(self, ident, name):
            verify(folders[ident])
            return folders[ident] / name

    request = {
        "reservation": "within_take",
        "attribute_ids": ["declared"],
        "attribute_units": ["dimensionless"],
        "settings": {"embargo_s": 0.1},
        "cases": selections,
    }
    before = snapshot(request, Service())
    changed = copy.deepcopy(request)
    for case in changed["cases"]:
        case["targets"] = [99.0]
    after = snapshot(changed, Service())
    assert before.provider == "r07_snapshot"
    assert [c.rms for c in before.cases] == [c.rms for c in after.cases]
    assert [c.projection_sha256 for c in before.cases] == [
        c.projection_sha256 for c in after.cases
    ]
    assert all(c.rms[0] == 0 for c in before.cases)
    # Rewritten source bytes are not accepted as a verified snapshot.
    report = folders[selections[-1]["projection_run_id"]] / "result.json"
    report.write_text("changed")
    with pytest.raises(ValueError):
        snapshot(request, Service())
