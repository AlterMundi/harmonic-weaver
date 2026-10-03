import json
import zipfile
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from harmonic_weaver.lab.contracts import Preset,Macro,MacroTarget
from harmonic_weaver.lab.evaluation.runner import Request,run
from harmonic_weaver.lab.evaluation.service import EvaluationService
from harmonic_weaver.lab.evaluation.packages import Selection,CreateRequest,plan,preview,PackageService,run_frozen
from test_lab_evaluation import source_fixture


def prepared(tmp_path):
    source,_,_=source_fixture(tmp_path,'sensitive-clip')
    presets=[Preset(id='sensitive-first',name='SENSITIVE NAME'),Preset(id='sensitive-second')]
    presets[0].voices[0].label='SENSITIVE VOICE'
    presets[0].routes[0].id='sensitive-route'
    presets[0].macros=[Macro(id='sensitive-macro',label='SENSITIVE MACRO',targets=[MacroTarget(path='master',minimum=0.,maximum=1.)])]
    root=tmp_path/'session';ident=uuid4().hex;folder=root/'evaluations'/ident;folder.mkdir(parents=True)
    request=Request(presets=presets,sources=[source],preroll_s=.2)
    atomic_json(folder/'request.json',request.model_dump());run(request,folder/'result')
    return root,ident,EvaluationService(root,None,None)


def test_summary_redacts_free_labels_and_paths_and_keeps_full_matrix_support(tmp_path):
    root,ident,evaluation=prepared(tmp_path)
    data=plan(evaluation,ident,Selection(run_indices=[0]))
    text=json.dumps(data['documents'])
    assert 'SENSITIVE' not in text and 'sensitive-' not in text and str(tmp_path) not in text
    assert 'person_id' not in text and 'media_path' not in text and 'calibration_provenance' not in text
    summary=data['documents']['summary.json']
    assert len(summary['runs'])==1 and len(summary['presets'])==1
    preset=Preset.model_validate(summary['presets'][0]);assert len(preset.voices)==6 and preset.macros[0].targets[0].path=='master'
    stats=summary['comparisons'][0]['signals']['zone.1.speed']
    original=evaluation.report(ident)['comparisons'][0]['signals']['zone.1.speed']
    assert stats['support_matrix_preset_count']==2 and stats['selected_preset_indices']==[0]
    assert stats['means_same_support']==original['means_same_support'][:1]
    assert preview(evaluation,ident,Selection(run_indices=[0]))['private_context'] is False
    assert not data['artifacts']
    original_request=Request.model_validate(evaluation.report(ident)['manifest']['request'])
    exported=original_request.model_copy(deep=True);exported.presets=[preset]
    regenerated=run(exported,tmp_path/'redacted-preset')
    original_rows=[json.loads(line) for line in evaluation.artifact(ident,evaluation.report(ident)['manifest']['runs'][0]['file']).read_text().splitlines()]
    exported_rows=[json.loads(line) for line in (tmp_path/'redacted-preset'/regenerated['runs'][0]['file']).read_text().splitlines()]
    assert [r['targets'] for r in exported_rows]==[r['targets'] for r in original_rows]
    assert [(r['features'] or {}).get('signals') for r in exported_rows]==[(r['features'] or {}).get('signals') for r in original_rows]
    evaluation.close()


def test_package_worker_repeat_restore_and_integrity(tmp_path):
    root,ident,evaluation=prepared(tmp_path)
    service=PackageService(root);selection=Selection(run_indices=[0],include_requests=True,include_traces=True)
    pre=preview(evaluation,ident,selection)
    assert pre['private_context'] and any(f['archive_name'].startswith('requests/') for f in pre['files'])
    request=CreateRequest(selection=selection,preview_sha256=pre['preview_sha256'])
    try:
        first=service.start(evaluation,ident,request);assert service.processes[first['id']].wait(timeout=30)==0
        second=service.start(evaluation,ident,request);assert service.processes[second['id']].wait(timeout=30)==0
        a=service.artifact(first['id'],'package.zip');b=service.artifact(second['id'],'package.zip')
        assert a.read_bytes()==b.read_bytes()
        with zipfile.ZipFile(a) as archive:
            assert set(archive.namelist())=={'summary.json','package-manifest.json','requests/run-0000.json','traces/run-0000.jsonl'}
            recipe=json.loads(archive.read('requests/run-0000.json'))
            assert len(recipe['presets'])==len(recipe['sources'])==1
            assert recipe['presets'][0]['id']=='sensitive-first'
            assert recipe['sources'][0]['media_path'].endswith('sensitive-clip.mp4')
            manifest=json.loads(archive.read('package-manifest.json'))
            import hashlib
            for entry in manifest['files']:
                assert hashlib.sha256(archive.read(entry['archive_name'])).hexdigest()==entry['sha256']
        restored=PackageService(root);assert restored.artifact(first['id'],'package.zip')==a
        a.write_bytes(b'changed')
        with pytest.raises(ValueError,match='changed'):restored.artifact(first['id'],'package.zip')
        with pytest.raises(ValueError):restored.artifact(second['id'],'../request.json')
        restored.close()
    finally:service.close();evaluation.close()


