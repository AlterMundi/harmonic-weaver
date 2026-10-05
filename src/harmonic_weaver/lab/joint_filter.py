"""Causal conditioning of measured pose; raw tracking/cache remain untouched.

Limits are tuning parameters in projected torso lengths, not physiological bounds.
No missing coordinate is filled; estimated positions are exposed separately.
"""
from collections import deque
from functools import lru_cache
from hashlib import sha256
import importlib
import math
import os
from pathlib import Path
import sys
import numpy as np

from .kinematics import observed_xy, torso_scale


@lru_cache(maxsize=1)
def harmocap_one_euro():
    """Use the actual checkout's lightweight filter, not a copied implementation."""
    source = Path(os.environ.get("HARMOCAP_DIR", Path.home()/"Projects/HarMoCAP"))/"src"
    sys.path.insert(0, str(source))
    try:
        module = importlib.import_module("harmocap.smoothing")
    except ImportError as exc:
        raise RuntimeError("One-Euro requires the HarMoCAP checkout; set HARMOCAP_DIR") from exc
    finally:
        sys.path.remove(str(source))
    if not Path(module.__file__).resolve().is_relative_to(source.resolve()):
        raise RuntimeError("HarMoCAP import differs from HARMOCAP_DIR; restart with the intended checkout")
    implementation = Path(module.__file__).resolve()
    return module.OneEuroFilter, str(implementation), sha256(implementation.read_bytes()).hexdigest()


class JointMotionFilter:
    def __init__(self, settings, scale=None):
        self.settings = settings
        self.scale = scale
        self.states = {}

    def push(self, frame, person_id):
        person = next((p for p in frame.persons if p.person_id == person_id), None)
        if not self.settings.tracking_filter_enabled:
            return frame, {"enabled": False}
        if person is None:
            self.states.clear()
            return frame, {"enabled": True, "state": "missing", "reason": "selected person missing"}
        for index in set(self.states)-{q.index for q in person.joints}:
            self.states.pop(index)
        if self.settings.tracking_smoother == "harmocap_one_euro":
            return self._one_euro(frame, person_id, person)
        if self.scale is None:
            self.scale = torso_scale(observed_xy(person))
        if self.scale is None:
            return frame, {"enabled": True, "state": "missing", "reason": "torso scale unavailable"}
        t = frame.source_time_s
        observations = {q.index:q for q in person.joints}
        swapped = False
        # A per-joint acceleration limiter cannot distinguish an isolated swap.
        # Repair only a decisive continuity mismatch, not every projected crossing.
        if self.settings.tracking_hip_swap_guard and all(i in observations and observations[i].state == "observed" and i in self.states for i in (11, 12)):
            dt = [t-self.states[i]["time"] for i in (11,12)]
            if all(0 < d <= self.settings.max_gap_s for d in dt):
                raw = [np.array(observations[i].position[:2])/self.scale for i in (11,12)]
                predicted = [self.states[i]["position"]+self.states[i]["velocity"]*d for i,d in zip((11,12),dt)]
                direct = sum(float(np.sum((x-y)**2)) for x,y in zip(raw,predicted))
                crossed = sum(float(np.sum((x-y)**2)) for x,y in zip(raw[::-1],predicted))
                if crossed < .35*direct and direct-crossed > .05**2:
                    observations[11], observations[12] = observations[12], observations[11]
                    swapped = True
        estimates, limited = [], []
        for original in person.joints:
            q = observations[original.index]
            index = original.index
            if q.state != "observed" or q.position is None:
                self.states.pop(index, None)
                estimates.append(original.model_copy(deep=True))
                continue
            measurement = np.array(q.position[:2], dtype=float)/self.scale
            previous = self.states.get(index)
            dt = t-previous["time"] if previous else None
            if previous is None or dt <= 0 or dt > self.settings.max_gap_s:
                previous = {"time":t, "position":measurement.copy(), "velocity":np.zeros(2),
                            "measurements":deque(maxlen=self.settings.tracking_median_frames)}
                self.states[index] = previous
                dt = None
            previous["measurements"].append(measurement)
            target = np.median(np.stack(previous["measurements"]), axis=0)
            if dt is not None:
                tau = self.settings.tracking_smoothing_s
                alpha = -math.expm1(-dt/tau) if tau else 1.
                desired_velocity = alpha*(target-previous["position"])/dt
                delta = desired_velocity-previous["velocity"]
                limit = self.settings.tracking_joint_accel_limits[index]*dt
                norm = float(np.linalg.norm(delta))
                if norm > limit:
                    delta *= limit/norm
                    limited.append(index)
                velocity = previous["velocity"]+delta
                previous["position"] += velocity*dt
                previous["velocity"] = velocity
            previous["time"] = t
            estimate = original.model_copy(deep=True)
            estimate.position = [float(v) for v in previous["position"]*self.scale]+list(q.position[2:])
            estimate.confidence = q.confidence
            estimates.append(estimate)
        conditioned = frame.model_copy(deep=True)
        selected = next(p for p in conditioned.persons if p.person_id == person_id)
        selected.joints = estimates
        return conditioned, {"enabled": True, "state": "conditioned", "scale": self.scale,
            "smoother": "bounded",
            "unit": "projected torso lengths/s²", "hip_labels_swapped": swapped,
            "acceleration_limited_joints": limited,
            "interpretation": "causal position estimates, not new raw observations or anatomical limits"}

    def _one_euro(self, frame, person_id, person):
        factory, source, source_hash = harmocap_one_euro()
        settings = self.settings
        estimates = []
        t = frame.source_time_s
        for q in person.joints:
            estimate = q.model_copy(deep=True)
            if q.state != "observed" or q.position is None:
                self.states.pop(q.index, None)
            else:
                previous = self.states.get(q.index)
                dt = t-previous["time"] if previous else 0.
                if previous is None or dt <= 0 or dt > settings.max_gap_s:
                    previous = {"filters": [factory(settings.tracking_one_euro_mincutoff,
                        settings.tracking_one_euro_beta, settings.tracking_one_euro_dcutoff)
                        for _ in q.position]}
                    self.states[q.index] = previous
                estimate.position = [f(x, dt) for f,x in zip(previous["filters"], q.position)]
                previous["time"] = t
            estimates.append(estimate)
        conditioned = frame.model_copy(deep=True)
        next(p for p in conditioned.persons if p.person_id == person_id).joints = estimates
        return conditioned, {"enabled": True, "state": "conditioned", "smoother": "harmocap_one_euro",
            "implementation": source, "implementation_sha256": source_hash,
            "unit": frame.unit, "hip_labels_swapped": False,
            "acceleration_limited_joints": [],
            "interpretation": "HarMoCAP One-Euro on observed coordinates; no hold, median, swap repair or acceleration cap"}
