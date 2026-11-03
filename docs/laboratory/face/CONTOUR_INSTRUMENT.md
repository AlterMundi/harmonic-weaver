# Facial contours in the Weaver / HarMoCAP laboratory

The laboratory's **Rostro** entry opens `?mode=face` in the same maintained web distribution. It uses a local browser camera, pinned facial landmark worker, personal reference, explicit contour-to-sound map and private practitioner trials. Native HarMoCAP continues to own body tracking; its COCO17 stream does not become a dense face stream. This integration does not start a second native perception/audio stack or add an undeclared OSC channel.

Use the ordinary laboratory launch command and choose **Rostro**. In that view: **Mi cámara → select camera → consent/connect → Tomar referencia → Activar sonido**. The eye midpoint is the initial geometric center; changing center invalidates the reference. **Cuerpo · HarMoCAP** returns to the existing laboratory. If the same physical camera is already held by body capture, stop that source explicitly in **Fuentes**, then connect it in the face view. Camera enumeration/device-change refresh does not activate a stream, and no alternate camera is selected after a failed exact-device request.

## A designed map, without emotion inference

Only validated geometry and changes relative to the person's reference enter the mapper. There is no emotion classifier, emotion probability, sincerity score or inferred inner state. The rendered lines are estimated facial contours, not segmentation of forehead wrinkles, infraorbital shading or nasolabial skin folds.

The new default map `face-contour-series/0.2` exposes **Respuesta de riqueza** and **Desvío por contracción**, each0–1. The previous `face-six-sines/0.1` mapping remains selectable. These are compositional controls chosen to explore the human's intended connection between opening/smiling-like gestures and a richer aligned spectrum, and between contraction and displaced upper partials. Their expected emotional reading is a hypothesis, not a software measurement.

For sensitivity S, feature changes d, and clip to[0,1]:

- C = clip(-S*d.mouthCurve/0.06): the selected mouth-chord change.
- B = clip(S*(d.browL+d.browR)/2/0.08).
- E = clip(S*(d.eyeL+d.eyeR)/2/0.24).
- O = clip(0.65*B+0.35*E); spread Q=max(C,O).
- T = clip(-S*(d.browL+d.browR)/2/0.028): brow-to-eye contraction.
- Richness R = Q*richness_depth.
- Deviation D = T*(1-Q)*detune_depth.

For n=1…8, weights are n^-0.8 for n≤3 and R*n^-0.8 otherwise. Scale all weights by0.22/sqrt(sum(weights²)), before the separate master. This keeps the sum of squared sine gains constant; it does not guarantee equal perceived loudness. Frequencies are `f_n=f0*(n+offset_n*D/2)`, with offsets `[0,.65,-.55,.35,-.50,.40,-.30,.25]`. The first partial remains at the chosen f0; displaced spectra are not asserted to have their acoustic/perceived fundamental at that frequency. f0 remains55–220Hz; no frequency clipping folds several voices onto one limit.

These constants define an exploratory instrument. They are not physiological thresholds. Mixed contour changes may coexist; the mapping's cancellation is a documented design rule, not a claim about mixed emotions. Loss of valid tracking releases the sound rather than assigning dissonance to missing data. The existing finite gain lease and continuous oscillator pool are retained.

## Local processing and study records

The model/WASM ship with the same UI build. A worker network guard permits same-origin fetch/XHR only, including blocking SDK diagnostics to external services. No microphone is requested. Camera/mesh data remain in the browser; the app does not upload frames. Session JSONv2 records the exact selected mapping/depths; CSV appends these controls. Valid v1 records remain importable and are explicitly marked as legacy rather than silently relabeled with the new map. Session hashes detect accidental protocol mismatch, not scientific authenticity.

The body instrument's native six voices, presets, source and routing remain separate. The face sound is the browser engine; a native Shaper face-source adapter is not claimed here. No public webcam application, hosted per-person session backend or shared collection service is implied by source publication.

See [the human experiment and pilot record](HUMAN_EXPERIMENT.md) before claiming emotion/perception evidence.
