# Native macOS Harmonic Lab receiving

This is the maintained shared route for the requested Mac mini installation,
not a claim of completed receiving or a second application. Exact chip, macOS,
interface, camera and existing installations must come from the receiving
operator. Do not copy the Linux PipeWire/ALSA launcher or a CUDA lock file.

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
