"""One-command deterministic, synthetic-only bench: stdout is the result JSON."""
from __future__ import annotations

import hashlib
import json
import platform
import importlib
from pathlib import Path

import numpy as np
import pydantic

from . import SAI_BASE, WEAVER_BASE
from .adapter import common_observed, read_models, summarize
from .prediction import prediction_contrast, support_selection_control
from .fourier import fourier_bench
from .synthetic import (ambiguous_projection, common_rhythm_no_pair_coupling,
                        concentration, diagonal_counterexample, equal_path_rhythm,
                        frame_controls, jittered_frames, paired_cycles, phase_controls,
                        plane_pair, spacetime_c)


def source_hashes():
    """Selected effective imported modules, not files relative to this bridge.

    This is a source manifest, not an exhaustive dependency/bytecode audit.
    Historical reference SHAs in source_sha do not identify the effective code.
    """
    names = ("contracts", "models", "analysis_math", "collective", "kinematics", "legacy")
    manifest = {}
    for name in names:
        module = importlib.import_module(f"harmonic_weaver.lab.{name}")
        path = Path(module.__file__).resolve()
        manifest[module.__name__] = {"path": str(path),
                                   "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return manifest


def bench():
    aligned_frames, aligned_phase = paired_cycles(opposed=False)
    opposed_frames, opposed_phase = paired_cycles(opposed=True)
    assert [f.source_time_s for f in aligned_frames] == [f.source_time_s for f in opposed_frames]
    models_a = read_models(aligned_frames)
    models_b = read_models(opposed_frames)
    descriptions = {}
    for algorithm in models_a:
        keys = ("zone.6.speed", "zone.6.velocity_error", "zone.6.I", "zone.6.R",
                "zone.6.angle_deg", "zone.6.angular_error", "collective.residual",
                "collective.change")
        descriptions[algorithm] = {}
        for key in keys:
            common = common_observed(models_a[algorithm], models_b[algorithm], key)
            descriptions[algorithm][key] = {
                "aligned": summarize(models_a[algorithm], key),
                "opposed": summarize(models_b[algorithm], key),
                "common_observed": len(common),
                "common_aligned_mean": sum(x for _, x, _ in common)/len(common) if common else None,
                "common_opposed_mean": sum(y for _, _, y in common)/len(common) if common else None,
            }
    clean = aligned_frames[:100]
    noisy = jittered_frames(clean, gap_at=50)
    quality = {}
    for name, frames in (("clean", clean), ("jitter_and_gap", noisy)):
        records = read_models(frames, algorithms=("relational",))["relational"]
        quality[name] = {key: summarize(records, key) for key in ("zone.6.I", "zone.6.speed")}
    data = {"kind": "synthetic-only; no human or HIT validation",
            "source_sha": {"weaver": WEAVER_BASE, "sai": SAI_BASE},
            "production_source_sha256": source_hashes(),
            "runtime": {"python": platform.python_version(), "numpy": np.__version__,
                        "pydantic": pydantic.__version__},
            "rhythm_same_path": equal_path_rhythm(),
            "spacetime_c_2d_analogue": spacetime_c(),
            "frame_controls": frame_controls(),
            "tracking_quality_probe": quality,
            "matched_marginals": {"phase_r_aligned": concentration(aligned_phase),
                                  "phase_r_opposed": concentration(opposed_phase),
                                  "event_only_r_both": 1., "plane_q": plane_pair(),
                                  "weaver": descriptions},
            "phase": phase_controls(),
            "common_rhythm_no_coupling": common_rhythm_no_pair_coupling(),
            "projection_ambiguity": ambiguous_projection(),
            "q_tensor_counterexample": diagonal_counterexample(),
            "prediction": {"null": prediction_contrast(False),
                           "related": prediction_contrast(True),
                           "selection_control": support_selection_control()},
            "fourier_controls": fourier_bench()}
    # Whole report digest includes paths, provenance and runtime, not just numbers.
    # No cross-environment equality or identity of historical digests is asserted.
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)
    data["result_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return data


def main():
    print(json.dumps(bench(), sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
