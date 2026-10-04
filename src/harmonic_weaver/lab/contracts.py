"""Versioned laboratory contracts. JSON is the portable representation.

Observations never belong to a Preset. Time fields name their clock explicitly;
missing measurements use None plus a state, never a manufactured zero.
"""
from __future__ import annotations

from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from harmonic_weaver.engine.compiler import validate_json_finite
from harmonic_weaver.engine.errors import WeaverError

Number = Annotated[float, Field(allow_inf_nan=False)]
Identifier = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,79}$")]
Observation = Literal["observed", "held", "missing"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)

    @model_validator(mode="before")
    @classmethod
    def finite_tree(cls, value):
        try:
            validate_json_finite(value)
        except WeaverError as exc:
            raise ValueError("configuration/telemetry must contain finite numbers") from exc
        return value


class Joint(Contract):
    index: int = Field(ge=0, le=16)
    position: list[Number] | None = None
    confidence: Number = Field(default=0, ge=0, le=1)
    state: Observation = "missing"

    @model_validator(mode="after")
    def presence(self):
        if self.state != "missing" and self.position is None:
            raise ValueError("observed/held joints require coordinates")
        if self.position is not None and len(self.position) not in (2, 3):
            raise ValueError("coordinates must be 2D or 3D")
        return self


class Person(Contract):
    person_id: str
    joints: list[Joint]

    @model_validator(mode="after")
    def unique_joints(self):
        if len({j.index for j in self.joints}) != len(self.joints):
            raise ValueError("duplicate joint index")
        return self


class MotionFrame(Contract):
    schema_version: Literal[1] = 1
    source_id: str
    stream_id: str
    sequence: int = Field(ge=0)
    source_time_s: Number = Field(ge=0)
    available_monotonic_s: Number = Field(ge=0)
    captured_monotonic_s: Number | None = Field(default=None, ge=0)
    duration_s: Number | None = Field(default=None, ge=0)
    timestamp_origin: Literal["pts", "capture", "index_fps", "synthetic"]
    source_pts: int | None = None
    time_base_num: int | None = None
    time_base_den: int | None = Field(default=None, gt=0)
    coordinate_frame: Literal["camera_isotropic", "world"] = "camera_isotropic"
    unit: Literal["frame_height", "meter"] = "frame_height"
    dimensions: Literal[2, 3] = 2
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    persons: list[Person] = Field(default_factory=list)

    @model_validator(mode="after")
    def shape(self):
        if len({p.person_id for p in self.persons}) != len(self.persons):
            raise ValueError("duplicate person identity")
        for person in self.persons:
            for joint in person.joints:
                if joint.position is not None and len(joint.position) != self.dimensions:
                    raise ValueError("joint dimension differs from frame")
        return self


class Signal(Contract):
    value: Number | None
    unit: str
    state: Observation = "observed"
    reason: str | None = None

    @model_validator(mode="after")
    def measured(self):
        if self.state == "observed" and self.value is None:
            raise ValueError("observed signal requires a value")
        return self


class FeatureFrame(Contract):
    schema_version: Literal[1] = 1
    source_time_s: Number
    available_monotonic_s: Number
    person_id: str | None
    algorithm_id: str
    algorithm_version: Literal[1] = 1
    lookahead_s: Number = Field(default=0, ge=0)
    signals: dict[str, Signal] = Field(default_factory=dict)
    diagnostics: dict = Field(default_factory=dict)


class ControlDescriptor(Contract):
    key: str
    label: str
    kind: Literal["number", "integer", "boolean", "choice"]
    default: Number | int | bool | str
    unit: str = "1"
    minimum: Number | None = None
    maximum: Number | None = None
    choices: list[str] = Field(default_factory=list)
    help: str
    application: Literal["tick", "reset", "visual"] = "tick"


class AlgorithmDescriptor(Contract):
    id: Identifier
    version: Literal[1] = 1
    label: str
    inputs: list[str]
    outputs: dict[str, str]
    controls: list[ControlDescriptor] = Field(default_factory=list)
    causal: bool = True
    warmup_s: Number = Field(default=0, ge=0)
    cost: Literal["light", "windowed"] = "light"
    description: str


