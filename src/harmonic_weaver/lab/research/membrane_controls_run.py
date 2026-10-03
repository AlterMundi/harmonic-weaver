"""Reproducible finite R07 transient control bank, with integrity reads and explicit numerical recomputation."""

import argparse
import json
import math
import platform
from pathlib import Path
import numpy as np
import scipy
from ..cache import atomic_json, sha256_file
from ..contracts import Contract
from .membrane_controls import Request, compare


def environment():
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
    }


def code_hashes():
    return {
        name: sha256_file(Path(__file__).with_name(name))
        for name in ("membrane.py", "membrane_controls.py", "membrane_controls_run.py")
    }


def equivalent(left, right):
    if type(left) is not type(right):
        return (
            type(left) in (int, float) and type(right) in (int, float) and left == right
        )
    if isinstance(left, float):
        return math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-15)
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            equivalent(left[k], right[k]) for k in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            equivalent(a, b) for a, b in zip(left, right)
        )
    return left == right


def run(request, folder):
    request = Request.model_validate(request)
    result = compare(request)
    folder = Path(folder)
    folder.mkdir(mode=0o700, parents=True, exist_ok=False)
    atomic_json(folder / "request.json", request.model_dump())
    atomic_json(folder / "result.json", result)
    manifest = {
        "schema_version": 1,
        "line": "R07",
        "kind": "transient_control_bank",
        "status": "complete",
        "input_hashes": {"request.json": sha256_file(folder / "request.json")},
        "output": {
            "file": "result.json",
            "sha256": sha256_file(folder / "result.json"),
        },
        "code_hashes": code_hashes(),
        "environment": environment(),
        "limits": result["limits"]
        + [
            "Integrity reads do not rerender; numerical recomputation is explicit",
            "Provenance/environment matches are separate from numerical equivalence",
            "Local hashes and recomputation are not signed custody or physical validation",
        ],
    }
    atomic_json(folder / "manifest.json", manifest)
    return manifest


def verify(folder, *, recompute=True):
    folder = Path(folder)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("Regular transient control directory required")
    names = ("request.json", "result.json", "manifest.json")
    for name in names:
        if (
            (folder / name).is_symlink()
            or not (folder / name).is_file()
            or (folder / name).stat().st_size > 32 * 1024 * 1024
        ):
            raise ValueError("Regular transient control artifacts required")
    hashes = {name: sha256_file(folder / name) for name in names}
    manifest = json.loads((folder / "manifest.json").read_text())
    if (
        manifest.get("schema_version"),
        manifest.get("line"),
        manifest.get("kind"),
        manifest.get("status"),
    ) != (1, "R07", "transient_control_bank", "complete"):
        raise ValueError("Complete transient control manifest required")
    if manifest.get("input_hashes") != {
        "request.json": hashes["request.json"]
    } or manifest.get("output") != {
        "file": "result.json",
        "sha256": hashes["result.json"],
    }:
        raise ValueError("Transient control inventory/hash mismatch")
    request = Request.model_validate_json((folder / "request.json").read_text())
    result = json.loads((folder / "result.json").read_text())
    Contract.finite_tree(result)
    if (
        not isinstance(result, dict)
        or result.get("schema_version") != 1
        or result.get("line") != "R07"
        or result.get("kind") != "transient_control_bank"
        or result.get("request") != request.model_dump()
        or set(result.get("conditions", {}))
        != {"impulse", "pulse", "multisine", "seeded_noise"}
    ):
        raise ValueError("Transient control frozen result binding mismatch")
    expected_clock = {
        "start_sample": 0,
        "stop_sample_exclusive": request.duration_samples,
        "sample_count": request.duration_samples,
        "sample_rate": request.membrane.sample_rate,
    }
    for condition in result["conditions"].values():
        field = condition.get("field", {})
        if any(
            type(field.get(k)) is not int or field.get(k) != v
            for k, v in expected_clock.items()
        ):
            raise ValueError(
                "Transient control sample support differs from frozen request"
            )
        rms = field.get("rms", [])
        if len(rms) != len(request.x) or any(
            type(v) not in (int, float) or v < 0 for v in rms
        ):
            raise ValueError("Transient control field inventory differs")
    if recompute and not equivalent(result, compare(request)):
        raise ValueError(
            "Transient control numerical recomputation differs from artifact"
        )
    for name, digest in hashes.items():
        if (folder / name).is_symlink() or sha256_file(folder / name) != digest:
            raise ValueError("Transient control artifact changed during verification")
    return manifest


def verification(folder, *, recompute=False):
    manifest = verify(folder, recompute=recompute)
    return {
        "verified_result_sha256": manifest["output"]["sha256"],
        "read_verification": "numerically_recomputed"
        if recompute
        else "integrity_only",
        "implementation_matches": manifest.get("code_hashes") == code_hashes(),
        "environment_matches": manifest.get("environment") == environment(),
        "numerical_tolerance": {"relative": 1e-12, "absolute": 1e-15}
        if recompute
        else None,
        "limits": [
            "Integrity and frozen source binding are not numerical recomputation or signed custody",
            "Recomputation compares with current implementation; provenance differences are reported separately",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(json.loads(args.request.read_text()), args.output)
