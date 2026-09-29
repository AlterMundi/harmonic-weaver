# harmonic-weaver

Headless modulation router/patchbay for the Harmonic Beacon ecosystem.

harmonic-weaver routes modulation from **sources** through **transformations**
into **instruments**. It manages scenes and a global panic, and is driven by
contract manifests. It has no UI of its own: all UIs are thin clients of the
same contract-manifest protocol, served over WebSocket (web first,
mobile/Quest later).

## Headless Weaver

Install the project and run the Stage Contract server on the local-only default
bind:

```console
python -m pip install -e .
python -m harmonic_weaver.weaver
```

The HTTP health probe is `GET /health`; the versioned JSON Stage Contract is at
`WS /ws`. The CLI creates measured rehearsal evidence below `reports/<run_id>/`.
There is no UI and the built-in output transport only records declared native
capability sends. Live OSC adapters are intentionally outside this MVP.

Drivers connect without wrappers by using `engine.driver_callback` as their
`on_frame(source_id, channel_values)` callback after an installed Source Frame
manifest has passed `source_hello`. Instruments similarly install an exact
Instrument Control manifest and safety profile, pass `instrument_hello` plus
`instrument_sync_complete`, and may supply a testable `send_callback`.

The authoritative implementation design remains
[`docs/CORE_DESIGN.md`](docs/CORE_DESIGN.md); the concrete recording-only MVP
boundary is documented in [`docs/ENGINE_MVP.md`](docs/ENGINE_MVP.md).

## Live HarMoCAP body instrument

The repository also contains the live integration harness used to drive the
Harmonic Shaper from HarMoCAP. The current body instrument is `bands-v1`: each
tracked wrist selects one of eight horizontal harmonic bands relative to the
person's calibrated body geometry.

On the current rehearsal workstation the known-good launch command is:

```console
./scripts/start-live-stack.sh \
  --camera 2 \
  --scene bands-v1 \
  --beacon-mute \
  --pads-view harmocap \
  --shaper-device "R24 Analog Stereo"
```

For the isolated **Consonancia kinética** experiment, run
`./scripts/start-kinetic-consonance.sh --camera 0`.
It starts only HarMoCAP, the consonance controller and Shaper, with camera
and skeleton overlay. See [the experiment guide](docs/KINETIC_CONSONANCE.md).

Camera indices and audio-device names are machine-specific. Stop the latest
stack with:

```console
./scripts/start-live-stack.sh --stop latest
```

Generated runtime evidence is stored under `rehearsal/artifacts/` and must not
be committed. Current stabilization and polyphony work is tracked in
[issue #4](https://github.com/AlterMundi/harmonic-weaver/issues/4); the bounded
Codex continuation plan is in
[`docs/CODEX_HANDOFF_BANDS_V1.md`](docs/CODEX_HANDOFF_BANDS_V1.md).

Bands-v1 artifact summaries can be produced without exposing pose coordinates:

```console
python -m rehearsal.analyze_bands_artifact rehearsal/artifacts/<run-id>
```

The command emits compact JSON with HarMoCAP frame counts, the declared
person-count histogram, harmonic source-slot activity, frame-batched harmonic
transition counts, and route-reset evidence. Initialization resets are excluded
from transition counts. Run it on live artifacts only after any participant-data
audit.

## Laboratorio corporal (plan de construcción)

El [índice del laboratorio](docs/laboratory/README.md) reúne la especificación,
los milestones y las tareas para explorar movimiento, sonido y geometría
en tiempo real, junto con la agenda de investigación y evaluación posterior.
Estado: plan publicado; implementación pendiente.
