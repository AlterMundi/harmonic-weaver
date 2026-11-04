# Facial ratios, dynamic expression and sonification

Research and implementation plan,2026-11-03. Prototype0.1 is an exploratory
instrument, not evidence that a particular face is inherently consonant or that
geometry identifies a person's emotion. The originating Sai/Nico idea is retained
as a paraphrased research question; their private conversation is not published.

## Question and deliverables

Within the same person, do projected changes of radial distances, contour bending
and bilateral coordination explain changes in perceived tension, pleasantness or
surprise beyond movement amplitude and timing? Is the upper nasal bridge a more
useful reference than an eye midpoint? Can a frozen sonification help people
notice these changes without building the expected emotion into the mapping?

The work proceeds through five deliverables:

1. A face mirror with opt-in local camera, landmark overlay, personal reference,
   finite-lease browser audio and explicitly synthetic teaching examples.
2. A mathematical contract, repeatable software tests and an actual-model check.
   Validate accuracy separately with independently annotated consented footage.
3. Consented practitioner trials, descriptive quality reports and local exports.
4. A separately consented observer experiment using neutral questions and
   balanced modality orders, with documented stimulus rights and uncertainty.
5. Prospectively frozen hypotheses, controls, analysis and sample justification
   before a new confirmatory cohort. No participant results are implied by QA.

Prototype0.1 implements1, software parts of2 and a practitioner capture/export
path for3. It documents4–5 but does not present those stages as completed research.
The existing body instrument, six accepted body voices, native Shaper, tuning and
camera source remain independent and unchanged. The face mirror uses a separate
browser synthesis map rather than claiming a full Shaper port.

## Measurements and reference

See [mathematical contract](MATHEMATICS.md). Use the subject's comfortable resting
expression as a reference, without assuming that rest means emotional neutrality.
Compare the same person within a session; habitual morphology is not an emotion,
attractiveness, honesty or health score. Record missing observations explicitly.

A narrow frontal camera view is required. The current geometry removes image-plane
translation, uniform scale and roll using outer eye corners. It rejects a coarse
large-yaw proxy; it does NOT solve perspective distortion, pitch, calibrated3D
surface curvature or identity continuity after another person enters the frame.
The interface asks for one person and rejects multiple detected faces. A new
person must explicitly take a new reference; this is not face recognition.

The pinned model is MediaPipe Face Landmarker float16 v1, SDK1.2.0, model SHA-256
`64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff`.
Estimated landmarks are not ground-truth muscle activity or certified FACS codes.
A human annotation comparison, glasses/occlusion tests and stable reference tests
across lighting, appearance and sessions remain required for scientific accuracy.

## Six initial movement families

Record consenting adults only. A proposed initial2–3-person feasibility group is
for instruction/capture debugging; it is not a powered emotion study. Use three
repetitions per family, comfortable intensity, a brief resting interval before
and after, similar framing and light, and actual source timestamps. A10-second
prototype trial is a convenience, not a validated biological timescale.

- Rest → small smile → rest.
- Rest → larger smile → rest.
- Brow contraction → release.
- Bilateral eyebrow/eye opening → unilateral change.
- Similar contraction with one brow raised.
- Deliberate photo-style smile and a naturally occurring smile, with independently
  recorded context and performer self-report. Neither is labelled truthful/fake
  from its geometry.

Do not force emotional extremes or treat an instruction to frown as proof of
felt anger. The six drawn examples demonstrate descriptor changes; they are not
human stimuli, model validation images or empirical emotion prototypes.

## Four experiments

### A. Measurement repeatability

Hold expression approximately steady while deliberately translating, resizing
and rolling the head/camera within an acceptable frontal view. Then move one
region while keeping others as similar as practical. Compare model points and
contours to independent manual annotations, report error/coverage by region and
conditions, and compare change magnitude with neutral/reference noise. Inspect
the actual footage instead of judging accuracy only from numerical readiness.
A nasal-center advantage can be rejected; retain the better reference or both.

### B. Silent transition perception

Prepare consented human clips with neutral IDs and a frozen selection/exclusion
ledger. Ask free interpretation first, then separate perceived tension,
pleasantness and surprise ratings; ask the practitioner's own feeling separately.
Allow no emotion, mixed, unsure, skipped items and withdrawal. Include context
as a planned manipulation or record it; do not infer a universal emotion map
from recognizable acted exemplars. Compare transitions, still frames and simple
amplitude/speed baselines. Retain all takes and counterexamples.

A proposed12–20-observer feasibility exercise checks wording, fatigue and variance;
it is not confirmatory sample sufficiency. Use held-out people and sessions,
not random adjacent frames, to separate descriptor development from assessment.

### C. Audio-visual relation

Freeze and hash a small parameter-to-sound map BEFORE new observer responses.
Compare silent video, derived sound alone and matched AV, plus a noncontingent or
permuted mapping control matched as closely as possible on level, timbre,
duration and pitch distribution. Changes in congruence must not be explained
solely by a happier-sounding preset selected by the experimenter.

