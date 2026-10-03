import pytest
from harmonic_weaver.lab.research.experience_transport_service import TransportService
from harmonic_weaver.lab.research.experience_service import ExperienceService
from harmonic_weaver.lab.cache import sha256_file
from test_experience_transport import trace
from test_experience_protocol import data


def test_transport_retry_restart_exports_and_protocol_independent_read(tmp_path):
    protocols=ExperienceService(tmp_path);protocol=protocols.start({'protocol':data()})
    body=trace();body.update(protocol_id=protocol['id'],duration_s=60,
        protocol_manifest_sha256=sha256_file(protocols.artifact(protocol['id'],'manifest.json')))
    service=TransportService(tmp_path);saved=service.start(protocols,body)
    assert saved['read_verification']=='summary_recomputed'
    reopened=TransportService(tmp_path)
    assert reopened.start(protocols,body)['id']==saved['id']
    assert len(reopened.list())==1
    for name in ('trace.json','binding.json','manifest.json'):
        assert reopened.artifact(saved['id'],name).is_file()
    protocols.artifact(protocol['id'],'result.json').unlink()
    assert reopened.read(saved['id'])['id']==saved['id']
    assert reopened.start(protocols,body)['id']==saved['id']
    changed={**body,'events':body['events']+[dict(sequence=2,monotonic_s=2,
        elapsed_s=2,epoch=0,kind='closed')]}
    with pytest.raises(ValueError):reopened.start(protocols,changed)
    assert len(reopened.list())==1
    reopened.artifact(saved['id'],'binding.json').write_text('{}')
    with pytest.raises(ValueError):reopened.read(saved['id'])
    assert reopened.list()==[]
    with pytest.raises(ValueError):reopened.artifact('../secret','trace.json')
