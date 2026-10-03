"""R07 causal membrane RMS window from a verified single R05 PCM run."""
from pathlib import Path
from typing import Literal
from pydantic import Field, model_validator, model_serializer
import numpy as np
import soundfile as sf
from ..contracts import Contract
from ..cache import sha256_file
from .membrane import Settings, Membrane, FieldWindow, RollingFieldWindow


class Trajectory(Contract):
    window_samples: int = Field(default=4800, ge=1)
    hop_samples: int = Field(default=4800, ge=1)
from .resonator_artifacts import verify
from .mechanism_run import verify as verify_pair


class Request(Contract):
    arm: Literal['single', 'excited', 'mapped'] = 'single'
    membrane: Settings = Field(default_factory=Settings)
    start_sample: int = Field(default=0, ge=0)
    stop_sample_exclusive: int = Field(gt=0)
    grid_x: int = Field(default=33, ge=2, le=129)
    grid_y: int = Field(default=33, ge=2, le=129)
    block_size: int = Field(default=1024, ge=16, le=8192)
    trajectory: Trajectory | None = None

    @model_serializer(mode='wrap')
    def serialize(self, handler):
        value = handler(self)
        if self.trajectory is None: value.pop('trajectory', None)
        return value

    @model_validator(mode='after')
    def valid_window(self):
        if self.start_sample >= self.stop_sample_exclusive or self.stop_sample_exclusive > self.membrane.sample_rate*120:
            raise ValueError('Nonempty window and at most 120 seconds of causal history required')
        if self.trajectory is not None:
            frames = (self.stop_sample_exclusive-self.start_sample-1)//self.trajectory.hop_samples+1
            if frames*self.grid_x*self.grid_y > 1_000_000 or self.trajectory.window_samples*self.membrane.modes_x*self.membrane.modes_y > 8_000_000:
                raise ValueError('Trajectory exceeds bounded grid/history budget')
        return self


def project(folder, request):
    request = Request.model_validate(request)
    folder = Path(folder)
    parent = folder
    pair_manifest = None
    pair_hash = None
    if request.arm != 'single':
        pair_manifest = verify_pair(parent)
        pair_hash = sha256_file(parent/'manifest.json')
        folder = parent/request.arm
    manifest = verify(folder)
    manifest_hash = sha256_file(folder/'manifest.json')
    sr = manifest['pcm']['sample_rate']
    start, stop = request.start_sample, request.stop_sample_exclusive
    if request.membrane.sample_rate != sr:
        raise ValueError('Membrane and verified PCM sample rates must agree; no implicit resampling')
    if not start < stop <= manifest['levels']['frames'] or stop > sr*120:
        raise ValueError('Nonempty in-range window with at most 120 seconds of causal history required')
    model = Membrane(request.membrane)
    window = FieldWindow(model, start)
    x, y = np.meshgrid(np.linspace(0, 1, request.grid_x), np.linspace(0, 1, request.grid_y))
    rolling = RollingFieldWindow(model, request.trajectory.window_samples) if request.trajectory else None
    frames = []
    next_frame = min(start+request.trajectory.hop_samples, stop) if request.trajectory else stop
    # Always replay from zero: a window changes observation support, not the
    # excitation history. No future samples influence its response.
    with sf.SoundFile(folder/'sum.wav') as audio:
        cursor = 0
        while cursor < stop:
            pcm = audio.read(min(request.block_size, next_frame-cursor, stop-cursor), dtype='float64')
            if not len(pcm):
                raise ValueError('Verified PCM truncated during read')
            q = model.render(pcm)['modal_displacement']
            if rolling is not None: rolling.append(q, cursor)
            first = max(start-cursor, 0)
            if first < len(q):
                window.append(q[first:], cursor+first)
            cursor += len(q)
            if rolling is not None and cursor == next_frame:
                frame = rolling.report(x.ravel(), y.ravel())
                frame['rms'] = frame['rms'].reshape(request.grid_y, request.grid_x).tolist()
                frames.append(frame)
                next_frame = min(next_frame+request.trajectory.hop_samples, stop)
    result = window.report(x.ravel(), y.ravel())
    # Full verification binds all source inputs and components, not just sum.
    if verify(folder) != manifest or sha256_file(folder/'manifest.json') != manifest_hash:
        raise ValueError('R05 artifacts changed during membrane projection')
    if pair_manifest is not None and (verify_pair(parent) != pair_manifest or sha256_file(parent/'manifest.json') != pair_hash):
        raise ValueError('R05 comparison changed during membrane projection')
    result['rms'] = result['rms'].reshape(request.grid_y, request.grid_x).tolist()
    report = {'schema_version': 1, 'line': 'R07', 'request': request.model_dump(),
            'window': result, 'source_manifest_sha256': manifest_hash,
            'source_pair_manifest_sha256': pair_hash,
            'source_component_sha256': manifest['output_hashes']['sum.wav'],
            'history_start_sample': 0, 'initial_state': 'zero',
            'limits': ['Sound-only final mix, no pose or gesture labels',
                       'No implicit resampling, spatial normalization or pressure calibration',
                       'Right-edge sample timestamps; history replayed from zero',
                       'Local artifact integrity, not signed custody or physical synchronization']}
    if rolling is not None:
        report['trajectory'] = frames
        report['limits'].append('Trajectory frames contain only past samples; warmup is not zero-padding')
    return report
