"""Settings are independent from the instrument; copies need real readback."""
from pathlib import Path
import hashlib
import json
import shutil
import time
import threading
from urllib.parse import urlsplit

import pytest
from fastapi.testclient import TestClient
from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.recording_storage import RecordingStorage,RecordingPreferences,SaveRequest
from harmonic_weaver.lab.recording_desktop import cloud_account,drive_status


class Exports:
    def __init__(self,root):
        self.root=root;root.mkdir();(root/'preview.mp4').write_bytes(b'synthetic video');(root/'capture.mkv').write_bytes(b'synthetic original')
    def artifact(self,ident,name):
        if ident!='export' or name not in ['preview.mp4','capture.mkv']:raise ValueError('Unknown export')
        return self.root/name


class Desktop:
    def __init__(self,folder):self.folder=folder;self.calls=[];self.lose_ack=False;self.uri=folder.as_uri();self.cancel=False
    def __call__(self,request,timeout=30):
        self.calls.append(request)
        if request['action']=='status':return {'account':request['account'],'account_available':False,'connect_available':True}
        if request['action']=='pick':return {'status':'cancelled'} if self.cancel else {'status':'selected','uri':self.uri,'label':'Test destination'}
        if request['action']=='connect':return {'status':'opened'}
        target=self.folder/request['filename']
        if request['action']=='copy':
            if target.exists():raise ValueError('Do not overwrite')
            shutil.copyfile(request['source'],target)
            if self.lose_ack:self.lose_ack=False;raise OSError('Synthetic lost acknowledgement')
        digest=hashlib.sha256(target.read_bytes()).hexdigest()
        return {'status':'verified','uri':target.as_uri(),'size':target.stat().st_size,'sha256':digest}


def service(tmp_path):
    folder=tmp_path/'chosen';folder.mkdir();desktop=Desktop(folder)
    return RecordingStorage(tmp_path,Exports(tmp_path/'exports'),desktop=desktop),desktop,folder


def finished(storage):
    storage.thread.join(timeout=5);assert not storage.thread.is_alive()
    return storage.list()[-1]


def test_preferences_and_picker_do_not_record_or_modify_the_instrument(tmp_path):
    app=create_app(tmp_path);folder=tmp_path/'chosen';folder.mkdir();fake=Desktop(folder);app.state.recording_storage.desktop=fake
    with TestClient(app,base_url='http://127.0.0.1') as client:
        before=client.get('/api/state').json()['preset']
        assert client.get('/api/recording-preferences').json()==RecordingPreferences().model_dump()
        result=client.post('/api/recording-destinations/pick',json={'kind':'folder'}).json()
        prefs={**RecordingPreferences().model_dump(),'include_audio':False,'harmonic_figure':True,'skeleton_overlay':False,'destination_id':result['destination']['id'],'format':'both'}
        assert client.post('/api/recording-preferences',json=prefs).json()==prefs
        assert client.get('/api/state').json()['preset']==before
        assert client.get('/api/captures').json()['jobs']==[]
        assert client.post('/api/recording-preferences',json={**prefs,'destination_id':'unknown'}).status_code==422
        assert client.post('/api/recording-destinations/pick',json={'kind':'arbitrary'}).status_code==422
        assert client.post('/api/recording-preferences',json={**prefs,'path':'/ungranted'}).status_code==422
    assert RecordingStorage(tmp_path,None,desktop=fake).preferences()==prefs


def test_cancel_does_not_create_a_destination(tmp_path):
    storage,desktop,_=service(tmp_path);desktop.cancel=True
    assert storage.pick('folder')=={'status':'cancelled'} and not storage.destinations()


def test_verified_copy_is_persisted_deduplicated_and_preserves_originals(tmp_path):
    storage,desktop,folder=service(tmp_path);ident=storage.pick('folder')['destination']['id']
    original={p:p.read_bytes() for p in storage.exports.root.iterdir()}
    job=storage.start('export',{'destination_id':ident,'format':'both'});result=finished(storage)
    assert result['status']=='complete' and len(result['verified_files'])==2
    assert storage.start('export',{'destination_id':ident,'format':'both'})['id']==job['id']
    assert len([c for c in desktop.calls if c['action']=='copy'])==2
    assert all(p.read_bytes()==data for p,data in original.items())
    restarted=RecordingStorage(tmp_path,storage.exports,desktop=desktop)
    assert restarted.list()[0]['status']=='complete' and len(list(folder.iterdir()))==2