Use the existing Trama/R10 methodology for consent, neutral prompts and modality
separation. A future adapter must name a distinct facial protocol; current
`face-mirror-session/v1` is a practitioner telemetry format, not a valid native
Shaper field, Trama-v3 import or completed observer workflow. A complete Williams
order cycle can balance positions/adjacent conditions; incomplete enrollment
cannot claim that balance. No automatic recruitment or shared collection exists.

### D. Held-out confirmation

After feasibility, preselect a few descriptors and comparisons, define a smallest
meaningful effect and precision/power rationale, specify exclusions, treatment of
missing data, participant/performer/clip dependence and multiple comparisons.
Freeze the protocol before a separate cohort/session. Compare geometry models
with intensity, speed, head pose and available action-unit baselines. Preserve
null findings and disagreements. An association is not a causal emotion law.

## Consent, recording and export

Camera access is an explicit adult opt-in; microphone access is never requested.
The model/WASM are served from the same origin; camera images are not uploaded.
Only deliberate trial capture stores derived values and responses in page memory.
No original video, image, audio, raw mesh or biometric identity template is saved
by this version. Therefore exported telemetry cannot establish image-grounded
measurement accuracy or independently reconstruct the original gesture.

JSON stores protocol/model/mapping identity, reference, center, actual sample
receipt times, gaps, settings, audio on/off events, completion state and separate
free responses. CSV preserves empty versus zero and guards spreadsheet formulas.
Import checks schema/limits/deltas/protocol identity/hash; hashes detect accidental
mismatch, not signed scientific authenticity. No default browser persistence,
cloud upload, public gallery or cross-device response backend is installed.

Before actual recruitment define the organizer/contact, exact recipients,
retention/deletion date, subject rights and any institutional review. Facial
measurement exports remain potentially identifying even without pixels. Clearing
page data cannot retract files already exported. A recording used for independent
annotation or observer display requires separate consent and its own private
source manifest, rights and clock qualification.

## Evidence ledger

- [Jack, Garrod & Schyns2014](https://eprints.gla.ac.uk/88928/): temporal signals
  in observer-expectation models. Abstract/summary read, not a replication or
  proof of a center-based face/acoustic equivalence.
- [MediaPipe official task](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker):
  model/API capabilities; receiving performance and landmark accuracy need testing.
- [DISFA author dataset](https://www.mohammadmahoor.com/pages/databases/disfa/):
  spontaneous actions and human intensity annotations; research agreement needed.
- [BP4D owner dataset](https://www.cs.binghamton.edu/~lijun/Research/3DFE/3DFE_Analysis.html):
  dynamic2D/3D and FACS references; institutional license needed. BP4D+/BU-EEG
  are later independent multimodal candidates, not physiological measurements here.
- [Krumhuber & Manstead2009](https://pubmed.ncbi.nlm.nih.gov/20001124/):
  dynamic and deliberate smiles; a Duchenne marker does not certify felt enjoyment.
- [Aviezer et al.2012](https://pubmed.ncbi.nlm.nih.gov/23197536/):
  contextual effects in intense facial-expression perception; scope is specific
  experiments, not proof that faces communicate nothing.
- [McDermott et al.2010](https://mcdermottlab.mit.edu/bib2php/pubs/makeAbs.php?loc=mcdermott10b):
  acoustic harmonicity/beating and judgments; not a spatial-ratio to frequency law.

No iris-based organ/life-history diagnosis, emotion diagnosis, lie detection,
EEG-band inference, universal beauty ratio or energetic-efficiency claim is part
of this protocol. Earlier Trama/general work remains separate roadmap scope, not completed by this prototype.

## Implemented continuation,2026-11-03

The [contour instrument0.2](CONTOUR_INSTRUMENT.md) implements an explicitly
designed3–8-partial map, with separate richness and contraction-deviation controls.
It is deliberately suggestive: a listener liking its output cannot validate
that faces are naturally consonant. The legacy map remains selectable and
imports keep their original protocol identity.
See the [stimulus-evoked human experiment](HUMAN_EXPERIMENT.md) for the current
next step, controls, pending stimulus rights and separation of felt/reported
experience from observer perception. No new human results are asserted.

## Local shape beyond center distance,2026-11-04

Sai emphasized that each expressive line carries shape/motion information beyond the nasal/eye reference. The [source-grounded continuation and mathematical bench](../../../research/laboratory/facial_curves/README.md) uses FACS/component-analysis antecedents and separates local curve geometry, regional movement, center relation and skin-line appearance. It provides matched-opening/different-curvature controls and a staged annotation/sonification plan. Synthetic geometry/browser checks are not action-recognition, human-perception or physical skin-crease validation; the deployed reader still uses its previous descriptors.
