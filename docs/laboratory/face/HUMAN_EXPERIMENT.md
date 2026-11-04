# Face-contour sonification: pilot record and next human experiment

Shared research brief,2026-11-03. Human direction: integrate a contour-following instrument and make the next step a real, consented study using stimuli to elicit expressions and listening to their derived sound. Do not infer emotion categories from the camera.

## Completed exploratory JAFFE extraction

The private noncommercial pilot processed213 static posed photographs from ten Japanese female expressers, using pinned MediaPipe Face Landmarker SDK1.2.0/model SHA256 `64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff`. All images passed the automatic geometry gate; anatomical accuracy was not independently annotated. The primary center was bridge168, with nose-tip sensitivity comparison. The new instrument's eye-midpoint default was not validated by that extraction.

Normalize nine radial distances by outer-eye span, and their convex-hull area by squared eye span. Contrast each person's pose median with their median of three neutral photographs, then summarize ten person contrasts:

| Requested pose | Median area change | Median nine-point radial change |
|---|---:|---:|
| Anger | −4.33% | −2.40% |
| Happiness | +4.87% | −1.25% |
| Sadness | +0.04% | +0.78% |
| Surprise | +2.95% | +5.40% |

Area and radial distance differ. Regional surprise contrasts put brows higher and mouth lower; sadness did not yield a clear global elongation. These are descriptive results from poses and a small population, not felt-emotion labels, validated classifier performance, temporal tracking or consonance evidence. Five selected overlays were regenerated and matched the retained extraction exactly. The illustrated seven-page scientific report includes five licensed source images, distinct example/group percentages, caveats and required credits; the raw dataset/photos do not belong in this repository or application.

JAFFE: Michael Lyons, Miyuki Kamachi and Jiro Gyoba, ©1997, [official v2](https://zenodo.org/records/14974867). Its terms restrict use to noncommercial scientific research, prohibit dataset redistribution/web/social images and permit at most ten sample images in scientific publications. Required references: [Coding Facial Expressions with Gabor Wavelets](https://arxiv.org/abs/2009.05938), [“Excavating AI” Re-excavated](https://arxiv.org/abs/2107.13998). The scientific report is selected for authenticated Tribe reading, not public photo release.

## Next step: elicitation, measurement, listening

This is the next planned human phase, not completed recruitment or a ready collection of licensed stimuli. The current browser trials collect local metrics/reflections, not a full observer study or original video/audio recording.

1. **Consent and stimulus ledger.** Work with voluntary consenting adults. Name the organizer/contact, recipients, retention/deletion period and recording choice before data collection. Record stimulus rights/source, exact excerpt/time range, intended condition, exposure order and stop/skip choice. Avoid participant identifiers in shared reports. Stimuli aim to evoke expressions; they do not prove what someone felt.
2. **Choose gentle, lawful material.** Candidate families are amusing scenes, benign surprise/novelty, a brief tolerable challenging task for frustration/contraction, and neutral/rest controls. Use owned or appropriately licensed clips/tasks. Do not substitute unlicensed reposts, startling threats or personal distress. Exact stimuli remain to be selected and piloted. A condition's intended emotion is not shown to the later listener.
3. **Silent capture first.** Keep diffuse fixed light and frontal framing, take repeated personal resting references, and interleave short stimulus blocks with rest. Record actual acquisition/receipt times and missing observations. Capture original video only with separate consent and a protected source manifest. Collect a brief time-bounded performer report before presenting derived sound. Do not call a voluntary smile false or regard spontaneous behavior as infallible proof of joy.
4. **Check measurements.** Compare a consented subset against independent annotations; inspect lighting, glasses/occlusion, head distance/yaw/pitch, repeatability and timing. Curves around eyes/brows/mouth are current proxies. Fine skin-line detection needs its own image branch and annotation validation. Reject missing/late data rather than rendering a guessed state.
5. **Freeze the sound map.** Record geometry/model/mapping versions, center, reference, sensitivity, f0, richness and deviation controls. Once chosen for assessment, do not tune it toward desired observer answers. Compare the legacy map and contour-series map where relevant. A map explicitly making a chosen gesture more harmonic is a design behavior, not independent confirmation of an emotion law.
6. **Listen with controls.** Collect free interpretation first, followed by separate perceived affect, tension/roughness, pleasantness, brightness and uncertainty. Compare silent video, sound alone, matched audiovisual and shuffled audiovisual, with balanced orders, durations and measured/perceived level controls. Keep the performer's feeling and observers' judgments separate. Compare three/eight partials and aligned/displaced placement to distinguish richness from alignment.
7. **Assess new people/sessions.** Feasibility checks instructions, latency, comfort, measurement noise and response variance. Define sample/precision rationale, exclusions, dependency between performer/clip/observer and primary comparisons before a separate confirmation stage. Reserve people/sessions rather than adjacent frames. Retain null findings and disagreement. Separate readout from any later study of whether hearing feedback itself changes feeling.

## Current reading and delivery boundaries

The canonical source and this text are reusable research records. The illustrated PDF's enforced Tribe audience and actual messaging receipt are separate from another daimon reading/incorporating it. No agent wakeup, automatic recruitment or background collection follows from sharing it. The laboratory is an instrument first; using it does not require finishing the scientific validation.

## Subsequent readout request,2026-11-04

The earlier no-category direction above is historical. Sai later explicitly asked
for an expression identifier alongside the measured points. The optional
[authored readout](EXPRESSION_READOUT.md) does this without feeding labels into
synthesis. It is not a validated emotion recognizer. Its labels are hidden during
trials and stay hidden until explicitly re-enabled; previous label exposure is
recorded, not undone. Use a separate unexposed observer session/cohort when testing
perceived emotion, rather than interpreting prompted responses as independent
confirmation. Nothing in this update adds human results to the JAFFE pilot.
