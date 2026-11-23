"""Phone perception plugged into the current laboratory router and audio owner.

No second synthesis kernel, Shaper process, output thread or body-pose adapter.
"""
from __future__ import annotations
import math
import secrets
from dataclasses import replace
from fastapi import Request
from .contracts import FeatureFrame, MappingTerm, Preset, Route, Signal, VoiceSettings
from .routing import PreparedRoutes
from harmonic_weaver.drivers.phone_pair import PhonePairSource
from harmonic_weaver.engine import WeaverEngine


def phone_preset():
    voices, routes = [], []
    for n in range(1, 29):
        role = 'a' if n <= 10 else 'b' if n <= 20 else 'pair'
        index = n if n <= 10 else n-10 if n <= 20 else n-20
        voices.append(VoiceSettings(id=n, label=f'{role.upper()} {index}', ratio=float(n), gain=.7/math.sqrt(index)))
        terms = [MappingTerm(source='phone-pair.synchrony', weight=.16)] if role == 'pair' else [
            MappingTerm(source=f'phone-{role}.sway_mps2', input_unit='m/s2', weight=.05, offset=.09),
            MappingTerm(source=f'phone-{role}.pitch', input_unit='deg', weight=.05/90)]
        routes.append(Route(id=f'phone-gain-{n}',voice=n,target='gain',terms=terms,clamp_min=0,clamp_max=.5,smoothing_s=.08))
        if role != 'pair':
            routes.append(Route(id=f'phone-pan-{n}',voice=n,target='pan',terms=[MappingTerm(source=f'phone-{role}.yaw',input_unit='deg',weight=.6/180)],clamp_min=-.6,clamp_max=.6,smoothing_s=.08))
    return Preset(id='phone-pair-native-v1',name='Phone Pair · native laboratory',voices=voices,routes=routes,master=.7,release_ms=500)


class PhonePairController:
    def __init__(self, audio, *, clock, revision=0):
        self.audio, self.clock, self.revision = audio, clock, revision
        self.engine = WeaverEngine(clock_us=lambda:int(clock()*1e6))
        self.source = PhonePairSource(self.engine, clock=clock)
        self.preset = phone_preset()
        catalog = {}
        for role, state in self.source.sources.items():
            for channel in state['manifest']['channels']:
                key=channel['name'];catalog[f'phone-{role}.{key}']='deg' if key in ('yaw','pitch','roll') else '1' if key=='synchrony' else 'm/s2'
        self.routes = PreparedRoutes(self.preset, source_catalog=catalog)
        self.catalog = catalog
        self.key = secrets.token_urlsafe(32)
        self.features = None
        self.targets = []
        self.routing = {}
        self.panic = False
        self.submissions = 0

    def tick(self):
        now = self.clock();self.source.expire();self.engine.tick()
        signals = {}
        for name, unit in self.catalog.items():
            value = self.engine.source_value(name)
            valid = value is not None and value.state == 'observed' and not self.panic and not self.source.paused
            signals[name] = Signal(value=value.value if valid else None, unit=unit,
                                   state='observed' if valid else 'missing', reason=None if valid else 'No fresh phone observation')
        self.features = FeatureFrame(source_time_s=now,available_monotonic_s=now,person_id=None,
                                     algorithm_id='phone-imu-receiver',signals=signals,
                                     diagnostics={'clock':'native receiver monotonic; not acquisition-clock alignment','pose':False})
        self.targets, self.routing = self.routes.evaluate(self.features, now)
        if self.panic:
            self.targets = [replace(target,gain=0.,release_s=0.) for target in self.targets]
        self.audio.submit(self.targets, self.revision)
        self.submissions += 1
        return self.targets

    def control(self, action):
        if action=='pause':self.source.pause(True)
        elif action=='resume':self.panic=False;self.source.pause(False)
        elif action=='cut':self.panic=True;self.source.pause(True)
        else:raise ValueError('Unknown phone control')
        self.tick()

    def snapshot(self):
        audio = self.audio.snapshot()
        state = audio['shaper']
        outputs = {f'/laboratory/voice/{target.id}/gain':target.gain for target in self.targets}
        ack_age = state.get('last_ack_age_ms')
        connected = ack_age is not None and 0 <= ack_age < 500
        voice_frame = audio.get('voice_frame')
        audio_verified = bool(state.get('telemetry_valid') and voice_frame and
                              voice_frame.get('control_owner') == getattr(self.audio,'owner',None))
        return {**self.source.snapshot(),'target':'shaper','output_kind':'laboratory_http','native_connected':connected,
                'audio_disabled':state.get('audio_disabled',False),'audio_verified':audio_verified,
                'gated':not bool(state.get('error')),'panic':self.panic,'native_error':state.get('error'),
                'outputs':outputs,'metrics':{**self.engine.metrics,'lab_frames_submitted':self.submissions},
                'shaper':state,'voice_frame':voice_frame,
                'mapping':'The same PreparedRoutes and ShaperOutput used by HarMoCAP; no OSC listener required.'}

    def close(self):
        self.source.close();self.engine.close();self.audio.submit([],self.revision)


