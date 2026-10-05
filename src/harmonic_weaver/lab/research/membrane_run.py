"""Persisted R07 projection with frozen request and local integrity checks."""
import argparse
import json
import platform
import re
from pathlib import Path
import numpy as np
import scipy
from ..cache import atomic_json, sha256_file
from .membrane_pcm import Request, project


def run(source, request, folder):
    request = Request.model_validate(request)
    # Validate and compute before creating a destination. Source remains in
    # place; no body media, tracking or PCM is copied into the result folder.
    result = project(source, request)
    folder = Path(folder)
    folder.mkdir(mode=0o700, parents=True, exist_ok=False)
    atomic_json(folder/'request.json', request.model_dump())
    atomic_json(folder/'result.json', result)
    manifest = {'schema_version': 1, 'line': 'R07', 'status': 'complete',
                'input_hashes': {'request.json': sha256_file(folder/'request.json')},
                'output': {'file': 'result.json', 'sha256': sha256_file(folder/'result.json')},
                'source': {key: result[key] for key in ('source_manifest_sha256',
                           'source_component_sha256', 'source_pair_manifest_sha256')},
                'code_hashes': {name: sha256_file(Path(__file__).with_name(name))
                               for name in ('membrane.py', 'membrane_pcm.py', 'membrane_run.py')},
                'environment': {'python': platform.python_version(), 'numpy': np.__version__,
                                'scipy': scipy.__version__}, 'limits': result['limits']}
    if isinstance(source, dict):
        manifest['code_hashes']['membrane_eval_source.py'] = sha256_file(Path(__file__).with_name('membrane_eval_source.py'))
    atomic_json(folder/'manifest.json', manifest)
    return manifest


def verify(folder):
    folder = Path(folder)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError('Regular R07 directory required')
    names = ('request.json', 'result.json', 'manifest.json')
    if (folder/'source.json').exists() or (folder/'source.json').is_symlink():
        names += ('source.json',)
    for name in names:
        if (folder/name).is_symlink() or not (folder/name).is_file():
            raise ValueError('Regular R07 artifacts required')
    snapshot = {name: sha256_file(folder/name) for name in names}
    manifest = json.loads((folder/'manifest.json').read_text())
    if (manifest.get('schema_version'), manifest.get('line'), manifest.get('status')) != (1, 'R07', 'complete'):
        raise ValueError('Complete R07 manifest required')
    expected_inputs = {name: snapshot[name] for name in names if name in ('request.json', 'source.json')}
    if manifest.get('input_hashes') != expected_inputs or manifest.get('output') != {'file': 'result.json', 'sha256': snapshot['result.json']}:
        raise ValueError('R07 artifact inventory/hash mismatch')
    request = Request.model_validate_json((folder/'request.json').read_text())
    result = json.loads((folder/'result.json').read_text())
    if result.get('request') != request.model_dump() or result.get('line') != 'R07' or result.get('schema_version') != 1:
        raise ValueError('R07 frozen request mismatch')
    if result.get('history_start_sample') != 0 or type(result.get('history_start_sample')) is not int or result.get('initial_state') != 'zero':
        raise ValueError('R07 zero-state causal history required')
    window = result['window']
    sr = request.membrane.sample_rate
    expected = {'start_sample': request.start_sample, 'stop_sample_exclusive': request.stop_sample_exclusive,
                'sample_count': request.stop_sample_exclusive-request.start_sample,
                'sample_rate': sr, 'first_output_time_s': (request.start_sample+1)/sr,
                'last_output_time_s': request.stop_sample_exclusive/sr}
    if set(window) != set(expected)|{'rms'} or expected['sample_count'] <= 0 or any(window.get(k) != v for k, v in expected.items()):
        raise ValueError('R07 window clock mismatch')
    if any(type(window[k]) is not int for k in ('start_sample','stop_sample_exclusive','sample_count','sample_rate')):
        raise ValueError('Integer R07 sample clock required')
    rms = np.asarray(window['rms'], dtype=float)
    if rms.shape != (request.grid_y, request.grid_x) or not np.isfinite(rms).all() or (rms < 0).any() or np.any(rms[[0, -1], :]) or np.any(rms[:, [0, -1]]):
        raise ValueError('R07 finite nonnegative fixed-boundary field required')
    if request.trajectory is None:
        if 'trajectory' in result: raise ValueError('Unexpected R07 trajectory')
    else:
        ends = list(range(request.start_sample+request.trajectory.hop_samples,
                          request.stop_sample_exclusive, request.trajectory.hop_samples)) + [request.stop_sample_exclusive]
        frames = result.get('trajectory')
        if not isinstance(frames, list) or len(frames) != len(ends):
            raise ValueError('Exact R07 trajectory frame inventory required')
        for frame, stop in zip(frames, ends):
            start = max(0, stop-request.trajectory.window_samples)
            expected_frame = {'start_sample': start, 'stop_sample_exclusive': stop,
                'sample_count': stop-start, 'sample_rate': sr,
                'first_output_time_s': (start+1)/sr, 'last_output_time_s': stop/sr,
                'requested_window_samples': request.trajectory.window_samples,
                'warmup': stop < request.trajectory.window_samples}
            if set(frame) != set(expected_frame)|{'rms'} or any(frame.get(k) != v for k,v in expected_frame.items()):
                raise ValueError('R07 trajectory causal clock mismatch')
            values = np.asarray(frame['rms'], dtype=float)
            if values.shape != rms.shape or not np.isfinite(values).all() or (values < 0).any() or np.any(values[[0,-1],:]) or np.any(values[:,[0,-1]]):
                raise ValueError('Invalid R07 trajectory field')
    if manifest['source'] != {k: result[k] for k in manifest['source']} or set(manifest['source']) != {'source_manifest_sha256', 'source_component_sha256', 'source_pair_manifest_sha256'}:
        raise ValueError('R07 source binding mismatch')
    for key, digest in manifest['source'].items():
        if key == 'source_pair_manifest_sha256' and request.arm == 'single':
            if digest is not None: raise ValueError('Single run must not declare a pair')
        elif not isinstance(digest, str) or not re.fullmatch('[a-f0-9]{64}', digest):
            raise ValueError('Valid R07 source SHA256 required')
    if any((folder/name).is_symlink() or sha256_file(folder/name) != digest for name, digest in snapshot.items()):
        raise ValueError('R07 artifacts changed during verification')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.source, json.loads(args.request.read_text()), args.output)
