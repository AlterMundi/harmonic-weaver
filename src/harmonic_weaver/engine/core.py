"""Serialized state store and headless Harmonic Weaver routing engine."""

from __future__ import annotations

import copy
import math
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, replace
from typing import Any, Callable, Iterable, Mapping

from harmonic_weaver.contract_codec import (
    ContractValidationError,
    contract_id_from_manifest,
    validate_manifest,
)

from .compiler import (
    AggregatorRuntime,
    CompiledAggregator,
    CompiledRoute,
    CompiledScene,
    RouteRuntime,
    compile_scene,
    destination_key,
    evaluate_aggregator,
    evaluate_route,
    finite,
    identifier,
    validate_json_finite,
)
from .errors import WeaverError, validation
from .model import (
    EventRecord,
    HELD,
    INVALID,
    InstrumentStatus,
    OBSERVED,
    PanicState,
    SourceStatus,
    StageState,
    ValueEnvelope,
    freeze,
    thaw,
)
from .reporting import ReportWriter
from .transport import InstrumentSendCallback, OutputRecord, OutputTransport, RecordingOutputTransport


_STREAM_RE = re.compile(r"^[0-9a-f]{16}$")


@dataclass
class TransitionRuntime:
    policy: str
    old_value: float
    started_at_us: int
    duration_us: int = 0
    await_valid_us: int = 0
    hold_us: int = 0
    received_new: bool = False


def _now_us() -> int:
    return time.time_ns() // 1000


def _stream_id(value: Any, path: str) -> str:
    if not isinstance(value, str) or not _STREAM_RE.fullmatch(value):
        raise validation(f"{path} must be a 64-bit lowercase hexadecimal string")
    return value


def _normalize_channel_value(raw: Any, path: str, now_us: int, captured_at_us: int | None) -> ValueEnvelope:
    if hasattr(raw, "value") and hasattr(raw, "state") and hasattr(raw, "confidence"):
        value, state, confidence = raw.value, raw.state, raw.confidence
    elif isinstance(raw, Mapping):
        try:
            value, state, confidence = raw["value"], raw["state"], raw["confidence"]
        except KeyError as exc:
            raise validation(f"{path} requires value, state and confidence") from exc
    elif isinstance(raw, (list, tuple)) and len(raw) == 3:
        value, state, confidence = raw
    else:
        raise validation(f"{path} must be a (value, state, confidence) envelope")
    state_names = {0: OBSERVED, 1: HELD, 2: INVALID, OBSERVED: OBSERVED, HELD: HELD, INVALID: INVALID}
    if isinstance(state, bool) or state not in state_names:
        raise validation(f"{path}.state is invalid")
    state_name = state_names[state]
    number = finite(value, f"{path}.value")
    confidence_number = finite(confidence, f"{path}.confidence")
    if not 0 <= confidence_number <= 1:
        raise validation(f"{path}.confidence must be in [0,1]")
    if state_name == INVALID:
        if number != 0.0:
            raise validation(f"{path} invalid state requires the 0.0 sentinel")
        confidence_number = 0.0
    return ValueEnvelope(number, state_name, confidence_number, now_us, captured_at_us)


