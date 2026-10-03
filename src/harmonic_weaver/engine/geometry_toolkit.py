"""Shared geometry expander toolkit — imported by every geometry expander.

Every geometry expander (vertical_bands, concentric_circles, pads_2d) produces
the same per-slot-per-hand structure: position aggregators, zone-index
aggregators, and match_value routes to harmonic_source_envelope. This module
extracts that boilerplate so adding a 4th geometry is ~50 lines of zone-math
code, not thousands of lines of duplicated slot loops.

Design constraint (external architecture review, 2026-07-25):
  Geometry expanders return TOPOLOGY ONLY. They must never emit instrument
  routes. Activation expanders own routes.
"""

from __future__ import annotations

from typing import Any

N_SLOTS = 8
N_HARMONICS = 32
HAND_SIDES = ("r", "l")
HAND_NAMES = {"r": "right", "l": "left"}

DEFAULT_CADENCE = {"mode": "on_input", "max_rate_hz": 60.0}
DEFAULT_VALIDITY = {
    "min_valid_count": 2,
    "min_observed_count": 2,
    "max_age_ms": 250.0,
    "include_held": False,
    "held_max_ms": 0.0,
    "confidence": "minimum",
}
SINGLE_VALIDITY = {
    "min_valid_count": 1,
    "min_observed_count": 1,
    "max_age_ms": 250.0,
    "include_held": False,
    "held_max_ms": 0.0,
    "confidence": "minimum",
}


def source_id(slot: int, hand_side: str) -> int:
    """Allocate a synth source S for a slot+hand pair.

    S = slot * 2 + hand_side  where hand_side is 0='r' or 1='l'.

    This gives an exact 1:1 mapping from the 16 hand-streams (8 slots × 2
    hands) to the 16 source IDs the shaper exposes — no merge/collision
    policy needed.
    """
    side_bit = 0 if hand_side == "r" else 1
    return slot * 2 + side_bit


def _derive_id(slot: int, kind: str, hand_side: str, suffix: str = "") -> str:
    """Compose a derived_source_id: ``slot_N_{kind}_{side}``."""
    return f"slot_{slot}_{kind}_{hand_side}" + (f"_{suffix}" if suffix else "")


# ── Position aggregators (hand_x, hand_y per slot+hand) ──────────────────────


def position_aggregator(slot: int, hand: str, axis: str) -> dict[str, Any]:
    """Mean aggregator for one hand coordinate, gated on slot present."""
    side = "r" if hand == "right" else "l"
    return {
        "aggregator_id": f"slot-{slot}-pos-{side}-{axis}",
        "aggregator_version": 1,
        "derived_source_id": _derive_id(slot, "pos", side, axis),
        "output_channel": axis,
        "inputs": [
            {
                "channel": f"harmocap.slot_{slot}_keypoint_{hand}_wrist_{axis}",
                "include_when": {
                    "channel": f"harmocap.slot_{slot}_present",
                    "op": "eq",
                    "value": 1.0,
                },
            }
        ],
        "operator": "mean",
        "cadence": DEFAULT_CADENCE,
        "validity": SINGLE_VALIDITY,
    }


def head_position_aggregator(slot: int, keypoint: str, axis: str) -> dict[str, Any]:
    """Mean aggregator for a head keypoint (nose) coordinate, gated on present."""
    return {
        "aggregator_id": f"slot-{slot}-head-{keypoint}-{axis}",
        "aggregator_version": 1,
        "derived_source_id": f"slot_{slot}_head_{keypoint}_{axis}",
        "output_channel": axis,
        "inputs": [
            {
                "channel": f"harmocap.slot_{slot}_keypoint_{keypoint}_{axis}",
                "include_when": {
                    "channel": f"harmocap.slot_{slot}_present",
                    "op": "eq",
                    "value": 1.0,
                },
            }
        ],
        "operator": "mean",
        "cadence": DEFAULT_CADENCE,
        "validity": SINGLE_VALIDITY,
    }


# ── Zone-index aggregator factory ────────────────────────────────────────────


