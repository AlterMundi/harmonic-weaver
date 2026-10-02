import json
import pytest
from harmonic_weaver.lab.research.spatial_service import SpatialService
from harmonic_weaver.lab.research.spatial_clock_service import SpatialClockService
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from test_spatial_external_stream import data as stream_data
from test_spatial_clock_fit import data as fit_data


def test_resolved_clock_conversion_freezes_sources_and_recovers(tmp_path,monkeypatch):
    conversions=SpatialService(tmp_path);clocks=SpatialClockService(tmp_path)
    stream=stream_data();stream['clock']['source_clock']='camera'
    source=conversions.start({'stream':stream});clock=clocks.start({'fit':fit_data()})
    selection={'conversion_id':source['id'],'fit_id':clock['id'],'idempotency_key':'a'*32}
    saved=conversions.from_clock(clocks,selection)
    result=json.loads(conversions.artifact(saved['id'],'result.json').read_text())
    assert result['stream']['clock']['offset_s']==2 and result['stream']['frames']==result['clock_application']['original_stream']['frames']
    assert result['clock_application']['conversion']['manifest_sha256']==sha256_file(conversions.root/source['id']/'manifest.json')
    def unavailable(*args):raise AssertionError('Must recover without fit resolution')
    monkeypatch.setattr(clocks,'artifact',unavailable)
    assert SpatialService(tmp_path).from_clock(clocks,selection)['id']==saved['id']
    assert len(conversions.list())==2


def test_source_change_discards_only_new_clock_conversion(tmp_path,monkeypatch):
    conversions=SpatialService(tmp_path);clocks=SpatialClockService(tmp_path)
    stream=stream_data();stream['clock']['source_clock']='camera'
    source=conversions.start({'stream':stream});clock=clocks.start({'fit':fit_data()})
    import harmonic_weaver.lab.research.spatial_service as module
    original=module.run
    def changed(request,folder):
        result=original(request,folder);path=clocks.root/clock['id']/'manifest.json'
        manifest=json.loads(path.read_text());manifest['limits'].append('changed');atomic_json(path,manifest)
        return result
    monkeypatch.setattr(module,'run',changed)
    with pytest.raises(ValueError,match='changed'):conversions.from_clock(clocks,{'conversion_id':source['id'],'fit_id':clock['id']})
    assert [r['id'] for r in conversions.list()]==[source['id']]
