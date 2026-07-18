"""Contract-correct builders shared by headless engine tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Iterable, Mapping

from harmonic_weaver.contract_codec import contract_id_from_manifest


ROOT = Path(__file__).resolve().parents[1]


def _template(name: str) -> dict:
    return json.loads((ROOT / "contracts" / name).read_text(encoding="utf-8"))


def source_manifest(
    source_id: str = "sensor",
    channels: Mapping[str, tuple[float, float]] | None = None,
    *,
    lease_ms: float = 2000.0,
) -> dict:
    manifest = _template("source_frame.template.json")
    old_namespace = manifest["namespace"]
    namespace = f"/src/{source_id}"
    manifest["name"] = f"{source_id}-source-frame"
    manifest["namespace"] = namespace
    manifest["source"]["source_id"] = source_id
    manifest["presence"]["lease_ms"] = lease_ms
    manifest["handshake"]["hello_address"] = f"{namespace}/hello"
    manifest["handshake"]["hello_request_address"] = f"{namespace}/hello/request"
    manifest["addresses"] = {
        address.replace(old_namespace, namespace): value
        for address, value in manifest["addresses"].items()
    }
    selected = channels or {"modulation": (0.0, 1.0)}
    manifest["channels"] = [
        {
            "name": name,
            "description": f"Test channel {name}.",
            "range": list(bounds),
            "polarity": "Declared test-domain minimum to maximum.",
            "rate_hz_nominal": 30.0,
            "smoothing_hints": "Control-rate test signal.",
        }
        for name, bounds in selected.items()
    ]
    manifest["contract_id"] = contract_id_from_manifest(manifest)
    return manifest


def instrument_manifest(instrument_id: str = "synth") -> dict:
    manifest = _template("instrument_contract.template.json")
    manifest["name"] = f"{instrument_id}-control"
    manifest["instrument"]["instrument_id"] = instrument_id
    manifest["contract_id"] = contract_id_from_manifest(manifest)
    return manifest


def safety_profile(
    manifest: Mapping,
    voices: Iterable[int] = (0, 1, 2, 3, 4),
) -> dict:
    instrument_id = manifest["instrument"]["instrument_id"]
    defaults = [
        {
            "capability": "voice_gain",
            "bindings": {"N": voice},
            "argument": "gain",
            "value": 0.0,
        }
        for voice in voices
    ]
    return {
        "instrument_id": instrument_id,
        "instrument_contract_id": manifest["contract_id"],
        "instrument_class": "control_only",
        "silence_actions": [],
        "reset_defaults": defaults,
        "rearm_fade_ms": 250.0,
    }


def route(
    route_id: str = "sensor-to-gain",
    *,
    channel: str = "sensor.modulation",
    voice: int = 0,
    transforms: list[dict] | None = None,
    validity: dict | None = None,
    version: int = 1,
) -> dict:
    return {
        "route_id": route_id,
        "route_version": version,
        "enabled": True,
        "inputs": [{"channel": channel}],
        "transforms": copy.deepcopy(transforms or []),
        "destination": {
            "instrument_id": "synth",
            "capability": "voice_gain",
            "bindings": {"N": voice},
            "argument": "gain",
        },
        "validity": copy.deepcopy(
            validity
            or {"held": "accept", "min_confidence": 0.0, "invalid": "suppress"}
        ),
    }


def scene(
    scene_id: str = "main",
    *,
    routes: list[dict] | None = None,
    aggregators: list[dict] | None = None,
    transition: dict | None = None,
    version: int = 1,
    updated_at_us: int = 0,
) -> dict:
    return {
        "scene_id": scene_id,
        "scene_version": version,
        "name": scene_id.title(),
        "description": "Engine behavior test scene.",
        "tags": ["test"],
        "created_at_us": 0,
        "updated_at_us": updated_at_us,
        "aggregators": copy.deepcopy(aggregators or []),
        "routes": copy.deepcopy(routes or []),
        "transition": copy.deepcopy(transition or {"policy": "reset"}),
    }


def ready_engine(*, channels: Mapping[str, tuple[float, float]] | None = None):
    from harmonic_weaver.engine import RecordingOutputTransport, WeaverEngine

    recorder = RecordingOutputTransport()
    engine = WeaverEngine(transport=recorder)
    source = source_manifest(channels=channels)
    instrument = instrument_manifest()
    engine.install_source(source)
    engine.source_hello("sensor", "0000000000000001", source["contract_id"])
    engine.install_instrument(instrument, safety_profile(instrument))
    engine.instrument_hello("synth", "0000000000000002", instrument["contract_id"])
    engine.instrument_sync_complete("synth", "0000000000000002", instrument["contract_id"])
    return engine, recorder, source, instrument
