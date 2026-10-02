import json
import subprocess
import time
import pytest
from harmonic_weaver.lab.research.rope_reader import RopeReader
from harmonic_weaver.lab.research.rope_service import RopeService
from harmonic_weaver.lab.research.rope_flow_service import RopeFlowService
from harmonic_weaver.lab.research.rope_flow_benchmark_service import RopeFlowBenchmarkService
from harmonic_weaver.lab.cache import sha256_file, atomic_json


def test_real_inputs_provenance_restart_and_changed_publication(tmp_path, monkeypatch):
    video=tmp_path/'source.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=10:duration=0.5','-c:v','libx264',str(video)],check=True)
    reader=RopeReader();media=reader.probe(video)
    refs=RopeService(tmp_path);flows=RopeFlowService(tmp_path,reader)
    try:
        ref=refs.save({'media_sha256':media['media_sha256'],'width_px':160,'height_px':120,
            'frames':[{'frame_index':i,'time_s':media['frame_times_s'][i],'state':'observed',
              'visible_segments':[[{'x':.2,'y':.2},{'x':.5,'y':.5}]],'endpoints':{'a':{'x':.5,'y':.5}}} for i in range(3)]},video)
        job=flows.start(video,{'media_sha256':media['media_sha256'],'width_px':160,'height_px':120,
            'start_frame_index':0,'frame_times_s':media['frame_times_s'][:3],'seeds':[{'x':.5,'y':.5}]})
        deadline=time.monotonic()+10
        while flows.report(job['id'])['status']=='running' and time.monotonic()<deadline:time.sleep(.01)
        assert flows.report(job['id'])['status']=='complete'
        selection={'reference_id':ref['id'],'flow_id':job['id'],'endpoint_seeds':{'a':0}}
        original={str(p):sha256_file(p) for root in (refs.root/ref['id'],flows.root/job['id']) for p in root.iterdir()}
        service=RopeFlowBenchmarkService(tmp_path,refs,flows);saved=service.start(selection)
        result=json.loads(service.artifact(saved['id'],'result.json').read_text())
        assert result['coverage']['seed_input_endpoints']==1 and result['coverage']['eligible_endpoints']==2
        request=json.loads(service.artifact(saved['id'],'request.json').read_text())
        assert request['flow_run']['manifest_sha256']==sha256_file(flows.root/job['id']/'manifest.json')
        assert original=={p:sha256_file(p) for p in original}
        assert RopeFlowBenchmarkService(tmp_path,refs,flows).list()[0]['read_verification']=='recomputed'
        with pytest.raises(ValueError):service.start({**selection,'endpoint_seeds':{'a':2}})
        assert len(service.list())==1
        import harmonic_weaver.lab.research.rope_flow_benchmark_service as module
        real=module.run
        def changed(request,folder):
            manifest=real(request,folder)
            path=refs.root/ref['id']/'manifest.json';data=json.loads(path.read_text());data['limits'].append('changed')
            atomic_json(path,data)
            return manifest
        monkeypatch.setattr(module,'run',changed)
        with pytest.raises(ValueError,match='changed'):service.start(selection)
        assert len(service.list())==1
    finally:flows.close()
