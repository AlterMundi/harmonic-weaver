"""Wire-level regression coverage for the exclusive kinetic consonance mode."""
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


driver = load("consonance_driver", ROOT / "research/movement-consonance/consonance/driver.py")
codec = load("consonance_test_codec", driver.KIT / "osc_codec.py")


def person(frame=0, *, slot=0, focused=True, present=True):
    # Synthetic body translating smoothly, with a fixed torso scale.
    x = 0.4 + 0.06 * math.sin(frame / 4)
    kp = [(x, 0.2, 1.0)] * 17
    for i in (5, 6):
        kp[i] = (x, 0.4, 1.0)
    for i in (11, 12):
        kp[i] = (x, 0.7, 1.0)
    return dict(slot_id=slot, present=present, focused=focused,
                keypoints=kp, kp_state=[(0, 0, 0)] * 17,
                captured_at_us=1_000_000 + frame * 33_333)


def packet(p, seq, stream="a"):
    return codec.build_person_bundle(
        stream_id=stream, captured_frame_id=seq, bundle_seq=seq,
        n_persons=2, fps=30., contract_id="0" * 32,
        calibration_generation=0, calibration_state="valid",
        captured_at_us=p["captured_at_us"], processed_at_us=0,
        queued_for_send_at_us=0,
        person=dict(p, keypoints_blob=codec.pack_keypoints(p["keypoints"]),
                    kp_state_blob=codec.pack_kp_state(p["kp_state"]),
                    bbox=(0., 0., 1., 1.),
                    features_blob=codec.pack_features([0.] * codec.N_FEATURES),
                    feat_state_blob=codec.pack_feat_state([0] * codec.N_FEATURES)))


def session():
    out = driver.ShaperOut("127.0.0.1", 9001, 40.4, .03, True)
    return driver.ConsonanceSession(out)


def move(s, receiver, start=0):
    for i in range(20):
        receiver.feed(packet(person(i), start + i), i / 30)
        s.update(receiver.snapshot(i / 30))
    assert len(s.out.on) == 6


def test_wire_motion_drives_six_voices_and_overlay_matches_output():
    r, s = driver.LiveReceiver(codec), session()
    move(s, r)
    state = s.state()
    assert state["slot_id"] == 0
    assert len(state["zones"]) == 6
    assert any(abs(z["detune"]) > .01 for z in state["zones"])
    for z in state["zones"]:
        assert 40.4 * (z["n"] - .5) <= z["freq"] <= 40.4 * (z["n"] + .5)
        assert 0 <= z["gain"] <= .45
        assert abs(z["phase_deg"]) <= 45
        assert z["active"] == (7000 + z["n"] in s.out.on)


def test_unfocused_bundles_do_not_replace_or_reprocess_focused_body():
    r, s = driver.LiveReceiver(codec), session()
    move(s, r)
    hist = list(s.tracker.zones[1].hist)
    r.feed(packet(person(20, slot=1, focused=False), 20), .7)
    s.update(r.snapshot(.7))
    assert s.identity == ("a", 0)
    assert list(s.tracker.zones[1].hist) == hist
    assert len(s.out.on) == 6


def test_focus_change_and_stream_restart_clear_old_motion():
    r, s = driver.LiveReceiver(codec), session()
    move(s, r)
    r.feed(packet(person(20, focused=False), 20), .7)
    r.feed(packet(person(20, slot=1), 21), .7)
    s.update(r.snapshot(.7))
    assert s.identity == ("a", 1)
    assert not s.out.on  # First sample contains no motion yet.
    assert len(s.tracker.zones[1].hist) == 1
    r.feed(packet(person(), 0, stream="b"), .8)
    s.update(r.snapshot(.8))
    assert s.identity == ("b", 0)
    assert len(r.snapshot(.8)["persons"]) == 1
    assert len(s.tracker.zones[1].hist) == 1


def test_out_of_order_packet_cannot_mutate_cached_person():
    r = driver.LiveReceiver(codec)
    r.feed(packet(person(5), 5), 1.)
    r.feed(packet(person(2, present=False), 2), 1.1)
    assert r.snapshot(1.1)["persons"][0]["captured_at_us"] == person(5)["captured_at_us"]


