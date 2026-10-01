"""Persist experimental R05 PCM without opening an audio device."""
import argparse
import json
import os
import platform
from pathlib import Path
import numpy as np
import scipy
import soundfile as sf
from ..cache import atomic_json, sha256_file
from .resonator_render import Render


def run(document, request, folder):
    if set(request) - {'resonators', 'excitation', 'render'}:
        raise ValueError('Unknown R05 request field')
    render = Render(document, request.get('resonators', {}),
                    request.get('excitation', {}), request.get('render', {}))
    folder = Path(folder)
    folder.mkdir(mode=0o700, parents=True, exist_ok=False)
    atomic_json(folder / 'input.json', document)
    atomic_json(folder / 'request.json', request)
    modules = ['resonator_run.py', 'resonator_render.py', 'resonators.py',
               'excitation.py', 'event_candidates.py', 'candidate_input.py', 'coincidence.py']
    manifest = {'schema_version': 1, 'line': 'R05', 'status': 'running',
        'input_hashes': {name: sha256_file(folder / name) for name in ('input.json', 'request.json')},
        'code_hashes': {name: sha256_file(Path(__file__).with_name(name)) for name in modules},
        'environment': {'python': platform.python_version(), 'numpy': np.__version__,
            'scipy': scipy.__version__, 'soundfile': sf.__version__,
            'libsndfile': sf.__libsndfile_version__, 'platform': platform.platform()},
        'preparation': render.manifest,
        'pcm': {'format': 'WAV', 'subtype': 'DOUBLE', 'sample_rate': render.resonators.sample_rate,
            'sum_channels': 1, 'voice_channels': len(render.resonators.ratios)},
        'limits': render.manifest['limits'] + [
            'Raw float64 PCM may exceed full scale; check levels before playback',
            'Per-voice file contains model outputs, not body features',
            'Software artifact integrity is not scientific validation or human acceptance']}
    manifest['code_hashes']['contracts.py'] = sha256_file(Path(__file__).parent.parent / 'contracts.py')
    manifest['code_hashes']['cache.py'] = sha256_file(Path(__file__).parent.parent / 'cache.py')
    atomic_json(folder / 'manifest.json', manifest)
    peak = 0.; squares = 0.; frames = 0; over = 0
    try:
        with sf.SoundFile(folder / 'sum.partial.wav', 'w', samplerate=render.resonators.sample_rate,
                          channels=1, format='WAV', subtype='DOUBLE') as summed, \
             sf.SoundFile(folder / 'voices.partial.wav', 'w', samplerate=render.resonators.sample_rate,
                          channels=len(render.resonators.ratios), format='WAV', subtype='DOUBLE') as voices:
            for block in render.blocks():
                values = block['sum']
                if not np.isfinite(values).all() or not np.isfinite(block['voices']).all():
                    raise ValueError('Nonfinite model PCM')
                summed.write(values); voices.write(block['voices'])
                frames += len(values)
                peak = max(peak, float(np.max(np.abs(values))))
                squares += float(np.dot(values, values))
                over += int(np.count_nonzero(np.abs(values) > 1))
        if frames != render.total_frames:
            raise ValueError('Incomplete R05 sample clock')
        for name, digest in manifest['input_hashes'].items():
            if (folder / name).is_symlink() or sha256_file(folder / name) != digest:
                raise ValueError('Frozen input changed during render')
        for name in ('sum', 'voices'):
            os.replace(folder / f'{name}.partial.wav', folder / f'{name}.wav')
        manifest.update(status='complete', output_hashes={
            f'{name}.wav': sha256_file(folder / f'{name}.wav') for name in ('sum', 'voices')},
            levels={'frames': frames, 'peak_abs': peak, 'rms': (squares / frames) ** .5,
                    'samples_over_full_scale': over})
        atomic_json(folder / 'manifest.json', manifest)
    except Exception as exc:
        manifest.update(status='failed', error_type=type(exc).__name__)
        manifest.pop('output_hashes', None)
        atomic_json(folder / 'manifest.json', manifest)
        raise
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--request', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    run(json.loads(args.input.read_text()), json.loads(args.request.read_text()), args.output)


if __name__ == '__main__':
    main()
