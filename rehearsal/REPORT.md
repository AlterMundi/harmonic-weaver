# T4.5 end-to-end integration rehearsal

Result: **PASS**
Run ID: `t45-20260719T092417Z`
Weaver report: `reports/t45-20260719T092417Z`
Rehearsal evidence: `rehearsal/artifacts/t45-20260719T092417Z`

## Runtime declaration

The full runtime completed as declared below.

Beacon is configured through the canonical `start-beacon.sh --file --no-https`
launcher with the 659 MB file-mode source. Shaper is configured headless with
`--no-midi --no-audio --slave`; its state API, not an audio device, is the
evidence plane. Weaver is configured with its normal Stage WebSocket API and
the HarMoCAP, MIDI, and ECG drivers installed. HarMoCAP uses the real
`two_persons.jsonl` kit replay over OSC. ECG uses a deterministic synthetic
raw-ADC stream over `/ecg/raw` into the production ECG driver. MIDI has no
hardware and its invalid channels are an expected assertion.

Repository inspection found that `cymatic-control/test_ecg_stream.py` is a
receiver/terminal diagnostic, despite the supplied inventory calling it an ECG
simulator. It cannot generate `/ecg/raw`. The rehearsal therefore uses
`rehearsal/ecg_simulator.py`, whose deterministic waveform comes from the
production driver's synthetic-ECG helper, and records this inventory mismatch
instead of pretending the diagnostic sends data. `simulate_eeg.py` is not
started because EEG is outside the Weaver driver set.

The configured Beacon gate requires its real OSC hello and atomic
contract-gated state dump. Shaper's exact v1 manifest explicitly declares that
OSC hello is not currently implemented, so the configured Weaver adapter gates
the exact manifest contract ID after the manifest-declared HTTP state snapshot.
This limitation is not hidden.

## Timeline

| Elapsed (s) | Event | Detail |
|---:|---|---|
| 0.008 | `process_started` | process=beacon, mode=--file --no-https |
| 10.048 | `process_started` | process=shaper, mode=--no-midi --no-audio --slave |
| 11.062 | `process_started` | process=weaver, drivers=harmocap,midi,ecg |
| 13.328 | `sources_started` | harmocap_fixture=/home/nicolas/Projects/HarMoCAP/examples/fixtures/two_persons.jsonl, ecg_bpm=72.0 |
| 14.389 | `scene_switched` | scene=event-demo, segment=1 |
| 14.390 | `recording_started` | path=/home/nicolas/Projects/harmonic-weaver/rehearsal/artifacts/t45-20260719T092417Z/audio/beacon_master_rehearsal.wav |
| 15.427 | `state_captured` | label=t0 |
| 60.529 | `scene_switched` | scene=sparse, phase=hot_swap |
| 70.659 | `scene_switched` | scene=event-demo, segment=2 |
| 115.736 | `state_captured` | label=end |
| 116.590 | `panic_triggered` | panic_generation=1 |
| 119.999 | `panic_cleared` | ack={'command_type': 'panic.clear', 'status': 'recovered', 'panic_generation': 1, 'activation_generation': 4} |
| 123.765 | `recording_stopped` | path=/home/nicolas/Projects/harmonic-weaver/rehearsal/artifacts/t45-20260719T092417Z/audio/beacon_master_rehearsal.wav |
| 126.357 | `rehearsal_complete` | result=PASS |
| 126.374 | `process_stopped` | process=ecg-simulator, exit_code=-15, log=/home/nicolas/Projects/harmonic-weaver/rehearsal/artifacts/t45-20260719T092417Z/logs/ecg-simulator.log |
| 126.375 | `process_stopped` | process=harmocap-replay, exit_code=-15, log=/home/nicolas/Projects/harmonic-weaver/rehearsal/artifacts/t45-20260719T092417Z/logs/harmocap-replay.log |
| 126.590 | `process_stopped` | process=weaver, exit_code=-15, log=/home/nicolas/Projects/harmonic-weaver/rehearsal/artifacts/t45-20260719T092417Z/logs/weaver.log |
| 127.406 | `process_stopped` | process=shaper, exit_code=0, log=/home/nicolas/Projects/harmonic-weaver/rehearsal/artifacts/t45-20260719T092417Z/logs/shaper.log |
| 127.406 | `process_stopped` | process=beacon, exit_code=0, log=/home/nicolas/Projects/harmonic-weaver/rehearsal/artifacts/t45-20260719T092417Z/logs/beacon.log |

