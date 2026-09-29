"""Past-only subspace estimates. These are geometric descriptors, not HIT proofs."""
from collections import deque

import numpy as np


def align_basis(basis, previous):
    """Orthogonal Procrustes keeps coordinates continuous within the same span."""
    if previous is None or previous.shape != basis.shape:
        result = basis.copy()
        for column in range(result.shape[1]):
            index = np.argmax(np.abs(result[:, column]))
            if result[index, column] < 0:
                result[:, column] *= -1
        return result
    left, _, right = np.linalg.svd(basis.T @ previous, full_matrices=False)
    return basis @ (left @ right)


def principal_angles(first, second):
    if first.shape != second.shape:
        return None
    cosines = np.linalg.svd(first.T @ second, compute_uv=False)
    return np.arccos(np.clip(cosines, -1, 1))


class CausalSubspace:
    def __init__(self, settings):
        self.settings = settings
        self.history = deque(maxlen=2048)
        self.previous_basis = None
        self.support = None

    def reset(self):
        self.history.clear()
        self.previous_basis = None
        self.support = None

    def push(self, t, vector, feature_ids):
        vector = np.asarray(vector, dtype=float)
        support = tuple(feature_ids)
        if vector.ndim != 1 or len(vector) != len(support):
            raise ValueError("collective feature IDs must match the vector")
        if not np.isfinite(vector).all():
            self.reset()
            return {"state": "missing", "reason": "missing collective support"}
        if support != self.support or (self.history and (
                t <= self.history[-1][0] or t-self.history[-1][0] > self.settings.max_gap_s)):
            self.reset()
            self.support = support
        while self.history and self.history[0][0] < t-self.settings.window_s:
            self.history.popleft()
        result = {"state": "missing", "reason": "warming collective window", "support": list(support),
                  "past_samples": len(self.history)}
        k = min(self.settings.components, len(vector))
        if len(self.history) >= max(k+2, 6):
            past = np.stack([v for _, v in self.history])
            mean = past.mean(axis=0)
            _, singular, vt = np.linalg.svd(past-mean, full_matrices=False)
            rank = int(np.sum(singular > self.settings.noise_velocity*np.sqrt(len(past))))
            k = min(k, rank)
            result.update(mean=mean.tolist(), singular_values=singular.tolist(), rank=rank)
            if k == 0:
                result["reason"] = "no established collective mode"
                self.previous_basis = None
            elif k < len(singular) and singular[k] > 0 and (singular[k-1]-singular[k])/singular[k-1] < .05:
                result["reason"] = "degenerate component boundary"
                self.previous_basis = None
            else:
                basis = align_basis(vt[:k].T, self.previous_basis)
                angles = principal_angles(self.previous_basis, basis) if self.previous_basis is not None else None
                centered = vector-mean
                amplitudes = basis.T @ centered
                residual = centered-basis @ amplitudes
                projector = basis @ basis.T
                result.update(state="observed", reason=None, components=k,
                              basis=basis.tolist(), projector=projector.tolist(), amplitudes=amplitudes.tolist(),
                              residual_vector=residual.tolist(),
                              residual=float(np.linalg.norm(residual)/max(np.linalg.norm(centered), self.settings.noise_velocity)),
                              principal_angles_deg=None if angles is None else np.degrees(angles).tolist(),
                              history_end_s=self.history[-1][0])
                self.previous_basis = basis
        # The observation under test never contributes to its own fitted subspace.
        self.history.append((t, vector.copy()))
        return result


class DeploymentEvents:
    """Independent regional candidates; zero, one or many can coexist."""
    def __init__(self, settings):
        self.settings = settings
        self.last_event = {}
        self.armed = {}

    def push(self, t, accelerations):
        output = {}
        noise = self.settings.noise_velocity/self.settings.derivative_window_s
        for region, acceleration in accelerations.items():
            if acceleration is None or not np.isfinite(acceleration):
                self.last_event.pop(region, None)
                self.armed.pop(region, None)
                output[region] = {"state": "missing", "candidate": False}
                continue
            ratio = abs(acceleration)/noise
            if ratio < self.settings.event_threshold*.5:
                self.armed[region] = True
            last = self.last_event.get(region, -float("inf"))
            if self.armed.get(region, True) and ratio >= self.settings.event_threshold and t-last >= self.settings.refractory_s:
                self.last_event[region] = t
                self.armed[region] = False
                last = t
            output[region] = {"state": "observed", "candidate": t-last < self.settings.event_duration_s,
                              "detectability": ratio, "event_time_s": last if np.isfinite(last) else None,
                              "interpretation": "kinematic candidate; not intention or causal origin"}
        return output
