"""Live Stage convergence knobs (/api/scene/params)."""

from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from harmonic_weaver.engine import OutputRecord, RecordingOutputTransport, WeaverEngine
from harmonic_weaver.scene_params import (
    KnobAwareTransport,
    SceneParamsStore,
    ceiling_level_to_n,
    ceiling_n_to_level,
    install_knob_transport,
)
from harmonic_weaver.server import create_app

from engine_fixtures import ready_engine


def test_ceiling_level_round_trip() -> None:
    for n in range(1, 33):
        assert ceiling_level_to_n(ceiling_n_to_level(n)) == n


def test_get_params_defaults() -> None:
    engine, _recorder, _source, _instrument = ready_engine()
    with TestClient(create_app(engine)) as client:
        response = client.get("/api/scene/params")
    assert response.status_code == 200
    body = response.json()
    assert body["settle_beats"] == 1.0
    assert body["ceiling_max"] == 32.0
    assert body["tempo_conf_threshold"] == 0.35
    assert body["clock_bpm_override"] == 0.0
    assert body["arp_register_lo"] == 1.0
    assert body["arp_register_hi"] == 16.0


def test_post_settle_beats_pushes_digital_address() -> None:
    engine, _recorder, _source, _instrument = ready_engine()
    app = create_app(engine)
    transport = engine.transport
    assert isinstance(transport, KnobAwareTransport)

    with TestClient(app) as client:
        response = client.post("/api/scene/params", json={"settle_beats": 2.0})
        assert response.status_code == 200
        payload = response.json()
        assert payload["params"]["settle_beats"] == 2.0
        assert any(
            item.get("address") == "/digital/settle_beats" and item.get("value") == 2.0
            for item in payload["pushed"]
        )

        # Page reload reads the same in-process values.
        again = client.get("/api/scene/params")
        assert again.json()["settle_beats"] == 2.0

    records = transport.records
    stage = [r for r in records if r.reason == "stage_knob" and r.capability == "settle_beats"]
    assert stage
    assert stage[-1].address == "/digital/settle_beats"
    assert stage[-1].value == 2.0


def test_clock_bpm_override_and_resume_body_tempo() -> None:
    engine, _recorder, _source, _instrument = ready_engine()
    app = create_app(engine)
    transport = engine.transport

    with TestClient(app) as client:
        locked = client.post("/api/scene/params", json={"clock_bpm_override": 120})
        assert locked.status_code == 200
        assert any(
            item.get("address") == "/digital/clock/bpm" and item.get("value") == 120.0
            for item in locked.json()["pushed"]
        )

        # Body-route clock traffic is rewritten while override is active.
        transport.inner.clear()
        transport.send_capability(
            OutputRecord(
                instrument_id="shaper",
                kind="capability",
                sent_at_us=1,
                reason="route",
                capability="clock_bpm",
                address="/digital/clock/bpm",
                bindings={},
                argument="bpm",
                value=88.0,
            )
        )
        assert transport.records[-1].value == 120.0

        released = client.post("/api/scene/params", json={"clock_bpm_override": 0})
        assert released.status_code == 200
        assert any(item.get("skipped") for item in released.json()["pushed"])

        transport.inner.clear()
        transport.send_capability(
            OutputRecord(
                instrument_id="shaper",
                kind="capability",
                sent_at_us=2,
                reason="route",
                capability="clock_bpm",
                address="/digital/clock/bpm",
                bindings={},
                argument="bpm",
                value=96.0,
            )
        )
        assert transport.records[-1].value == 96.0


def test_static_settle_route_cannot_fight_knob() -> None:
    store = SceneParamsStore()
    store.update({"settle_beats": 3.0}, push=False)
    recorder = RecordingOutputTransport()
    transport = KnobAwareTransport(recorder, store)
    transport.send_capability(
        OutputRecord(
            instrument_id="shaper",
            kind="capability",
            sent_at_us=1,
            reason="route",
            capability="settle_beats",
            address="/digital/settle_beats",
            bindings={},
            argument="beats",
            value=1.0,
        )
    )
    assert recorder.records[-1].value == 3.0


def test_ceiling_max_clamps_partial_ceiling_level() -> None:
    store = SceneParamsStore()
    store.update({"ceiling_max": 8}, push=False)
    recorder = RecordingOutputTransport()
    transport = KnobAwareTransport(recorder, store)
    # level 1.0 → n=32, must clamp to 8
    transport.send_capability(
        OutputRecord(
            instrument_id="shaper",
            kind="capability",
            sent_at_us=1,
            reason="route",
            capability="partial_ceiling",
            address="/digital/ceiling",
            bindings={},
            argument="level",
            value=1.0,
        )
    )
    assert ceiling_level_to_n(float(recorder.records[-1].value)) == 8


def test_validation_rejects_out_of_range() -> None:
    engine, _recorder, _source, _instrument = ready_engine()
    with TestClient(create_app(engine)) as client:
        bad = client.post("/api/scene/params", json={"settle_beats": 99})
        assert bad.status_code == 400
        assert bad.json()["error"] == "validation_error"


def test_patchbay_page_includes_knobs_panel() -> None:
    engine, _recorder, _source, _instrument = ready_engine()
    with TestClient(create_app(engine)) as client:
        page = client.get("/")
        script = client.get("/static/patchbay.js")
    assert page.status_code == 200
    assert 'id="knobs-panel"' in page.text
    assert 'data-param="settle_beats"' in page.text
    assert 'data-param="clock_bpm_override"' in page.text
    assert "/api/scene/params" in script.text
    assert "postSceneParam" in script.text


def test_install_knob_transport_is_idempotent() -> None:
    engine = WeaverEngine()
    store = SceneParamsStore()
    first = install_knob_transport(engine, store)
    second = install_knob_transport(engine, store)
    assert first is second
    assert engine.transport is first
