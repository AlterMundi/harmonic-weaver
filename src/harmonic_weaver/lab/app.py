"""HTTP resources and latest-state WebSocket for the local laboratory."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlsplit

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Query
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
from .research.relational_bank import Settings as RelationalSettings
from .research.relational_service import RelationalService
from .research.activation_service import ActivationService
from .research.membrane_service import MembraneService
from .research.membrane_pcm import Request as MembraneRequest
from .research.activation_bank import Settings as ActivationSettings,schedules as activation_schedules
from .research.resonator_service import ResonatorService
from .research.resonators import Settings as ResonatorSettings
from .research.excitation import Settings as ExcitationSettings
from .research.resonator_render import Settings as ResonatorRenderSettings
from .research.parameter_render import Settings as MappingSettings
from .research.model_projection import Request as ModelProjectionRequest
from .research.model_projection import Configuration as ModelProjectionConfiguration
from .research.relational_input import EndpointRequest
from .research.body import BodyRequest
from .research.candidate_input import CandidateRequest, candidate_snapshot
from .research.coincidence import content_hash
from .research.coincidence_service import CoincidenceService
from .research.mark_input import verified_marks, verify_source_binding


class RevisionRequest(Contract):
    expected_revision: int = Field(ge=0)


class ConfigurationRequest(RevisionRequest):
    preset: Preset


class MacroRequest(RevisionRequest):
    value: Number = Field(ge=0, le=1)


class MarkRequest(Contract):
    category: Literal["note","preparation","deployment","release","experience"] = "note"
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


class CoincidenceRequest(Contract):
    candidate: CandidateRequest
    source_id: str = Field(min_length=1)
    person_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    observed_epoch: int = Field(ge=0)
    category: Literal["note", "preparation", "deployment", "release", "experience"]
    through_sequence: int = Field(ge=0)
    mark_support: list[Annotated[list[Number], Field(min_length=2, max_length=2)]] = Field(min_length=1, max_length=500)
    control_offsets_s: list[Number] = Field(default_factory=list, max_length=16)
    tolerance_s: Number = Field(default=.2, ge=0, le=10)
    mark_offset_s: Number = Field(default=0, ge=-10, le=10)


class RelationalBodyRequest(Contract):
    settings: RelationalSettings = Field(default_factory=RelationalSettings)
    selection: EndpointRequest


class ResonatorSelection(Contract):
    evaluation_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    run_index: int = Field(ge=0)
    signal_id: str = Field(min_length=1,max_length=200)
    start_s: Number = Field(default=0,ge=0)
    end_s: Number = Field(gt=0)


class ResonatorRequest(Contract):
    selection: ResonatorSelection
    resonators: ResonatorSettings = Field(default_factory=ResonatorSettings)
    excitation: ExcitationSettings = Field(default_factory=ExcitationSettings)
    render: ResonatorRenderSettings = Field(default_factory=ResonatorRenderSettings)
    mapping: MappingSettings | None = None


class ActivationConfig(Contract):
    schema_version:Literal[1]=1
    settings:ActivationSettings=Field(default_factory=ActivationSettings)


class MembranePlayback(Contract):
    follow_audio:bool=False
    loop_audio:bool=False
    color_scale:Number=Field(default=10000,ge=0,le=1e12)


class MembraneConfig(Contract):
    schema_version:Literal[1]=1
    settings:MembraneRequest=Field(default_factory=lambda:MembraneRequest(stop_sample_exclusive=48000))
    playback:MembranePlayback=Field(default_factory=MembranePlayback)


class MembraneStart(Contract):
    source_run_id:str
    settings:MembraneRequest


class ResonatorConfig(Contract):
    schema_version: Literal[1] = 1
    resonators: ResonatorSettings = Field(default_factory=ResonatorSettings)
    excitation: ExcitationSettings = Field(default_factory=ExcitationSettings)
    render: ResonatorRenderSettings = Field(default_factory=ResonatorRenderSettings)
    mapping: MappingSettings | None = None


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
    coincidence = CoincidenceService(data_dir)
    relational = RelationalService(data_dir)
    resonators = ResonatorService(data_dir)
    activation = ActivationService(data_dir)
    membrane = MembraneService(data_dir)
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
            activation.close()
            membrane.close()
            resonators.close()
            relational.close()
            coincidence.close()
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

    @app.get("/api/research/r01/{ident}/artifacts/{name}")
    def research_artifact(ident: str, name: str):
        return FileResponse(research.artifact(ident,name),filename=name)

    @app.post("/api/research/r01")
    def research_r01(body: GrassmannSettings):return research.start(body.model_dump())

    @app.post("/api/research/r01/{ident}/cancel")
    def research_cancel(ident: str):return research.cancel(ident)

    @app.post("/api/research/r01/trace")
    def research_body(body: BodyRequest):
        if evaluation is None:raise ValueError('No comparison library available')
        return research.start_body(body.model_dump(),evaluation)

    @app.get("/api/research/r03")
    def coincidence_jobs():return coincidence.list()

    @app.get("/api/research/r03/{ident}/artifacts/{name}")
    def coincidence_artifact(ident: str, name: str):
        return FileResponse(coincidence.artifact(ident,name),filename=name)

    @app.post("/api/research/r03/{ident}/cancel")
    def coincidence_cancel(ident: str):return coincidence.cancel(ident)

    @app.post("/api/research/r03")
    def coincidence_start(body: CoincidenceRequest):
        if evaluation is None:raise ValueError('No comparison library available')
        # Explicit coverage is never inferred from human button events.
        from .research.temporal_match import compare_events
        compare_events([], [], body.mark_support, [], tolerance_s=body.tolerance_s,
                       mark_offset_s=body.mark_offset_s)
        if body.control_offsets_s:
            from .research.temporal_controls import compare_shifts
            compare_shifts([],[],body.mark_support,[],offsets_s=body.control_offsets_s,
                           tolerance_s=body.tolerance_s,mark_offset_s=body.mark_offset_s)
        context={name:getattr(body,name) for name in
                 ('source_id','person_id','session_id','observed_epoch','category')}
        marks=session.marks_snapshot(**context,through_sequence=body.through_sequence)
        verified_marks(marks,**context)
        features=candidate_snapshot(evaluation,body.candidate)
        verify_source_binding(marks,features)
        if features['provenance']['source']['person_id']!=body.person_id:
            raise ValueError('Replay person differs from annotation person')
        request={'feature_sha256':content_hash(features),'context':context,
                 'mark_support':body.mark_support,'tolerance_s':body.tolerance_s,
                 'mark_offset_s':body.mark_offset_s,'control_offsets_s':body.control_offsets_s}
        return coincidence.start(request,marks,features)

    @app.get("/api/research/r04")
    def relational_jobs():return relational.list()

    @app.post("/api/research/r04")
    def relational_start(body: RelationalSettings):return relational.start(body.model_dump())

    @app.post("/api/research/r04/trace")
    def relational_trace(body: RelationalBodyRequest):
        if evaluation is None:raise ValueError('No comparison library available')
        return relational.start_body(body.settings,body.selection,evaluation)

    @app.post("/api/research/r04/{ident}/cancel")
    def relational_cancel(ident: str):return relational.cancel(ident)

    @app.get("/api/research/r04/{ident}/artifacts/{name}")
    def relational_artifact(ident: str, name: str):
        return FileResponse(relational.artifact(ident,name),filename=name)

    @app.get("/api/research/r06")
    def activation_jobs():return activation.list()

    @app.get('/api/research/r07')
    def membrane_jobs():return membrane.list()

    @app.post('/api/research/r07/configuration')
    def membrane_configuration(body:MembraneConfig):return body.model_dump()

    @app.post('/api/research/r07')
    def membrane_start(body:MembraneStart):
        source=resonators.folder(body.source_run_id)
        return membrane.start(source,body.settings.model_dump())

    @app.get('/api/research/r07/{ident}')
    def membrane_report(ident:str):return membrane.report(ident)

    @app.post('/api/research/r07/{ident}/cancel')
    def membrane_cancel(ident:str):return membrane.cancel(ident)

    @app.get('/api/research/r07/{ident}/artifacts/{name}')
    def membrane_artifact(ident:str,name:str):
        return FileResponse(membrane.artifact(ident,name),filename=name)

    @app.get('/api/research/r07/{ident}/listen')
    def membrane_listen(ident:str,request:Request,gain:float=Query(default=1,ge=0,le=10)):
        from .research.audio_preview import preview_response
        return preview_response(membrane.audio_source(ident),gain=gain,range_header=request.headers.get('range'))

    @app.post("/api/research/r06/configuration")
    def activation_configuration(body:ActivationConfig):
        activation_schedules(body.settings)
        return body.model_dump()

    @app.post("/api/research/r06")
    def activation_start(body:ActivationSettings):return activation.start(body.model_dump())

    @app.get("/api/research/r06/{ident}")
    def activation_report(ident:str):return activation.report(ident)

    @app.post("/api/research/r06/{ident}/cancel")
    def activation_cancel(ident:str):return activation.cancel(ident)

    @app.get("/api/research/r06/{ident}/artifacts/{name}")
    def activation_artifact(ident:str,name:str):
        return FileResponse(activation.artifact(ident,name),filename=name)

    @app.get("/api/research/r05")
    def resonator_jobs(): return resonators.list()

    @app.post("/api/research/r05/configuration")
    def resonator_configuration(body: ResonatorConfig):
        if len(body.excitation.voice_weights) != len(body.resonators.ratios):
            raise ValueError('One explicit excitation weight per resonator required')
        if body.mapping is not None and len(body.mapping.voice_weights)!=len(body.resonators.ratios):
            raise ValueError('One mapping weight per carrier required')
        result=body.model_dump()
        if body.mapping is None:result.pop('mapping')
        else:
            from .research.parameter_render import validate_frequency
            validate_frequency(body.resonators,body.mapping)
            result['mapping']=body.mapping.model_dump(exclude_none=True)
        return result

    @app.post("/api/research/r05/projection/configuration")
    def projection_configuration(body: ModelProjectionConfiguration):
        result=body.model_dump()
        if body.playback is None:result.pop('playback')
        return result

    @app.post("/api/research/r05")
    def resonator_start(body: ResonatorRequest):
        if evaluation is None: raise ValueError('No comparison library available')
        candidate = CandidateRequest.model_validate({**body.selection.model_dump(),
            **{name:getattr(body.excitation,name) for name in ('high','low','refractory_s','max_gap_s')}})
        features = candidate_snapshot(evaluation,candidate)
        parameters={name:getattr(body,name).model_dump() for name in ('resonators','excitation','render')}
        if body.mapping is not None:parameters['mapping']=body.mapping.model_dump(exclude_none=True)
        return resonators.start(parameters,features)

    @app.post("/api/research/r05/{ident}/cancel")
    def resonator_cancel(ident: str): return resonators.cancel(ident)

    @app.get("/api/research/r05/{ident}/artifacts/{name}")
    def resonator_artifact(ident: str,name: str):
        return FileResponse(resonators.artifact(ident,name),filename=name)

    @app.post("/api/research/r05/{ident}/projection")
    def resonator_projection(ident: str,body: ModelProjectionRequest):
        return resonators.projection(ident,body)

    @app.get("/api/research/r05/{ident}/listen/{arm}")
    def resonator_listen(ident: str,arm: Literal['single','excited','mapped'],request: Request,
                        gain: float=Query(default=1,ge=0,le=10,allow_inf_nan=False)):
        from .research.audio_preview import preview_response
        name='sum.wav' if arm=='single' else f'{arm}-sum.wav'
        path=resonators.artifact(ident,name)
        return preview_response(path,gain=gain,range_header=request.headers.get('range'))

    def resolve_resonator_source(ident):
        if evaluation is None:raise ValueError('No comparison library available')
        import json
        from .research.source_binding import source_binding
        document=json.loads(resonators.artifact(ident,'input.json').read_text())
        return source_binding(evaluation,document)

    @app.get("/api/research/r05/{ident}/source-pose")
    def resonator_source_pose(ident: str):
        if evaluation is None:raise ValueError('No comparison library available')
        import json
        from .research.source_binding import source_pose
        document=json.loads(resonators.artifact(ident,'input.json').read_text())
        return source_pose(evaluation,document)

    @app.get("/api/research/r05/{ident}/source-info")
    def resonator_source_info(ident: str):return resolve_resonator_source(ident)[1]

    @app.get("/api/research/r05/{ident}/source")
    def resonator_source_file(ident: str):return FileResponse(resolve_resonator_source(ident)[0])

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

    @app.get("/api/marks/snapshot")
    def marks_snapshot(source_id: str | None = None, person_id: str | None = None,
                       start_s: float | None = None, end_s: float | None = None, category: str | None = None,
                       session_id: str | None = None, observed_epoch: int | None = None, through_sequence: int | None = None):
        return JSONResponse(session.marks_snapshot(source_id=source_id,person_id=person_id,start_s=start_s,end_s=end_s,category=category,session_id=session_id,observed_epoch=observed_epoch,through_sequence=through_sequence),headers={"Content-Disposition":'attachment; filename="movement-marks.json"'})

    @app.post("/api/marks")
    def mark(body: MarkRequest):
        (runtime.mark if runtime is not None and hasattr(runtime,"mark") else session.mark)(body.text, category=body.category)
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
                media_type="audio/wav" if path.suffix == ".wav" else "application/json" if path.suffix=='.json' else "application/x-ndjson")

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
