"""Named Linux camera inventory. Query capabilities; never start streaming/model work."""
from pathlib import Path
import hashlib
import os
import struct
import sys


def query_capabilities(path):
    import fcntl
    buffer=bytearray(104)  # struct v4l2_capability; VIDIOC_QUERYCAP
    descriptor=os.open(path,os.O_RDONLY|os.O_NONBLOCK)
    try:fcntl.ioctl(descriptor,0x80685600,buffer,True)
    finally:os.close(descriptor)
    driver,card,bus,version,capabilities,device_caps,*_=struct.unpack('=16s32s32s6I',buffer)
    flags=device_caps if capabilities&0x80000000 else capabilities
    return {'name':card.split(b'\0')[0].decode('utf8',errors='replace'),'capture':bool(flags&(0x1|0x1000))}


class CameraDevices:
    def __init__(self,*,sys_root='/sys/class/video4linux',dev_root='/dev',platform=None,probe=query_capabilities):
        self.sys_root=Path(sys_root);self.dev_root=Path(dev_root);self.platform=platform or sys.platform;self.probe=probe

    def _entries(self):
        if not self.platform.startswith('linux'):return []
        aliases={}
        # A by-id alias is preferred; by-path identifies the physical port when no serial exists.
        for group in ('by-id','by-path'):
            for alias in sorted((self.dev_root/'v4l'/group).glob('*')):
                if alias.is_symlink():aliases.setdefault(str(alias.resolve()),str(alias))
        rows=[]
        for entry in sorted(self.sys_root.glob('video*'),key=lambda p:int(p.name[5:]) if p.name[5:].isdigit() else 100000):
            if not entry.name[5:].isdigit():continue
            index=int(entry.name[5:]);device=self.dev_root/entry.name
            try:name=(entry/'name').read_text().strip()
            except OSError:continue  # Hot-unplug during enumeration.
            reason=None
            try:
                capabilities=self.probe(device)
                if not capabilities['capture']:continue  # Metadata/output nodes are not cameras.
                name=capabilities['name'] or name
            except FileNotFoundError:continue
            except PermissionError:
                # Without capabilities, do not advertise secondary metadata nodes as usable.
                try:
                    if (entry/'index').read_text().strip()!='0':continue
                except OSError:continue
                reason='Sin permiso para consultar esta cámara.'
            except OSError:continue
            path=aliases.get(str(device.resolve()),str(device))
            stable=path if path!=str(device) else str(entry.resolve())
            identifier='cam-'+hashlib.sha256(stable.encode()).hexdigest()[:32]
            if index>32:reason='Índice fuera del rango admitido por este laboratorio.'
            rows.append({'id':identifier,'label':name,'index':index,'available':reason is None,'reason':reason,'_path':path})
        return rows

    def snapshot(self):
        return {'supported':self.platform.startswith('linux'),'cameras':[{k:v for k,v in row.items() if not k.startswith('_')} for row in self._entries()],
                'scope':'laboratory_host','streaming_started':False}

    def resolve(self,identifier):
        row=next((row for row in self._entries() if row['id']==identifier),None)
        if row is None:raise ValueError('La cámara elegida ya no está conectada. Actualizá cámaras y elegila de nuevo.')
        if not row['available']:raise ValueError(row['reason'])
        return row
