import pytest
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
