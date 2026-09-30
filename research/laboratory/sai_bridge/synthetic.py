"""Original synthetic constructions, attributed to the questions in Sai's banks.

The 3D arrays are synthetic truth, never an estimate from MotionFrame's 2D view.
No Sai source code is copied: the numerical contrasts are independently built.
"""
from __future__ import annotations

import math
from random import Random

import numpy as np

from harmonic_weaver.lab.contracts import Joint, MotionFrame, Person

TAU = 2 * math.pi
BASE_POSE = np.array([
    [.50, .16], [.47, .15], [.53, .15], [.43, .17], [.57, .17],
    [.42, .29], [.58, .29], [.34, .42], [.66, .42], [.28, .55],
    [.72, .55], [.45, .55], [.55, .55], [.44, .74], [.56, .74],
    [.43, .94], [.57, .94],
], dtype=float)


def motion_frame(t: float, sequence: int, *, left=None, right=None,
                 shift=(0., 0.), states=None, stream="synthetic", person="p0",
                 availability_lag=.01) -> MotionFrame:
    """A COCO-17 isotropic 2D frame with explicit source and availability clocks."""
    points = BASE_POSE.copy() + np.asarray(shift)
    if left is not None:
        points[9] = left
    if right is not None:
        points[10] = right
    states = states or {}
    joints = [Joint(index=i, position=None if states.get(i) == "missing" else points[i].tolist(),
                    confidence=0. if states.get(i) == "missing" else 1.,
                    state=states.get(i, "observed")) for i in range(17)]
    return MotionFrame(source_id="sai_bridge", stream_id=stream, sequence=sequence,
                       source_time_s=float(t), available_monotonic_s=float(t + availability_lag),
                       timestamp_origin="synthetic", width=640, height=480,
                       persons=[Person(person_id=person, joints=joints)])


def phase(cycle: int, fraction: float, swing: float) -> float:
    return TAU * (cycle + fraction) + swing * math.sin(math.pi * fraction) ** 2


def paired_cycles(*, opposed: bool, cycles=4, hz=60, swing=1.8) -> tuple[list[MotionFrame], np.ndarray]:
    """Equal individual speed marginals; only within-cycle pairing differs."""
    frames, differences = [], []
    for k in range(cycles * hz + 1):
        cycle, tick = divmod(k, hz)
        fraction = tick / hz
        left_swing = swing if cycle % 2 == 0 else -swing
        right_swing = -left_swing if opposed else left_swing
        lp, rp = phase(cycle, fraction, left_swing), phase(cycle, fraction, right_swing)
        frames.append(motion_frame(k / hz, k,
                      left=[.34 + .065 * math.cos(lp), .42 + .065 * math.sin(lp)],
                      right=[.66 + .065 * math.cos(rp), .42 + .065 * math.sin(rp)]))
        if k < cycles * hz:
            differences.append(rp - lp)
    return frames, np.asarray(differences)


def concentration(differences) -> float:
    """Sai's phase concentration R_phase, not Anni's transverse R_e."""
    phases = np.asarray(differences, dtype=float)
    return float(abs(np.exp(1j * phases).mean()))


def equal_path_rhythm(n=1200) -> dict:
    """Same ordered unit circle; q(t) changes dwell time, not arc occupation."""
    t = np.linspace(0., 1., n + 1)
    warped = t + .8 * t * (1 - t)
    paths = [np.stack([np.cos(TAU * u), np.sin(TAU * u)], axis=1) for u in (t, warped)]
    results = []
    for u, points in zip((t, warped), paths):
        ds = np.linalg.norm(np.diff(points, axis=0), axis=1)
        results.append({"time_half": float(np.mean(u[:-1] <= .5)),
                        "arc_half": float(ds[u[:-1] <= .5].sum() / ds.sum()),
                        "length": float(ds.sum())})
    return {"uniform": results[0], "warped": results[1]}


