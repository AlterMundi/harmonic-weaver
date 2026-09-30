"""Versioned starting places, never overwriting a user's saved configuration."""
from .contracts import Macro, MacroTarget, Preset


def initial_presets():
    names = {"baseline":"01 · Instrumento original / seis plucks",
             "local":"02 · Movimiento continuo / predicción local",
             "relational":"03 · Interferencia relativa / Anni v0",
             "angular":"04 · Articulaciones / geometría angular",
             "collective":"05 · Organización colectiva / tres componentes, seis voces"}
    result = []
    for algorithm, name in names.items():
        preset = Preset(id=f"lab-v1-{algorithm}", name=name, favorite=True)
        preset.algorithm.id = algorithm
        preset.response.pluck_enabled = algorithm == "baseline"
        preset.macros = [Macro(id="intensity", label="Intensidad", value=.7,
                              targets=[MacroTarget(path="master", minimum=0., maximum=1.)]),
                         Macro(id="phase", label="Movimiento de fase", value=.25,
                              targets=[MacroTarget(path="response.phase_depth", minimum=0., maximum=180.)])]
        result.append(preset)
    continuous = result[0].model_copy(deep=True)
    continuous.id = "lab-v1-baseline-continuous"
    continuous.name = "01b · Instrumento original / movimiento continuo"
    continuous.response.pluck_enabled = False
    result.insert(1, continuous)
    sustained = continuous.model_copy(deep=True)
    sustained.id = "lab-v1-baseline-sustained"
    sustained.name = "01c · Armónicos sostenidos / intensidad corporal"
    for route in sustained.routes:
        if route.target in {"detune", "phase_deg"}:
            route.enabled = False
        elif route.target == "gain":
            route.smoothing_s = .03
    result.insert(2, sustained)
    reference = sustained.model_copy(deep=True)
    reference.id = "lab-v2-reference-sustained"
    reference.name = "06 · Referencia 01c / afinado sostenido"
    result.append(reference)
    contrast = reference.model_copy(deep=True)
    contrast.id = "lab-v2-reference-transients"
    contrast.name = "07 · Exploración / realce ×10 y transientes 30%"
    contrast.expression = 10.
    contrast.transient_mix = .3
    result.append(contrast)
    return result


def seed_presets(store):
    existing = {p["id"] for p in store.list_presets()}
    for preset in initial_presets():
        if preset.id not in existing:
            store.save(preset)
