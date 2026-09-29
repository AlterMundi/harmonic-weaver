"""Zone kinematics and snap math for the consonance driver.

Stdlib only. Implements the operational definitions from the research pack
(CROSS_REPORT §B + ADDENDUM-f1-2-grid.md):

- Per-zone ballistic prediction error ("surprise") — deviation from the
  inertia of the movement in course, the core of Nicolás' redefinition.
- Signed mechanical power P = <a, v> — the brake/pump discriminator
  (P<0 = braked by resistance -> detune down; P>0 out of phase = pumping
  -> detune up).
- Snap as a finite potential well: small deviations stay snapped to the
  natural harmonic series (d=0); the movement deviation must exceed an
  escape threshold for the sound to leave the snap and slide continuously
  toward the f1/2-grid walls (|d|=1 = just intervals: fifth, third, 7th...).

All quantities are in torso units T (shoulder_mid-to-hip_mid distance) for
distance-to-camera invariance, and use REAL dt from captured_at_us (never
frame indices), following HarMoCAP conventions.
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

# ── zone definitions ────────────────────────────────────────────────────────
# COCO-17 indices (KEYPOINT_ORDER canonical order).
NOSE, L_EYE, R_EYE, L_EAR, R_EAR = 0, 1, 2, 3, 4
L_SHO, R_SHO, L_ELB, R_ELB, L_WRI, R_WRI = 5, 6, 7, 8, 9, 10
L_HIP, R_HIP, L_KNE, R_KNE, L_ANK, R_ANK = 11, 12, 13, 14, 15, 16

# Six shared voices, ordered explicitly by Nicolás (2026-09-27).
# Torso pairs use their midpoint; limb pairs retain the current side selector.
ZONES: tuple[tuple[int, str, str], ...] = (
    (1, "hips",      "midpoint"),
    (2, "shoulders", "midpoint"),
    (3, "knees",     "pair"),
    (4, "elbows",    "pair"),
    (5, "ankles",    "pair"),
    (6, "wrists",    "pair"),
)

ZONE_POINTS: dict[str, tuple[int, ...]] = {
    "hips": (L_HIP, R_HIP),
    "shoulders": (L_SHO, R_SHO),
    "knees": (L_KNE, R_KNE),
    "elbows": (L_ELB, R_ELB),
    "ankles": (L_ANK, R_ANK),
    "wrists": (L_WRI, R_WRI),
}

PAIR_IDX = {"knees": (L_KNE, R_KNE), "ankles": (L_ANK, R_ANK),
            "elbows": (L_ELB, R_ELB), "wrists": (L_WRI, R_WRI)}


@dataclass
class ZoneState:
    """Trailing-window kinematic state for one zone of one person."""
    n: int
    name: str
    kind: str
    # history of (t_s, x, y, observed) — causal windows
    hist: deque = field(default_factory=lambda: deque(maxlen=64))
    # per-side speed history for pair energy-max selection
    side_speed: tuple[float, float] = (0.0, 0.0)
    # smoothed outputs
    acceleration: float = 0.0  # T/s², measured before response scaling
    drive: float = 0.0         # signed ballistic deviation in torso units
    speed: float = 0.0          # T/s
    surprise: float = 0.0       # T (ballistic prediction error)
    power_sign: int = 0         # -1 brake, 0 neutral, +1 pump
    brake_frac: float = 0.0     # 0..1 fraction of |P| that is braking
    observed_frac: float = 1.0
    active: bool = False
    d_raw: float = 0.0
    d_eff: float = 0.0          # after snap
    gain: float = 0.0


def _torso(kp: list, kp_state: list) -> float:
    """Torso length T = |shoulder_mid - hip_mid| in isotropic units."""
    try:
        shx = (kp[L_SHO][0] + kp[R_SHO][0]) / 2.0
        shy = (kp[L_SHO][1] + kp[R_SHO][1]) / 2.0
        hpx = (kp[L_HIP][0] + kp[R_HIP][0]) / 2.0
        hpy = (kp[L_HIP][1] + kp[R_HIP][1]) / 2.0
        t = math.hypot(shx - hpx, shy - hpy)
        return t if t > 1e-6 else 0.2  # fallback nominal
    except (IndexError, TypeError):
        return 0.2


def zone_point(name: str, kind: str, kp: list, kp_state: list,
               side_speed: tuple[float, float]) -> tuple[float, float, bool]:
    """Compute the zone's driving point (x, y, observed) in isotropic units.

    midpoint: midpoint of the anatomical pair (hips or shoulders).
    pair: the more-active observed side drives the shared voice.
    """
    def obs(i: int) -> bool:
        try:
            return kp_state[i][0] == 0  # OBSERVED
        except (IndexError, TypeError):
            return False

    def pt(i: int) -> tuple[float, float]:
        return (kp[i][0], kp[i][1])

    if kind == "midpoint":
        li, ri = ZONE_POINTS[name]
        return ((kp[li][0] + kp[ri][0]) / 2,
                (kp[li][1] + kp[ri][1]) / 2, obs(li) and obs(ri))

    # pair: energy-max side
    li, ri = PAIR_IDX[name]
    l_obs, r_obs = obs(li), obs(ri)
    l_sp, r_sp = side_speed
    if l_obs and r_obs:
        pick = li if l_sp >= r_sp else ri
    elif l_obs:
        pick = li
    elif r_obs:
        pick = ri
    else:
        return (pt(li)[0] + pt(ri)[0]) / 2, (pt(li)[1] + pt(ri)[1]) / 2, False
    px, py = pt(pick)
    return px, py, True


def snap_map(d_raw: float, snap: float, theta: float = 0.15) -> float:
    """Finite potential well: snap to the natural series (d=0) with escape.

    snap = 0   -> pure continuous (no snap; d_eff = d_raw).
    snap in (0,1] -> well of relative depth `snap`: deviations below
        theta*(1-snap) are fully snapped to 0; above, d slides continuously
        toward the wall at |d|=1 (the f1/2-grid just interval). The movement
        deviation must EXCEED the escape threshold to leave the snap.

    Continuous everywhere (no discontinuous jumps) — a smooth escape ramp,
    per Nicolás: "continuo pero con nivel de snap; el desvío debe superar
    cierto valor para salirse del snap".
    """
    if snap <= 0.0:
        return max(-1.0, min(1.0, d_raw))
    a = abs(d_raw)
    s = 1.0 if d_raw >= 0 else -1.0
    thr = theta * (1.0 - snap)          # deadband shrinks as snap -> 1? no:
    # snap=1 -> thr=0 (hard well, everything above 0 escapes proportionally)
    # snap->0 -> thr=theta (soft, small deviations pass) — invert:
    thr = theta * snap                  # deeper snap = wider deadband
    if a <= thr:
        return 0.0                      # snapped to the series
    # escape ramp: from thr..1 maps to 0..1 continuously
    span = max(1e-9, 1.0 - thr)
    return s * min(1.0, (a - thr) / span)


def freq_for(n: int, d: float, f1: float) -> float:
    """f'(n,d) = f1*(n + d/2) — the ADDENDUM rule. d=0 -> series of f1;
    d=±1 -> odd multiples of f1/2 (just intervals: 3/2, 5/4, 7/4...)."""
    return f1 * (n + d / 2.0)


class ZoneTracker:
    """Per-person zone kinematics with causal windows (HarMoCAP conventions)."""

    def __init__(self, *, w_surprise: float = 1.0, w_brake: float = 0.5,
                 pred_tau: float = 0.15, brake_win: float = 0.30,
                 speed_norm: float = 1.5, gate_speed: float = 0.0):
        self.w_surprise = w_surprise
        self.w_brake = w_brake
        self.pred_tau = pred_tau        # s — ballistic prediction horizon
        self.brake_win = brake_win      # s — brake-fraction window
        self.speed_norm = speed_norm    # T/s mapped to gain 1.0
        self.gate_speed = gate_speed    # T/s — motion gate for activation
        self.zones: dict[int, ZoneState] = {}
        for n, name, kind in ZONES:
            self.zones[n] = ZoneState(n, name, kind)
        self._speed_p90: dict[int, float] = {n: 0.3 for n, _, _ in ZONES}
        # Independent histories prevent side selection from creating motion.
        self._pair_hist = {name: {i: deque(maxlen=64) for i in indices}
                           for name, indices in PAIR_IDX.items()}

    def update(self, kp: list, kp_state: list, t_s: float,
               present: bool) -> None:
        if not present:
            for z in self.zones.values():
                z.active = False
                z.gain = 0.0
            return
        T = _torso(kp, kp_state)

        # per-side speeds for pair energy-max selection (independent raw
        # history per COCO point, so each side's speed is its own)
        side_sp = {}
        for name, (li, ri) in PAIR_IDX.items():
            speeds = {}
            for i in (li, ri):
                try:
                    x, y = kp[i][0], kp[i][1]
                except (IndexError, TypeError):
                    continue
                hist = self._pair_hist[name][i]
                observed = kp_state[i][0] == 0
                if hist and observed and hist[-1][3]:
                    lt, lx, ly, _ = hist[-1]
                    dt = max(1e-3, t_s - lt)
                    speeds[i] = math.hypot(x - lx, y - ly) / dt / T
                hist.append((t_s, x, y, observed))
            side_sp[name] = (speeds.get(li, 0.0), speeds.get(ri, 0.0))

        for n, name, kind in ZONES:
            z = self.zones[n]
            ss = side_sp.get(name, (0.0, 0.0))
            z.side_speed = ss
            x, y, obs = zone_point(name, kind, kp, kp_state, ss)
            if kind == "pair":
                li, ri = PAIR_IDX[name]
                pick = li if kp_state[li][0] == 0 and (kp_state[ri][0] != 0 or ss[0] >= ss[1]) else ri
                z.hist = self._pair_hist[name][pick]
            else:
                z.hist.append((t_s, x, y, obs))

            z.gain = 0.0
            z.speed = 0.0
            z.acceleration = 0.0
            z.drive = 0.0
            z.active = False
            if len(z.hist) < 2:
                continue

            (t0, x0, y0, o0) = z.hist[-2]
            (t1, x1, y1, o1) = z.hist[-1]
            dt = max(1e-3, t1 - t0)
            # observed fraction over ~300 ms
            win = [h for h in z.hist if t1 - h[0] <= 0.30]
            z.observed_frac = (sum(1 for h in win if h[3]) / len(win)) if win else 0.0

            if not (o0 and o1):
                z.active = False
                z.gain = 0.0
                continue

            vx = (x1 - x0) / dt / T
            vy = (y1 - y0) / dt / T
            speed = math.hypot(vx, vy)
            z.speed = speed
            z.active = speed > self.gate_speed
            z.gain = min(1.0, speed / self.speed_norm) if z.active else 0.0
            if len(z.hist) < 3:
                z.d_raw = 0.0
                continue

            # acceleration from previous velocity sample (vx already in T/s,
            # so ax = dv/dt is T/s² — do NOT divide by T again)
            (tm, xm, ym, om) = z.hist[-3]
            dtm = max(1e-3, t0 - tm)
            if om:
                vxm = (x0 - xm) / dtm / T
                vym = (y0 - ym) / dtm / T
                ax = (vx - vxm) / dt
                ay = (vy - vym) / dt
            else:
                ax = ay = 0.0

            z.acceleration = math.hypot(ax, ay)

            # signed mechanical power P = <a, v>
            P = ax * vx + ay * vy
            z.power_sign = 1 if P > 1e-4 else (-1 if P < -1e-4 else 0)

            # brake fraction over brake_win
            brakes = [h for h in z.hist if t1 - h[0] <= self.brake_win]
            # (approximate: recompute P per consecutive pair in window)
            neg = pos = 0.0
            for i in range(1, len(brakes)):
                (ta, xa, ya, oa) = brakes[i - 1]
                (tb, xb, yb, ob) = brakes[i]
                dtt = max(1e-3, tb - ta)
                if not (oa and ob):
                    continue
                vxa = (xb - xa) / dtt / T
                vya = (yb - ya) / dtt / T
                # crude accel within window
                if i >= 2:
                    (tc, xc, yc, oc) = brakes[i - 2]
                    dtc = max(1e-3, ta - tc)
                    if oc:
                        vxc = (xa - xc) / dtc / T
                        vyc = (ya - yc) / dtc / T
                        axw = (vxa - vxc) / dtt
                        ayw = (vya - vyc) / dtt
                        Pw = axw * vxa + ayw * vya
                        if Pw < 0:
                            neg += abs(Pw)
                        else:
                            pos += abs(Pw)
            tot = neg + pos
            z.brake_frac = (neg / tot) if tot > 1e-9 else 0.0

            # ballistic prediction error ("surprise") — deviation from inertia
            surprise = 0.0
            target_t = t1 - self.pred_tau
            past = None
            for h in z.hist:
                if h[0] <= target_t:
                    past = h
            if past is not None and past[3] and o1:
                (tp, xp, yp, _) = past
                dtp = max(1e-3, t1 - tp)
                # velocity at past sample (central-ish)
                idx = z.hist.index(past)
                if idx >= 1 and z.hist[idx - 1][3]:
                    (tq, xq, yq, _) = z.hist[idx - 1]
                    dtq = max(1e-3, tp - tq)
                    vxp = (xp - xq) / dtq / T
                    vyp = (yp - yq) / dtq / T
                else:
                    vxp = vyp = 0.0
                pred_x = xp + vxp * dtp * T   # vxp is T/s → back to isotropic
                pred_y = yp + vyp * dtp * T
                surprise = math.hypot(x1 - pred_x, y1 - pred_y) / T

            z.surprise = surprise

            # adaptive normalization: running p90 of surprise per zone
            p90 = self._speed_p90[n]
            self._speed_p90[n] = 0.98 * p90 + 0.02 * max(surprise, speed)
            norm = max(0.05, self._speed_p90[n])

            # d_raw: magnitude from surprise, sign from power (brake->down,
            # pump->up), plus brake-fraction bias
            sign = z.power_sign if z.power_sign != 0 else (
                -1 if z.brake_frac > 0.5 else 1)
            mag = min(2.0, surprise / norm)
            # The brake/pump character MODULATES the deviation magnitude — a
            # quiet zone (mag≈0) must sit at d≈0 (snapped to the series), not
            # at a constant offset. d = sign·mag·(w_s + w_b·(2·bf−1)).
            d_raw = sign * mag * (self.w_surprise +
                                  self.w_brake * (2.0 * z.brake_frac - 1.0))
            z.drive = sign * surprise * (self.w_surprise + self.w_brake * (2.0 * z.brake_frac - 1.0))
            z.d_raw = max(-1.0, min(1.0, d_raw))


    def apply_snap(self, snap: float, theta: float = 0.15) -> None:
        for z in self.zones.values():
            z.d_eff = snap_map(z.d_raw, snap, theta)
