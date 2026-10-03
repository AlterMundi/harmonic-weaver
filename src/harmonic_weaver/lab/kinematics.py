"""Source-time pose preparation; normalization is explicit and missingness survives."""
from collections import deque
import math

import numpy as np

from .analysis_math import CausalSlope

ZONES = ((11, 12), (5, 6), (13, 14), (7, 8), (15, 16), (9, 10))
PARENTS = ((5, 6), (11, 12), (11, 12), (5, 6), (13, 14), (7, 8))


def observed_xy(person):
    points = np.full((17, 2), np.nan)
    if person is not None:
        for joint in person.joints:
            if joint.state == "observed" and joint.position is not None:
                points[joint.index] = joint.position[:2]
    return points


def torso_scale(points):
    if not np.isfinite(points[[5, 6, 11, 12]]).all():
        return None
    length = float(np.linalg.norm(points[[5, 6]].mean(axis=0)-points[[11, 12]].mean(axis=0)))
    return length if length > 1e-6 else None


def coordinates(points, settings, scale):
    if scale is None or not np.isfinite(scale) or scale <= 0:
        return np.full_like(points, np.nan)
    transformed = points.copy()
    if settings.reference in {"pelvis", "torso"}:
        if not np.isfinite(points[[11, 12]]).all():
            return np.full_like(points, np.nan)
        transformed -= points[[11, 12]].mean(axis=0)
    elif settings.reference == "fixed":
        transformed -= [settings.fixed_x, settings.fixed_y]
    if settings.reference == "torso":
        if not np.isfinite(points[[5, 6]]).all():
            return np.full_like(points, np.nan)
        vertical = points[[11, 12]].mean(axis=0)-points[[5, 6]].mean(axis=0)
        length = np.linalg.norm(vertical)
        if length < 1e-6:
            return np.full_like(points, np.nan)
        vertical /= length
        horizontal = np.array([vertical[1], -vertical[0]])
        transformed = transformed @ np.stack([horizontal, vertical]).T
    return transformed/scale


class Kinematics:
    def __init__(self, settings, scale=None):
        self.settings, self.scale = settings, scale
        self.positions = [CausalSlope(settings.derivative_window_s, settings.max_gap_s) for _ in range(17)]
        self.velocities = [CausalSlope(settings.derivative_window_s, settings.max_gap_s) for _ in range(17)]
        self.filtered = np.full((17, 2), np.nan)
        self.last_t = None
        self.history = deque(maxlen=2048)

    def push(self, t, person):
        raw = observed_xy(person)
        points = coordinates(raw, self.settings, self.scale)
        dt = t-self.last_t if self.last_t is not None else 0.
        if self.last_t is not None and (dt <= 0 or dt > self.settings.max_gap_s):
            for estimator in self.positions+self.velocities:
                estimator.clear()
            self.filtered[:] = np.nan
            self.history.clear()
        if self.settings.smoothing_s and dt > 0:
            alpha = -math.expm1(-dt/self.settings.smoothing_s)
            valid = np.isfinite(points).all(axis=1) & np.isfinite(self.filtered).all(axis=1)
            points[valid] = self.filtered[valid]+alpha*(points[valid]-self.filtered[valid])
        self.filtered = points.copy()
        velocity, acceleration = np.full_like(points, np.nan), np.full_like(points, np.nan)
        for index in range(17):
            value = self.positions[index].push(t, points[index])
            if value is not None:
                velocity[index] = value
            value = self.velocities[index].push(t, value)
            if value is not None:
                acceleration[index] = value
        prior = next((row for row in reversed(self.history) if row[0] <= t-self.settings.horizon_s), None)
        position_error = np.full(17, np.nan)
        velocity_error = np.full(17, np.nan)
        if prior is not None:
            pt, pp, pv = prior
            position_error = np.linalg.norm(points-pp, axis=1)
            velocity_error = np.linalg.norm(points-(pp+pv*(t-pt)), axis=1)
        self.history.append((t, points.copy(), velocity.copy()))
        while self.history and self.history[0][0] < t-max(2*self.settings.horizon_s, 1.):
            self.history.popleft()
        self.last_t = t
        return {"raw": raw, "position": points, "velocity": velocity, "acceleration": acceleration,
                "position_error": position_error, "velocity_error": velocity_error}