def band_zone_aggregator(
    slot: int,
    side: str,
    subdivisions: int,
    *,
    band_span: float,
) -> tuple[str, list[dict[str, Any]]]:
    """bin_2d(cols=subdivisions, rows=1) over signed (hand_x − head_x).

    The relative offset spans [-band_span, +band_span] → zone index 0..(subdivisions-1).
    Left-of-center (negative) maps to low indices, right-of-center to high indices.
    ``mirror`` symmetry (both sides → same harmonic) is a future card; Phase 1
    ships asymmetric bands.

    The computation chain is:

        rel = difference(hand_x, head_x)
        bin_2d(cols=subdivisions, rows=1, x_min=-band_span, x_max=+band_span)
    """
    hand_x_ch = f"{_derive_id(slot, 'pos', side, 'x')}.x"
    head_x_ch = f"{_derive_id(slot, 'head', 'nose', 'x')}.x"

    aggregators: list[dict[str, Any]] = []

    # Step 1: relative offset
    rel_id = _derive_id(slot, "rel", side, "x")
    aggregators.append(
        {
            "aggregator_id": f"slot-{slot}-rel-{side}-x",
            "aggregator_version": 1,
            "derived_source_id": rel_id,
            "output_channel": "x",
            "inputs": [
                {"channel": hand_x_ch},
                {"channel": head_x_ch},
            ],
            "operator": "difference",
            "cadence": DEFAULT_CADENCE,
            "validity": DEFAULT_VALIDITY,
        }
    )

    # Step 2: bin_2d on signed offset
    pad_id = _derive_id(slot, "band", side)
    head_y_ch = f"{_derive_id(slot, 'head', 'nose', 'y')}.y"
    aggregators.append(
        {
            "aggregator_id": f"slot-{slot}-band-{side}",
            "aggregator_version": 1,
            "derived_source_id": pad_id,
            "output_channel": "band",
            "inputs": [
                {"channel": f"{rel_id}.x"},
                {"channel": head_y_ch},  # rows=1 → Y is unused but must be a valid channel
            ],
            "operator": "bin_2d",
            "cols": subdivisions,
            "rows": 1,
            "serpentine": False,
            "x_min": -band_span,
            "x_max": band_span,
            "y_min": 0.0,
            "y_max": 1.0,
            "cadence": DEFAULT_CADENCE,
            "validity": DEFAULT_VALIDITY,
        }
    )

    return pad_id, aggregators


def band_zone_aggregator_symmetric(
    slot: int,
    side: str,
    subdivisions: int,
    *,
    band_span: float,
) -> tuple[str, list[dict[str, Any]]]:
    """bin_2d(cols=subdivisions, rows=1) over normalized wrist position.

    HarMoCAP normalizes wrist X in bands mode: x = abs(wrist_x - nose_x) / band_span.
    The weaver bins on fixed 0..1 range — no dynamic range needed.

    Both left and right of head map to the same band index — symmetric.
    Center (near head) = band 0 (H1), outermost = band subdivisions-1 (HN).
    """
    hand_name = HAND_NAMES[side]
    band_ch = f"harmocap.slot_{slot}_keypoint_{hand_name}_wrist_x"
    head_y_ch = f"harmocap.slot_{slot}_keypoint_nose_y"

    aggregators: list[dict[str, Any]] = []

    # bin_2d on normalized band position
    pad_id = _derive_id(slot, "band", side)
    aggregators.append(
        {
            "aggregator_id": f"slot-{slot}-band-{side}",
            "aggregator_version": 1,
            "derived_source_id": pad_id,
            "output_channel": "band",
            "inputs": [
                {"channel": band_ch},
                {"channel": head_y_ch},
            ],
            "operator": "bin_2d",
            "cols": subdivisions,
            "rows": 1,
            "serpentine": False,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": 0.0,
            "y_max": 1.0,
            "cadence": DEFAULT_CADENCE,
            "validity": DEFAULT_VALIDITY,
        }
    )

    return pad_id, aggregators


# ── Route factory ─────────────────────────────────────────────────────────────


def harmonic_source_route(
    slot: int,
    side: str,
    zone_index: int,
    *,
    zone_source_id: str,
) -> dict[str, Any]:
    """match_value route: zone source .band == zone_index → gain=1."""
    return {
        "route_id": f"slot-{slot}-hand-{side}-band-{zone_index:02d}",
        "route_version": 1,
        "enabled": True,
        "inputs": [{"channel": f"{zone_source_id}.band"}],
        "transforms": [
            {"type": "match_value", "value": float(zone_index), "on": 1.0, "off": 0.0}
        ],
        "destination": {
            "instrument_id": "shaper",
            "capability": "harmonic_source_envelope",
            "bindings": {"N": zone_index + 1, "S": source_id(slot, side)},
            "argument": "gain",
        },
        "validity": {
            "held": "reject",
            "invalid": "hold_then_reset",
            "min_confidence": 0.5,
            "hold_ms": 150.0,
        },
    }


def band_routes(
    slot: int, side: str, subdivisions: int, *, zone_source_id: str
) -> list[dict[str, Any]]:
    """All match_value routes for one hand's band geometry."""
    return [
        harmonic_source_route(
            slot, side, zi, zone_source_id=zone_source_id
        )
        for zi in range(subdivisions)
    ]


# ── Effect route factory ──────────────────────────────────────────────────────


def head_y_effect_route(
    slot: int,
    *,
    head_y_source_id: str,
    capability: str = "master_gain",
    argument: str = "gain",
    lo: float = 0.2,
    hi: float = 1.0,
) -> dict[str, Any]:
    """scale_range route: nose_y ∈ [0,1] → master_gain ∈ [lo, hi]."""
    return {
        "route_id": f"slot-{slot}-head-y-effect",
        "route_version": 1,
        "enabled": True,
        "inputs": [{"channel": f"{head_y_source_id}.y"}],
        "transforms": [
            {
                "type": "scale_range",
                "in": [0.0, 1.0],
                "out": [lo, hi],
                "clamp": True,
            }
        ],
        "destination": {
            "instrument_id": "shaper",
            "capability": capability,
            "bindings": {},
            "argument": argument,
        },
        "validity": {
            "held": "accept",
            "invalid": "hold_then_reset",
            "min_confidence": 0.5,
            "hold_ms": 150.0,
        },
    }
