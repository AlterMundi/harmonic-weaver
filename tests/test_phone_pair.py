"""Real Weaver engine/contract and native Shaper checks; no device is opened."""
import json
import math
from pathlib import Path
import socket
import time
import pytest

from harmonic_weaver.contract_codec import contract_id_from_manifest, decode_bundle
from harmonic_weaver.drivers.phone_pair import PhonePairSource, source_manifest
from harmonic_weaver.engine import WeaverEngine
from harmonic_weaver.phone_pair import PairSession, PairTransport, create_pair_app

ROOT = Path(__file__).resolve().parents[1]
SHAPER = ROOT.parent/'harmonic-shaper'
BEACON = ROOT.parent/'beacon-spatial'


def frame(device='A', seq=1, **kw):
    return {'device': device, 'stream': 'fixture-'+device, 'seq': seq,
            'yaw': 0, 'pitch': 0, 'roll': 0, 'ax': 0, 'ay': 0, 'az': 0, **kw}


class Clock:
    now = 100.0
    def seconds(self): return self.now
    def us(self): return int(self.now*1e6)


@pytest.fixture
def source():
    clock = Clock(); engine = WeaverEngine(clock_us=clock.us)
    driver = PhonePairSource(engine, clock=clock.seconds)
    yield clock, engine, driver
    driver.close(); engine.close()


def test_exact_contracts_and_zero_is_observed(source):
    clock, engine, driver = source
    for role in ['a', 'b', 'pair']:
        m = source_manifest(role)
        assert m['contract_id'] == contract_id_from_manifest(m)
        assert all('gain' not in c['name'] and 'pan' not in c['name'] for c in m['channels'])
    driver.consume(frame())
    assert engine.source_value('phone-a.az').state == 'observed'
    assert engine.source_value('phone-a.az').value == 0
    assert engine.source_value('phone-pair.synchrony').state == 'invalid'


def test_aligned_relation_and_independent_phone_freshness(source):
    clock, engine, driver = source
    for i in range(30):
        clock.now = 100+i*.1
        for d in ['A', 'B']:driver.consume(frame(d, i+1, az=2+math.sin(i*.4)))
    assert driver.relation()['value'] == pytest.approx(1)
    clock.now += .9;driver.consume(frame('A', 31, yaw=90));clock.now += .2;driver.expire();engine.tick()
    assert driver.fresh('a') and not driver.fresh('b')
    assert engine.source_value('phone-b.yaw').state == 'invalid'
    assert engine.source_value('phone-a.yaw').state == 'observed'


def test_flat_missing_and_jitter_gaps_are_not_observed_synchrony(source):
    clock, engine, driver = source
    for i in range(8):
        clock.now = 100+i*.1
        for d in ['A', 'B']:driver.consume(frame(d, i+1, az=0))
    assert driver.relation()['state'] == 'flat'
    assert engine.source_value('phone-pair.synchrony').state == 'invalid'
    for i in range(8, 11):
        clock.now += .7
        for d in ['A', 'B']:driver.consume(frame(d, i+1, az=i))
    assert driver.relation()['state'] == 'insufficient'


def test_order_conflict_closed_stream_and_new_source_epoch(source):
    clock, engine, driver = source
    driver.consume(frame())
    for f in [frame(), frame(seq=2, stream='different')]:
        with pytest.raises(ValueError):driver.consume(f)
    driver.stop('A', 'fixture-A')
    with pytest.raises(ValueError):driver.consume(frame(seq=2))
    before = driver.sources['a']['stream'];driver.consume(frame(seq=1, stream='new-person'))
    assert driver.sources['a']['stream'] != before
    assert engine.source_value('phone-a.yaw').state == 'observed'


def test_expiry_and_fresh_reconnection_reenter_weaver(source):
    clock, engine, driver = source
    driver.consume(frame());clock.now += 2;driver.expire();engine.tick()
    assert engine.source_value('phone-a.yaw').state == 'invalid'
    clock.now += 3;engine.tick();driver.consume(frame(seq=2, yaw=30))
    assert engine.source_value('phone-a.yaw').value == 30


def test_bad_payloads_never_replace_current_observation(source):
    _, engine, driver = source;driver.consume(frame())
    for kw in [{'az': float('nan')}, {'ax': 201}, {'yaw': 181}, {'seq': True}, {'stream': 'x'*65}]:
        with pytest.raises(ValueError):driver.consume(frame(seq=2, **kw) if 'seq' not in kw else frame(**kw))
    assert engine.source_value('phone-a.ax').value == 0


def test_histories_and_tombstones_are_bounded(source):
    clock, _, driver = source
    for i in range(300):
        clock.now += .01;driver.consume(frame(seq=i+1))
    assert len(driver.rows['a']['history']) <= 128
    for i in range(100):
        stream='fixture-'+str(i);driver.stop('A', driver.rows['a']['stream']);driver.consume(frame(stream=stream))
    assert len(driver.closed) == 64 and len(driver.rows) == 1


def make_session(target, clock, **kw):
    path = SHAPER/'contracts/shaper.contract.json' if target == 'shaper' else BEACON/'beacon_spatial.contract.json'
    return PairSession(target, json.loads(path.read_text()), clock=clock.seconds, clock_us=clock.us, **kw)


