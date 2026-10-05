# Conditioning tracking and local 3D candidates

## Causal conditioning, 2026-10-04

Nicolás reports that detector jumps, especially hips, become false musical events.
Local frame inspection identifies adjacent-frame left/right hip label swaps as one
concrete contributor. Raw inference and cached observations remain unchanged.

`MotionModel` owns a shared conditioning stage before baseline/local/relational/
angular/collective analysis. It uses source timestamps, not rendering cadence:

1. Optional hip-pair continuity guard: exchange labels only if the swapped assignment
   is decisively closer to previous positions/velocities (cost <35% of direct cost,
   reduction >0.05² projected torso units). This stabilizes labels, not anatomical truth.
2. Trailing median, default three measurements, suppresses short-lived outliers.
3. Position response, default 50 ms, plus an acceleration bound per COCO-17 joint.
   Initial limits: hips 35, shoulders 60, elbows/knees 120/100, wrists 240,
   ankles 180 T/s²; face limits are 80–100. These are tunable conditioning parameters
   in projected torso units, not physiological limits or metres.

The filter estimates positions; it does not repair identity assignment or prove
that a trajectory is physical. Small latency and suppression of real rapid motion
are tradeoffs. Missing/held joints are not filled. Each joint resets on invalid
support/time gaps; the model resets at source/body/seek/loop discontinuities.
Baseline without explicit scale uses the first observed torso within that epoch;
other models retain their explicit calibration requirement. No recalculation of
tracking is needed when these parameters change.

Presets carry the controls. The filter defaults off so accepted reference presets
can reproduce their previous response. It is enabled in Nicolás's current session
for this trial. Modelos exposes the switch, hip guard, median length, response time
and 17 named acceleration limits. Figura can show raw or conditioned skeleton.
`motion_frame` remains raw; `conditioned_motion_frame` is an explicitly separate
estimate channel, and feature diagnostics identify corrected labels/clamped joints.

Offline evaluation uses the same MotionModel stage. Conditioning changes spectra,
correlations and geometry: research comparisons must preserve/declare these settings.
No inference about HIT follows from smoother tracking or smaller residuals.

Recovery correction, 2026-10-05: position/prediction errors require uninterrupted
observations for that joint between the historical reference and the current sample.
Reacquisition after a missing, held or omitted joint warms a new prediction history;
it cannot measure displacement from a pre-loss coordinate. Other joints retain
their valid histories. The bounded filter also forgets joints omitted from a frame,
as the native One-Euro path already did. No raw cache or preset default changes.

Verification: isolated hip swaps, irregular source cadence/acceleration bounds,
preservation of steady motion, no filling missing/held joints, seeks and all model
paths. Local body comparison/configuration/plots stay in the private data directory;
no video, frames, identities or body result tables are published.

## State of the art: decision review, 2026-10-04

### Immediate local direction and HarMoCAP reuse

The model research below is retained for later; no new model installation or
training is part of the immediate glitch repair. Mariano's public HarMoCAP main
(`bdeebbf`, 2026-08-17) is already an ancestor of our checkout (`25fda8d`). The
other public branch inspected, `agent/fix-visible-person-focus`, is historical
July identity/focus work, not a newer pose model. Unpublished work is unknown.

HarMoCAP uses YOLO26m-pose fine-tuned on CrowdPose plus COCO (COCO-17 2D), person
association and a causal One-Euro validity/smoothing layer. Weaver's perception
worker uses the detector and identity layer; raw caches intentionally precede
conditioning. Our current capture uses `imgsz=320`; the ft2 training used 640.
The original batch-16 training recipe documents approximately 10.3 GB VRAM and
cannot simply be reused on this machine's 6 GB GPU. Fine-tuning might address
domain errors but does not add temporal reasoning, 3D or joint rotations to YOLO.

`tracking_smoother=harmocap_one_euro` now selects the actual checkout's
`harmocap.smoothing.OneEuroFilter` (implementation path in diagnostics), with
native defaults: minimum cutoff 1 Hz, beta .15, derivative cutoff 1 Hz. It replaces
the bounded median/response/acceleration/hip-guard path; it does not stack with it.
Three smoothing parameters are editable in Modelos and stored in portable presets. The
HarMoCAP checkout selected by `HARMOCAP_DIR` is required when using this option.
Positions use the raw frame's coordinate units, as in native HarMoCAP; beta is
unit-dependent. Missing/held support resets the joint; no retained coordinate is
promoted to observed, and no hold-last motion is generated for synthesis.

