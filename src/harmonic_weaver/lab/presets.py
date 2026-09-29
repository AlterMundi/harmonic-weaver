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
    return result


def seed_presets(store):
    existing = {p["id"] for p in store.list_presets()}
    for preset in initial_presets():
        if preset.id not in existing:
            store.save(preset)
