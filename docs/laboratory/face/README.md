# Weaver facial mirror — contour instrument0.2

Build the existing laboratory with `cd laboratory-ui && npm ci && npm run build`.
The build prepares pinned model/WASM under ignored `public/face-assets`; weights
are verified before use. Serve the ordinary laboratory, then open
`/?mode=face` or the **Rostro** link. A static same-origin HTTP server on
localhost can also serve `laboratory-ui/dist`; remote camera use requires HTTPS.
No separate backend, account, host-camera permission or native Shaper is needed.

1. Try a drawn example, or choose **Mi cámara**, adult local-use consent and
   **Conectar cámara**. The first permission may reveal named camera choices.
2. Choose a reference center and take a resting reference. Changing center/source
   clears it. Keep the face close and frontal. A camera occupied by another app
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
pixels/audio, identify people, classify emotions, certify true/fake smiles, infer
EEG/health or implement the later observer modality experiment. Explicit
synthetic examples are not study participants or evidence of expression accuracy.

[Mathematics](MATHEMATICS.md) specifies descriptors, thresholds and sound;
[research plan](RESEARCH_PLAN.md) specifies stages, four experiments and sources.
Physical camera tracking, expression accuracy and actual hearing require a
consented human check separate from synthetic/browser/model-fixture QA.

The current [contour instrument](CONTOUR_INSTRUMENT.md) specifies the3–8-partial
map, geometric drives, worker network boundary and v1/v2 export compatibility.
The [next human experiment](HUMAN_EXPERIMENT.md) separates the JAFFE geometry
pilot from prospective stimulus-evoked expression and listening trials.
