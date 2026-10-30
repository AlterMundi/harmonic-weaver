"""Recording preferences and explicitly selected, verified output destinations."""
import json
import os
from pathlib import Path
import subprocess
import threading
from typing import Literal
from uuid import uuid4

from pydantic import Field
from .contracts import Contract,Identifier,Number
from .cache import atomic_json,sha256_file


class RecordingPreferences(Contract):
    schema_version: Literal[1]=1
    max_seconds: Number=Field(default=300,ge=1,le=300)
    include_audio: bool=True
    skeleton_overlay: bool=True
    harmonic_figure: bool=False
    format: Literal['mp4','mkv','both']='mp4'
    destination_id: Identifier|None=None


class PickRequest(Contract):
    kind: Literal['folder','drive']


class SaveRequest(Contract):
    destination_id: Identifier
    format: Literal['mp4','mkv','both']='mp4'


class CopyBusy(ValueError):
    """A rejected request that created no job and wrote no destination bytes."""


class Desktop:
    def __init__(self,root):self.root=Path(root)
    def __call__(self,request,timeout=30):
        env=dict(os.environ)
        config=self.root/'desktop.json'
        if config.is_file():
            allowed={'DISPLAY','XAUTHORITY','DBUS_SESSION_BUS_ADDRESS','XDG_RUNTIME_DIR'}
            env.update({k:v for k,v in json.loads(config.read_text()).items() if k in allowed})
        command=['/usr/bin/python3',str(Path(__file__).with_name('recording_desktop.py'))]
        p=subprocess.run(command,input=json.dumps(request),capture_output=True,text=True,timeout=timeout,env=env)
        try:result=json.loads(p.stdout)
        except ValueError:raise ValueError('El selector de carpetas no está disponible en esta computadora.')
        if p.returncode or result.get('status')=='error':raise ValueError(result.get('error','No se pudo confirmar el destino.'))
        return result


