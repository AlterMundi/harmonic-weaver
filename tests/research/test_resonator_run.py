import json
import numpy as np
import pytest
import soundfile as sf
from harmonic_weaver.lab.cache import sha256_file
from harmonic_weaver.lab.research.resonator_render import Render
from harmonic_weaver.lab.research.resonator_run import run


def document():
    return {'request': dict(evaluation_id='a'*32, run_index=0, signal_id='speed',
        start_s=0, end_s=.3, high=1, low=.2), 'unit': 'T/s',
        'rows': [{'time_s': t, 'value': v, 'valid': True} for t,v in [(0,0),(.03,2),(.06,2)]],
        'provenance': {'fixture': 'synthetic'}}


def test_float_pcm_roundtrip_repeat_and_partition_invariance(tmp_path):
    doc = document(); hashes = []
    for index, block in enumerate((256,256,317)):
        request = {'resonators': {'sample_rate': 8000}, 'render': {'block_size': block, 'tail_s': .1}}
        folder = tmp_path / str(index)
        manifest = run(doc, request, folder)
        assert manifest['status'] == 'complete'
        assert json.loads((folder/'manifest.json').read_text()) == manifest
        assert manifest['levels']['frames'] == 3200
        for name,digest in manifest['output_hashes'].items():
            assert sha256_file(folder/name) == digest
        samples,sr = sf.read(folder/'sum.wav', dtype='float64')
        voices,_ = sf.read(folder/'voices.wav', dtype='float64', always_2d=True)
        expected = np.concatenate([b['sum'] for b in Render(doc, request['resonators'], {}, request['render']).blocks()])
        np.testing.assert_array_equal(samples, expected)
        np.testing.assert_array_equal(samples, voices.sum(axis=1))
        assert sr == 8000 and voices.shape == (3200,6)
        assert sf.info(folder/'sum.wav').subtype == 'DOUBLE'
        assert manifest['levels']['peak_abs'] == np.abs(samples).max()
        assert manifest['levels']['rms'] == pytest.approx(np.sqrt(np.mean(samples**2)))
        hashes.append(manifest['output_hashes'])
    assert hashes[0] == hashes[1] == hashes[2]
    with pytest.raises(FileExistsError): run(doc, {}, tmp_path/'0')


def test_invalid_request_does_not_create_run(tmp_path):
    folder = tmp_path/'bad'
    with pytest.raises(ValueError): run(document(), {'unknown': 1}, folder)
    assert not folder.exists()
    with pytest.raises(ValueError): run(document(), {'resonators': {'ratios': [1,2]}}, folder)
    assert not folder.exists()


def test_changed_frozen_input_fails_without_complete_outputs(tmp_path, monkeypatch):
    folder = tmp_path/'changed'; original = Render.blocks
    def mutated(self):
        for block in original(self):
            (folder/'input.json').write_text('{}')
            yield block
    monkeypatch.setattr(Render, 'blocks', mutated)
    with pytest.raises(ValueError, match='Frozen input changed'):
        run(document(), {'resonators': {'sample_rate': 8000}}, folder)
    manifest = json.loads((folder/'manifest.json').read_text())
    assert manifest['status'] == 'failed' and 'output_hashes' not in manifest
    assert not (folder/'sum.wav').exists()
