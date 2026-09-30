"""HTTP resources and latest-state WebSocket for the local laboratory."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import Field

from .contracts import Contract, Number, PERSISTED_CONTRACTS, PerceptionSettings, Preset
from .store import RevisionConflict, SessionStore
from .evaluation.pcm import PCMSettings
from .capture import CaptureSettings, CaptureSession
from .capture_export import ExportSettings, CaptureExports
from .research.grassmann import Settings as GrassmannSettings
from .research.service import ResearchService


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


class EvaluationSegment(Contract):
    asset_id: str
    person_id: str
    start_s: Number = Field(default=0, ge=0)
    end_s: Number = Field(gt=0)
    calibration_id: str | None = None


class EvaluationRequest(Contract):
    preset_ids: list[str] = Field(min_length=1, max_length=32)
    segments: list[EvaluationSegment] = Field(min_length=1, max_length=32)
    control_hz: int = Field(default=60, ge=10, le=240)
    preroll_s: Number = Field(default=2, ge=0, le=30)
    pcm: PCMSettings = Field(default_factory=PCMSettings)


class CameraRequest(Contract):
    index: int = Field(default=0, ge=0, le=32)
    perception: PerceptionSettings


class TransportRequest(Contract):
    playing: bool | None = None
    position_s: Number | None = Field(default=None, ge=0)
    loop: bool | None = None


class SourcePreferencesRequest(Contract):
    default_person: Literal["best_coverage", "first"] = "best_coverage"
    autoplay_video: bool = True


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


def create_app(data_dir: Path, *, store: SessionStore | None = None, runtime=None,
               perception: PerceptionSettings | None = None, ui_dir: Path | None = None, capture_client_factory=None) -> FastAPI:
    session = store or SessionStore(data_dir)
    capture = CaptureSession(data_dir, session, runtime, client_factory=capture_client_factory) if runtime is not None else None
    exports = CaptureExports(capture) if capture is not None else None
    research = ResearchService(data_dir)
    evaluation = None
    if runtime is not None:
        from .evaluation.service import EvaluationService
        evaluation = EvaluationService(data_dir, session, runtime.library)

    @asynccontextmanager
    async def lifespan(app):
        if runtime is not None:
            runtime.start()
        try:
            yield
        finally:
            research.close()
            if exports is not None:
                exports.close()
            if capture is not None:
                capture.close()
            if evaluation is not None:
                evaluation.close()
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

    @app.get("/api/captures")
    def captures():
        return {"current":capture.snapshot(), "jobs":capture.list()} if capture else {"current":{"status":"idle"}, "jobs":[]}

    @app.post("/api/captures/start")
    def start_capture(body: CaptureSettings):
        if capture is None: raise ValueError("No hay runtime para capturar")
        return capture.start(body.model_dump())

    @app.post("/api/captures/stop")
    def stop_capture():
        return capture.stop() if capture else {"status":"idle"}

    @app.get("/api/capture-recovery")
    def capture_recovery_state():
        return capture.recovery_snapshot() if capture else {"status":"idle"}

    @app.post("/api/captures/{ident}/recover")
    def capture_recover(ident: str):
        if capture is None: raise ValueError("No hay runtime para recuperar")
        return capture.recover(ident)

    @app.get("/api/capture-exports")
    def capture_export_state():
        return exports.snapshot() if exports else {"status":"idle"}

    @app.get("/api/capture-exports/jobs")
    def capture_export_jobs():
        return exports.list() if exports else []

    @app.get("/api/capture-exports/{ident}/artifacts/{name}")
    def capture_export_artifact(ident: str, name: str):
        if exports is None: raise ValueError("No hay exportaciones")
        path=exports.artifact(ident,name)
        return FileResponse(path,filename=name)

    @app.post("/api/captures/{ident}/export")
    def capture_export(ident: str, body: ExportSettings):
        if exports is None: raise ValueError("No hay runtime para exportar")
        return exports.start(ident, body.model_dump())

    @app.post("/api/capture-exports/cancel")
    def capture_export_cancel():
        return exports.cancel() if exports else {"status":"idle"}

    @app.get("/api/research/r01")
    def research_jobs():return research.list()

    @app.post("/api/research/r01")
    def research_r01(body: GrassmannSettings):return research.start(body.model_dump())

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

    @app.get("/api/source-preferences")
    def source_preferences():
        return session.source_preferences()

    @app.post("/api/source-preferences")
    def set_source_preferences(body: SourcePreferencesRequest):
        return session.set_source_preferences(body.model_dump())

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
        @app.post("/api/evaluations")
        def start_evaluation(body: EvaluationRequest):
            return evaluation.start(body.preset_ids, [s.model_dump() for s in body.segments],
                                    control_hz=body.control_hz, preroll_s=body.preroll_s, pcm=body.pcm.model_dump())

        @app.get("/api/evaluations")
        def list_evaluations():
            return [evaluation.snapshot(i) for i in list(evaluation.jobs)]

        @app.get("/api/evaluations/{ident}")
        def evaluation_status(ident: str):
            return evaluation.snapshot(ident)

        @app.post("/api/evaluations/{ident}/cancel")
        def cancel_evaluation(ident: str):
            return evaluation.cancel(ident)

        @app.post("/api/evaluations/{ident}/repeat")
        def repeat_evaluation(ident: str):
            return evaluation.repeat(ident)

        @app.get("/api/evaluations/{ident}/artifacts/{filename}")
        def evaluation_artifact(ident: str, filename: str):
            path = evaluation.artifact(ident, filename)
            return FileResponse(path, filename=filename,
                media_type="audio/wav" if path.suffix == ".wav" else "application/x-ndjson")

        @app.get("/api/evaluations/{ident}/sources/{source_index}")
        def evaluation_source(ident: str, source_index: int):
            return FileResponse(evaluation.source_file(ident, source_index))

        @app.get("/api/evaluations/{ident}/report")
        def evaluation_report(ident: str):
            return evaluation.report(ident)

        @app.get("/api/environment")
        def environment():
            return {"perception":perception.model_dump() if perception else None}

        @app.get("/api/signals")
        def signals():
            from .routing import signal_catalog
            return signal_catalog()

        @app.get("/api/algorithms")
        def algorithms():
            from .registry import algorithm_descriptors
            return [descriptor.model_dump() for descriptor in algorithm_descriptors()]

        @app.get("/api/media")
        def media():
            return runtime.library.list_assets()

        @app.post("/api/sources/video")
        def open_video(body: VideoRequest):
            return runtime.open_video(body.path, body.perception, body.force)

        @app.post("/api/sources/upload")
        async def upload_video(file: UploadFile = File(...), perception_json: str = Form(...)):
            from uuid import uuid4
            settings = PerceptionSettings.model_validate_json(perception_json)
            suffix = Path(file.filename or "").suffix.lower()
            if suffix not in {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}:
                raise ValueError("choose a video file")
            uploads = data_dir / "uploads"
            uploads.mkdir(parents=True, exist_ok=True)
            path = uploads / (uuid4().hex + suffix)
            try:
                size = 0
                with path.open("xb") as output:
                    while chunk := await file.read(1024*1024):
                        size += len(chunk)
                        if size > 16*1024**3:
                            raise ValueError("upload exceeds 16 GiB; open the local path instead")
                        await asyncio.to_thread(output.write, chunk)
                return runtime.open_video(path, settings)
            except Exception:
                path.unlink(missing_ok=True)
                raise
            finally:
                await file.close()

        @app.post("/api/sources/camera")
        def open_camera(body: CameraRequest):
            return runtime.open_camera(body.index, body.perception)

        @app.post("/api/sources/close")
        def close_source():
            runtime.close_source()
            return snapshot()

        @app.post("/api/media/{job_id}/retry-cpu")
        def retry_cpu(job_id: str):
            return runtime.retry_cpu(job_id)

        @app.get("/api/media/{job_id}/quality")
        def media_quality(job_id: str, start_s: float = 0., end_s: float | None = None,
                          person_id: str | None = None):
            import math
            if not math.isfinite(start_s) or (end_s is not None and not math.isfinite(end_s)):
                raise ValueError("Los tiempos deben ser finitos")
            return runtime.library.quality_report(job_id, start_s, end_s, person_id)

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

    if ui_dir is not None and (ui_dir / "index.html").is_file():
        app.mount("/", StaticFiles(directory=ui_dir, html=True), name="laboratory-ui")
    return app
