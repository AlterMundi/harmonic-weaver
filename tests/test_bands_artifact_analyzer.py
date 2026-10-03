from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from rehearsal.analyze_bands_artifact import analyze_artifact


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _output(
    source: int,
    harmonic: int,
    value: float,
    *,
    reason: str = "route",
    sent_at_us: int = 1_000,
) -> dict:
    return {
        "instrument_id": "shaper",
        "kind": "capability",
        "sent_at_us": sent_at_us,
        "reason": reason,
        "capability": "harmonic_source_envelope",
        "address": f"/digital/harmonic/{harmonic}/source/{source}/envelope",
        "bindings": {"N": harmonic, "S": source},
        "argument": "gain",
        "value": value,
        "action": None,
        "osc_host": "127.0.0.1",
        "osc_port": 9002,
    }


def test_analyze_bands_artifact_summarizes_synthetic_polyphony(tmp_path: Path) -> None:
    _write_jsonl(
        tmp_path / "harmocap-session.jsonl",
        [
            {"frame_seq": 0, "persons": []},
            {"frame_seq": 1, "persons": [{"slot": 0}]},
            {"frame_seq": 2, "persons": [{"slot": 0}, {"slot": 1}]},
            {"frame_seq": 3, "persons": [{"slot": 0}]},
        ],
    )
    _write_jsonl(
        tmp_path / "instrument_outputs.jsonl",
        [
            # Initialization resets for parallel routes must not be reported as
            # harmonic transitions.
            _output(0, 1, 0.0, reason="scene_reset", sent_at_us=500),
            _output(0, 2, 0.0, reason="scene_reset", sent_at_us=500),
            _output(0, 1, 1.0, sent_at_us=1_000),
            _output(1, 6, 1.0, sent_at_us=1_000),
            _output(2, 3, 1.0, sent_at_us=1_000),
            _output(3, 8, 1.0, sent_at_us=1_000),
            # One real frame-level harmonic change for source 0.
            _output(0, 1, 0.0, sent_at_us=2_000),
            _output(0, 2, 1.0, sent_at_us=2_000),
            _output(2, 3, 0.0, reason="route_reset", sent_at_us=3_000),
            _output(3, 8, 0.0, reason="route_reset", sent_at_us=3_000),
        ],
    )

    result = analyze_artifact(tmp_path)

    assert result["missing"] == []
    assert result["harmocap"]["frames"] == 4
    assert result["harmocap"]["person_count_histogram"] == {"0": 1, "1": 2, "2": 1}
    outputs = result["instrument_outputs"]
    assert outputs["events"] == 10
    assert outputs["active_source_slots"] == [0, 1, 2, 3]
    assert outputs["active_person_hands"] == [
        {"person_slot": 0, "hand": "l"},
        {"person_slot": 0, "hand": "r"},
        {"person_slot": 1, "hand": "l"},
        {"person_slot": 1, "hand": "r"},
    ]
    assert outputs["harmonic_transition_count"] == 1
    assert outputs["harmonic_transitions"] == [
        {
            "source": 0,
            "person_slot": 0,
            "hand": "r",
            "from_N": 1,
            "to_N": 2,
            "count": 1,
        }
    ]
    assert outputs["ambiguous_state_change_count"] == 0
    assert outputs["reset_release"]["route_reset_zero_count"] == 2
    assert outputs["reset_release"]["scene_reset_zero_count"] == 2
    assert outputs["reset_release"]["released_source_slots"] == [2, 3]


def test_analyze_bands_artifact_prefers_declared_person_count(tmp_path: Path) -> None:
    _write_jsonl(
        tmp_path / "harmocap-session.jsonl",
        [{"n_persons": 0, "persons": [{"slot_id": 0}]}],
    )

    result = analyze_artifact(tmp_path)

    assert result["harmocap"]["person_count_histogram"] == {"0": 1}


def test_analyze_bands_artifact_command_emits_compact_json(tmp_path: Path) -> None:
    _write_jsonl(tmp_path / "harmocap-session.jsonl", [{"persons": []}])
    _write_jsonl(tmp_path / "instrument_outputs.jsonl", [_output(0, 1, 1.0)])

    completed = subprocess.run(
        [sys.executable, "-m", "rehearsal.analyze_bands_artifact", str(tmp_path)],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "\n" not in completed.stdout.strip()
    payload = json.loads(completed.stdout)
    assert payload["harmocap"]["frames"] == 1
    assert payload["instrument_outputs"]["active_source_slots"] == [0]
