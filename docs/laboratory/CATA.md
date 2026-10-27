# Cata: bounded CPU laboratory

Nicolás selected Cata on 2026-10-27 after an unexpected Legion shutdown.
The operator independently verified the receiving hostname, the existing
ThinkPad CPU-only route and an attached Logitech C920e. This does not diagnose
Legion's shutdown or establish live performance on Cata.

## Installation and ownership

Use the ordinary `~/Projects/harmonic-weaver`, `~/Projects/harmonic-shaper`
and `~/Projects/HarMoCAP` checkouts and their existing `.venv` directories.
The supported launcher owns Weaver and its Shaper child. HarMoCAP provides
the separate perception environment. Preserve each project's requirements;
HarMoCAP's `requirements.lock` is a historical GPU snapshot, not the portable
installation recipe. Install CPU Torch/TorchVision from the official CPU wheel
index before installing HarMoCAP and the laboratory's `av>=12,<17` dependency.
Use HarMoCAP's `scripts/fetch_models.py` to obtain and verify its published
pose checkpoint. The launcher needs Node/npm to build the existing web UI and
PipeWire's JACK bridge for the selected audio route.

The retained task setup/run scripts, logs and terminal exit files are under
`~/.local/state/harmonic-weaver/cata-20261027/` on Cata. Setup runs in named
screen session `movement-setup-20261027`; inspect it and its exit file before
retrying. SSH loss is not process completion. No startup service is installed.

## Bounded launch

The prepared run script uses a transient user scope around the supported
launcher, with a total CPU quota of 150% (1.5 logical CPUs across the scope's
processes), CPUWeight 50, and the following application environment:

```sh
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=2
systemd-run --user --scope --unit=weaver-cata-20261027 \
  -p CPUQuota=150% -p CPUWeight=50 \
  ./scripts/start-laboratory.sh --audio-backend jack --device "R24 Analog Stereo" \
  --tracking-device cpu --audio-block-size 1024
```

Run from the Weaver checkout in a retained named screen session. The quota is
an aggregate process budget, not a temperature guarantee, and does not constrain
an independently opened browser. Inspect temperatures and audio underflows
during the real trial. Do not change host fan/clock policy or unrelated workloads
merely to start the instrument. A larger audio buffer trades latency for callback
headroom; physical latency and musical preference require listening.

The receiving JACK device query identified both built-in stereo and the R24;
the prepared launcher explicitly selects the R24 rather than the first device.

The first trial with the published ft2 medium checkpoint had processed-frame
ages around 1.5 seconds under the initial 200% quota. The selected lightweight
variant uses HarMoCAP's existing `yolo26n-pose.pt` model option, explicit CPU
perception, image size 256, 640×480 capture at requested 10 fps, ByteTrack and
at most two detection/identity slots. The CPU quota was reduced to 150%.
Requested camera rate is not measured
inference throughput. Lower compute cost does not establish anatomical accuracy.

Import the selected saved musical preset through the supported preset API,
excluding Legion's source-specific calibration. Keep its six voices, tuning and
routes intact. Opening a new camera requires an observed calibration for that
source/person. Do not transplant Legion's video, tracking, session database or
calibration into this host. Camera recording remains opt-in.

## Verification and recovery

Check both Weaver's `/api/state` and Shaper's `/api/audio/voices`, the actual
scope quota and the camera's ready/error state. API audio connectivity is not
physical hearing; a ready camera is not a detected/calibrated performer.
Browser visibility, pose cadence, calibration, audible response and sustained
thermal behavior are separate observations.

Stop only this task's named scope to close its owned processes, retaining data.
The scope has no restart policy or boot activation. Inspect `runtime-exit`,
`runtime.log` and the named screen session before reopening; never replay a
camera/preset operation solely because an SSH invocation timed out.

## Receiving result, 27 October

Setup exited 0; the web build and supported dependency check passed. Weaver
`61aa863`, Shaper `dcebaf8` and HarMoCAP `25fda8d` were selected. CPU Torch
reports `2.14.1+cpu`; the environments and checkpoint downloads remain on Cata.
The saved musical preset was imported/applied through the API with calibration
explicitly null, preserving its six voices and disabled pitch/phase routes.

The Logitech capture node was independently identified as video2 on this boot
(the integrated camera is video0). Resolve it again after hardware changes.
The live nano camera reached ready/error-null. Five short observations reported
processed-frame ages about 282–503 ms; these are age samples, not a measured
frame rate or physical movement-to-sound latency. Temperatures were 72–78 C in
that sample, not a demonstrated sustained equilibrium. No selected performer or
calibration was present in those observations.

The scope was active with CPUQuotaPerSecUSec=1.5 s. Shaper reported running at
48 kHz, 1024-frame callbacks and zero underflows/status events at the inspected
sample. A browser open was requested on Cata's desktop and persistent local web
connections were observed. Physical screen visibility, hearing, pose quality,
calibration and performance acceptance remain with the human trial. Recording
was not started. The retained `ready-check.json` contains the scoped observations.
