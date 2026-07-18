from __future__ import annotations

import pytest


fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from harmonic_weaver.server import PROTOCOL_VERSION, STAGE_CONTRACT_ID, create_app

from engine_fixtures import ready_engine, route, scene


def client_message(message_type: str, request_id: str, payload: dict) -> dict:
    return {
        "type": message_type,
        "protocol_version": PROTOCOL_VERSION,
        "request_id": request_id,
        "payload": payload,
    }


def test_websocket_handshake_snapshot_and_route_create_event_round_trip() -> None:
    engine, _recorder, _source, _instrument = ready_engine()
    engine.upsert_scene(scene(routes=[]), engine.stage_revision)
    engine.switch_scene("main", 1, engine.stage_revision)
    app = create_app(engine)

    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["contract_id"] == STAGE_CONTRACT_ID

        with client.websocket_connect("/ws") as socket:
            first = socket.receive_json()
            assert first["type"] == "server.hello"
            assert first["payload"]["gate_state"] == "awaiting_client"
            socket.send_json(
                client_message(
                    "client.hello",
                    "hello-1",
                    {
                        "client_id": "pytest-client",
                        "expected_contract_id": STAGE_CONTRACT_ID,
                        "supported_protocol_versions": [PROTOCOL_VERSION],
                    },
                )
            )
            ready = socket.receive_json()
            assert ready["type"] == "server.hello"
            assert ready["payload"]["gate_state"] == "ready"

            socket.send_json(client_message("state.subscribe", "subscribe-1", {"topics": ["stage", "routes"]}))
            snapshot = socket.receive_json()
            assert snapshot["type"] == "state.snapshot"
            assert snapshot["request_id"] == "subscribe-1"
            revision = snapshot["stage_revision"]

            socket.send_json(
                client_message(
                    "route.create",
                    "create-1",
                    {
                        "scene_id": "main",
                        "expected_stage_revision": revision,
                        "route": route("ws-route", voice=0),
                    },
                )
            )
            responses = [socket.receive_json(), socket.receive_json()]
            ack = next(item for item in responses if item["type"] == "command.ack")
            event = next(item for item in responses if item["type"] == "state.event")
            assert ack["request_id"] == "create-1"
            assert ack["payload"]["command_type"] == "route.create"
            assert event["payload"]["action"] == "route.created"
            assert event["event_seq"] > snapshot["payload"]["snapshot_event_seq"]
