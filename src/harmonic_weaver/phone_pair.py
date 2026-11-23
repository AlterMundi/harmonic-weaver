"""Local phone perception -> Weaver -> existing Shaper or live-guitar Spatializer.

No renderer, device, motor, camera or source process is started here. --connect
explicitly joins an already running, contract-compatible native instrument.
"""
from __future__ import annotations
import argparse
from collections import deque
import json
import secrets
import socket
import threading
import time
from pathlib import Path
from fastapi import Request, WebSocket

from harmonic_weaver.contract_codec import contract_id_from_manifest, encode_message, validate_manifest
from harmonic_weaver.drivers.phone_pair import PhonePairSource
from harmonic_weaver.engine import WeaverEngine
from harmonic_weaver.phone_pair_scene import build_scene


class PairTransport:
    """Native output seam; bounded diagnostic tail; never logs participant frames."""
    def __init__(self, endpoint=None):
        self.endpoint = endpoint
        self.records = deque(maxlen=128)
        self.values = {}
        self.lock = threading.RLock()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) if endpoint else None

    def send_capability(self, record):
        if self.socket:
            self.socket.sendto(encode_message(record.address, [record.value]), self.endpoint)
        with self.lock:
            self.records.append(record)
            self.values[record.address] = record.value

    def invoke_action(self, record):
        raise ValueError('Phone Pair declares only explicit native capability writes')

    def close(self):
        if self.socket:
            self.socket.close()


class PairSession:
    def __init__(self, target, manifest, *, baseline=None, endpoint=None, clock=time.monotonic, clock_us=None, native_check=None, native_identity=None):
        if target != 'beacon':
            raise ValueError('Shaper phones belong to the current laboratory and its ShaperOutput')
        self.target, self.clock = target, clock
        self.lock = threading.RLock()
        self.transport = PairTransport(endpoint)
        self.engine = WeaverEngine(transport=self.transport, **({'clock_us': clock_us} if clock_us else {}))
        self.stage_engine = self.engine
        self.source = PhonePairSource(self.engine, clock=clock)
        self.manifest = manifest
        validate_manifest(manifest)
        self.scene, profile = build_scene(target, manifest, baseline)
        self.contract = self.engine.install_instrument_manifest(manifest, profile)
        self.instrument = manifest['instrument']['instrument_id']
        self.connected = endpoint is not None
        self.gated = False
        self.closed = False
        self.native_check, self.native_identity = native_check, native_identity
        self.native_error = None

    def synchronize(self, stream):
        if not self.engine.instrument_hello(self.instrument, stream, self.contract):
            raise ValueError('Native instrument hello rejected')
        if not self.engine.instrument_sync_complete(self.instrument, stream, self.contract):
            raise ValueError('Native instrument state synchronization rejected')
        self.engine.upsert_scene(self.scene, self.engine.stage_revision)
        self.engine.switch_scene(self.scene['scene_id'], 1, self.engine.stage_revision)
        self.gated = True

    def tick(self):
        with self.lock:
            self.source.expire()
            self.engine.tick()

    def ingest(self, frame):
        with self.lock:self.source.consume(frame)

    def stop(self, role, stream):
        with self.lock:self.source.stop(role, stream)

    def control(self, action):
        with self.lock:
            if action=='pause':self.source.pause(True)
            elif action=='resume':
                if not self.gated:raise ValueError(self.native_error or 'Verify the native instrument first')
                if self.engine.panic_active:self.engine.clear_panic(self.engine.panic_generation,self.scene['scene_id'],1)
                self.source.pause(False)
            elif action=='cut':
                self.source.pause(True);self.engine.trigger_panic('Explicit phone-pair modulation cut')
            else:raise ValueError('Unknown phone action')

    def snapshot(self):
        with self.lock:
            return {**self.source.snapshot(), 'target': self.target, 'native_connected': self.connected,
                    'gated': self.gated, 'panic': self.engine.panic_active, 'native_error': self.native_error,
                    'metrics': dict(self.engine.metrics), 'outputs': dict(self.transport.values)}

    def check_native(self):
        if not self.native_check or not self.gated:
            return
        try:
            if self.native_check() != self.native_identity:
                raise ValueError('Native instrument restarted')
        except Exception:
            with self.lock:
                if self.closed:
                    return
                self.source.pause(True)
                self.engine.instrument_disconnected(self.instrument, reason='Native state/stream revalidation failed')
                self.gated = False
                self.native_error = 'El motor dejó de responder o cambió de instancia. Reiniciá el receptor para verificarlo de nuevo.'

    def close(self):
        with self.lock:
            if self.closed:
                return
            self.closed = True
            self.source.close()
            self.engine.tick()
            self.engine.close()
            self.transport.close()


