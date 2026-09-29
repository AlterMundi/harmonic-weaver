"""Local controls and telemetry for the isolated kinetic instrument."""
from __future__ import annotations

import copy
import json
import math
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading

NAMES = ['Caderas', 'Hombros', 'Rodillas', 'Codos', 'Tobillos', 'Muñecas']
COLORS = ['#ffb86b', '#f6d96b', '#8ede92', '#5ad7cf', '#7aa9ff', '#cf98f9']
DEFAULTS = dict(core_falloff=0.75, snap=0.0, master=1.0, trail_ms=320,
                f1=40.4, phase_depth=45.0, pluck_enabled=1, attack_ms=80, tail_ms=700, impulse_threshold=.15,
                zones={str(n): dict(sensitivity=1.0, distance=distance,
                                   speed_range=0.6, accel_range=6.0)
                       for n, distance in enumerate([0, 1, 1, 2, 2, 3], 1)})
LIMITS = dict(pluck_enabled=(0, 1), attack_ms=(10, 500), tail_ms=(50, 3000), impulse_threshold=(.01, 2), f1=(10, 220), phase_depth=(0, 180), core_falloff=(0, 3), snap=(0, 1), master=(0, 2), trail_ms=(0, 800))
ZONE_LIMITS = dict(sensitivity=(0, 8), distance=(0, 5),
                   speed_range=(0.02, 10), accel_range=(0.1, 100))


def validate_patch(current, patch):
    if not isinstance(patch, dict):
        raise ValueError('Expected settings object')
    result = copy.deepcopy(current)
    def number(key, value, limits):
        if key not in limits or isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f'Invalid parameter: {key}')
        lo, hi = limits[key]
        if not math.isfinite(value) or not lo <= value <= hi:
            raise ValueError(f'{key}: expected {lo}..{hi}')
        return value
    for key, value in patch.items():
        if key == 'zones':
            if not isinstance(value, dict):
                raise ValueError('Expected zones object')
            for n, fields in value.items():
                if n not in result['zones'] or not isinstance(fields, dict):
                    raise ValueError('Invalid zone')
                for field, val in fields.items():
                    result['zones'][n][field] = number(field, val, ZONE_LIMITS)
        else:
            result[key] = number(key, value, LIMITS)
    return result


class LiveControls:
    def __init__(self, path=None, *, snap=0.0, f1=40.4):
        self.path = Path(path) if path else None
        self.lock = threading.Lock()
        self.settings = copy.deepcopy(DEFAULTS)
        self.settings['snap'] = snap
        self.settings['f1'] = f1
        if self.path and self.path.exists():
            self.settings = validate_patch(self.settings, json.loads(self.path.read_text()))
        self.revision = 0
        self.applied_revision = -1
        self.state = dict(mode='Consonancia kinetica', zones=[], updated_at=0,
                          slot_id=None, stream_id=None, skeleton=[])
        self.server = None

    def snapshot(self):
        with self.lock:
            return copy.deepcopy(self.settings), self.revision

    def update(self, patch):
        with self.lock:
            updated = validate_patch(self.settings, patch)
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                tmp = self.path.with_suffix('.tmp')
                tmp.write_text(json.dumps(updated, indent=2))
                tmp.replace(self.path)
            self.settings = updated
            self.revision += 1
            return self.revision

    def publish(self, state, applied_revision):
        with self.lock:
            self.state = copy.deepcopy(state)
            self.applied_revision = applied_revision

    def payload(self):
        with self.lock:
            return dict(state=copy.deepcopy(self.state), settings=copy.deepcopy(self.settings),
                        revision=self.revision, applied_revision=self.applied_revision,
                        labels=NAMES, colors=COLORS)

    def start(self, port=8766):
        owner = self
        web = Path(__file__).with_name('web')
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def respond(self, status, data, content_type='application/json'):
                content = data if isinstance(data, bytes) else json.dumps(data).encode()
                self.send_response(status)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(content)

            def do_GET(self):
                if self.path == '/api/state':
                    return self.respond(200, owner.payload())
                pages = {'/': ('index.html', 'text/html; charset=utf-8'),
                         '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                         '/style.css': ('style.css', 'text/css; charset=utf-8')}
                if self.path not in pages:
                    return self.respond(404, {'error': 'Not found'})
                file, mime = pages[self.path]
                self.respond(200, (web / file).read_bytes(), mime)

            def do_POST(self):
                if self.path != '/api/settings':
                    return self.respond(404, {'error': 'Not found'})
                origin = self.headers.get('Origin')
                if origin and origin not in (f'http://localhost:{owner.server.server_port}',
                                             f'http://127.0.0.1:{owner.server.server_port}'):
                    return self.respond(403, {'error': 'Local origin required'})
                if self.headers.get_content_type() != 'application/json':
                    return self.respond(415, {'error': 'JSON required'})
                try:
                    length = int(self.headers.get('Content-Length', '0'))
                    if not 0 < length <= 16384:
                        raise ValueError('Invalid request size')
                    revision = owner.update(json.loads(self.rfile.read(length)))
                    self.respond(200, {'revision': revision})
                except (ValueError, TypeError) as exc:
                    self.respond(400, {'error': str(exc)})
                except OSError:
                    self.respond(500, {'error': 'Could not save settings'})
        self.server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True,
                         name='consonance-ui').start()
        return self.server.server_port

    def close(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
