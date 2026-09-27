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

v1 known compromises (documented, not hidden):
- Gain updates go through voice_on, which calls record_strum() — at frame rate
  that would pollute the shaper's strum-period estimator, so voice_on is
  throttled (only when gain moves > --gain-eps or on activation change).
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
import math
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metrics as M  # noqa: E402

KIT = Path.home() / "Projects/HarMoCAP/harmocap-nico-kit"

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
                 dry: bool):
        self.host, self.port, self.f1 = host, port, f1
        self.gain_eps, self.dry = gain_eps, dry
        self.sock = None if dry else socket.socket(socket.AF_INET,
                                                   socket.SOCK_DGRAM)
        self.last_gain: dict[int, float] = {}
        self.on: set[int] = set()

    def _send(self, address: str, args: list) -> None:
        if self.dry or self.sock is None:
            return
        self.sock.sendto(enc_msg(address, args), (self.host, self.port))

    def update(self, n: int, freq: float, gain: float) -> None:
        vid = VOICE_ID_BASE + n
        prev = self.last_gain.get(n)
        if vid not in self.on or prev is None or abs(gain - prev) > self.gain_eps:
            # (re)assert voice with current gain — throttled (see module doc)
            self._send("/beacon/voice/on", [vid, float(freq), float(gain), int(n)])
            self.on.add(vid)
            self.last_gain[n] = gain
        else:
            self._send("/beacon/voice/freq", [vid, float(freq)])

    def release(self, n: int) -> None:
        vid = VOICE_ID_BASE + n
        if vid in self.on:
            self._send("/beacon/voice/off", [vid])
            self.on.discard(vid)
            self.last_gain.pop(n, None)

    def panic(self) -> None:
        self._send("/beacon/panic", [])
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


