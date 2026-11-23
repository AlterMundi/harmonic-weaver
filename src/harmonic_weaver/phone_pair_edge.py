"""Private phone edge for the EXISTING laboratory's selected phone source.

The edge has no audio engine, model state, hardware access or copied human
session. All perception/routing remains in the current LaboratoryRuntime.
"""
from __future__ import annotations
import threading
from urllib.parse import urlsplit
import httpx


class LaboratoryPhoneEdge:
    target = 'shaper'
    engine = None
    stage_engine = None
    def __init__(self, url='http://127.0.0.1:8765'):
        parsed=urlsplit(url)
        if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost','::1') or parsed.username or parsed.password or parsed.path not in ('','/') or parsed.query or parsed.fragment:
            raise ValueError('Phone edge requires the existing loopback laboratory URL')
        self.url=url.rstrip('/');self.lock=threading.RLock();self.closed=False
        self.client=httpx.Client(base_url=self.url,timeout=.5,trust_env=False,follow_redirects=False)
        value=self._request('POST','activate',{})
        self.key=value['key']

    def _request(self, method, name, value=None):
        headers={'Origin':self.url}
        if hasattr(self,'key'):headers['X-Phone-Pair-Key']=self.key
        response=self.client.request(method,'/api/phone-pair/'+name,headers=headers,json=value)
        if response.status_code!=200:
            raise ValueError('The local laboratory refused phone control; verify its selected source and update. HTTP '+str(response.status_code))
        if len(response.content)>128*1024:raise ValueError('Unexpected laboratory response size')
        return response.json()

    def ingest(self, frame):
        with self.lock:self._request('POST','frame',frame)

    def stop(self, role, stream):
        with self.lock:
            try:self._request('POST','control',{'action':'stop','device':role,'stream':stream})
            except (ValueError,httpx.HTTPError):pass

    def control(self, action):
        with self.lock:return self._request('POST','control',{'action':action})

    def snapshot(self):
        with self.lock:return self._request('GET','state')

    def tick(self):
        pass  # The existing laboratory analysis tick owns perception and sound.

    def check_native(self):
        pass  # ShaperOutput already reports ACK, lease, output telemetry and errors.

    def close(self):
        with self.lock:
            if self.closed:return
            self.closed=True
            try:self._request('POST','control',{'action':'deactivate'})
            except (ValueError,httpx.HTTPError):pass
            self.client.close()
