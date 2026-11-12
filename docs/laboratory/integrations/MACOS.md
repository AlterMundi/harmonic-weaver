# Native macOS Harmonic Lab receiving

This is the maintained shared route for the requested Mac mini installation,
not a claim of completed receiving or a second application. Exact chip, macOS,
interface, camera and existing installations must come from the receiving
operator. Do not copy the Linux PipeWire/ALSA launcher or a CUDA lock file.

## Portable handoff 1 — 2026-11-12

Oliva's receiving report (Matrix message `6f06f88d-4ad5-48bc-bb17-784c217b3d79`)
only establishes an October 12–13 historical demo with Darwin, Python 3.12.13
and a Logitech C920. Current chip/RAM/macOS, audio/MIDI devices, checkouts,
environments and local changes remain unknown. The identified SSH route is a
forced demo status/options helper; it is **not** a shell, inventory or install
route. No Mac call or access expansion is part of this handoff. Oliva has already
asked Ani for the machine details; do not duplicate that question. Cuevanico is
a different resource. Consolidate coordination in the existing detailed thread;
there is one receiving plan.

Exact source cutoff, all in the existing AlterMundi repositories:

| Repository | Complete source revision | Role |
| --- | --- | --- |
| harmonic-weaver | `b01d79246e8ca1f49abf70b79e8fffa7670adc92` | Joint entry and native body backend selection |
| beacon-spatial | `74fbde89dd2edd0f69ee935fd52f59517ba23830` | CoreAudio companion, existing DSP/OSC/UI |
| harmonic-shaper | `dcebaf84764b47836a4e8d523ec0ef8b4cbccd5d` | Existing native synthesis backend |
| HarMoCAP | `25fda8d74c663a573aab6bc8f540c2c46ef250b9` | Existing MPS/CPU pose implementation |

This selects a reproducible code baseline, not four latest-main promises or
Mac-tested dependency locks. HarMoCAP remote main was also observed at
`4d56e4d3da534287042e5eb870106ba0c589eb5f` (named-camera fix and Face guide);
that later source is not silently included in this cutoff. Reconcile any newer
receiving changes explicitly. Eko's separate Mac browser/Face review packet is
not qualification of native pose/audio or a substitute for the requested stack;
its publication and paused-goal holds remain independent.

## Cutoff amendment 2 — Sai companion contribution

The source audit found that the selected HarMoCAP baseline omitted Sai's
`2d566f1a9370a44eae2b96d3066b3d4e68808021` named-camera fix. Use HarMoCAP
`4d56e4d3da534287042e5eb870106ba0c589eb5f` for the current receiving cutoff;
the other three source revisions in handoff 1 stay the same. The change treats
only regular media files as paced/EOF-terminated files, preserving live behavior
for named devices and URLs. The two capture-wakeup regression tests passed in
the existing Linux laboratory environment after adoption; that is not a Mac
camera/driver test. See [Sai contribution audit](SAI_CONTRIBUTIONS.md).
Handoff 1 remains historical preparation evidence; this amendment supersedes
its deliberate exclusion of the later HarMoCAP revision.

## Reuse the installation

Keep the four existing sibling checkouts: `harmonic-weaver`, `harmonic-shaper`,
`HarMoCAP`, and `beacon-spatial`. Update through their ordinary Git routes while
preserving local commits, presets, calibration, weights and private media.
Use each project's existing environment/pyproject; HarMoCAP's portable dependency
list is in pyproject.toml, not the historical server GPU requirements.lock.
Python must satisfy HarMoCAP's >=3.11 floor; the web build currently uses Node22.
Build the ordinary Weaver frontend through its maintained launcher/dependency
preparer. Do not add a separate Mac frontend, App, account or login system.

Spatializer requires the native SuperCollider application, sc3 plugins, ATK Quark
and its kernels. Those are native dependencies, not supplied by pip. Reuse their
installed copies. Kernel/architecture/driver compatibility needs actual receiving
checks, not a successful source pull. The selected live guitar path does not
require copying the historical large Beacon WAV.

Only after the actual receiving install route/scope is established, use the
selected project's existing Python environment. Missing environments can use
`python3 -m venv .venv`; install Weaver with `.venv/bin/python -m pip install -e '.[lab]'`,
Shaper and HarMoCAP with their respective `.venv/bin/python -m pip install -e .`,
and Spatializer with `.venv/bin/python -m pip install -r requirements.txt`.
Do not reinstall a working environment or replace private checkpoints. These are
source dependency declarations, not a tested Mac lock; record resolved versions
and stop at a concrete architecture/dependency error. The body launcher expects
an existing pose checkpoint; select it with `HARMOCAP_CHECKPOINT` rather than
starting an unbounded model/media download. Node 22 and npm use the maintained
`prepare-laboratory-dependencies.mjs` and build. No global Python/package-manager
change is prescribed here. Native PortAudio availability must be checked for
Shaper's sounddevice; SuperCollider/ATK/plugin versions and architectures must
be recorded separately from Python dependencies.