def create_pair_app(session, *, room=None):
    """One private demo capability, same-origin WebSockets, no credential store.

    All routes (including the ordinary Stage API) live under the room prefix.
    Keep its URL private. This is a native rehearsal capability, not Home login.
    """
    import asyncio
    from contextlib import asynccontextmanager
    from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
    from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
    from harmonic_weaver.server import create_app
    room = room or secrets.token_urlsafe(24)
    if not room or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in room):
        raise ValueError('Invalid private room capability')
    static = Path(__file__).with_name('static')
    inner = create_app(session.stage_engine) if session.stage_engine else None

    @asynccontextmanager
    async def lifespan(app):
        async def tick():
            while True:
                await asyncio.to_thread(session.tick)
                await asyncio.sleep(.02)
        task = asyncio.create_task(tick())
        async def health():
            while True:
                await asyncio.sleep(1)
                await asyncio.to_thread(session.check_native)
        health_task = asyncio.create_task(health())
        try:
            yield
        finally:
            for owned in (task, health_task):
                owned.cancel()
                try:
                    await owned
                except asyncio.CancelledError:
                    pass
            session.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    prefix = '/'+room
    headers = {'Cache-Control': 'private, no-store', 'Referrer-Policy': 'no-referrer',
               'Permissions-Policy': 'accelerometer=(self), gyroscope=(self), magnetometer=(self), camera=(), microphone=()',
               'Content-Security-Policy': "default-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'self'"}

    @app.middleware('http')
    async def private_headers(request, call_next):
        response = await call_next(request)
        for key, value in headers.items():
            response.headers[key] = value
        return response

    @app.get(prefix+'/')
    async def landing():
        return RedirectResponse(prefix+'/pair/')

    @app.get(prefix+'/pair/')
    async def panel():
        return FileResponse(static/'phone_pair.html')

    @app.get(prefix+'/pair/phone')
    async def phone():
        return FileResponse(static/'phone_sender.html')

    @app.get(prefix+'/pair/{asset}')
    async def asset(asset: str):
        allow = {'phone-pair.js': 'phone_pair.js', 'phone-sender.js': 'phone_sender.js', 'phone-pair.css': 'phone_pair.css'}
        if asset not in allow:
            return JSONResponse({'error': 'Not found'}, status_code=404)
        return FileResponse(static/allow[asset])

    @app.get(prefix+'/pair/api/status')
    async def status():
        return await asyncio.to_thread(session.snapshot)

    @app.post(prefix+'/pair/api/control')
    async def control(request: Request):
        from urllib.parse import urlsplit
        origin = urlsplit(request.headers.get('origin', ''))
        if origin.netloc != request.headers.get('host') or origin.scheme not in ('http', 'https') or request.headers.get('sec-fetch-site') == 'cross-site':
            return JSONResponse({'error': 'Same origin required'}, status_code=403)
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > 256:
                return JSONResponse({'error': 'Request too large'}, status_code=413)
        try:
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError('Expected an action')
        except (ValueError, TypeError):
            return JSONResponse({'error': 'Invalid JSON action'}, status_code=400)
        try:
            await asyncio.to_thread(session.control,value.get('action'))
        except ValueError as error:
            return JSONResponse({'error':str(error)},status_code=409)
        return {'ok': True}

    @app.websocket(prefix+'/pair/imu')
    async def imu(websocket: WebSocket):
        from urllib.parse import urlsplit
        origin = urlsplit(websocket.headers.get('origin', ''))
        if origin.netloc != websocket.headers.get('host') or origin.scheme not in ('http', 'https'):
            await websocket.close(code=1008)
            return
        await websocket.accept()
        role = stream = None
        try:
            while True:
                raw = await websocket.receive_text()
                if len(raw.encode()) > 4096:
                    raise ValueError('Phone frame exceeds4KiB')
                frame = json.loads(raw)
                if not isinstance(frame, dict):
                    raise ValueError('Expected an IMU object')
                if role is not None and (frame.get('device'), frame.get('stream')) != (role, stream):
                    raise ValueError('One WebSocket owns one phone stream')
                if frame.get('stop'):
                    if role:await asyncio.to_thread(session.stop,role,stream)
                    break
                await asyncio.to_thread(session.ingest,frame)
                role, stream = frame['device'], frame['stream']
                # No HTTP request/ack roundtrip per sample, and no audio here.
        except WebSocketDisconnect:
            pass
        except (ValueError, TypeError, KeyError) as error:
            try:
                await websocket.close(code=1008, reason=str(error)[:100])
            except (RuntimeError,WebSocketDisconnect):
                pass
        finally:
            if role:
                await asyncio.to_thread(session.stop,role,stream)
            try:
                await websocket.close()
            except (RuntimeError,WebSocketDisconnect):
                pass

    # The ordinary contract Stage API remains available behind the same capability.
    if inner is not None:app.mount(prefix+'/stage', inner)
    app.state.room = room
    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=['shaper', 'beacon'], default='shaper')
    parser.add_argument('--connect', action='store_true', help='Join the existing local native instrument after a real state/contract read')
    parser.add_argument('--port', type=int, default=5053)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--lab-url', default='http://127.0.0.1:8765', help='Existing current laboratory for the Shaper target')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    sibling = root.parent/('harmonic-shaper' if args.target == 'shaper' else 'beacon-spatial')
    manifest_path = args.manifest or (sibling/'contracts/shaper.contract.json' if args.target == 'shaper' else sibling/'beacon_spatial.contract.json')
    manifest = json.loads(manifest_path.read_text()) if args.target=='beacon' else None
    # Reserve our listener before any native output/handshake; never kill owners.
    listener = socket.socket()
    listener.bind(('127.0.0.1', args.port))
    if args.target=='shaper':
        if args.connect:
            from harmonic_weaver.phone_pair_edge import LaboratoryPhoneEdge
            session=LaboratoryPhoneEdge(args.lab_url)
        else:
            from harmonic_weaver.lab.phone_pair import PhoneLaboratoryDiagnostic
            session=PhoneLaboratoryDiagnostic()
        app=create_pair_app(session)
        print('Native Pair: '+('current laboratory / ShaperOutput' if args.connect else 'SILENT diagnostic; real laboratory routing, no audio output'),flush=True)
        print(f'Private panel: http://127.0.0.1:{args.port}/{app.state.room}/pair/',flush=True)
        print('Expose only this private phone edge over HTTPS, never the whole laboratory.',flush=True)
        import uvicorn
        try:uvicorn.run(app,host='127.0.0.1',port=args.port,ws_max_size=4096,ws_max_queue=1,access_log=False,log_level='warning',proxy_headers=False,fd=listener.fileno())
        finally:session.close();listener.close()
        return
    baseline, stream, endpoint, native_check, native_identity = {}, secrets.token_hex(8), None, None, None
    if args.connect:
        from rehearsal.support import http_json, beacon_snapshot
        snapshot = beacon_snapshot(host='127.0.0.1', port=57120, expected_contract_id=contract_id_from_manifest(manifest))
        baseline, stream, endpoint = snapshot['dump']['values'], snapshot['hello']['stream_id'], ('127.0.0.1', 57120)
        def native_check():
            return beacon_snapshot(host='127.0.0.1', port=57120, expected_contract_id=contract_id_from_manifest(manifest),timeout=.5)['hello']['stream_id']
        native_identity = stream
    session = PairSession(args.target, manifest, baseline=baseline, endpoint=endpoint, native_check=native_check, native_identity=native_identity)
    session.synchronize(stream)
    app = create_pair_app(session)
    # The explicit human start owns this private capability; do not publish it.
    print('Native Pair: '+('CONNECTED '+args.target if args.connect else 'SILENT diagnostic; no native endpoint'), flush=True)
    print(f'Private panel: http://127.0.0.1:{args.port}/{app.state.room}/pair/', flush=True)
    print('Phones need a selected HTTPS route to THIS Mac listener; Home is a different receiver.', flush=True)
    import uvicorn
    try:
        uvicorn.run(app, host='127.0.0.1', port=args.port, ws_max_size=4096, access_log=False, log_level='warning', proxy_headers=False, loop='asyncio', lifespan='on', fd=listener.fileno())
    finally:
        session.close()
        listener.close()


if __name__ == '__main__':
    main()
