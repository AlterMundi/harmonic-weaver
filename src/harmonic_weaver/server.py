"""FastAPI Stage Contract transport for the headless Weaver engine."""

from __future__ import annotations

import asyncio
import contextlib
import secrets
from contextlib import asynccontextmanager
from typing import Any, Mapping

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .engine import EventRecord, WeaverEngine, WeaverError


STAGE_CONTRACT_ID = "cc2f83205e0dccf6d0b5d488883d73ad"
PROTOCOL_VERSION = "0.1-draft"
SCHEMA_VERSION = "0.1.0"
TOPICS = {"stage", "routes", "scenes", "sources", "instruments", "metrics"}
COMMANDS = {
    "route.create",
    "route.update",
    "route.delete",
    "route.batch",
    "scene.upsert",
    "scene.delete",
    "scene.switch",
    "panic.trigger",
    "panic.clear",
}


class StageServer:
    def __init__(self, engine: WeaverEngine, *, queue_size: int = 256) -> None:
        self.engine = engine
        self.server_stream_id = secrets.token_hex(8)
        self.queue_size = queue_size
        if engine.report_writer is not None:
            engine.report_writer.accept_contract(
                "stage",
                "harmonic-weaver-stage",
                STAGE_CONTRACT_ID,
            )

    def envelope(
        self,
        message_type: str,
        payload: Mapping[str, Any],
        *,
        request_id: str | None = None,
        event: EventRecord | None = None,
        stage_revision: int | None = None,
        event_seq: int | None = None,
    ) -> dict[str, Any]:
        message: dict[str, Any] = {
            "type": message_type,
            "protocol_version": PROTOCOL_VERSION,
            "server_stream_id": self.server_stream_id,
            "event_seq": (
                event.event_seq
                if event is not None
                else self.engine.event_seq if event_seq is None else event_seq
            ),
            "stage_revision": (
                event.stage_revision
                if event is not None
                else self.engine.stage_revision
                if stage_revision is None
                else stage_revision
            ),
            "sent_at_us": self.engine._clock_us() if event is None else event.sent_at_us,
            "payload": dict(payload),
        }
        if request_id is not None:
            message["request_id"] = request_id
        return message

    def hello(self, gate_state: str, reason: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "contract_id": STAGE_CONTRACT_ID,
            "schema_version": SCHEMA_VERSION,
            "gate_state": gate_state,
        }
        if reason is not None:
            payload["reason"] = reason
        return self.envelope("server.hello", payload)

    @staticmethod
    def validate_client_message(message: Any) -> tuple[str, str, dict[str, Any]]:
        if not isinstance(message, dict):
            raise WeaverError("bad_message", "client message must be an object")
        required = {"type", "protocol_version", "request_id", "payload"}
        if set(message) != required:
            raise WeaverError("bad_message", "client envelope fields must exactly match the Stage Contract")
        if message["protocol_version"] != PROTOCOL_VERSION:
            raise WeaverError("bad_message", f"protocol_version must be {PROTOCOL_VERSION}")
        request_id = message["request_id"]
        if not isinstance(request_id, str) or not request_id:
            raise WeaverError("bad_message", "request_id must be non-empty")
        if not isinstance(message["type"], str) or not isinstance(message["payload"], dict):
            raise WeaverError("bad_message", "type must be a string and payload must be an object")
        return message["type"], request_id, message["payload"]

    def command(self, command_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if command_type == "route.create":
            return self.engine.create_route(payload["scene_id"], payload["route"], payload["expected_stage_revision"])
        if command_type == "route.update":
            return self.engine.update_route(payload["scene_id"], payload["route_id"], payload["expected_route_version"], payload["route"], payload["expected_stage_revision"])
        if command_type == "route.delete":
            return self.engine.delete_route(payload["scene_id"], payload["route_id"], payload["expected_route_version"], payload["expected_stage_revision"])
        if command_type == "route.batch":
            return self.engine.route_batch(payload["operations"], payload["expected_stage_revision"])
        if command_type == "scene.upsert":
            return self.engine.upsert_scene(payload["scene"], payload["expected_stage_revision"], expected_scene_version=payload.get("expected_scene_version"))
        if command_type == "scene.delete":
            return self.engine.delete_scene(payload["scene_id"], payload["expected_scene_version"], payload["expected_stage_revision"])
        if command_type == "scene.switch":
            return self.engine.switch_scene(payload["scene_id"], payload["expected_scene_version"], payload["expected_stage_revision"])
        if command_type == "panic.trigger":
            return self.engine.trigger_panic(payload.get("reason"))
        if command_type == "panic.clear":
            return self.engine.clear_panic(payload["panic_generation"], payload["scene_id"], payload["expected_scene_version"])
        raise WeaverError("bad_message", f"unknown command type {command_type!r}")

    @staticmethod
    def event_topic(event: EventRecord) -> str:
        if event.type == "registry.source":
            return "sources"
        if event.type == "registry.instrument":
            return "instruments"
        if event.type == "panic.event":
            return "stage"
        return str(event.payload.get("topic", "stage"))

    async def websocket(self, websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.send_json(self.hello("awaiting_client", "client.hello required"))
        gated = False
        seen_request_ids: set[str] = set()
        subscriptions: set[str] = set()
        outbound: asyncio.Queue[EventRecord] = asyncio.Queue(maxsize=self.queue_size)
        overflowed = {"value": False}
        loop = asyncio.get_running_loop()
        sender_task: asyncio.Task[None] | None = None
        snapshot_seq = 0
        send_lock = asyncio.Lock()

        def listener(event: EventRecord) -> None:
            if not subscriptions or self.event_topic(event) not in subscriptions:
                return

            def enqueue() -> None:
                if overflowed["value"]:
                    return
                try:
                    outbound.put_nowait(event)
                except asyncio.QueueFull:
                    overflowed["value"] = True

            loop.call_soon_threadsafe(enqueue)

        remove_listener = self.engine.add_event_listener(listener)

        async def sender() -> None:
            nonlocal snapshot_seq
            while True:
                if overflowed["value"]:
                    await websocket.close(code=1013, reason="outbound queue overflow")
                    return
                event = await outbound.get()
                if event.event_seq <= snapshot_seq or self.event_topic(event) not in subscriptions:
                    continue
                async with send_lock:
                    await websocket.send_json(
                        self.envelope(
                            event.type,
                            event.as_dict()["payload"],
                            event=event,
                        )
                    )

        try:
            try:
                first = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
            except asyncio.TimeoutError:
                await websocket.close(code=1008, reason="client.hello timeout")
                return
            try:
                message_type, request_id, payload = self.validate_client_message(first)
                seen_request_ids.add(request_id)
                if message_type != "client.hello":
                    raise WeaverError("not_gated", "client.hello must be the first client message")
                required = {"client_id", "expected_contract_id", "supported_protocol_versions"}
                if not required.issubset(payload):
                    raise WeaverError("bad_message", "client.hello payload is incomplete")
                supported = payload["supported_protocol_versions"]
                if payload["expected_contract_id"] != STAGE_CONTRACT_ID or not isinstance(supported, list) or PROTOCOL_VERSION not in supported:
                    await websocket.send_json(self.hello("incompatible", "stage contract or protocol mismatch"))
                else:
                    gated = True
                    await websocket.send_json(self.hello("ready"))
            except WeaverError as exc:
                await websocket.send_json(self.error("client.hello", request_id if "request_id" in locals() else None, exc))

            while True:
                message = await websocket.receive_json()
                request_id: str | None = None
                message_type = "unknown"
                try:
                    message_type, request_id, payload = self.validate_client_message(message)
                    if request_id in seen_request_ids:
                        raise WeaverError("bad_message", "request_id was already used on this socket")
                    seen_request_ids.add(request_id)
                    if message_type == "client.hello":
                        raise WeaverError("bad_message", "client.hello may only be sent once")
                    if not gated:
                        raise WeaverError("not_gated", "connection is not contract-gated")
                    if message_type == "state.subscribe":
                        topics = payload.get("topics")
                        if not isinstance(topics, list) or not topics or any(topic not in TOPICS for topic in topics):
                            raise WeaverError("bad_message", "topics must be a non-empty Stage Contract subset")
                        subscriptions.clear()
                        subscriptions.update(topics)
                        snapshot, snapshot_revision, snapshot_event_seq = (
                            self.engine.snapshot_transaction(subscriptions)
                        )
                        snapshot_seq = snapshot["snapshot_event_seq"]
                        async with send_lock:
                            await websocket.send_json(
                                self.envelope(
                                    "state.snapshot",
                                    snapshot,
                                    request_id=request_id,
                                    stage_revision=snapshot_revision,
                                    event_seq=snapshot_event_seq,
                                )
                            )
                        if sender_task is None:
                            sender_task = asyncio.create_task(sender())
                        continue
                    if message_type not in COMMANDS:
                        raise WeaverError("bad_message", f"unknown message type {message_type!r}")
                    try:
                        result = self.command(message_type, payload)
                    except KeyError as exc:
                        raise WeaverError("bad_message", f"missing required payload field {exc.args[0]!r}") from exc
                    async with send_lock:
                        await websocket.send_json(self.envelope("command.ack", result, request_id=request_id))
                except WeaverError as exc:
                    async with send_lock:
                        await websocket.send_json(self.error(message_type, request_id, exc))
                except (TypeError, ValueError) as exc:
                    error = WeaverError("bad_message", str(exc))
                    async with send_lock:
                        await websocket.send_json(self.error(message_type, request_id, error))
        except WebSocketDisconnect:
            pass
        finally:
            remove_listener()
            if sender_task is not None:
                sender_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await sender_task

    def error(self, command_type: str, request_id: str | None, error: WeaverError) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "command_type": command_type,
            "code": error.code,
            "message": error.message,
        }
        if error.details is not None:
            payload["details"] = error.details
        if error.current_stage_revision is not None:
            payload["current_stage_revision"] = error.current_stage_revision
        return self.envelope("command.error", payload, request_id=request_id)


def create_app(engine: WeaverEngine | None = None, *, queue_size: int = 256) -> FastAPI:
    owned_engine = engine is None
    selected_engine = engine or WeaverEngine()
    stage_server = StageServer(selected_engine, queue_size=queue_size)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        stop = asyncio.Event()

        async def ticker() -> None:
            while not stop.is_set():
                await asyncio.to_thread(selected_engine.tick)
                try:
                    await asyncio.wait_for(stop.wait(), timeout=0.01)
                except asyncio.TimeoutError:
                    pass

        task = asyncio.create_task(ticker())
        try:
            yield
        finally:
            stop.set()
            with contextlib.suppress(asyncio.CancelledError):
                await task
            if owned_engine:
                selected_engine.close()

    app = FastAPI(title="Harmonic Weaver", version="0.1.0", lifespan=lifespan)
    app.state.engine = selected_engine
    app.state.stage_server = stage_server

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "contract_id": STAGE_CONTRACT_ID,
            "server_stream_id": stage_server.server_stream_id,
            "stage_revision": selected_engine.stage_revision,
            "panic_active": selected_engine.panic_active,
        }

    @app.websocket("/ws")
    async def stage_socket(websocket: WebSocket) -> None:
        await stage_server.websocket(websocket)

    return app


__all__ = [
    "PROTOCOL_VERSION",
    "SCHEMA_VERSION",
    "STAGE_CONTRACT_ID",
    "StageServer",
    "create_app",
]