Choose the exact input and output device names from the receiving CoreAudio
inventory. Check the actual selected interface/OS driver, channels, sample rate,
monitoring and microphone/camera permissions locally. Respect the receiving
macOS privacy controls and existing authorized access. If a required local action
cannot be completed through that access, retain the exact gap rather than
bypassing it or announcing completion.

## One established entry

After the native companion update and exact device selection:

```sh
export BEACON_INPUT_DEVICE='Exact receiving CoreAudio input'
export BEACON_OUTPUT_DEVICE='Exact receiving CoreAudio output'
export HARMONIC_SHAPER_DEVICE='Exact receiving PortAudio output'
scripts/start-live-stack.sh --guitar-lab --with-weaver --no-guitar-controller
```

These device names are placeholders. `--no-guitar-controller` removes the
CyberBrick requirement when this computer has no physical guitar motor board;
it does not remove Spatializer guitar input or body/synthesis software. If that
board is part of the selected receiving setup, inspect its real serial identity
and install the existing supported panel instead of inventing a Linux by-id path.
The original panel analyzer's `arecord` capture remains Linux-specific; its
optional Mac equivalent is not qualified by this CoreAudio launcher.

On macOS the joint entry uses the native Spatializer companion (no PipeWire,
JACK aliases, `ss` or Linux `script -c`) and selects the existing body launcher
with `--audio-backend native`. HarMoCAP's existing `auto` path selects MPS when
available, otherwise CPU; no NVIDIA/CUDA requirement is imposed on a Mac.
No camera/source, motor, board write or recording is started merely by this
composition. Select camera/source and calibration in the existing laboratory.

The native Spatializer uses scsynth's documented exact `-H input output` device
selection and the existing DSP/OSC/UI. Its sclang has an owned Python PTY;
SuperCollider binaries can come from PATH or the standard application bundle.
The native UI stays on loopback and no public tunnel/account/network policy is
created. The usual finite session/owned-only cleanup and bounded latest logs
remain. The Linux branch retains its verified JACK graph path.

## Channels, ports, local effects and recovery

The native Spatializer requests 48 kHz, two input channels and two output
channels. Existing live DSP reads the first input channel (CoreAudio channel 1)
and emits a stereo pair (channels 1–2); this is a configuration request, not
proof of hardware mapping. Choose the actual interface and verify the signal
there. Shaper's PortAudio output name is selected independently; do not assume
that it equals the CoreAudio name or that separate devices share a clock.

The selected composition uses Spatializer HTTP 5050, sclang OSC UDP 57120,
scsynth UDP 57110, the existing body laboratory HTTP 8765 and its managed Shaper
HTTP 8085. The optional motor panel HTTP 18879 is skipped by the documented
command. Preserve existing owners of these ports; do not kill unrelated servers
or use the legacy launcher's automatic orphan reclamation to free them.

Before changing a checkout, record its HEAD and inspect its local diff. Preserve
presets, calibrations, models and media in place. Planned writes are the selected
source/dependency updates, the ordinary frontend build, and the existing local
session state/logs; no firmware, account, login, firewall, router or provider
change is included. Run the joint entry in the receiving operator's foreground
terminal (or existing named persistent terminal if authorized). Ctrl+C closes
only children started by this composition; borrowed components remain running.
The composition defaults to eight hours, owns one latest state/lock and bounded
1 MiB tail logs per child. Do not enable recording or create extra media copies
as an installation check.

Recovery: stop the owned session, retain the bounded failure log and actual exit
status, and return only task-modified clean source to its recorded prior revision
through normal Git operations. Never hard-reset a dirty checkout. Preserve any
new personal settings and the previous environment's dependency inventory;
reconcile dependencies with that prior source instead of deleting an existing
environment. This route installs no recurring service, system login hook or
network exposure to remove. A Mac-native installation has not yet happened,
so there is no receiving rollback or acceptance receipt to claim.

## Evidence required to finish receiving

Record installed source/environment versions and actual startup/stop of the
owned session, exact native hello/state synchronization, selected devices and
ports, real input/output signal and human hearing. Then check Shaper audio and
HarMoCAP tracking with the chosen camera, retaining personal source calibration.
Measure useful latency/continuity instead of inferring them from an M-series
chip or green imports. Preserve existing source presets, including accepted
six-voice behavior. A component list does not prove their combined operation.

The new command/device selection, source route gates and lifecycle paths have
Linux-hosted unit checks. Those are implementation evidence only. No Mac
CoreAudio/ATK/driver/physical-input/tracking/listening acceptance is claimed yet.
Coordinate actual receiving through the human-selected operator; completion
notification to either human follows actual checks, not message admission.

## Primary references

- [SuperCollider for macOS](https://supercollider.github.io/downloads)
- [Audio device selection](https://doc.sccode.org/Reference/AudioDeviceSelection.html)
- [scsynth command options](https://doc.sccode.org/Reference/Server-Architecture.html)
- [ATK installation](https://github.com/ambisonictoolkit/atk-sc3)

These references explain native dependencies; they do not establish the current
Mac mini's permissions, installed versions or compatible audio driver.
