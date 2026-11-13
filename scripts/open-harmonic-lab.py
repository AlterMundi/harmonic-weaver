#!/usr/bin/env python3
"""Explicit local URI activation: reuse or start the finite panel, then open it."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shlex
import socket
import subprocess
import time
from urllib.request import build_opener, ProxyHandler

URL = 'http://localhost:18879/'


def ready():
    try:
        with build_opener(ProxyHandler({})).open('http://127.0.0.1:18879/state',timeout=.4) as r:
            state=json.loads(r.read(65537))
            return r.status==200 and isinstance(state.get('usb'),dict) and 'busy' in state and 'phase' in state
    except Exception:
        return False


def ensure_panel(panel):
    if ready():return 'reused'
    # Refuse an unrelated port owner; never kill or replace another process.
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1',18879))==0:
            raise RuntimeError('El puerto del controlador está ocupado por otra aplicación')
    script=panel/'run-panel.sh'
    if not script.is_file():raise RuntimeError('Falta la instalación del controlador')
    result=subprocess.run(['tmux','has-session','-t','=hbg-motor-panel'],capture_output=True,timeout=4)
    if result.returncode:
        subprocess.run(['tmux','new-session','-d','-s','hbg-motor-panel',shlex.quote(str(script))],check=True,timeout=4)
    deadline=time.monotonic()+12
    while time.monotonic()<deadline:
        if ready():return 'started'
        time.sleep(.15)
    raise RuntimeError('El controlador no pudo iniciar. Consultá el registro del panel.')


def component_ready(port, title):
    try:
        with build_opener(ProxyHandler({})).open(f'http://127.0.0.1:{port}/',timeout=.5) as r:
            return r.status==200 and title in r.read(65536).decode(errors='replace')
    except Exception:return False


def ensure_component(kind):
    if kind=='router':
        return ensure_router()
    port,title,session,flags,seconds=(5050,'Spatializer','harmonic-lab',[],60) if kind=='audio' else (8765,'Weaver','harmonic-lab-body',['--body-only'],200)
    if component_ready(port,title):return 'reused'
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1',port))==0:raise RuntimeError('La interfaz está ocupada por otra aplicación')
    checkout=Path.home()/'Projects/harmonic-weaver'
    entry=checkout/'scripts/start-live-stack.sh'
    if not entry.is_file():raise RuntimeError('Falta la instalación del laboratorio')
    if subprocess.run(['tmux','has-session','-t','='+session],capture_output=True,timeout=4).returncode:
        command=shlex.join([str(entry),'--guitar-lab',*flags])
        # Session entry owns its finite children and bounded component logs.
        subprocess.run(['tmux','new-session','-d','-s',session,command],check=True,timeout=4)
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        if component_ready(port,title):return 'started'
        if subprocess.run(['tmux','has-session','-t','='+session],capture_output=True,timeout=4).returncode:
            raise RuntimeError('El laboratorio no pudo iniciar. Consultá el registro de la sesión.')
        time.sleep(.4)
    raise RuntimeError('El laboratorio sigue preparando su interfaz; revisá la sesión antes de reintentar')


def ensure_router():
    """Use the maintained headless engine without opening hardware or reports."""
    if component_ready(8767,'Harmonic Weaver'):return 'reused'
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1',8767))==0:raise RuntimeError('La interfaz de ruteos está ocupada')
    root=Path.home()/'Projects/harmonic-weaver'
    if not(root/'.venv/bin/python').is_file():raise RuntimeError('Falta instalar el motor de ruteos')
    session='harmonic-lab-router'
    if subprocess.run(['tmux','has-session','-t','='+session],capture_output=True,timeout=4).returncode:
        subprocess.run(['tmux','new-session','-d','-s',session,shlex.join([str(root/'.venv/bin/python'),str(root/'scripts/router-session.py')])],check=True,timeout=4)
    deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        if component_ready(8767,'Harmonic Weaver'):return 'started'
        time.sleep(.2)
    raise RuntimeError('El motor de ruteos no pudo iniciar')


def configuration(panel):
    path=Path.home()/'.config/harmonic-lab/launch.json'
    config=json.loads(path.read_text()) if path.is_file() else {}
    services={'router':False,'guitar':(panel/'run-panel.sh').is_file(),'audio':False,'body':(Path.home()/'Projects/harmonic-weaver/scripts/start-laboratory.sh').is_file()}
    selected=config.get('services',{})
    if set(selected)-set(services) or any(type(v) is not bool for v in selected.values()):raise ValueError('Selección de instrumentos inválida')
    services.update(selected)
    allowed={'HARMONIC_LAB_AUDIO_BACKEND','HARMONIC_SHAPER_DEVICE','HARMONIC_LAB_TRACKING_DEVICE','BEACON_OUTPUT_TARGET','BEACON_INPUT_DEVICE','BEACON_OUTPUT_DEVICE','BEACON_INPUT_PORT','BEACON_OUTPUT_LEFT','BEACON_OUTPUT_RIGHT'}
    environment=config.get('environment',{})
    if set(environment)-allowed or any(not isinstance(v,str) or len(v)>512 or '\x00' in v for v in environment.values()):raise ValueError('Configuración de audio inválida')
    os.environ.update(environment)
    return services


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('uri',nargs='?',default='hbg-controller://open')
    parser.add_argument('--no-browser',action='store_true')
    args=parser.parse_args()
    routes={'hbg-controller://open':'guitar',**{f'harmonic-lab://{key}':key for key in ('guitar','audio','body','all')}}
    destination=routes.get(args.uri.rstrip('/'))
    if destination is None:
        parser.error('Destino no admitido')
    panel=Path(os.environ.get('HBG_PANEL_DIR',str(Path.home()/'.local/share/hbg-cyberbrick/panel')))
    state=Path.home()/'.local/state/harmonic-lab';state.mkdir(parents=True,exist_ok=True)
    services=configuration(panel)
    with (state/'launcher.lock').open('a') as lock:
        deadline=time.monotonic()+15
        while True:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
            except BlockingIOError:
                if time.monotonic()>=deadline:raise RuntimeError('Otra apertura del controlador sigue pendiente')
                time.sleep(.1)
        results={}
        chosen=('guitar','audio','body') if destination=='all' else (destination,)
        for name in chosen:
            if not services[name]:
                results[name]={'status':'not-selected'}
                continue
            try:results[name]={'status':ensure_panel(panel) if name=='guitar' else ensure_component(name)}
            except Exception as exc:results[name]={'status':'unavailable','message':str(exc)[:250]}
        target={'guitar':URL,'audio':'http://localhost:5050/','body':'http://localhost:8765/','all':'https://compaii.dmn.homes/harmonic_lab'}[destination]
        failed=any(v['status']=='unavailable' for v in results.values())
        if not args.no_browser:subprocess.run(['xdg-open',target],check=True,timeout=5)
        (state/'launch-current.json').write_text(json.dumps({'components':results,'url':target,'board_opened':False})+'\n')
        if failed:raise RuntimeError('Algunos instrumentos no pudieron iniciar; los demás se conservaron. Consultá el registro del laboratorio.')
    print('Controlador disponible')


if __name__=='__main__':main()