def spacetime_c(n=1200) -> dict:
    """Illustrative C: arc-weighted mean speed in image-right minus left.

    Sai's C is defined in a declared 3D body frame with front/back regions.
    Here the analogous signed 2D half-plane contrast only tests the separation
    of trajectory occupancy and speed; it is NOT a valid Sai C emission.
    """
    t = np.linspace(0., 1., n + 1)
    result = {}
    for name, u in (("uniform", t), ("warped", t + .8*t*(1-t))):
        x = np.stack([np.cos(TAU*u), np.sin(TAU*u)], axis=1)
        ds = np.linalg.norm(np.diff(x, axis=0), axis=1)
        speed = ds / np.diff(t)
        mid = (x[:-1, 0] + x[1:, 0]) / 2
        positive, negative = mid >= 0, mid < 0
        result[name] = float(np.average(speed[positive], weights=ds[positive])
                             - np.average(speed[negative], weights=ds[negative]))
    return result


def direction_tensor(points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Length-weighted E[tangent tangentᵀ]; its diagonal is Q."""
    steps = np.diff(np.asarray(points, dtype=float), axis=0)
    ds = np.linalg.norm(steps, axis=1)
    valid = ds > 1e-12
    if not valid.any():
        raise ValueError("no observed arc")
    tangent = steps[valid] / ds[valid, None]
    tensor = np.einsum("n,ni,nj->ij", ds[valid], tangent, tangent) / ds[valid].sum()
    return tensor, np.diag(tensor)


def plane_pair(n=720) -> dict:
    angle = np.linspace(0., TAU, n + 1)
    xy = np.stack([np.cos(angle), np.sin(angle), np.zeros(len(angle))], axis=1)
    xz = np.stack([np.cos(angle), np.zeros(len(angle)), np.sin(angle)], axis=1)
    return {"xy": direction_tensor(xy)[1].tolist(), "xz": direction_tensor(xz)[1].tolist()}


def diagonal_counterexample() -> dict:
    """Identical Q=(.5,.5,0), opposite off-diagonal geometry/projectors."""
    a = np.array([[0., 0., 0.], [1., 1., 0.]])
    b = np.array([[0., 0., 0.], [1., -1., 0.]])
    ta, qa = direction_tensor(a)
    tb, qb = direction_tensor(b)
    return {"q_a": qa.tolist(), "q_b": qb.tolist(),
            "tensor_a": ta.tolist(), "tensor_b": tb.tolist(),
            "projector_gap": float(np.linalg.norm(ta - tb))}


def ambiguous_projection(n=720) -> dict:
    """Pinhole projections coincide, while two positive-depth 3D arcs differ."""
    theta = np.linspace(0., TAU, n + 1)
    image = np.stack([.2 * np.cos(theta), .2 * np.sin(theta)], axis=1)
    za = np.full(len(theta), 2.)
    zb = 2. + .6 * np.sin(2 * theta)
    a = np.column_stack([image * za[:, None], za])
    b = np.column_stack([image * zb[:, None], zb])
    return {"image_max_difference": float(np.max(np.linalg.norm(a[:, :2]/a[:, 2, None]
                       - b[:, :2]/b[:, 2, None], axis=1))),
            "arc_3d_a": float(np.linalg.norm(np.diff(a, axis=0), axis=1).sum()),
            "arc_3d_b": float(np.linalg.norm(np.diff(b, axis=0), axis=1).sum())}


def ambiguous_observation_frames(n=60) -> list[MotionFrame]:
    """The one 2D observation sequence compatible with both 3D truth worlds."""
    theta = np.linspace(0., TAU, n+1)
    return [motion_frame(float(k/n), k,
            left=[.34 + .04*math.cos(a), .42 + .04*math.sin(a)])
            for k, a in enumerate(theta)]


def jittered_frames(frames: list[MotionFrame], *, sigma=.002, seed=19,
                    gap_at=None) -> list[MotionFrame]:
    """Deterministic camera-plane pose jitter, with an optional held/missing gap."""
    rng = np.random.default_rng(seed)
    output = []
    for index, original in enumerate(frames):
        frame = original.model_copy(deep=True)
        for joint in frame.persons[0].joints:
            if joint.index in (9, 10):
                joint.position = (np.asarray(joint.position) + rng.normal(0., sigma, 2)).tolist()
                if index == gap_at:
                    joint.state = "held" if joint.index == 9 else "missing"
                    if joint.state == "missing":
                        joint.position = None
                    joint.confidence = 0.
        output.append(MotionFrame.model_validate(frame.model_dump()))
    return output


def frame_controls() -> dict:
    """Rigid translation cancels per edge; a rotating body frame does not."""
    origin = BASE_POSE[11:13].mean(axis=0)
    initial = BASE_POSE[9] - BASE_POSE[7]
    camera_edges, body_edges = [], []
    for angle in np.linspace(0., math.pi/2, 61):
        rotation = np.array([[math.cos(angle), -math.sin(angle)],
                             [math.sin(angle), math.cos(angle)]])
        moved = (BASE_POSE-origin) @ rotation.T + origin
        camera_edges.append(moved[9]-moved[7])
        body_edges.append((moved[9]-moved[7]) @ rotation)
    camera_edges, body_edges = np.asarray(camera_edges), np.asarray(body_edges)
    shifted = BASE_POSE + [.12, -.08]
    return {"translated_edge_error": float(np.linalg.norm((shifted[9]-shifted[7])-initial)),
            "rotating_camera_edge_arc": float(np.linalg.norm(np.diff(camera_edges, axis=0), axis=1).sum()),
            "rotating_body_edge_arc": float(np.linalg.norm(np.diff(body_edges, axis=0), axis=1).sum())}


def event_phase(t: float, events: list[float], max_age=1.5) -> tuple[str, float | None]:
    if any(a >= b for a, b in zip(events, events[1:])):
        raise ValueError("events are not strictly ordered")
    if events and events[-1] > t:
        raise ValueError("future event unavailable")
    if len(events) < 2:
        return "warmup", None
    period = events[-1] - events[-2]
    if t - events[-1] > max_age * period:
        return "expired", None
    return "estimated", (360 * (t - events[-1]) / period) % 360


def phase_controls() -> dict:
    stable = event_phase(2.5, [0., 1., 2.])
    early = event_phase(2.4, [0., 1., 2.])
    true_accelerated = 360 * .4 / .8
    return {"stable_deg": stable[1], "accelerated_live_deg": early[1],
            "accelerated_offline_deg": true_accelerated,
            "error_deg": early[1] - true_accelerated,
            "expired": event_phase(3.6, [0., 1., 2.])[0],
            "warmup": event_phase(.4, [0.])[0]}


def common_rhythm_no_pair_coupling() -> dict:
    """Eight independent-by-construction session offsets share frequency.

    Within a session the apparent phase lock is perfect; across prespecified
    offsets it vanishes. This is a negative control, not causal identification.
    """
    offsets = np.arange(8) * TAU / 8
    return {"within_session_r": [concentration(np.full(100, x)) for x in offsets],
            "pooled_r": concentration(np.repeat(offsets, 100))}


def prediction_rows(*, related: bool, seed: int, sessions=10, length=120) -> list[dict]:
    """Past-only rows with complete-session holdouts and an independent target."""
    rng = Random(seed)
    rows = []
    for session in range(sessions):
        prior, current = 0., 0.
        for k in range(length):
            left, right = rng.gauss(0, 1), rng.gauss(0, 1)
            y_next = .35 * current + (1.2 * left * right if related else 0.) + rng.gauss(0, .25)
            rows.append({"session": session, "cycle": k, "origin": float(k),
                         "latest": float(k), "available": float(k), "target_start": float(k+1),
                         "left": left, "right": right, "previous": prior,
                         "current": current, "target": y_next})
            prior, current = current, y_next
    return rows