def test_stale_preview_and_changed_artifact_do_not_publish(tmp_path):
    root,ident,evaluation=prepared(tmp_path);service=PackageService(root)
    selection=Selection(run_indices=[0],include_traces=True);pre=preview(evaluation,ident,selection)
    with pytest.raises(ValueError,match='preview'):
        service.start(evaluation,ident,CreateRequest(selection=selection.model_copy(update={'include_requests':True}),preview_sha256=pre['preview_sha256']))
    frozen=plan(evaluation,ident,selection)
    folder=tmp_path/'frozen';folder.mkdir()
    atomic_json(folder/'input.json',frozen);atomic_json(folder/'request.json',{'preview_sha256':pre['preview_sha256']})
    atomic_json(folder/'job.json',{'input_hashes':{n:sha256_file(folder/n) for n in ('request.json','input.json')}})
    artifact=evaluation.artifact(ident,evaluation.report(ident)['manifest']['runs'][0]['file']);artifact.write_bytes(b'changed')
    with pytest.raises(ValueError,match='changed during packaging'):run_frozen(folder)
    assert json.loads((folder/'manifest.json').read_text())['status']=='failed'
    assert not (folder/'package.zip').exists()
    with pytest.raises(ValueError):preview(evaluation,ident,selection)
    service.close();evaluation.close()


def test_selection_bounds_budget_and_actual_api_package(tmp_path):
    root,ident,evaluation=prepared(tmp_path)
    with pytest.raises(ValueError):Selection(run_indices=[0,0])
    with pytest.raises(ValueError):plan(evaluation,ident,Selection(run_indices=[9]))
    selection=Selection(run_indices=[1])
    runtime=SimpleNamespace(library=None,start=lambda:None,close=lambda:None,snapshot=lambda:{})
    with TestClient(create_app(root,runtime=runtime),base_url='http://127.0.0.1') as client:
        pre=client.post(f'/api/evaluations/{ident}/package-preview',json=selection.model_dump())
        assert pre.status_code==200 and not pre.json()['private_context']
        job=client.post(f'/api/evaluations/{ident}/packages',json={'selection':selection.model_dump(),'preview_sha256':pre.json()['preview_sha256']}).json()
        import time
        for _ in range(200):
            rows=client.get('/api/evaluation-packages').json();record=next(r for r in rows if r['id']==job['id'])
            if record['status'] not in ('queued','running'):break
            time.sleep(.025)
        assert record['status']=='complete',record
        download=client.get(f"/api/evaluation-packages/{job['id']}/artifacts/package.zip")
        assert download.status_code==200 and download.content[:2]==b'PK'
        late_cancel=client.post(f"/api/evaluation-packages/{job['id']}/cancel",json={})
        assert late_cancel.status_code==200 and late_cancel.json()['status']=='complete'
    evaluation.close()


def test_payload_budget_rejects_large_verified_traces(tmp_path):
    source,_,_=source_fixture(tmp_path)
    root=tmp_path/'session';ident=uuid4().hex;folder=root/'evaluations'/ident;folder.mkdir(parents=True)
    request=Request(presets=[Preset(id=f'p-{i}') for i in range(4)],sources=[source],control_hz=240)
    atomic_json(folder/'request.json',request.model_dump());manifest=run(request,folder/'result')
    assert sum((folder/'result'/r['file']).stat().st_size for r in manifest['runs'])>1024**2
    evaluation=EvaluationService(root,None,None)
    with pytest.raises(ValueError,match='size budget'):
        preview(evaluation,ident,Selection(run_indices=[0,1,2,3],include_traces=True,max_mb=1))
    evaluation.close()