class AlgorithmSettings(Contract):
    id: Literal["baseline", "local", "relational", "angular", "collective"] = "baseline"
    version: Literal[1] = 1
    reference: Literal["camera", "pelvis", "torso", "fixed"] = "camera"
    fixed_x: Number = Field(default=0, ge=-10, le=10)
    fixed_y: Number = Field(default=0, ge=-10, le=10)
    joints: list[int] = Field(default_factory=lambda: list(range(5, 17)), min_length=2, max_length=17)
    tracking_filter_enabled: bool = False
    tracking_smoother: Literal["bounded", "harmocap_one_euro"] = "bounded"
    tracking_one_euro_mincutoff: Number = Field(default=1., ge=.01, le=30)
    tracking_one_euro_beta: Number = Field(default=.15, ge=0, le=20)
    tracking_one_euro_dcutoff: Number = Field(default=1., ge=.01, le=30)
    tracking_hip_swap_guard: bool = True
    tracking_median_frames: int = Field(default=3, ge=1, le=9)
    tracking_smoothing_s: Number = Field(default=.05, ge=0, le=.5)
    tracking_joint_accel_limits: list[Annotated[float, Field(ge=.1, le=2000, allow_inf_nan=False)]] = Field(
        default_factory=lambda: [80.,100.,100.,100.,100.,60.,60.,120.,120.,240.,240.,35.,35.,100.,100.,180.,180.],
        min_length=17, max_length=17,
        description="Per COCO-17 joint acceleration limits in projected torso lengths/s²; tuning parameters, not anatomical bounds.")
    smoothing_s: Number = Field(default=0, ge=0, le=2)
    derivative_window_s: Number = Field(default=.12, ge=.02, le=.5)
    horizon_s: Number = Field(default=.15, ge=.01, le=2)
    history_s: Number = Field(default=.25, ge=.05, le=5)
    noise_velocity: Number = Field(default=.02, ge=.0001, le=2)
    noise_delta: Number = Field(default=.015, ge=.0001, le=2)
    relation_reference: Literal["history", "instantaneous"] = "history"
    window_s: Number = Field(default=2, ge=.3, le=10)
    components: int = Field(default=3, ge=1, le=12)
    collective_support: Literal["fixed", "observed"] = Field(default="fixed",
        description="fixed requires every selected coordinate; observed uses only coordinates observed throughout the current causal window, without filling gaps.")
    ridge: Number = Field(default=.1, ge=.00001, le=100)
    lag_s: Number = Field(default=.12, ge=.02, le=1)
    propagation_interval_s: Number = Field(default=.2, ge=.03, le=2)
    event_threshold: Number = Field(default=2, ge=.1, le=50)
    refractory_s: Number = Field(default=.25, ge=.02, le=3)
    event_duration_s: Number = Field(default=.15, ge=.02, le=2)
    max_gap_s: Number = Field(default=.25, ge=.05, le=2)

    @model_validator(mode="after")
    def selection(self):
        if len(set(self.joints)) != len(self.joints) or any(j < 0 or j > 16 for j in self.joints):
            raise ValueError("joints must be unique COCO-17 indices")
        return self


class ZoneSettings(Contract):
    sensitivity: Number = Field(default=1, ge=0, le=8)
    distance: Number = Field(default=0, ge=0, le=5)
    speed_range: Number = Field(default=.6, ge=.02, le=10)
    accel_range: Number = Field(default=6, ge=.1, le=100)


class ResponseSettings(Contract):
    core_falloff: Number = Field(default=.75, ge=0, le=3)
    snap: Number = Field(default=0, ge=0, le=1)
    phase_depth: Number = Field(default=45, ge=0, le=180)
    pluck_enabled: bool = True
    attack_ms: Number = Field(default=80, ge=10, le=500)
    tail_ms: Number = Field(default=700, ge=50, le=3000)
    impulse_threshold: Number = Field(default=.15, ge=.01, le=2)
    zones: list[ZoneSettings] = Field(default_factory=lambda: [
        ZoneSettings(distance=float(d)) for d in (0, 1, 1, 2, 2, 3)], min_length=6, max_length=6)


class VoiceSettings(Contract):
    id: int = Field(ge=1, le=32)
    label: str = Field(max_length=80)
    ratio: Number = Field(gt=0, le=64)
    gain: Number = Field(default=1, ge=0, le=2)
    detune: Number = Field(default=0, ge=-.99, le=1)
    phase_deg: Number = Field(default=0, ge=-360, le=360)
    pan: Number = Field(default=0, ge=-1, le=1)
    shape: Number = Field(default=0, ge=0, le=1)
    muted: bool = False
    solo: bool = False


