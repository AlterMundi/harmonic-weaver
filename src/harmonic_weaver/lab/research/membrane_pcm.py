"""R07 causal membrane RMS window from a verified single R05 PCM run."""
from pathlib import Path
from pydantic import Field
import numpy as np
import soundfile as sf
from ..contracts import Contract
from ..cache import sha256_file
from .membrane import Settings, Membrane, FieldWindow
from .resonator_artifacts import verify


class Request(Contract):
    membrane: Settings = Field(default_factory=Settings)
    start_sample: int = Field(default=0, ge=0)
    stop_sample_exclusive: int = Field(gt=0)
    grid_x: int = Field(default=33, ge=2, le=129)
    grid_y: int = Field(default=33, ge=2, le=129)
    block_size: int = Field(default=1024, ge=16, le=8192)


def project(folder, request):
    request = Request.model_validate(request)
    folder = Path(folder)
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
    # Always replay from zero: a window changes observation support, not the
    # excitation history. No future samples influence its response.
    with sf.SoundFile(folder/'sum.wav') as audio:
        cursor = 0
        while cursor < stop:
            pcm = audio.read(min(request.block_size, stop-cursor), dtype='float64')
            if not len(pcm):
                raise ValueError('Verified PCM truncated during read')
            q = model.render(pcm)['modal_displacement']
            first = max(start-cursor, 0)
            if first < len(q):
                window.append(q[first:], cursor+first)
            cursor += len(q)
    x, y = np.meshgrid(np.linspace(0, 1, request.grid_x), np.linspace(0, 1, request.grid_y))
    result = window.report(x.ravel(), y.ravel())
    # Full verification binds all source inputs and components, not just sum.
    if verify(folder) != manifest or sha256_file(folder/'manifest.json') != manifest_hash:
        raise ValueError('R05 artifacts changed during membrane projection')
    result['rms'] = result['rms'].reshape(request.grid_y, request.grid_x).tolist()
    return {'schema_version': 1, 'line': 'R07', 'request': request.model_dump(),
            'window': result, 'source_manifest_sha256': manifest_hash,
            'source_component_sha256': manifest['output_hashes']['sum.wav'],
            'history_start_sample': 0, 'initial_state': 'zero',
            'limits': ['Sound-only final mix, no pose or gesture labels',
                       'No implicit resampling, spatial normalization or pressure calibration',
                       'Right-edge sample timestamps; history replayed from zero',
                       'Local artifact integrity, not signed custody or physical synchronization']}
