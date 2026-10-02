import json
import subprocess
import threading
import pytest
from harmonic_weaver.lab.cache import sha256_file
from harmonic_weaver.lab.research.rope_flow_run import Request,calculate,run,verify
from harmonic_weaver.lab.research.rope_reader import RopeReader
from harmonic_weaver.lab.research.rope_process import DecodeCancelled


def source(tmp_path):
    video=tmp_path/'video.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=10:duration=0.5','-c:v','libx264',str(video)],check=True)
    reader=RopeReader();media=reader.probe(video)
    request={k:media[k] for k in ('media_sha256','width_px','height_px')}
    request.update(start_frame_index=1,frame_times_s=media['frame_times_s'][1:4],seeds=[{'x':.5,'y':.5}])
    return video,reader,request


def test_actual_decode_repeat_integrity_and_source_recompute(tmp_path):
    video,reader,request=source(tmp_path);a=tmp_path/'a';b=tmp_path/'b'
    run(request,video,a,reader);run(request,video,b,reader)
    assert (a/'result.json').read_bytes()==(b/'result.json').read_bytes()
    assert sorted(p.name for p in a.iterdir())==['manifest.json','request.json','result.json']
    assert verify(a,path=video,reader=reader)['status']=='complete'
    result=json.loads((a/'result.json').read_text())
    assert [f['frame_index'] for f in result['frames']]==[1,2,3]
    assert [f['time_s'] for f in result['frames']]==request['frame_times_s']
    assert result['frames'][0]['status']=='seeded'
    result['frames'][1]['rows'][0]['displacement_px']+=.01
    (a/'result.json').write_text(json.dumps(result))
    manifest=json.loads((a/'manifest.json').read_text());manifest['output']['sha256']=sha256_file(a/'result.json')
    (a/'manifest.json').write_text(json.dumps(manifest))
    assert verify(a)['status']=='complete' # Explicit integrity-only, not numerical verification.
    with pytest.raises(ValueError,match='recomputation'):verify(a,path=video,reader=reader)
    result['frames'][0]['time_s']+=.01
    (a/'result.json').write_text(json.dumps(result));manifest['output']['sha256']=sha256_file(a/'result.json')
    (a/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='clock'):verify(a)
    with video.open('ab') as handle:handle.write(b'changed')
    with pytest.raises(ValueError,match='identity'):verify(b,path=video,reader=reader)


def test_source_clock_and_cancel_do_not_publish(tmp_path):
    video,reader,request=source(tmp_path)
    bad={**request,'frame_times_s':[.1,.21,.3]}
    with pytest.raises(ValueError,match='clock'):run(bad,video,tmp_path/'bad',reader)
    assert not (tmp_path/'bad').exists()
    event=threading.Event();event.set()
    with pytest.raises(DecodeCancelled):run(request,video,tmp_path/'cancel',reader,cancel=event)
    assert not (tmp_path/'cancel').exists()
    event.clear()
    class CancelAfterDecode:
        def probe(self,*args,**kwargs):return reader.probe(*args,**kwargs)
        def frame(self,*args,**kwargs):
            png=reader.frame(*args,**kwargs);event.set();return png
    with pytest.raises(DecodeCancelled):run(request,video,tmp_path/'middle',CancelAfterDecode(),cancel=event)
    assert not (tmp_path/'middle').exists()


def test_request_budgets_and_gap_reset(tmp_path):
    video,reader,request=source(tmp_path)
    for patch in ({'frame_times_s':[.1]*2},{'frame_times_s':[i*.1 for i in range(121)]},
                  {'width_px':32768,'height_px':32768},{'settings':{'max_points':1},'seeds':[{'x':.5,'y':.5}]*2}):
        with pytest.raises(ValueError):Request.model_validate({**request,**patch})
    result=calculate({**request,'settings':{'max_gap_s':.05}},video,reader)
    assert [f['status'] for f in result['frames']]==['seeded','reset','reset']
    assert all(row['point'] is None for f in result['frames'][1:] for row in f['rows'])
