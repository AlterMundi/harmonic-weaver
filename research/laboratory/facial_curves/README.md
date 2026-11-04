# Local facial curves, actions and reference geometry

Research continuation,2026-11-04. Sai's correction: opening and distance from the nasal/eye reference are insufficient; each expressive line also has local shape and movement. Nico's center-relative concavity idea is retained alongside center-independent curve descriptors. This record adds a reproducible mathematical bench and a synthetic teaching note; it does not extend the live camera/audio mapping or reinterpret existing JAFFE results.

## Relevant prior work

- **FACS:** the [Paul Ekman Group description](https://www.paulekman.com/facial-action-coding-system/) defines anatomically based observable facial actions and their combinations. This is a useful vocabulary for movements and coding; it does not itself specify our numerical curvature estimator or make every line a unique emotion signal. We consulted the public description, not the paid full manual, and claim no FACS coding certification.
- **Tian, Kanade and Cohn,2001:** [publication](https://publications.ri.cmu.edu/recognizing-action-units-for-facial-expression-analysis), [author-hosted paper](https://publications.ri.cmu.edu/storage/publications/pub_files/pub2/tian_ying_li_2001_2/tian_ying_li_2001_2.pdf), especially sections3.2–3.3 and figures9–10. Their component models distinguish lip position, orientation and shape, represent eye/lip contours with parametric arcs, and measure eyebrow/cheek movement. A separate image branch detects changing furrows near the nose and outer eyes and measures nasolabial orientation. This directly supports studying local shape, motion and appearance rather than only one global facial expansion. Its published recognition results are not our results; no automatic emotion interpretation is inherited.
- **OpenFace:** the [maintainer's AU documentation](https://github.com/TadasBaltrusaitis/OpenFace/wiki/Action-Units) describes separate presence/intensity outputs, static versus person-calibrated dynamic models and weaker multi-face support. It is a candidate comparison tool rather than installed evidence or an annotation oracle. Review the code and training-data terms before selecting it. We did not install/run it here.
- **MediaPipe:** the [landmark guide](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker) documents estimated landmarks. Our existing engine computes projected contours from those points with blendshape output disabled. Landmark polylines, skin creases and measured physical3D surface curvature are different data products.

Primary-source descriptions were checked on4 November2026. The AFA article was published in February2001; a later repository/crawl timestamp does not make it a new study. The current collective reader returned no relevant record for the combined FACS/curvature query; this is a bounded lexical-search observation, not proof that the corpus contains no related work.

## Operational distinction: a bend is not yet a curvature profile

The live `geometry.ts` uses a directed chord descriptor for selected mouth/brow triples. If A,C are endpoints and B is the middle sample, its signed perpendicular offset is

`d = cross(C-A, B-A) / |C-A|`.

Its center-oriented sign multiplies this by the side on which the facial reference lies. This measures midpoint bulging relative to a chord. It does not describe the complete intervening curve. The historical code returns zero when the reference cannot orient the chord; do not reinterpret that historical value as proof of flatness. New research descriptors retain unavailable orientation as null.

A reference point and three curve samples cannot determine every intervening shape. For example,

`P(t) = (t, a(1-t²) + b t(1-t²)), -1 ≤ t ≤ 1`.

The endpoints and midpoint are independent of b. A second identical line translated vertically by h has the same constant separation h for every b. Yet b changes the local curve, including possible inflections. Our65-sample demonstration at a=0.15 yields:

| b | Three-point center-oriented offset | Maximum discrete curvature | Turning-sign changes |
|---:|---:|---:|---:|
| 0 | 0.150 | 0.299993 | 0 |
| 0.35 | 0.150 | 1.475295 | 1 |

These values use drawing units and a fixed C=(0,1). They are synthetic mathematical results, not face measurements, emotion proportions or FACS recognition accuracy.

## What to measure independently

| Description | Candidate measurements | Main qualification |
|---|---|---|
| Local line shape | Curvature magnitude/vector along the line, location of bends and sign changes, arc/chord ratio | Sparse points and image noise limit spatial detail; keep the profile rather than only a mean |
| Regional movement | Translation, inclination, local stretching, relative changes from rest, onset/offset/speed | Requires timestamps, repeated personal references and head-motion controls |
| Relations between regions | Left/right coordination, eye/lip separation, inter-region distances | Equal opening can coexist with different shapes; a single symmetry or expansion scalar is incomplete |
| Relation to the chosen center | Radial distances and projection of a curve's bending direction onto the vector toward C | This is a contextual descriptor; changing C must not change the line's own shape descriptors |
| Skin-line appearance | Appearance/deepening/length/orientation of forehead, periocular or nasolabial folds | Needs image/lighting analysis and independent annotations; not reconstructed by connecting a few landmarks |

Candidate action comparisons include inner versus outer brow movement, whole-brow lowering versus changing its arch, raising the lip corners versus separating the lips, and changing upper/lower eyelid contour at comparable aperture. Use the relevant FACS criteria with qualified annotations before assigning action codes. Those comparisons are proposed tests, not one-to-one emotion rules.

## Reproducible projected geometry

First use the existing eye-aligned, eye-span-normalized coordinate frame. For a smooth planar curve r(t), the oriented curvature is

`κ = cross(r′,r″) / |r′|³`.

Its sign depends on the chosen axes and traversal. Reversing the traversal changes that sign. A local curvature vector points toward the osculating-circle center, with length1/R. The vector is invariant to reversing the traversal; rotation/reflection rotate/reflect it. Thus we retain both the shape-only magnitude/profile and the orientation convention, rather than calling an entire open line simply positive/negative or concave/convex without a frame.

The bench uses the circumcircle of each ordered triple Pprev,Q,Pnext. With u=Pprev−Q, v=Pnext−Q, D=cross(u,v), A=|u|²vy−|v|²uy and B=ux|v|²−vx|u|², the vector is

`K = 2D(A,B)/(A²+B²)`.

Distinct collinear triples give K=0. Repeated, folded or nonfinite triples are rejected. Endpoint curvature is unavailable. The center-context projection is

`κC = K · (C−Q)/|C−Q|`.

It is null when C=Q or no reference is supplied. Positive means the vector points partly toward C; it does not indicate an emotion. Moving C changes κC while leaving |K| and the turning profile unchanged. Midpoint bulging toward C can occur while K points away from C: these are different notions and must not share an unqualified concavity label.

Lengths are measured in the supplied coordinate units; curvature uses inverse units. If the input is resized by λ, curvature scales by1/λ. Eye-span normalization or the explicitly dimensionless product κ·chord length supports scale comparisons. The returned arc-weighted mean is only a summary; retain all local samples. Turning-sign changes use the recorded technical threshold0.001rad, not a validated physiological noise limit. This is discrete osculating-circle geometry, not a fitted smooth contour or a segmentation algorithm.

Run without cameras, models or new dependencies:

```sh
node --test tests/test_facial_curve_geometry.mjs
node research/laboratory/facial_curves/render_demo.mjs /chosen/output/Curvas-y-gestos.html
```

Open the resulting self-contained HTML to vary shape, separation and reference independently. `demo.template.html` is the source template, not the deliverable. The optional browser verification uses the already installed laboratory Playwright/Chromium and `CURVE_DEMO_QA_DIR`; it checks the rendered mathematical controls, keyboard and narrow layout without human tabs or network requests.

## Next integration and validation

1. Validate pose/scale handling and per-line repeatability on consented controlled movement. Compare a stable reference, translated curves and deformed curves; compare different sampling/smoothing settings so jitter is not reported as an expressive bend. Derive uncertainty from actual recording noise, not synthetic tests alone.
2. Retain upper/lower lip and eyelid arcs and each brow separately, with region/order definitions, personal reference, timestamps and missing values. Compare measured changes with independently annotated actions and skin-line locations. JAFFE pose labels do not supply those action/crease annotations.
3. Introduce a versioned optional curve-profile record and readout in the existing face instrument once qualified. Keep previous scalar geometry/session imports and the accepted sound map available. The bench is not silently inserted into live sound here.
4. For sonification, keep aperture, shape, asymmetry, center relation and temporal dynamics as explicit parameters. Freeze a selected map and compare matched-aperture/different-curvature and matched-shape/different-aperture conditions, then performer reports and observer listening. A programmed frequency relation does not establish the felt emotion or naturally correct sound of a face.

The current practitioner trials and the [human experiment](../../../docs/laboratory/face/HUMAN_EXPERIMENT.md) remain the owning study path; this is a continuation, not another application or a recruitment/collection service.
