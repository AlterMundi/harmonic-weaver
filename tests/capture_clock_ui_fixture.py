"""Isolated Stage fixture: synthetic controls only, no hardware or media."""

from harmonic_weaver.server import create_app
from engine_fixtures import ready_engine, route, scene

engine, _, _, _ = ready_engine(channels={"slot_0_pos": (0.0, 1.0)})
engine._clock_us = lambda: 9000000000
preset = scene(
    routes=[
        route(
            "capture-derivative",
            channel="sensor.slot_0_pos",
            transforms=[
                {
                    "type": "derivative",
                    "window_ms": 40.0,
                    "max_abs": 10.0,
                    "max_dt_ms": 1000.0,
                },
                {
                    "type": "scale_range",
                    "in": [-10.0, 10.0],
                    "out": [0.0, 1.0],
                    "clamp": True,
                },
            ],
        ),
        route('capture-smoothing',channel='sensor.slot_0_pos',voice=1,
              transforms=[{'type':'smoothing','kind':'one_pole','time_ms':35.}]),
    ]
)
engine.upsert_scene(preset, engine.stage_revision)
engine.switch_scene("main", 1, engine.stage_revision)
app = create_app(engine)


@app.get("/fixture/state")
def fixture_state():
    return engine.snapshot()