def frames_from_osc(port: int, bufsize: int = 65535):
    """Live wire → frame dicts. Uses the kit codec when importable."""
    sys.path.insert(0, str(KIT))
    import osc_codec  # type: ignore

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    print(f"[driver] listening for /harmocap/v1/* on udp:{port}", flush=True)
    stream_id, last_seq = None, -1
    pending: dict[int, dict] = {}   # captured_frame_id -> frame being assembled
    while True:
        data, _ = sock.recvfrom(bufsize)
        try:
            msgs = osc_codec.decode_bundle(data)
        except Exception:
            continue
        frame = None
        for addr, args in msgs:
            if addr.endswith("/meta"):
                (sid, fid, seq, n_persons, fps, _cid, _cg, _cs,
                 cap_us, _proc_us, _q_us) = args[:11]
                if sid != stream_id:            # kit rule 2: new stream → reset
                    stream_id, last_seq, pending = sid, -1, {}
                if seq <= last_seq:             # kit rule 3: monotonic
                    continue
                last_seq = seq
                frame = {"stream_id": sid, "captured_frame_id": fid,
                         "captured_at_us": cap_us, "fps": fps,
                         "n_persons": n_persons, "persons": []}
                pending[fid] = frame
            elif addr is not None and "/person/" in addr:
                rest = addr.split("/person/", 1)[1]
                slot_s, _, field = rest.partition("/")
                fid = max(pending) if pending else None
                if fid is None:
                    continue
                fr = pending[fid]
                slot = int(slot_s)
                per = next((p for p in fr["persons"] if p["slot_id"] == slot),
                           None)
                if per is None:
                    per = {"slot_id": slot, "present": False}
                    fr["persons"].append(per)
                if field == "present":
                    per["present"] = bool(args[0])
                elif field == "keypoints":
                    per["keypoints"] = osc_codec.unpack_keypoints(args[0])
                elif field == "kp_state":
                    per["kp_state"] = osc_codec.unpack_kp_state(args[0])
        if frame is not None:
            # emit once the bundle for its last person arrived; simplest: emit
            # every frame we started, persons fill in as their bundles land.
            yield frame
            # prune old assemblies
            for fid in [k for k in pending if k < frame["captured_frame_id"] - 4]:
                pending.pop(fid, None)


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
    ap.add_argument("--f1", type=float, default=40.0)
    ap.add_argument("--snap", type=float, default=0.5,
                    help="0 = continuous (no snap) … 1 = hard wells")
    ap.add_argument("--snap-mode", default="series",
                    choices=["off", "series", "grid", "both"])
    ap.add_argument("--theta", type=float, default=0.15,
                    help="escape threshold (T units, surprise-normalized)")
    ap.add_argument("--gain-eps", type=float, default=0.03,
                    help="gain change that justifies a voice_on re-assert")
    ap.add_argument("--w-surprise", type=float, default=1.0)
    ap.add_argument("--w-brake", type=float, default=0.5)
    ap.add_argument("--pred-tau", type=float, default=0.15)
    ap.add_argument("--max-persons", type=int, default=1,
                    help="v1: track the first N slots (focus order)")
    ap.add_argument("--rate", type=float, default=1.0,
                    help="replay speed factor (file source only)")
    ap.add_argument("--dry", action="store_true",
                    help="no audio out; print a 1 Hz per-zone table")
    args = ap.parse_args()

    tracker = M.ZoneTracker(w_surprise=args.w_surprise, w_brake=args.w_brake,
                            pred_tau=args.pred_tau)
    out = ShaperOut(args.shaper_host, args.shaper_port, args.f1,
                    args.gain_eps, args.dry)

    if args.source == "osc":
        src = frames_from_osc(args.osc_port)
    else:
        src = frames_from_file(Path(args.source).expanduser())

    t0_wall = time.monotonic()
    t0_cap = None
    last_print = 0.0
    n_frames = 0
    try:
        for frame in src:
            cap_us = frame.get("captured_at_us")
            if cap_us is None:
                continue
            if t0_cap is None:
                t0_cap = cap_us
            # realtime pacing for file replay
            if args.source != "osc":
                target = t0_wall + (cap_us - t0_cap) / 1e6 / args.rate
                delay = target - time.monotonic()
                if delay > 0:
                    time.sleep(delay)
            t_s = cap_us / 1e6

            persons = [p for p in frame.get("persons", []) if p.get("present")]
            persons.sort(key=lambda p: (not p.get("focused"), p["slot_id"]))
            persons = persons[:args.max_persons]

            for p in persons:
                kp = p.get("keypoints")
                kps = p.get("kp_state")
                if kp is None or kps is None:
                    continue
                tracker.update(kp, kps, t_s, present=True)
            if not persons:
                tracker.update([], [], t_s, present=False)

            tracker.apply_snap(args.snap if args.snap_mode != "off" else 0.0,
                               args.theta)
            # NOTE: apply_snap uses metrics.snap_map (series well); grid/both
            # modes post-process here:
            if args.snap_mode in ("grid", "both"):
                for z in tracker.zones.values():
                    z.d_eff = snap_apply(z.d_raw, args.snap, args.snap_mode,
                                         args.theta)

            for n, z in tracker.zones.items():
                if z.active and z.gain > 0.01:
                    freq = M.freq_for(n, z.d_eff, args.f1)
                    out.update(n, freq, z.gain * 0.6)
                else:
                    out.release(n)
            n_frames += 1

            if args.dry and t_s - last_print >= 1.0:
                last_print = t_s
                print(f"── t={t_s - t0_cap / 1e6:7.1f}s frame={n_frames}")
                for n, z in sorted(tracker.zones.items()):
                    if z.active:
                        f = M.freq_for(n, z.d_eff, args.f1)
                        print(f"  H{n:<2} {z.name:<12} d={z.d_eff:+.3f} "
                              f"f={f:7.2f}Hz g={z.gain:.2f} "
                              f"surp={z.surprise:.3f} P={'+' if z.power_sign > 0 else ('-' if z.power_sign < 0 else '0')}")
    except KeyboardInterrupt:
        print("\n[driver] interrupted")
    finally:
        out.panic()
    print(f"[driver] done: {n_frames} frames")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
