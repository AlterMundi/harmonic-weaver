"""HTTP resources and latest-state WebSocket for the local laboratory."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse, Response
from pydantic import Field

from .contracts import Contract, Number, PERSISTED_CONTRACTS, PerceptionSettings, Preset
from .store import RevisionConflict, SessionStore


class RevisionRequest(Contract):
    expected_revision: int = Field(ge=0)


class ConfigurationRequest(RevisionRequest):
    preset: Preset


class MacroRequest(RevisionRequest):
    value: Number = Field(ge=0, le=1)


class MarkRequest(Contract):
    text: str = Field(min_length=1, max_length=500)


class VideoRequest(Contract):
    path: str
    perception: PerceptionSettings
    force: bool = False


class CameraRequest(Contract):
    index: int = Field(default=0, ge=0, le=32)
    perception: PerceptionSettings


class TransportRequest(Contract):
    playing: bool | None = None
    position_s: Number | None = Field(default=None, ge=0)
    loop: bool | None = None


class PersonRequest(Contract):
    person_id: str


class CalibrationRequest(Contract):
    reuse_id: str | None = None


def _local_request(headers):
    host = headers.get("host", "")
    if urlsplit(f"http://{host}").hostname not in {"localhost", "127.0.0.1", "::1"}:
        return False
    origin = headers.get("origin")
    return origin is None or origin in {f"http://{host}", f"https://{host}"}


def create_app(data_dir: Path, *, store: SessionStore | None = None, runtime=None) -> FastAPI:
    session = store or SessionStore(data_dir)

    @asynccontextmanager
    async def lifespan(app):
        if runtime is not None:
            runtime.start()
        try:
            yield
        finally:
            if runtime is not None:
                runtime.close()
            if store is None:
                session.close()

    app = FastAPI(title="Laboratorio corporal", version="1", lifespan=lifespan)
    app.state.session_store = session
    app.state.runtime = runtime

    @app.middleware("http")
    async def local_origin(request: Request, call_next):
        if not _local_request(request.headers):
            return JSONResponse({"error": "local_origin_required"}, status_code=403)
        return await call_next(request)

    @app.exception_handler(RevisionConflict)
    async def conflict(request, exc):
        return JSONResponse({"error": "revision_conflict", "detail": str(exc),
                             "state": session.snapshot()}, status_code=409)

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({"error": "invalid_configuration", "detail": str(exc)}, status_code=422)

    @app.exception_handler(KeyError)
    async def absent(request, exc):
        return JSONResponse({"error": "not_found"}, status_code=404)

    @app.exception_handler(RequestValidationError)
    async def bad_request(request, exc):
        # Never echo invalid raw NaN values into a JSON response.
        return JSONResponse({"error": "invalid_request", "detail": [
            {"loc": list(e["loc"]), "message": e["msg"]} for e in exc.errors()]}, status_code=422)

    def snapshot():
        state = session.snapshot()
        if runtime is not None:
            state.update(runtime.snapshot())
        return state

    @app.get("/api/state")
    def state():
        return snapshot()

    @app.get("/api/schemas")
    def schemas():
        return {c.__name__: c.model_json_schema() for c in PERSISTED_CONTRACTS}

    @app.put("/api/configuration")
    def configure(body: ConfigurationRequest):
        return session.edit(body.preset, body.expected_revision)

    @app.post("/api/undo")
    def undo(body: RevisionRequest):
        return session.history(body.expected_revision)

    @app.post("/api/redo")
    def redo(body: RevisionRequest):
        return session.history(body.expected_revision, redo=True)

    @app.post("/api/macros/{macro_id}")
    def macro(macro_id: str, body: MacroRequest):
        return session.apply_macro(macro_id, body.value, body.expected_revision)

    @app.get("/api/presets")
    def presets():
        return session.list_presets()

    @app.post("/api/presets")
    def save_preset(body: Preset):
        return session.save(body)

    @app.get("/api/presets/{preset_id}")
    def export_preset(preset_id: str):
        return session.load(preset_id).model_dump()

    @app.post("/api/presets/{preset_id}/apply")
    def apply_preset(preset_id: str, body: RevisionRequest):
        return session.edit(session.load(preset_id), body.expected_revision, reason="preset_apply")

    @app.get("/api/calibrations")
    def calibrations():
        return session.calibrations()

    @app.get("/api/events")
    def events():
        return session.events()

    @app.post("/api/marks")
    def mark(body: MarkRequest):
        session.mark(body.text)
        return {"ok": True}

    if runtime is not None:
        @app.get("/api/signals")
        def signals():
            from .routing import signal_catalog
            return signal_catalog()

        @app.get("/api/media")
        def media():
            return runtime.library.list_assets()

        @app.post("/api/sources/video")
        def open_video(body: VideoRequest):
            return runtime.open_video(body.path, body.perception, body.force)

        @app.post("/api/sources/camera")
        def open_camera(body: CameraRequest):
            return runtime.open_camera(body.index, body.perception)

        @app.get("/api/media/{job_id}/file")
        def video_file(job_id: str):
            return FileResponse(runtime.library.path(job_id))

        @app.post("/api/media/{job_id}/cancel")
        def cancel_video(job_id: str):
            return runtime.library.cancel(job_id)

        @app.get("/api/camera/preview")
        def camera_preview():
            import base64
            jpeg = runtime.camera.jpeg
            return Response(base64.b64decode(jpeg) if jpeg else b"", media_type="image/jpeg",
                            status_code=200 if jpeg else 204, headers={"Cache-Control":"no-store"})

        @app.post("/api/transport")
        def transport(body: TransportRequest):
            return runtime.control(**body.model_dump())

        @app.post("/api/person")
        def person(body: PersonRequest):
            runtime.select_person(body.person_id)
            return snapshot()

        @app.post("/api/calibrate")
        def calibrate(body: CalibrationRequest):
            return runtime.calibrate(body.reuse_id)

    @app.websocket("/ws")
    async def live(websocket: WebSocket):
        if not _local_request(websocket.headers):
            await websocket.close(code=1008)
            return
        await websocket.accept()
        try:
            while True:
                # No event backlog. Each client reads the latest complete snapshot.
                await asyncio.wait_for(websocket.send_json(snapshot()), timeout=2)
                await asyncio.sleep(1 / 30)
        except (WebSocketDisconnect, RuntimeError, OSError, asyncio.TimeoutError):
            pass

    return app
