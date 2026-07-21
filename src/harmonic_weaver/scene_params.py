"""Live convergence knobs for the Stage web UI.

Knob values live in process memory, survive page reloads, and are pushed to the
Shaper over the engine's OutputTransport (LiveOSCTransport in rehearsal). Route
traffic is rewritten so static scene constants cannot fight operator overrides.
"""

from __future__ import annotations

import threading
import time
from dataclasses import replace
from typing import Any, Mapping

from .engine.transport import OutputRecord, OutputTransport

# Defaults match instrumento_v1_mvp scene constants / proposal knobs.
DEFAULT_SCENE_PARAMS: dict[str, float] = {
    "settle_beats": 1.0,
    "ceiling_max": 32.0,
    "tempo_conf_threshold": 0.35,
    "clock_bpm_override": 0.0,
    "arp_register_lo": 1.0,
    "arp_register_hi": 16.0,
}

PARAM_BOUNDS: dict[str, tuple[float, float]] = {
    "settle_beats": (0.25, 4.0),
    "ceiling_max": (1.0, 32.0),
    "tempo_conf_threshold": (0.0, 1.0),
    "clock_bpm_override": (0.0, 240.0),
    "arp_register_lo": (1.0, 32.0),
    "arp_register_hi": (1.0, 32.0),
}

# Capability → OSC address (H=0 for arp registers; intercept rewrites all hands).
_PUSH_SPECS: dict[str, dict[str, Any]] = {
    "settle_beats": {
        "capability": "settle_beats",
        "address": "/digital/settle_beats",
        "argument": "beats",
        "bindings": {},
        "as_int": False,
    },
    "ceiling_max": {
        "capability": "partial_ceiling",
        "address": "/digital/ceiling",
        "argument": "level",
        "bindings": {},
        "as_int": False,
        "level_from_n": True,
    },
    "clock_bpm_override": {
        "capability": "clock_bpm",
        "address": "/digital/clock/bpm",
        "argument": "bpm",
        "bindings": {},
        "as_int": False,
        "skip_if_zero": True,
    },
    "arp_register_lo": {
        "capability": "arp_register_lo",
        "address": "/digital/arp/0/register_lo",
        "argument": "n",
        "bindings": {"H": 0},
        "as_int": True,
    },
    "arp_register_hi": {
        "capability": "arp_register_hi",
        "address": "/digital/arp/0/register_hi",
        "argument": "n",
        "bindings": {"H": 0},
        "as_int": True,
    },
}


def ceiling_n_to_level(n_max: float) -> float:
    """Inverse of Shaper level_to_partial_ceiling: n = 1 + round(level * 31)."""
    n = max(1, min(32, int(round(float(n_max)))))
    return (n - 1) / 31.0


def ceiling_level_to_n(level: float) -> int:
    level = max(0.0, min(1.0, float(level)))
    return int(1 + round(level * 31))


