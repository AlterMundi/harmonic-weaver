#!/usr/bin/python3
"""Operator-only receiving setup; existing administrative login files are untouched."""
import json,os,pwd,subprocess,sys,re,ipaddress
from pathlib import Path
if sys.platform!='linux':raise SystemExit('Use the receiving operator route on this OS; no mutation performed')
settings=json.loads(Path(sys.argv[2]).read_text())
operator=settings['operator'];gateway=str(ipaddress.ip_address(settings['gateway_address']))
if not re.fullmatch('[a-z_][a-z0-9_-]{0,31}',operator):raise SystemExit('Invalid receiving operator')
pwd.getpwnam(operator)
pub=Path(sys.argv[1]).read_text().strip()
if not pub.startswith('ssh-ed25519 ') or len(pub)>512 or '\n' in pub:raise SystemExit('Invalid public key')
name='hblab-control';home=Path('/var/lib/harmonic-lab-ssh')
try:
 account=pwd.getpwnam(name)
 if account.pw_dir!=str(home):raise SystemExit('Existing unrelated account preserved')
except KeyError:
 subprocess.run(['useradd','--system','--create-home','--home-dir',str(home),'--shell','/bin/sh',name],check=True)
 account=pwd.getpwnam(name)
(home/'.ssh').mkdir(exist_ok=True,mode=0o700)
auth=home/'.ssh/authorized_keys'
selected='from="'+gateway+'",restrict,command="/usr/bin/sudo -H -n -u '+operator+' /usr/local/libexec/harmonic-lab-agent" '+pub+'\n'
if auth.exists() and auth.read_text()!=selected:raise SystemExit('Existing differing service key preserved')
auth.write_text(selected)
for p in (home,home/'.ssh',auth):
 os.chown(p,account.pw_uid,account.pw_gid);p.chmod(0o600 if p==auth else 0o700)
sudoers=Path('/etc/sudoers.d/harmonic-lab-control')
rule='hblab-control ALL=('+operator+') NOPASSWD: /usr/local/libexec/harmonic-lab-agent ""\n'
if sudoers.exists() and sudoers.read_text()!=rule:raise SystemExit('Existing differing grant preserved')
stage=sudoers.with_suffix('.pending');stage.write_text(rule);stage.chmod(0o440)
subprocess.run(['visudo','-cf',str(stage)],check=True,stdout=subprocess.DEVNULL)
os.replace(stage,sudoers)
Path('/usr/local/libexec').mkdir(parents=True,exist_ok=True)
subprocess.run(['install','-o','root','-g','root','-m','0755',str(Path(__file__).with_name('agent.py')),'/usr/local/libexec/harmonic-lab-agent'],check=True)
print(json.dumps({'service_user':name,'forced_agent':True,'existing_admin_files_changed':False,'devices_opened':False}))
