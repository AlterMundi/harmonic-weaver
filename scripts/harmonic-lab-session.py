#!/usr/bin/env python3
"""Foreground composition of existing Guitar, Spatializer and optional body lab."""
import argparse
import fcntl
import json
import os
import platform
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
from urllib.request import build_opener, ProxyHandler

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from rehearsal.support import beacon_snapshot
from harmonic_weaver.contract_codec import contract_id_from_manifest


def alive(url):
    try:
        with build_opener(ProxyHandler({})).open(url,timeout=.5) as response:
            return response.status==200
    except Exception:
        return False


class Stack:
    def __init__(self,args):
        self.args=args;self.children={};self.borrowed=[];self.stop=threading.Event()
        self.state=args.state_dir.expanduser();self.state.mkdir(parents=True,exist_ok=True)
        self.lock=open(self.state/'session.lock','a')
        try:fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except Exception:
            self.lock.close()
            raise
        # Reuse the Spatializer's bounded latest-tail logger for all owned children.
        sys.path.insert(0,str(args.spatializer_dir))
        from bounded_log import copy_tail
        self.copy_tail=copy_tail
        self.started=time.monotonic()

    def record(self,phase,**extra):
        data={'phase':phase,'owned':{k:p.pid for k,p in self.children.items()},
              'borrowed':self.borrowed,'hours_limit':self.args.hours,
              'elapsed_s':round(time.monotonic()-self.started,1),**extra}
        pending=self.state/'current.pending';pending.write_text(json.dumps(data,indent=2)+'\n');pending.replace(self.state/'current.json')

    def start(self,name,command,cwd,env=None):
        child=subprocess.Popen(command,cwd=cwd,env=env,start_new_session=True,
                               stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        self.children[name]=child
        threading.Thread(target=self.copy_tail,args=(child.stdout,self.state/(name+'.log')),daemon=True).start()
        self.record('starting')

    def wait_ready(self,name,probe,seconds):
        deadline=time.monotonic()+seconds
        while not self.stop.is_set():
            child=self.children.get(name)
            if child and child.poll() is not None:
                raise RuntimeError(name+' exited; see its bounded session log')
            if probe():return
            if time.monotonic()>deadline:raise RuntimeError(name+' did not become ready')
            self.stop.wait(.25)
        raise RuntimeError('Startup interrupted')

    def audio_ready(self):
        if not alive('http://127.0.0.1:5050/'):return False
        contract=json.loads((self.args.spatializer_dir/'beacon_spatial.contract.json').read_text())
        try:
            snapshot=beacon_snapshot(host='127.0.0.1',port=57120,expected_contract_id=contract_id_from_manifest(contract),timeout=.6)
            if platform.system()=='Darwin':
                native=json.loads((self.state/'spatializer/native.json').read_text())
                if native.get('phase')!='processes_started' or native.get('source')!='live':return False
                if native.get('input_device')!=os.environ.get('BEACON_INPUT_DEVICE') or native.get('output_device')!=os.environ.get('BEACON_OUTPUT_DEVICE'):return False
                snapshot['coreaudio_configuration']=native
            else:
                subprocess.run([sys.executable,str(self.args.spatializer_dir/'beacon_routes.py'),'--output','r24','--check'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=4)
            self.audio_snapshot=snapshot
            return True
        except Exception:return False

    def run(self):
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',BEACON_OUTPUT_TARGET='r24',
                 BEACON_LOG_DIR=str(self.state/'spatializer'))
        controller='http://127.0.0.1:18879/state'
        if self.args.no_guitar_controller:pass
        elif alive(controller):self.borrowed.append('guitar')
        else:
            self.start('guitar',[str(self.args.guitar_panel_dir/'run-panel.sh')],self.args.guitar_panel_dir,env)
            self.wait_ready('guitar',lambda:alive(controller),10)
        if alive('http://127.0.0.1:5050/'):
            self.borrowed.append('spatializer')
            if not self.audio_ready():raise RuntimeError('Existing Spatializer does not match the requested R24 live path; preserved')
        else:
            self.start('spatializer',[str(self.args.spatializer_dir/'start-beacon.sh'),'--live','--no-https'],self.args.spatializer_dir,env)
            self.wait_ready('spatializer',self.audio_ready,40)
        if self.args.with_weaver:
            if alive('http://127.0.0.1:8765/'):self.borrowed.append('weaver')
            else:
                native=platform.system()=='Darwin'
                device=os.environ.get('HARMONIC_SHAPER_DEVICE',os.environ.get('BEACON_OUTPUT_DEVICE','')) if native else 'R24 Analog Stereo'
                if not device:raise ValueError('Select the native Shaper output device')
                self.start('weaver',[str(ROOT/'scripts/start-laboratory.sh'),'--audio-backend','native' if native else 'jack','--device',device,'--tracking-device','auto' if native else 'cpu'],ROOT,env)
                self.wait_ready('weaver',lambda:alive('http://127.0.0.1:8765/'),180)
        self.record('ready',audio=self.audio_snapshot,
                    entry={'spatializer':'http://localhost:5050','guitar':None if self.args.no_guitar_controller else 'http://localhost:18879',
                           'weaver':'http://localhost:8765' if self.args.with_weaver else None})
        print('Harmonic Lab iniciado con CoreAudio seleccionado; verificar audio y escucha en esta Mac.' if platform.system()=='Darwin' else 'Harmonic Lab listo: guitarra R24 canal1 → Spatializer → salida R24.',flush=True)
        print('Spatializer: http://localhost:5050'+('' if self.args.no_guitar_controller else ' · Guitarra: http://localhost:18879'),flush=True)
        if self.args.with_weaver:print('Weaver/HarMoCAP: http://localhost:8765 · elegir fuente no activa la cámara automáticamente.',flush=True)
        print('Ctrl+C cierra sólo los componentes iniciados aquí; los que ya estaban abiertos se conservan.',flush=True)
        while not self.stop.wait(.5):
            for name,child in self.children.items():
                if child.poll() is not None:raise RuntimeError(name+' exited during the session')
            if time.monotonic()-self.started>=self.args.hours*3600:break

    def close(self):
        # Every PID below owns a process group created by this exact invocation.
        for child in reversed(list(self.children.values())):
            try:os.killpg(child.pid,signal.SIGTERM)
            except ProcessLookupError:pass
        deadline=time.monotonic()+8
        for child in self.children.values():
            try:child.wait(timeout=max(.01,deadline-time.monotonic()))
            except subprocess.TimeoutExpired:
                try:os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                child.wait(timeout=2)
        self.lock.close()
        self.children_exit={name:child.returncode for name,child in self.children.items()}


def main():
    parser=argparse.ArgumentParser(description='Start the existing Guitar + R24 Spatializer together; optional Weaver/HarMoCAP UI')
    parser.add_argument('--spatializer-dir',type=Path,default=ROOT.parent/'beacon-spatial')
    parser.add_argument('--guitar-panel-dir',type=Path,default=Path.home()/'.local/share/hbg-cyberbrick/panel')
    parser.add_argument('--state-dir',type=Path,default=Path.home()/'.local/state/harmonic-lab')
    parser.add_argument('--no-guitar-controller',action='store_true',help='run audio/body software without requiring a CyberBrick motor controller')
    parser.add_argument('--with-weaver',action='store_true',help='also start the usual Weaver/Shaper laboratory; camera remains an explicit UI choice')
    parser.add_argument('--hours',type=float,default=8)
    args=parser.parse_args()
    if not 0<args.hours<=8:parser.error('--hours must be greater than0 and at most8')
    for p in (args.spatializer_dir/'start-beacon.sh',args.spatializer_dir/'bounded_log.py',args.spatializer_dir/'beacon_routes.py'):
        if not p.is_file():parser.error('Update the existing Spatializer checkout first: missing '+p.name)
    stack=Stack(args)
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:stack.stop.set())
    failure=None
    try:
        stack.run()
    except Exception as exc:
        failure=str(exc)
        raise
    finally:
        stack.close()
        stack.record('failed' if failure else 'stopped',error=failure,exit_codes=stack.children_exit)

if __name__=='__main__':main()
