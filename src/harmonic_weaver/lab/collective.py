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
        self.effective_support = None

    def reset(self):
        self.history.clear()
        self.previous_basis = None
        self.support = None
        self.effective_support = None

    def push(self, t, vector, feature_ids):
        vector = np.asarray(vector, dtype=float)
        support = tuple(feature_ids)
        if vector.ndim != 1 or len(vector) != len(support):
            raise ValueError("collective feature IDs must match the vector")
        adaptive = self.settings.collective_support == "observed"
        if not np.isfinite(vector).any() or (not adaptive and not np.isfinite(vector).all()):
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
        past = np.stack([v for _, v in self.history]) if self.history else np.empty((0, len(vector)))
        mask = np.isfinite(vector) & np.isfinite(past).all(axis=0)
        effective = tuple(np.array(support)[mask])
        if effective != self.effective_support:
            self.previous_basis = None
            self.effective_support = effective
        result.update(support=list(effective), requested_support=list(support),
                      excluded_support=[name for name, present in zip(support, mask) if not present],
                      support_policy=self.settings.collective_support)
        k = min(self.settings.components, len(effective))
        if len(effective) < 2:
            result["reason"] = "insufficient common observed collective support"
        elif len(self.history) >= max(k+2, 6):
            past = past[:, mask]
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
                centered = vector[mask]-mean
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


class LaggedPropagation:
    """Delayed predictive support, compared with each destination's own history.

    Select a lag on a chronological validation tail of the *past* window. Fit
    with past targets only; evaluate on the new observation before appending it.
    Zero/multiple positive region scores are allowed. This is not causality.
    """
    def __init__(self, settings):
        self.settings = settings
        self.history = deque(maxlen=2048)
        self.models = {}
        self.last_fit = -float("inf")
        self.errors = {}

    def _fit(self, x, y):
        mean, scale = x.mean(axis=0), np.maximum(x.std(axis=0), self.settings.noise_velocity)
        design = np.column_stack([np.ones(len(x)), (x-mean)/scale])
        penalty = np.eye(design.shape[1])*self.settings.ridge
        penalty[0, 0] = 0
        weights = np.linalg.solve(design.T@design+penalty, design.T@y)
        return mean, scale, weights

    @staticmethod
    def _predict(model, x):
        mean, scale, weights = model
        return np.r_[1., (x-mean)/scale]@weights

    def _train(self, t, regions):
        times = np.array([row[0] for row in self.history])
        values = np.stack([row[1] for row in self.history])
        lags = sorted({max(.02, min(1., self.settings.lag_s*factor)) for factor in (.5, 1., 2.)})
        candidates = {}
        for lag in lags:
            indices = np.searchsorted(times, times-lag+1e-9, side="right")-1
            valid = indices >= 0
            rows = np.flatnonzero(valid)
            rows = rows[times[rows]-times[indices[rows]] <= lag+self.settings.max_gap_s]
            if len(rows) < 16:
                continue
            split = max(10, int(len(rows)*.7))
            if len(rows)-split < 4:
                continue
            previous, actual = values[indices[rows]], values[rows]
            for target in range(regions):
                for source in [None]+[s for s in range(regions) if s != target]:
                    x = previous[:, target] if source is None else np.concatenate([previous[:, target], previous[:, source]], axis=1)
                    y = actual[:, target]
                    fitted = self._fit(x[:split], y[:split])
                    predicted = np.stack([self._predict(fitted, row) for row in x[split:]])
                    loss = float(np.mean((predicted-y[split:])**2))
                    key = source, target
                    if key not in candidates or loss < candidates[key][0]:
                        candidates[key] = loss, lag, self._fit(x, y)
        self.models = candidates
        self.last_fit = t

    def push(self, t, velocities):
        velocities = np.asarray(velocities, dtype=float)
        if velocities.ndim != 2 or min(velocities.shape,default=0)==0 or not np.isfinite(velocities).all() or not np.isfinite(t):
            self.history.clear(); self.models.clear(); self.errors.clear()
            return {"state":"missing", "reason":"missing regional support"}
        if self.history and (velocities.shape!=self.history[-1][1].shape or
                t <= self.history[-1][0] or t-self.history[-1][0] > self.settings.max_gap_s):
            self.history.clear(); self.models.clear(); self.errors.clear()
        while self.history and self.history[0][0] < t-self.settings.window_s:
            self.history.popleft()
        regions = len(velocities)
        if len(self.history) >= 20 and (not self.models or t-self.last_fit >= self.settings.propagation_interval_s):
            self._train(t, regions)
        result = {"state":"missing", "reason":"warming delayed predictor", "regions":{},
                  "interpretation":"delayed predictive support, not causal origin",
                  "history_end_s":self.history[-1][0] if self.history else None}
        predictions = {}
        for (source, target), (_, lag, model) in self.models.items():
            past = next((v for pt, v in reversed(self.history) if pt <= t-lag+1e-9 and t-pt <= lag+self.settings.max_gap_s), None)
            if past is None:
                continue
            x = past[target] if source is None else np.r_[past[target], past[source]]
            prediction = self._predict(model, x)
            squared_error = float(np.mean((prediction-velocities[target])**2))
            key = source, target
            errors = self.errors.setdefault(key, deque(maxlen=2048))
            errors.append((t, squared_error))
            while errors and errors[0][0] < t-self.settings.window_s:
                errors.popleft()
            predictions[key] = dict(errors), lag
        for source in range(regions):
            support = []
            for target in range(regions):
                baseline = predictions.get((None, target))
                augmented = predictions.get((source, target))
                if baseline is None or augmented is None:
                    continue
                common=sorted(baseline[0].keys() & augmented[0].keys())
                if len(common)<5:continue
                base_error=float(np.mean([baseline[0][stamp] for stamp in common]))
                error=float(np.mean([augmented[0][stamp] for stamp in common]))
                gain = (base_error-error)/max(base_error, self.settings.noise_velocity**2)
                support.append({"target":target+1, "improvement":float(np.clip(gain,-1,1)),
                                "lag_s":augmented[1], "own_history_error":base_error,
                                "augmented_error":error, "evaluation_samples":len(common),
                                "own_history_available_samples":len(baseline[0]),
                                "augmented_available_samples":len(augmented[0]),
                                "evaluation_start_s":common[0],"evaluation_end_s":common[-1],
                                "support":"same target timestamps for both predictors"})
            if support:
                result["regions"][str(source+1)] = {"score":float(np.mean([max(0.,s["improvement"]) for s in support])),
                                                   "support":support}
        if result["regions"]:
            result.update(state="observed", reason=None)
        self.history.append((t, velocities.copy()))
        return result
