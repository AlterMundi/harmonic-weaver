import json
import numpy as np
import pytest
import soundfile as sf
from harmonic_weaver.lab.cache import atomic_json, sha256_file
from harmonic_weaver.lab.research.resonator_run import run
from harmonic_weaver.lab.research.resonator_artifacts import verify


def fixture(folder):
    document = {'request': dict(evaluation_id='a'*32, run_index=0, signal_id='speed',
        start_s=0, end_s=.3, high=1, low=.2), 'unit': 'T/s',
        'rows': [{'time_s': t, 'value': v, 'valid': True} for t,v in [(0,0),(.03,2)]],
        'provenance': {'fixture': 'synthetic'}}
    return run(document, {'resonators': {'sample_rate': 8000}}, folder)


def test_complete_read_only_verification(tmp_path):
    folder = tmp_path/'run'; manifest = fixture(folder)
    before = {p.name:sha256_file(p) for p in folder.iterdir()}
    assert verify(folder) == manifest
    assert before == {p.name:sha256_file(p) for p in folder.iterdir()}


@pytest.mark.parametrize('change', ['hash', 'symlink', 'incomplete', 'clock', 'sum', 'levels', 'input'])
def test_rejects_modified_or_inconsistent_artifacts(tmp_path, change):
    folder = tmp_path/'run'; manifest = fixture(folder)
    if change == 'hash':
        with (folder/'sum.wav').open('ab') as handle: handle.write(b'changed')
    elif change == 'symlink':
        (folder/'sum.wav').rename(tmp_path/'external.wav')
        (folder/'sum.wav').symlink_to(tmp_path/'external.wav')
    elif change == 'incomplete': manifest['status'] = 'running'
    elif change in ('clock','sum'):
        values,sr = sf.read(folder/'sum.wav')
        if change == 'clock': values = values[:-1]
        else: values[1000] += .1
        sf.write(folder/'sum.wav',values,sr,subtype='DOUBLE')
        manifest['output_hashes']['sum.wav'] = sha256_file(folder/'sum.wav')
    elif change == 'levels': manifest['levels']['rms'] += .1
    elif change == 'input':
        doc = json.loads((folder/'input.json').read_text());doc['rows'][1]['time_s'] = .04
        atomic_json(folder/'input.json',doc)
        manifest['input_hashes']['input.json'] = sha256_file(folder/'input.json')
    atomic_json(folder/'manifest.json',manifest)
    with pytest.raises(ValueError): verify(folder)
