"""Synthetic R05 PCM -> verified R07 figures for real API/UI readout tests."""

import argparse
from pathlib import Path

from harmonic_weaver.lab.cache import atomic_json
from harmonic_weaver.lab.research.membrane_worker import run_frozen
from harmonic_weaver.lab.research.resonator_run import run


def seed(root):
    root = Path(root)
    source_root = root / "synthetic-readout-sources"
    source_root.mkdir(parents=True, exist_ok=False)
    cases = []
    for i, gain in enumerate([0.2, 0.4, 0.6, 0.8, 0.3, 0.7]):
        source = source_root / str(i)
        document = {
            "request": {
                "evaluation_id": "a" * 32,
                "run_index": 0,
                "signal_id": "speed",
                "start_s": 0,
                "end_s": 0.1,
                "high": 1,
                "low": 0.2,
            },
            "unit": "T/s",
            "rows": [
                {"time_s": 0.0, "value": 0.0, "valid": True},
                {"time_s": 0.03, "value": 2.0, "valid": True},
            ],
            "provenance": {"fixture": "synthetic_readout_gain"},
        }
        run(
            document,
            {"resonators": {"sample_rate": 8000}, "excitation": {"gain": gain}},
            source,
        )
        ident = f"{i + 1:032x}"
        projection = root / "research/r07" / ident
        projection.mkdir(parents=True, exist_ok=False)
        atomic_json(
            projection / "request.json",
            {
                "membrane": {"sample_rate": 8000},
                "grid_x": 5,
                "grid_y": 5,
                "stop_sample_exclusive": 800,
            },
        )
        atomic_json(projection / "source.json", {"directory": str(source.resolve())})
        run_frozen(projection)
        cases.append(
            {
                "id": f"gain-{i}",
                "projection_run_id": ident,
                "role": "train" if i < 4 else "test",
                "recording_id": f"synthetic-gain-{i}",
                "subject_group": "synthetic",
                "targets": [gain],
            }
        )
    request = {
        "schema_version": 1,
        "reservation": "take",
        "attribute_ids": ["excitation_gain"],
        "attribute_units": ["dimensionless"],
        "settings": {"ridge": 0.001},
        "cases": cases,
    }
    atomic_json(root / "readout-request.json", request)
    return request


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    seed(parser.parse_args().root)
