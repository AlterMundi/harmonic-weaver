"""Observed 2D wrist separation controls level; never invent missing body points."""
import math

from .kinematics import observed_xy, torso_scale


class BodyVolume:
    def __init__(self):
        self.reset()

    def reset(self):
        self.identity = None
        self.last_time = None
        self.level = 0.
        self.diagnostic = {"state": "missing", "ratio": None, "level": 0.,
                           "reason": "Faltan muñecas, hombros o caderas observados."}

    def update(self, frame, person_id, settings, now):
        identity = (frame.source_id, frame.stream_id, person_id) if frame else None
        if identity != self.identity:
            self.reset()
            self.identity = identity
        person = next((p for p in frame.persons if p.person_id == person_id), None) if frame else None
        points = observed_xy(person)
        scale = torso_scale(points)
        if scale is None or not all(math.isfinite(float(v)) for v in points[[9, 10]].flat):
            self.reset()
            return self.diagnostic
        ratio = float(math.dist(points[9], points[10])) / scale
        if not math.isfinite(ratio) or ratio > 10:
            self.reset()
            self.diagnostic["reason"] = "Revisá el encuadre y los puntos del torso antes de usar la apertura."
            return self.diagnostic
        target = max(0., min(1., (ratio-settings.closed_ratio)/(settings.open_ratio-settings.closed_ratio)))
        dt = max(0., now-self.last_time) if self.last_time is not None else 0.
        alpha = 1. if settings.smoothing_s == 0 else -math.expm1(-dt/settings.smoothing_s)
        self.level += alpha*(target-self.level)
        self.last_time = now
        self.diagnostic = {"state": "observed", "ratio": ratio, "level": self.level,
                           "target": target, "enabled": settings.enabled, "mode": settings.mode,
                           "reason": "Separación 2D de muñecas / longitud observada del torso."}
        return self.diagnostic
