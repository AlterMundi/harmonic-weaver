# Weaver facial mirror — contour instrument0.5

Build the existing laboratory with `cd laboratory-ui && npm ci && npm run build`.
The build prepares pinned model/WASM under ignored `public/face-assets`; weights
are verified before use. Serve the ordinary laboratory, then open
`/?mode=face` or the **Rostro** link. A static same-origin HTTP server on
localhost can also serve `laboratory-ui/dist`; remote camera use requires HTTPS.
No separate backend, account, host-camera permission or native Shaper is needed.

1. Try a drawn example, or choose **Mi cámara**, adult local-use consent and
   **Conectar cámara**. The first permission may reveal named camera choices.
2. Choose a reference center and take a resting reference. Changing center/source
   clears it. Start with the face close and approximately frontal. A camera occupied by another app
   is not automatically taken over or replaced.
3. Choose the contour-series map (default) or the preserved six-voice legacy map.
   The default reference is the eye midpoint. Activate sound from a button; adjust volume, sensitivity and fundamental.
   Expand the mirror and return with Esc. Hiding the tab stops its owned camera
   and mutes sound; reconnect explicitly. The body instrument is unchanged.
4. In **Investigación**, opt into keeping local metrics, select the movement and
   collect10s. Describe felt experience and perceived impression separately.
   Export private JSON/CSV before closing; import validates compatible sessions.
   Use **Borrar mis datos** to withdraw page-held data, including an active trial.

This version saves derived metrics and answers only. It does not record camera
pixels/audio, identify people, validate felt emotions, certify true/fake smiles, infer
EEG/health or implement the later observer modality experiment. Explicit
synthetic examples are not study participants or evidence of expression accuracy.

[Mathematics](MATHEMATICS.md) specifies descriptors, thresholds and sound;
[research plan](RESEARCH_PLAN.md) specifies stages, four experiments and sources.
Physical camera tracking, expression accuracy and actual hearing require a
consented human check separate from synthetic/browser/model-fixture QA.

The current [contour instrument](CONTOUR_INSTRUMENT.md) specifies the3–8-partial
map, geometric drives, worker network boundary and v1/v2/v3 export compatibility.
The [next human experiment](HUMAN_EXPERIMENT.md) separates the JAFFE geometry
pilot from prospective stimulus-evoked expression and listening trials.

## Optional expression readout,2026-11-04

Sai requested a visible emotion/expression identifier after the geometry-only
version. The mirror now offers four **experimental geometric hypotheses** beside
the face, highlights supporting points in violet and explains the deltas. Take a
new resting reference, then enable **Mostrar lectura orientativa**. This is a
hand-authored, unvalidated rule system, not a trained emotion model or FACS coder.
Unknown, mixed, reference-needed and tracking-lost states are explicit. The audio
map still depends on geometry, independently of these labels.

[Expression readout specification](EXPRESSION_READOUT.md) gives the exact features,
thresholds, persistence, limitations and validation plan. Trials automatically hide
labels and leave them hidden afterward; v3 exports retain prior exposure context
and expression geometry. Old imports retain unknown exposure, not assumed blinding.


## Head-relative comparison and cool contours,2026-11-12

The default **Compensar giros moderados · experimental** compares estimated
relative3D landmarks in a face-fixed plane, anchored by eye corners33/263 and
nasal bridge168/6. Iris/pupil landmarks are neither needed nor used as a gate.
Looking sideways with the eyes does not invalidate the geometry. Relative depth
comes from the pinned model; it is not measured physical depth. Moderate head
turns are supported experimentally; steep profiles/occlusion remain unknown.
The prior **Comparación frontal · anterior** mode remains available. Changing
comparison mode clears the resting reference and mutes sound until a new reference
is taken. New sessions identify geometry mode in v4 JSON/CSV; v1–v3 imports retain
their original protocol definitions.

All measured curves and evidence markers use violet, cyan, blue, teal or green,
with dark contour shadows. No skin-like pink/gold overlays remain. The four
expression labels are still unvalidated authored geometric suggestions, and the
sound still follows geometry rather than a label. No body tracking engine, native
sound tuning, camera activation or public hosting selection changed.

Validation:32 focused face tests pass, including synthetic yaw/pitch transforms,
iris independence, steep-profile rejection, reference invalidation, exports,
withdrawal, Web Audio, layout, and an actual pinned-model/WASM portrait fixture.
These checks do not establish expression accuracy during real human turns;
consented camera and hearing acceptance remain separate.


##40.4Hz reference,2026-11-12

Sai selected40.4Hz as the facial instrument's default, matching the numeric
reference of the native body set. Earlier facial builds defaulted to110Hz and
rejected values below55Hz. The browser instrument now starts at40.4Hz, offers
40.4–220Hz in0.1Hz steps and an explicit reset to40.4Hz. The displayed summary
shows the current base even while detailed controls are collapsed. Both contour
and six-voice comparison modes retain a first partial at the selected base;
no55Hz floor silently retunes a40.4Hz first partial.

In the aligned contour series the partials are40.4,80.8,121.2,161.6,202,242.4,
282.8 and323.2Hz. Rest uses the first three; geometric opening/bending brings in
higher partials, while contraction can displace upper frequencies without moving
the first one. The existing power normalization, volume, expression rules and
tracking-loss gain lease are unchanged. This is a compositional reference, not
a validated natural emotion-to-pitch or brain-frequency correspondence. The
browser and native engines share a numeric reference, not a synchronized phase clock.

Session/protocolv5 identifies the default/range/step. Each trial keeps its actual
fundamental; CSV appends fundamental_hz. Exact v1–v4 protocol definitions remain
accepted with their historical55–220Hz range, and old110Hz records are not retuned.
Actual loudspeaker/camera/hearing acceptance is separate from oscillator and
export checks. A live browser page keeps its current settings until a deliberate
reload; export unsaved research trials first. No native body process restart is
needed for this frontend update.

Validation for the40.4Hz change:34 focused tests passed, including both mapper
reference partials, real Web Audio oscillator values, decimal input/reset,
v5 JSON/CSV and historical110Hz imports, plus the existing geometry, camera
fixture, finite gain lease, withdrawal and narrow-screen journeys. This is
software/fixture verification; no physical hearing/camera acceptance is inferred.
