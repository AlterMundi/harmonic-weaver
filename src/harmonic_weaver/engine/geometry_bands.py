"""Vertical bands geometry expander.

Registered as ``vertical_bands`` in the geometry expander registry.
Produces zone indices via per-slot-per-hand band bins, then wires
match_value activation routes to harmonic_source_envelope.

Schema (Phase 1 — asymmetric, no ``mirror``):

  {
    "geometry": {
      "type": "vertical_bands",
      "subdivisions": 8,
      "band_span": 0.4
    },
    "activation": {
      "kernel": "delta",
      "magnitude": "presence",
      "envelope": "none"
    },
    "effects": [{
      "source": {"slot_keypoint": "nose", "axis": "y",
                 "normalized": [0.0, 1.0]},
      "target": {"capability": "master_gain", "argument": "gain",
                 "range": [0.2, 1.0]}
    }]
  }

Phase 2 will add ``mirror: true/false``, gaussian kernel, kinetic_energy
magnitude, and slew envelope.
"""

from __future__ import annotations

from typing import Any, Mapping

from harmonic_weaver.engine.compiler import GeometryExpansion, validation
from harmonic_weaver.engine.geometry_toolkit import (
    N_HARMONICS,
    N_SLOTS,
    HAND_SIDES,
    HAND_NAMES,
    band_routes,
    band_zone_aggregator_symmetric,
    head_position_aggregator,
    head_y_effect_route,
    position_aggregator,
)

# ---------------------------------------------------------------------------
# Activation schema validation
# ---------------------------------------------------------------------------

_VALID_KERNELS = {"delta", "gaussian"}
_VALID_MAGNITUDES = {"presence", "kinetic_energy"}
_VALID_ENVELOPES = {"none", "slew"}


def _validate_activation(raw: Mapping[str, Any], path: str) -> dict[str, str]:
    kernel = str(raw.get("kernel", "delta"))
    magnitude = str(raw.get("magnitude", "presence"))
    envelope = str(raw.get("envelope", "none"))
    if kernel not in _VALID_KERNELS:
        raise validation(
            f"{path}.kernel must be one of {sorted(_VALID_KERNELS)}"
        )
    if magnitude not in _VALID_MAGNITUDES:
        raise validation(
            f"{path}.magnitude must be one of {sorted(_VALID_MAGNITUDES)}"
        )
    if envelope not in _VALID_ENVELOPES:
        raise validation(
            f"{path}.envelope must be one of {sorted(_VALID_ENVELOPES)}"
        )
    if magnitude == "kinetic_energy" or envelope == "slew":
        raise validation(
            f"{path}: Phase 2 features (kinetic_energy, slew) are not yet implemented"
        )
    if kernel == "gaussian":
        raise validation(
            f"{path}: Phase 2 feature (gaussian kernel) is not yet implemented"
        )
    return {"kernel": kernel, "magnitude": magnitude, "envelope": envelope}


# ---------------------------------------------------------------------------
# Expander
# ---------------------------------------------------------------------------


def expand_vertical_bands(
    scene: dict[str, Any],
    base_channel_ranges: Mapping[str, tuple[float, float]],
) -> GeometryExpansion:
    geo = scene["geometry"]
    if not isinstance(geo, Mapping):
        raise validation("scene.geometry must be an object")

    subdivisions = int(geo.get("subdivisions", 8))
    if not 2 <= subdivisions <= 32:
        raise validation(
            f"scene.geometry.subdivisions must be 2..32, got {subdivisions}"
        )
    if subdivisions > N_HARMONICS:
        raise validation(
            f"scene.geometry.subdivisions ({subdivisions}) exceeds max harmonics ({N_HARMONICS})"
        )

    # band_span is now computed by HarMoCAP (per-slot calibration); scene value is ignored

    # ── Activation ──
    activation_raw = scene.get("activation", {})
    if not isinstance(activation_raw, Mapping):
        raise validation("scene.activation must be an object if present")
    activation = _validate_activation(activation_raw, "scene.activation")

    # ── Aggregators ──
    geo_aggregators: list[dict[str, Any]] = []

    # Position aggregators (hand_x/hand_y) for every slot+hand
    # + head position (nose_x/nose_y) for every slot
    for slot in range(N_SLOTS):
        for side in HAND_SIDES:
            geo_aggregators.append(
                position_aggregator(slot, HAND_NAMES[side], "x")
            )
            geo_aggregators.append(
                position_aggregator(slot, HAND_NAMES[side], "y")
            )
        for axis in ("x", "y"):
            geo_aggregators.append(
                head_position_aggregator(slot, "nose", axis)
            )

    # Band zone aggregators for every slot+hand
    band_source_ids: dict[tuple[int, str], str] = {}
    for slot in range(N_SLOTS):
        for side in HAND_SIDES:
            pad_id, sub_aggs = band_zone_aggregator_symmetric(
                slot, side, subdivisions, band_span=1.0  # normalized, HarMoCAP handles calibration
            )
            band_source_ids[(slot, side)] = pad_id
            geo_aggregators.extend(sub_aggs)

    # ── Routes ──
    all_routes: list[dict[str, Any]] = []

    # match_value routes per slot+hand+zone
    for slot in range(N_SLOTS):
        for side in HAND_SIDES:
            zone_src = band_source_ids[(slot, side)]
            all_routes.extend(
                band_routes(slot, side, subdivisions, zone_source_id=zone_src)
            )

    # ── Effects ──
    effects_raw = scene.get("effects", [])
    if isinstance(effects_raw, list):
        for effect in effects_raw:
            if not isinstance(effect, Mapping):
                continue
            src = effect.get("source", {})
            tgt = effect.get("target", {})
            if not isinstance(src, Mapping) or not isinstance(tgt, Mapping):
                continue
            if (
                src.get("slot_keypoint") == "nose"
                and src.get("axis") == "y"
            ):
                lo, hi = tgt.get("range", [0.2, 1.0])
                for slot in range(N_SLOTS):
                    head_y_id = f"slot_{slot}_head_{src['slot_keypoint']}_y"
                    all_routes.append(
                        head_y_effect_route(
                            slot,
                            head_y_source_id=head_y_id,
                            capability=tgt.get("capability", "master_gain"),
                            argument=tgt.get("argument", "gain"),
                            lo=float(lo),
                            hi=float(hi),
                        )
                    )

    return GeometryExpansion(
        aggregators=tuple(geo_aggregators),
        zone_layout={
            "type": "vertical_bands",
            "subdivisions": subdivisions,
            "band_span": 1.0,  # normalized; HarMoCAP computes per-slot calibration
            "activation": activation,
            "source_ids": {
                f"{slot}_{side}": src
                for (slot, side), src in band_source_ids.items()
            },
        },
        routes=tuple(all_routes),
    )
