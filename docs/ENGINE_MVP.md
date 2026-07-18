# Headless engine MVP boundary

The implementation in `harmonic_weaver.engine` follows `CORE_DESIGN.md` and
keeps the source, routing, state-store and Stage Contract transport layers
separate. Scene and route definitions are canonical JSON data; a compiled
generation contains no executable content from clients.

Safety-profile capability writes use this declarative shape:

```json
{
  "capability": "voice_gain",
  "bindings": {"N": 4},
  "argument": "gain",
  "value": 0.0,
  "ramp_ms": 20.0
}
```

The same object is valid in `reset_defaults` and `silence_actions` (where
`ramp_ms` is optional). An object can instead wrap the first four destination
fields below `destination`. A native action uses `{"action": "name"}` and is
accepted only when that name appears in an optional manifest `actions` array;
the MVP records it but does not invent an OSC address or packet format.

The bundled transport is deliberately recording-only. Hardware discovery,
live beacon/shaper OSC, authentication/TLS termination, UI clients, audio
rendering and claims about audible behavior remain deployment or follow-on
work. Fixed-Hz derived sources run from the server's 10 ms engine ticker;
declarations still control their actual cadence.
