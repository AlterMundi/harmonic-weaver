"""Compact analyzer for bands-v1 live-run artifact directories."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


HARMOCAP_CANDIDATES = ("harmocap-session.jsonl", "harmocap.jsonl")
OUTPUT_AUDIT = "instrument_outputs.jsonl"


def _read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            value = json.loads(stripped)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            yield value


def _source_slot(bindings: Any) -> int | None:
    if not isinstance(bindings, dict):
        return None
    value = bindings.get("S")
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _harmonic(bindings: Any) -> int | None:
    if not isinstance(bindings, dict):
        return None
    value = bindings.get("N")
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _source_label(source: int) -> dict[str, Any]:
    return {
        "source": source,
        "person_slot": source // 2,
        "hand": "r" if source % 2 == 0 else "l",
    }


def _person_count(frame: dict[str, Any]) -> int:
    declared = frame.get("n_persons")
    if isinstance(declared, int) and not isinstance(declared, bool) and declared >= 0:
        return declared
    people = frame.get("persons", [])
    return len(people) if isinstance(people, list) else 0


def _analyze_harmocap(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "path": None,
            "frames": 0,
            "person_count_histogram": {},
        }
    histogram: Counter[int] = Counter()
    frames = 0
    for frame in _read_jsonl(path):
        histogram[_person_count(frame)] += 1
        frames += 1
    return {
        "path": str(path),
        "frames": frames,
        "person_count_histogram": {
            str(person_count): histogram[person_count]
            for person_count in sorted(histogram)
        },
    }


def _empty_output_analysis(path: Path | None) -> dict[str, Any]:
    return {
        "path": str(path) if path is not None else None,
        "events": 0,
        "active_source_slots": [],
        "active_person_hands": [],
        "harmonic_transition_count": 0,
        "harmonic_transitions": [],
        "ambiguous_state_change_count": 0,
        "reset_release": {
            "route_reset_zero_count": 0,
            "scene_reset_zero_count": 0,
            "released_source_slots": [],
        },
    }


def _analyze_outputs(path: Path | None) -> dict[str, Any]:
    if path is None:
        return _empty_output_analysis(path)

    events = 0
    active_sources: set[int] = set()
    active_person_hands: set[tuple[int, str]] = set()
    released_sources: set[int] = set()
    route_reset_zero_count = 0
    scene_reset_zero_count = 0
    batches: dict[Any, list[tuple[int, int, float]]] = {}

    for sequence, record in enumerate(_read_jsonl(path)):
        if record.get("capability") != "harmonic_source_envelope":
            continue
        source = _source_slot(record.get("bindings"))
        harmonic = _harmonic(record.get("bindings"))
        value = record.get("value")
        if source is None or harmonic is None:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue

        numeric = float(value)
        events += 1
        reason = record.get("reason")
        if numeric > 0.0 and reason == "route":
            active_sources.add(source)
            label = _source_label(source)
            active_person_hands.add((label["person_slot"], label["hand"]))
        if numeric == 0.0:
            if reason == "route_reset":
                route_reset_zero_count += 1
                released_sources.add(source)
            elif reason == "scene_reset":
                scene_reset_zero_count += 1

        timestamp = record.get("sent_at_us")
        batch_key: Any = timestamp if timestamp is not None else ("sequence", sequence)
        batches.setdefault(batch_key, []).append((source, harmonic, numeric))

    state: dict[int, dict[int, float]] = {}
    transition_counts: Counter[tuple[int, int, int]] = Counter()
    ambiguous_state_change_count = 0
    for batch in batches.values():
        affected_sources = {source for source, _harmonic_n, _value in batch}
        before = {
            source: {
                harmonic
                for harmonic, value in state.get(source, {}).items()
                if value > 0.0
            }
            for source in affected_sources
        }
        for source, harmonic, value in batch:
            state.setdefault(source, {})[harmonic] = value
        for source in affected_sources:
            after = {
                harmonic
                for harmonic, value in state.get(source, {}).items()
                if value > 0.0
            }
            if before[source] == after:
                continue
            if len(before[source]) == 1 and len(after) == 1:
                from_harmonic = next(iter(before[source]))
                to_harmonic = next(iter(after))
                if from_harmonic != to_harmonic:
                    transition_counts[(source, from_harmonic, to_harmonic)] += 1
            elif before[source] and after:
                ambiguous_state_change_count += 1

    harmonic_transitions = [
        {
            **_source_label(source),
            "from_N": from_harmonic,
            "to_N": to_harmonic,
            "count": count,
        }
        for (source, from_harmonic, to_harmonic), count in sorted(
            transition_counts.items()
        )
    ]
    return {
        "path": str(path),
        "events": events,
        "active_source_slots": sorted(active_sources),
        "active_person_hands": [
            {"person_slot": person, "hand": hand}
            for person, hand in sorted(active_person_hands)
        ],
        "harmonic_transition_count": sum(transition_counts.values()),
        "harmonic_transitions": harmonic_transitions,
        "ambiguous_state_change_count": ambiguous_state_change_count,
        "reset_release": {
            "route_reset_zero_count": route_reset_zero_count,
            "scene_reset_zero_count": scene_reset_zero_count,
            "released_source_slots": sorted(released_sources),
        },
    }


def analyze_artifact(artifact_dir: str | Path) -> dict[str, Any]:
    root = Path(artifact_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"artifact directory not found: {root}")
    harmocap_path = next(
        (root / name for name in HARMOCAP_CANDIDATES if (root / name).is_file()),
        None,
    )
    outputs_path = root / OUTPUT_AUDIT
    if not outputs_path.is_file():
        outputs_path = None
    missing = []
    if harmocap_path is None:
        missing.append("harmocap-session.jsonl")
    if outputs_path is None:
        missing.append(OUTPUT_AUDIT)
    return {
        "artifact_dir": str(root),
        "missing": missing,
        "harmocap": _analyze_harmocap(harmocap_path),
        "instrument_outputs": _analyze_outputs(outputs_path),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize bands-v1 frame/polyphony evidence from an artifact directory."
    )
    parser.add_argument("artifact_dir", type=Path)
    args = parser.parse_args(argv)
    try:
        result = analyze_artifact(args.artifact_dir)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
