"""Frozen 2D body blocks and whole-block offline Fourier controls.

No interpolation, resampling, pose correction, calibration inference or audio.
Inputs/outputs may contain private tracking: keep such artifacts local. The
default CLI consumes only the public synthetic fixture specification beside it.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import importlib
import json
from pathlib import Path
import platform

import numpy as np
import pydantic

from harmonic_weaver.lab.contracts import MotionFrame, Preset
from harmonic_weaver.lab.models import MotionModel
from .adapter import comparison_key, _index_units
from .fourier import common_three, phase_surrogate, spectral_checks
from .run import source_hashes
from .synthetic import BASE_POSE, motion_frame

INTEGRATION_REFERENCE = "94536702b568641ba0e22c2668130877d6bdd99d"
SIGNALS = tuple(f"zone.{z}.{name}" for z in range(1, 7) for name in ("I", "R")) + (
    "collective.residual", "collective.change")
SEGMENTS = ((5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (5, 11), (6, 12),
            (11, 12), (11, 13), (13, 15), (12, 14), (14, 16))


@dataclass(frozen=True)
class BodyConfig:
    person_id: str
    channels: tuple[tuple[int, int], ...]
    sample_hz: float
    scale: float
    scale_unit: str
    scale_provenance: str
    min_samples: int = 64
    absolute_tolerance_s: float = 1e-8
    relative_tolerance: float = 1e-6
    max_gap_s: float = .25
    minimum_confidence: float = .5

    def __post_init__(self):
        object.__setattr__(self, "channels", tuple(tuple(c) for c in self.channels))
        if (not isinstance(self.person_id, str) or not self.person_id or not self.channels
                or len(set(self.channels)) != len(self.channels)
                or any(type(j) is not int or type(a) is not int or j not in range(17)
                       or a not in (0, 1) for j, a in self.channels)):
            raise ValueError("explicit person and unique COCO-17 scalar 2D channels required")
        if (not np.isfinite([self.sample_hz, self.scale, self.absolute_tolerance_s,
                self.relative_tolerance, self.max_gap_s, self.minimum_confidence]).all()
                or self.sample_hz <= 0 or self.scale <= 0 or type(self.min_samples) is not int or self.min_samples < 4
                or min(self.absolute_tolerance_s, self.relative_tolerance) < 0
                or self.max_gap_s <= 1/self.sample_hz or not 0 <= self.minimum_confidence <= 1
                or self.scale_unit not in ("frame_height", "meter")
                or not isinstance(self.scale_provenance, str) or not self.scale_provenance):
            raise ValueError("invalid explicit sampling, validity or scale configuration")


@dataclass(frozen=True)
class BodyBlock:
    frames: tuple[MotionFrame, ...]
    input_indices: tuple[int, ...]
    config: BodyConfig
    provenance: dict

    def values(self):
        return block_values(self)


def _joints(frame, person_id):
    person = next((p for p in frame.persons if p.person_id == person_id), None)
    return None if person is None else {j.index: j for j in person.joints}


def block_values(block):
    return np.array([[_joints(f, block.config.person_id)[j].position[a]
                      for j, a in block.config.channels] for f in block.frames])


def _metadata(frame, person_id):
    return (frame.source_id, frame.stream_id, person_id, frame.coordinate_frame,
            frame.unit, frame.dimensions, frame.width, frame.height, frame.timestamp_origin)


def _identity(frame, person_id):
    return {"source_id": frame.source_id, "stream_id": frame.stream_id,
            "person_id": person_id, "sequence": frame.sequence,
            "source_time_s": frame.source_time_s,
            "available_monotonic_s": frame.available_monotonic_s}


def prepare_blocks(frames, config: BodyConfig, *, provenance: dict):
    """Retain maximal regular valid blocks in supplied order; report every loss.

    Explicitly supplied Hz defines the index grid. Both adjacent interval and
    total grid residual must be within atol + rtol/Hz. A bad interval separates
    blocks without dropping its valid endpoints; short blocks are excluded.
    Returned snapshots are deep copies, never views of the caller's frames.
    """
    if not isinstance(provenance, dict) or not provenance:
        raise ValueError("explicit input provenance required")
    provenance = json.loads(json.dumps(provenance, allow_nan=False))
    blocks, excluded, boundaries, pending, indices = [], [], [], [], []
    last_times = {}
    expected = 1/config.sample_hz
    tolerance = config.absolute_tolerance_s + config.relative_tolerance*expected
    input_count = 0

    def flush():
        if len(pending) >= config.min_samples:
            blocks.append(BodyBlock(tuple(pending), tuple(indices), config, provenance.copy()))
        else:
            excluded.extend({"input_index": i, "reason": "short_block",
                             **_identity(f, config.person_id)} for i, f in zip(indices, pending))
        pending.clear()
        indices.clear()

    for i, raw in enumerate(frames):
        input_count += 1
        # Contract-invalid input is a hard error, not a silent conversion/drop.
        frame = MotionFrame.model_validate(raw.model_dump() if isinstance(raw, MotionFrame) else raw).model_copy(deep=True)
        comparison_key(_identity(frame, config.person_id))
        joints = _joints(frame, config.person_id)
        reason = None
        if frame.dimensions != 2:
            reason = "unsupported_dimensions"
        elif frame.unit != config.scale_unit:
            reason = "scale_unit_mismatch"
        elif joints is None:
            reason = "selected_person_absent"
        elif any(j not in joints or joints[j].state != "observed" or
                 joints[j].position is None or joints[j].confidence < config.minimum_confidence
                 for j, _ in config.channels):
            reason = "selected_joint_invalid"
        epoch = (frame.source_id, frame.stream_id, config.person_id)
        if epoch in last_times and frame.source_time_s <= last_times[epoch]:
            reason = "nonincreasing_time_in_epoch"
        last_times[epoch] = max(last_times.get(epoch, -1.), frame.source_time_s)
        if reason:
            flush()
            excluded.append({"input_index": i, "reason": reason, **_identity(frame, config.person_id)})
            continue
        if pending:
            previous = pending[-1]
            dt = frame.source_time_s-previous.source_time_s
            boundary = None
            if _metadata(previous, config.person_id) != _metadata(frame, config.person_id):
                boundary = "identity_or_metadata_change"
            elif dt > config.max_gap_s:
                boundary = "gap"
            elif abs(dt-expected) > tolerance:
                boundary = "irregular_interval"
            elif abs(frame.source_time_s-(pending[0].source_time_s+len(pending)*expected)) > tolerance:
                boundary = "sampling_grid_drift"
            if boundary:
                boundaries.append({"input_index": i, "reason": boundary, "interval_s": dt,
                                   **_identity(frame, config.person_id)})
                flush()
        pending.append(frame)
        indices.append(i)
    flush()
    retained = sum(len(b.frames) for b in blocks)
    support = {"input_frames": input_count, "retained_frames": retained,
        "excluded_frames": len(excluded), "exclusion_counts": dict(Counter(e["reason"] for e in excluded)),
        "exclusions": excluded, "boundaries": boundaries, "grid_tolerance_s": tolerance,
        "blocks": [{"index": i, "input_indices": list(b.input_indices), "samples": len(b.frames),
                    "first": _identity(b.frames[0], config.person_id),
                    "last": _identity(b.frames[-1], config.person_id),
                    "coordinate_frame": b.frames[0].coordinate_frame, "unit": b.frames[0].unit,
                    "maximum_grid_residual_s": max(abs(f.source_time_s-(b.frames[0].source_time_s+k*expected))
                        for k, f in enumerate(b.frames))} for i, b in enumerate(blocks)]}
    assert input_count == retained + len(excluded)
    return blocks, support


def control_frames(block, *, seed):
    """Transform selected scalar coordinates only, preserving all other content."""
    x = block_values(block)
    controls = {"original": x, "shared": phase_surrogate(x, seed=seed, shared=True),
                "independent": phase_surrogate(x, seed=seed, shared=False)}
    outputs = {}
    for name, values in controls.items():
        frames = [f.model_copy(deep=True) for f in block.frames]
        for frame, row in zip(frames, values):
            joints = _joints(frame, block.config.person_id)
            for (j, a), value in zip(block.config.channels, row):
                joints[j].position[a] = float(value)
        outputs[name] = frames
    return outputs, {name: {
        "full_coordinates": spectral_checks(x, values),
        # Also expose fluctuation spectra so the large absolute-position DC
        # coefficient cannot obscure a changed cross-spectrum of body motion.
        "fluctuations": spectral_checks(x-x.mean(axis=0), values-values.mean(axis=0))}
        for name, values in controls.items() if name != "original"}


def observe_body(frames, *, person_id, scale, preset):
    """One fresh unchanged facade per block/condition; no history across cuts."""
    model = MotionModel(preset.model_copy(deep=True), scale=scale)
    rows = []
    for frame in frames:
        result = model.observe(frame, person_id, frame.available_monotonic_s)
        rows.append({**_identity(frame, person_id), "signals": {
            name: result.signals[name].model_dump() for name in SIGNALS if name in result.signals}})
    return rows


def geometric_diagnostics(original, transformed, *, person_id, segments=SEGMENTS,
                          minimum_confidence=.5):
    """Segment-length changes in original coordinate units; no pose repair.

    This flags distortions of the frozen reference, not anatomical plausibility.
    Missing endpoint measurements stay missing; no scale normalization is used.
    """
    if len(original) != len(transformed):
        raise ValueError("geometry requires the same observation support")
    result = {}
    for parent, child in segments:
        lengths = [[], []]
        for left, right in zip(original, transformed):
            if comparison_key(_identity(left, person_id)) != comparison_key(_identity(right, person_id)):
                raise ValueError("geometry identities differ")
            if _metadata(left, person_id) != _metadata(right, person_id):
                raise ValueError("geometry units or coordinate metadata differ")
            pairs = [_joints(f, person_id) for f in (left, right)]
            if not all(joints is not None and all(j in joints and joints[j].state == "observed"
                    and joints[j].position is not None and joints[j].confidence >= minimum_confidence
                    for j in (parent, child)) for joints in pairs):
                continue
            for values, joints in zip(lengths, pairs):
                values.append(float(np.linalg.norm(np.array(joints[child].position)-joints[parent].position)))
        a, b = (np.asarray(v) for v in lengths)
        valid = a > 1e-12
        result[f"{parent}-{child}"] = {"common_observed": len(a), "total": len(original),
            "original_mean": float(a.mean()) if len(a) else None,
            "original_std": float(a.std()) if len(a) else None,
            "transformed_std": float(b.std()) if len(b) else None,
            "paired_length_mae": float(np.mean(abs(b-a))) if len(a) else None,
            "paired_length_max_change": float(np.max(abs(b-a))) if len(a) else None,
            "maximum_relative_length_change": float(np.max(abs(b[valid]-a[valid])/a[valid])) if valid.any() else None,
            "relative_support": int(valid.sum()),
            "transformed_near_zero_lengths": int(np.sum(b <= 1e-12))}
    return {"unit": original[0].unit if original else None,
            "interpretation": "deviation from frozen segment lengths; not an anatomical validity score",
            "segments": result}


def compare_signal(rows, signal):
    """Existing common-support summary plus inspectable temporal differences."""
    summary = common_three(rows, signal)
    indices = {name: _index_units(values) for name, values in rows.items()}
    traces = []
    for key in sorted(set.intersection(*(set(index) for index in indices.values()))):
        cells = {name: index[key]["signals"].get(signal) for name, index in indices.items()}
        if not all(cell and cell["state"] == "observed" for cell in cells.values()):
            continue
        values = {name: cell["value"] for name, cell in cells.items()}
        traces.append({"identity": list(key), "sequence": indices["original"][key]["sequence"],
            "shared_minus_original": values["shared"]-values["original"],
            "independent_minus_original": values["independent"]-values["original"],
            "shared_minus_independent": values["shared"]-values["independent"]})
    assert len(traces) == summary["common_observed"]
    return {**summary, "paired_temporal_differences": traces,
        "missing_reason_counts": {name: dict(Counter(
            row["signals"].get(signal, {}).get("reason") or "signal unavailable"
            for row in values if row["signals"].get(signal, {}).get("state") != "observed"))
            for name, values in rows.items()}}


def compare_blocks(blocks, *, seeds, preset):
    preset = Preset.model_validate(preset).model_copy(deep=True)
    if preset.algorithm.id == "baseline" or preset.response.pluck_enabled:
        raise ValueError("use a non-baseline descriptive preset with plucks explicitly disabled")
    results = []
    for block_index, block in enumerate(blocks):
        if block.config.max_gap_s > preset.algorithm.max_gap_s:
            raise ValueError("preparation gap limit exceeds the model's declared gap limit")
        for seed in seeds:
            controls, checks = control_frames(block, seed=seed)
            rows = {name: observe_body(frames, person_id=block.config.person_id,
                scale=block.config.scale, preset=preset) for name, frames in controls.items()}
            results.append({"block_index": block_index, "seed": seed,
                "source_id": block.frames[0].source_id, "stream_id": block.frames[0].stream_id,
                "person_id": block.config.person_id, "samples": len(block.frames),
                "config": asdict(block.config), "input_provenance": block.provenance,
                "spectral_checks": checks,
                "descriptors": {name: compare_signal(rows, name) for name in SIGNALS},
                "geometry": {name: geometric_diagnostics(controls["original"], frames,
                    person_id=block.config.person_id, minimum_confidence=block.config.minimum_confidence)
                    for name, frames in controls.items() if name != "original"}})
    return {"preset": preset.model_dump(), "results": results,
            "history_policy": "fresh facade for every block and condition",
            "operation": "offline full block; stored availability is replay metadata, not transform causality"}


def synthetic_frames(spec):
    """Public deterministic fixture recipe, frozen to MotionFrames before use."""
    frames = []
    for epoch in spec["epochs"]:
        n = epoch["samples"]
        for k in range(n):
            angle = 2*np.pi*k/n
            frame = motion_frame(k/spec["sample_hz"], k, stream=epoch["stream_id"], person="athlete")
            frame.source_id = "body_fourier_public_synthetic"
            points = BASE_POSE.copy()
            if epoch["kind"] == "coupled":
                a = np.sin(3*angle)+.55*np.sin(7*angle)+.35*np.sin(10*angle)
                b = np.cos(3*angle)+.55*np.cos(7*angle)+.35*np.cos(10*angle)
                for j, factor in ((7, 1), (8, 1), (9, 2), (10, 2)):
                    points[j] += .018*factor*np.array([a, b])
            elif epoch["kind"] == "articulated":
                # Four rotating rigid links; nonlinear posture varies, while
                # each constructed arm segment length stays exactly constant.
                for shoulder, elbow, wrist, side in ((5, 7, 9, -1), (6, 8, 10, 1)):
                    theta = side*(.7+.45*np.sin(2*angle)+.2*np.sin(5*angle))
                    phi = side*(1.2+.55*np.sin(3*angle+.4))
                    points[elbow] = points[shoulder]+.16*np.array([np.sin(theta), np.cos(theta)])
                    points[wrist] = points[elbow]+.14*np.array([np.sin(phi), np.cos(phi)])
            elif epoch["kind"] == "single_channel":
                points[9, 0] += .025*(np.sin(3*angle)+.55*np.sin(7*angle))
            elif epoch["kind"] != "static":
                raise ValueError("unknown public synthetic epoch")
            for joint in frame.persons[0].joints:
                joint.position = points[joint.index].tolist()
            # A moving bystander, alternating list order, must never become the
            # selected body merely because it appears first in a frame.
            bystander = frame.persons[0].model_copy(deep=True)
            bystander.person_id = "bystander"
            for joint in bystander.joints:
                joint.position[0] += .15+.01*np.sin(angle)
            frame.persons = [bystander, frame.persons[0]] if k % 2 else [frame.persons[0], bystander]
            if k in epoch.get("drop_indices", []):
                continue
            if k in epoch.get("invalid_indices", []):
                joint = _joints(frame, "athlete")[9]
                joint.state, joint.position, joint.confidence = "missing", None, 0.
            if k in epoch.get("absent_indices", []):
                frame.persons = [bystander]
            frames.append(frame)
    return frames


def body_experiment(spec_path=None):
    path = Path(spec_path) if spec_path else Path(__file__).with_name("fixtures") / "body_fourier_public.json"
    raw = path.read_bytes()
    spec = json.loads(raw)
    frames = synthetic_frames(spec)
    preset = Preset(id="sai_body_fourier", algorithm=spec["algorithm"])
    preset.response.pluck_enabled = False
    runs = []
    for selection in spec["selections"]:
        config = BodyConfig(person_id="athlete", channels=tuple(tuple(c) for c in selection["channels"]),
            sample_hz=spec["sample_hz"], scale=spec["scale"], scale_unit="frame_height",
            scale_provenance=spec["scale_provenance"], **spec["preparation"])
        chosen = [f for f in frames if f.stream_id in selection["streams"]]
        blocks, support = prepare_blocks(chosen, config, provenance={
            "kind": "public synthetic recipe frozen in memory before transforms",
            "fixture_sha256": hashlib.sha256(raw).hexdigest(),
            "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "selection": selection["name"]})
        runs.append({"selection": selection["name"], "preparation": support,
                     "comparison": compare_blocks(blocks, seeds=spec["seeds"], preset=preset)})
    return {"kind": "synthetic control characterization; no human or HIT validation",
            "integration_reference": INTEGRATION_REFERENCE, "configuration": spec,
            "effective_modules": effective_modules(),
            "runtime": {"python": platform.python_version(), "numpy": np.__version__, "pydantic": pydantic.__version__},
            "runs": runs}


def effective_modules():
    """Selected effective producers, not an exhaustive dependency audit."""
    manifest = source_hashes()
    for name in (phase_surrogate.__module__, __name__):
        module = importlib.import_module(name)
        path = Path(module.__file__).resolve()
        manifest[name] = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    # MotionModel uses this dynamically loaded frozen driver even for its Pluck
    # class with plucking disabled. Resolve the actual loader result, not a guess.
    module = importlib.import_module("harmonic_weaver.lab.legacy").baseline_module()
    path = Path(module.__file__).resolve()
    manifest[module.__name__] = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return manifest


def main():
    print(json.dumps(body_experiment(), sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