class WeaverEngine:
    """Minimum complete headless router described by ``CORE_DESIGN.md``."""

    def __init__(
        self,
        *,
        transport: OutputTransport | None = None,
        report_writer: ReportWriter | None = None,
        clock_us: Callable[[], int] = _now_us,
    ) -> None:
        self._lock = threading.RLock()
        self._clock_us = clock_us
        self._state = StageState()
        self._sources: dict[str, SourceStatus] = {}
        self._instruments: dict[str, InstrumentStatus] = {}
        self._values: dict[str, ValueEnvelope] = {}
        self._compiled_scene: CompiledScene | None = None
        self._route_runtime: dict[str, RouteRuntime] = {}
        self._aggregator_runtime: dict[str, AggregatorRuntime] = {}
        self._last_outputs: dict[tuple[Any, ...], float] = {}
        self._transitions: dict[tuple[Any, ...], TransitionRuntime] = {}
        self._driver_seq: dict[str, int] = {}
        self._callbacks: dict[str, InstrumentSendCallback] = {}
        self.transport = transport or RecordingOutputTransport()
        self.report_writer = report_writer
        self._event_seq = 0
        self._events: list[EventRecord] = []
        self._listeners: set[Callable[[EventRecord], None]] = set()
        self.metrics = {
            "frames_accepted": 0,
            "frames_dropped": 0,
            "route_evaluations": 0,
            "instrument_writes": 0,
            "validation_rejections": 0,
            "transport_errors": 0,
        }

    @property
    def stage_revision(self) -> int:
        return self._state.revision

    @property
    def activation_generation(self) -> int:
        return self._state.activation_generation

    @property
    def panic_generation(self) -> int:
        return self._state.panic.generation

    @property
    def panic_active(self) -> bool:
        return self._state.panic.active

    @property
    def active_scene_id(self) -> str | None:
        return self._state.active_scene_id

    @property
    def event_seq(self) -> int:
        return self._event_seq

    @property
    def events(self) -> list[EventRecord]:
        with self._lock:
            return list(self._events)

    def add_event_listener(self, listener: Callable[[EventRecord], None]) -> Callable[[], None]:
        with self._lock:
            self._listeners.add(listener)

        def remove() -> None:
            with self._lock:
                self._listeners.discard(listener)

        return remove

    def _publish(self, event_type: str, payload: Mapping[str, Any], *, revision: int | None = None) -> EventRecord:
        self._event_seq += 1
        event = EventRecord(
            self._event_seq,
            self._state.revision if revision is None else revision,
            event_type,
            freeze(dict(payload)),
            self._clock_us(),
        )
        self._events.append(event)
        if len(self._events) > 4096:
            del self._events[: len(self._events) - 4096]
        if self.report_writer is not None:
            self.report_writer.behavior_event(event.as_dict())
        for listener in tuple(self._listeners):
            try:
                listener(event)
            except Exception:
                continue
        return event

    def _advance_revision(self) -> None:
        self._state = replace(self._state, revision=self._state.revision + 1)

    def _check_revision(self, expected: Any) -> None:
        if isinstance(expected, bool) or not isinstance(expected, int) or expected != self._state.revision:
            raise WeaverError(
                "revision_conflict",
                f"expected stage revision {expected!r}, current revision is {self._state.revision}",
                current_stage_revision=self._state.revision,
            )

    def _instrument_manifests(self) -> dict[str, Mapping[str, Any]]:
        return {instrument_id: status.manifest for instrument_id, status in self._instruments.items()}

    def _base_channel_ranges(self) -> dict[str, tuple[float, float]]:
        result: dict[str, tuple[float, float]] = {}
        for source_id, status in self._sources.items():
            if status.kind != "external":
                continue
            for channel in status.manifest.get("channels", ()):
                result[f"{source_id}.{channel['name']}"] = tuple(channel["range"])  # type: ignore[assignment]
        return result

    def _manifest_capability(self, instrument_id: str, capability_name: str) -> Mapping[str, Any]:
        status = self._instruments.get(instrument_id)
        if status is None:
            raise WeaverError("capability_missing", f"unknown instrument {instrument_id!r}")
        for capability in status.manifest.get("capabilities", ()):
            if capability.get("name") == capability_name:
                return capability
        raise WeaverError("capability_missing", f"unknown capability {instrument_id}.{capability_name}")

    def _normalize_profile_write(self, instrument_id: str, raw: Any, path: str) -> dict[str, Any]:
        if not isinstance(raw, Mapping):
            raise validation(f"{path} must be an object")
        if "destination" in raw:
            if not isinstance(raw["destination"], Mapping):
                raise validation(f"{path}.destination must be an object")
            merged = dict(raw["destination"])
            merged["value"] = raw.get("value")
            if "ramp_ms" in raw:
                merged["ramp_ms"] = raw["ramp_ms"]
            raw = merged
        for key in ("capability", "bindings", "argument", "value"):
            if key not in raw:
                raise validation(f"{path} missing {key}")
        capability_name = identifier(raw["capability"], f"{path}.capability")
        capability = self._manifest_capability(instrument_id, capability_name)
        if capability.get("write") is not True:
            raise WeaverError("unsafe_instrument", f"{path} references non-writable capability")
        bindings = raw["bindings"]
        if not isinstance(bindings, Mapping) or set(bindings) != set(capability.get("parameters", {})):
            raise validation(f"{path}.bindings must bind every placeholder")
        clean_bindings: dict[str, int] = {}
        for name, spec in capability.get("parameters", {}).items():
            value = bindings[name]
            if isinstance(value, bool) or not isinstance(value, int):
                raise validation(f"{path}.bindings.{name} must be an integer")
            low, high = spec["bounds"]
            if not low <= value <= high:
                raise validation(f"{path}.bindings.{name} is outside bounds")
            clean_bindings[name] = value
        argument_name = identifier(raw["argument"], f"{path}.argument")
        argument = next((item for item in capability.get("arguments", ()) if item.get("name") == argument_name), None)
        if argument is None or "range" not in argument:
            raise validation(f"{path}.argument is not a numeric declared argument")
        value_number = finite(raw["value"], f"{path}.value")
        low, high = argument["range"]
        if not low <= value_number <= high:
            raise validation(f"{path}.value is outside [{low}, {high}]")
        if argument["type"] in {"int32", "int64"}:
            if not value_number.is_integer():
                raise validation(f"{path}.value must be integral")
            clean_value: float | int = int(value_number)
        else:
            clean_value = value_number
        clean = {
            "capability": capability_name,
            "bindings": clean_bindings,
            "argument": argument_name,
            "value": clean_value,
        }
        if "ramp_ms" in raw:
            clean["ramp_ms"] = finite(raw["ramp_ms"], f"{path}.ramp_ms")
        return clean

    def _declared_action_names(self, manifest: Mapping[str, Any]) -> set[str]:
        return {
            item["name"]
            for item in manifest.get("actions", ())
            if isinstance(item, Mapping) and isinstance(item.get("name"), str)
        }

    def _validate_safety_profile(self, instrument_id: str, contract_id: str, profile: Any) -> dict[str, Any]:
        if not isinstance(profile, Mapping):
            raise validation("safety_profile must be an object")
        validate_json_finite(profile, "safety_profile")
        for key in ("instrument_id", "instrument_contract_id", "instrument_class", "silence_actions", "reset_defaults", "rearm_fade_ms"):
            if key not in profile:
                raise validation(f"safety_profile missing {key}")
        if profile["instrument_id"] != instrument_id or profile["instrument_contract_id"] != contract_id:
            raise WeaverError("unsafe_instrument", "safety profile identity or contract_id mismatch")
        instrument_class = profile["instrument_class"]
        if instrument_class not in {"sustained_processor", "polyphonic_instrument", "control_only"}:
            raise validation("safety_profile.instrument_class is invalid")
        rearm = finite(profile["rearm_fade_ms"], "safety_profile.rearm_fade_ms")
        if rearm < 250:
            raise validation("safety_profile.rearm_fade_ms must be at least 250")
        clean = copy.deepcopy(dict(profile))
        reset_raw = profile["reset_defaults"]
        if not isinstance(reset_raw, list) or not reset_raw:
            raise validation("safety_profile.reset_defaults must be a non-empty array")
        clean["reset_defaults"] = [self._normalize_profile_write(instrument_id, item, f"safety_profile.reset_defaults[{index}]") for index, item in enumerate(reset_raw)]
        silence_raw = profile["silence_actions"]
        if not isinstance(silence_raw, list):
            raise validation("safety_profile.silence_actions must be an array")
        silence: list[dict[str, Any]] = []
        declared_actions = self._declared_action_names(self._instruments[instrument_id].manifest)
        for index, item in enumerate(silence_raw):
            if isinstance(item, Mapping) and "action" in item:
                if item["action"] not in declared_actions:
                    raise WeaverError("unsafe_instrument", f"undeclared native action {item['action']!r}")
                silence.append({"action": item["action"]})
            else:
                write = self._normalize_profile_write(instrument_id, item, f"safety_profile.silence_actions[{index}]")
                if float(write.get("ramp_ms", 0.0)) > 20.0:
                    raise validation("audio silence ramp must be no more than 20 ms")
                silence.append(write)
        clean["silence_actions"] = silence
        if instrument_class in {"sustained_processor", "polyphonic_instrument"} and not silence:
            raise WeaverError("unsafe_instrument", "audio safety profile requires silence_actions")
        if instrument_class == "polyphonic_instrument":
            for key in ("release_all_action", "force_all_off_action", "release_grace_ms"):
                if key not in profile:
                    raise validation(f"polyphonic safety profile missing {key}")
            if profile["release_all_action"] not in declared_actions or profile["force_all_off_action"] not in declared_actions:
                raise WeaverError("unsafe_instrument", "polyphonic safety actions are not declared by the manifest")
            grace = finite(profile["release_grace_ms"], "safety_profile.release_grace_ms")
            if not 0 <= grace <= 500:
                raise validation("release_grace_ms must be in [0,500]")
        return clean

    def _safety_defaults(self) -> dict[tuple[Any, ...], float | int]:
        defaults: dict[tuple[Any, ...], float | int] = {}
        for instrument_id, status in self._instruments.items():
            if status.safety_profile is None:
                continue
            for item in status.safety_profile["reset_defaults"]:
                destination = {
                    "instrument_id": instrument_id,
                    "capability": item["capability"],
                    "bindings": thaw(item["bindings"]),
                    "argument": item["argument"],
                }
                defaults[destination_key(destination)] = item["value"]
        return defaults

    def install_source_manifest(self, manifest: Mapping[str, Any]) -> str:
        candidate = copy.deepcopy(dict(manifest))
        try:
            validate_manifest(candidate)
        except ContractValidationError as exc:
            raise validation(str(exc)) from exc
        if candidate["contract_type"] != "source_frame":
            raise validation("source installation requires a Source Frame manifest")
        source_id = candidate["source"]["source_id"]
        contract_id = candidate.get("contract_id") or contract_id_from_manifest(candidate)
        with self._lock:
            if source_id in self._sources:
                raise WeaverError("already_exists", f"source {source_id!r} is already installed")
            status = SourceStatus(
                source_id,
                "external",
                contract_id,
                freeze(candidate),
                lease_ms=float(candidate["presence"]["lease_ms"]),
            )
            self._sources[source_id] = status
            installed_at_us = self._clock_us()
            for channel in candidate["channels"]:
                self._values[f"{source_id}.{channel['name']}"] = ValueEnvelope.invalid(
                    installed_at_us
                )
            self._advance_revision()
            self._publish("registry.source", self._source_event(status, "installed"))
            if self.report_writer is not None:
                self.report_writer.accept_contract("sources", source_id, contract_id)
            return contract_id

    install_source = install_source_manifest

    def source_hello(self, source_id: str, stream_id: str, contract_id: str, *, now_us: int | None = None) -> bool:
        now = self._clock_us() if now_us is None else now_us
        _stream_id(stream_id, "stream_id")
        with self._lock:
            status = self._sources.get(source_id)
            if status is None or status.kind != "external":
                raise WeaverError("not_found", f"source {source_id!r} is not installed")
            changed_stream = status.stream_id is not None and status.stream_id != stream_id
            if contract_id != status.expected_contract_id:
                status = replace(status, gate_state="incompatible", runtime_contract_id=contract_id, stream_id=stream_id, last_frame_seq=-1, lease_deadline_us=None, reason="contract_id mismatch")
                self._invalidate_source_values(source_id, now)
                self._sources[source_id] = status
                self._advance_revision()
                self._publish("registry.source", self._source_event(status, "hello_rejected"))
                return False
            if changed_stream:
                self._invalidate_source_values(source_id, now)
                self._driver_seq[source_id] = -1
            status = replace(status, gate_state="ready", runtime_contract_id=contract_id, stream_id=stream_id, last_frame_seq=-1 if changed_stream or status.stream_id is None else status.last_frame_seq, lease_deadline_us=now + int(float(status.lease_ms or 0) * 1000), reason=None)
            self._sources[source_id] = status
            self._advance_revision()
            self._publish("registry.source", self._source_event(status, "stream_changed" if changed_stream else "hello_accepted"))
            return True

    def _source_event(self, status: SourceStatus, action: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source_id": status.source_id,
            "kind": status.kind,
            "action": action,
            "gate_state": status.gate_state,
            "expected_contract_id": status.expected_contract_id,
        }
        for key in ("runtime_contract_id", "stream_id", "reason"):
            value = getattr(status, key)
            if value is not None:
                payload[key] = value
        return payload

    def _invalidate_source_values(self, source_id: str, now_us: int) -> set[str]:
        changed: set[str] = set()
        prefix = source_id + "."
        for address in list(self._values):
            if address.startswith(prefix):
                self._values[address] = ValueEnvelope.invalid(now_us)
                changed.add(address)
        return changed

    def ingest_source_frame(
        self,
        source_id: str,
        stream_id: str,
        contract_id: str,
        frame_seq: int,
        channel_values: Mapping[str, Any],
        *,
        captured_at_us: int | None = None,
        now_us: int | None = None,
    ) -> bool:
        receipt_perf_ns = time.perf_counter_ns()
        now = self._clock_us() if now_us is None else now_us
        if captured_at_us is not None and (
            isinstance(captured_at_us, bool)
            or not isinstance(captured_at_us, int)
            or captured_at_us < 0
        ):
            raise validation("captured_at_us must be a non-negative integer")
        if isinstance(frame_seq, bool) or not isinstance(frame_seq, int) or frame_seq < 0:
            raise validation("frame_seq must be an unsigned integer")
        with self._lock:
            status = self._sources.get(source_id)
            if status is None:
                raise WeaverError("not_found", f"source {source_id!r} is not installed")
            if status.kind != "external" or status.gate_state != "ready" or status.stream_id != stream_id or status.runtime_contract_id != contract_id:
                self.metrics["frames_dropped"] += 1
                if self.report_writer is not None:
                    self.report_writer.count("drops")
                return False
            if frame_seq <= status.last_frame_seq:
                self.metrics["frames_dropped"] += 1
                if self.report_writer is not None:
                    self.report_writer.count("drops")
                return False
            declared = {item["name"]: tuple(item["range"]) for item in status.manifest["channels"]}
            if set(channel_values) != set(declared):
                self.metrics["frames_dropped"] += 1
                raise validation("source frame must contain exactly every declared channel")
            normalized: dict[str, ValueEnvelope] = {}
            for channel_name, raw in channel_values.items():
                envelope = _normalize_channel_value(raw, f"channels.{channel_name}", now, captured_at_us)
                low, high = declared[channel_name]
                if envelope.state != INVALID and not low <= envelope.value <= high:
                    raise validation(f"channels.{channel_name}.value is outside [{low}, {high}]")
                address = f"{source_id}.{channel_name}"
                previous = self._values.get(address)
                if (
                    envelope.state == HELD
                    and previous is not None
                    and previous.state == HELD
                    and envelope.value == previous.value
                    and envelope.confidence > previous.confidence + 1e-12
                ):
                    raise validation(f"channels.{channel_name}.confidence must decay monotonically while held")
                normalized[address] = envelope
            self._values.update(normalized)
            status = replace(status, last_frame_seq=frame_seq, lease_deadline_us=now + int(float(status.lease_ms or 0) * 1000))
            self._sources[source_id] = status
            self.metrics["frames_accepted"] += 1
            if self.report_writer is not None:
                self.report_writer.trace({"phase": "source_received", "source_id": source_id, "stream_id": stream_id, "frame_seq": frame_seq, "received_at_us": now, "captured_at_us": captured_at_us})
            self._run_tick_locked(now, set(normalized), receipt_perf_ns=receipt_perf_ns, input_changed=True)
            return True

    ingest_frame = ingest_source_frame

    def ingest_driver_frame(self, source_id: str, channel_values: Mapping[str, Any]) -> None:
        """Existing-driver callback seam: ``on_frame(source_id, channel_values)``."""

        with self._lock:
            status = self._sources.get(source_id)
            if status is None or status.gate_state != "ready" or status.stream_id is None or status.runtime_contract_id is None:
                self.metrics["frames_dropped"] += 1
                return
            sequence = max(status.last_frame_seq, self._driver_seq.get(source_id, -1)) + 1
            self._driver_seq[source_id] = sequence
            stream_id = status.stream_id
            contract_id = status.runtime_contract_id
        self.ingest_source_frame(source_id, stream_id, contract_id, sequence, channel_values)

    driver_callback = ingest_driver_frame
    on_frame = ingest_driver_frame

    def install_instrument_manifest(
        self,
        manifest: Mapping[str, Any],
        safety_profile: Mapping[str, Any] | None = None,
        *,
        send_callback: InstrumentSendCallback | None = None,
    ) -> str:
        candidate = copy.deepcopy(dict(manifest))
        try:
            validate_manifest(candidate)
        except ContractValidationError as exc:
            raise validation(str(exc)) from exc
        if candidate["contract_type"] != "instrument_control":
            raise validation("instrument installation requires an Instrument Control manifest")
        instrument_id = candidate["instrument"]["instrument_id"]
        contract_id = candidate.get("contract_id") or contract_id_from_manifest(candidate)
        with self._lock:
            if instrument_id in self._instruments:
                raise WeaverError("already_exists", f"instrument {instrument_id!r} is already installed")
            provisional = InstrumentStatus(instrument_id, contract_id, freeze(candidate), None, "missing")
            self._instruments[instrument_id] = provisional
            try:
                clean_profile = None if safety_profile is None else self._validate_safety_profile(instrument_id, contract_id, safety_profile)
            except Exception:
                del self._instruments[instrument_id]
                raise
            status = replace(provisional, safety_profile=freeze(clean_profile) if clean_profile is not None else None, safety_state="valid" if clean_profile is not None else "missing")
            self._instruments[instrument_id] = status
            if send_callback is not None:
                self._callbacks[instrument_id] = send_callback
            self._advance_revision()
            self._publish("registry.instrument", self._instrument_event(status, "installed"))
            if self.report_writer is not None:
                self.report_writer.accept_contract("instruments", instrument_id, contract_id)
            return contract_id

    install_instrument = install_instrument_manifest

    def instrument_hello(self, instrument_id: str, stream_id: str, contract_id: str) -> bool:
        _stream_id(stream_id, "stream_id")
        with self._lock:
            status = self._instruments.get(instrument_id)
            if status is None:
                raise WeaverError("not_found", f"instrument {instrument_id!r} is not installed")
            changed_stream = status.stream_id is not None and status.stream_id != stream_id
            if contract_id != status.expected_contract_id:
                status = replace(status, gate_state="incompatible", runtime_contract_id=contract_id, stream_id=stream_id, state_synced=False, reason="contract_id mismatch")
                self._instruments[instrument_id] = status
                self._advance_revision()
                self._publish("registry.instrument", self._instrument_event(status, "hello_rejected"))
                return False
            if (
                status.stream_id == stream_id
                and status.runtime_contract_id == contract_id
                and status.state_synced
            ):
                self._advance_revision()
                self._publish("registry.instrument", self._instrument_event(status, "hello_accepted"))
                return True
            status = replace(status, gate_state="gated", runtime_contract_id=contract_id, stream_id=stream_id, state_synced=False, reason="state synchronization incomplete")
            self._instruments[instrument_id] = status
            self._advance_revision()
            self._publish("registry.instrument", self._instrument_event(status, "stream_changed" if changed_stream else "hello_accepted"))
            return True

    def instrument_sync_complete(self, instrument_id: str, stream_id: str, contract_id: str) -> bool:
        with self._lock:
            status = self._instruments.get(instrument_id)
            if status is None:
                raise WeaverError("not_found", f"instrument {instrument_id!r} is not installed")
            if status.stream_id != stream_id or status.runtime_contract_id != contract_id or contract_id != status.expected_contract_id:
                raise WeaverError("contract_mismatch", "instrument synchronization tuple does not match the accepted hello")
            if status.safety_profile is None:
                raise WeaverError("unsafe_instrument", f"instrument {instrument_id!r} has no valid safety profile")
            status = replace(status, gate_state="ready", state_synced=True, safety_state="safe" if self._state.panic.active else "valid", reason=None)
            self._instruments[instrument_id] = status
            outcome: str | None = None
            if self._state.panic.active:
                outcome = self._panic_instrument(instrument_id)
                if outcome != "ok":
                    status = replace(
                        status,
                        gate_state="gated",
                        safety_state="degraded",
                        reason="panic safety dispatch failed",
                    )
                    self._instruments[instrument_id] = status
            self._advance_revision()
            if outcome is not None:
                self._publish("panic.event", {"panic_generation": self._state.panic.generation, "phase": "instrument_result", "instrument_id": instrument_id, "outcome": outcome})
            self._publish("registry.instrument", self._instrument_event(status, "sync_completed"))
            return status.gate_state == "ready"

    complete_instrument_sync = instrument_sync_complete

    def instrument_disconnected(self, instrument_id: str, *, reason: str = "disconnected") -> None:
        with self._lock:
            status = self._instruments.get(instrument_id)
            if status is None:
                raise WeaverError("not_found", f"instrument {instrument_id!r} is not installed")
            status = replace(status, gate_state="absent", state_synced=False, reason=reason)
            self._instruments[instrument_id] = status
            self._advance_revision()
            self._publish("registry.instrument", self._instrument_event(status, "disconnected"))

    def _instrument_event(self, status: InstrumentStatus, action: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "instrument_id": status.instrument_id,
            "action": action,
            "gate_state": status.gate_state,
            "expected_contract_id": status.expected_contract_id,
            "safety_state": status.safety_state,
        }
        for key in ("runtime_contract_id", "stream_id", "reason"):
            value = getattr(status, key)
            if value is not None:
                payload[key] = value
        return payload

    def _preflight_runtime_contracts(self, compiled: CompiledScene) -> None:
        for route in compiled.routes:
            instrument = self._instruments[route.destination.definition["instrument_id"]]
            if instrument.gate_state == "incompatible":
                raise WeaverError("contract_mismatch", f"instrument {instrument.instrument_id!r} has an incompatible runtime contract")
            if instrument.safety_profile is None:
                raise WeaverError("unsafe_instrument", f"instrument {instrument.instrument_id!r} has no valid safety profile")
        external_source_ids = {
            item.split(".", 1)[0]
            for route in compiled.routes
            for item in route.inputs
            if item.split(".", 1)[0] in self._sources and self._sources[item.split(".", 1)[0]].kind == "external"
        }
        for source_id in external_source_ids:
            if self._sources[source_id].gate_state == "incompatible":
                raise WeaverError("contract_mismatch", f"source {source_id!r} has an incompatible runtime contract")

    def _compile_scene(self, scene: Mapping[str, Any]) -> CompiledScene:
        compiled = compile_scene(thaw(scene), self._base_channel_ranges(), self._instrument_manifests(), self._safety_defaults())
        external_ids = {
            source_id
            for source_id, status in self._sources.items()
            if status.kind == "external"
        }
        for aggregator in compiled.aggregators:
            if aggregator.definition["derived_source_id"] in external_ids:
                raise validation(
                    f"derived_source_id {aggregator.definition['derived_source_id']!r} collides with an installed source"
                )
        self._preflight_runtime_contracts(compiled)
        return compiled

    def upsert_scene(self, scene: Mapping[str, Any], expected_stage_revision: int, *, expected_scene_version: int | None = None) -> dict[str, Any]:
        started = time.perf_counter_ns()
        with self._lock:
            self._check_revision(expected_stage_revision)
            candidate = copy.deepcopy(dict(scene))
            scene_id = candidate.get("scene_id")
            existing = self._state.scenes.get(scene_id) if isinstance(scene_id, str) else None
            if existing is None:
                if candidate.get("scene_version") != 1:
                    raise validation("new scenes must start at scene_version 1")
                if expected_scene_version is not None:
                    raise validation("expected_scene_version must be omitted for scene creation")
            else:
                if expected_scene_version != existing["scene_version"]:
                    raise WeaverError("revision_conflict", "scene version conflict", current_stage_revision=self._state.revision)
                if candidate.get("scene_version") != expected_scene_version + 1:
                    raise validation("replacement scene_version must increment exactly once")
            compiled = self._compile_scene(candidate)
            scenes = thaw(self._state.scenes)
            scenes[scene_id] = candidate
            active_change = self._state.active_scene_id == scene_id and not self._state.panic.active
            generation = self._state.activation_generation + (1 if active_change else 0)
            self._state = replace(self._state, revision=self._state.revision + 1, activation_generation=generation, scenes=freeze(scenes))
            if active_change:
                self._activate_compiled(compiled, self._clock_us())
            self._publish("state.event", {"topic": "scenes", "action": "scene.upserted", "entity_id": scene_id, "entity": candidate, **({"activation_generation": generation} if active_change else {})})
            self._record_mutation(started)
            return self._ack("scene.upsert", active_change)

    scene_upsert = upsert_scene

    def delete_scene(self, scene_id: str, expected_scene_version: int, expected_stage_revision: int) -> dict[str, Any]:
        with self._lock:
            self._check_revision(expected_stage_revision)
            if scene_id == self._state.active_scene_id:
                raise validation("the active scene cannot be deleted")
            existing = self._state.scenes.get(scene_id)
            if existing is None:
                raise WeaverError("not_found", f"scene {scene_id!r} was not found")
            if existing["scene_version"] != expected_scene_version:
                raise WeaverError("revision_conflict", "scene version conflict", current_stage_revision=self._state.revision)
            scenes = thaw(self._state.scenes)
            del scenes[scene_id]
            self._state = replace(self._state, revision=self._state.revision + 1, scenes=freeze(scenes))
            self._publish("state.event", {"topic": "scenes", "action": "scene.deleted", "entity_id": scene_id, "entity": thaw(existing)})
            return self._ack("scene.delete", False)

    scene_delete = delete_scene

    def _route_transaction(self, command: str, scene_id: str, expected_stage_revision: int, mutator: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
        started = time.perf_counter_ns()
        with self._lock:
            self._check_revision(expected_stage_revision)
            existing = self._state.scenes.get(scene_id)
            if existing is None:
                raise WeaverError("not_found", f"scene {scene_id!r} was not found")
            scene = thaw(existing)
            mutator(scene)
            scene["scene_version"] += 1
            scene["updated_at_us"] = self._clock_us()
            compiled = self._compile_scene(scene)
            scenes = thaw(self._state.scenes)
            scenes[scene_id] = scene
            active_change = self._state.active_scene_id == scene_id and not self._state.panic.active
            generation = self._state.activation_generation + (1 if active_change else 0)
            self._state = replace(self._state, revision=self._state.revision + 1, activation_generation=generation, scenes=freeze(scenes))
            if active_change:
                self._activate_compiled(compiled, self._clock_us())
            action = {"route.create": "route.created", "route.update": "route.updated", "route.delete": "route.deleted"}[command]
            entity_id = getattr(mutator, "entity_id", None)
            committed_route = next(
                (item for item in scene["routes"] if item.get("route_id") == entity_id),
                None,
            )
            audit_entity = committed_route or getattr(
                mutator,
                "deleted_entity",
                {"scene_id": scene_id, "route_id": entity_id},
            )
            self._publish("state.event", {"topic": "routes", "action": action, "entity_id": entity_id, "entity": audit_entity, "activation_generation": generation if active_change else self._state.activation_generation})
            self._record_mutation(started)
            return self._ack(command, active_change)

    def create_route(self, scene_id: str, route: Mapping[str, Any], expected_stage_revision: int) -> dict[str, Any]:
        candidate = copy.deepcopy(dict(route))

        def mutate(scene: dict[str, Any]) -> None:
            if candidate.get("route_version") != 1:
                raise validation("new routes must start at route_version 1")
            if any(item.get("route_id") == candidate.get("route_id") for item in scene["routes"]):
                raise WeaverError("already_exists", f"route {candidate.get('route_id')!r} already exists")
            scene["routes"].append(candidate)

        mutate.entity_id = candidate.get("route_id")  # type: ignore[attr-defined]
        return self._route_transaction("route.create", scene_id, expected_stage_revision, mutate)

    route_create = create_route

    def update_route(self, scene_id: str, route_id: str, expected_route_version: int, route: Mapping[str, Any], expected_stage_revision: int) -> dict[str, Any]:
        candidate = copy.deepcopy(dict(route))

        def mutate(scene: dict[str, Any]) -> None:
            if candidate.get("route_id") != route_id:
                raise validation("route_id must equal route.route_id")
            for index, existing in enumerate(scene["routes"]):
                if existing.get("route_id") == route_id:
                    if existing["route_version"] != expected_route_version:
                        raise WeaverError("revision_conflict", "route version conflict", current_stage_revision=self._state.revision)
                    if candidate.get("route_version") != expected_route_version + 1:
                        raise validation("route_version must increment exactly once")
                    scene["routes"][index] = candidate
                    return
            raise WeaverError("not_found", f"route {route_id!r} was not found")

        mutate.entity_id = route_id  # type: ignore[attr-defined]
        return self._route_transaction("route.update", scene_id, expected_stage_revision, mutate)

    route_update = update_route

    def delete_route(self, scene_id: str, route_id: str, expected_route_version: int, expected_stage_revision: int) -> dict[str, Any]:
        def mutate(scene: dict[str, Any]) -> None:
            for index, existing in enumerate(scene["routes"]):
                if existing.get("route_id") == route_id:
                    if existing["route_version"] != expected_route_version:
                        raise WeaverError("revision_conflict", "route version conflict", current_stage_revision=self._state.revision)
                    mutate.deleted_entity = copy.deepcopy(existing)  # type: ignore[attr-defined]
                    del scene["routes"][index]
                    return
            raise WeaverError("not_found", f"route {route_id!r} was not found")

        mutate.entity_id = route_id  # type: ignore[attr-defined]
        return self._route_transaction("route.delete", scene_id, expected_stage_revision, mutate)

    route_delete = delete_route

    def route_batch(self, operations: Iterable[Mapping[str, Any]], expected_stage_revision: int) -> dict[str, Any]:
        started = time.perf_counter_ns()
        operations_list = list(operations)
        if not operations_list:
            raise validation("route.batch operations must be non-empty")
        with self._lock:
            self._check_revision(expected_stage_revision)
            scenes = thaw(self._state.scenes)
            touched: set[str] = set()
            audit: list[dict[str, Any]] = []
            for raw_op in operations_list:
                if not isinstance(raw_op, Mapping):
                    raise validation("route.batch operation must be an object")
                command = raw_op.get("type", raw_op.get("operation", raw_op.get("command")))
                payload = dict(raw_op.get("payload", {key: value for key, value in raw_op.items() if key not in {"type", "operation", "command"}}))
                if command not in {"route.create", "route.update", "route.delete"}:
                    raise validation("route.batch operation type is invalid")
                scene_id = payload.get("scene_id")
                if scene_id not in scenes:
                    raise WeaverError("not_found", f"scene {scene_id!r} was not found")
                scene = scenes[scene_id]
                if command == "route.create":
                    route = copy.deepcopy(payload.get("route"))
                    if not isinstance(route, dict) or route.get("route_version") != 1:
                        raise validation("batched new route must start at version 1")
                    if any(item["route_id"] == route.get("route_id") for item in scene["routes"]):
                        raise WeaverError("already_exists", f"route {route.get('route_id')!r} already exists")
                    scene["routes"].append(route)
                elif command == "route.update":
                    route_id = payload.get("route_id")
                    replacement = copy.deepcopy(payload.get("route"))
                    found = False
                    for index, existing in enumerate(scene["routes"]):
                        if existing["route_id"] == route_id:
                            found = True
                            expected = payload.get("expected_route_version")
                            if existing["route_version"] != expected or not isinstance(replacement, dict) or replacement.get("route_id") != route_id or replacement.get("route_version") != expected + 1:
                                raise WeaverError("revision_conflict", "batched route version conflict", current_stage_revision=self._state.revision)
                            scene["routes"][index] = replacement
                            break
                    if not found:
                        raise WeaverError("not_found", f"route {route_id!r} was not found")
                else:
                    route_id = payload.get("route_id")
                    found = False
                    for index, existing in enumerate(scene["routes"]):
                        if existing["route_id"] == route_id:
                            found = True
                            if existing["route_version"] != payload.get("expected_route_version"):
                                raise WeaverError("revision_conflict", "batched route version conflict", current_stage_revision=self._state.revision)
                            del scene["routes"][index]
                            break
                    if not found:
                        raise WeaverError("not_found", f"route {route_id!r} was not found")
                touched.add(scene_id)
                audit.append({"type": command, "scene_id": scene_id, "route_id": payload.get("route_id", payload.get("route", {}).get("route_id"))})
            compiled_by_scene: dict[str, CompiledScene] = {}
            for scene_id in touched:
                scenes[scene_id]["scene_version"] += 1
                scenes[scene_id]["updated_at_us"] = self._clock_us()
                compiled_by_scene[scene_id] = self._compile_scene(scenes[scene_id])
            active_change = self._state.active_scene_id in touched and not self._state.panic.active
            generation = self._state.activation_generation + (1 if active_change else 0)
            self._state = replace(self._state, revision=self._state.revision + 1, activation_generation=generation, scenes=freeze(scenes))
            if active_change:
                self._activate_compiled(compiled_by_scene[self._state.active_scene_id], self._clock_us())  # type: ignore[index]
            self._publish("state.event", {"topic": "routes", "action": "route.batch_committed", "entity": {"operations": copy.deepcopy(operations_list), "audit": audit, "resulting_scene_versions": {scene_id: scenes[scene_id]["scene_version"] for scene_id in touched}}, "activation_generation": generation if active_change else self._state.activation_generation})
            self._record_mutation(started)
            return self._ack("route.batch", active_change)

    def switch_scene(self, scene_id: str, expected_scene_version: int, expected_stage_revision: int) -> dict[str, Any]:
        started = time.perf_counter_ns()
        with self._lock:
            self._check_revision(expected_stage_revision)
            if self._state.panic.active:
                raise WeaverError("panic_latched", "scene switching is disabled while panic is latched")
            scene = self._state.scenes.get(scene_id)
            if scene is None:
                raise WeaverError("not_found", f"scene {scene_id!r} was not found")
            if scene["scene_version"] != expected_scene_version:
                raise WeaverError("revision_conflict", "scene version conflict", current_stage_revision=self._state.revision)
            compiled = self._compile_scene(scene)
            generation = self._state.activation_generation + 1
            self._state = replace(self._state, revision=self._state.revision + 1, activation_generation=generation, active_scene_id=scene_id)
            self._activate_compiled(compiled, self._clock_us())
            self._publish("state.event", {"topic": "stage", "action": "scene.switched", "entity_id": scene_id, "entity": thaw(scene), "activation_generation": generation})
            self._record_mutation(started)
            return self._ack("scene.switch", True)

    scene_switch = switch_scene

    def _transition_for(self, compiled: CompiledScene, destination: Mapping[str, Any]) -> dict[str, Any]:
        transition = compiled.definition["transition"]
        key = destination_key(destination)
        for override in transition.get("destination_overrides", ()):
            raw_destination = override.get("destination", override)
            try:
                if destination_key(raw_destination) == key:
                    return override.get("transition", override)
            except Exception:
                continue
        return transition

    def _activate_compiled(self, compiled: CompiledScene, now_us: int, *, recovery: bool = False) -> None:
        old_scene = self._compiled_scene
        old_routes = {route.route_id: route for route in old_scene.routes} if old_scene is not None else {}
        old_runtime = self._route_runtime
        new_runtime: dict[str, RouteRuntime] = {}
        for route in compiled.routes:
            previous = old_routes.get(route.route_id)
            if previous is not None and previous.canonical == route.canonical and not recovery:
                new_runtime[route.route_id] = old_runtime.get(route.route_id, RouteRuntime())
            else:
                new_runtime[route.route_id] = RouteRuntime()
        old_aggregators = {item.definition["aggregator_id"]: item for item in old_scene.aggregators} if old_scene is not None else {}
        new_aggregator_runtime: dict[str, AggregatorRuntime] = {}
        for aggregator in compiled.aggregators:
            aggregator_id = aggregator.definition["aggregator_id"]
            previous = old_aggregators.get(aggregator_id)
            if previous is not None and previous.definition == aggregator.definition and not recovery:
                new_aggregator_runtime[aggregator_id] = self._aggregator_runtime.get(aggregator_id, AggregatorRuntime())
            else:
                new_aggregator_runtime[aggregator_id] = AggregatorRuntime()
        self._route_runtime = new_runtime
        self._aggregator_runtime = new_aggregator_runtime
        self._transitions.clear()
        defaults = self._safety_defaults()
        new_destinations = {route.destination.key: route for route in compiled.routes if route.definition["enabled"]}
        old_destinations = {route.destination.key: route for route in old_scene.routes if route.definition["enabled"]} if old_scene is not None else {}
        affected = set(old_destinations) | set(new_destinations)
        for key in affected:
            old_route = old_destinations.get(key)
            new_route = new_destinations.get(key)
            unchanged = old_route is not None and new_route is not None and old_route.canonical == new_route.canonical
            if unchanged and not recovery:
                continue
            old_value = float(defaults.get(key, self._last_outputs.get(key, 0.0))) if recovery else self._last_outputs.get(key, float(defaults.get(key, 0.0)))
            if new_route is None:
                if key in defaults and old_route is not None:
                    self._send_destination(old_route.destination, defaults[key], now_us, "scene_reset", safety=False, receipt_perf_ns=None)
                continue
            if recovery:
                instrument = self._instruments[new_route.destination.definition["instrument_id"]]
                duration_ms = max(250.0, float(instrument.safety_profile["rearm_fade_ms"]))  # type: ignore[index]
                self._transitions[key] = TransitionRuntime("crossfade", old_value, now_us, int(duration_ms * 1000), int(duration_ms * 1000))
                continue
            policy = self._transition_for(compiled, new_route.destination.definition)
            if policy["policy"] == "reset":
                self._send_destination(new_route.destination, defaults[key], now_us, "scene_reset", safety=False, receipt_perf_ns=None)
            elif policy["policy"] == "held":
                self._transitions[key] = TransitionRuntime("held", old_value, now_us, hold_us=int(float(policy.get("hold_ms", 250.0)) * 1000))
            else:
                self._transitions[key] = TransitionRuntime("crossfade", old_value, now_us, duration_us=int(float(policy.get("duration_ms", 100.0)) * 1000), await_valid_us=int(float(policy.get("await_valid_ms", 250.0)) * 1000))
        self._compiled_scene = compiled
        self._materialize_derived(compiled)
        if self.report_writer is not None:
            self.report_writer.scene_snapshot(compiled.definition)

    def _materialize_derived(self, compiled: CompiledScene) -> None:
        desired = {item.definition["derived_source_id"]: item for item in compiled.aggregators}
        for source_id in [key for key, value in self._sources.items() if value.kind == "derived" and key not in desired]:
            status = self._sources.pop(source_id)
            self._invalidate_source_values(source_id, self._clock_us())
            self._publish("registry.source", self._source_event(replace(status, gate_state="absent", reason="removed from active scene"), "removed"))
        for source_id, aggregator in desired.items():
            pseudo_manifest = freeze({"derived_source_id": source_id, "channels": [{"name": aggregator.definition["output_channel"], "range": list(aggregator.output_range)}], "aggregator": aggregator.definition})
            previous = self._sources.get(source_id)
            status = SourceStatus(source_id, "derived", aggregator.contract_id, pseudo_manifest, gate_state="ready")
            self._sources[source_id] = status
            if previous is None or previous.expected_contract_id != aggregator.contract_id:
                self._invalidate_source_values(source_id, self._clock_us())
                self._values[aggregator.output_address] = ValueEnvelope.invalid(
                    self._clock_us()
                )
            self._publish("registry.source", self._source_event(status, "derived_ready"))
            if self.report_writer is not None:
                self.report_writer.accept_contract("derived", source_id, aggregator.contract_id)

    def tick(self, *, now_us: int | None = None) -> None:
        now = self._clock_us() if now_us is None else now_us
        with self._lock:
            changed: set[str] = set()
            for source_id, status in list(self._sources.items()):
                if status.kind == "external" and status.gate_state == "ready" and status.lease_deadline_us is not None and now > status.lease_deadline_us:
                    changed.update(self._invalidate_source_values(source_id, now))
                    expired = replace(status, gate_state="absent", reason="presence lease expired", lease_deadline_us=None)
                    self._sources[source_id] = expired
                    self._advance_revision()
                    self._publish("registry.source", self._source_event(expired, "lease_expired"))
            self._run_tick_locked(now, changed, receipt_perf_ns=None, input_changed=False)

    def _run_tick_locked(self, now_us: int, changed: set[str], *, receipt_perf_ns: int | None, input_changed: bool) -> None:
        compiled = self._compiled_scene
        if compiled is None:
            return
        derived_changed: set[str] = set()
        for aggregator in compiled.aggregators:
            runtime = self._aggregator_runtime[aggregator.definition["aggregator_id"]]
            cadence = aggregator.definition["cadence"]
            rate = float(cadence["rate_hz"] if cadence["mode"] == "fixed_hz" else cadence["max_rate_hz"])
            period_us = max(1, int(1_000_000 / rate))
            dependencies = {item["channel"] for item in aggregator.inputs}
            dependencies.update(item["include_when"]["channel"] for item in aggregator.inputs if "include_when" in item)
            if dependencies & (changed | derived_changed):
                runtime.pending_input = True
            due = now_us >= runtime.next_due_us
            should_compute = due and (
                cadence["mode"] == "fixed_hz" or runtime.pending_input
            )
            if should_compute:
                envelope = evaluate_aggregator(aggregator, runtime, self._values, now_us)
                previous = self._values.get(aggregator.output_address)
                self._values[aggregator.output_address] = envelope
                runtime.last_compute_us = now_us
                runtime.next_due_us = now_us + period_us
                runtime.pending_input = False
                if previous != envelope:
                    derived_changed.add(aggregator.output_address)
        all_changed = changed | derived_changed
        for route in compiled.routes:
            if not route.definition["enabled"]:
                continue
            runtime = self._route_runtime[route.route_id]
            needs_time = route.destination.key in self._transitions or route.definition["validity"]["invalid"] == "hold_then_reset"
            if not (set(route.inputs) & all_changed) and not needs_time:
                continue
            self.metrics["route_evaluations"] += 1
            value, reason = evaluate_route(route, runtime, self._values, now_us)
            if self.report_writer is not None:
                self.report_writer.trace({"phase": "route_evaluated", "route_id": route.route_id, "evaluated_at_us": now_us, "result": reason, "value": value})
            if reason == "reset":
                default = self._safety_defaults()[route.destination.key]
                self._send_destination(route.destination, default, now_us, "route_reset", safety=False, receipt_perf_ns=receipt_perf_ns)
            elif value is not None:
                self._dispatch_route_value(route, value, now_us, receipt_perf_ns)
        self._expire_transitions(now_us)

    def _dispatch_route_value(self, route: CompiledRoute, value: float, now_us: int, receipt_perf_ns: int | None) -> None:
        transition = self._transitions.get(route.destination.key)
        if transition is not None:
            if transition.policy == "held":
                transition.received_new = True
                del self._transitions[route.destination.key]
            else:
                transition.received_new = True
                fraction = 1.0 if transition.duration_us <= 0 else min(1.0, max(0.0, (now_us - transition.started_at_us) / transition.duration_us))
                value = transition.old_value + fraction * (value - transition.old_value)
                if fraction >= 1.0:
                    del self._transitions[route.destination.key]
        self._send_destination(route.destination, value, now_us, "route", safety=False, receipt_perf_ns=receipt_perf_ns)

    def _expire_transitions(self, now_us: int) -> None:
        if self._compiled_scene is None:
            return
        routes = {route.destination.key: route for route in self._compiled_scene.routes}
        defaults = self._safety_defaults()
        for key, transition in list(self._transitions.items()):
            timeout = transition.await_valid_us if transition.policy == "crossfade" else transition.hold_us
            if transition.received_new or now_us - transition.started_at_us < timeout:
                continue
            route = routes.get(key)
            if route is not None:
                self._send_destination(route.destination, defaults[key], now_us, "transition_timeout_reset", safety=False, receipt_perf_ns=None)
            del self._transitions[key]

    def _send_destination(self, destination: Any, value: float | int, now_us: int, reason: str, *, safety: bool, receipt_perf_ns: int | None) -> bool:
        instrument_id = destination.definition["instrument_id"]
        status = self._instruments[instrument_id]
        if not safety and (self._state.panic.active or status.gate_state != "ready" or not status.state_synced):
            return False
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            self.metrics["transport_errors"] += 1
            return False
        low, high = destination.value_range
        if not low <= float(value) <= high:
            self.metrics["transport_errors"] += 1
            return False
        native_value: float | int = int(value) if destination.argument_type in {"int32", "int64"} else float(value)
        if destination.argument_type in {"int32", "int64"} and not float(value).is_integer():
            self.metrics["transport_errors"] += 1
            return False
        record = OutputRecord(instrument_id, "capability", now_us, reason, destination.definition["capability"], destination.address, freeze(destination.definition["bindings"]), destination.definition["argument"], native_value)
        try:
            self.transport.send_capability(record)
            callback = self._callbacks.get(instrument_id)
            if callback is not None:
                callback(instrument_id, destination.definition["capability"], thaw(destination.definition["bindings"]), destination.definition["argument"], native_value)
        except Exception:
            self.metrics["transport_errors"] += 1
            if self.report_writer is not None:
                self.report_writer.count("errors")
            return False
        self.metrics["instrument_writes"] += 1
        self._last_outputs[destination.key] = float(native_value)
        if self.report_writer is not None:
            self.report_writer.trace({"phase": "instrument_sent", "instrument_id": instrument_id, "capability": destination.definition["capability"], "argument": destination.definition["argument"], "value": native_value, "sent_at_us": now_us, "reason": reason})
            if receipt_perf_ns is not None:
                self.report_writer.record_weaver_latency((time.perf_counter_ns() - receipt_perf_ns) / 1_000_000)
        return True

    def _profile_destination(self, instrument_id: str, item: Mapping[str, Any]) -> Any:
        capability = self._manifest_capability(instrument_id, item["capability"])
        address = capability["address_pattern"]
        for name, value in item["bindings"].items():
            address = address.replace("{" + name + "}", str(value))
        argument = next(arg for arg in capability["arguments"] if arg["name"] == item["argument"])
        definition = {"instrument_id": instrument_id, "capability": item["capability"], "bindings": thaw(item["bindings"]), "argument": item["argument"]}
        from .compiler import DestinationSpec

        return DestinationSpec(definition, destination_key(definition), argument["type"], tuple(argument["range"]), address)

    def _send_profile_item(self, instrument_id: str, item: Mapping[str, Any], reason: str) -> None:
        now = self._clock_us()
        if "action" in item:
            record = OutputRecord(instrument_id, "action", now, reason, action=item["action"])
            self.transport.invoke_action(record)
            return
        destination = self._profile_destination(instrument_id, item)
        if not self._send_destination(
            destination,
            item["value"],
            now,
            reason,
            safety=True,
            receipt_perf_ns=None,
        ):
            raise RuntimeError(f"failed to dispatch safety capability for {instrument_id}")

    def _invoke_profile_action(self, instrument_id: str, action: str, reason: str) -> None:
        if action not in self._declared_action_names(self._instruments[instrument_id].manifest):
            raise WeaverError("unsafe_instrument", f"native action {action!r} is not declared")
        self.transport.invoke_action(OutputRecord(instrument_id, "action", self._clock_us(), reason, action=action))

    def _panic_instrument(self, instrument_id: str) -> str:
        status = self._instruments[instrument_id]
        profile = status.safety_profile
        if profile is None:
            return "failed"
        try:
            instrument_class = profile["instrument_class"]
            if instrument_class == "polyphonic_instrument":
                self._invoke_profile_action(instrument_id, profile["release_all_action"], "panic_release_all")
            pinned_destinations: set[tuple[Any, ...]] = set()
            for item in profile["silence_actions"]:
                self._send_profile_item(instrument_id, item, "panic_silence")
                if "capability" in item:
                    pinned_destinations.add(
                        destination_key(
                            {
                                "instrument_id": instrument_id,
                                "capability": item["capability"],
                                "bindings": item["bindings"],
                                "argument": item["argument"],
                            }
                        )
                    )
            if instrument_class == "polyphonic_instrument":
                grace = float(profile["release_grace_ms"]) / 1000.0
                if grace > 0:
                    threading.Event().wait(grace)
                self._invoke_profile_action(instrument_id, profile["force_all_off_action"], "panic_force_all_off")
            for item in profile["reset_defaults"]:
                item_key = destination_key(
                    {
                        "instrument_id": instrument_id,
                        "capability": item["capability"],
                        "bindings": item["bindings"],
                        "argument": item["argument"],
                    }
                )
                if instrument_class != "control_only" and item_key in pinned_destinations:
                    continue
                self._send_profile_item(instrument_id, item, "panic_reset")
            return "ok"
        except Exception:
            return "failed"

    def trigger_panic(self, reason: str | None = None) -> dict[str, Any]:
        with self._lock:
            if self._state.panic.active:
                return {"command_type": "panic.trigger", "status": "already_latched", "panic_generation": self._state.panic.generation}
            generation = self._state.panic.generation + 1
            panic = PanicState(True, generation, reason, freeze({}))
            self._state = replace(self._state, revision=self._state.revision + 1, panic=panic)
            self._transitions.clear()
            self._publish("panic.event", {"panic_generation": generation, "phase": "latched", **({"reason": reason} if reason else {})})
            instrument_ids = list(self._instruments)
        outcomes: dict[str, str] = {}
        with ThreadPoolExecutor(max_workers=max(1, len(instrument_ids)), thread_name_prefix="weaver-panic") as executor:
            futures = {executor.submit(self._panic_instrument, instrument_id): instrument_id for instrument_id in instrument_ids}
            for future in as_completed(futures):
                instrument_id = futures[future]
                try:
                    outcomes[instrument_id] = future.result()
                except Exception:
                    outcomes[instrument_id] = "failed"
        with self._lock:
            for instrument_id, outcome in outcomes.items():
                status = self._instruments[instrument_id]
                self._instruments[instrument_id] = replace(
                    status,
                    safety_state="safe" if outcome == "ok" else "degraded",
                    reason=None if outcome == "ok" else "panic safety dispatch failed",
                )
            self._state = replace(self._state, revision=self._state.revision + 1, panic=replace(self._state.panic, outcomes=freeze(outcomes)))
            for instrument_id, outcome in outcomes.items():
                self._publish("panic.event", {"panic_generation": generation, "phase": "instrument_result", "instrument_id": instrument_id, "outcome": outcome})
            self._publish("panic.event", {"panic_generation": generation, "phase": "safe"})
            return {"command_type": "panic.trigger", "status": "latched", "panic_generation": generation}

    panic_trigger = trigger_panic

    def clear_panic(self, panic_generation: int, scene_id: str, expected_scene_version: int) -> dict[str, Any]:
        with self._lock:
            if not self._state.panic.active or panic_generation != self._state.panic.generation:
                raise WeaverError("revision_conflict", "panic_generation does not match the active latch", current_stage_revision=self._state.revision)
            try:
                scene = self._state.scenes.get(scene_id)
                if scene is None:
                    raise WeaverError("not_found", f"scene {scene_id!r} was not found")
                if scene["scene_version"] != expected_scene_version:
                    raise WeaverError("revision_conflict", "scene version conflict", current_stage_revision=self._state.revision)
                compiled = self._compile_scene(scene)
                for status in self._instruments.values():
                    if status.safety_profile is None:
                        raise WeaverError("unsafe_instrument", f"instrument {status.instrument_id!r} is unsafe")
                    if status.gate_state != "ready" or not status.state_synced or status.runtime_contract_id != status.expected_contract_id:
                        raise WeaverError("state_sync_incomplete", f"instrument {status.instrument_id!r} is not synchronized")
                self._publish("panic.event", {"panic_generation": panic_generation, "phase": "recovery_started"})
                for instrument_id, status in self._instruments.items():
                    for item in status.safety_profile["reset_defaults"]:  # type: ignore[index]
                        self._send_profile_item(instrument_id, item, "panic_recovery_default")
            except WeaverError as exc:
                self._publish("panic.event", {"panic_generation": panic_generation, "phase": "recovery_failed", "reason": exc.message})
                raise
            except Exception as exc:
                self._publish("panic.event", {"panic_generation": panic_generation, "phase": "recovery_failed", "reason": str(exc)})
                raise WeaverError("internal_error", "panic recovery safety dispatch failed") from exc
            generation = self._state.activation_generation + 1
            self._state = replace(self._state, revision=self._state.revision + 1, activation_generation=generation, active_scene_id=scene_id, panic=PanicState(False, panic_generation, None, self._state.panic.outcomes))
            self._activate_compiled(compiled, self._clock_us(), recovery=True)
            self._publish("panic.event", {"panic_generation": panic_generation, "phase": "recovered"})
            return {"command_type": "panic.clear", "status": "recovered", "panic_generation": panic_generation, "activation_generation": generation}

    panic_clear = clear_panic

    def _record_mutation(self, started_perf_ns: int) -> None:
        if self.report_writer is not None:
            self.report_writer.record_mutation_latency((time.perf_counter_ns() - started_perf_ns) / 1_000_000)

    def _ack(self, command: str, activation_changed: bool) -> dict[str, Any]:
        ack: dict[str, Any] = {"command_type": command, "status": "committed"}
        if activation_changed:
            ack["activation_generation"] = self._state.activation_generation
        return ack

    def snapshot(self, topics: Iterable[str] | None = None) -> dict[str, Any]:
        selected = set(topics or {"stage", "routes", "scenes", "sources", "instruments", "metrics"})
        with self._lock:
            result: dict[str, Any] = {
                "topics": sorted(selected),
                "snapshot_event_seq": self._event_seq,
                "stage": {
                    "active_scene_id": self._state.active_scene_id,
                    "activation_generation": self._state.activation_generation,
                    "panic": {
                        "active": self._state.panic.active,
                        "panic_generation": self._state.panic.generation,
                        "reason": self._state.panic.reason,
                        "outcomes": thaw(self._state.panic.outcomes),
                    },
                },
            }
            if "routes" in selected:
                active = self._state.scenes.get(self._state.active_scene_id) if self._state.active_scene_id else None
                route_snapshots: list[dict[str, Any]] = []
                if active is not None:
                    compiled_routes = {
                        route.route_id: route
                        for route in (self._compiled_scene.routes if self._compiled_scene else ())
                    }
                    for route_definition in thaw(active["routes"]):
                        compiled_route = compiled_routes.get(route_definition["route_id"])
                        instrument_ready = False
                        last_output: float | None = None
                        if compiled_route is not None:
                            instrument = self._instruments[
                                compiled_route.destination.definition["instrument_id"]
                            ]
                            instrument_ready = (
                                instrument.gate_state == "ready"
                                and instrument.state_synced
                            )
                            last_output = self._last_outputs.get(
                                compiled_route.destination.key
                            )
                        route_definition["runtime"] = {
                            "active": bool(
                                compiled_route is not None
                                and route_definition["enabled"]
                                and not self._state.panic.active
                                and instrument_ready
                            ),
                            "instrument_ready": instrument_ready,
                            "last_output": last_output,
                        }
                        route_snapshots.append(route_definition)
                result["routes"] = route_snapshots
            if "scenes" in selected:
                result["scenes"] = [thaw(scene) for _, scene in sorted(self._state.scenes.items())]
            if "sources" in selected:
                result["sources"] = [self._source_snapshot(status) for _, status in sorted(self._sources.items())]
            if "instruments" in selected:
                result["instruments"] = [self._instrument_snapshot(status) for _, status in sorted(self._instruments.items())]
            if "metrics" in selected:
                result["metrics"] = dict(self.metrics)
            return result

    def snapshot_transaction(
        self,
        topics: Iterable[str] | None = None,
    ) -> tuple[dict[str, Any], int, int]:
        """Capture one snapshot with its exact revision and event high-water."""

        with self._lock:
            snapshot = self.snapshot(topics)
            return snapshot, self._state.revision, self._event_seq

    def _source_snapshot(self, status: SourceStatus) -> dict[str, Any]:
        prefix = status.source_id + "."
        channels = {
            address[len(prefix) :]: {
                "value": envelope.value,
                "state": envelope.state,
                "confidence": envelope.confidence,
                "received_at_us": envelope.received_at_us,
                "captured_at_us": envelope.captured_at_us,
            }
            for address, envelope in self._values.items()
            if address.startswith(prefix)
        }
        return {
            "source_id": status.source_id,
            "kind": status.kind,
            "expected_contract_id": status.expected_contract_id,
            "runtime_contract_id": status.runtime_contract_id,
            "stream_id": status.stream_id,
            "gate_state": status.gate_state,
            "reason": status.reason,
            "last_frame_seq": status.last_frame_seq,
            "channels": channels,
        }

    def _instrument_snapshot(self, status: InstrumentStatus) -> dict[str, Any]:
        return {
            "instrument_id": status.instrument_id,
            "expected_contract_id": status.expected_contract_id,
            "runtime_contract_id": status.runtime_contract_id,
            "stream_id": status.stream_id,
            "gate_state": status.gate_state,
            "safety_state": status.safety_state,
            "state_synced": status.state_synced,
            "reason": status.reason,
        }

    def source_value(self, address: str) -> ValueEnvelope | None:
        with self._lock:
            return self._values.get(address)

    def close(self) -> None:
        if self.report_writer is not None:
            self.report_writer.finalize()


__all__ = ["WeaverEngine"]