class MappingTerm(Contract):
    source: str = Field(min_length=1, max_length=100)
    input_unit: str = "1"
    weight: Number = Field(default=1, ge=-100, le=100)
    offset: Number = Field(default=0, ge=-1000, le=1000)
    exponent: Number = Field(default=1, ge=.1, le=5)
    deadband: Number = Field(default=0, ge=0, le=100)
    absolute: bool = False


class Route(Contract):
    id: Identifier
    voice: int = Field(ge=1, le=32)
    target: Literal["gain", "detune", "phase_deg", "pan"]
    terms: list[MappingTerm] = Field(min_length=1, max_length=32)
    mix: Literal["sum", "mean", "max", "product"] = "sum"
    enabled: bool = True
    clamp_min: Number = -1
    clamp_max: Number = 1
    smoothing_s: Number = Field(default=0, ge=0, le=2)
    missing: Literal["silence", "zero"] = "silence"

    @model_validator(mode="after")
    def bounds(self):
        if self.clamp_min >= self.clamp_max:
            raise ValueError("route clamp must be increasing")
        return self


class VisualSettings(Contract):
    window_periods: Number = Field(default=2, ge=.1, le=30)
    samples: int = Field(default=2400, ge=256, le=12000)
    persistence: Number = Field(default=.65, ge=0, le=.98)
    line_width: Number = Field(default=1.5, ge=.5, le=6)
    brightness: Number = Field(default=.8, ge=.1, le=2)
    scale: Number = Field(default=1, ge=.1, le=5)
    auto_scale: bool = True
    components: bool = False
    color: Literal["ice", "gold", "violet"] = "ice"
    mirror_video: bool = False
    show_skeleton: bool = True
    show_raw_tracking: bool = False
    collective_view: Literal["off", "projector", "basis"] = "off"
    collective_max_axes: int = Field(default=12, ge=2, le=34)
    on_disconnect: Literal["clear", "freeze"] = "clear"


class MacroTarget(Contract):
    path: str
    minimum: Number
    maximum: Number


class Macro(Contract):
    id: Identifier
    label: str
    value: Number = Field(default=.5, ge=0, le=1)
    targets: list[MacroTarget] = Field(min_length=1, max_length=16)


def initial_voices():
    return [VoiceSettings(id=i, label=label, ratio=float(i)) for i, label in enumerate(
        ["Caderas", "Hombros", "Rodillas", "Codos", "Tobillos", "Muñecas"], 1)]


def initial_routes():
    return [Route(id=f"zone-{i}-{target}", voice=i, target=target,
                  terms=[MappingTerm(source=f"zone.{i}.{target}", input_unit="deg" if target == "phase_deg" else "1")],
                  clamp_min=0.0 if target == "gain" else (-180.0 if target == "phase_deg" else -1.0),
                  clamp_max=180.0 if target == "phase_deg" else 1.0)
            for i in range(1, 7) for target in ("gain", "detune", "phase_deg")]


class Preset(Contract):
    schema_version: Literal[1] = 1
    id: Identifier = Field(default_factory=lambda: uuid4().hex)
    name: str = Field(default="Seis zonas · plucks", min_length=1, max_length=100)
    favorite: bool = False
    algorithm: AlgorithmSettings = Field(default_factory=AlgorithmSettings)
    response: ResponseSettings = Field(default_factory=ResponseSettings)
    fundamental_hz: Number = Field(default=40.4, ge=10, le=440)
    master: Number = Field(default=.7, ge=0, le=1)
    expression: Number = Field(default=0, ge=-1, le=10)
    transient_mix: Number = Field(default=0, ge=0, le=1)
    transient_decay_s: Number = Field(default=.15, ge=.02, le=2)
    expression_window_s: Number = Field(default=.12, ge=.02, le=1)
    voices: list[VoiceSettings] = Field(default_factory=initial_voices, min_length=6, max_length=32)
    routes: list[Route] = Field(default_factory=initial_routes, max_length=128)
    macros: list[Macro] = Field(default_factory=list, max_length=12)
    visual: VisualSettings = Field(default_factory=VisualSettings)
    pause_behavior: Literal["release", "silence"] = "release"
    release_ms: Number = Field(default=150, ge=0, le=2000)

    @model_validator(mode="after")
    def destinations(self):
        ids = {v.id for v in self.voices}
        if len(ids) != len(self.voices):
            raise ValueError("duplicate voice ID")
        if len({r.id for r in self.routes}) != len(self.routes):
            raise ValueError("duplicate route ID")
        destinations = set()
        for route in self.routes:
            if route.voice not in ids:
                raise ValueError("route points to absent voice")
            dest = (route.voice, route.target)
            if route.enabled and dest in destinations:
                raise ValueError("one final writer per destination; mix terms in one route")
            if route.enabled:
                destinations.add(dest)
        if len({m.id for m in self.macros}) != len(self.macros):
            raise ValueError("duplicate macro ID")
        return self


