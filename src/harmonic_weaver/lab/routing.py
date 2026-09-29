"""Prepared signal-to-voice matrix: explicit mixes, units and one final writer.

The topology is a two-layer DAG (features -> mixed destinations). It cannot
contain feedback cycles; resonators, when implemented, own their internal state.
No OSC addresses or Python expressions are accepted from a preset.
"""
from dataclasses import dataclass
import math

from .contracts import Preset


def signal_catalog():
    catalog = {}
    for zone in range(1, 7):
        for name, unit in {"gain": "1", "detune": "1", "phase_deg": "deg", "speed": "T/s",
                           "acceleration": "T/s2", "position_error": "T", "velocity_error": "T",
                           "I": "1", "R": "1", "A": "1", "angle_deg": "deg",
                           "angular_velocity": "deg/s", "angular_error": "deg",
                           "event": "1", "center_score": "1"}.items():
            catalog[f"zone.{zone}.{name}"] = unit
    catalog.update({"collective.residual": "1", "collective.change": "deg", "collective.rank": "1",
                    "global.speed": "T/s", "global.angle_deg": "deg"})
    for mode in range(1, 13):
        catalog[f"collective.mode.{mode}"] = "T/s"
    return catalog


@dataclass(frozen=True)
class VoiceTarget:
    id: int
    frequency_hz: float
    gain: float
    phase_deg: float
    pan: float
    shape: float
    release_s: float


class PreparedRoutes:
    def __init__(self, preset: Preset):
        self.preset = preset.model_copy(deep=True)
        self.catalog = signal_catalog()
        self.routes = [r for r in self.preset.routes if r.enabled]
        self.smoothed = {}
        self.expression_history = {}
        self.transient_envelopes = {}
        self.last_time = None
        for route in self.routes:
            for term in route.terms:
                if term.source not in self.catalog:
                    raise ValueError(f"unknown signal: {term.source}")
                if term.input_unit != self.catalog[term.source]:
                    raise ValueError(f"{term.source}: expected unit {self.catalog[term.source]}, got {term.input_unit}")
            if route.target == "gain" and (route.clamp_min < 0 or route.clamp_max > 2):
                raise ValueError("gain route must be bounded within 0..2")
            if route.target == "pan" and (route.clamp_min < -1 or route.clamp_max > 1):
                raise ValueError("pan route must be bounded within -1..1")
            if route.target == "detune" and (route.clamp_min < -1 or route.clamp_max > 1):
                raise ValueError("detune route must be bounded within -1..1")
            if route.target == "phase_deg" and (route.clamp_min < -360 or route.clamp_max > 360):
                raise ValueError("phase route must be bounded within -360..360 degrees")
        for voice in self.preset.voices:
            route = next((r for r in self.routes if r.voice == voice.id and r.target == "detune"), None)
            low = voice.detune + (route.clamp_min if route else 0)
            high = voice.detune + (route.clamp_max if route else 0)
            if self.preset.fundamental_hz*(voice.ratio+low/2) < 1:
                raise ValueError(f"voice {voice.id}: pitch range includes non-positive or sub-1 Hz frequencies")
            if self.preset.fundamental_hz*(voice.ratio+high/2) > 20000:
                raise ValueError(f"voice {voice.id}: pitch range exceeds 20 kHz")

    def reset(self):
        self.smoothed.clear()
        self.expression_history.clear()
        self.transient_envelopes.clear()
        self.last_time = None

    def evaluate(self, features, now):
        dt = max(0., now-self.last_time) if self.last_time is not None else None
        self.last_time = now
        values, invalid, diagnostics = {}, set(), []
        for route in self.routes:
            terms = []
            missing = False
            for term in route.terms:
                signal = features.signals.get(term.source)
                if signal is None or signal.state != "observed" or signal.value is None:
                    missing = True
                    if route.missing == "zero":
                        terms.append(0.)
                    continue
                if signal.unit != term.input_unit:
                    missing = True
                    invalid.add(route.voice)
                    diagnostics.append(f"unit mismatch at {term.source}")
                    continue
                x = signal.value
                if abs(x) < term.deadband:
                    x = 0.
                x = abs(x) if term.absolute else x
                try:
                    x = math.copysign(abs(x)**term.exponent, x) if term.weight else 0.
                    value = x*term.weight+term.offset
                except OverflowError:
                    value = float("nan")
                if not math.isfinite(value):
                    invalid.add(route.voice)
                    diagnostics.append(f"numeric overflow at {term.source}")
                    continue
                terms.append(value)
            if missing and route.missing == "silence":
                invalid.add(route.voice)
                self.smoothed.pop(route.id, None)
                continue
            if not terms:
                invalid.add(route.voice)
                continue
            if route.mix == "sum":
                value = sum(terms)
            elif route.mix == "mean":
                value = sum(terms)/len(terms)
            elif route.mix == "max":
                value = max(terms)
            else:
                value = math.prod(terms)
            if not math.isfinite(value):
                invalid.add(route.voice)
                diagnostics.append(f"numeric overflow in route {route.id}")
                continue
            value = max(route.clamp_min, min(route.clamp_max, value))
            if route.smoothing_s and dt is not None and route.id in self.smoothed:
                alpha = -math.expm1(-dt/route.smoothing_s)
                value = self.smoothed[route.id]+alpha*(value-self.smoothed[route.id])
            self.smoothed[route.id] = value
            values[(route.voice, route.target)] = value
        solo = any(v.solo for v in self.preset.voices)
        targets = []
        for voice in self.preset.voices:
            drive = values.get((voice.id, "gain"), 0.)
            # Transient contrast around a causal per-voice moving baseline.
            # First sample seeds history: seeks/resets must not invent attacks.
            if voice.id in invalid:
                self.expression_history.pop(voice.id, None)
                self.transient_envelopes.pop(voice.id, None)
            else:
                previous = self.expression_history.get(voice.id, drive)
                alpha = -math.expm1(-dt/self.preset.expression_window_s) if dt is not None else 1.
                baseline = previous + alpha*(drive-previous)
                self.expression_history[voice.id] = baseline
                rising = max(0., drive-baseline)
                decay = math.exp(-dt/self.preset.transient_decay_s) if dt is not None else 0.
                transient = max(self.transient_envelopes.get(voice.id, 0.)*decay,
                                min(1., 4*rising))
                if transient < 1e-6:
                    transient = 0.
                self.transient_envelopes[voice.id] = transient
                if self.preset.expression > 0 and drive > 0:
                    drive = max(0., min(1., drive + 4*self.preset.expression*(drive-baseline)))
                elif self.preset.expression < 0 and drive > 0:
                    # Preserve the attenuating negative side the player liked.
                    drive = min(1., drive) ** math.exp(-2.5*self.preset.expression)
                drive = (1-self.preset.transient_mix)*drive + self.preset.transient_mix*transient
            gain = drive*voice.gain*self.preset.master
            if voice.id in invalid or voice.muted or (solo and not voice.solo):
                gain = 0.
            detune = voice.detune+values.get((voice.id, "detune"), 0.)
            targets.append(VoiceTarget(
                id=voice.id, frequency_hz=self.preset.fundamental_hz*(voice.ratio+detune/2),
                gain=min(1., max(0., gain)), phase_deg=voice.phase_deg+values.get((voice.id, "phase_deg"), 0.),
                pan=max(-1., min(1., voice.pan+values.get((voice.id, "pan"), 0.))), shape=voice.shape,
                release_s=self.preset.release_ms/1000))
        return targets, {"invalid_voices": sorted(invalid), "messages": diagnostics}
