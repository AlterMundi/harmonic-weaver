import json
import pytest
from harmonic_weaver.lab.research.rope_flow_benchmark_run import run as benchmark_run
from harmonic_weaver.lab.research.rope_flow_benchmark_service import RopeFlowBenchmarkService
from harmonic_weaver.lab.research.rope_flow_paired_service import RopeFlowPairedService
from harmonic_weaver.lab.cache import sha256_file,atomic_json
from test_rope_flow_benchmark_run import inputs


def test_resolve_real_artifacts_preserve_sources_and_restart(tmp_path,monkeypatch):
    benchmarks=RopeFlowBenchmarkService(tmp_path,None,None)
    ids=['a'*32,'b'*32]
    for ident in ids:benchmark_run(inputs(),benchmarks.root/ident)
    before={str(p):sha256_file(p) for ident in ids for p in (benchmarks.root/ident).iterdir()}
    service=RopeFlowPairedService(tmp_path,benchmarks);selection={'conditions':{'one':ids[0],'two':ids[1]}}
    saved=service.start(selection)
    result=json.loads(service.artifact(saved['id'],'result.json').read_text())
    assert result['common_supported_endpoints']==4
    assert result['paired_differences'][0]['mean_right_minus_left_error_px']==0
    assert before=={p:sha256_file(p) for p in before}
    assert RopeFlowPairedService(tmp_path,benchmarks).list()[0]['read_verification']=='recomputed'
    with pytest.raises(ValueError,match='distinct'):service.start({'conditions':{'one':ids[0],'two':ids[0]}})
    import harmonic_weaver.lab.research.rope_flow_paired_service as module
    real=module.run
    def changed(request,folder):
        result=real(request,folder);path=benchmarks.root/ids[0]/'manifest.json'
        manifest=json.loads(path.read_text());manifest['limits'].append('changed');atomic_json(path,manifest)
        return result
    monkeypatch.setattr(module,'run',changed)
    with pytest.raises(ValueError,match='changed'):service.start(selection)
    assert len(service.list())==1
