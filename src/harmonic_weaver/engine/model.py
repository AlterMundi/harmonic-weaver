"""Immutable public values and internal runtime state for Harmonic Weaver."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


OBSERVED = "observed"
HELD = "held"
INVALID = "invalid"


@dataclass(frozen=True)
class ValueEnvelope:
    value: float
    state: str
    confidence: float
    received_at_us: int
    captured_at_us: int | None = None

    @classmethod
    def invalid(cls, now_us: int) -> "ValueEnvelope":
        return cls(0.0, INVALID, 0.0, now_us, None)


@dataclass(frozen=True)
class EventRecord:
    event_seq: int
    stage_revision: int
    type: str
    payload: Mapping[str, Any]
    sent_at_us: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "event_seq": self.event_seq,
            "stage_revision": self.stage_revision,
            "sent_at_us": self.sent_at_us,
            "payload": thaw(self.payload),
        }


@dataclass(frozen=True)
class PanicState:
    active: bool = False
    generation: int = 0
    reason: str | None = None
    outcomes: Mapping[str, str] = field(
        default_factory=lambda: MappingProxyType({})
    )


@dataclass(frozen=True)
class StageState:
    """Persisted stage state swapped as one immutable value."""

    revision: int = 0
    activation_generation: int = 0
    active_scene_id: str | None = None
    scenes: Mapping[str, Mapping[str, Any]] = field(
        default_factory=lambda: MappingProxyType({})
    )
    panic: PanicState = field(default_factory=PanicState)


@dataclass(frozen=True)
class SourceStatus:
    source_id: str
    kind: str
    expected_contract_id: str
    manifest: Mapping[str, Any]
    gate_state: str = "installed"
    runtime_contract_id: str | None = None
    stream_id: str | None = None
    last_frame_seq: int = -1
    lease_ms: float | None = None
    lease_deadline_us: int | None = None
    reason: str | None = None


@dataclass(frozen=True)
class InstrumentStatus:
    instrument_id: str
    expected_contract_id: str
    manifest: Mapping[str, Any]
    safety_profile: Mapping[str, Any] | None
    safety_state: str
    gate_state: str = "installed"
    runtime_contract_id: str | None = None
    stream_id: str | None = None
    state_synced: bool = False
    reason: str | None = None


def freeze(value: Any) -> Any:
    """Recursively freeze JSON-compatible state."""

    if isinstance(value, Mapping):
        return MappingProxyType({str(key): freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(item) for item in value)
    return value


def thaw(value: Any) -> Any:
    """Return an ordinary JSON-compatible deep copy of frozen state."""

    if isinstance(value, Mapping):
        return {str(key): thaw(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [thaw(item) for item in value]
    return value


__all__ = [
    "EventRecord",
    "HELD",
    "INVALID",
    "InstrumentStatus",
    "OBSERVED",
    "PanicState",
    "SourceStatus",
    "StageState",
    "ValueEnvelope",
    "freeze",
    "thaw",
]
