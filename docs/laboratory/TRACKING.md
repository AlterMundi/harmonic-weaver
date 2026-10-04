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

Verification: isolated hip swaps, irregular source cadence/acceleration bounds,
preservation of steady motion, no filling missing/held joints, seeks and all model
paths. Local body comparison/configuration/plots stay in the private data directory;
no video, frames, identities or body result tables are published.

## Candidate backends, reviewed 2026-10-04

| Candidate | Actual representation / use | Fit to our lab |
| --- | --- | --- |
| [MediaPipe Pose Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker) | 33 estimated 3D landmarks, image/world coordinates, VIDEO/LIVE_STREAM; optimized for on-device use | First lightweight local alternative to compare against current 2D detector. Does not directly expose complete articulated joint rotations; positions alone do not resolve bone twist. |
| [GVHMR](https://github.com/zju3dv/GVHMR) | Temporal monocular-video motion recovery; camera/global SMPL-X parameters, body pose and root motion | First candidate for cached video + articulated pose. Official demo selects one track, so preserve our explicit person selection for multi-person footage. Static-camera option is available. |
| [WHAM](https://github.com/yohanshin/WHAM) | Video-to-SMPL motion, global/camera reconstruction; optional temporal SMPLify refinement | Additional temporal comparator, not a claim of superiority to newer models on rope-flow. |
| [SAM 3D Body](https://github.com/facebookresearch/sam-3d-body) / [MHR](https://github.com/facebookresearch/MHR) | Single-image full-body rig/mesh including hands/feet; official estimator exports `body_pose_params`, `pred_joint_coords`, `pred_global_rots` | Rich joint rotations and a reusable rig. Needs temporal conditioning/identity handling for video; single-image accuracy alone does not solve our jitter. |

Sources: [SAM estimator output fields](https://github.com/facebookresearch/sam-3d-body/blob/main/sam_3d_body/sam_3d_body_estimator.py),
[SAM setup/checkpoint access](https://github.com/facebookresearch/sam-3d-body/blob/main/INSTALL.md),
[GVHMR installation/SMPL-X registration](https://github.com/zju3dv/GVHMR/blob/main/docs/INSTALL.md),
[GVHMR actual demo pipeline](https://github.com/zju3dv/GVHMR/blob/main/tools/demo/demo.py).

Legion currently has RTX 2060 / 6 GB VRAM. No throughput or fit is claimed without
running on that hardware. SAM checkpoints require access authorization; GVHMR/WHAM
body assets require registration/licence acceptance. Existing videos can stay local.
No new model has been downloaded or benchmarked in this change.

## Next integration within R09

Compare the same short source/person/PTS segment with current raw/conditioned tracking,
a lightweight 3D landmarker, and a temporal articulated model. Prefer MediaPipe for
live feasibility and GVHMR for the first recorded-video rotation trial. These are
engineering priorities, not rankings of scientific accuracy.

Keep one laboratory and selectable providers in its source UI. Provider/model/input
settings identify cached outputs; playback of a processed video uses the cache.
Do not replace original timestamps with demo re-encoding timestamps or duplicate the
large original. Store skeleton hierarchy, coordinate frames, units, visibility,
root translation/orientation, local and global rotations, and their provenance.
Current COCO-17 camera-space contracts are not sufficient for a full articulated rig;
use a versioned representation rather than treating inferred depth as measured depth.

Use quaternion/rotation-matrix operations for 3D angular velocity and relative rotation;
Euler-angle subtraction creates wrap artifacts. Map torso rotation, limb angular
velocity, phase relations and collective rotational modes to the existing six-voice
instrument through explicit routes. Monocular estimates still need tests on viewpoint
changes, occlusion, identities and latency before claims about actual 3D motion.
