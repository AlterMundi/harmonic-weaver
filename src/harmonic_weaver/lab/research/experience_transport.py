"""Browser-declared R10 transport telemetry, never proof of human exposure."""
from typing import Literal
from pydantic import Field, model_validator
from ..contracts import Contract


class MediaState(Contract):
    current_time_s: float = Field(ge=0)
    paused: bool
    muted: bool
    volume: float = Field(ge=0, le=1)
    ready_state: int = Field(ge=0, le=4)
    seeking: bool
    ended: bool
    playback_rate: float = Field(gt=0, le=16)


class Event(Contract):
    sequence: int = Field(ge=0)
    monotonic_s: float = Field(ge=0)
    elapsed_s: float = Field(ge=0)
    epoch: int = Field(ge=0)
    kind: Literal['prepared', 'play_requested', 'pause', 'seek', 'waiting',
                  'media_error', 'nominal_end', 'snapshot', 'closed']
    video: MediaState | None = None
    audio: MediaState | None = None


class Trace(Contract):
    schema_version: Literal[1] = 1
    protocol_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    protocol_manifest_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    trial_id: str = Field(min_length=1, max_length=80)
    duration_s: float = Field(gt=0, le=120)
    video_enabled: bool
    audio_enabled: bool
    events: list[Event] = Field(min_length=1, max_length=20000)

    @model_validator(mode='after')
    def timeline(self):
        previous = None
        for index, event in enumerate(self.events):
            if event.sequence != index:
                raise ValueError('Transport event sequence must be contiguous from zero')
            if event.elapsed_s > self.duration_s:
                raise ValueError('Transport elapsed position exceeds trial duration')
            if event.video is not None and not self.video_enabled:
                raise ValueError('Video telemetry contradicts disabled video condition')
            if event.audio is not None and not self.audio_enabled:
                raise ValueError('Audio telemetry contradicts disabled audio condition')
            if previous is not None:
                if event.monotonic_s < previous.monotonic_s or event.epoch < previous.epoch:
                    raise ValueError('Transport monotonic clock and epochs cannot go backward')
                if event.elapsed_s < previous.elapsed_s and event.epoch == previous.epoch:
                    raise ValueError('Backward transport movement requires a new epoch')
            previous = event
        return self


def summarize(trace):
    """Report declared facts only; no interpolation of exposure across samples."""
    trace = Trace.model_validate(trace)
    return {'schema_version': 1, 'protocol_id': trace.protocol_id,
            'protocol_manifest_sha256': trace.protocol_manifest_sha256,
            'trial_id': trace.trial_id, 'event_count': len(trace.events),
            'nominal_end_reported': any(e.kind == 'nominal_end' for e in trace.events),
            'closed_reported': any(e.kind == 'closed' for e in trace.events),
            'waiting_count': sum(e.kind == 'waiting' for e in trace.events),
            'seek_count': sum(e.kind == 'seek' for e in trace.events),
            'media_error_count': sum(e.kind == 'media_error' for e in trace.events),
            'limits': ['Browser-declared telemetry; not independently observed playback',
                       'Nominal end does not establish complete or uninterrupted exposure',
                       'No exposure duration inferred between sparse events',
                       'Muted/volume state does not establish physical level or human hearing']}
