"""Measured run evidence writer for headless Weaver rehearsals."""

from __future__ import annotations

import json
import math
import threading
import time
from pathlib import Path
from typing import Any, Mapping

from harmonic_weaver.contract_codec import canonical_json_dumps


def _percentile(samples: list[float], percentile: float) -> float | None:
    if not samples:
        return None
    ordered = sorted(samples)
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


class ReportWriter:
    """Write canonical configuration, traces, events and measured summaries."""

    def __init__(
        self,
        root: str | Path = "reports",
        *,
        run_id: str | None = None,
        run_config: Mapping[str, Any] | None = None,
    ) -> None:
        self.run_id = run_id or time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        self.path = Path(root) / self.run_id
        self.path.mkdir(parents=True, exist_ok=False)
        self._lock = threading.Lock()
        self._accepted: dict[str, dict[str, str]] = {
            "stage": {},
            "sources": {},
            "instruments": {},
            "derived": {},
        }
        self._latencies_ms: list[float] = []
        self._mutation_ms: list[float] = []
        self._counts = {"drops": 0, "rejections": 0, "errors": 0}
        self._write_json(
            "run_config.json",
            {
                "run_id": self.run_id,
                "started_at_us": time.time_ns() // 1000,
                "mode": "headless",
                "claims": {"hardware": False, "audible_audio": False},
                **dict(run_config or {}),
            },
        )
        self._write_json("accepted_contract_ids.json", self._accepted)
        self._write_json("scene_snapshot.json", None)
        self.finalize()

    def _write_json(self, name: str, value: Any) -> None:
        (self.path / name).write_text(canonical_json_dumps(value) + "\n", encoding="utf-8")

    def _append_jsonl(self, name: str, value: Mapping[str, Any]) -> None:
        with (self.path / name).open("a", encoding="utf-8") as handle:
            handle.write(canonical_json_dumps(dict(value)) + "\n")

    def accept_contract(self, kind: str, entity_id: str, contract_id: str) -> None:
        with self._lock:
            self._accepted.setdefault(kind, {})[entity_id] = contract_id
            self._write_json("accepted_contract_ids.json", self._accepted)

    def scene_snapshot(self, scene: Mapping[str, Any] | None) -> None:
        with self._lock:
            self._write_json("scene_snapshot.json", scene)

    def behavior_event(self, event: Mapping[str, Any]) -> None:
        with self._lock:
            self._append_jsonl("behavior_events.jsonl", event)

    def trace(self, event: Mapping[str, Any]) -> None:
        with self._lock:
            self._append_jsonl("state_timestamps.jsonl", event)

    def record_weaver_latency(self, milliseconds: float) -> None:
        if math.isfinite(milliseconds) and milliseconds >= 0:
            with self._lock:
                self._latencies_ms.append(milliseconds)

    def record_mutation_latency(self, milliseconds: float) -> None:
        if math.isfinite(milliseconds) and milliseconds >= 0:
            with self._lock:
                self._mutation_ms.append(milliseconds)

    def count(self, name: str, amount: int = 1) -> None:
        with self._lock:
            if name in self._counts:
                self._counts[name] += amount

    def finalize(self) -> Path:
        with self._lock:
            weaver = {
                "status": "measured" if self._latencies_ms else "no_samples",
                "sample_count": len(self._latencies_ms),
                "p50_ms": _percentile(self._latencies_ms, 0.50),
                "p95_ms": _percentile(self._latencies_ms, 0.95),
                "p99_ms": _percentile(self._latencies_ms, 0.99),
            }
            mutation = {
                "status": "measured" if self._mutation_ms else "no_samples",
                "sample_count": len(self._mutation_ms),
                "p50_ms": _percentile(self._mutation_ms, 0.50),
                "p95_ms": _percentile(self._mutation_ms, 0.95),
                "p99_ms": _percentile(self._mutation_ms, 0.99),
            }
            self._write_json(
                "latency_summary.json",
                {
                    "weaver_receipt_to_instrument_send": weaver,
                    "ws_mutation_receipt_to_generation_swap": mutation,
                    "source_capture": {"status": "not_measured", "reason": "driver callback has no common capture clock"},
                    "network": {"status": "not_measured"},
                    "audio": {"status": "not_measured"},
                    "intentional_cadence_and_transition_time": {"status": "reported_by_declaration_not_folded_into_weaver_overhead"},
                },
            )
            self._write_json("summary.json", dict(self._counts))
        return self.path


__all__ = ["ReportWriter"]
