"""Finite-window Fourier probes; not a PSD estimate or physical energy measurement."""

import math
from typing import Literal
import numpy as np
from pydantic import Field, model_validator
from ..contracts import Contract, Number


class Settings(Contract):
    frequencies_hz: list[Number] = Field(min_length=1, max_length=32)
    window: Literal["complete", "excitation", "tail"] = "complete"

    @model_validator(mode="after")
    def ordered(self):
        if any(f < 0 for f in self.frequencies_hz) or any(
            a >= b for a, b in zip(self.frequencies_hz, self.frequencies_hz[1:])
        ):
            raise ValueError(
                "Probe frequencies must be nonnegative and strictly increasing"
            )
        return self


def support(settings, sample_rate, excitation_frames, total_frames):
    settings = Settings.model_validate(settings)
    if any(f >= sample_rate / 2 for f in settings.frequencies_hz):
        raise ValueError("Probe frequencies must be strictly below Nyquist")
    start, stop = {
        "complete": (0, total_frames),
        "excitation": (0, excitation_frames),
        "tail": (excitation_frames, total_frames),
    }[settings.window]
    if stop <= start:
        raise ValueError("Spectral probe requires a nonempty window")
    return start, stop


class Accumulator:
    def __init__(self, settings, sample_rate, excitation_frames, total_frames):
        self.settings = Settings.model_validate(settings)
        self.start, self.stop = support(
            settings, sample_rate, excitation_frames, total_frames
        )
        self.sample_rate = sample_rate
        self.frequencies = np.asarray(self.settings.frequencies_hz, dtype=float)
        self.output = np.zeros(len(self.frequencies), dtype=complex)
        self.count = 0
        self.next_start = 0

    def add(self, start, output):
        output = np.asarray(output, dtype=float)
        if (
            type(start) is not int
            or start != self.next_start
            or output.ndim != 1
            or not np.isfinite(output).all()
        ):
            raise ValueError("Spectral probe requires contiguous finite output blocks")
        self.next_start += len(output)
        lo = max(start, self.start)
        hi = min(start + len(output), self.stop)
        if hi <= lo:
            return
        # Output sample represents the state after the step at (index+1)/sr.
        times = (np.arange(lo, hi, dtype=float) + 1) / self.sample_rate
        self.output += (
            np.exp(-2j * np.pi * self.frequencies[:, None] * times)
            @ output[lo - start : hi - start]
        )
        self.count += hi - lo

    def finish(self, events):
        count = self.stop - self.start
        if self.count != count:
            raise ValueError("Spectral probe output window is incomplete")
        selected = [i for i in events if self.start <= i < self.stop]
        rows = []
        for f, coefficient in zip(self.frequencies, self.output):
            # Timing indicator is one at each event, before the step at index/sr.
            angles = [-2 * math.pi * float(f) * i / self.sample_rate for i in selected]
            forcing = (
                complex(
                    math.fsum(math.cos(a) for a in angles),
                    math.fsum(math.sin(a) for a in angles),
                )
                / count
            )
            response = complex(coefficient) / count
            rows.append(
                {
                    "frequency_hz": float(f),
                    "event_real": forcing.real,
                    "event_imag": forcing.imag,
                    "event_coefficient_squared": abs(forcing) ** 2,
                    "output_real": response.real,
                    "output_imag": response.imag,
                    "output_coefficient_squared": abs(response) ** 2,
                }
            )
        return {
            "metric_version": "finite_window_fourier_mean_v1",
            "window": self.settings.window,
            "start_sample": self.start,
            "stop_sample": self.stop,
            "sample_count": count,
            "sample_rate": self.sample_rate,
            "event_count_in_window": len(selected),
            "input_clock": "impulse_before_step_index_over_sr",
            "output_clock": "state_after_step_index_plus_one_over_sr",
            "rows": rows,
            "limits": [
                "Rectangular finite window; coefficients divided by sample count",
                "Input is the unit event indicator, not impulse amplitude, force or input energy",
                "Squared complex coefficient is not PSD, watts or integrated band power",
                "Arbitrary probe frequencies need not be orthogonal; do not sum them as energy",
                "Finite-window leakage and transients remain; this is not a transfer-function estimate",
            ],
        }


def validate_probe(
    result, settings, sample_rate, excitation_frames, total_frames, events
):
    settings = Settings.model_validate(settings)
    start, stop = support(settings, sample_rate, excitation_frames, total_frames)
    selected = [i for i in events if start <= i < stop]
    count = stop - start
    expected = {
        "metric_version": "finite_window_fourier_mean_v1",
        "window": settings.window,
        "start_sample": start,
        "stop_sample": stop,
        "sample_count": count,
        "sample_rate": sample_rate,
        "event_count_in_window": len(selected),
        "input_clock": "impulse_before_step_index_over_sr",
        "output_clock": "state_after_step_index_plus_one_over_sr",
    }
    if any(
        type(result.get(k)) is not type(v) or result.get(k) != v
        for k, v in expected.items()
    ):
        raise ValueError(
            "Spectral probe support/clock differs from frozen configuration"
        )
    rows = result.get("rows", [])
    if len(rows) != len(settings.frequencies_hz):
        raise ValueError("Spectral probe frequency inventory differs")
    keys = {
        "frequency_hz",
        "event_real",
        "event_imag",
        "event_coefficient_squared",
        "output_real",
        "output_imag",
        "output_coefficient_squared",
    }
    for f, row in zip(settings.frequencies_hz, rows):
        if (
            set(row) != keys
            or any(
                type(v) not in (int, float) or not math.isfinite(v)
                for v in row.values()
            )
            or row["frequency_hz"] != f
        ):
            raise ValueError("Invalid spectral probe row/frequency")
        angles = [-2 * math.pi * f * i / sample_rate for i in selected]
        real = math.fsum(math.cos(a) for a in angles) / count
        imag = math.fsum(math.sin(a) for a in angles) / count
        if not math.isclose(
            row["event_real"], real, rel_tol=1e-12, abs_tol=1e-15
        ) or not math.isclose(row["event_imag"], imag, rel_tol=1e-12, abs_tol=1e-15):
            raise ValueError("Spectral probe input differs from calendar")
        for prefix in ("event", "output"):
            power = row[prefix + "_coefficient_squared"]
            expected_power = row[prefix + "_real"] ** 2 + row[prefix + "_imag"] ** 2
            if power < 0 or not math.isclose(
                power, expected_power, rel_tol=1e-12, abs_tol=1e-15
            ):
                raise ValueError("Spectral probe squared coefficient differs")
