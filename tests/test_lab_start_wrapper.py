"""Exercise real wrappers with inert local executables; never start audio or services."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import pytest

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
SELECTORS=('WEAVER_PYTHON','SHAPER_DIR','SHAPER_PYTHON','HARMOCAP_DIR','HARMOCAP_VENV','HARMOCAP_CHECKPOINT')


def executable(path,body='#!/bin/sh\nexit 0\n'):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(body);path.chmod(0o755)


@pytest.fixture
def stack(tmp_path):
    root=tmp_path/'projects'/'weaver with spaces';(root/'scripts').mkdir(parents=True)
    for name in ('start-laboratory.sh','start-laboratory-development.sh','start-laboratory-dev.sh'):
        shutil.copy2(SCRIPTS/name,root/'scripts'/name)
    (root/'laboratory-ui/node_modules').mkdir(parents=True)
    recorder='#!/usr/bin/env python3\nimport json,os,sys\nfrom pathlib import Path\nPath(os.environ["WEAVER_START_RECORD"]).write_text(json.dumps({"argv":sys.argv[1:],"path":os.environ["PYTHONPATH"],"harmocap":os.environ["HARMOCAP_DIR"],"shaper":os.environ["SHAPER_DIR"]}))\n'
    executable(root/'.venv/bin/python',recorder)
    for repo in ('harmonic-weaver','harmonic-shaper','harmonic-shaper-lab','harmonic-shaper-dev','HarMoCAP','HarMoCAP-lab'):
        executable(root.parent/repo/'.venv/bin/python')
    (root.parent/'HarMoCAP/harmocap-m-pose-ft2.pt').write_text('local synthetic model marker')
    bindir=tmp_path/'bin';executable(bindir/'npm')
    env={k:v for k,v in os.environ.items() if k not in SELECTORS and k not in ('WEAVER_LAB_DATA_DIR','LAB_DEV_DATA_DIR')}
    env.update(PATH=str(bindir)+os.pathsep+env['PATH'],WEAVER_START_RECORD=str(tmp_path/'record.json'),WEAVER_LAB_DATA_DIR=str(tmp_path/'private dev data'))
    return root,env


def run(stack,*args,development=False,overrides=None):
    root,env=stack
    return subprocess.run([str(root/'scripts'/('start-laboratory-development.sh' if development else 'start-laboratory.sh')),*args],env={**env,**(overrides or {})},capture_output=True,text=True,timeout=10)


def test_describe_resolves_daily_without_build_or_launch(stack):
    root,env=stack
    executable(Path(env['PATH'].split(os.pathsep)[0])/'npm','#!/bin/sh\nexit 73\n')
    result=run(stack,'--describe')
    assert result.returncode==0,result.stderr
    assert str(root.parent/'harmonic-shaper') in result.stdout
    assert str(root.parent/'HarMoCAP') in result.stdout
    assert not Path(env['WEAVER_START_RECORD']).exists()


@pytest.mark.parametrize('selector',SELECTORS)
def test_explicit_missing_selection_never_falls_back(stack,selector):
    root,env=stack;missing=root.parent/'explicit missing selection'
    result=run(stack,'--describe',overrides={selector:str(missing)})
    assert result.returncode==1 and str(missing) in result.stderr
    assert not Path(env['WEAVER_START_RECORD']).exists()


def test_cli_selections_and_spaced_arguments_reach_the_effective_launcher(stack):
    root,env=stack;chosen=root.parent/'chosen shaper';chosen.mkdir()
    python=chosen/'custom python';executable(python)
    checkpoint=root.parent/'chosen model.pt';checkpoint.write_text('another synthetic marker')
    result=run(stack,'--shaper-dir='+str(chosen),'--shaper-python',str(python),'--checkpoint',str(checkpoint),'--device','R24 Analog Stereo','--tracking-device','cpu')
    assert result.returncode==0,result.stderr
    captured=json.loads(Path(env['WEAVER_START_RECORD']).read_text());args=captured['argv']
    assert args[:2]==['-m','harmonic_weaver.lab']
    assert args[args.index('--shaper-dir')+1]==str(chosen)
    assert args[args.index('--shaper-python')+1]==str(python)
    assert args[args.index('--checkpoint')+1]==str(checkpoint)
    assert args[args.index('--device')+1]=='R24 Analog Stereo'
    assert captured['path']==str(root/'src')
    assert captured['shaper']==str(chosen)
    assert str(chosen) in result.stdout


def test_legacy_development_alias_uses_the_same_project_and_data(stack):
    root,env=stack
    result=run(stack,'--device','R24 Analog Stereo',development=True)
    assert result.returncode==0,result.stderr
    args=json.loads(Path(env['WEAVER_START_RECORD']).read_text())['argv']
    assert args[args.index('--data-dir')+1]==env['WEAVER_LAB_DATA_DIR']
    assert args[args.index('--shaper-dir')+1]==str(root.parent/'harmonic-shaper')
    assert '--port' not in args and '--shaper-port' not in args


def test_both_legacy_spellings_share_describe_and_allow_explicit_overrides(stack):
    root,env=stack
    result=subprocess.run([str(root/'scripts/start-laboratory-dev.sh'),'--describe'],env=env,capture_output=True,text=True,timeout=10)
    alias=run(stack,'--describe',development=True)
    assert result.returncode==alias.returncode==0
    assert result.stdout==alias.stdout
    result=run(stack,'--port','17775','--data-dir','chosen data',development=True)
    assert result.returncode==0,result.stderr
    args=json.loads(Path(env['WEAVER_START_RECORD']).read_text())['argv']
    assert args[args.index('--port')+1]=='17775'
    assert args[-2:]==['--data-dir','chosen data']
