"""Discoverable descriptions for the explicitly versioned v1 model set."""
from .contracts import AlgorithmDescriptor, AlgorithmSettings, ControlDescriptor
from .routing import signal_catalog


DESCRIPTIONS = {
    "baseline": ("Instrumento original", "Controlador preservado de seis zonas; escala adaptativa y respuesta originales."),
    "local": ("Predicción local", "Posición y velocidad constantes, derivadas causales y error a horizonte configurable; escala corporal fija explícita."),
    "relational": ("Interferencia relativa · Anni v0", "Velocidad distal relativa a su región proximal; I/R/A comparan cambio con historia previa o referencia instantánea explícita. Sin modo no equivale a neutralidad."),
    "angular": ("Geometría angular", "Ángulos internos de caderas, hombros, rodillas y codos; orientación de segmentos distales en tobillos/muñecas (COCO-17 no observa pies/manos). Unwrap y predicción causal."),
    "collective": ("Organización colectiva", "Subespacio de velocidades normalizadas ajustado al pasado; amplitudes, residuo, ángulos principales y evidencia predictiva retardada entre regiones. No establece intención ni causalidad."),
}
UNITS = {"fixed_x":"frame_height", "fixed_y":"frame_height", "smoothing_s":"s", "derivative_window_s":"s",
         "horizon_s":"s", "history_s":"s", "window_s":"s", "lag_s":"s", "max_gap_s":"s",
         "refractory_s":"s", "event_duration_s":"s", "propagation_interval_s":"s",
         "noise_velocity":"T/s", "noise_delta":"T/s"}


def algorithm_descriptors():
    schema = AlgorithmSettings.model_json_schema()
    controls = []
    for key, field in schema["properties"].items():
        if key in {"id", "version", "joints"}:
            continue
        kind = "choice" if "enum" in field else {"number":"number", "integer":"integer", "boolean":"boolean"}.get(field.get("type"))
        if kind is None:
            continue
        controls.append(ControlDescriptor(key=key, label=field.get("title", key), kind=kind,
            default=field["default"], unit=UNITS.get(key,"1"), minimum=field.get("minimum"),
            maximum=field.get("maximum"), choices=field.get("enum",[]),
            help=field.get("description", "Parámetro exploratorio; cambiarlo reinicia la historia del modelo."), application="reset"))
    return [AlgorithmDescriptor(id=key, label=label, description=description,
        inputs=["MotionFrame/camera_isotropic/2D", "source time", "selected person", "explicit torso calibration" if key != "baseline" else "adaptive original scale"],
        outputs=signal_catalog() if key != "baseline" else {k:v for k,v in signal_catalog().items() if k.endswith((".gain", ".detune", ".phase_deg", ".speed", ".acceleration")) and k.startswith("zone.")},
        controls=controls if key != "baseline" else [c for c in controls if c.key in {"horizon_s","max_gap_s"} or c.key.startswith("tracking_")],
        warmup_s=2. if key == "collective" else .25, cost="windowed" if key == "collective" else "light")
        for key,(label,description) in DESCRIPTIONS.items()]