## Scripted assertions

| Result | Assertion | Evidence |
|---|---|---|
| PASS | `preflight.inventory` | missing=[] |
| PASS | `preflight.file_source_size` | bytes=691200078 |
| PASS | `preflight.demo_runtime` | declared cumulative demo runtime=90.000s |
| PASS | `preflight.executable.pw-jack` | resolved=/usr/bin/pw-jack |
| PASS | `preflight.executable.scsynth` | resolved=/usr/bin/scsynth |
| PASS | `preflight.executable.sclang` | resolved=/usr/bin/sclang |
| PASS | `preflight.port.8765` | loopback socket created and port available before launch |
| PASS | `preflight.port.8080` | loopback socket created and port available before launch |
| PASS | `preflight.port.57120` | loopback socket created and port available before launch |
| PASS | `preflight.port.9002` | loopback socket created and port available before launch |
| PASS | `preflight.port.9001` | loopback socket created and port available before launch |
| PASS | `preflight.port.9100` | loopback socket created and port available before launch |
| PASS | `preflight.port.5001` | loopback socket created and port available before launch |
| PASS | `contract.beacon.golden` | contract_id=eaad56d9081d01c4a63646e0055b37b7 |
| PASS | `contract.shaper.golden` | contract_id=763efea4f567f6c9396b13b7af33c540 |
| PASS | `contract.stage.golden` | contract_id=cc2f83205e0dccf6d0b5d488883d73ad |
| PASS | `process.beacon.ready` | real hello and atomic state dump completed |
| PASS | `process.shaper.ready` | HTTP state API ready with audio and MIDI disabled |
| PASS | `process.weaver.ready` | health={'status': 'ok', 'contract_id': 'cc2f83205e0dccf6d0b5d488883d73ad', 'server_stream_id': '7cbbddae18670c2c', 'stage_revision': 12, 'panic_active': False} |
| PASS | `gate.instrument.beacon-spatial` | gate_state=ready contract_id=eaad56d9081d01c4a63646e0055b37b7 |
| PASS | `gate.instrument.shaper` | gate_state=ready contract_id=763efea4f567f6c9396b13b7af33c540 |
| PASS | `beacon.nature.loaded` | path=/home/nicolas/Projects/beacon-spatial/assets/nature-samples/dominicalito_frogs_pond.wav |
| PASS | `beacon.nature.gain_bounded` | gain=0.11999999731779099 |
| PASS | `shaper.five_voices.primed` | active_voices=5 |
| PASS | `scene.demo.routes_active` | active_scene=event-demo |
| PASS | `source.midi.hardware_absent_invalid` | cc_1 and modwheel are invalid as expected without MIDI hardware |
| PASS | `source.harmocap.replay_flowing` | last_frame_seq=117 |
| PASS | `source.ecg.raw_flowing` | last_frame_seq=28 |
| PASS | `scene.hot_swap.to_sparse` | active scene changed atomically and activation generation incremented |
| PASS | `scene.hot_swap.return_demo` | demo scene restored after sparse interlude |
| PASS | `timeline.demo_runtime_ge_90s` | measured cumulative demo runtime=90.000168s |
| PASS | `route.focused_subject.five_harmonics` | observed_harmonics=[1, 2, 3, 4, 5] |
| PASS | `route.ecg.rhythmic_pulses` | full-gain beat pulses=113 |
| PASS | `panic.stage.latched_safe` | outcomes={'beacon-spatial': 'ok', 'shaper': 'ok'} |
| PASS | `panic.shaper.voices_released` | active_voices=0 |
| PASS | `panic.beacon.silence_profile` | master=0.0 nature_gain=0.0 |
| PASS | `panic.routes.gated` | route writes stayed at 38357 for 3 seconds while sources continued |
| PASS | `panic.clear.routes_recovered` | route writes before=38357 after=39745 |
| PASS | `panic.clear.shaper_rearmed` | active_voices=5 |
| PASS | `panic.clear.beacon_recovered` | master=0.3809061050415039 |
| PASS | `audio.wav.created` | exists=True bytes=41984088 |
| PASS | `audio.duration` | duration=109.333333s required>=100.000168s |
| PASS | `audio.finite` | nan=0 inf=0 |
| PASS | `audio.signal_flow` | peak=0.219502091 rms=0.009157086 non_silence_ratio=0.961897675 |
| PASS | `weaver.behavior_reports.present` | report_root=/home/nicolas/Projects/harmonic-weaver/reports/t45-20260719T092417Z |
| PASS | `process.shutdown.all_managed_processes` | all managed process groups stopped after SIGTERM |

