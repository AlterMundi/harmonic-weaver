"""Explicit audio/journal capture with separately opted-in processed camera previews."""
import json
from pathlib import Path
import threading
import time
from uuid import uuid4

import httpx
from pydantic import Field
from .contracts import Contract, Number
from .cache import atomic_json, sha256_file


class CaptureSettings(Contract):
    max_seconds: Number = Field(default=120,ge=.1,le=3600)
    queue_blocks: int = Field(default=128,ge=4,le=1024)
    timeline_hz: int = Field(default=20,ge=1,le=60)
    record_camera: bool = False
    camera_queue_frames: int = Field(default=8,ge=1,le=128)
    camera_max_frames: int = Field(default=10000,ge=1,le=216000)
    camera_max_mb: int = Field(default=256,ge=1,le=8192)


class CaptureSession:
    def __init__(self, data_dir, store, runtime, *, client_factory=None):
        self.root=Path(data_dir)/'captures'
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.store,self.runtime=store,runtime
        url=getattr(getattr(runtime,'audio',None),'url','http://127.0.0.1:8085')
        self.client_factory=client_factory or (lambda:httpx.Client(base_url=url,timeout=8,trust_env=False))
        self.lock=threading.RLock()
        self.stop_event=threading.Event()
        self.thread=None
        self.recovery_thread=None
        self.recovery_job={'status':'idle'}
        self.job=None
        self.jobs={}
        for folder in sorted(self.root.iterdir()):
            if (folder/'manifest.json').is_file():
                try:
                    job=json.loads((folder/'manifest.json').read_text())
                    if job['status'] in ('starting','recording','stopping'):
                        job['status']='interrupted'
                        job['error']='Collector process stopped before a confirmed close'
                        atomic_json(folder/'manifest.json',job)
                    recovery_path=folder/'recovery.json'
                    if recovery_path.is_file():
                        try:
                            recovery=json.loads(recovery_path.read_text())
                            if recovery.get('status') in ('recovering','audio_recovered'):
                                recovery.update(status='interrupted',error='Recovery collector stopped before a confirmed finish')
                                atomic_json(recovery_path,recovery)
                            job['recovery']=recovery
                        except (OSError,ValueError): pass
                    self.jobs[job['id']]=job
                except (OSError,ValueError,KeyError): pass

    def _boundary(self):
        if hasattr(self.runtime,'capture_boundary'): return self.runtime.capture_boundary()
        value=self.store.event_boundary();value['state'].update(self.runtime.snapshot());return value

    def start(self, settings):
        settings=CaptureSettings.model_validate(settings)
        with self.lock:
            if self.thread and self.thread.is_alive(): raise ValueError('Ya hay una captura activa')
            ident=uuid4().hex; folder=self.root/ident;folder.mkdir(mode=0o700)
            from .evaluation.runner import code_identity
            code=code_identity()
            ui_root=Path(__file__).resolve().parents[3]/'laboratory-ui'
            code['ui_files']={str(p.relative_to(ui_root)):sha256_file(p)
                              for p in sorted((ui_root/'src').rglob('*')) if p.is_file()}
            boundary=self._boundary()
            self.job=dict(schema_version=1,id=ident,status='starting',error=None,settings=settings.model_dump(),
                directory=str(folder),owner='weaver_'+ident,shaper=None,events=0,timeline_rows=0,
                initial=boundary,code={'weaver':code},requested_monotonic_s=time.monotonic(),
                stages={'audio':'Shaper post_shape_master_soft_limiter','video':'processed_camera_preview_opt_in' if settings.record_camera else 'not_recorded'},
                limits=['Camera preview pixels only after explicit opt-in; file video referenced in place','Timeline is sampled, events are committed journal entries',
                        'Warm model/router state is not serialized: no exact recomputation claim',
                        'DAC timestamps are backend reports, not audiovisual latency measurements'])
            self.jobs[ident]=self.job
            atomic_json(folder/'manifest.json',self.job)
            self.stop_event.clear()
            self.thread=threading.Thread(target=self._record,args=(settings,boundary['cursor']),daemon=True,name='lab-capture')
            self.thread.start()
            return self.snapshot()

    @staticmethod
    def source_identity(source):
        source=source or {}
        job=source.get('job') or {}
        identity={k:job.get(k) for k in ('id','path','media_id','cache_key','generation','cache_location')}
        identity['kind']=source.get('kind')
        identity['camera']=source.get('camera')
        identity['media_hash_origin']='tracking library declaration; original not rehashed or copied'
        location=job.get('cache_location')
        if location:
            try: identity['cache_manifest_sha256']=sha256_file(location)
            except OSError as exc: identity['cache_manifest_error']=str(exc)
        return identity

    def _record(self, settings, cursor):
        job=self.job;folder=Path(job['directory'])
        driver_id=None
        camera=None
        try:
            job['initial_source_identity']=self.source_identity(job['initial']['state'].get('source'))
            with self.client_factory() as client:
                payload={k:settings.model_dump()[k] for k in ('max_seconds','queue_blocks')}
                payload['owner']=job['owner']
                try:
                    response=client.post('/api/audio/capture/start',json=payload);response.raise_for_status()
                    driver=response.json()
                except httpx.HTTPError:
                    # Resolve only this nonce. Never stop another recorder after a lost ack.
                    response=client.get('/api/audio/capture');response.raise_for_status();driver=response.json()
                    if driver.get('owner')!=job['owner']: raise ValueError('No se pudo confirmar el inicio propio de Shaper')
                if driver.get('owner')!=job['owner']: raise ValueError('Shaper no reconoce este contrato de captura')
                driver_id=driver['id'];job['shaper']=driver
                if driver['status']=='failed': raise ValueError(driver.get('error') or 'Shaper capture failed')
                job['status']='recording';atomic_json(folder/'manifest.json',job)
                if settings.record_camera:
                    from .capture_camera import CameraCapture
                    camera=CameraCapture(folder,queue_frames=settings.camera_queue_frames,
                        max_frames=settings.camera_max_frames,max_bytes=settings.camera_max_mb*1024*1024)
                with (folder/'events.jsonl').open('w') as events, (folder/'timeline.jsonl').open('w') as timeline:
                    while True:
                        rows=self.store.events_since(cursor)
                        for row in rows:
                            events.write(json.dumps(self._event_record(row),sort_keys=True,allow_nan=False)+'\n')
                            cursor=row['sequence'];job['events']+=1
                        sampled=time.monotonic()
                        state=self._boundary()['state']
                        camera_ref=None
                        if camera:
                            camera_ref=camera.offer(self.runtime.capture_preview())
                            job['camera']=camera.snapshot()
                        timeline.write(json.dumps({'sampled_monotonic_s':sampled,'state':state,'camera_ref':camera_ref},sort_keys=True,allow_nan=False)+'\n')
                        job['timeline_rows']+=1
                        if job['timeline_rows']==1 or sampled-job.get('last_poll',0)>=.2:
                            response=client.get('/api/audio/capture');response.raise_for_status()
                            driver=response.json();job['shaper']=driver;job['last_poll']=sampled
                            if driver.get('id')!=driver_id: raise ValueError('La captura Shaper fue reemplazada')
                            if driver['status'] in ('complete','failed'): break
                        if self.stop_event.wait(1/settings.timeline_hz): break
                    response=client.post('/api/audio/capture/stop',json={'id':driver_id});response.raise_for_status()
                    driver=response.json();job['shaper']=driver
                    deadline=time.monotonic()+15
                    while driver.get('writer_alive') and time.monotonic()<deadline:
                        time.sleep(.1)
                        response=client.get('/api/audio/capture');response.raise_for_status();driver=response.json()
                        if driver.get('id')!=driver_id: raise ValueError('La captura Shaper fue reemplazada al cerrar')
                        job['shaper']=driver
                    # Final committed boundary, not a fixed-size history slice.
                    final_cursor=self.store.event_boundary()['cursor']
                    while cursor<final_cursor:
                        rows=self.store.events_since(cursor)
                        if not rows: raise ValueError('Journal boundary could not be drained')
                        for row in rows:
                            if row['sequence']>final_cursor: break
                            events.write(json.dumps(self._event_record(row),sort_keys=True,allow_nan=False)+'\n')
                            cursor=row['sequence'];job['events']+=1
                    job['final_event_cursor']=cursor
                if driver['status']!='complete' or driver.get('writer_alive'):
                    raise ValueError(driver.get('error') or 'Shaper writer has not confirmed completion')
                if camera:
                    job['camera']=camera.close()
                    if job['camera']['status']!='complete':raise ValueError(job['camera']['error'] or 'Camera writer failed')
                job['status']='complete'
                job['hashes']={p.name:sha256_file(p) for p in (folder/'events.jsonl',folder/'timeline.jsonl')}
        except Exception as exc:
            job['status']='failed';job['error']=str(exc)
            if driver_id:
                try:
                    with self.client_factory() as client: client.post('/api/audio/capture/stop',json={'id':driver_id})
                except Exception: pass
        finally:
            if camera:
                try:job['camera']=camera.close(error=job.get('error') if camera.thread.is_alive() else None)
                except OSError as exc:job['status']='failed';job['error']=str(exc)
            job['ended_monotonic_s']=time.monotonic()
            try: atomic_json(folder/'manifest.json',job)
            except OSError as exc: job['status']='failed';job['error']=f'{job.get("error") or ""}; manifest: {exc}'

    def _event_record(self, row):
        if row['event']['kind']!='source': return row
        payload=row['event']['payload']
        return {**row,'source_identity':self.source_identity(payload)}

    def stop(self):
        with self.lock:
            if self.job and self.thread and self.thread.is_alive():
                self.stop_event.set()
            return self.snapshot()

    def recover(self, ident):
        with self.lock:
            if self.recovery_thread and self.recovery_thread.is_alive(): raise ValueError('Ya hay una recuperación activa')
            job=self.jobs.get(ident)
            if self.thread and self.thread.is_alive() and self.job and self.job['id']==ident:
                raise ValueError('La captura todavía está cerrando')
            if not job or job['status'] not in ('failed','interrupted'): raise ValueError('Elegí una captura fallida o interrumpida')
            driver_id=(job.get('shaper') or {}).get('id')
            if not driver_id: raise ValueError('No hay identidad confirmada de la captura Shaper')
            previous=job.get('recovery') or {}
            recovery_id=(previous.get('shaper_recovery_job_id') if previous.get('status') in ('recovering','unconfirmed','interrupted') else None) or uuid4().hex
            self.recovery_job={'status':'recovering','capture_id':ident,'shaper_recovery_job_id':recovery_id}
            def persist():
                snapshot=self.recovery_snapshot()
                atomic_json(Path(job['directory'])/'recovery.json',snapshot)
                job['recovery']=snapshot
            persist()
            def work():
                acknowledgement_lost=False
                try:
                    with self.client_factory() as client:
                        contract=client.get('/api/audio/capture/recovery-contract')
                        supports_retry=contract.status_code==200 and contract.json().get('schema_version')==1 and contract.json().get('idempotent_source_hashes') is True
                        if contract.status_code==200 and contract.json().get('pollable_jobs') is True:
                            from .capture_recovery_poll import recover as recover_polled
                            result=recover_polled(client,driver_id,recovery_id)
                        else:
                            try:response=client.post('/api/audio/capture/recover',json={'id':driver_id},timeout=120)
                            except httpx.TransportError:
                                acknowledgement_lost=True
                                if not supports_retry:raise
                                response=client.post('/api/audio/capture/recover',json={'id':driver_id},timeout=120)
                            response.raise_for_status();result=response.json()
                    if result.get('status')!='recovered' or result.get('capture_id')!=driver_id:
                        raise ValueError('Shaper did not confirm this recovered prefix')
                    from .capture_journal_recovery import recover_journal
                    self.recovery_job.update(result=result)
                    self.recovery_job.update(phase='journal',journal_status='pending')
                    persist()
                    try:journal=recover_journal(job['directory'])
                    except (OSError,ValueError) as exc:journal={'status':'failed','error':str(exc)}
                    camera={'status':'not_recorded'}
                    if (Path(job['directory'])/'camera').exists():
                        from .capture_camera_recovery import recover_camera
                        try:camera=recover_camera(job['directory'])
                        except (OSError,ValueError) as exc:camera={'status':'failed','error':str(exc)}
                    self.recovery_job.update(status='recovered',result=result,journal=journal,camera=camera)
                    persist()
                except Exception as exc:
                    from .capture_recovery_poll import UnconfirmedRecovery
                    status='unconfirmed' if (acknowledgement_lost or isinstance(exc,UnconfirmedRecovery)) and 'result' not in self.recovery_job else 'failed'
                    self.recovery_job.update(status=status,error=str(exc))
                    try:persist()
                    except OSError as disk_error:
                        self.recovery_job['persistence_error']=str(disk_error)
                        job['recovery']=self.recovery_snapshot()
            self.recovery_thread=threading.Thread(target=work,daemon=True,name='lab-capture-recovery')
            self.recovery_thread.start()
            return self.recovery_snapshot()

    def recovery_snapshot(self):return json.loads(json.dumps(dict(self.recovery_job)))

    def snapshot(self):
        return json.loads(json.dumps(dict(self.job))) if self.job else {'status':'idle'}

    def list(self):
        return [json.loads(json.dumps(dict(j))) for j in list(self.jobs.values())]

    def close(self):
        self.stop()
        # The journal must remain open until the collector drains its final boundary.
        # HTTP calls have finite timeouts; never close SQLite under this worker.
        if self.thread: self.thread.join()
        if self.recovery_thread: self.recovery_thread.join()
