"""Causal estimators used by the laboratory, independent of synthesis or UI."""
from collections import deque
import math

import numpy as np


class CausalSlope:
    """Trailing least-squares derivative in source seconds, reset on invalid input."""
    def __init__(self, window_s=.12, max_gap_s=.25):
        self.window_s, self.max_gap_s = window_s, max_gap_s
        self.samples = deque(maxlen=2048)

    def clear(self):
        self.samples.clear()

    def push(self, t, value):
        value = None if value is None else np.asarray(value, dtype=float)
        if value is None or not np.isfinite(value).all():
            self.clear()
            return None
        if self.samples and (t <= self.samples[-1][0] or t-self.samples[-1][0] > self.max_gap_s):
            self.clear()
        self.samples.append((t, value.copy()))
        while self.samples and self.samples[0][0] < t-self.window_s:
            self.samples.popleft()
        if len(self.samples) < 3 or t-self.samples[0][0] < min(self.window_s*.5, .05):
            return None
        times = np.array([s[0] for s in self.samples])
        centered = times-times.mean()
        denominator = centered @ centered
        if denominator < 1e-12:
            return None
        values = np.stack([s[1] for s in self.samples])
        return np.tensordot(centered, values, axes=(0, 0)) / denominator


def interference(mode, contribution, noise_velocity, noise_delta):
    """Anni v0 in 2D. Missing direction is not a neutral measurement."""
    mode, contribution = np.asarray(mode), np.asarray(contribution)
    norm_mode, norm_delta = float(np.linalg.norm(mode)), float(np.linalg.norm(contribution))
    if not np.isfinite(mode).all() or not np.isfinite(contribution).all():
        return {"state": "missing", "reason": "invalid observation"}
    amplitude = norm_delta/noise_delta
    if norm_mode <= noise_velocity:
        return {"state": "missing", "reason": "no established mode", "A": amplitude}
    if norm_delta <= noise_delta:
        return {"state": "missing", "reason": "no detectable contribution", "A": amplitude}
    dot = float(mode @ contribution)/(norm_mode*norm_delta)
    cross = float(mode[0]*contribution[1]-mode[1]*contribution[0])/(norm_mode*norm_delta)
    return {"state": "observed", "I": float(np.clip(dot, -1, 1)), "R": min(1., abs(cross)),
            "A": amplitude, "angle_deg": math.degrees(math.atan2(cross, dot))}


class RelativeMode:
    def __init__(self, settings):
        self.settings = settings
        self.history = deque(maxlen=2048)
        self.slope = CausalSlope(settings.derivative_window_s, settings.max_gap_s)
        self.previous = None

    def push(self, t, velocity):
        invalid_time = type(t) not in (int, float) or not math.isfinite(t) or t < 0
        invalid_velocity = velocity is None
        if not invalid_velocity:
            try:
                velocity = np.asarray(velocity, dtype=float)
                invalid_velocity = velocity.shape != (2,) or not np.isfinite(velocity).all()
            except (TypeError, ValueError):
                invalid_velocity = True
        if invalid_time or invalid_velocity:
            self.history.clear()
            self.previous = None
            self.slope.clear()
            return {"state": "missing", "reason": "invalid relationship time" if invalid_time else "missing or invalid relationship"}
        if self.history and (t <= self.history[-1][0] or t-self.history[-1][0] > self.settings.max_gap_s):
            self.history.clear()
            self.previous = None
            self.slope.clear()
        while self.history and self.history[0][0] < t-self.settings.history_s:
            self.history.popleft()
        # Every sample in this mode ends strictly before the contribution under test.
        mode = (np.mean([v for _, v in self.history], axis=0) if self.history else None)
        if self.settings.relation_reference == "instantaneous":
            mode = velocity
        delta = velocity-self.previous[1] if self.previous else None
        dt = t-self.previous[0] if self.previous else None
        derivative = self.slope.push(t, velocity)
        result = {"state": "missing", "reason": "warming relationship"}
        if mode is not None and delta is not None:
            result = interference(mode, delta, self.settings.noise_velocity, self.settings.noise_delta)
            result.update(delta=delta.tolist(), delta_per_s=(delta/dt).tolist(),
                          derivative=None if derivative is None else derivative.tolist(),
                          prior_mode=mode.tolist())
        self.history.append((t, velocity.copy()))
        self.previous = (t, velocity.copy())
        return result


class AngularMode:
    def __init__(self, settings):
        self.settings = settings
        self.previous = None
        self.velocity = CausalSlope(settings.derivative_window_s, settings.max_gap_s)
        self.history = deque(maxlen=2048)

    def push(self, t, vector):
        if vector is None or np.linalg.norm(vector) <= 1e-8:
            self.previous = None
            self.velocity.clear()
            self.history.clear()
            return {"state": "missing", "reason": "missing segment"}
        angle = math.atan2(vector[1], vector[0])
        if self.previous and 0 < t-self.previous[0] <= self.settings.max_gap_s:
            delta = math.atan2(math.sin(angle-self.previous[1]), math.cos(angle-self.previous[1]))
            angle = self.previous[1]+delta
        else:
            self.velocity.clear()
            self.history.clear()
        prediction = None
        eligible = [s for s in self.history if s[0] <= t-self.settings.horizon_s]
        if eligible and eligible[-1][2] is not None:
            pt, pa, pv = eligible[-1]
            prediction = pa+pv*(t-pt)
        speed = self.velocity.push(t, angle)
        self.history.append((t, angle, None if speed is None else float(speed)))
        while self.history and self.history[0][0] < t-max(2*self.settings.horizon_s, 1.):
            self.history.popleft()
        self.previous = (t, angle)
        return {"state": "observed", "angle_deg": math.degrees(angle),
                "velocity_deg_s": None if speed is None else math.degrees(float(speed)),
                "prediction_error_deg": None if prediction is None else math.degrees(angle-prediction)}
