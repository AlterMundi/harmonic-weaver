"""Instrument output seams. No live OSC behavior is defined here."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol


@dataclass(frozen=True)
class OutputRecord:
    instrument_id: str
    kind: str
    sent_at_us: int
    reason: str
    capability: str | None = None
    address: str | None = None
    bindings: Mapping[str, int] | None = None
    argument: str | None = None
    value: float | int | None = None
    action: str | None = None


class OutputTransport(Protocol):
    def send_capability(self, record: OutputRecord) -> None: ...

    def invoke_action(self, record: OutputRecord) -> None: ...


class RecordingOutputTransport:
    """Thread-safe recorder used by tests and headless dry runs."""

    def __init__(self) -> None:
        self._records: list[OutputRecord] = []
        self._lock = threading.Lock()

    @property
    def records(self) -> list[OutputRecord]:
        with self._lock:
            return list(self._records)

    def clear(self) -> None:
        with self._lock:
            self._records.clear()

    def send_capability(self, record: OutputRecord) -> None:
        with self._lock:
            self._records.append(record)

    def invoke_action(self, record: OutputRecord) -> None:
        with self._lock:
            self._records.append(record)


InstrumentSendCallback = Callable[
    [str, str, Mapping[str, int], str, float | int], None
]


__all__ = [
    "InstrumentSendCallback",
    "OutputRecord",
    "OutputTransport",
    "RecordingOutputTransport",
]
