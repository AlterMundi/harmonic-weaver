import json

import pytest

from harmonic_weaver.lab.research.neuro_csv import convert
from harmonic_weaver.lab.research.neuro_csv_archive import CSVService, verify
from research.test_neuro_csv import request


def test_original_bom_crlf_map_and_conversion_survive_restart(tmp_path):
    body = request()
    body['csv_text'] = '\ufeff' + body['csv_text']
    service = CSVService(tmp_path)
    saved = service.start(body)
    ident = saved['id']
    folder = service.folder(ident)
    before = {p.name: p.read_bytes() for p in folder.iterdir()}
    assert before['source.csv'] == body['csv_text'].encode('utf-8')
    assert json.loads(before['result.json']) == convert(body)
    assert service.start(body)['id'] == ident
    reopened = CSVService(tmp_path)
    assert len(reopened.list()) == 1
    assert reopened.read(ident, recompute=True)['read_verification'] == 'recomputed'
    assert {p.name: p.read_bytes() for p in folder.iterdir()} == before
    edited = {**body, 'csv_text': body['csv_text'].replace('\r\n', '\n')}
    assert reopened.start(edited)['id'] != ident


def test_historical_integrity_is_independent_of_current_code(tmp_path, monkeypatch):
    import harmonic_weaver.lab.research.neuro_csv_archive as archive
    service = CSVService(tmp_path)
    ident = service.start(request())['id']
    monkeypatch.setattr(archive, 'code_hashes', lambda: {'different': '0'*64})
    assert service.read(ident)['current_code_matches'] is False
    assert service.read(ident, recompute=True)['read_verification'] == 'recomputed'


@pytest.mark.parametrize('name', ['source.csv', 'request.json', 'result.json'])
def test_corrupted_artifact_not_listed_or_exported(tmp_path, name):
    service = CSVService(tmp_path)
    ident = service.start(request())['id']
    path = service.folder(ident) / name
    path.write_bytes(path.read_bytes() + b' ')
    assert service.list() == []
    with pytest.raises(ValueError, match='hash mismatch'):
        service.artifact(ident, name)


def test_partial_publication_retry_does_not_discard_valid_generation(tmp_path, monkeypatch):
    import harmonic_weaver.lab.research.neuro_csv_archive as archive
    original = archive.atomic_json
    def fail_manifest(path, value):
        if path.name == 'manifest.json':
            raise OSError('simulated interrupted publication')
        return original(path, value)
    service = CSVService(tmp_path)
    monkeypatch.setattr(archive, 'atomic_json', fail_manifest)
    with pytest.raises(OSError):
        service.start(request())
    assert service.list() == []
    monkeypatch.setattr(archive, 'atomic_json', original)
    ident = service.start(request())['id']
    assert len(service.list()) == 1
    assert verify(service.folder(ident), recompute=True)


def test_rehashed_source_still_requires_exact_frozen_bytes(tmp_path):
    from harmonic_weaver.lab.cache import sha256_file
    service = CSVService(tmp_path)
    ident = service.start(request())['id']
    folder = service.folder(ident)
    (folder / 'source.csv').write_bytes(b'other bytes')
    manifest = json.loads((folder / 'manifest.json').read_text())
    manifest['hashes']['source.csv'] = sha256_file(folder / 'source.csv')
    (folder / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='original bytes'):
        service.read(ident)
