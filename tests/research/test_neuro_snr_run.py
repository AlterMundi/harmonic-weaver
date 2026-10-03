import json
import pytest
from harmonic_weaver.lab.cache import atomic_json, sha256_file
from harmonic_weaver.lab.research import neuro_snr_run as bank
from research.test_neuro_snr import config


def test_save_repeat_and_restart_preserve_frozen_components(tmp_path):
    service = bank.SNRService(tmp_path)
    request = config()
    request["missing_indices"] = [3]
    saved = service.start(request)
    assert saved["read_verification"] == "recomputed"
    assert saved["implementation_matches"] and saved["environment_matches"]
    result = json.loads(service.artifact(saved["id"], "result.json").read_text())
    assert result["samples"][3]["signal"] is None
    assert 3 not in result["used_indices"]
    assert service.start(request)["id"] == saved["id"]
    assert len(bank.SNRService(tmp_path).list()) == 1
    assert bank.SNRService(tmp_path).read(saved["id"]) == saved


def test_provenance_difference_does_not_block_numerical_recomputation(tmp_path):
    bank.run(config(), tmp_path / "run")
    path = tmp_path / "run/manifest.json"
    manifest = json.loads(path.read_text())
    manifest["environment"] = {"python": "different-environment"}
    manifest["code_hashes"] = {"reference": "a" * 64}
    atomic_json(path, manifest)
    read = bank.verify(tmp_path / "run")
    assert read["read_verification"] == "recomputed"
    assert not read["implementation_matches"] and not read["environment_matches"]


def test_rehashed_numerical_corruption_rejected_but_integrity_only_distinct(tmp_path):
    bank.run(config(), tmp_path / "run")
    result_path = tmp_path / "run/result.json"
    result = json.loads(result_path.read_text())
    result["metrics"]["snr_db"] += 1
    atomic_json(result_path, result)
    path = tmp_path / "run/manifest.json"
    manifest = json.loads(path.read_text())
    manifest["hashes"]["result.json"] = sha256_file(result_path)
    atomic_json(path, manifest)
    assert (
        bank.verify(tmp_path / "run", recompute=False)["read_verification"]
        == "integrity_only"
    )
    with pytest.raises(ValueError, match="numerical"):
        bank.verify(tmp_path / "run")


def test_interrupted_staging_allows_retry_without_partial_record(tmp_path, monkeypatch):
    service = bank.SNRService(tmp_path)
    original = bank.run

    def fail(request, folder):
        folder.mkdir()
        atomic_json(folder / "request.json", request.model_dump())
        raise OSError("interrupted")

    monkeypatch.setattr(bank, "run", fail)
    with pytest.raises(OSError):
        service.start(config())
    assert service.list() == []
    monkeypatch.setattr(bank, "run", original)
    assert service.start(config())["read_verification"] == "recomputed"
    assert len(service.list()) == 1


def test_support_and_structure_are_exact_float_tolerance_explicit():
    assert bank.numerically_equivalent(
        {"v": 1.0, "indices": [1, 2]}, {"v": 1.0 + 1e-13, "indices": [1, 2]}
    )
    assert not bank.numerically_equivalent(
        {"v": 1.0, "indices": [1, 2]}, {"v": 1.0, "indices": [1, 3]}
    )
    assert not bank.numerically_equivalent(True, 1)
