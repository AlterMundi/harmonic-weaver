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
