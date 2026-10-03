import json

import pytest

from harmonic_weaver.lab.cache import atomic_json, sha256_file
from harmonic_weaver.lab.research.membrane_readout_run import run, verify
from test_membrane_readout import fixture


def test_repeat_explicit_recompute_environment_and_no_overwrite(tmp_path):
    for i in range(2):
        folder = tmp_path / str(i)
        run(fixture(), folder)
        assert verify(folder)["read_verification"] == "integrity_only"
        assert (
            verify(folder, recompute=True)["read_verification"]
            == "numerically_recomputed"
        )
    assert (tmp_path / "0/result.json").read_bytes() == (
        tmp_path / "1/result.json"
    ).read_bytes()
    with pytest.raises(FileExistsError):
        run(fixture(), tmp_path / "0")
    manifest_path = tmp_path / "0/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["environment"]["numpy"] = "historical"
    manifest["code_hashes"] = {"historical": "a" * 64}
    atomic_json(manifest_path, manifest)
    before = {p.name: p.read_bytes() for p in (tmp_path / "0").iterdir()}
    result = verify(tmp_path / "0", recompute=True)
    assert not result["implementation_matches"] and not result["environment_matches"]
    assert before == {p.name: p.read_bytes() for p in (tmp_path / "0").iterdir()}


def test_corruption_and_rehashed_numerical_changes(tmp_path):
    run(fixture(), tmp_path / "run")
    folder = tmp_path / "run"
    path = folder / "result.json"
    result = json.loads(path.read_text())
    result["mean_squared_error"]["rms_full"][0] += 0.1
    atomic_json(path, result)
    with pytest.raises(ValueError, match="hash"):
        verify(folder)
    manifest = json.loads((folder / "manifest.json").read_text())
    manifest["output"]["sha256"] = sha256_file(path)
    atomic_json(folder / "manifest.json", manifest)
    assert verify(folder)["read_verification"] == "integrity_only"
    with pytest.raises(ValueError, match="recomputation"):
        verify(folder, recompute=True)


def test_invalid_split_creates_no_folder(tmp_path):
    data = fixture()
    data["cases"][-1]["recording_id"] = data["cases"][0]["recording_id"]
    with pytest.raises(ValueError):
        run(data, tmp_path / "bad")
    assert not (tmp_path / "bad").exists()


def test_rehashed_reserved_targets_are_not_accepted_as_frozen_labels(tmp_path):
    run(fixture(), tmp_path / "run")
    folder = tmp_path / "run"
    path = folder / "result.json"
    result = json.loads(path.read_text())
    result["rows"][0]["actual"][0] += 1
    atomic_json(path, result)
    manifest = json.loads((folder / "manifest.json").read_text())
    manifest["output"]["sha256"] = sha256_file(path)
    atomic_json(folder / "manifest.json", manifest)
    with pytest.raises(ValueError, match="target"):
        verify(folder)
