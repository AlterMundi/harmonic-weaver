import pytest
import json
from harmonic_weaver.lab.cache import atomic_json, sha256_file
from harmonic_weaver.lab.research.membrane_run import run, verify
from test_resonator_artifacts import fixture


def test_persisted_repeat_inventory_and_tamper(tmp_path):
    source = tmp_path/'source'
    fixture(source)
    request = {'membrane': {'sample_rate': 8000}, 'stop_sample_exclusive': 800}
    reports = []
    for i in range(2):
        destination = tmp_path/str(i)
        manifest = run(source, request, destination)
        assert verify(destination) == manifest
        assert {p.name for p in destination.iterdir()} == {'manifest.json', 'request.json', 'result.json'}
        reports.append((destination/'result.json').read_bytes())
    assert reports[0] == reports[1]
    with pytest.raises(FileExistsError): run(source, request, tmp_path/'0')
    with (tmp_path/'0/result.json').open('ab') as handle: handle.write(b'changed')
    with pytest.raises(ValueError): verify(tmp_path/'0')


@pytest.mark.parametrize('mutation', ['clock','boundary','negative','nonfinite','history','source','pair','settings'])
def test_semantic_mutations_rejected_even_with_rewritten_hash(tmp_path, mutation):
    source = tmp_path/'source'
    fixture(source)
    folder = tmp_path/'result'
    manifest = run(source, {'membrane': {'sample_rate': 8000}, 'stop_sample_exclusive': 800}, folder)
    result = json.loads((folder/'result.json').read_text())
    if mutation == 'clock': result['window']['sample_rate'] = 9000
    elif mutation == 'boundary': result['window']['rms'][0][1] = .1
    elif mutation == 'negative': result['window']['rms'][1][1] = -.1
    elif mutation == 'nonfinite': result['window']['rms'][1][1] = 'NaN'
    elif mutation == 'history': result['history_start_sample'] = 1
    elif mutation == 'source':
        result['source_component_sha256'] = 'bad'
        manifest['source']['source_component_sha256'] = 'bad'
    elif mutation == 'pair':
        result['source_pair_manifest_sha256'] = 'a'*64
        manifest['source']['source_pair_manifest_sha256'] = 'a'*64
    else: result['request']['grid_x'] = 7
    atomic_json(folder/'result.json', result)
    manifest['output']['sha256'] = sha256_file(folder/'result.json')
    atomic_json(folder/'manifest.json', manifest)
    with pytest.raises(ValueError): verify(folder)
