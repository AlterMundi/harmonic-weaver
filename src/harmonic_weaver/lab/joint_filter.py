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
        if self.settings.tracking_smoother == "outlier_gate":
            return self._outlier_gate(frame, person_id, person)
        t = frame.source_time_s
        observations, swapped = self._hip_assignment(person, t, self.settings.tracking_hip_swap_guard)
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

    def _outlier_gate(self, frame, person_id, person):
        """Reject sparse glitches without a low-pass, holding or interpolation.

        Acceleration uses adjacent source-time velocity intervals and a position
        noise allowance. A new coherent trajectory is reacquired after missing
        samples, so downstream derivatives cannot span the rejected jump.
        """
        t = frame.source_time_s
        settings = self.settings
        observations, swapped = self._hip_assignment(person, t, settings.tracking_hip_swap_guard)
        estimates, rejected, reacquired = [], [], []
        for original in person.joints:
            index = original.index
            q = observations[index]
            estimate = original.model_copy(deep=True)
            if q.state != "observed" or q.position is None:
                self.states.pop(index, None)
                estimates.append(estimate)
                continue
            measurement = np.array(q.position[:2], dtype=float)/self.scale
            previous = self.states.get(index)
            sample_dt = t-previous["sample_time"] if previous else 0.
            if previous is None or sample_dt <= 0 or sample_dt > settings.max_gap_s:
                previous = {"time": t, "sample_time": t, "position": measurement.copy(),
                            "velocity": np.zeros(2), "interval": None, "candidates": []}
                self.states[index] = previous
            else:
                dt = t-previous["time"]
                limit = settings.tracking_joint_accel_limits[index]
                interval = previous["interval"] or dt
                residual = measurement-(previous["position"]+previous["velocity"]*dt)
                allowance = settings.tracking_outlier_tolerance + .5*limit*(interval+dt)*dt
                if dt > settings.max_gap_s or np.linalg.norm(residual) > allowance:
                    candidates = previous["candidates"]
                    # Reacquisition also checks acceleration: a noisy, oscillating
                    # run must not become trusted merely because it lasted longer.
                    if len(candidates) >= 2:
                        pt, pp = candidates[-1]
                        ot, op = candidates[-2]
                        cd, od = t-pt, pt-ot
                        prediction = pp+(pp-op)/od*cd
                        if np.linalg.norm(measurement-prediction) > settings.tracking_outlier_tolerance + .5*limit*(od+cd)*cd:
                            candidates.clear()
                    candidates.append((t, measurement.copy()))
                    if len(candidates) < settings.tracking_outlier_recovery_frames:
                        estimate.state, estimate.position, estimate.confidence = "missing", None, 0.
                        previous["sample_time"] = t
                        rejected.append(index)
                        estimates.append(estimate)
                        continue
                    ct, cp = candidates[-2]
                    previous["velocity"] = (measurement-cp)/(t-ct)
                    previous["interval"] = t-ct
                    reacquired.append(index)
                else:
                    previous["velocity"] = (measurement-previous["position"])/dt
                    previous["interval"] = dt
                previous["position"] = measurement.copy()
                previous["time"] = previous["sample_time"] = t
                previous["candidates"].clear()
            # Accepted measurements are exact, including extra coordinates and
            # confidence. A repaired hip uses its assigned measurement's values.
            estimate.position, estimate.confidence = list(q.position), q.confidence
            estimates.append(estimate)
        conditioned = frame.model_copy(deep=True)
        next(p for p in conditioned.persons if p.person_id == person_id).joints = estimates
        return conditioned, {"enabled": True, "state": "conditioned", "smoother": "outlier_gate",
            "scale": self.scale, "unit": "projected torso lengths/s²",
            "hip_labels_swapped": swapped, "rejected_joints": rejected,
            "reacquired_joints": reacquired, "acceleration_limited_joints": [],
            "interpretation": "accepted measurements unchanged; rejected jumps missing, not held or interpolated; limits are adjustable, not anatomical"}

    def _hip_assignment(self, person, t, enabled):
        observations = {q.index:q for q in person.joints}
        swapped = False
        # A per-joint acceleration limiter cannot distinguish an isolated swap.
        # Repair only a decisive continuity mismatch, not every projected crossing.
        if enabled and self.scale is not None and all(i in observations and observations[i].state == "observed" and i in self.states and "position" in self.states[i] for i in (11, 12)):
            dt = [t-self.states[i]["time"] for i in (11,12)]
            if all(0 < d <= self.settings.max_gap_s for d in dt):
                raw = [np.array(observations[i].position[:2])/self.scale for i in (11,12)]
                predicted = [self.states[i]["position"]+self.states[i]["velocity"]*d for i,d in zip((11,12),dt)]
                direct = sum(float(np.sum((x-y)**2)) for x,y in zip(raw,predicted))
                crossed = sum(float(np.sum((x-y)**2)) for x,y in zip(raw[::-1],predicted))
                if crossed < .35*direct and direct-crossed > .05**2:
                    observations[11], observations[12] = observations[12], observations[11]
                    swapped = True
        return observations, swapped

    def _one_euro(self, frame, person_id, person):
        factory, source, source_hash = harmocap_one_euro()
        settings = self.settings
        estimates = []
        t = frame.source_time_s
        guard = settings.tracking_one_euro_hip_swap_guard
        if guard and self.scale is None:
            self.scale = torso_scale(observed_xy(person))
        observations, swapped = self._hip_assignment(person, t, guard)
        for original in person.joints:
            q = observations[original.index]
            estimate = original.model_copy(deep=True)
            if q.state != "observed" or q.position is None:
                self.states.pop(q.index, None)
            else:
                previous = self.states.get(original.index)
                dt = t-previous["time"] if previous else 0.
                old_position = previous.get("position") if previous else None
                if previous is None or dt <= 0 or dt > settings.max_gap_s:
                    previous = {"filters": [factory(settings.tracking_one_euro_mincutoff,
                        settings.tracking_one_euro_beta, settings.tracking_one_euro_dcutoff)
                        for _ in q.position]}
                    self.states[original.index] = previous
                estimate.position = [f(x, dt) for f,x in zip(previous["filters"], q.position)]
                estimate.confidence = q.confidence
                if guard and self.scale is not None and original.index in (11,12):
                    position = np.array(q.position[:2], dtype=float)/self.scale
                    previous["velocity"] = (position-old_position)/dt if old_position is not None and 0 < dt <= settings.max_gap_s else np.zeros(2)
                    previous["position"] = position
                previous["time"] = t
            estimates.append(estimate)
        conditioned = frame.model_copy(deep=True)
        next(p for p in conditioned.persons if p.person_id == person_id).joints = estimates
        return conditioned, {"enabled": True, "state": "conditioned", "smoother": "harmocap_one_euro",
            "implementation": source, "implementation_sha256": source_hash,
            "unit": frame.unit, "hip_labels_swapped": swapped,
            "hip_swap_guard_enabled": guard, "hip_swap_guard_available": guard and self.scale is not None,
            "acceleration_limited_joints": [],
            "interpretation": "HarMoCAP One-Euro with optional hip-label continuity repair; no hold, median or acceleration cap"}