class Calibration(Contract):
    schema_version: Literal[1] = 1
    id: Identifier = Field(default_factory=lambda: uuid4().hex)
    source_id: str
    person_id: str
    torso_scale: Number = Field(gt=0)
    measured_at: str
    provenance: str
    policy: Literal["new_source", "reuse_explicit"] = "new_source"


class SessionState(Contract):
    schema_version: Literal[1] = 1
    session_id: str = Field(default_factory=lambda: uuid4().hex)
    desired_revision: int = Field(default=0, ge=0)
    applied_revision: int | None = Field(default=None, ge=0)
    analysis_epoch: int = Field(default=0, ge=0)
    source_id: str | None = None
    person_id: str | None = None
    calibration_id: str | None = None
    position_s: Number = Field(default=0, ge=0)
    playing: bool = False
    loop: bool = True
    status: str = "idle"
    error: str | None = None


class SessionEvent(Contract):
    schema_version: Literal[1] = 1
    session_id: str
    monotonic_s: Number
    source_time_s: Number | None = None
    kind: Literal["configuration", "preset_save", "mark", "calibration", "source", "transport", "person"]
    revision: int
    payload: dict


class EffectiveVoice(Contract):
    voice_id: int
    harmonic_n: int
    frequency_hz: Number = Field(ge=0)
    gain_end: Number | None = None
    phase_offset_delta_rad: Number = 0
    gain: Number = Field(ge=0)
    phase_rad: Number
    envelope: Number = Field(ge=0)
    pan: Number = Field(ge=-1, le=1)
    shape: Number = Field(ge=0, le=1)
    releasing: bool


class VoiceFrame(Contract):
    schema_version: Literal[1] = 1
    sample_index: int = Field(ge=0)
    sample_rate: int = Field(gt=0)
    block_frames: int = Field(gt=0)
    generated_monotonic_s: Number
    control_owner: str | None = None
    control_sequence: int | None = Field(default=None, ge=0)
    control_applied_monotonic_s: Number | None = None
    control_sampled_monotonic_s: Number | None = None
    output_dac_time_s: Number | None = None
    running: bool
    stage: Literal["oscillators_pre_shape_limiter"] = "oscillators_pre_shape_limiter"
    voices: list[EffectiveVoice]


PERSISTED_CONTRACTS = (MotionFrame, FeatureFrame, AlgorithmDescriptor, Preset,
                       Calibration, SessionState, SessionEvent, VoiceFrame)


class PerceptionSettings(Contract):
    """Source-specific settings; deliberately outside portable musical presets."""
    checkpoint: str = Field(min_length=1)
    device: str = "auto"
    imgsz: int = Field(default=320, ge=160, le=1280, multiple_of=32)
    confidence: Number = Field(default=.3, ge=.01, le=1)
    joint_confidence: Number = Field(default=.3, ge=.01, le=1)
    max_detections: int = Field(default=6, ge=1, le=32)
    max_slots: int = Field(default=4, ge=1, le=8)
    tracker: Literal["bytetrack.yaml", "botsort.yaml"] = "bytetrack.yaml"
    reacquisition: bool = True
    camera_width: int = Field(default=1280, ge=160, le=3840)
    camera_height: int = Field(default=720, ge=120, le=2160)
    camera_fps: int = Field(default=30, ge=1, le=120)


PERSISTED_CONTRACTS += (PerceptionSettings,)
