"""Motion descriptors and their editable default musical response.

Analysis advances only on new source observations. Envelopes advance on the
control clock; repeated display ticks cannot manufacture motion or impulses.
"""
import math

import numpy as np

from .analysis_math import AngularMode, RelativeMode
from .collective import CausalSubspace, DeploymentEvents, LaggedPropagation
from .contracts import FeatureFrame, Signal
from .kinematics import Kinematics, PARENTS, ZONES
from .joint_filter import JointMotionFilter
from .legacy import FrozenBaseline, baseline_module


def finite_mean(values):
    values = np.asarray(values)
    return float(values.mean()) if np.isfinite(values).all() else None


class MotionModel:
    def __init__(self, preset, scale=None):
        self.preset = preset.model_copy(deep=True)
        self.scale = scale
        self.reset()

    def reset(self):
        settings = self.preset.algorithm
        self.baseline = FrozenBaseline(self.preset) if settings.id == "baseline" else None
        self.joint_filter = JointMotionFilter(settings, self.scale)
        self.conditioned_frame = None
        self.filter_diagnostics = {"enabled": False}
        self.kinematics = Kinematics(settings, self.scale)
        self.relative = [[RelativeMode(settings) for _ in range(2)] for _ in ZONES]
        self.angular = [[AngularMode(settings) for _ in range(2)] for _ in ZONES]
        self.subspace = CausalSubspace(settings)
        self.events = DeploymentEvents(settings)
        self.propagation = LaggedPropagation(settings)
        self.global_angle = AngularMode(settings)
        self.plucks = [baseline_module().Pluck() for _ in ZONES]
        self.frame = None
        self.person_id = None
        self.features = None
        self.responses = {}

    def observe(self, frame, person_id, now):
        if self.frame is not None:
            discontinuity = (frame.stream_id != self.frame.stream_id or person_id != self.person_id
                             or frame.source_time_s <= self.frame.source_time_s
                             or frame.source_time_s-self.frame.source_time_s > self.preset.algorithm.max_gap_s)
            if discontinuity:
                self.reset()
        self.frame, self.person_id = frame, person_id
        frame, self.filter_diagnostics = self.joint_filter.push(frame, person_id)
        self.conditioned_frame = frame if self.preset.algorithm.tracking_filter_enabled else None
        if self.baseline:
            features = self.baseline.observe(frame, person_id, now)
            features.diagnostics["tracking_filter"] = self.filter_diagnostics
            return features
        person = next((p for p in frame.persons if p.person_id == person_id), None)
        kin = self.kinematics.push(frame.source_time_s, person)
        t, settings = frame.source_time_s, self.preset.algorithm
        signals, details, accelerations = {}, {}, {}

        def put(name, value, unit="1", reason="missing observation or warming history"):
            valid = value is not None and math.isfinite(value)
            signals[name] = Signal(value=float(value) if valid else None, unit=unit,
                                   state="observed" if valid else "missing", reason=None if valid else reason)

        for z, (joints, parents) in enumerate(zip(ZONES, PARENTS)):
            prefix = f"zone.{z+1}."
            speed = finite_mean(np.linalg.norm(kin["velocity"][list(joints)], axis=1))
            acceleration = finite_mean(np.linalg.norm(kin["acceleration"][list(joints)], axis=1))
            put(prefix+"speed", speed, "T/s")
            put(prefix+"acceleration", acceleration, "T/s2")
            accelerations[z+1] = acceleration
            for name in ("position_error", "velocity_error"):
                put(prefix+name, finite_mean(kin[name][list(joints)]), "T")
            relations, angles = [], []
            for side, (joint, parent) in enumerate(zip(joints, parents)):
                relative = kin["velocity"][joint]-kin["velocity"][parent]
                relations.append(self.relative[z][side].push(t, relative if np.isfinite(relative).all() else None))
                vector = kin["position"][joint]-kin["position"][parent]
                # Internal angles at hip/shoulder/knee/elbow need both adjacent
                # segments. COCO-17 lacks hands/feet: wrists/ankles expose distal
                # segment orientation, never an invented wrist/ankle joint angle.
                children = {11:13, 12:14, 5:7, 6:8, 13:15, 14:16, 7:9, 8:10}
                if joint in children:
                    proximal = vector
                    vector = kin["position"][children[joint]]-kin["position"][joint]
                    vector = np.array([proximal @ vector, proximal[0]*vector[1]-proximal[1]*vector[0]])
                angles.append(self.angular[z][side].push(t, vector if np.isfinite(vector).all() else None))
            details[str(z+1)] = {"relations": relations, "angles": angles,
                                "angle_kind":"internal joint angle" if z < 4 else "distal segment orientation (COCO-17)"}
            for name in ("I", "R", "A"):
                vals = [r.get(name) for r in relations]
                put(prefix+name, finite_mean(vals) if all(v is not None for v in vals) else None)
            for output, key, unit in (("angle_deg", "angle_deg", "deg"),
                                      ("angular_velocity", "velocity_deg_s", "deg/s"),
                                      ("angular_error", "prediction_error_deg", "deg")):
                vals = [a.get(key) for a in angles]
                put(prefix+output, finite_mean(vals) if all(v is not None for v in vals) else None, unit)
            angular_speeds = [a.get("velocity_deg_s") for a in angles]
            put(prefix+"angular_speed", finite_mean([abs(v) for v in angular_speeds])
                if all(v is not None for v in angular_speeds) else None, "deg/s")
            cfg = self.preset.response.zones[z]
            factor = cfg.sensitivity/(1+self.preset.response.core_falloff*cfg.distance)
            gain = min(1., speed*factor/cfg.speed_range) if speed is not None else None
            error = signals[prefix+"velocity_error"].value
            drive = None if error is None else min(1., 2*error*factor/(settings.horizon_s**2*cfg.accel_range))
            if settings.id == "relational":
                interference = signals[prefix+"I"].value
                drive = None if interference is None else -interference
            elif settings.id == "angular":
                angular_error = signals[prefix+"angular_error"].value
                drive = None if angular_error is None else max(-1., min(1., angular_error/180))
            if drive is not None:
                drive *= 1-self.preset.response.snap
            if gain is None or factor == 0:
                self.plucks[z] = baseline_module().Pluck()
            elif acceleration is not None and self.preset.response.pluck_enabled:
                self.plucks[z].observe(acceleration*factor/cfg.accel_range,
                                      self.preset.response.impulse_threshold, now,
                                      self.preset.response.attack_ms/1000, self.preset.response.tail_ms/1000)
            self.responses[z] = gain, drive

        event_data = self.events.push(t, accelerations)
        propagation = self.propagation.push(t, np.array([kin["velocity"][list(joints)].mean(axis=0) for joints in ZONES])) if settings.id == "collective" else {"state":"missing", "reason":"enable collective model for delayed propagation"}
        for z, event in event_data.items():
            put(f"zone.{z}.event", float(event["candidate"]) if event["state"] == "observed" else None)
            region = propagation.get("regions", {}).get(str(z), {})
            put(f"zone.{z}.center_score", region.get("score"), reason="propagation evidence not yet available")
        selected = kin["velocity"][settings.joints]
        speed_support = np.isfinite(selected).all(axis=1)
        speed_selected = selected[speed_support] if settings.collective_support == "observed" else selected
        put("global.speed", finite_mean(np.linalg.norm(speed_selected, axis=1)) if len(speed_selected) else None, "T/s")
        trunk = kin["raw"][[5, 6]].mean(axis=0)-kin["raw"][[11, 12]].mean(axis=0)
        orientation = self.global_angle.push(t, trunk if np.isfinite(trunk).all() else None)
        put("global.angle_deg", orientation.get("angle_deg"), "deg")
        collective = self.subspace.push(t, selected.ravel(), [f"{j}.{axis}" for j in settings.joints for axis in "xy"])
        collective["speed_support"] = [joint for joint, valid in zip(settings.joints, speed_support) if valid]
        collective_reason = collective.get("reason") or "requested collective descriptor not established"
        put("collective.rank", collective.get("rank"), reason=collective_reason)
        put("collective.residual", collective.get("residual"), reason=collective_reason)
        principal = collective.get("principal_angles_deg")
        put("collective.change", max(principal) if principal else None, "deg", reason=collective_reason if collective.get("state") != "observed" else "no previous collective basis for angle comparison")
        for i in range(12):
            amplitudes = collective.get("amplitudes", [])
            put(f"collective.mode.{i+1}", amplitudes[i] if i < len(amplitudes) else None, "T/s",
                reason=collective_reason if collective.get("state") != "observed" else "requested mode exceeds established collective components")
        if settings.id == "collective":
            residual = collective.get("residual")
            for z, (gain, _) in self.responses.items():
                self.responses[z] = gain, None if residual is None else min(1., residual)*(1-self.preset.response.snap)
        self.features = FeatureFrame(source_time_s=t, available_monotonic_s=now, person_id=person_id,
            algorithm_id=settings.id, signals=signals, diagnostics={"regions":details, "collective":collective,
            "events":event_data, "propagation":propagation, "scale":self.scale, "reference":settings.reference,
            "interpretation":"kinematic descriptors; no causal or physiological efficacy claim"})
        return self.tick(now)

    def tick(self, now):
        if self.baseline:
            features = self.baseline.tick(now)
            features.diagnostics["tracking_filter"] = self.filter_diagnostics
            return features
        if self.features is None:
            return FeatureFrame(source_time_s=0., available_monotonic_s=now, person_id=None,
                                algorithm_id=self.preset.algorithm.id)
        features = self.features.model_copy(deep=True)
        features.available_monotonic_s = now
        features.diagnostics["tracking_filter"] = self.filter_diagnostics
        for z, (gain, drive) in self.responses.items():
            if gain is not None and self.preset.response.pluck_enabled:
                gain = self.plucks[z].gain(now, gain)
            for key, value, unit in (("gain", None if gain is None else .45*gain, "1"),
                                     ("detune", drive, "1"),
                                     ("phase_deg", None if drive is None else drive*self.preset.response.phase_depth, "deg")):
                features.signals[f"zone.{z+1}.{key}"] = Signal(value=value, unit=unit,
                    state="missing" if value is None else "observed")
        return features
