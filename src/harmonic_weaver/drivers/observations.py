"""Versioned per-slot observations; producer and receiver clocks are never conflated."""

from dataclasses import asdict, dataclass
import math
from typing import Literal


@dataclass(frozen=True)
class ObservationEvent:
    source_id: str
    stream_id: str
    slot: int
    event_kind: Literal["slot_update", "slot_invalidated"]
    reason: str
    contract_id: str | None
    calibration_generation: int | None
    calibration_hash: str | None
    captured_frame_id: int | None
    bundle_seq: int | None
    captured_at_us: int | None
    processed_at_us: int | None
    queued_for_send_at_us: int | None
    received_at_us: int
    channel_values: dict[str, tuple[float, int, float]]
    schema_version: int = 2
    capture_clock: str = "producer_monotonic_us_unmapped"
    receipt_clock: str = "receiver_monotonic_us"
    scope: str = "updated_slot_only"

    def __post_init__(self):
        if self.schema_version != 2 or self.scope != "updated_slot_only":
            raise ValueError("unsupported observation version or scope")
        if (
            self.capture_clock != "producer_monotonic_us_unmapped"
            or self.receipt_clock != "receiver_monotonic_us"
        ):
            raise ValueError("unsupported observation clock domains")
        if self.event_kind not in ("slot_update", "slot_invalidated"):
            raise ValueError("invalid observation event kind")
        if any(
            not isinstance(value, str) or not value
            for value in (self.source_id, self.stream_id)
        ):
            raise ValueError("observation requires source and stream identities")
        if type(self.slot) is not int or type(self.received_at_us) is not int:
            raise ValueError("slot and received_at_us must be integers")
        for name in (
            "slot",
            "received_at_us",
            "calibration_generation",
            "captured_frame_id",
            "bundle_seq",
            "captured_at_us",
            "processed_at_us",
            "queued_for_send_at_us",
        ):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"{name} must be a nonnegative integer or None")
        if not 0 <= self.slot < 8:
            raise ValueError("invalid observation slot")
        if self.event_kind == "slot_update" and any(
            value is None
            for value in (self.captured_frame_id, self.bundle_seq, self.captured_at_us)
        ):
            raise ValueError("slot update requires producer identity and capture time")
        for name, (value, state, confidence) in self.channel_values.items():
            if not name.startswith(f"slot_{self.slot}_"):
                raise ValueError("observation contains channels of another slot")
            if type(state) is not int or state not in (0, 1, 2):
                raise ValueError("invalid observation channel state")
            if (
                not math.isfinite(value)
                or not math.isfinite(confidence)
                or not 0 <= confidence <= 1
            ):
                raise ValueError("invalid observation channel value or confidence")
            if state == 2 and (value != 0 or confidence != 0):
                raise ValueError(
                    "invalid channel requires zero sentinel and confidence"
                )

    def to_dict(self):
        return asdict(self)


class SlotObservationHistory:
    """Small explicit consumer example: new observed samples only, no tick-derived motion."""

    def __init__(self, max_gap_us=500000):
        if type(max_gap_us) is not int or max_gap_us <= 0:
            raise ValueError("max_gap_us must be a positive integer")
        self.max_gap_us = max_gap_us
        self.previous = {}
        self.rows = []

    def consume(self, event):
        for name, (value, state, confidence) in event.channel_values.items():
            key = (event.source_id, event.slot, name)
            prior = self.previous.get(key)
            if (
                state != 0
                or event.event_kind != "slot_update"
                or event.captured_at_us is None
            ):
                self.previous.pop(key, None)
                continue
            identity = (
                event.contract_id,
                event.stream_id,
                event.calibration_generation,
                event.calibration_hash,
            )
            sample = (identity, event.captured_frame_id, event.captured_at_us, value)
            if (
                prior
                and prior[0] == identity
                and (
                    event.captured_frame_id <= prior[1]
                    or event.captured_at_us <= prior[2]
                )
            ):
                continue
            derivative = None
            cause = "warming"
            if prior and prior[0] == identity:
                dt = event.captured_at_us - prior[2]
                if 0 < dt <= self.max_gap_us:
                    derivative = (value - prior[3]) / (dt / 1e6)
                    cause = None
                else:
                    cause = "capture_gap_or_nonincreasing_clock"
            self.previous[key] = sample
            self.rows.append(
                {
                    "source_id": event.source_id,
                    "slot": event.slot,
                    "channel": name,
                    "contract_id": event.contract_id,
                    "calibration_generation": event.calibration_generation,
                    "calibration_hash": event.calibration_hash,
                    "state": state,
                    "confidence": confidence,
                    "stream_id": event.stream_id,
                    "captured_frame_id": event.captured_frame_id,
                    "bundle_seq": event.bundle_seq,
                    "captured_at_us": event.captured_at_us,
                    "received_at_us": event.received_at_us,
                    "capture_clock": event.capture_clock,
                    "receipt_clock": event.receipt_clock,
                    "value": value,
                    "derivative_per_producer_s": derivative,
                    "cause": cause,
                }
            )