class SceneParamsStore:
    """Thread-safe live knob store with OSC push + route rewrite helpers."""

    def __init__(self, initial: Mapping[str, float] | None = None) -> None:
        self._lock = threading.RLock()
        self._values = dict(DEFAULT_SCENE_PARAMS)
        if initial:
            self.update(dict(initial), push=False)

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            return {
                "settle_beats": float(self._values["settle_beats"]),
                "ceiling_max": float(int(round(self._values["ceiling_max"]))),
                "tempo_conf_threshold": float(self._values["tempo_conf_threshold"]),
                "clock_bpm_override": float(self._values["clock_bpm_override"]),
                "arp_register_lo": float(int(round(self._values["arp_register_lo"]))),
                "arp_register_hi": float(int(round(self._values["arp_register_hi"]))),
            }

    def update(
        self,
        patch: Mapping[str, Any],
        *,
        transport: OutputTransport | None = None,
        engine: Any | None = None,
        push: bool = True,
    ) -> dict[str, Any]:
        """Apply a partial update. Returns snapshot plus push audit."""

        if not isinstance(patch, Mapping):
            raise ValueError("body must be a JSON object")
        unknown = [key for key in patch if key not in PARAM_BOUNDS]
        if unknown:
            raise ValueError(f"unknown knob(s): {', '.join(sorted(unknown))}")

        changed: list[str] = []
        with self._lock:
            for key, raw in patch.items():
                if raw is None:
                    continue
                try:
                    value = float(raw)
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"{key} must be a number") from exc
                if not (value == value) or value in (float("inf"), float("-inf")):
                    raise ValueError(f"{key} must be finite")
                lo, hi = PARAM_BOUNDS[key]
                if value < lo or value > hi:
                    raise ValueError(f"{key} must be in [{lo}, {hi}]")
                if key in {"ceiling_max", "arp_register_lo", "arp_register_hi"}:
                    value = float(int(round(value)))
                if self._values[key] != value:
                    changed.append(key)
                self._values[key] = value

            # Keep register window ordered.
            lo = self._values["arp_register_lo"]
            hi = self._values["arp_register_hi"]
            if lo > hi:
                self._values["arp_register_lo"], self._values["arp_register_hi"] = hi, lo
                if "arp_register_lo" not in changed:
                    changed.append("arp_register_lo")
                if "arp_register_hi" not in changed:
                    changed.append("arp_register_hi")

            values = self.snapshot()

        if "tempo_conf_threshold" in changed or "tempo_conf_threshold" in patch:
            self._patch_tempo_conf_threshold(engine, values["tempo_conf_threshold"])

        pushes: list[dict[str, Any]] = []
        if push and transport is not None:
            keys_to_push = changed if changed else [
                key for key in patch if key in _PUSH_SPECS
            ]
            # Always push explicit keys present in this request (even if unchanged)
            # so the operator can re-assert a value mid-session.
            for key in patch:
                if key in _PUSH_SPECS and key not in keys_to_push:
                    keys_to_push.append(key)
            for key in keys_to_push:
                if key not in _PUSH_SPECS:
                    continue
                result = self._push_one(transport, key, values[key])
                if result is not None:
                    pushes.append(result)

        return {"params": values, "changed": changed, "pushed": pushes}

    def rewrite_record(self, record: OutputRecord) -> OutputRecord:
        """Rewrite route/safety capability traffic to honor live knobs."""

        if record.kind != "capability" or record.capability is None or record.value is None:
            return record
        with self._lock:
            values = dict(self._values)

        cap = record.capability
        value = record.value

        if cap == "settle_beats":
            return replace(record, value=float(values["settle_beats"]))

        if cap == "clock_bpm":
            override = float(values["clock_bpm_override"])
            if override > 0.0:
                return replace(record, value=override)
            return record

        if cap == "partial_ceiling":
            n = ceiling_level_to_n(float(value))
            ceiling_max = int(round(values["ceiling_max"]))
            if n > ceiling_max:
                return replace(record, value=ceiling_n_to_level(ceiling_max))
            return record

        if cap == "arp_register_lo":
            return replace(record, value=int(round(values["arp_register_lo"])))

        if cap == "arp_register_hi":
            return replace(record, value=int(round(values["arp_register_hi"])))

        return record

    def _push_one(
        self,
        transport: OutputTransport,
        key: str,
        value: float,
    ) -> dict[str, Any] | None:
        spec = _PUSH_SPECS[key]
        if spec.get("skip_if_zero") and float(value) <= 0.0:
            return {
                "key": key,
                "skipped": True,
                "reason": "clock_bpm_override=0 uses body tempo",
            }
        osc_value: float | int
        if spec.get("level_from_n"):
            osc_value = ceiling_n_to_level(value)
        elif spec.get("as_int"):
            osc_value = int(round(value))
        else:
            osc_value = float(value)

        record = OutputRecord(
            instrument_id="shaper",
            kind="capability",
            sent_at_us=time.time_ns() // 1000,
            reason="stage_knob",
            capability=str(spec["capability"]),
            address=str(spec["address"]),
            bindings=dict(spec["bindings"]),
            argument=str(spec["argument"]),
            value=osc_value,
        )
        try:
            transport.send_capability(record)
        except Exception as exc:  # noqa: BLE001 — surface transport errors to the UI
            return {
                "key": key,
                "address": record.address,
                "value": osc_value,
                "error": str(exc),
            }
        return {
            "key": key,
            "address": record.address,
            "value": osc_value,
            "capability": record.capability,
        }

    @staticmethod
    def _patch_tempo_conf_threshold(engine: Any | None, threshold: float) -> None:
        """Hot-patch include_when gates that reference tempo_conf channels."""

        if engine is None:
            return
        compiled = getattr(engine, "_compiled_scene", None)
        if compiled is None:
            return
        for aggregator in compiled.aggregators:
            for item in aggregator.inputs:
                predicate = item.get("include_when") if isinstance(item, dict) else None
                if not isinstance(predicate, dict):
                    continue
                channel = predicate.get("channel")
                if isinstance(channel, str) and channel.endswith("tempo_conf"):
                    predicate["value"] = float(threshold)


class KnobAwareTransport:
    """OutputTransport decorator that applies live knobs to capability writes."""

    def __init__(self, inner: OutputTransport, params: SceneParamsStore) -> None:
        self._inner = inner
        self._params = params

    @property
    def inner(self) -> OutputTransport:
        return self._inner

    @property
    def records(self) -> list[OutputRecord]:
        # Preserve RecordingOutputTransport / LiveOSCTransport audit access.
        return getattr(self._inner, "records")  # type: ignore[no-any-return]

    def send_capability(self, record: OutputRecord) -> None:
        self._inner.send_capability(self._params.rewrite_record(record))

    def invoke_action(self, record: OutputRecord) -> None:
        self._inner.invoke_action(record)

    def clear(self) -> None:
        clearer = getattr(self._inner, "clear", None)
        if callable(clearer):
            clearer()


def install_knob_transport(engine: Any, params: SceneParamsStore) -> KnobAwareTransport:
    """Ensure engine.transport rewrites capability traffic through knobs."""

    current = engine.transport
    if isinstance(current, KnobAwareTransport):
        return current
    wrapped = KnobAwareTransport(current, params)
    engine.transport = wrapped
    return wrapped


__all__ = [
    "DEFAULT_SCENE_PARAMS",
    "KnobAwareTransport",
    "PARAM_BOUNDS",
    "SceneParamsStore",
    "ceiling_level_to_n",
    "ceiling_n_to_level",
    "install_knob_transport",
]
