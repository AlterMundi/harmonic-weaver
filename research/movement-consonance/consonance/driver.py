#!/usr/bin/env python3
"""Consonance driver v1 — movement quality → harmonic-series detuning.

Research-pack prototype (movement-consonance/ADDENDUM-f1-2-grid.md):
per-zone ballistic-surprise + signed-power kinematics → d ∈ [-1,1] →
f'(n,d) = f1·(n + d/2), with a configurable snap well.

Sources:
  --source session.jsonl     replay a HarMoCAP recording (frame dicts, realtime)
  --source osc               live: listen for /harmocap/v1/* bundles on --osc-port

Output (to the shaper's optional /beacon/* slave, default 127.0.0.1:9001 —
start the shaper with --slave):
  /beacon/voice/on  voice_id freq gain n     (voice_id = 7000+n, stable)
  /beacon/voice/freq voice_id freq           (every frame, phase-continuous
                                              inside the shaper's block engine)
  /beacon/voice/off voice_id                 (zone released)

Why the slave port and not a new capability: the shaper engine ALREADY renders
per-block params.freq with continuous phase (audio_engine.py L242/L268-270),
and voice_on/voice_freq accept ARBITRARY frequency; the f1·n resets only touch
envelope-owned voices (voice_id = -10000-n). So an external driver can own
voice_ids 7000+n with continuous detune, ZERO shaper changes, no contract
bump. The native /digital detune capability stays for later (CROSS_REPORT §G).

Raw movement mode:
- No snap, gain floor, output smoothing or held sound on missing joints.
- Voice gain follows observed speed; zero speed is silent.
- Native gain/phase updates do not reassert voice_on during continuous motion.
- Live-mode gating implements stream_id reset + monotonic seq + 2s lease, but
  NOT the strict hello/calibration handshake (the kit's osc_receiver_example
  does; for exploration we accept frames directly). Flagged in the README.

Examples:
  # dry run — print per-zone d_eff/freq table at 1 Hz, no audio:
  python driver.py --source ~/Projects/HarMoCAP/examples/session_v1.jsonl --dry
  # through the shaper (shaper must run with --slave):
  python driver.py --source session.jsonl --snap 0.6
  # continuous, no snap:
  python driver.py --source osc --snap 0
  # snap well with both walls (series d=0 AND f1/2 grid |d|=1):
  python driver.py --source session.jsonl --snap 0.6 --snap-mode both
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import signal
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metrics as M  # noqa: E402

KIT = Path(os.environ.get("HARMOCAP_DIR", str(Path.home() / "Projects/HarMoCAP"))) / "harmocap-nico-kit"

VOICE_ID_BASE = 7000          # stable ids, clear of envelope ids (-10000-n)
LEASE_S = 2.0                 # kit rule 4: no data for 2 s → absent


# ──────────────────────────────────────────────────────────────────────────
# snap modes
# ──────────────────────────────────────────────────────────────────────────

def snap_apply(d_raw: float, snap: float, mode: str, theta: float) -> float:
    """Mode-aware snap.

    off    → pure continuous (d_eff = d_raw).
    series → well around d=0 (metrics.snap_map): small deviations stay on the
             natural series; escape slides continuously toward the |d|=1 wall.
    grid   → well around BOTH walls |d|=1 (the f1/2 just-interval grid) and
             d=0: deviations must exceed theta to leave a grid point, then
             slide continuously to the next one. "Expresión musical más
             conocida" (Nicolás): the walls are 3/2, 5/4, 7/4 ...
    both   → series well + extra magnetic stop at the walls (snap pulls to
             whichever grid point — 0 or ±1 — is nearer, past theta).
    """
    if mode == "off" or snap <= 0.0:
        return max(-1.0, min(1.0, d_raw))
    if mode == "series":
        return M.snap_map(d_raw, snap, theta)
    # grid / both: magnetic stops at -1, 0, +1
    thr = theta * snap
    best, best_d = d_raw, abs(d_raw)
    for wall in (-1.0, 0.0, 1.0):
        if abs(d_raw - wall) <= thr and abs(d_raw - wall) < best_d:
            best, best_d = wall, abs(d_raw - wall)
    if best in (-1.0, 0.0, 1.0):
        return best
    # escape ramp between grid points, continuous
    return M.snap_map(d_raw, snap * 0.5, theta) if mode == "both" else max(
        -1.0, min(1.0, d_raw))


# ──────────────────────────────────────────────────────────────────────────
# shaper output
# ──────────────────────────────────────────────────────────────────────────

def enc_msg(address: str, args: list) -> bytes:
    """Minimal OSC encoder (i/f only — all we need for /beacon/*).

    OSC strings are NUL-terminated THEN padded to 4 bytes — forgetting the
    NUL makes the receiver read the typetag as part of the address and
    silently drop the message to the default handler.
    """
    import struct
    def pad4(b: bytes) -> bytes:
        return b + b"\x00" * ((4 - len(b) % 4) % 4)
    def osc_str(s: str) -> bytes:
        return pad4(s.encode() + b"\x00")
    tags, payload = ",", b""
    for a in args:
        if isinstance(a, int):
            tags += "i"; payload += struct.pack(">i", a)
        elif isinstance(a, float):
            tags += "f"; payload += struct.pack(">f", a)
        else:
            raise TypeError(f"unsupported arg {a!r}")
    return osc_str(address) + osc_str(tags) + payload


class ShaperOut:
    def __init__(self, host: str, port: int, f1: float, gain_eps: float,
                 dry: bool, control_port: int = 9002):
        self.host, self.port, self.f1 = host, port, f1
        self.control_port = control_port
        self.gain_eps, self.dry = gain_eps, dry
        self.sock = None if dry else socket.socket(socket.AF_INET,
                                                   socket.SOCK_DGRAM)
        self.last_gain: dict[int, float] = {}
        self.on: set[int] = set()

    def _send(self, address: str, args: list) -> None:
        if self.dry or self.sock is None:
            return
        self.sock.sendto(enc_msg(address, args), (self.host, self.port))

    def _control(self, address: str, value: float) -> None:
        if not self.dry and self.sock is not None:
            self.sock.sendto(enc_msg(address, [float(value)]),
                             (self.host, self.control_port))

    def update(self, n: int, freq: float, gain: float, phase: float = 0.0) -> None:
        vid = VOICE_ID_BASE + n
        if vid not in self.on:
            self._send("/beacon/voice/on", [vid, float(freq), float(gain), int(n)])
            self.on.add(vid)
        else:
            self._send("/beacon/voice/freq", [vid, float(freq)])
        # Existing Shaper controls change sustained voices without recording
        # another strum or changing voice ownership.
        self._control(f"/digital/harmonic/{n}/gain", gain)
        self._control(f"/digital/harmonic/{n}/phase", phase)
        self.last_gain[n] = gain

    def release(self, n: int) -> None:
        vid = VOICE_ID_BASE + n
        if vid in self.on:
            self._send("/beacon/voice/off", [vid])
            self.on.discard(vid)
            self.last_gain.pop(n, None)

    def panic(self) -> None:
        # Release only voices owned by this mode; preserve other instruments.
        for vid in list(self.on):
            self.release(vid - VOICE_ID_BASE)
        if self.sock:
            self.sock.close()


# ──────────────────────────────────────────────────────────────────────────
# frame sources → normalized frame dicts (same schema as the jsonl recordings)
# ──────────────────────────────────────────────────────────────────────────

def frames_from_file(path: Path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


class LiveReceiver:
    """Per-slot wire cache: person bundles are atomic, not whole-body frames."""

    def __init__(self, codec):
        self.codec = codec
        self.stream_id = None
        self.last_seq = -1
        self.persons = {}

    def feed(self, data, now):
        msgs = self.codec.decode_bundle(data)
        if not msgs or msgs[0][0] != "/harmocap/v1/meta":
            return
        sid, fid, seq, count, fps, cid, cg, cs, cap_us, *_ = msgs[0][1]
        if sid != self.stream_id:
            self.stream_id, self.last_seq, self.persons = sid, -1, {}
        if seq <= self.last_seq:
            return
        self.last_seq = seq
        person = {"present": False, "focused": False,
                  "captured_at_us": cap_us, "received_at": now}
        for addr, args in msgs[1:]:
            if "/person/" not in addr:
                continue
            slot, field = addr.split("/person/", 1)[1].split("/", 1)
            person["slot_id"] = int(slot)
            if field in ("present", "focused"):
                person[field] = bool(args[0])
            elif field == "keypoints":
                person[field] = self.codec.unpack_keypoints(args[0])
            elif field == "kp_state":
                person[field] = self.codec.unpack_kp_state(args[0])
        if "slot_id" in person:
            self.persons[person["slot_id"]] = person

    def snapshot(self, now):
        return {"stream_id": self.stream_id, "persons": [
            p for p in self.persons.values()
            if p["present"] and now - p["received_at"] < LEASE_S
        ]}


def frames_from_osc(port: int, bufsize: int = 65535):
    """Poll even during silence so the presence lease can release voices."""
    sys.path.insert(0, str(KIT))
    import osc_codec

    receiver = LiveReceiver(osc_codec)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", port))
        sock.settimeout(0.1)
        print(f"[driver] listening for /harmocap/v1/* on udp:{port}", flush=True)
        while True:
            try:
                data, _ = sock.recvfrom(bufsize)
                receiver.feed(data, time.monotonic())
            except socket.timeout:
                pass
            except (ValueError, TypeError, IndexError, KeyError, struct.error):
                pass
            yield receiver.snapshot(time.monotonic())


class ConsonanceSession:
    """One focused performer; identity changes start fresh kinematic history."""

    def __init__(self, out, *, snap=0.0, snap_mode="series", theta=0.15,
                 w_surprise=1.0, w_brake=0.5, pred_tau=0.15):
        self.out = out
        self.snap, self.snap_mode, self.theta = snap, snap_mode, theta
        self.tracker_args = dict(w_surprise=w_surprise, w_brake=w_brake,
                                 pred_tau=pred_tau)
        self.tracker = M.ZoneTracker(**self.tracker_args)
        self.identity = None
        self.last_cap = None
        self.person = None
        self.sustained = {}

    def update(self, frame):
        people = [p for p in frame.get("persons", []) if p.get("present")]
        people.sort(key=lambda p: (not p.get("focused"), p["slot_id"]))
        person = people[0] if people else None
        identity = (frame.get("stream_id"), person["slot_id"]) if person else None
        if identity != self.identity:
            for n in self.tracker.zones:
                self.out.release(n)
            self.tracker = M.ZoneTracker(**self.tracker_args)
            self.identity, self.last_cap = identity, None
            self.sustained.clear()
        self.person = person
        if person is None:
            return
        cap = person.get("captured_at_us", frame.get("captured_at_us"))
        kp, states = person.get("keypoints"), person.get("kp_state")
        if cap is None or kp is None or states is None:
            for n in self.tracker.zones:
                self.out.release(n)
            self.person, self.last_cap = None, None
            self.sustained.clear()
            self.tracker = M.ZoneTracker(**self.tracker_args)
            return
        if self.last_cap is not None and cap <= self.last_cap:
            return  # Other slots/heartbeat packets must not advance this body.
        self.last_cap = cap
        self.tracker.update(kp, states, cap / 1e6, present=True)
        for n, z in self.tracker.zones.items():
            z.d_eff = snap_apply(z.d_raw, self.snap, self.snap_mode, self.theta)
            _, _, observed = M.zone_point(z.name, z.kind, kp, states, z.side_speed)
            if not observed or z.gain <= 0.0:
                self.out.release(n)
                self.sustained[n] = (M.freq_for(n, z.d_eff, self.out.f1), 0.0,
                                     45.0 * z.d_eff)
                continue
            current = (M.freq_for(n, z.d_eff, self.out.f1),
                       0.45 * z.gain, 45.0 * z.d_eff)
            self.sustained[n] = current
            self.out.update(n, *current)

    def state(self):
        zones = []
        if self.person and self.last_cap is not None:
            for n, z in self.tracker.zones.items():
                x, y, observed = M.zone_point(
                    z.name, z.kind, self.person["keypoints"],
                    self.person["kp_state"], z.side_speed)
                zones.append(dict(n=n, x=x, y=y, observed=observed,
                                  active=VOICE_ID_BASE + n in self.out.on,
                                  freq=self.sustained.get(n, (self.out.f1 * n, 0., 0.))[0],
                                  detune=z.d_eff,
                                  gain=self.sustained.get(n, (0., 0., 0.))[1],
                                  phase_deg=self.sustained.get(n, (0., 0., 0.))[2]))
        return dict(mode="Consonancia kinetica", updated_at=time.time(),
                    stream_id=self.identity[0] if self.identity else None,
                    slot_id=self.identity[1] if self.identity else None,
                    captured_at_us=self.last_cap, zones=zones)


def write_state(path, state):
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state), encoding="utf-8")
        tmp.replace(path)


# ──────────────────────────────────────────────────────────────────────────
# main loop
# ──────────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--source", required=True,
                    help="session .jsonl path, or 'osc' for live wire")
    ap.add_argument("--osc-port", type=int, default=9000)
    ap.add_argument("--shaper-host", default="127.0.0.1")
    ap.add_argument("--shaper-port", type=int, default=9001,
                    help="shaper /beacon/* slave port (run shaper with --slave)")
    ap.add_argument("--shaper-control-port", type=int, default=9002)
    ap.add_argument("--f1", type=float, default=40.0)
    ap.add_argument("--snap", type=float, default=0.0,
                    help="0 = continuous (no snap) … 1 = hard wells")
    ap.add_argument("--snap-mode", default="series",
                    choices=["off", "series", "grid", "both"])
    ap.add_argument("--theta", type=float, default=0.15,
                    help="escape threshold (T units, surprise-normalized)")
    ap.add_argument("--gain-eps", type=float, default=0.03,
                    help="legacy compatibility option; sustained updates do not retrigger")
    ap.add_argument("--w-surprise", type=float, default=1.0)
    ap.add_argument("--w-brake", type=float, default=0.5)
    ap.add_argument("--pred-tau", type=float, default=0.15)
    ap.add_argument("--max-persons", type=int, choices=[1], default=1,
                    help="v1: track the first N slots (focus order)")
    ap.add_argument("--rate", type=float, default=1.0,
                    help="replay speed factor (file source only)")
    ap.add_argument("--dry", action="store_true",
                    help="no audio out; print a 1 Hz per-zone table")
    ap.add_argument("--state-file", type=Path, help="Live state for the camera overlay")
    ap.add_argument("--max-runtime-s", type=float, default=0.0)
    args = ap.parse_args()
    if args.rate <= 0:
        ap.error("--rate must be positive")
    if not 0 <= args.snap <= 1 or args.f1 <= 0:
        ap.error("--snap must be in [0,1] and --f1 must be positive")

    def stop(*_):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)

    out = ShaperOut(args.shaper_host, args.shaper_port, args.f1,
                    args.gain_eps, args.dry, args.shaper_control_port)
    session = ConsonanceSession(out, snap=args.snap, snap_mode=args.snap_mode,
                                theta=args.theta, w_surprise=args.w_surprise,
                                w_brake=args.w_brake, pred_tau=args.pred_tau)
    write_state(args.state_file, session.state())

    if args.source == "osc":
        src = frames_from_osc(args.osc_port)
    else:
        src = frames_from_file(Path(args.source).expanduser())

    t0_wall = time.monotonic()
    t0_cap = None
    last_print = 0.0
    n_frames = 0
    try:
        last_state = 0.0
        for frame in src:
            now = time.monotonic()
            if args.max_runtime_s and now - t0_wall >= args.max_runtime_s:
                break
            if args.source != "osc":
                cap_us = frame.get("captured_at_us")
                if cap_us is None:
                    continue
                if t0_cap is None:
                    t0_cap = cap_us
                delay = t0_wall + (cap_us - t0_cap) / 1e6 / args.rate - now
                if delay > 0:
                    time.sleep(delay)
            session.update(frame)
            n_frames += 1
            if now - last_state >= 0.1:
                write_state(args.state_file, session.state())
                last_state = now
            if args.dry and now - last_print >= 1.0:
                last_print = now
                print(json.dumps(session.state()), flush=True)
    except KeyboardInterrupt:
        print("\n[driver] interrupted")
    finally:
        out.panic()
        session.update({"persons": []})
        write_state(args.state_file, session.state())
    print(f"[driver] done: {n_frames} frames")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