def test_silence_expires_even_without_new_frames():
    r, s = driver.LiveReceiver(codec), session()
    move(s, r)
    s.update(r.snapshot(3.))
    assert not s.out.on
    assert s.state()["zones"] == []


def test_tombstone_releases_immediately():
    r, s = driver.LiveReceiver(codec), session()
    move(s, r)
    r.feed(packet(person(20, present=False), 20), .7)
    s.update(r.snapshot(.7))
    assert not s.out.on


def test_shutdown_releases_only_owned_voices():
    out = driver.ShaperOut("127.0.0.1", 9001, 40.4, .03, True)
    messages = []
    out._send = lambda addr, args: messages.append((addr, args))
    out.update(1, 40.4, .2)
    out.update(9, 360., .2)
    messages.clear()
    out.panic()
    assert set((addr, args[0]) for addr, args in messages) == {
        ("/beacon/voice/off", 7001), ("/beacon/voice/off", 7009)}
    assert not out.on


def test_state_file_written_atomically(tmp_path):
    path = tmp_path / "state.json"
    s = session()
    driver.write_state(path, s.state())
    assert json.loads(path.read_text())["zones"] == []
    assert not path.with_suffix(".tmp").exists()


def test_stationary_body_is_silent():
    s = session()
    messages = []
    s.out._send = lambda addr, args: messages.append((addr, args))
    for i in range(100):
        p = person(0)
        p["captured_at_us"] += i * 33_333
        s.update(dict(stream_id="still", persons=[p]))
    assert not s.out.on
    assert not messages
    assert all(z["gain"] == 0 for z in s.state()["zones"])


def test_movement_modulates_sustained_voices_without_note_ons():
    s, r = session(), driver.LiveReceiver(codec)
    messages = []
    s.out._send = lambda addr, args: messages.append((addr, args))
    move(s, r)
    assert any(abs(z["phase_deg"]) > .01 for z in s.state()["zones"])
    assert any(z["gain"] > 0 for z in s.state()["zones"])
    before = dict(s.sustained)
    p = person(20)
    p["kp_state"] = [(2, 0, 0)] * 17
    s.update(dict(stream_id="a", persons=[p]))
    assert not s.out.on
    assert all(z["gain"] == 0 for z in s.state()["zones"])


def test_six_voice_anatomical_order_and_rest_frequencies():
    s = session()
    p = person()
    # Give every joint a distinct coordinate to detect crossed assignments.
    p["keypoints"] = [(i / 20, i / 30, 1.) for i in range(17)]
    s.update(dict(stream_id="mapping", persons=[p]))
    expected = [("hips", 11, 12), ("shoulders", 5, 6),
                ("knees", 13, 14), ("elbows", 7, 8),
                ("ankles", 15, 16), ("wrists", 9, 10)]
    assert set(s.tracker.zones) == set(range(1, 7))
    assert not s.out.on
    for z, (name, left, right) in zip(s.state()["zones"], expected):
        assert s.tracker.zones[z["n"]].name == name
        index = (left + right) / 2 if name in ("hips", "shoulders") else left
        assert abs(z["x"] - index / 20) < 1e-10
        assert abs(z["y"] - index / 30) < 1e-10
        assert z["freq"] == 40.4 * z["n"]


def test_only_moving_wrist_sounds_and_stops_on_next_stationary_sample():
    s = session()
    p = person(0)
    s.update(dict(stream_id="raw", persons=[p]))
    p = person(0)
    p["captured_at_us"] += 33_333
    p["keypoints"][9] = (.5, .2, 1.)
    s.update(dict(stream_id="raw", persons=[p]))
    assert s.out.on == {7006}
    assert s.sustained[6][1] > 0
    p["captured_at_us"] += 33_333
    s.update(dict(stream_id="raw", persons=[p]))
    assert not s.out.on
    assert s.sustained[6][1] == 0


def test_raw_pitch_gain_phase_have_no_snap_or_output_smoothing():
    r, s = driver.LiveReceiver(codec), session()
    move(s, r)
    assert s.snap == 0
    for n, z in s.tracker.zones.items():
        assert z.d_eff == z.d_raw
        assert s.sustained[n] == (40.4 * (n + z.d_raw / 2),
                                  .45 * z.gain, 45 * z.d_raw)
