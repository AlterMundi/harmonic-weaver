# Regional facial readout0.1 —2026-11-13

Sai requested a visible reading of mouth, eyes and brows, with their curves and
local gestures composing the total instead of requiring a whole-face template.
This replaces the default exploratory display. The historical four-pattern
`face-expression-rules/0.1` functions and exact v1–v5 protocols stay available
for interpreting earlier records; the current method is
`face-expression-regions/0.1`, protocol/sessionv6. No trained emotion, AU,
sincerity, health or ear detector was added.

## Geometry and availability

The same pinned FaceLandmarker provides estimated facial landmarks. The selected
pose frame uses outer eye corners33/263 and the nasal bridge168/6; no pupil-center
condition is used. Head-relative mode still compensates moderate turns using
estimated relative depth. It does not establish real surface3D or accurate profiles.
[Upstream FaceLandmarker](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker)
describes the facial mesh; this implementation uses no ear keypoints and does
not relabel face-oval points as ears. No extra model or camera is started.

`projectFace` normalizes whatever selected points are finite after checking the
shared pose anchors. Each region computes its own available descriptors. A
missing mouth point does not invalidate available eye/brow descriptors. Invalid
pose anchors, multiple faces, model loss or stale frames clear all live readings.
Finite model coordinates are estimates, not independent proof of visibility.

Numeric sound metrics require21 metric landmarks, rather than every vertex of
the displayed polylines. A missing decorative vertex therefore no longer mutes
otherwise valid sound. Missing metric landmarks still pause the original sound
map; regional labels can remain available independently. No missing metric is
filled with zero or a guessed gesture. Hiding the SVG overlay does not change
inference, reference, region calculation, sound or recording.

## Signed arcs and local motion

Each arc uses these ordered contours:

- Upper lip:61,40,37,0,267,270,291.
- Upper eyelids:left362,385,386,387,263; right33,160,159,158,133.
- Brows:left336,296,334,293,300; right70,63,105,66,107.

The **arc deflection** is the mean signed perpendicular distance of interior
vertices to their endpoint chord, divided by chord length. Its orientation is
positive toward the selected facial center and negative away. Eyelids use nasal
point6 for orientation because the eye-midpoint reference may lie on their chord.
The **oriented total turn**, in radians, sums `atan2(cross,dot)` over consecutive
segments with the corresponding orientation. Both descriptors are invariant to
translation/scale/roll and to reversal of contour traversal. A zero-length chord,
degenerate segment or unavailable reference returns null. No skin-fold or
forehead-wrinkle segmentation is implied. This is a curve descriptor, not an
absolute law mapping the words concave/convex to emotion.

The panel shows current deflection, change from resting reference and total turn,
plus local aperture, height and corner/brow slope changes. Reference values and
MAD noise are calculated independently per descriptor from at least10 valid
reference samples. Unknown descriptors remain null. Each directional comparison
exceeds both its authored minimum and3 times that descriptor's reference MAD.

## Authored local cues and composition

These weights are compositional design choices, **not probabilities or measured
accuracy**:

| Region | Local cue | Contribution |
| --- | --- | --- |
| Mouth | Both corner heights rise>.008 and both lifts>.010 | Joy-like cue0.7;1.0 if heights>.015/lifts>.018 |
| Mouth | Both corner heights/lifts descend by the same small floors | Sadness-like cue1.0 |
| Mouth | Aperture increase>.10, without a corner cue | Open mouth; surprise support0.5, insufficient alone |
| Eyes | Both aperture ratios increase>.045 | Surprise support0.5; one eye gives0.25 |
| Brows | Both heights rise>.025 | Surprise support0.5 |
| Brows | Both heights descend>.014 and both inner slopes descend>.020 | Anger/concentration-like cue1.0 |

One-sided changes, closing eyelids, and local curve changes are shown descriptively
without forced emotion votes. Unmatched arc changes beyond.012 deflection or.10
radians (and their noise floors) remain visible as local curve changes. The total
collects independently stabilized contributions. Joy/sadness/anger-like hypotheses
need0.7 support; surprise needs1.0, thus at least two different supporting zones.
Mouth opening alone is not called surprise. Eyes+brows can support surprise while
the mouth stays relaxed. A smiling mouth plus furrowed brows produces a mixed
reading rather than canceling either component. Near-reference is not emotional
calm. Ambiguity and partial coverage remain visible; no label proves felt emotion.

Each zone requires at least2 frames spanning250ms. A changed candidate gets up
to350ms of explicitly marked transition grace; unresolved flicker cannot retain
an old contribution indefinitely. Missing evidence clears that contributor
immediately. A gap>500ms resets persistence; the existing750ms freshness watchdog
and finite sound lease remain. One changing zone does not reset stable peers.

## Records, presentation and acceptance

Trial labels, regional cards, stage chips and evidence rings share the existing
opt-in/hide boundary: they are hidden during a research trial and stay hidden
after it until deliberately re-enabled. Prior exposure remains recorded. v6
records the actual method, optional regional reference and per-sample regional
values, including nulls. CSV appends `region_*` fields; zero stays zero. Old records
are not given invented regional readings or reinterpreted as the new method.
The40.4Hz reference, curve-to-sound map, power normalization and native body set
are unchanged by the classifier. New drawn teaching examples include relaxed
mouth with raised eyes/brows, isolated mouth opening, and smile+furrow. They are
synthetic demonstrations, not human validation or a confirmatory emotion study.

Check software geometry/curve invariance, independent missingness, composite
weights, transition bounds, overlay independence, exports and trial hiding. Then
check a consented real camera: gentle gaze/head turns, localized gestures,
contradictory combinations, lighting and loss/recovery. Record observer agreement
and human feedback separately from software success before claiming recognition
accuracy. No automatic human capture, public release or recruitment follows.

## Software qualification

The focused face suite passed42 cases after the regional implementation, including
geometry, contour synthesis, research compatibility, pinned model/WASM fixture
inference and Web Audio values. After reducing badge overlap on small screens,
22 expression/mirror/regional cases passed again. The8 new regional cases cover
partial landmarks, pose transforms, independent persistence, mixed gestures,
null/zero export compatibility and desktop/narrow/fullscreen controls. Browser
examples are drawn fixtures. No physical camera, hearing or human-expression
accuracy acceptance is claimed.
