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
        path=source.cache_manifest
        manifest=json.loads(open(path).read());manifest['generation']='changed'
        atomic_json(path,manifest)
        with pytest.raises(ValueError,match='changed'):endpoint_snapshot(evaluation,selection)
    finally:evaluation.close();store.close()