@pytest.mark.parametrize('target', ['beacon'])
def test_no_output_before_exact_native_handshake_and_real_scene(target):
    clock=Clock();session=make_session(target, clock)
    try:
        session.source.consume(frame())
        assert not session.transport.records
        session.synchronize('0123456789abcdef')
        for i in range(20):
            clock.now += .04;session.source.consume(frame(seq=i+2, yaw=90, az=2))
        assert session.engine.metrics['instrument_writes'] > 0
        addresses=session.transport.values
        expected='/digital/harmonic/1/envelope/15' if target=='shaper' else '/beacon/gain/1'
        assert expected in addresses
        assert all(a.startswith('/digital/') if target=='shaper' else a.startswith('/beacon/') for a in addresses)
    finally:session.close()


def test_beacon_expiry_restores_guitar_baseline_without_master_write():
    clock=Clock();baseline={f'/beacon/gain/{n}':.6 for n in range(1,14)}
    session=make_session('beacon',clock,baseline=baseline)
    try:
        session.synchronize('0123456789abcdef')
        for i in range(20):
            clock.now += .04;session.source.consume(frame(seq=i+1,az=3,yaw=90))
        assert session.transport.values['/beacon/gain/1'] != .6
        clock.now += 1.01;session.tick()
        assert session.transport.values['/beacon/gain/1'] == .6
        assert '/beacon/master' not in session.transport.values
    finally:session.close()


def test_real_udp_output_uses_native_address_and_bounded_tail():
    receiver=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);receiver.bind(('127.0.0.1',0));receiver.settimeout(1)
    clock=Clock();session=make_session('beacon',clock,endpoint=receiver.getsockname())
    try:
        session.synchronize('0123456789abcdef');session.source.consume(frame(az=2))
        packets=[decode_bundle(receiver.recv(4096)) for _ in range(3)]
        assert any(address.startswith('/beacon/') for bundle in packets for address,_ in bundle)
        for i in range(180):
            clock.now += .04;session.source.consume(frame(seq=i+2,yaw=i%120,az=2))
        assert len(session.transport.records)<=128
    finally:session.close();receiver.close()



def test_private_http_websocket_scene_and_pause():
    from fastapi.testclient import TestClient
    clock=Clock();session=make_session('beacon',clock);session.synchronize('0123456789abcdef')
    app=create_pair_app(session,room='fixture-room')
    with TestClient(app) as client:
        assert client.get('/').status_code==404
        assert client.get('/fixture-room/pair/').status_code==200
        assert client.get('/fixture-room/pair/phone').status_code==200
        with client.websocket_connect('/fixture-room/pair/imu',headers={'origin':'http://testserver'}) as ws:
            ws.send_json(frame())
            for _ in range(30):
                snapshot=client.get('/fixture-room/pair/api/status').json()
                if snapshot['devices']['A']['online']:break
                time.sleep(.01)
            assert snapshot['devices']['A']['online']
        assert not client.get('/fixture-room/pair/api/status').json()['devices']['A']['online']
        assert client.post('/fixture-room/pair/api/control',json={'action':'pause'},headers={'origin':'https://bad.invalid'}).status_code==403
        assert client.post('/fixture-room/pair/api/control',json={'action':'pause'},headers={'origin':'http://testserver'}).status_code==200
        assert session.source.paused
        # Same-origin HTTPS through a TLS terminator keeps the upstream HTTP
        # scheme; source binding must compare the actual host, not that scheme.
        assert client.post('/fixture-room/pair/api/control',json={'action':'resume'},headers={'origin':'https://testserver'}).status_code==200
        assert not session.source.paused
        assert client.post('/fixture-room/pair/api/control',content='x'*257,headers={'origin':'https://testserver'}).status_code==413


def test_native_loss_or_changed_identity_latches_gate_without_auto_resume():
    clock=Clock();identity=['engine-1']
    session=make_session('beacon',clock,native_check=lambda:identity[0],native_identity='engine-1')
    try:
        session.synchronize('0123456789abcdef');session.check_native();assert session.gated
        identity[0]='engine-2';session.check_native()
        assert not session.gated and session.source.paused
        session.source.consume(frame())
        count=session.engine.metrics['instrument_writes'];clock.now+=.1;session.tick()
        assert session.engine.metrics['instrument_writes']==count
        identity[0]='engine-1';session.check_native();assert not session.gated
    finally:session.close()


def test_occupied_listener_fails_before_any_native_join():
    import os
    import subprocess
    import sys
    blocker=socket.socket();blocker.bind(('127.0.0.1',0));blocker.listen()
    try:
        result=subprocess.run([sys.executable,'-m','harmonic_weaver.phone_pair','--target','shaper','--connect','--port',str(blocker.getsockname()[1]),'--manifest',str(SHAPER/'contracts/shaper.contract.json')],env={**os.environ,'PYTHONPATH':str(ROOT/'src')},capture_output=True,text=True,timeout=5)
        assert result.returncode!=0 and 'Address already in use' in result.stderr
        assert '/api/state' not in result.stderr
    finally:blocker.close()
