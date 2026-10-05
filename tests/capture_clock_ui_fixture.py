"""Isolated Stage fixture: synthetic controls only, no hardware or media."""

from harmonic_weaver.server import create_app
from engine_fixtures import route, scene, safety_profile, source_manifest, instrument_manifest
from harmonic_weaver.engine import RecordingOutputTransport, WeaverEngine

engine=WeaverEngine(transport=RecordingOutputTransport())
source=source_manifest(channels={"slot_0_pos":(0.,1.)})
engine.install_source(source)
engine.source_hello('sensor','0000000000000001',source['contract_id'])
instrument=instrument_manifest()
engine.install_instrument(instrument,safety_profile(instrument,range(7)))
engine.instrument_hello('synth','0000000000000002',instrument['contract_id'])
engine.instrument_sync_complete('synth','0000000000000002',instrument['contract_id'])
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
        route('capture-phase',channel='sensor.slot_0_pos',voice=2,
              transforms=[{'type':'phase_accumulator','wrap_deg':360.,'max_dt_ms':100.},
                          {'type':'scale_range','in':[0.,360.],'out':[0.,1.],'clamp':True}]),
        route('capture-slew',channel='sensor.slot_0_pos',voice=3,
              transforms=[{'type':'slew_limiter','max_rate':2.,'max_dt_ms':100.}]),
        route('capture-beat',channel='sensor.slot_0_pos',voice=4,
              transforms=[{'type':'beat_envelope'}]),
        route('capture-peak',channel='sensor.slot_0_pos',voice=5,
              transforms=[{'type':'peak_detector'}]),
        route('capture-dwell',channel='sensor.slot_0_pos',voice=6,
              transforms=[{'type':'pad_dwell'}]),
    ]
)
engine.upsert_scene(preset, engine.stage_revision)
engine.switch_scene("main", 1, engine.stage_revision)
app = create_app(engine)


@app.get("/fixture/state")
def fixture_state():
    return engine.snapshot()
