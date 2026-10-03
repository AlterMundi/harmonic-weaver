"""Read-only calls into Weaver's public laboratory contracts and model facade."""
from __future__ import annotations

import math

from harmonic_weaver.lab.contracts import MotionFrame, Preset
from harmonic_weaver.lab.models import MotionModel


ALGORITHMS = ("baseline", "local", "relational", "angular", "collective")
SIGNALS = ("zone.6.speed", "zone.6.velocity_error", "zone.6.I", "zone.6.R",
           "zone.6.angle_deg", "zone.6.angular_error", "collective.residual",
           "collective.change")


def read_models(frames, *, scale=.26, algorithms=ALGORITHMS):
    """No audio/routing: exactly the same 2D frames go to each separate model."""
    frames = [MotionFrame.model_validate(frame) for frame in frames]
    last_times = {}
    for frame in frames:
        epoch = (frame.source_id, frame.stream_id)
        if epoch in last_times and frame.source_time_s <= last_times[epoch]:
            raise ValueError("source timestamps must increase within a stream epoch; "
                             "loops/seeks need a distinct stream_id")
        last_times[epoch] = frame.source_time_s
    outputs = {}
    for algorithm in algorithms:
        preset = Preset(id=f"sai_bridge_{algorithm}")
        preset.algorithm.id = algorithm
        preset.response.pluck_enabled = False
        model = MotionModel(preset, scale=scale)
        records = []
        previous_source = None
        for frame in frames:
            # The production facade resets on stream/person changes; source_id
            # also names a separate history even when stream tokens coincide.
            if previous_source is not None and frame.source_id != previous_source:
                model.reset()
            previous_source = frame.source_id
            person_id = frame.persons[0].person_id if frame.persons else None
            result = model.observe(frame, person_id, frame.available_monotonic_s)
            records.append({"source_id": frame.source_id, "stream_id": frame.stream_id,
                            "person_id": person_id, "sequence": frame.sequence,
                            "source_time_s": frame.source_time_s,
                            "available_monotonic_s": result.available_monotonic_s,
                            "zone6_relations": result.diagnostics.get("regions", {}).get("6", {}).get("relations"),
                            "signals": {key: result.signals[key].model_dump() for key in SIGNALS
                                        if key in result.signals}})
        outputs[algorithm] = records
    return outputs


def comparison_key(row):
    """An exact observation identity shared by conditions, never an epoch ordinal."""
    for field in ("source_id", "stream_id", "person_id", "source_time_s"):
        if field not in row:
            raise ValueError(f"missing comparison identity: {field}")
    if any(not isinstance(row[field], str) or not row[field]
           for field in ("source_id", "stream_id")):
        raise ValueError("comparison source/stream identities must be nonempty strings")
    person = row["person_id"]
    if person is not None and (not isinstance(person, str) or not person):
        raise ValueError("comparison person identity must be a nonempty string or None")
    t = row["source_time_s"]
    if isinstance(t, bool) or not isinstance(t, (int, float)) or not math.isfinite(t) or t < 0:
        raise ValueError("comparison source time must be finite and nonnegative")
    return row["source_id"], row["stream_id"], person, t


def _index_units(records):
    indexed = {}
    for row in records:
        key = comparison_key(row)
        if key in indexed:
            raise ValueError(f"duplicate comparison unit: {key}")
        indexed[key] = row
    return indexed


def common_observed(a, b, signal):
    """Return (identity, x, y) on common observed units; reject ambiguous input.

    Source/stream/person IDs must identify the same units across conditions.
    Differently named sessions are not matched implicitly by time or position.
    """
    by_a, by_b = _index_units(a), _index_units(b)
    aligned = []
    for key, left in by_a.items():
        right = by_b.get(key)
        if right is None:
            continue
        x = left["signals"].get(signal)
        y = right["signals"].get(signal)
        if x and y and x["state"] == y["state"] == "observed":
            if x["unit"] != y["unit"]:
                raise ValueError("units differ")
            aligned.append((key, x["value"], y["value"]))
    return aligned


def summarize(records, signal):
    values = [r["signals"][signal]["value"] for r in records
              if signal in r["signals"] and r["signals"][signal]["state"] == "observed"]
    return {"observed": len(values), "total": len(records),
            "mean": sum(values)/len(values) if values else None}
