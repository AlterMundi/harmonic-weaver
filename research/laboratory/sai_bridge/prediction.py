"""Session-held-out prediction controls, without importing Sai's implementation."""
from __future__ import annotations

import math
from random import Random

import numpy as np

from .synthetic import prediction_rows


def require_causal(rows):
    for row in rows:
        if not (row["latest"] <= row["origin"] and row["available"] <= row["origin"]
                and row["origin"] < row["target_start"]):
            raise ValueError("feature unavailable at prediction origin")


def require_same_support(a, b):
    def keyed(rows):
        result = {(r["session"], r["cycle"]): (r["target_start"], r["target"]) for r in rows}
        if len(result) != len(rows):
            raise ValueError("duplicate unit")
        return result
    if keyed(a) != keyed(b):
        raise ValueError("different evaluation support or target")


def design(row, kind):
    core = [1., row["previous"], row["current"], row["left"], row["right"]]
    if kind == "linear":
        return core
    if kind == "linear_relation":
        return core + [row["left"] * row["right"]]
    if kind == "matched_nonlinear":
        return core + [row["left"] ** 2, row["right"] ** 2,
                       row["left"] * row["right"]]
    raise ValueError(kind)


def fitted_rmse(train, test, kind):
    require_causal(train + test)
    x = np.array([design(row, kind) for row in train])
    y = np.array([row["target"] for row in train])
    coefficients = np.linalg.lstsq(x, y, rcond=None)[0]
    predicted = np.array([design(row, kind) for row in test]) @ coefficients
    truth = np.array([row["target"] for row in test])
    return float(np.sqrt(np.mean((predicted - truth) ** 2)))


def prediction_contrast(related: bool):
    rows = prediction_rows(related=related, seed=71 if related else 72)
    train = [r for r in rows if r["session"] < 6]
    held = [r for r in rows if r["session"] >= 6]
    require_same_support(held, list(reversed(held)))
    truth = np.array([r["target"] for r in held])
    current = np.array([r["current"] for r in held])
    previous = np.array([r["previous"] for r in held])
    return {"train_sessions": 6, "held_sessions": 4, "held_units": len(held),
            "persistence_rmse": float(np.sqrt(np.mean((current-truth)**2))),
            "constant_velocity_rmse": float(np.sqrt(np.mean(((2*current-previous)-truth)**2))),
            **{kind + "_rmse": fitted_rmse(train, held, kind) for kind in
               ("linear", "linear_relation", "matched_nonlinear")}}


def support_selection_control():
    """An apparent gain from selecting easy held-out rows is invalid."""
    rng = Random(88)
    rows = []
    for session in range(10):
        for cycle in range(80):
            left, right = rng.gauss(0, 1), rng.gauss(0, 1)
            rows.append({"session": session, "cycle": cycle, "origin": float(cycle),
                         "latest": float(cycle), "available": float(cycle),
                         "target_start": float(cycle+1), "previous": 0., "current": 0.,
                         "left": left, "right": right,
                         "target": rng.gauss(0, .2 if cycle % 2 == 0 else 2.),
                         "easy": cycle % 2 == 0})
    train = [r for r in rows if r["session"] < 6]
    held = [r for r in rows if r["session"] >= 6]
    easy = [r for r in held if r["easy"]]
    try:
        require_same_support(held, easy)
    except ValueError:
        rejected = True
    else:
        rejected = False
    return {"unmatched_rejected": rejected,
            "invalid_full_linear_rmse": fitted_rmse(train, held, "linear"),
            "invalid_easy_relation_rmse": fitted_rmse(train, easy, "linear_relation"),
            "matched_easy_linear_rmse": fitted_rmse(train, easy, "linear"),
            "matched_easy_relation_rmse": fitted_rmse(train, easy, "linear_relation")}
