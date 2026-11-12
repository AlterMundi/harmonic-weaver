# Start the existing instruments together

[Native macOS receiving and current acceptance limits](MACOS.md). The default
Linux R24/JACK recipe below is not a Mac installation instruction.

From the maintained `harmonic-weaver` checkout:

```sh
scripts/start-live-stack.sh --guitar-lab
```

This is the existing full-stack entry point, with an explicit guitar profile.
The historical default still activates its chosen scene and camera; the guitar
profile uses `harmonic-lab-session.py` only as its internal supervisor.

This starts/reuses the existing Guitar panel and starts the existing Spatializer
in live mode, without a public tunnel. The verified audio path is R24 physical
channel1 → SuperCollider input1 → 13-band ATK Spatializer → R24 stereo playback.
No motor trial, board save/reset, recording or camera is started by this command.
Use the Guitar panel to control the motor explicitly. The former separate
`start-laboratory.sh` remains the body laboratory's own supported launcher.

To include the ordinary body laboratory in the same invocation:

```sh
scripts/start-live-stack.sh --guitar-lab --with-weaver
```

This reuses `start-laboratory.sh --audio-backend jack --device "R24 Analog Stereo"
--tracking-device cpu`, including its existing Shaper and prepared HarMoCAP APIs.
It retains source/camera selection as an explicit action in the ordinary web UI.
Shaper sums at the selected R24 output; this does not automatically map body
features to Spatializer knobs or send Shaper audio through its guitar input.
Select such mappings deliberately through the existing contracts.

The interfaces keep their established same-machine entries: Spatializer5050,
Guitar18879, and optional Weaver8765. There is no new App, web server, proxy,
account or public listener. Reload an existing tab after source updates.

If the base session is already running, the optional ordinary body launcher can
also run alongside it in a separate terminal. Do not start a second joint owner
or restart the base audio merely to add the optional laboratory.

## Receiving sources and lifecycle

Use the existing sibling `beacon-spatial` checkout with `beacon_routes.py` and
`bounded_log.py` (source5941756 or later). The joint launcher refuses a missing
companion update. Source updates do not change presets, media, calibration or
saved board programs. The optional body launcher retains its existing model,
dependency-build and storage requirements; the base session does not build it.

`--spatializer-dir`, `--guitar-panel-dir` and `--state-dir` select existing
receiving locations. The Guitar directory must contain its existing supported
`run-panel.sh` if the panel is not already running. Do not replace the live
controller from a historical checkout to satisfy this composition.

The session has one lock and one latest state record, defaulting to
`~/.local/state/harmonic-lab/current.json`. Each component log is at most1MiB;
Spatializer uses the same bounded tail writer. A new session replaces these
latest files, with no multiplying logs/recordings. `--hours` is >0 and <=8
(default8); Ctrl+C or expiry closes only process groups created by that exact
invocation. Components already running are borrowed and remain running.
Private operational state is not a release artifact or a global session control.

Readiness requires actual Spatializer hello/state synchronization with its exact
native contract and a readback of the selected JACK links, plus the existing web
endpoint. Neither process existence nor a successful `jack_connect` invocation
alone establishes the path. Actual sound, guitar input level, headphone setup,
latency and human listening acceptance remain independent observations.

Tests use isolated graph/process fixtures and bounded scratch logs. They do not
claim operational audio integration; record actual receiving checks separately
in the owning Harmonic Lab work record. There is no autonomous model attention,
background sensor service or global Stop.
