"""Read-only verification of completed R05 float PCM artifacts."""
import argparse
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from ..cache import sha256_file
from .resonator_render import Render


def verify(folder):
    folder = Path(folder)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError('Regular R05 run directory required')
    names = ('manifest.json', 'input.json', 'request.json', 'sum.wav', 'voices.wav')
    for name in names:
        path = folder / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Missing or nonregular R05 artifact')
    manifest_hash = sha256_file(folder / 'manifest.json')
    manifest = json.loads((folder / 'manifest.json').read_text())
    if manifest.get('schema_version') != 1 or manifest.get('line') != 'R05' or manifest.get('status') != 'complete':
        raise ValueError('Completed R05 manifest required')
    if set(manifest.get('input_hashes', {})) != {'input.json', 'request.json'} or \
       set(manifest.get('output_hashes', {})) != {'sum.wav', 'voices.wav'}:
        raise ValueError('Exact R05 artifact inventory required')
    hashes = {**manifest['input_hashes'], **manifest['output_hashes']}
    for name, digest in hashes.items():
        if sha256_file(folder / name) != digest:
            raise ValueError('R05 artifact hash mismatch')
    document = json.loads((folder / 'input.json').read_text())
    request = json.loads((folder / 'request.json').read_text())
    if manifest['preparation'].get('mechanism')=='positive_amplitude_mapping':
        from .parameter_render import Render as ParameterRender
        if set(request)-{'carriers','mapping','render'}:raise ValueError('Unknown mapping request field')
        prepared=ParameterRender(document,request.get('carriers',{}),request.get('mapping',{}),request.get('render',{}))
        carriers=prepared.carriers
    else:
        if set(request) - {'resonators', 'excitation', 'render'}:
            raise ValueError('Unknown R05 request field')
        prepared = Render(document, request.get('resonators', {}), request.get('excitation', {}), request.get('render', {}))
        carriers=prepared.resonators
    if manifest['preparation'] != prepared.manifest:
        raise ValueError('R05 preparation differs from frozen inputs')
    sr = carriers.sample_rate; n = len(carriers.ratios)
    expected = {'format': 'WAV', 'subtype': 'DOUBLE', 'sample_rate': sr,
                'sum_channels': 1, 'voice_channels': n}
    if manifest['pcm'] != expected:
        raise ValueError('R05 PCM contract mismatch')
    for name, channels in (('sum.wav', 1), ('voices.wav', n)):
        info = sf.info(folder / name)
        if (info.format, info.subtype, info.samplerate, info.channels, info.frames) != \
           ('WAV', 'DOUBLE', sr, channels, prepared.total_frames):
            raise ValueError('R05 PCM header or clock mismatch')
    peak = 0.; squares = 0.; frames = 0; over = 0
    with sf.SoundFile(folder / 'sum.wav') as summed, sf.SoundFile(folder / 'voices.wav') as voices:
        while True:
            values = summed.read(4096, dtype='float64')
            if not len(values): break
            components = voices.read(len(values), dtype='float64', always_2d=True)
            if not np.isfinite(values).all() or not np.isfinite(components).all() or \
               not np.array_equal(values, components.sum(axis=1)):
                raise ValueError('R05 PCM must be finite and equal the sum of all voices')
            frames += len(values); peak = max(peak, float(np.abs(values).max()))
            squares += float(np.dot(values, values)); over += int(np.count_nonzero(np.abs(values) > 1))
    levels = manifest['levels']
    if levels['frames'] != frames or levels['peak_abs'] != peak or levels['samples_over_full_scale'] != over or \
       not np.isclose(levels['rms'], (squares / frames)**.5, rtol=1e-12, atol=1e-15):
        raise ValueError('R05 level report mismatch')
    # Verify again after reading PCM; this is local integrity, not signed custody.
    for name, digest in {**hashes, 'manifest.json': manifest_hash}.items():
        if (folder / name).is_symlink() or sha256_file(folder / name) != digest:
            raise ValueError('R05 artifact changed during verification')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    report = verify(args.folder)
    print(json.dumps({'status': 'verified', 'frames': report['levels']['frames'],
                      'levels': report['levels'], 'output_hashes': report['output_hashes']}))


if __name__ == '__main__':
    main()
