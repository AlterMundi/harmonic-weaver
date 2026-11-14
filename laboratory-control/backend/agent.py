#!/usr/bin/python3
"""Fixed per-computer service operations. Never opens a board or camera."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HOME=Path.home()
STATE=HOME/'.local/state/harmonic-lab/web-control'
LAUNCHER=HOME/'Projects/harmonic-weaver/scripts/open-harmonic-lab.py'
SERVICES={'router':(8767,'Weaver · ruteos'),'guitar':(18879,'Guitarra'),'audio':(5050,'Spatializer'),'body':(8765,'Weaver · HarMoCAP · Shaper')}

def atomic(path,data):
    pending=path.with_suffix('.pending');pending.write_text(json.dumps(data,ensure_ascii=False)+'\n');os.replace(pending,path)

def launcher():
    spec=importlib.util.spec_from_file_location('lab_launcher',LAUNCHER)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def snapshot(module=None):
    module=module or launcher()
    panel=HOME/'.local/share/hbg-cyberbrick/panel'
    enabled=module.configuration(panel)
    rows=[]
    for name,(port,label) in SERVICES.items():
        installed=(panel/'run-panel.sh').is_file() if name=='guitar' else (HOME/'Projects/harmonic-weaver/scripts/start-laboratory.sh').is_file()
        if name=='body':installed=installed and (HOME/'Projects/harmonic-shaper/.venv/bin/python').is_file()
        if name=='router':installed=(HOME/'Projects/harmonic-weaver/.venv/bin/python').is_file()
        if name=='audio':installed=installed and (HOME/'Projects/beacon-spatial/start-beacon.sh').is_file()
        ready=module.ready() if name=='guitar' else module.component_ready(port,'Spatializer' if name=='audio' else 'Weaver')
        rows.append(dict(id=name,label=label,enabled=enabled[name],installed=installed,status='ready' if ready else 'stopped' if installed else 'unavailable',url=f'http://localhost:{port}/' if ready else None))
    profile=HOME/'.config/harmonic-lab/launch.json'
    config=json.loads(profile.read_text()) if profile.is_file() else {'services':enabled,'environment':{}}
    job=None
    try:job=json.loads((STATE/'job.json').read_text())
    except (OSError,ValueError):pass
    if job and job.get('phase') in ('queued','starting') and time.time()-job.get('started',0)>300:
        job=dict(job,phase='failed',message='El inicio no terminó dentro del tiempo previsto.')
    return dict(services=rows,profile=config,job=job)

def worker(ident,names):
    STATE.mkdir(parents=True,exist_ok=True)
    with (STATE/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        m=launcher();panel=HOME/'.local/share/hbg-cyberbrick/panel';enabled=m.configuration(panel)
        job=dict(id=ident,phase='starting',services=names,results={},started=time.time(),pid=os.getpid())
        atomic(STATE/'job.json',job)
        for name in names:
            try:
                if not enabled[name]:result={'status':'not-selected'}
                else:result={'status':m.ensure_panel(panel) if name=='guitar' else m.ensure_component(name)}
            except Exception as exc:result={'status':'failed','message':str(exc)[:300]}
            job['results'][name]=result;atomic(STATE/'job.json',job)
        job.update(phase='finished',finished=time.time());atomic(STATE/'job.json',job)

def dispatch(request):
    STATE.mkdir(parents=True,exist_ok=True)
    if not isinstance(request,dict) or set(request)-{'op','service','id','profile'}:raise ValueError('Solicitud inválida')
    op=request.get('op')
    if op=='status':return snapshot()
    if op=='configure':
        profile=request.get('profile')
        if not isinstance(profile,dict) or set(profile)-{'services','environment'}:raise ValueError('Configuración inválida')
        services=profile.get('services',{});environment=profile.get('environment',{})
        if not isinstance(services,dict) or set(services)-set(SERVICES) or any(type(v)is not bool for v in services.values()):raise ValueError('Instrumentos inválidos')
        allowed={'HARMONIC_LAB_AUDIO_BACKEND','HARMONIC_SHAPER_DEVICE','HARMONIC_LAB_TRACKING_DEVICE','BEACON_OUTPUT_TARGET','BEACON_INPUT_DEVICE','BEACON_OUTPUT_DEVICE','BEACON_INPUT_PORT','BEACON_VOICE_INPUT_PORT','BEACON_OUTPUT_LEFT','BEACON_OUTPUT_RIGHT'}
        if not isinstance(environment,dict) or set(environment)-allowed or any(not isinstance(v,str) or len(v)>512 or any(c in v for c in ('\0','\n','\r')) for v in environment.values()):raise ValueError('Audio inválido')
        if environment.get('HARMONIC_LAB_AUDIO_BACKEND','auto') not in ('auto','native','jack'):raise ValueError('Backend inválido')
        path=HOME/'.config/harmonic-lab/launch.json';path.parent.mkdir(parents=True,exist_ok=True)
        atomic(path,profile);path.chmod(0o600)
        return snapshot()
    if op!='start':raise ValueError('Operación no admitida')
    name=request.get('service');ident=request.get('id')
    if name not in (*SERVICES,'all') or not isinstance(ident,str) or not 1<=len(ident)<=64 or not all(c.isalnum() or c in '-_' for c in ident):raise ValueError('Inicio inválido')
    names=list(SERVICES) if name=='all' else [name]
    with (STATE/'request.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        ledger_path=STATE/'requests.json'
        try:ledger=json.loads(ledger_path.read_text())
        except (OSError,ValueError):ledger=[]
        previous=next((item for item in ledger if item['id']==ident),None)
        if previous:
            if previous['services']!=names:raise ValueError('Identificador reutilizado con otros instrumentos')
            return snapshot()
        old=None
        try:old=json.loads((STATE/'job.json').read_text())
        except (OSError,ValueError):pass
        if old and old.get('id')==ident:return snapshot()
        if old and old.get('phase') in ('queued','starting') and time.time()-old.get('started',0)<300:
            return snapshot()
        atomic(STATE/'job.json',dict(id=ident,phase='queued',services=names,results={},started=time.time()))
        ledger.append(dict(id=ident,services=names));atomic(ledger_path,ledger[-32:])
        subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker',ident,*names],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
    return snapshot()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--worker',nargs='+');args=parser.parse_args()
    if args.worker:
        ident,*names=args.worker
        if not names or any(n not in SERVICES for n in names):raise SystemExit(2)
        worker(ident,names)
    else:
        try:
            raw=sys.stdin.buffer.read(16385)
            if len(raw)>16384:raise ValueError('Solicitud demasiado grande')
            print(json.dumps({'ok':True,'data':dispatch(json.loads(raw))},ensure_ascii=False))
        except Exception as exc:print(json.dumps({'ok':False,'error':str(exc)[:300]},ensure_ascii=False));raise SystemExit(1)