def test_uncertain_copy_is_never_replayed_but_can_be_verified(tmp_path):
    storage,desktop,folder=service(tmp_path);ident=storage.pick('folder')['destination']['id'];desktop.lose_ack=True
    job=storage.start('export',{'destination_id':ident});assert finished(storage)['status']=='unconfirmed'
    with pytest.raises(ValueError,match='Verific'):storage.start('export',{'destination_id':ident})
    assert len(list(folder.iterdir()))==1
    storage.verify(job['id']);assert finished(storage)['status']=='complete'
    assert len([c for c in desktop.calls if c['action']=='copy'])==1


def test_restart_does_not_resume_an_uncertain_remote_write(tmp_path):
    storage,desktop,_=service(tmp_path);ident=storage.pick('folder')['destination']['id']
    job=storage.start('export',{'destination_id':ident});finished(storage)
    file=storage.root/'deliveries'/f'{job["id"]}.json';value=json.loads(file.read_text());value['status']='copying';file.write_text(json.dumps(value));desktop.calls.clear()
    restored=RecordingStorage(tmp_path,storage.exports,desktop=desktop)
    assert restored.list()[0]['status']=='unconfirmed' and desktop.calls==[]


def test_drive_requires_the_selected_account_and_never_accepts_an_arbitrary_uri(tmp_path):
    storage,desktop,_=service(tmp_path);storage._write('provider.json',{'account':'studio@example.test'})
    desktop.uri='google-drive://wrong@example.test/folder'
    with pytest.raises(ValueError,match='cuenta'):storage.pick('drive')
    assert not storage.destinations()
    desktop.uri='google-drive://studio@example.test/folder';row=storage.pick('drive')['destination']
    assert row['account']=='studio@example.test'
    assert cloud_account(row['uri'])=='studio@example.test'
    desktop.uri='https://not-a-drive.invalid/folder'
    with pytest.raises(ValueError):storage.pick('drive')
    with pytest.raises(ValueError):storage.pick('folder')
    storage._write('provider.json',{'account':'other@example.test'})
    with pytest.raises(ValueError,match='actual'):storage.start('export',{'destination_id':row['id']})


def test_drive_detection_does_not_call_google_or_read_keyring(tmp_path,monkeypatch):
    monkeypatch.setattr(Path,'home',lambda:tmp_path)
    path=tmp_path/'.config/goa-1.0/accounts.conf';path.parent.mkdir(parents=True)
    path.write_text('[Account test]\nProvider=google\nIdentity=studio@example.test\nFilesEnabled=true\n')
    assert drive_status('studio@example.test')['account_available']
    assert not drive_status('wrong@example.test')['account_available']
    path.write_text(path.read_text().replace('FilesEnabled=true','FilesEnabled=false'))
    assert not drive_status('studio@example.test')['account_available']


def test_corrupt_readback_never_claims_success(tmp_path):
    storage,desktop,_=service(tmp_path);ident=storage.pick('folder')['destination']['id']
    original=storage.desktop
    def corrupt(request,timeout=30):
        result=original(request,timeout);result['sha256']='bad';return result
    storage.desktop=corrupt;storage.start('export',{'destination_id':ident})
    assert finished(storage)['status']=='unconfirmed'


def test_confirmation_persistence_failure_is_visible(tmp_path,monkeypatch):
    storage,desktop,_=service(tmp_path);ident=storage.pick('folder')['destination']['id']
    original=storage._save_job
    def fail(job):
        if job.get('verified_files'):raise OSError('Synthetic disk full')
        return original(job)
    monkeypatch.setattr(storage,'_save_job',fail);storage.start('export',{'destination_id':ident})
    assert finished(storage)['status']=='unconfirmed'


def test_active_duplicate_is_retained_and_busy_rejection_creates_no_new_job(tmp_path):
    app=create_app(tmp_path);storage=app.state.recording_storage
    folder=tmp_path/'chosen';folder.mkdir();desktop=Desktop(folder)
    storage.desktop=desktop;storage.exports=Exports(tmp_path/'exports')
    ident=storage.pick('folder')['destination']['id'];entered=threading.Event();release=threading.Event()
    def slow(request,timeout=30):
        if request['action']=='copy':entered.set();assert release.wait(5)
        return desktop(request,timeout)
    storage.desktop=slow
    try:
        with TestClient(app,base_url='http://127.0.0.1') as client:
            first=client.post('/api/capture-exports/export/save',json={'destination_id':ident}).json()
            assert entered.wait(2)
            assert client.post('/api/capture-exports/export/save',json={'destination_id':ident}).json()['id']==first['id']
            assert client.post('/api/capture-exports/export/save',json={'destination_id':ident,'format':'both'}).status_code==409
            assert len(storage.list())==1
    finally:release.set();finished(storage)
