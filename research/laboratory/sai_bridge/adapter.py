"""Read-only calls into Weaver's public laboratory contracts and model facade."""
from __future__ import annotations

from harmonic_weaver.lab.contracts import MotionFrame, Preset
from harmonic_weaver.lab.models import MotionModel


ALGORITHMS = ("baseline", "local", "relational", "angular", "collective")
SIGNALS = ("zone.6.speed", "zone.6.velocity_error", "zone.6.I", "zone.6.R",
           "zone.6.angle_deg", "zone.6.angular_error", "collective.residual",
           "collective.change")


def read_models(frames, *, scale=.26, algorithms=ALGORITHMS):
    """No audio/routing: exactly the same 2D frames go to each separate model."""
    frames = [MotionFrame.model_validate(frame) for frame in frames]
    if any(a.source_time_s >= b.source_time_s and a.stream_id == b.stream_id
           for a, b in zip(frames, frames[1:])):
        raise ValueError("source timestamps must increase within a stream epoch")
    outputs = {}
    for algorithm in algorithms:
        preset = Preset(id=f"sai_bridge_{algorithm}")
        preset.algorithm.id = algorithm
        preset.response.pluck_enabled = False
        model = MotionModel(preset, scale=scale)
        records = []
        for frame in frames:
            person_id = frame.persons[0].person_id if frame.persons else None
            result = model.observe(frame, person_id, frame.available_monotonic_s)
            records.append({"source_time_s": frame.source_time_s,
                            "available_monotonic_s": result.available_monotonic_s,
                            "zone6_relations": result.diagnostics.get("regions", {}).get("6", {}).get("relations"),
                            "signals": {key: result.signals[key].model_dump() for key in SIGNALS
                                        if key in result.signals}})
        outputs[algorithm] = records
    return outputs


def common_observed(a, b, signal):
    """Align by source time, retaining only rows observed in both conditions."""
    by_t = {row["source_time_s"]: row for row in b}
    aligned = []
    for left in a:
        right = by_t.get(left["source_time_s"])
        if right is None:
            continue
        x = left["signals"].get(signal)
        y = right["signals"].get(signal)
        if x and y and x["state"] == y["state"] == "observed":
            if x["unit"] != y["unit"]:
                raise ValueError("units differ")
            aligned.append((left["source_time_s"], x["value"], y["value"]))
    return aligned


def summarize(records, signal):
    values = [r["signals"][signal]["value"] for r in records
              if signal in r["signals"] and r["signals"][signal]["state"] == "observed"]
    return {"observed": len(values), "total": len(records),
            "mean": sum(values)/len(values) if values else None}