## Audio statistics

SuperCollider recorded its master output. These numbers prove a finite, non-silent signal was written; they do not claim a person heard it.

- Duration: `109.33333333333333` seconds
- Non-silence ratio: `0.961897675304878` at absolute threshold `0.0001`
- Peak absolute sample: `0.21950209140777588`
- RMS: `0.009157085768100537`
- NaN / Inf: `0` / `0`

## State-dump diffs and panic/recovery

Machine-readable pre/post swap, panic, and recovery diffs are in `rehearsal/artifacts/t45-20260719T092417Z/state_diffs.json`. The exact Stage, Beacon, and Shaper snapshots named in the artifact
tree are the primary evidence. Panic assertions require Shaper voices inactive,
Beacon master and nature gain at zero, no route transport writes during a
three-second gated window, and route writes resuming after `panic.clear`.

## Artifact tree

- `rehearsal/artifacts/t45-20260719T092417Z/audio/beacon_master_rehearsal.wav` (41984088 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/audio_stats.json` (400 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/beacon_runtime_sync.json` (1925 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/instrument_outputs.jsonl` (11490249 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/logs/beacon-sclang.log` (6818 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/logs/beacon-scsynth.log` (268 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/logs/beacon-webui.log` (611 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/logs/beacon.log` (1048 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/logs/ecg-simulator.log` (630 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/logs/harmocap-replay.log` (0 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/logs/shaper.log` (1084 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/logs/weaver.log` (432 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/results.json` (13444 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/run_manifest.json` (1595 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/runtime_ready.json` (445 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/runtime_status.final.json` (269704 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/runtime_status.json` (269704 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/shaper_runtime_sync.json` (429 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/state_diffs.json` (4582 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/end.beacon.json` (2036 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/end.shaper.json` (1096 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/end.stage.json` (269179 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/mid_post_swap_sparse.beacon.json` (2049 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/mid_post_swap_sparse.shaper.json` (1040 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/mid_post_swap_sparse.stage.json` (265557 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/mid_pre_swap.beacon.json` (2035 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/mid_pre_swap.shaper.json` (1096 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/mid_pre_swap.stage.json` (269203 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/mid_return_demo.beacon.json` (2034 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/mid_return_demo.shaper.json` (1101 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/mid_return_demo.stage.json` (269199 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/panic.beacon.json` (2005 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/panic.shaper.json` (1027 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/panic.stage.json` (269143 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/recovery.beacon.json` (2036 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/recovery.shaper.json` (1099 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/recovery.stage.json` (269216 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/t0.beacon.json` (2032 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/t0.shaper.json` (1096 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/states/t0.stage.json` (269127 bytes)
- `rehearsal/artifacts/t45-20260719T092417Z/timeline.json` (2931 bytes)
- `reports/t45-20260719T092417Z/accepted_contract_ids.json` (754 bytes)
- `reports/t45-20260719T092417Z/behavior_events.jsonl` (38467 bytes)
- `reports/t45-20260719T092417Z/latency_summary.json` (524 bytes)
- `reports/t45-20260719T092417Z/run_config.json` (365 bytes)
- `reports/t45-20260719T092417Z/scene_snapshot.json` (6687 bytes)
- `reports/t45-20260719T092417Z/state_timestamps.jsonl` (15095816 bytes)
- `reports/t45-20260719T092417Z/summary.json` (38 bytes)

## Explicitly unverified

- Audible monitoring or subjective audio quality by a human.
- R24 live input or any other audio-interface input.
- Physical MIDI hardware, camera input, live people, ESP32/AD8232 hardware,
  EEG hardware, or EEG routing.
- Shaper real-time audio output; Shaper is configured with `--no-audio` by design.
- Shaper OSC hello/state dump, because the installed real manifest marks that
  wire handshake as planned rather than implemented.
- The supplied characterization of `cymatic-control/test_ecg_stream.py` as a
  simulator; the file is verified to be a listener, so it is inventory-only.
