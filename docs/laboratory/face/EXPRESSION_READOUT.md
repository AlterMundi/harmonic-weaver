# Optional expression readout0.1

2026-11-04, requested by Sai: show a possible emotional reading beside the face
and let the person inspect its supporting points. This supersedes the earlier
geometry-only display preference; it does not change the geometry-to-sound map.

## What the display claims

`face-expression-rules/0.1` is a small **hand-authored, unvalidated geometric
classifier**. It suggests “Alegría posible”, “Sorpresa posible”, “Enojo posible”
or “Tristeza posible” from a few motor patterns. It does not measure felt emotion,
sincerity, mental health, attraction or all possible expressions. No percentages
or empirical accuracy estimates are displayed. A smile may be posed; lowered
brows may indicate concentration. A reference close to the current pose means
“Sin cambio marcado”, not emotional calm. Nonmatching and mixed gestures remain
explicit rather than being forced into one category.

FACS describes observable movement through action units, with emotional meaning
requiring a separate interpretation ([official FACS overview and FAQ](https://www.paulekman.com/facial-action-coding-system/),
accessed2026-11-04). Our point rules are **not** a trained or certified FACS/AU
detector and are not implementation of the restricted EMFACS instructions.
No JAFFE images, trained weights derived from JAFFE or new emotion model are
distributed. Existing MediaPipe landmarks supply geometry only.

## Features and exact authored rules

Use existing aspect-corrected, eye-span-normalized, roll-aligned2D landmarks.
With image y downward, define:

- Brow heightL/R: `-y334`, `-y105` relative to the eye line.
- Inner brow slopeL/R: `y300-y336`, `y70-y107`.
- Mouth corner heightL/R: `-y291`, `-y61`.
- Corner liftL/R relative to the upper lip: `y13-y291`, `y13-y61`.
- Eye aperturesL/R: upper/lower distances divided by the local eye width.
- Mouth aperture: `distance(13,14)/distance(61,291)`.

Each change is current minus the median personal reference. The same contiguous
resting sample set used for sound calibration supplies an independent optional
expression reference with median absolute deviations (MAD). A directional feature
must exceed `max(authored minimum,3*MAD)`. No sound sensitivity parameter enters
the classifier. Heights/slopes use eye-span units; aperture ratios use local widths.

| Suggestion | Required changes, each beyond its noise floor |
| --- | --- |
| Joy | Both corner heights increase>.015 and both corner lifts increase>.018 |
| Surprise | Both brow heights increase>.025, both eye apertures increase>.045 and mouth aperture increases>.10 |
| Anger | Both brow heights decrease>.014 and both inner slopes decrease>.020 |
| Sadness | Both corner heights decrease>.015 and both corner lifts decrease>.018 |

Multiple complete matches produce “Gesto mixto”. With no match, changes within
the per-feature floors used above produce “Sin cambio marcado”; otherwise the
result is “Sin una sugerencia clara”. Gold rings and a point list identify the
evidence; displayed signed deltas retain the measurement units. These are coarse
point/chord descriptors, not full local curve curvature or physical skin-fold
segmentation. Nose/eye-center distances remain available in the original meters;
changing center requires a new reference.

At least three contiguous valid frames spanning500ms are needed. A changed
candidate immediately shows a transition instead of retaining the old label.
Gaps>350ms restart persistence; invalid/multiple/late frames and worker failures
clear the suggestion. The existing750ms camera freshness watchdog clears stale
overlays/readings. Source, center and reference changes invalidate the readout.
Slow devices may remain in transition rather than show a stale emotional label.

## Study and export boundary

The optional readout starts enabled for exploration, but cannot be toggled during
a trial. Starting a trial hides the card's hypotheses, stage badge and evidence
rings. They remain hidden after completion/interruption until deliberately shown
again. Answer the neutral reflection questions before re-enabling it.

Sessionv3 freezes this method in the protocol. Trial context records the method
version, whether the control was enabled before the trial, whether a categorical
suggestion was already displayed earlier in the session and `labelsDuringTrial:false`.
Samples optionally retain the measured expression features, and the baseline its
independent feature reference/noise. CSV appends context/features. Felt/perceived
answers remain separate free text. v1/v2 import and re-export preserve missing
readout context as **unknown**, never false. Prior exposure is not undone by hiding
labels; use new unexposed observers for an independent perception experiment.

## Validation and next evidence

Software checks cover the four explicitly drawn motor patterns, unilateral
changes, mouth opening without a smile, eyelid-only movement, mixed geometry,
noise floors, similarity transforms, persistence/loss, point attribution,
export/import, prior exposure and trial hiding. Browser checks cover actual
WebAudio, camera consent/cleanup, model/WASM fixture inference, narrow/fullscreen
layouts and the research workflow. Drawn fixtures are not human-expression data;
passing these checks is not accuracy on real people.

Before reporting recognition performance: collect consented frontal clips across
people/lighting/pose and spontaneous versus posed actions; annotate visible motor
actions independently and obtain separate observer readings and actor reports.
Freeze thresholds prospectively and split by person. Report unknown/mixed rates,
per-class errors and intervals, demographic/context limits and latency/loss as
well as agreement. Include concentration versus anger, speaking/yawning versus
surprise, posed smiles and non-prototypical sadness as negative controls. Keep
this classifier exploratory until that evidence exists.
