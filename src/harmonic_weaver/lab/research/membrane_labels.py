"""Explicit retrospective window labels from the evaluation bound to R07 PCM.

This module reads body features only after the sound figure exists. It does
not feed features or labels to the membrane renderer or infer intentions.
"""

from collections import Counter
import json
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..cache import sha256_file
from ..contracts import Contract, Number
from ..evaluation.runner import digest
from .body import snapshot as body_snapshot


class Settings(Contract):
    signal_ids: list[str] = Field(min_length=1, max_length=8)
    method: Literal["mean", "rms", "std", "peak_abs"] = "mean"
    min_observations: int = Field(default=2, ge=2, le=14400)
    min_observed_fraction: Number = Field(default=1.0, gt=0, le=1)
    max_gap_s: Number = Field(default=0.1, gt=0, le=5)

    @model_validator(mode="after")
    def unique(self):
        if len(set(self.signal_ids)) != len(self.signal_ids) or any(
            not s or len(s) > 200 for s in self.signal_ids
        ):
            raise ValueError("Distinct bounded signal IDs required")
        return self


class Request(Settings):
    projection_run_id: str = Field(pattern=r"^[a-f0-9]{32}$")


class Window(Contract):
    evaluation_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    run_index: int = Field(ge=0)
    signal_ids: list[str] = Field(min_length=1, max_length=8)
    start_s: Number = Field(ge=0)
    end_s: Number = Field(gt=0)


def context(projections, evaluation, ident):
    report_path = projections.artifact(ident, "result.json")
    report_hash = sha256_file(report_path)
    figure = json.loads(report_path.read_text())
    audio = projections.audio_source(ident)
    manifest_path = audio.with_name("manifest.json")
    manifest = json.loads(manifest_path.read_text())
    if sha256_file(manifest_path) != figure["source_manifest_sha256"]:
        raise ValueError("Label source manifest differs from frozen figure")
    input_path = audio.with_name("input.json")
    document = json.loads(input_path.read_text())
    if sha256_file(input_path) != manifest["input_hashes"]["input.json"]:
        raise ValueError("Label PCM input changed")
    selection = document["request"]
    evaluated = evaluation.report(selection["evaluation_id"])["manifest"]
    index = selection["run_index"]
    if not 0 <= index < len(evaluated["runs"]):
        raise ValueError("Bound label run outside evaluation")
    run = evaluated["runs"][index]
    provenance = document["provenance"]
    if (
        provenance.get("evaluation_id") != selection["evaluation_id"]
        or provenance.get("run_index") != index
        or provenance.get("trace_sha256") != run["sha256"]
        or provenance.get("request_sha256") != evaluated["request_sha256"]
    ):
        raise ValueError("PCM input is not bound to this frozen evaluation trace")
    field = figure["window"]
    origin = selection["start_s"]
    start = origin + field["start_sample"] / field["sample_rate"]
    end = origin + field["stop_sample_exclusive"] / field["sample_rate"]
    if end > selection["end_s"]:
        raise ValueError("Sound tail has no contemporaneous body-feature label")
    if sha256_file(report_path) != report_hash:
        raise ValueError("Figure changed during label selection")
    return {
        "figure": figure,
        "projection_sha256": report_hash,
        "evaluation_id": selection["evaluation_id"],
        "run_index": index,
        "trace_sha256": run["sha256"],
        "start_s": start,
        "end_s": end,
        "signals": run["signals"],
        "paths": {
            report_path: report_hash,
            manifest_path: figure["source_manifest_sha256"],
            input_path: manifest["input_hashes"]["input.json"],
        },
    }


def catalog(projections, evaluation, ident):
    bound = context(projections, evaluation, ident)
    return {
        k: bound[k]
        for k in (
            "evaluation_id",
            "run_index",
            "start_s",
            "end_s",
            "signals",
            "projection_sha256",
        )
    }


def calculate(projections, evaluation, request):
    request = Request.model_validate(request)
    bound = context(projections, evaluation, request.projection_run_id)
    window = Window(
        evaluation_id=bound["evaluation_id"],
        run_index=bound["run_index"],
        signal_ids=request.signal_ids,
        start_s=bound["start_s"],
        end_s=bound["end_s"],
    )
    document = body_snapshot(evaluation, window)
    rows = document["rows"]
    observed = [r for r in rows if r["values"] is not None]
    causes = Counter()
    for row in rows:
        if row["values"] is None:
            for key, reason in row.get(
                "invalid_signals", {"frame": row.get("reason", "missing")}
            ).items():
                causes[f"{key}: {reason}"] += 1
    coverage = len(observed) / len(rows)
    if (
        len(observed) < request.min_observations
        or coverage < request.min_observed_fraction
    ):
        raise ValueError(
            f"Label coverage insufficient: {len(observed)}/{len(rows)} observations; causes={dict(causes)}"
        )
    times = np.asarray([row["time_s"] for row in observed])
    gap = max([times[0] - window.start_s, window.end_s - times[-1], *np.diff(times)])
    if gap > request.max_gap_s + 1e-12:
        raise ValueError("Label observed support exceeds configured maximum gap")
    values = np.asarray([row["values"] for row in observed])
    target = {
        "mean": lambda: np.mean(values, axis=0),
        "rms": lambda: np.sqrt(np.mean(values**2, axis=0)),
        "std": lambda: np.std(values, axis=0),
        "peak_abs": lambda: np.max(np.abs(values), axis=0),
    }[request.method]()
    for path, expected in bound["paths"].items():
        if sha256_file(path) != expected:
            raise ValueError("Label source changed during aggregation")
    run = evaluation.report(window.evaluation_id)["manifest"]["runs"][window.run_index]
    if (
        document["provenance"]["trace_sha256"] != bound["trace_sha256"]
        or run["sha256"] != bound["trace_sha256"]
    ):
        raise ValueError("Label evaluation trace changed")
    result = {
        "schema_version": 1,
        "request": request.model_dump(),
        "attribute_ids": [f"{request.method}:{key}" for key in request.signal_ids],
        "attribute_units": [document["unit"]] * len(request.signal_ids),
        "targets": target.tolist(),
        "window": {"start_s": window.start_s, "end_s": window.end_s},
        "coverage": {
            "observations": len(rows),
            "observed": len(observed),
            "observed_fraction": coverage,
            "max_observed_gap_s": float(gap),
            "invalid_causes": dict(causes),
            "duplicate_control_holds_excluded": document[
                "duplicate_control_holds_excluded"
            ],
        },
        "projection_sha256": bound["projection_sha256"],
        "implementation": {
            "module": __name__,
            "sha256": sha256_file(Path(__file__)),
            "numpy": np.__version__,
        },
        "provenance": document["provenance"],
        "limits": [
            "Retrospective concurrent window label, not a forecast or annotation of intention",
            "Sample statistics on unique observed features, not time-weighted interpolation",
            "Coverage fraction counts observations, not seconds or accuracy of pose",
            "Same-unit signals use common observed support; gaps are not imputed",
            "Source body IDs are tracking declarations, not verified biometric identity",
        ],
    }
    Contract.finite_tree(result)
    result["content_sha256"] = digest(result)
    return result
