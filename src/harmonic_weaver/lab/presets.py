"""Starting places: migrate unchanged factory defaults, preserve user edits."""
from .contracts import Macro, MacroTarget, MappingTerm, Preset, Route


def initial_presets(*, legacy=False):
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
        if not legacy and algorithm != "baseline":
            for route in preset.routes:
                if route.target in {"detune", "phase_deg"}:
                    route.enabled = False
                elif route.target == "gain":
                    route.smoothing_s = .03
            preset.macros = [m for m in preset.macros if m.id != "phase"]
            if algorithm == "collective":
                preset.algorithm.collective_support = "observed"
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
    result.extend(descriptor_presets(reference, legacy=legacy))
    return result


def seed_presets(store):
    existing = {p["id"]:p for p in store.list_presets()}
    old_defaults = {p.id:p for p in initial_presets(legacy=True)}
    for preset in initial_presets():
        old = existing.get(preset.id)
        if old is None or (old == old_defaults[preset.id].model_dump() and old != preset.model_dump()):
            store.save(preset)


def descriptor_presets(reference, *, legacy=False):
    """Tuned amplitude-only examples; no calibration/source, never rewrite saved presets."""
    specs = [
        ("local", "08 · Afinado / error de predicción local"),
        ("relational", "09 · Afinado / oposición relativa × movimiento"),
        ("angular", "10 · Afinado / velocidad angular sin cancelación bilateral"),
        ("collective", "11 · Afinado / modos y organización colectiva"),
    ]
    result = []
    for algorithm, name in specs:
        preset = reference.model_copy(deep=True)
        preset.id = f"lab-v3-descriptor-{algorithm}"
        preset.name = name
        preset.algorithm.id = algorithm
        preset.response.pluck_enabled = False
        # Keep the accepted continuous tuned carrier. Only the gain descriptor differs.
        preset.expression = 0.
        preset.transient_mix = 0.
        preset.macros = [macro for macro in preset.macros if macro.id != "phase"]
        routes = []
        for zone in range(1, 7):
            prefix = f"zone.{zone}."
            mix = "sum"
            if algorithm == "local":
                terms = [MappingTerm(source=prefix+"velocity_error", input_unit="T", weight=5.)]
            elif algorithm == "relational":
                terms = [MappingTerm(source=prefix+"gain"),
                         MappingTerm(source=prefix+"I", weight=-.5, offset=.5)]
                mix = "product"
            elif algorithm == "angular":
                terms = [MappingTerm(source=prefix+"angular_speed", input_unit="deg/s", weight=.45/180.)]
            elif zone <= 3:
                terms = [MappingTerm(source=f"collective.mode.{zone}", input_unit="T/s", absolute=True, weight=.75)]
            elif zone == 4:
                terms = [MappingTerm(source="collective.residual"),
                         MappingTerm(source="global.speed", input_unit="T/s", weight=.75)]
                mix = "product"
            elif zone == 5:
                terms = [MappingTerm(source="collective.change", input_unit="deg", weight=1/30.),
                         MappingTerm(source="global.speed", input_unit="T/s", weight=.75)]
                mix = "product"
            else:
                terms = [MappingTerm(source="global.speed", input_unit="T/s", weight=.75)]
            routes.append(Route(id=f"descriptor-{zone}", voice=zone, target="gain", terms=terms,
                mix=mix, clamp_min=0., clamp_max=.45, smoothing_s=.03))
        preset.routes = routes
        if algorithm == "collective":
            preset.algorithm.components = 3
            preset.algorithm.collective_support = "fixed" if legacy else "observed"
            for voice, label in zip(preset.voices, ("Modo 1", "Modo 2", "Modo 3", "Residuo × velocidad", "Cambio de subespacio × velocidad", "Velocidad global")):
                voice.label = label
        result.append(Preset.model_validate(preset.model_dump()))
    return result