class RecordingStorage:
    def __init__(self,data_dir,exports,*,desktop=None):
        self.root=Path(data_dir)/'recording';self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.exports=exports;self.desktop=desktop or Desktop(self.root)
        self.lock=threading.RLock();self.picker_lock=threading.Lock();self.thread=None
        self.jobs={}
        (self.root/'deliveries').mkdir(exist_ok=True,mode=0o700)
        for file in (self.root/'deliveries').glob('*.json'):
            try:
                job=json.loads(file.read_text())
                if job['status'] in ('copying','verifying'):
                    job.update(status='unconfirmed',error='El proceso se cerró sin confirmar la copia. Verificá el destino antes de repetir.');self._save_job(job)
                self.jobs[job['id']]=job
            except (OSError,ValueError,KeyError):pass
    def _read(self,name,default):
        path=self.root/name
        return json.loads(path.read_text()) if path.is_file() else default
    def _write(self,name,value):
        atomic_json(self.root/name,value);os.chmod(self.root/name,0o600)
    def preferences(self):return RecordingPreferences.model_validate(self._read('preferences.json',{})).model_dump()
    def save_preferences(self,value):
        prefs=RecordingPreferences.model_validate(value)
        if prefs.destination_id and prefs.destination_id not in self._read('destinations.json',{}):raise ValueError('Elegí una carpeta confirmada.')
        self._write('preferences.json',prefs.model_dump());return prefs.model_dump()
    def account(self):return self._read('provider.json',{}).get('account','')
    def destinations(self):return list(self._read('destinations.json',{}).values())
    def provider(self):
        account=self.account()
        try:return self.desktop({'action':'status','account':account})
        except (OSError,ValueError,subprocess.TimeoutExpired):return {'account':account,'account_available':False,'connect_available':False}
    def connect(self):
        if not self.account():raise ValueError('Configurá la cuenta de Drive de esta instalación.')
        return self.desktop({'action':'connect','account':self.account()})
    def pick(self,kind):
        if kind=='drive' and not self.account():raise ValueError('Configurá la cuenta de Drive de esta instalación.')
        if not self.picker_lock.acquire(blocking=False):raise ValueError('Ya hay un selector de carpetas abierto.')
        try:
            result=self.desktop({'action':'pick','kind':kind,'account':self.account()},timeout=180)
            if result['status']=='cancelled':return result
            if result['status']!='selected':raise ValueError('No se confirmó una carpeta.')
            from .recording_desktop import cloud_account
            uri=result['uri']
            if kind=='drive' and (not self.account() or cloud_account(uri)!=self.account().casefold()):raise ValueError('La carpeta debe pertenecer a la cuenta institucional elegida.')
            if kind=='folder' and (not uri.startswith('file://') or '/gvfs/google-drive:' in uri):raise ValueError('Elegí una carpeta local.')
            with self.lock:
                rows=self._read('destinations.json',{})
                existing=next((r for r in rows.values() if r['uri']==uri and r['kind']==kind),None)
                row=existing or {'id':uuid4().hex,'kind':kind,'uri':uri,'label':result['label'],'account':self.account() if kind=='drive' else None}
                rows[row['id']]=row;self._write('destinations.json',rows)
            return {'status':'selected','destination':row}
        finally:self.picker_lock.release()
    def list(self):return json.loads(json.dumps(list(self.jobs.values())))
    def _save_job(self,job):self._write('deliveries/'+job['id']+'.json',job)
    def start(self,export_id,request):
        request=SaveRequest.model_validate(request)
        with self.lock:
            destination=self._read('destinations.json',{}).get(request.destination_id)
            if not destination:raise ValueError('Elegí una carpeta confirmada.')
            if destination['kind']=='drive' and destination.get('account','').casefold()!=self.account().casefold():raise ValueError('Volvé a elegir la carpeta de la cuenta de Drive actual.')
            if self.exports is None:raise ValueError('No hay exportaciones disponibles.')
            for old in self.jobs.values():
                if old['export_id']==export_id and old['destination']['id']==request.destination_id and old['format']==request.format:
                    if old['status'] in ('complete','copying','verifying'):return old
                    if old['status']=='unconfirmed':raise ValueError('Verificá el guardado anterior antes de repetirlo.')
            if self.thread and self.thread.is_alive():raise CopyBusy('Esperá a que termine el guardado en curso.')
            ident=uuid4().hex;files=[]
            for name in (['preview.mp4','capture.mkv'] if request.format=='both' else ['preview.mp4' if request.format=='mp4' else 'capture.mkv']):
                source=self.exports.artifact(export_id,name)
                files.append({'source':str(source),'filename':f'HarmoCap-{export_id[:8]}-{ident[:8]}{source.suffix}',
                    'sha256':sha256_file(source),'size':source.stat().st_size})
            job={'id':ident,'export_id':export_id,'destination':destination,'format':request.format,'status':'copying','files':files,'verified_files':[],'error':None}
            self.jobs[ident]=job;self._save_job(job)
            self.thread=threading.Thread(target=self._work,args=(job,False),daemon=True,name='recording-save');self.thread.start()
            return json.loads(json.dumps(job))
    def _work(self,job,verify):
        try:
            job['verified_files']=[]
            for file in job['files']:
                result=self.desktop({'action':'verify' if verify else 'copy',**job['destination'],**file},timeout=900)
                if result.get('status')!='verified' or result.get('sha256')!=file['sha256'] or result.get('size')!=file['size']:raise ValueError('No se pudo verificar el archivo guardado.')
                job['verified_files'].append(result);self._save_job(job)
            job.update(status='complete',error=None)
        except Exception:
            job.update(status='unconfirmed',error='No se confirmó el guardado. Los originales siguen disponibles; verificá el destino antes de repetir.')
        finally:
            try:self._save_job(job)
            except OSError:job.update(status='unconfirmed',error='No se pudo conservar la confirmación del guardado. Verificá el destino antes de repetir.')
    def verify(self,ident):
        with self.lock:
            if self.thread and self.thread.is_alive():raise ValueError('Esperá a que termine el guardado en curso.')
            job=self.jobs.get(ident)
            if not job:raise ValueError('Guardado desconocido.')
            job['status']='verifying';self._save_job(job)
            self.thread=threading.Thread(target=self._work,args=(job,True),daemon=True,name='recording-verify');self.thread.start()
            return json.loads(json.dumps(job))
