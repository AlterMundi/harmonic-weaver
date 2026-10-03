"""Local reproducible known-component controls; provenance is separate from results."""

import json
import inspect
import math
import platform
import threading
from pathlib import Path
from uuid import uuid4

from ..cache import atomic_json, sha256_file
from ..contracts import Contract
from .experience_response_service import identity
from .experience_transport_service import TransportService
from .neuro_snr import Config, calculate

FILES = ("request.json", "result.json", "manifest.json")


def code_hashes():
    return {
        "neuro_snr.py": sha256_file(Path(inspect.getfile(calculate))),
        "neuro_snr_run.py": sha256_file(Path(__file__)),
        "contracts.py": sha256_file(Path(inspect.getfile(Contract))),
    }


def run(request, folder):
    frozen = Config.model_validate(request)
    result = calculate(frozen)
    folder = Path(folder)
    folder.mkdir(mode=0o700, parents=True, exist_ok=False)
    atomic_json(folder / "request.json", frozen.model_dump())
    atomic_json(folder / "result.json", result)
    atomic_json(
        folder / "manifest.json",
        {
            "schema_version": 1,
            "line": "R11",
            "kind": "synthetic_snr_record",
            "status": "complete",
            "request_sha256": identity(frozen.model_dump()),
            "hashes": {name: sha256_file(folder / name) for name in FILES[:-1]},
            "code_hashes": code_hashes(),
            "environment": {"python": platform.python_version()},
            "metric_version": result["metric_version"],
            "limits": result["limits"]
            + [
                "Artifact hashes verify local integrity, not signed custody",
                "Implementation/environment provenance is independent of numerical equivalence",
            ],
        },
    )
    return verify(folder)


def numerically_equivalent(left, right):
    """Exact structure/support, floating results within an explicit small tolerance."""
    if type(left) is not type(right):
        return False
    if isinstance(left, float):
        return math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            numerically_equivalent(left[k], right[k]) for k in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            numerically_equivalent(a, b) for a, b in zip(left, right)
        )
    return left == right


def verify(folder, *, recompute=True):
    folder = Path(folder)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("Regular SNR record directory required")
    for name in FILES:
        path = folder / name
        if (
            path.is_symlink()
            or not path.is_file()
            or path.stat().st_size > 32 * 1024 * 1024
        ):
            raise ValueError("Regular bounded SNR artifacts required")
    hashes = {name: sha256_file(folder / name) for name in FILES}
    manifest = json.loads((folder / "manifest.json").read_text())
    Contract.finite_tree(manifest)
    if (
        manifest.get("schema_version") != 1
        or manifest.get("line") != "R11"
        or manifest.get("kind") != "synthetic_snr_record"
        or manifest.get("status") != "complete"
    ):
        raise ValueError("Invalid SNR manifest")
    if manifest.get("hashes") != {name: hashes[name] for name in FILES[:-1]}:
        raise ValueError("SNR artifact hash mismatch")
    frozen = Config.model_validate_json((folder / "request.json").read_text())
    if manifest.get("request_sha256") != identity(frozen.model_dump()):
        raise ValueError("SNR request identity mismatch")
    result = json.loads((folder / "result.json").read_text())
    Contract.finite_tree(result)
    if (
        not isinstance(result, dict)
        or result.get("config") != frozen.model_dump()
        or result.get("metric_version") != manifest.get("metric_version")
        or result.get("line") != "R11"
        or result.get("kind") != "synthetic_known_components"
    ):
        raise ValueError("SNR frozen result binding mismatch")
    # Environment/code changes are recorded, not used as a numerical equality gate.
    if recompute and not numerically_equivalent(result, calculate(frozen)):
        raise ValueError("SNR numerical recomputation differs")
    for name, digest in hashes.items():
        if (folder / name).is_symlink() or sha256_file(folder / name) != digest:
            raise ValueError("SNR artifact changed during verification")
    return {
        **manifest,
        "read_verification": "recomputed" if recompute else "integrity_only",
        "implementation_matches": manifest.get("code_hashes") == code_hashes(),
        "environment_matches": manifest.get("environment")
        == {"python": platform.python_version()},
        "numerical_tolerance": {"relative": 1e-12, "absolute": 1e-12}
        if recompute
        else None,
    }


class SNRService(TransportService):
    def __init__(self, data_dir):
        self.root = Path(data_dir) / "research/r11-snr"
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.lock = threading.RLock()

    def read(self, ident):
        folder = self.folder(ident)
        manifest = verify(folder)
        if manifest["request_sha256"][:32] != ident:
            raise ValueError("SNR content ID mismatch")
        return {**manifest, "id": ident}

    def start(self, request):
        frozen = Config.model_validate(request)
        digest = identity(frozen.model_dump())
        ident = digest[:32]
        with self.lock:
            if (self.root / ident).exists():
                saved = self.read(ident)
                if saved["request_sha256"] != digest:
                    raise ValueError("SNR content ID collision")
                return saved
            staging = self.root / f".pending-{uuid4().hex}"
            run(frozen, staging)
            staging.rename(self.root / ident)
            return self.read(ident)

    def artifact(self, ident, name):
        if name not in FILES:
            raise ValueError("Unknown SNR artifact")
        self.read(ident)
        return self.folder(ident) / name
