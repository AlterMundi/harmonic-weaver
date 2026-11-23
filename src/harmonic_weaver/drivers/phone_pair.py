"""Phone IMU -> real Weaver sources. No destination gains, audio or browser DSP."""
from __future__ import annotations

from collections import deque
import json
import math
import re
import secrets
import time
from importlib.resources import files

from harmonic_weaver.contract_codec import contract_id_from_manifest, validate_manifest

INVALID = (0.0, 'invalid', 0.0)
FIELDS = ('yaw', 'pitch', 'roll', 'ax', 'ay', 'az')


def source_manifest(role):
    if role not in ('a', 'b', 'pair'):
        raise ValueError('Unknown phone source role')
    resource = files(__package__).joinpath(f'phone_{role}.contract.json')
    manifest = json.loads(resource.read_text())
    golden = files(__package__).joinpath(f'phone_{role}.contract.golden').read_text().strip()
    validate_manifest(manifest)
    if manifest['contract_id'] != golden or contract_id_from_manifest(manifest) != golden:
        raise ValueError('Phone source contract digest mismatch')
    return manifest


class PhonePairSource:
    """Three source-domain contracts, independent role clocks, bounded histories.

    Browser clocks are not comparable across phones. Derivation uses one native
    receiver clock and reports that explicitly. Unknown/flat support is invalid,
    never invented correlation. The scene owns all sound mapping and smoothing.
    """
    def __init__(self, engine, *, clock=time.monotonic):
        self.engine, self.clock = engine, clock
        self.rows = {}
        self.closed = deque(maxlen=64)
        self.sources = {}
        self.paused = False
        self.pair_state = 'waiting'
        self.accepted = 0
        self.expired = set()
        for role in ('a', 'b', 'pair'):
            manifest = source_manifest(role)
            contract = engine.install_source_manifest(manifest)
            stream = secrets.token_hex(8)
            self.sources[role] = {'manifest': manifest, 'contract': contract, 'stream': stream, 'seq': 0, 'emitted': clock()}
            if not engine.source_hello('phone-' + role, stream, contract):
                raise RuntimeError('Weaver rejected the phone source handshake')

    def _emit(self, role, values):
        source = self.sources[role]
        if self.clock() - source['emitted'] > 1.0:
            self.engine.source_hello('phone-' + role, source['stream'], source['contract'])
        source['seq'] += 1
        if self.paused:
            values = {name: INVALID for name in values}
        result = self.engine.ingest_source_frame('phone-' + role, source['stream'], source['contract'], source['seq'], values)
        if not result:
            raise RuntimeError('Weaver rejected the installed phone source tuple')
        source['emitted'] = self.clock()
        return result

    def fresh(self, role):
        row = self.rows.get(role)
        return bool(row and row['arrival'] is not None and 0 <= self.clock() - row['arrival'] <= 1.0)

    def _history(self, role):
        history = self.rows.get(role, {}).get('history', deque())
        while history and history[0][0] < self.clock() - 2.0:
            history.popleft()
        return history

    def sway(self, role):
        history = self._history(role)
        return math.sqrt(sum(value**2 for _, value in history) / len(history)) if self.fresh(role) and history else 0.0

    @staticmethod
    def _at(history, t):
        for index, (when, value) in enumerate(history):
            if abs(when - t) < 1e-8:
                return value
            if when > t:
                if index == 0:
                    return None
                before, low = history[index-1]
                return None if when - before > .35 else low + (value-low) * (t-before) / (when-before)
        return None

    def relation(self):
        if not self.fresh('a') or not self.fresh('b'):
            return {'state': 'waiting', 'value': None, 'samples': 0}
        a, b = list(self._history('a')), list(self._history('b'))
        first = math.ceil((max(a[0][0], b[0][0])-1e-9) / .1)
        last = math.floor((min(a[-1][0], b[-1][0])+1e-9) / .1)
        pairs = [(self._at(a, i*.1), self._at(b, i*.1)) for i in range(first, last+1)]
        pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
        if len(pairs) < 6:
            return {'state': 'insufficient', 'value': None, 'samples': len(pairs)}
        x, y = zip(*pairs)
        mx, my = sum(x)/len(x), sum(y)/len(y)
        vx, vy = sum((v-mx)**2 for v in x), sum((v-my)**2 for v in y)
        if vx < 1e-9 or vy < 1e-9:
            return {'state': 'flat', 'value': None, 'samples': len(pairs)}
        value = sum((a-mx)*(b-my) for a, b in pairs) / math.sqrt(vx*vy)
        return {'state': 'observed', 'value': max(0.0, min(1.0, value)), 'samples': len(pairs)}

    def _emit_role(self, role):
        row = self.rows.get(role)
        if self.fresh(role):
            values = {key: (row[key], 'observed', 1.0) for key in FIELDS}
            values['sway_mps2'] = (self.sway(role), 'observed', 1.0)
        else:
            values = {key: INVALID for key in (*FIELDS, 'sway_mps2')}
        return self._emit(role, values)

    def _emit_pair(self):
        relation = self.relation()
        self.pair_state = relation['state']
        both = self.fresh('a') and self.fresh('b')
        energy = (self.sway('a') + self.sway('b')) / 2
        return self._emit('pair', {
            'synchrony': (relation['value'], 'observed', 1.0) if relation['state'] == 'observed' else INVALID,
            'energy_mps2': (energy, 'observed', 1.0) if both else INVALID,
        })

    def consume(self, frame):
        if not isinstance(frame, dict) or frame.get('device') not in ('A', 'B'):
            raise ValueError('Select phone A or B')
        role = frame['device'].lower()
        for key in FIELDS:
            value = frame.get(key)
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError('Missing finite phone reading: ' + key)
            limit = 360 if key == 'pitch' else 180 if key in ('yaw', 'roll') else 200
            if abs(value) > limit:
                raise ValueError('Phone reading outside declared range: ' + key)
        stream, seq = frame.get('stream'), frame.get('seq')
        if not isinstance(stream, str) or not re.fullmatch(r'[A-Za-z0-9-]{1,64}', stream) or type(seq) is not int or seq < 0:
            raise ValueError('Invalid phone stream or sequence')
        if (role, stream) in self.closed:
            raise ValueError('Sending stream closed; Stop and Start again')
        old = self.rows.get(role)
        if old and old['stream'] == stream and seq <= old['seq']:
            raise ValueError('Duplicate or out-of-order phone reading')
        if old and old['stream'] != stream and self.fresh(role):
            raise ValueError('This phone role is already connected')
        history = old['history'] if old and old['stream'] == stream and self.fresh(role) else deque(maxlen=128)
        if old and old['stream'] != stream:
            for changed in (role, 'pair'):
                source = self.sources[changed]
                source['stream'], source['seq'] = secrets.token_hex(8), 0
                self.engine.source_hello('phone-' + changed, source['stream'], source['contract'])
        history.append((self.clock(), math.hypot(frame['ax'], frame['ay'], frame['az'])))
        self.rows[role] = {key: float(frame[key]) for key in FIELDS} | {'stream': stream, 'seq': seq, 'arrival': self.clock(), 'history': history}
        self.expired.discard(role)
        self.accepted += 1
        self._emit_role(role)
        self._emit_pair()

    def stop(self, role, stream):
        role = role.lower()
        row = self.rows.get(role)
        if row and row['stream'] == stream:
            self.closed.append((role, stream))
            row['arrival'] = None
            row['history'].clear()
            self.expired.add(role)
            self._emit_role(role)
            self._emit_pair()

    def expire(self):
        changed = False
        for role in tuple(self.rows):
            if not self.fresh(role) and role not in self.expired:
                self.expired.add(role)
                self._emit_role(role)
                changed = True
        if changed:
            self._emit_pair()

    def pause(self, value):
        self.paused = bool(value)
        for role in ('a', 'b'):
            self._emit_role(role)
        self._emit_pair()

    def snapshot(self):
        self.expire()
        devices = {}
        for role in ('a', 'b'):
            row = self.rows.get(role, {})
            online = self.fresh(role)
            devices[role.upper()] = {'online': online, 'age_s': None if row.get('arrival') is None else max(0, self.clock()-row['arrival']), 'sway': self.sway(role), 'recent_frames': sum(t >= self.clock()-1 for t, _ in self._history(role)), **{key: row.get(key) if online else None for key in FIELDS}}
        return {'devices': devices, 'relation': self.relation(), 'paused': self.paused, 'accepted': self.accepted, 'timing': 'One native receiver clock; 100ms resampling; no inferred position or physiology.'}

    def close(self):
        for role, row in list(self.rows.items()):
            self.stop(role, row['stream'])
