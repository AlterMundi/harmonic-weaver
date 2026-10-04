"""Persist/recompute frozen R07 attribute readouts, without rerendering figures."""

import argparse
import json
import platform
from pathlib import Path

import numpy as np

from ..cache import atomic_json, sha256_file
from .membrane_controls_run import equivalent
from .membrane_readout import Dataset, calculate


def code_hashes():
    return {
        name: sha256_file(Path(__file__).with_name(name))
        for name in (
            "membrane_readout.py",
            "membrane_readout_run.py",
            "membrane_controls_run.py",
        )
    }


def environment():
    return {"python": platform.python_version(), "numpy": np.__version__}


def run(dataset, folder):
    dataset = Dataset.model_validate(dataset)
    result = calculate(dataset)
    folder = Path(folder)
    folder.mkdir(mode=0o700, parents=True, exist_ok=False)
    atomic_json(folder / "dataset.json", dataset.model_dump())
    atomic_json(folder / "result.json", result)
    manifest = {
        "schema_version": 1,
        "line": "R07",
        "kind": "reserved_attribute_readout",
        "status": "complete",
        "input_hashes": {"dataset.json": sha256_file(folder / "dataset.json")},
        "output": {
            "file": "result.json",
            "sha256": sha256_file(folder / "result.json"),
        },
        "code_hashes": code_hashes(),
        "environment": environment(),
        "limits": result["limits"],
    }
    atomic_json(folder / "manifest.json", manifest)
    return manifest


def verify(folder, *, recompute=False):
    folder = Path(folder)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("Regular readout directory required")
    names = ("dataset.json", "result.json", "manifest.json")
    for name in names:
        path = folder / name
        if (
            path.is_symlink()
            or not path.is_file()
            or path.stat().st_size > 16 * 1024 * 1024
        ):
            raise ValueError("Bounded regular readout artifacts required")
    hashes = {name: sha256_file(folder / name) for name in names}
    manifest = json.loads((folder / "manifest.json").read_text())
    if (
        manifest.get("schema_version"),
        manifest.get("line"),
        manifest.get("kind"),
        manifest.get("status"),
    ) != (1, "R07", "reserved_attribute_readout", "complete"):
        raise ValueError("Complete readout manifest required")
    if manifest.get("input_hashes") != {
        "dataset.json": hashes["dataset.json"]
    } or manifest.get("output") != {
        "file": "result.json",
        "sha256": hashes["result.json"],
    }:
        raise ValueError("Readout inventory/hash mismatch")
    dataset = Dataset.model_validate_json((folder / "dataset.json").read_text())
    result = json.loads((folder / "result.json").read_text())
    from ..contracts import Contract
    from ..evaluation.runner import digest

    Contract.finite_tree(result)
    if (
        result.get("schema_version"),
        result.get("line"),
        result.get("kind"),
        result.get("dataset_sha256"),
    ) != (1, "R07", "reserved_attribute_readout", digest(dataset.model_dump())):
        raise ValueError("Readout frozen dataset binding mismatch")
    training = [c for c in dataset.cases if c.role == "train"]
    reserved = [c for c in dataset.cases if c.role == "test"]
    if (
        result.get("attribute_ids") != dataset.attribute_ids
        or result.get("attribute_units") != dataset.attribute_units
        or result.get("training_case_ids") != [c.id for c in training]
        or result.get("reserved_case_ids") != [c.id for c in reserved]
        or type(result.get("common_count")) is not int
        or result["common_count"] != len(reserved)
    ):
        raise ValueError("Readout attribute/case support differs from frozen dataset")
    methods = {
        "training_mean",
        "rms_full",
        "rms_shape",
        "rms_magnitude",
        "rms_full_training_shuffle",
        "rms_shape_training_shuffle",
        "rms_magnitude_training_shuffle",
    }
    rows = result.get("rows")
    if not isinstance(rows, list) or len(rows) != len(reserved):
        raise ValueError("Readout reserved row inventory differs")
    for row, case in zip(rows, reserved):
        if (
            not isinstance(row, dict)
            or row.get("case_id") != case.id
            or row.get("actual") != case.targets
        ):
            raise ValueError("Readout target differs from frozen reserved case")
        for key in ("predictions", "squared_error"):
            values = row.get(key)
            if (
                not isinstance(values, dict)
                or set(values) != methods
                or any(
                    not isinstance(v, list)
                    or len(v) != len(dataset.attribute_ids)
                    or any(
                        type(n) not in (int, float)
                        or (key == "squared_error" and n < 0)
                        for n in v
                    )
                    for v in values.values()
                )
            ):
                raise ValueError("Readout method/attribute inventory differs")
    metrics = result.get("mean_squared_error")
    if (
        not isinstance(metrics, dict)
        or set(metrics) != methods
        or any(
            not isinstance(v, list)
            or len(v) != len(dataset.attribute_ids)
            or any(type(n) not in (int, float) or n < 0 for n in v)
            for v in metrics.values()
        )
    ):
        raise ValueError("Readout metric inventory differs")
    if recompute and not equivalent(result, calculate(dataset)):
        raise ValueError("Readout numerical recomputation differs from artifact")
    if any(
        (folder / name).is_symlink() or sha256_file(folder / name) != value
        for name, value in hashes.items()
    ):
        raise ValueError("Readout artifacts changed during verification")
    return {
        **manifest,
        "read_verification": "numerically_recomputed"
        if recompute
        else "integrity_only",
        "implementation_matches": manifest.get("code_hashes") == code_hashes(),
        "environment_matches": manifest.get("environment") == environment(),
        "numerical_tolerance": {"relative": 1e-12, "absolute": 1e-15}
        if recompute
        else None,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(json.loads(args.dataset.read_text()), args.output)
