# Facial geometry and browser sound contract0.1

All descriptors are projected measurements, not internal-state labels. Coordinates
are anatomical model left/right; mirroring affects display only.

## Alignment

For normalized model point p_i=(x_i,y_i), image W×H, convert to pixels
q_i=(W x_i,H y_i). Let a=q_33 and b=q_263 be outer eye corners,
s=||b-a||, o=(a+b)/2, e_x=(b-a)/s, e_y=(-e_x.y,e_x.x).
The aligned point is u_i=((q_i-o)·e_x,(q_i-o)·e_y)/s.
This removes2D translation, scale and roll, preserves aspect and is tested under
known transforms. It does not compensate yaw, pitch or arbitrary camera projection.
The center c is u_168 (upper bridge candidate) or0 (eye midpoint).

Reject nonfinite/missing selected points, degenerate feature denominators,
outer-eye separation<8% image width, or z-based yaw proxy
|z_263-z_33| W/s>0.55. These are engineering thresholds for this prototype,
not validated anatomy/confidence thresholds. Detection/presence/tracking model
thresholds are0.6. Two detected faces invalidate a frame; no identity matching.

## Features

- Radial: mean ||u_i-c|| over105,334,159,386,61,291,13,14,152.
- Left/right eyebrow gap: y_386-y_334 and y_159-y_105 in face-width units.
- Left/right eye aperture: ||u_386-u_374||/||u_362-u_263|| and
  ||u_159-u_145||/||u_33-u_133||.
- Mouth aperture: ||u_13-u_14||/||u_61-u_291||.
- Asymmetry: left eyebrow gap minus right eyebrow gap. It describes this selected
  pair only, not all facial asymmetry.
- Directed bulge B(a,b,c)=cross(c-a,b-a)/||c-a||. Inward bend is
  B(a,b,c) sign(B(a,center,c)). Use fixed ordered endpoint/midpoint triples:
  mouth61/13/291, left brow336/334/300, right brow70/105/107.
  Zero orientation means the center lies on the chord; do not interpret it as
  a proof of flat physical surface. This is a signed projected chord descriptor,
  NOT differential3D surface curvature or a complete measure of concavity.

A reference uses featurewise medians and median absolute deviations across at
least10 contiguous valid frames covering≥1.2s, collected across at least1.8s. A gap>500ms restarts the collection window;
the final reference still rejects such gaps. The UI allows cancellation and ends
an unsuccessful collection after12s. Reject MAD>0.012 for either eyebrow gap or>0.035 for mouth
aperture. These thresholds require physical qualification. Changes are raw
feature minus personal reference, not ratios between different people's faces.

## Sound map

The independent browser engine uses six continuously running sine oscillators.
For feature changes d, movement vector m=(3d_radial,7d_browL,7d_browR,
2d_eyeL,2d_eyeR,1.2d_mouth), bend vector
b=(0,5d_browCurveL,5d_browCurveR,4d_asymmetry,-4d_asymmetry,6d_mouthCurve).
At sensitivity S∈[0.25,3], fundamental F∈[55,220]Hz:

f_i=clamp(F(i+1)2^clamp(S b_i,-0.2,0.2),55,1600).
g_i=(0.13 if i=0 else0.045)+0.075 clamp(|S m_i|,0,1).

Gain/frequency updates ramp; the master gain defaults to0.25 and is user-controlled.
Every update schedules a gain hold through280ms followed by release to zero at
420ms. Missing/invalid data explicitly release within40ms. The finite audio-thread
lease also releases if the main thread stalls. A compressor limits abrupt peaks;
no calibrated sound-pressure-level or hearing-safety certification is implied.
The figure reuses Weaver's phasor geometry from the current mapping; phases are
estimated for drawing, not actual sampled audio telemetry or physical cymatics.

Distances/curvatures are not frequencies. A designed map does not establish
natural consonance. Signed inward bend, harmonicity, roughness, subjective
pleasantness, perceived tension and practitioner feeling remain separate.