2026-10-05: an independent, opt-in `tracking_one_euro_hip_swap_guard` now
repairs decisive hip-label continuity mismatches before native smoothing. Default
false preserves the accepted One-Euro response. It shares the existing bounded
assignment criterion (crossed cost <35% of direct cost and improvement >0.05²
projected torso units), using the previous corrected measurement/velocity for
native One-Euro, not its delayed smoothed position. Confidence follows the assigned
measurement; raw labels/cache remain unchanged. A missing/held/omitted hip or time
discontinuity removes that assignment history. No median or acceleration cap is
enabled. Torso scale, if absent, is estimated only to normalize this heuristic's
threshold; it does not calibrate the movement model. Without usable scale,
One-Euro continues and diagnostics report the guard unavailable. This cannot
distinguish every true turn from detector relabeling; disable it when it damages
real movement. Modelos exposes the switch and diagnostics report corrections.

Native smoothing was replayed on the existing private 60-second cache, including
the two previously inspected jumps. Local configuration/results/scripts remain
in the private checks directory. Smoothed acceleration falls substantially, but
this alone neither repairs wrong joint labels nor demonstrates preserved real
movement. A synthetic 30 FPS, amplitude .05 frame-height sinusoid under native
defaults retains about 71% amplitude at 1 Hz with 113 ms phase delay, and 31% at
3 Hz with 52 ms phase delay (fit after five seconds of warmup). This is filter
response, not measured live latency or body ground truth. Listening is pending.
Automatic checks cover native implementation parity, absence/held support,
person loss, gaps/seeks and all five model paths, plus existing contracts,
runtime and evaluation tests (60 distinct tests) and the web build. The local
session was switched to native One-Euro and runtime telemetry confirmed six voices
and no audio/runtime error. Its previous source, person, explicit same-source
calibration and paused transport position were restored. This is not perceptual
acceptance. Reference preset defaults remain unchanged.

Next local work, conditional on this trial:

1. Compare bounded versus native One-Euro on the same cached person/source,
   including the identified jumps, turns and genuine fast wrists. Adjust existing
   cutoff/beta controls before adding complexity; retain the accepted audio ratios,
   continuous voices and articulation. Lower acceleration alone is not success.
2. If false motion persists, separate outlier/label continuity repair from smoothing.
   Improve hip-pair assignment using measured support and short source-time history;
   inspect pelvis centre and width separately. Avoid enforcing constant projected
   bone lengths, which change legitimately with turns/perspective. Reject dubious
   support explicitly instead of concealing it as an observed interpolated point.
3. Tune by joint/region if a single response dampens wrists while stabilizing hips.
   Check onset/phase and recovery, not just average jitter. Keep raw caches reusable
   and the same causal path in live and replay. No retraining is required for this.
4. If raw pose errors remain systematic, compare 320/640 on small existing local
   segments before considering targeted, manually corrected rope-flow fine-tuning.
   Split any eventual training/evaluation by session/source, not adjacent frames;
   teacher-model labels are suggestions, not independent ground truth.

A useful HarMoCAP collaboration proposal would be a configurable conditioning
stage separating continuity/outlier handling from adaptive smoothing, with
observed/held/invalid semantics and causal replay tests. Before implementing there,
ask Mariano or his agents about unpublished changes and contribution instructions.
Do not send messages autonomously; no outreach has occurred in this trial. This
proposal depends on finding a concrete remaining problem in the local comparison.

The initial four-model shortlist was insufficient. It omitted recent causal video
recovery, multi-person articulated tracking, efficient rotation uplift, and explicit
recovery of velocity/acceleration. This review replaces its unconditional
MediaPipe-live / GVHMR-video recommendation with the priorities below.

Research question: for fast, turning, sometimes occluded rope-flow with one or two
people, which locally executable video models can reduce false motion without
suppressing real rhythm, while exposing 3D positions and articulated rotations?
The current raw/conditioned tracker is the engineering baseline. Relevant outcomes
are false events, identity continuity, retained motion amplitude/phase, and source-to-
audio latency. A prettier mesh or lower raw acceleration alone does not decide this.

Applied skills: shared `scientific-research-workflows` / `literature-search` and
`research-and-knowledge-work` / `arxiv`, read from `~/.hermes/skills/`.
This is a focused narrative engineering review, not an exhaustive systematic review
or a pooled ranking of incompatible benchmarks. Search coverage: arXiv, CVF
proceedings, OpenAlex discovery, author project pages, and official repositories;
2024 through 2026-10-04, with older practical baselines retained. Search families:

