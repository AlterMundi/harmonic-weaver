"""Offline, periodic multichannel Fourier surrogates; never a live filter.

Channels are scalar coordinate displacements, not persons or joint blocks.
Shared phases preserve every complex cross-spectrum (second-order circular
relations). Neither control preserves arbitrary nonlinear organization.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .adapter import SIGNALS, _index_units, read_models
from .synthetic import BASE_POSE, motion_frame


@dataclass(frozen=True)
class FourierConfig:
    samples: int = 480
    hz: float = 60.
    seeds: tuple[int, ...] = (7, 19, 41)


def phase_surrogate(values, *, seed: int, shared: bool):
    """Preserve rFFT magnitudes, DC and real Nyquist; randomize interior bins.

    Needs the entire regularly sampled, finite N×C record. No repeated periodic
    endpoint, window, padding, clipping or detrending is applied. Missingness and
    irregular observations must be handled explicitly before calling this API.
    """
    x = np.asarray(values, dtype=float)
    if x.ndim != 2 or x.shape[0] < 4 or x.shape[1] < 1 or not np.isfinite(x).all():
        raise ValueError("expected finite samples×channels with at least four samples")
    coefficients = np.fft.rfft(x, axis=0)
    stop = len(coefficients) - (x.shape[0] % 2 == 0)
    # Draw channel-first so the first independent channel equals the shared
    # draw for the same seed. This makes a one-channel negative control exact.
    phases = np.random.default_rng(seed).uniform(
        -np.pi, np.pi, size=(1 if shared else x.shape[1], stop - 1)).T
    coefficients[1:stop] *= np.exp(1j * phases)
    return np.fft.irfft(coefficients, n=len(x), axis=0)


def spectral_checks(original, transformed):
    """Errors normalized by global maximum; zero input has denominator one."""
    a, b = np.fft.rfft(original, axis=0), np.fft.rfft(transformed, axis=0)
    cross_a = a[:, :, None] * a[:, None, :].conj()
    cross_b = b[:, :, None] * b[:, None, :].conj()
    power_scale = max(float(np.max(np.abs(a) ** 2)), 1e-30)
    cross_scale = max(float(np.max(np.abs(cross_a))), 1e-30)
    return {
        "power_max_relative_error": float(np.max(np.abs(abs(a)**2 - abs(b)**2)) / power_scale),
        "cross_spectrum_max_relative_change": float(np.max(np.abs(cross_a-cross_b)) / cross_scale),
        "mean_max_absolute_error": float(np.max(np.abs(np.mean(original, axis=0)-np.mean(transformed, axis=0)))),
        "third_moment_first_channel_original": float(np.mean(np.asarray(original)[:, 0]**3)),
        "third_moment_first_channel_transformed": float(np.mean(np.asarray(transformed)[:, 0]**3)),
    }


def scenario(name, config=FourierConfig()):
    """Return periodic displacements and their explicit COCO joint/axis map."""
    if config.samples < 64 or not np.isfinite(config.hz) or config.hz <= 0:
        raise ValueError("bank requires at least 64 samples and positive finite hz")
    t = np.arange(config.samples) / config.samples
    a = np.sin(2*np.pi*3*t) + .55*np.sin(2*np.pi*7*t) + .35*np.sin(2*np.pi*10*t)
    b = np.cos(2*np.pi*3*t) + .55*np.cos(2*np.pi*7*t) + .35*np.cos(2*np.pi*10*t)
    if name == "coupled_multitone":
        # Elbow and wrist displacements are exactly proportional on both sides;
        # relative velocity remains nonzero because wrist amplitude is larger.
        return .018*np.column_stack([a, b, 2*a, 2*b, a, b, 2*a, 2*b]), (
            (7, 0), (7, 1), (9, 0), (9, 1), (8, 0), (8, 1), (10, 0), (10, 1))
    if name == "single_channel":
        return (.025*a)[:, None], ((9, 0),)
    if name == "static":
        return np.zeros((config.samples, 4)), ((9, 0), (9, 1), (10, 0), (10, 1))
    raise ValueError(f"unknown Fourier scenario: {name}")


def frames_from_channels(values, channel_map, *, hz=60.):
    """Reusable MotionFrame fixture adapter; conditions share unit identities."""
    x = np.asarray(values, dtype=float)
    if (x.ndim != 2 or x.shape[1] != len(channel_map) or not np.isfinite(x).all()
            or not np.isfinite(hz) or hz <= 0):
        raise ValueError("invalid finite channel array, map or sampling rate")
    if len(set(channel_map)) != len(channel_map) or any(
            joint not in range(17) or axis not in (0, 1) for joint, axis in channel_map):
        raise ValueError("channel map must contain unique COCO-17 2D coordinates")
    frames = []
    for k, row in enumerate(x):
        frame = motion_frame(k/hz, k, stream="fourier")
        for delta, (joint, axis) in zip(row, channel_map):
            frame.persons[0].joints[joint].position[axis] = float(BASE_POSE[joint, axis]+delta)
        frames.append(frame)
    return frames


def common_three(records, signal):
    """One intersection across original/shared/independent, never pairwise means."""
    indexed = {name: _index_units(rows) for name, rows in records.items()}
    keys = set.intersection(*(set(rows) for rows in indexed.values()))
    values = {name: [] for name in indexed}
    for key in sorted(keys):
        cells = {name: rows[key]["signals"].get(signal) for name, rows in indexed.items()}
        if not all(cell and cell["state"] == "observed" for cell in cells.values()):
            continue
        if len({cell["unit"] for cell in cells.values()}) != 1:
            raise ValueError("units differ")
        for name, cell in cells.items():
            values[name].append(cell["value"])
    n = len(next(iter(values.values())))
    summaries = {name: {"observed": sum(
        row["signals"].get(signal, {}).get("state") == "observed" for row in records[name]),
        "common_mean": float(np.mean(v)) if n else None,
        "common_std": float(np.std(v)) if n else None} for name, v in values.items()}
    return {"common_observed": n, "total": len(next(iter(records.values()))),
            "conditions": summaries,
            "common_shared_independent_mae": float(np.mean(np.abs(
                np.asarray(values["shared"])-values["independent"]))) if n else None,
            "common_mae_from_original": {name: float(np.mean(np.abs(
                np.asarray(v)-values["original"]))) if n else None
                for name, v in values.items() if name != "original"}}


def fourier_bench(config=FourierConfig()):
    results = []
    for name in ("coupled_multitone", "single_channel", "static"):
        original, channel_map = scenario(name, config)
        for seed in config.seeds:
            conditions = {"original": original,
                "shared": phase_surrogate(original, seed=seed, shared=True),
                "independent": phase_surrogate(original, seed=seed, shared=False)}
            # Only descriptive facade outputs, not three independent scientific
            # estimators: multiple algorithm mappings compute the same signals.
            records = {label: read_models(frames_from_channels(x, channel_map, hz=config.hz),
                        algorithms=("relational",))["relational"] for label, x in conditions.items()}
            results.append({"scenario": name, "seed": seed, "channels": channel_map,
                "spectral_checks": {label: spectral_checks(original, x)
                                    for label, x in conditions.items() if label != "original"},
                "descriptors": {signal: common_three(records, signal) for signal in SIGNALS},
                "shared_independent_coordinate_max_difference": float(np.max(np.abs(
                    conditions["shared"]-conditions["independent"])))})
    return {"config": asdict(config), "operation": "offline whole-record periodic rFFT",
            "channel_semantics": "scalar joint coordinate displacements in camera 2D",
            "results": results}
