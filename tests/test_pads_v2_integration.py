"""Integration: synthetic HarMoCAP poses → pads_v2 → OSC transport records.

Follows the same replay pattern as test_pads_e2e.py but with synthetic
hand positions instead of a recorded session. Verifies that the correct
harmonic N receives envelope writes when the hand is on the target pad.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT.parent
SHAPER_MANIFEST = PROJECTS / "harmonic-shaper" / "contracts" / "shaper.contract.json"
PADS_V2 = ROOT / "rehearsal" / "scenes" / "pads_v2.scene.json"


def _load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _make_person(
    slot: int,
    side: str,        # "r" or "l"
    hand_nx: float,   # unit-normalised X (0..1, 0=left in original cam)
    hand_ny: float,   # unit-normalised Y (0..1, 0=top)
    focused: bool = True,
    *,
    nose_nx: float = 0.5,
    nose_ny: float = 0.4,
) -> dict:
    """Build a single-person dict matching the HarMoCAP wire format.

    Keypoints are list-of-lists: [[x, y, state], ...] in COCO order.
    """
    kp_idx = 9 if side == "r" else 10  # right_wrist=9, left_wrist=10
    nose_idx = 0
    kps = []
    kp_state = []
    for i in range(17):
        if i == kp_idx:
            kps.append([hand_nx, hand_ny, 1.0])
            kp_state.append([2, 2, 2])
        elif i == nose_idx:
            kps.append([nose_nx, nose_ny, 1.0])
            kp_state.append([2, 2, 2])
        else:
            kps.append([0.0, 0.0, 0.0])
            kp_state.append([0, 0, 0])
    return {
        "slot_id": slot,
        "focused": 1 if focused else 0,
        "present": 1,
        "keypoints": kps,
        "kp_state": kp_state,
        "features": [0.0] * 24,
        "feat_state": [0] * 24,
    }


def _make_frame(*persons: dict) -> dict:
    return {
        "captured_frame_id": 1,
        "n_persons": len(persons),
        "stream_id": "test-stream-0001",
        "contract_id": "test-contract-0000000000000001",
        "schema_version": "1.4.0",
        "feature_set_version": "1.1.0",
        "producer_version": "0.1.0",
        "model_id": "replay",
        "config_hash": "0" * 32,
        "calibration_generation": 0,
        "calibration_state": "valid",
        "persons": list(persons),
    }


def _harMoCAP_engine_with_pads_v2(monkeypatch):
    """Set up the Weaver engine exactly like test_pads_e2e.py does, but
    with the pads-v2 scene."""
    from harmonic_weaver.drivers.harmocap_driver import HarMoCAPDriver
    from harmonic_weaver.engine import RecordingOutputTransport, WeaverEngine
    from harmonic_weaver.contract_codec import contract_id_from_manifest
    from rehearsal.weaver_runtime import (
        _frame_to_wire,
        _handshake_bytes,
        _load_kit_codec,
        _pad_person_features,
        harmocap_manifest,
        shaper_safety_profile,
    )

    # UDP-free transport.
    recorder = RecordingOutputTransport()
    engine = WeaverEngine(transport=recorder)

    # Shaper instrument.
    shaper = _load_json(SHAPER_MANIFEST)
    shaper_cid = contract_id_from_manifest(shaper)
    engine.install_instrument(shaper, shaper_safety_profile(shaper_cid))
    assert engine.instrument_hello("shaper", "00000000000000c1", shaper_cid)
    assert engine.instrument_sync_complete("shaper", "00000000000000c1", shaper_cid)

    # HarMoCAP source.
    harmocap = harmocap_manifest(lease_ms=60_000.0)
    harmocap_cid = engine.install_source(harmocap)
    assert engine.source_hello("harmocap", "00000000000000a1", harmocap_cid)

    # Scene.
    scene = _load_json(PADS_V2)
    engine.upsert_scene(scene, engine.stage_revision)
    engine.switch_scene(scene["scene_id"], int(scene["scene_version"]),
                         engine.stage_revision)

    codec = _load_kit_codec()
    return engine, recorder, codec, harmocap, scene


def _replay_frames(engine, recorder, codec, frames: list[dict]):
    from harmonic_weaver.drivers.harmocap_driver import HarMoCAPDriver
    from rehearsal.weaver_runtime import _frame_to_wire, _handshake_bytes

    driver = HarMoCAPDriver(on_frame=engine.driver_callback, lease_ms=60_000.0)
    now_ms = 1_000_000.0
    seq = 0
    for fi, frame in enumerate(frames):
        frame = dict(frame)
        if frame.get("persons"):
            from rehearsal.weaver_runtime import _pad_person_features
            frame["persons"] = [
                _pad_person_features(dict(p)) for p in frame["persons"]
            ]
        if fi == 0 or fi % 30 == 0:
            for packet in _handshake_bytes(codec, frame):
                driver.handle_datagram(packet, now_ms=now_ms)
        for packet in _frame_to_wire(codec, frame, first_seq=seq + 1):
            seq += 1
            driver.handle_datagram(packet, now_ms=now_ms)
        now_ms += 33.0
    return recorder.records


def _envelope_writes_for_n(records, n: int) -> list:
    return [
        r for r in records
        if r.instrument_id == "shaper"
        and r.capability == "harmonic_envelope"
        and r.bindings
        and r.bindings.get("N") == n
    ]


# ── Tests ────────────────────────────────────────────────────────────────

def test_hand_r_top_left_activates_n1(monkeypatch):
    """Hand r at normalised (0.85, 0.85) → pad 0 → N=1 envelope > 0."""
    engine, recorder, codec, harmocap, scene = _harMoCAP_engine_with_pads_v2(monkeypatch)

    # Normalised coords that bin_2d maps to pad 0 (col 0, row 0):
    # bin_2d with x_min=1.0, x_max=0.0 (mirror flip):
    # col = floor((x-1)/(0-1)*4) → x=0.9 gives col=0
    # y_min=1.0, y_max=0.0: row = floor((y-1)/(0-1)*8) → y=0.9 gives row=0
    person = _make_person(0, "r", hand_nx=0.88, hand_ny=0.88)
    records = _replay_frames(engine, recorder, codec, [_make_frame(person)] * 10)

    n1 = _envelope_writes_for_n(records, 1)
    assert n1, f"no envelope writes for N=1; total harmonic_envelope records: {len([r for r in records if r.capability=='harmonic_envelope'])}"

    active = [r for r in n1 if r.value > 0.3]
    assert active, f"N=1 envelope too low: {[r.value for r in n1]}"


def test_hand_r_mid_right_activates_different_n(monkeypatch):
    """Hand r at a DIFFERENT position → different N active, N=1 silent."""
    engine, recorder, codec, harmocap, scene = _harMoCAP_engine_with_pads_v2(monkeypatch)

    # Normalised coords for pad 4 (col 1, row 4?):
    # col=1 at x≈0.1: floor((0.1-1)/(0-1)*4) = floor(3.6) = 3 ... no.
    # col=1 at x≈0.6: floor((0.6-1)/-1*4) = floor(1.6) = 1 ✓
    # y for row 4: floor((y-1)/-1*8) = 4 → (y-1)/-1 = 0.5 → y=0.5
    person = _make_person(0, "r", hand_nx=0.62, hand_ny=0.50)
    records = _replay_frames(engine, recorder, codec, [_make_frame(person)] * 10)

    # N=1 should be silent (hand is not on pad 0).
    n1 = _envelope_writes_for_n(records, 1)
    if n1:
        assert all(r.value < 0.1 for r in n1), (
            f"N=1 should be silent; got {[r.value for r in n1]}"
        )

    # At least one other odd N should be active.
    all_env = [r for r in records
               if r.capability == "harmonic_envelope" and r.value > 0.3]
    assert all_env, "no active envelope writes at all"


def test_hand_l_activates_even_n(monkeypatch):
    """Left hand → even N active."""
    engine, recorder, codec, harmocap, scene = _harMoCAP_engine_with_pads_v2(monkeypatch)

    person = _make_person(0, "l", hand_nx=0.88, hand_ny=0.88)
    records = _replay_frames(engine, recorder, codec, [_make_frame(person)] * 10)

    evens = [r for r in records
             if r.capability == "harmonic_envelope"
             and r.bindings and r.bindings.get("N", 0) % 2 == 0
             and r.value > 0.3]
    assert evens, "no even-N envelope writes"
    # N=1 (odd) should be silent.
    n1 = _envelope_writes_for_n(records, 1)
    if n1:
        assert all(r.value < 0.1 for r in n1)