import os
import pytest
from harmonic_weaver.lab.research import projection_reader
from harmonic_weaver.lab.research.model_projection import project
from harmonic_weaver.lab.research.resonator_run import run
from harmonic_weaver.lab.research.mechanism_run import run as run_pair


def fixture(folder,paired=False):
    doc={'request':dict(evaluation_id='a'*32,run_index=0,signal_id='speed',start_s=0,end_s=.3,high=1,low=.2),
         'unit':'T/s','rows':[{'time_s':t,'value':v,'valid':True} for t,v in [(0,0),(.03,2)]]}
    request={'resonators':{'sample_rate':8000},'render':{'tail_s':.1}}
    if paired:run_pair(doc,{**request,'mapping':{}},folder)
    else:run(doc,request,folder)


@pytest.mark.parametrize('paired',[False,True])
def test_repeated_window_uses_cached_verification_and_changes_invalidate(tmp_path,monkeypatch,paired):
    folder=tmp_path/'run';fixture(folder,paired);reader=projection_reader.ProjectionReader()
    calls=[];original=projection_reader.verify_arm
    def counted(path):calls.append(path);return original(path)
    monkeypatch.setattr(projection_reader,'verify_arm',counted)
    request={'arm':'mapped' if paired else 'single','start_sample':300,'points':32}
    first=project(folder,request,reader=reader)
    assert project(folder,request,reader=reader)==first and len(calls)==1
    # A same-content rewrite retaining mtime still changes ctime and invalidates.
    path=folder/'request.json';info=path.stat();content=path.read_bytes()
    path.write_bytes(content);os.utime(path,ns=(info.st_atime_ns,info.st_mtime_ns))
    assert project(folder,request,reader=reader)==first and len(calls)==2
    pcm=folder/('excited/sum.wav' if paired else 'sum.wav')
    pcm.write_bytes(b'altered')
    with pytest.raises(ValueError):project(folder,request,reader=reader)
    assert not reader.cache
    reader.close()


def test_symlink_and_during_read_changes_discard_cache(tmp_path,monkeypatch):
    folder=tmp_path/'run';fixture(folder);reader=projection_reader.ProjectionReader()
    project(folder,{},reader=reader)
    original=reader.check
    def mutate(folder,arm,expected):
        (folder/'sum.wav').write_bytes(b'changed')
        return original(folder,arm,expected)
    monkeypatch.setattr(reader,'check',mutate)
    with pytest.raises(ValueError,match='during read'):project(folder,{},reader=reader)
    assert not reader.cache
    other=tmp_path/'other';fixture(other)
    reader.prepare(other,'single')
    (other/'voices.wav').rename(other/'backup.wav');(other/'voices.wav').symlink_to(other/'backup.wav')
    with pytest.raises(ValueError,match='Regular'):reader.prepare(other,'single')
    assert not reader.cache


def test_capacity_and_close_bound_cached_metadata(tmp_path):
    reader=projection_reader.ProjectionReader();reader.capacity=2
    for i in range(3):
        folder=tmp_path/str(i);fixture(folder);reader.prepare(folder,'single')
    assert len(reader.cache)==2
    assert not any(key[0].endswith('/0') for key in reader.cache)
    reader.close();assert not reader.cache