- `streaming human mesh recovery real time rotations lightweight`
- `causal human mesh recovery 2026`
- `human motion recovery 2026 September` and `human mesh recovery 2026 August temporal`
- `Efficient 2D to Full 3D Human Pose Uplifting`
- `Hitting the Gym with Fit3D`
- Model-specific searches for code, checkpoints, temporal processing and hardware.

Include methods supplying motion geometry, rotation estimation, temporal correction,
or useful local implementations. Exclude appearance-only avatar rendering from the
main comparison, and retain additional-sensor work only as a later capture option.
Read papers beyond abstracts, inspect implementation/asset availability, and keep
reported timings tied to hardware and timing scope. No new backend was installed or
benchmarked on Legion in this review. Repository paths below are mutable upstream
references, not a frozen local experiment manifest.

### Models that change the engineering choice

| Candidate / primary sources | Representation and temporal behavior | Availability and consequence for this laboratory |
| --- | --- | --- |
| [MediaPipe Pose Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker) | 33 image/world landmarks; VIDEO and LIVE_STREAM processing. No complete articulated rotation output. | Released local on-device baseline. Useful for measuring whether lightweight inferred depth helps; not a solution for bone twist or guaranteed identity continuity. |
| [RTMW3D](https://arxiv.org/abs/2407.08634), [official model zoo](https://github.com/open-mmlab/mmpose/blob/main/projects/rtmpose3d/README.md) | Direct image-to-whole-body 3D keypoints, including more hand/foot detail than COCO-17. Does not supply a complete articulated rotation rig. | L/X checkpoints are published. Important omitted lightweight comparator; detector, identity association and temporal conditioning still belong to the pipeline. Local speed remains unmeasured. |
| [Multi-HMR 2](https://arxiv.org/html/2606.14841v1), [code/weights](https://github.com/naver/multi-hmr2) | Multi-person camera-centric meshes with Anny bone rotations and estimated camera intrinsics. Framewise reconstruction plus online association using appearance and pelvis history. | Released 2.b checkpoint and Python API. Paper reports 4–5 FPS on V100, 20 FPS with compilation. Identity association is not learned temporal smoothing of joint poses. Particularly relevant to two-person footage. |
| [OnlineHMR](https://arxiv.org/html/2603.17355v1), [code](https://github.com/Tsukasane/Video-OnlineHMR) | SMPL joint rotations/root motion; causal historical attention plus incremental SLAM. Distinguishes whole-system causality from offline world reconstruction. | Code and download script for its checkpoint exist; SMPL assets require registration. Full pipeline reports 3.3 FPS / 0.30 s delay on RTX 6000 Ada. Scientifically relevant, but not our first full live backend. A camera-relative branch without SLAM would be a separate, unbenchmarked engineering variant. |
| [SAM 3D Body](https://arxiv.org/abs/2602.15989), [estimator](https://github.com/facebookresearch/sam-3d-body/blob/main/sam_3d_body/sam_3d_body_estimator.py) | Single-image MHR rig with body, hands and feet; exports body parameters, joint coordinates and global rotations. Promptable with image evidence. | Official code exists; checkpoint access is gated. Strong pose/rig candidate, but independent frame predictions do not solve temporal glitches by themselves. |
| [Fast SAM 3D Body](https://arxiv.org/html/2603.15603v1), [code](https://github.com/yangtiming/Fast-SAM-3D-Body) | Faster SAM pipeline plus learned MHR-to-SMPL conversion; camera/video publisher exists. | Code and conversion-network weight files are present; original SAM/body assets still apply. Paper's 65 ms teleoperation result is on RTX 5090, not RTX 2060. Up to 10.9× pipeline acceleration is distinct from the much larger conversion-only speedup. Optional smoothing needs its own causality and output-consistency check. |
| [GVHMR](https://github.com/zju3dv/GVHMR) + [HTD-Refine](https://arxiv.org/html/2605.26879v1), [refinement code](https://github.com/ant-research/HTD-Refine) | Temporal articulated video recovery plus refinement toward predicted 3D velocities/accelerations; refinement optimizes the full sequence. | Both code/checkpoint routes exist, with licensed SMPL/SMPL-X assets. Strong cached-video comparison for dynamics, not a causal live replacement. HTD demo expects 30 FPS and a primary subject; supply explicit matching boxes/track for multi-person input. |
| [GEM-X](https://github.com/NVlabs/GEM-X), [model](https://github.com/NVlabs/GEM-X/blob/main/docs/MODEL_OVERVIEW.md), [demo](https://github.com/NVlabs/GEM-X/blob/main/docs/DEMO.md) | Video-based SOMA motion, 77 joints with articulated body/hands/face. Camera/global outputs; approximately 520M-parameter temporal model plus upstream feature/keypoint models. | Checkpoints and ONNX demo available, including a keypoint-only input option. Repository code is Apache-2.0; associated model has NVIDIA Open Model terms. Recorded-video candidate; accelerated inference does not establish end-to-end causality, fit or latency on our hardware. |

The Multi-HMR 2 implementation exposes `bone_poses`, `rest_bone_poses`, `j3d`,
`transl_pelvis`, and `track_id` in
[PersonOutput](https://github.com/naver/multi-hmr2/blob/main/src/multihmr2/models/detr_root_relative/decoder.py).
Its [video helper](https://github.com/naver/multi-hmr2/blob/main/src/multihmr2/api.py)
extracts frames before sequential inference. Use its lower-level model/tracker for a
live adapter; do not confuse a causal model with a camera-ready streaming API.
`--lowres` reduces body mesh size, not the ViT encoder's input cost.

Other relevant branches:

- [Neural Localizer Fields](https://arxiv.org/html/2407.07532v1),
  [released models](https://github.com/isarandi/nlf): dense body point prediction
  with parametric fitting to obtain rotations and per-point uncertainty. A useful
  position/rotation comparator; raw nonparametric XYZ is not already a rotation rig.
  Do not quote batched fitting throughput as camera-to-pose latency.
- [Efficient full 3D uplift](https://arxiv.org/html/2504.09953v1),
  [implementation](https://github.com/kaulquappe23/full_3d_hpe_uplifting): directly
  estimates positions and rotations from 2D pose sequences. Code and an AMASS weight
  file exist. Its central-frame sequence includes future observations: a fast
  forward pass does not make this published model causal. Lifting also cannot undo
  all upstream 2D identity/left-right errors.
- [HybrIK-X](https://github.com/jeffffffli/HybrIK) provides an established
  analytical/neural inverse-kinematics route to whole-body rotations. Keep as a
  fallback comparison, not a claim of being the strongest 2026 temporal model.
- [WHAM](https://github.com/yohanshin/WHAM) remains a temporal SMPL comparator.
  Camera-relative operation and world recovery with future-dependent VO have
  different causality contracts; do not apply one latency claim to both.
- [DETRAM](https://arxiv.org/html/2607.09089v1) propagates per-person queries and
  supports prompting a chosen person. Reported 10.87 FPS uses RTX A4000; prompted
  evaluation includes oracle boxes for missed detections. An official released
  implementation/checkpoint was not located in this sweep, so it is a research
  lead rather than a ready dependency.
- [FootMR](https://twehrbein.github.io/footmr-website/),
  [code](https://github.com/twehrbein/FootMR): specialized foot-motion correction
  addresses failures that overall body scores can hide. Consider when foot
  articulation becomes an actual route in the instrument.

### What the temporal evidence actually establishes

[HTD-Refine's results](https://zju3dv.github.io/htd-refine/) are unusually relevant:
on EMDB-2, GVHMR refinement reduces reported jitter from 17.2 to 7.2 and acceleration
error from 10.4 to 7.9, while foot sliding worsens from 4.0 to 5.7. This supports
measuring actual dynamics and checking tradeoffs, rather than minimizing a single
smoothness score. It does not validate our acceleration limits or establish
accuracy on rope-flow. Its whole-sequence optimizer cannot be inserted unchanged
into causal live operation.

[OnlineHMR](https://arxiv.org/html/2603.17355v1) also evaluates motion spectra and
regularizes velocity/acceleration. This motivates checking frequency content,
but a general motion-band assumption must not become a hard rule that removes
fast wrists or rope transients. The existing filter's cap is a configurable
conditioning heuristic in projected torso units, not a measured anatomical limit.

The [Fit3D benchmark study](https://pmc.ncbi.nlm.nih.gov/articles/PMC13413046/)
explicitly limits its evidence to controlled single-person fitness capture and
sparsely sampled frame metrics; it does not credit dense temporal consistency.
Do not transfer a fitness benchmark winner to two-person rope-flow without checking
turning, back/side views, occlusions and timing. Likewise, root-centered or
per-frame Procrustes-aligned accuracy can conceal root jumps that trigger our audio.

### Local hardware: plausible is not verified

Legion has RTX 2060 / 6 GB VRAM. None of the above paper timings measures this host.
Weights fitting in memory is different from usable latency; precision, temporary
activations, detectors and concurrent models count too. Avoid assuming BF16 support
or transferring a 5090/V100/6000 Ada number to this GPU.

A more relevant implementation report is
[AmmarkoV/SAM3DBody-cpp](https://github.com/AmmarkoV/SAM3DBody-cpp): single-person,
25-frame warm measurement on RTX 1000 Ada **6 GB**, reports 273 ms/frame with CUDA EP
and 170 ms/frame (5.9 FPS) with TensorRT FP16. The report also identifies output
changes from switching precision. This demonstrates a 6 GB route on another GPU,
not confirmed fit/speed/rotation accuracy on RTX 2060, and not peer-reviewed evidence
of tracking quality. Inspect actual runtime provider rather than silently accepting
TensorRT fallback. This belongs in the local feasibility shortlist.

[localai-org/sam3d.cpp](https://github.com/localai-org/sam3d.cpp) is another native
CPU/Vulkan route. Its frame estimates are independent and detailed hand refinement
is outside supported scope. Its reported browser pipeline latency is scoped to
render submission, not physical motion-to-display or motion-to-audio latency.
A native rewrite alone is not evidence of smoother or more faithful tracking.

### Revised integration priorities within R09

These are engineering choices inferred from the evidence, not a universal SOTA
ranking. We can replay expensive cached tracking interactively even when extraction
runs slower than real time. Live camera must satisfy a separate latency constraint.

1. **Compare lightweight 3D first:** MediaPipe and RTMW3D against current tracking on
   the same small private segments, including turns and two-person footage. This
   answers whether inexpensive depth/keypoint changes already improve the instrument.
2. **First multi-person articulated trial:** Multi-HMR 2, exporting Anny rotations
   and explicit identities without rendering meshes on every inference. Test local
   memory/latency before promising live use; start with cached segments if needed.
3. **Temporal quality comparator:** GVHMR plus optional HTD-Refine, and GEM-X as a
   richer whole-body alternative. Run small existing segments, not the huge original.
   HTD refinement and other future-dependent outputs must be identified as offline.
4. **Live articulated feasibility:** compare Fast SAM/native FP16 routes if the
   lightweight baselines lack necessary rotations. Measure on RTX 2060 with the
   actual pipeline; stronger hardware becomes a concrete decision only after this.
   OnlineHMR's full world pipeline is a later comparator, not the default live choice.

For each trial, preserve the same selected person and source timestamps. Inspect
hip label/root flips, limb length changes and gaps; compare rhythmic phase,
movement amplitude, genuine quick changes and false audio activations. Report p50/p95
end-to-end delay and sustained output cadence separately, plus peak GPU memory.
Without independent 3D reference, call these consistency/perceptual observations,
not position or rotation accuracy. Existing synthetic trajectories can quantify
filter attenuation/phase delay, but cannot validate the neural tracker on real bodies.
Human listening remains an actual listening step, not inferred from a smooth plot.

Keep **one laboratory**, selectable providers and reusable caches. Do not copy the
large source or adopt demo re-encoding/extraction clocks. If a model needs uniform
30 FPS, create timestamped in-memory samples from the selected segment and preserve
the mapping back to original PTS. No automatic calibration transfer between people.

A versioned articulated frame must carry joint names/hierarchy, handedness, units,
coordinate frames, root translation/orientation, local/global rotations, validity and
provenance. Keep inferred/held/refined states distinct from observed evidence; a
model's confident completion behind an occluder is not a new observation. Current
COCO-17 camera-space contracts cannot represent these semantics by simply adding z.
Use rotation matrices/quaternions and SO(3) operations for relative/angular motion,
not Euler subtraction. Retain six independently routed voices and existing tuning;
root/pelvis angular motion, limb angular velocities and rotational phase relations
become additional features, not an unsolicited pitch modulation.

Later capture decisions remain under R08/R09 in [#23](https://github.com/AlterMundi/harmonic-weaver/issues/23):
second synchronized calibrated camera for depth/occlusion, then optional torso/pelvis
IMU for orientation/fast inertial evidence. These add observations that monocular
priors cannot recover reliably. [OpenCap](https://www.opencap.ai/) is a relevant
biomechanical reference, but its hosted workflow computes on cloud servers and is
not our private local live pipeline. [PIP](https://github.com/Xinyu-Yi/PIP) demonstrates
sparse-IMU motion recovery, with six sensors; it does not establish that one pelvis
IMU measures every joint. No hardware purchase is justified solely by this review.
