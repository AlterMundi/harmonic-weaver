import json
from uuid import uuid4
import pytest
from harmonic_weaver.lab.cache import atomic_json
from harmonic_weaver.lab.evaluation.runner import Request,run
from harmonic_weaver.lab.evaluation.service import EvaluationService
from harmonic_weaver.lab.presets import initial_presets
from harmonic_weaver.lab.store import SessionStore
from harmonic_weaver.lab.research.relational_input import endpoint_snapshot
from test_lab_evaluation import source_fixture


def test_real_frozen_pose_endpoints_repeat_gaps_and_changed_generation_rejected(tmp_path):
    source,_,_=source_fixture(tmp_path)
    root=tmp_path/'session';ident=uuid4().hex;folder=root/'evaluations'/ident;folder.mkdir(parents=True)
    request=Request(presets=[next(p for p in initial_presets() if p.algorithm.id=='local')],sources=[source])
    atomic_json(folder/'request.json',request.model_dump());run(request,folder/'result')
    store=SessionStore(root);evaluation=EvaluationService(root,store,None)
    selection=dict(evaluation_id=ident,run_index=0,parent_joint=7,child_joint=9,start_s=.2,end_s=2)
    try:
        snapshot=endpoint_snapshot(evaluation,selection)
        assert snapshot==endpoint_snapshot(evaluation,selection)
        assert snapshot['unit']=='T/s' and snapshot['scale']==.2
        assert snapshot['rows'][0]['valid'] is False
        assert any(r['valid'] for r in snapshot['rows'])
        assert all(not r['valid'] for r in snapshot['rows'] if 1<=r['time_s']<1.1)
        assert snapshot['provenance']['source']['person_id']=='one'
        with pytest.raises(ValueError,match='distinct'):endpoint_snapshot(evaluation,{**selection,'parent_joint':9})
        with pytest.raises(ValueError,match='outside'):endpoint_snapshot(evaluation,{**selection,'start_s':0})
        from harmonic_weaver.lab.research.relational_body import probe_endpoints
        from harmonic_weaver.lab.research.relational_service import RelationalService
        from harmonic_weaver.lab.cache import sha256_file
        import numpy as np
        expected=probe_endpoints({},snapshot)
        assert expected['unused_synthetic_settings']==['samples','hz']
        original=expected['traces']['original']
        for control,rows in expected['traces'].items():
            for a,b in zip(rows,original):
                assert a['relative']['state']==b['relative']['state']
                if a['relative']['state']=='observed':
                    np.testing.assert_allclose([a['relative'][k] for k in ('I','R','A')],
                                              [b['relative'][k] for k in ('I','R','A')],atol=1e-12)
        service=RelationalService(root)
        try:
            hashes=[]
            for _ in range(2):
                job=service.start_body({},selection,evaluation)
                assert service.processes[job['id']].wait(timeout=10)==0
                result=service.artifact(job['id'],'result.json')
                assert json.loads(result.read_text())==expected
                hashes.append(sha256_file(result))
                assert json.loads(service.artifact(job['id'],'input.json').read_text())==snapshot
            assert hashes[0]==hashes[1]
        finally:service.close()
        from fastapi.testclient import TestClient
        from harmonic_weaver.lab.app import create_app
        import time
        class Runtime:
            library=None
            def start(self):pass
            def close(self):pass
        with TestClient(create_app(root,store=store,runtime=Runtime()),base_url='http://127.0.0.1') as client:
            response=client.post('/api/research/r04/trace',json={'selection':selection})
            assert response.status_code==200,response.text
            job=response.json()['id'];deadline=time.monotonic()+10
            while True:
                report=next(j for j in client.get('/api/research/r04').json() if j['id']==job)
                if report['status'] not in ('queued','running'):break
                assert time.monotonic()<deadline
                time.sleep(.02)
            assert report['status']=='complete'
            assert client.get(f'/api/research/r04/{job}/artifacts/result.json').json()==expected
        path=source.cache_manifest
        manifest=json.loads(open(path).read());manifest['generation']='changed'
        atomic_json(path,manifest)
        with pytest.raises(ValueError,match='changed'):endpoint_snapshot(evaluation,selection)
    finally:evaluation.close();store.close()
