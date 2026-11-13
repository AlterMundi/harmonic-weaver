# Expression-axis sound — 2026-11-13

Sai selected an optional musical interpretation alongside the existing contour
map: increasingly anger-like cues toward harmonic11 and increasingly joy-like
cues toward f0. This is a designed feedback instrument, not an observed natural
emotion/frequency law. The default contour and legacy sound maps stay unchanged.
Native HarMoCAP/Shaper body voices, calibration and tuning are untouched.

## Use

In Rostro, take a relaxed reference. Under Escuchá los cambios choose **Emoción ·
eje expresivo** beside **Contornos actuales**, then explicitly activate sound.
Switching maps never starts a camera or audio context. Set these controls:

| Control | Default | Effect |
| --- | --- | --- |
| Alegría · destino H | 1 | Position approached as smile cues increase |
| Enojo · destino H | 11 | Position approached as furrow cues increase |
| Respuesta expresiva | 100% | Depth of movement away from the midpoint |
| Movimiento | Deslizar entre armónicos | Continuous ratio; alternatively choose rounded integer harmonics |

Each endpoint is an integer1–16. H1 means f0, H11 means11 times f0. At the
selected40.4Hz reference the default endpoints are40.4 and444.4Hz. The resting
position is their midpoint, H6/242.4Hz; it is not a neutral-emotion diagnosis.
Depth0 freezes that middle position. Mixed cues combine rather than selecting
one category. Sadness and surprise have no separate target in this initial axis.
The current cue intensities and target ratio are visible independently of labels.

The f0 reference stays fixed and quieter below the moving voice. Near H1 the
moving voice fades out, leaving the root alone. The continuous mode can pass
through noninteger multiples; those positions are not exact harmonic partials.
The step mode rounds the ratio before the existing audio smoothing. H11 is a
selected destination; this implementation does not define it as inherently angry
or dissonant. Perceived tension depends on listening and remains to be tested.
If H1 is quiet on the chosen output, compare H2/H4 using the explicit endpoint
control while retaining the40.4Hz reference; record the selected values.

## Reproducible mapping

Method `face-expression-axis/0.1` uses available normalized personal-reference
regional deltas and MAD noise floors. It never switches pitch from displayed
categorical label text. Cue intensities are authored controls, not probabilities.
For each component with signed delta d, noise n, floor b and width w:

    component = clamp((direction * d * sensitivity - max(b, 3*n*sensitivity))/w, 0, 1)

The minimum of four components gives each cue. Missing any required component
makes that cue null, not zero. All missing cues give no sound decision. Available
but subthreshold cues give zero intensity. The existing full sound-metric gate
still applies: model loss, incomplete core metrics or stale observations silence
the instrument rather than sound a remembered or guessed face.

| Cue | Components | Direction | Floor | Width |
| --- | --- | --- | --- | --- |
| Smile/joy-like | Both corner heights | Up | .008 | .045 |
| Smile/joy-like | Both corner lifts | Up | .010 | .040 |
| Furrow/anger-like | Both brow heights | Down | .014 | .014 |
| Furrow/anger-like | Both inner slopes | Down | .020 | .030 |

For available strengths j/a, missing strength has no contribution to the blend.
Let R be the endpoint midpoint. The weighted target is
`T=(j*joyH+a*angerH)/(j+a)` when there is support, otherwise R. The final ratio is
`R+(T-R)*max(j,a)*depth`, optionally rounded to an integer. It remains within the
selected endpoints. At default saturated cues: joy→1, anger→11, both→6. The
thresholds are design parameters, not fitted or validated population statistics.

The two voices are at f0 and ratio*f0. Moving weight is
`.82*clamp((ratio-1)/.5,0,1)`; fixed-root weight is its complement. Gains are
`.22*weight`, so their sum remains.22. This bounds the digital amplitude; it does
not ensure equal perceived loudness across frequencies or listening devices.
Existing40ms oscillator smoothing, finite gain leases, volume/compressor and
750ms tracking watchdog remain. No extra oscillator allocation is needed.

## Research and exposure

Protocol/sessionv7 identifies the selected map and exact expression settings.
Each expression-axis sample stores nullable cue intensities and target ratio;
the importer recomputes and verifies them from the retained regional descriptors,
reference, sensitivity and settings. CSV adds endpoints, depth, movement, drives,
ratio and target Hz. Missing/stale decisions remain null. Exact v1–v6 protocols
remain importable without invented expression-sound history.

Visual labels/axis indicators are hidden during trials and remain hidden after.
Hearing this mode still encodes the selected authored interpretation. Do not call
that an unexposed or blinded emotion-recognition condition. The existing questions
separate intended gesture, felt emotion and perceived sound. A comparison should
freeze settings and compare the contour mode, this axis and an appropriate silent
or shuffled control, without fitting the map to the same person's expected answer.
No new recruitment, raw video/audio capture or automatic data sharing is added.

## Qualification boundary

Software fixtures check endpoints, intensity/depth, mixed and missing cues, noisy
reference, integer movement, gain bounds, historical/v7 JSON/CSV compatibility,
actual Web Audio oscillator values and the responsive selection/trial journey.
These are not human recognition accuracy or physical camera/hearing acceptance.
Use the existing human camera/hearing check to compare posed smile/furrow and
mixed cues, return to rest, continuity, level and whether the sound communicates
the intended contrast. The earlier chat-timed gestures produced no exported
measurements; do not count them as recorded experimental results.

The48 distinct focused face cases passed across the initial47 successful cases
and one targeted model-fixture rerun. The first model case failed because its
private QA portrait file had not been copied into the new QA folder (ENOENT);
restoring that existing fixture resolved it without changing application code.
The six new cases include actual browser oscillator movement40.4↔444.4Hz,
mode restoration and a completed synthetic v7 recording/export. Desktop and390px
screenshots were inspected. Physical camera and hearing acceptance remain open.