class SilentPhoneLaboratory:
    """Same source/routing code without opening a Shaper or sending native I/O."""
    def submit(self, targets, revision):
        pass
    def snapshot(self):
        return {'shaper':{'audio_disabled':True,'error':None,'telemetry_valid':False},'voice_frame':None}


class PhoneLaboratoryDiagnostic:
    target = 'shaper'
    stage_engine = None
    def __init__(self, *, clock=None):
        import threading,time
        self.lock=threading.RLock();self.closed=False
        self.controller=PhonePairController(SilentPhoneLaboratory(),clock=clock or time.monotonic)
        self.engine=self.controller.engine
    def ingest(self,frame):
        with self.lock:self.controller.source.consume(frame)
    def stop(self,role,stream):
        with self.lock:self.controller.source.stop(role,stream)
    def control(self,action):
        with self.lock:self.controller.control(action)
    def tick(self):
        with self.lock:self.controller.tick()
    def snapshot(self):
        with self.lock:return self.controller.snapshot()
    def check_native(self):
        pass
    def close(self):
        with self.lock:
            if self.closed:return
            self.closed=True;self.controller.close()


def mount_phone_pair_routes(app, runtime):
    """Local-only laboratory endpoint. The separate private edge exposes phones.

    Existing laboratory remains bound to loopback and is never tunnelled whole.
    An ephemeral per-activation capability owns just the phone source.
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse

    async def body(request):
        from urllib.parse import urlsplit
        origin=urlsplit(request.headers.get('origin',''))
        if origin.netloc!=request.headers.get('host') or origin.scheme not in ('http','https'):
            raise ValueError('Same origin required')
        raw=bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw)>4096:raise ValueError('Phone request exceeds4KiB')
        import json
        value=json.loads(raw)
        if not isinstance(value,dict):raise ValueError('Expected an object')
        return value

    def selected(request):
        controller=runtime.phone_pair
        key=request.headers.get('x-phone-pair-key','')
        if runtime.kind!='phones' or controller is None or not secrets.compare_digest(key,controller.key):
            raise ValueError('This phone source is no longer selected')
        return controller

    @app.post('/api/phone-pair/activate')
    async def activate(request: Request):
        try:
            await body(request)
            with runtime._lock:
                controller=runtime.open_phone_pair()
                return {'key':controller.key,'state':controller.snapshot()}
        except (ValueError,TypeError) as error:return JSONResponse({'error':str(error)},status_code=409)

    @app.get('/api/phone-pair/state')
    async def state(request: Request):
        try:
            with runtime._lock:return selected(request).snapshot()
        except ValueError as error:return JSONResponse({'error':str(error)},status_code=409)

    @app.post('/api/phone-pair/frame')
    async def frame(request: Request):
        try:
            value=await body(request)
            with runtime._lock:
                selected(request).source.consume(value)
                return {'ok':True}
        except (ValueError,TypeError,KeyError) as error:return JSONResponse({'error':str(error)},status_code=409)

    @app.post('/api/phone-pair/control')
    async def control(request: Request):
        try:
            value=await body(request)
            with runtime._lock:
                controller=selected(request)
                if value.get('action')=='stop':controller.source.stop(value['device'],value['stream'])
                elif value.get('action')=='deactivate':runtime.close_source()
                else:controller.control(value.get('action'))
                return {'ok':True}
        except (ValueError,TypeError,KeyError) as error:return JSONResponse({'error':str(error)},status_code=409)
