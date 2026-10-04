"""Synthetic tracked features -> frozen EVAL -> R05 PCM -> R07 figures."""

from pathlib import Path

from harmonic_weaver.lab.cache import atomic_json
from harmonic_weaver.lab.evaluation.runner import Request, run
from harmonic_weaver.lab.evaluation.service import EvaluationService
from harmonic_weaver.lab.presets import initial_presets
from harmonic_weaver.lab.research.candidate_input import candidate_snapshot
from harmonic_weaver.lab.research.membrane_worker import run_frozen
from harmonic_weaver.lab.research.resonator_run import run as render
from harmonic_weaver.lab.routing import PreparedRoutes
from harmonic_weaver.lab.store import SessionStore
from test_lab_evaluation import source_fixture


def seed(root):
    root = Path(root)
    inputs = root / "synthetic-label-inputs"
    inputs.mkdir(parents=True, exist_ok=False)
    source, _, _ = source_fixture(inputs)
    preset = next(p for p in initial_presets() if p.algorithm.id == "local")
    request = Request(presets=[preset], sources=[source])
    ident = "a" * 32
    folder = root / "evaluations" / ident
    folder.mkdir(parents=True, exist_ok=False)
    atomic_json(folder / "request.json", request.model_dump())
    run(request, folder / "result")
    store = SessionStore(root, prepare=PreparedRoutes)
    evaluation = EvaluationService(root, store, None)
    try:
        document = candidate_snapshot(
            evaluation,
            {
                "evaluation_id": ident,
                "run_index": 0,
                "signal_id": "zone.1.speed",
                "start_s": 0.2,
                "end_s": 2.0,
                "high": 0.3,
                "low": 0.1,
            },
        )
    finally:
        evaluation.close()
        store.close()
    pcm = root / "research/r05" / ("b" * 32)
    render(document, {"resonators": {"sample_rate": 8000}}, pcm)
    ids = []
    for i, start in enumerate([0, 1600, 3200, 8800, 10400, 12000]):
        projection_id = f"{i + 1:032x}"
        projection = root / "research/r07" / projection_id
        projection.mkdir(parents=True, exist_ok=False)
        atomic_json(
            projection / "request.json",
            {
                "membrane": {"sample_rate": 8000},
                "grid_x": 5,
                "grid_y": 5,
                "start_sample": start,
                "stop_sample_exclusive": start + 1600,
            },
        )
        atomic_json(projection / "source.json", {"directory": str(pcm.resolve())})
        run_frozen(projection)
        ids.append(projection_id)
    atomic_json(
        root / "label-fixture.json", {"projection_ids": ids, "evaluation_id": ident}
    )
    return ids


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    seed(parser.parse_args().root)
