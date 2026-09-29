---
project: harmonic-weaver
title: "Candidate v0: relative-motion interference between body segments"
type: research-note
date: 2026-09-29
status: conceptual candidate for offline comparison; no audio mapping chosen
---

# Candidate v0 — does a new movement reinforce or change an existing relation?

Prepared in response to Nicolás and CompAII's request of 2026-09-29. This is one deliberately small operationalization of [issue #6](https://github.com/AlterMundi/harmonic-weaver/issues/6), to compare with the published controller on the **same recordings**. “Interference” here is a kinematic analogy, not a measurement of wave interference or physical force.

## State and measure

Represent the body as a small graph of adjacent tracked segments, initially shoulder→elbow→wrist and hip→knee→ankle on each visible side. For each edge `e = (parent, child)`, let `p` be a 2D keypoint position, `T` a robust torso-size reference, and `b_e = (p_child - p_parent)/T` the parent-to-child vector. Its causal time derivative `u_e = db_e/dt` is **relative velocity**: it removes translation shared by the two endpoints. The current local relational state `m_e(t)` is a smoothed history of `u_e` *ending before* the new observation. The new contribution is `Δu_e(t) = u_e(t) - u_e(t-Δt)`.

For a measurable prior mode and change, report two dimensionless components and one separate magnitude:

```text
I_e = dot(m_e, Δu_e) / (|m_e| |Δu_e|)       ∈ [-1, 1]
R_e = |cross2D(m_e, Δu_e)| / (|m_e| |Δu_e|) ∈ [0, 1]
A_e = |Δu_e| / measured Δu noise scale       (detectability only)
```

`I>0`: relative motion is being reinforced; `I<0`: it is being reduced or opposed. `I≈0` with substantial `R` is a **transformation**, such as turning the relation without immediately increasing or decreasing its speed. A change below the measured noise floor is “no detectable contribution.” If the prior relation is too weak to define a direction, label it “no established mode”; do **not** silently call it neutral. Keep `I`, `R`, and `A` continuous rather than choosing musical thresholds now.

The signed unnormalized form makes the relational ingredient explicit:

```text
u_e · du_e/dt ∝ (v_child - v_parent) · (a_child - a_parent)
             = a_child·v_child + a_parent·v_parent
               - a_child·v_parent - a_parent·v_child
```

The last two cross-terms say how one segment's change acts relative to the other's motion. The published controller computes ballistic position error and `a_j·v_j` **per zone**; its sign describes a zone's own acceleration/braking. This proposal asks whether the *relationship between two zones* is reinforced or altered. All terms are derived from the same kinematics; this is a candidate representation, not a new physical law. A sufficiently flexible model using all joint variables could recover the cross-terms, so added predictive value must be tested rather than asserted.

Minimal offline pseudocode:

```text
for each observed HarMoCAP frame in timestamp order:
    estimate T robustly for the recording; reject low-confidence/held keypoints
    for each valid parent–child edge:
        b = (child_xy - parent_xy) / T
        u = causal_smoothed_slope(b, past ~120 ms)
        m = causal_history_of_u(ending before this update, ~200–300 ms)
        delta = u - previous_u
        if norm(m) <= history_velocity_noise: output "no established mode"
        else if norm(delta) <= delta_velocity_noise: output "no detectable contribution"
        else: output I, R, A, confidence, edge_id, timestamp
```

The windows are starting values from the existing HarMoCAP/Weaver research, not fitted constants. Use real `captured_at_us`, a fixed or slowly calibrated `T`, and noise thresholds estimated from still/controlled footage **before** inspecting experimental labels. Do not differentiate raw adjacent camera frames twice. A later model may add time-lagged propagation along shoulder→elbow→wrist; this v0 measures only local edge change.

## Four sequences that discriminate it from the current controller

The numbers below are illustrative instantaneous velocities `v` and accelerations `a` in normalized camera-plane units; `p` means proximal and `c` distal. For a short step, `m≈v_c-v_p` and `Δu≈(a_c-a_p)Δt`, so the signs follow directly. “Surprise” means the existing constant-velocity predictor's error over a nonzero horizon.

| Sequence | Current zone reading | Candidate relation | Why it matters |
|---|---|---|---|
| **Shared acceleration:** `v_p=v_c=(1,0)`, `a_p=a_c=(0.5,0)`. | Both zones have `a·v>0` and a nonzero ballistic surprise. | `u=0`: **no established relative mode**, rather than two reinforced segment relations. | Whole-body translation may matter musically, but it should not be mistaken for a change *between* these segments. Analyze it in a separate global channel. |
| **Local pumping, relational reduction:** `v_p=1`, `v_c=2`, `a_p=1`, `a_c=0.2` along the same axis. | Both `a_p·v_p=1` and `a_c·v_c=0.4` are positive. | `u=1`, `du/dt=-0.8`; `I=-1`: the relative movement is shrinking. | Two locally accelerating zones can oppose the previously expressed intersegment relation. |
| **Turn without immediate strengthening or weakening:** proximal segment still; distal `v_c=(1,0)`, `a_c=(0,1)`. | Distal ballistic surprise rises; `a_c·v_c=0` does not identify the nature of the turn. | `u=(1,0)`, `du/dt=(0,1)`; `I=0`, `R=1`: **transformation**. | An intentional redirection should be distinguishable from simple braking or pumping; its task value remains to be tested. |
| **Same wrist brake, different parent:** distal `v_c=1`, `a_c=-0.5`. Case A: parent `v_p=0`, `a_p=0`. Case B: parent `v_p=2`, `a_p=0`. | The distal zone has the same surprise and `a_c·v_c=-0.5` in both cases. | A: `u=1`, `du/dt=-0.5`, `I=-1`. B: `u=-1`, `du/dt=-0.5`, `I=+1`. | An identical wrist event changes meaning with the body's prior relation. This is the clearest contextual prediction. |

“Reinforcement” in this note means reinforcement of the **measured relative-motion mode**. It does not yet mean good technique, low energy use, consonance perceived by a listener, or a desirable note. For example, maintaining an unhelpful coordination pattern may also yield `I>0`. The task and receiver still matter in HIT.

## What 2D tracking permits, and what it does not

HarMoCAP can provide timestamped 2D keypoints, observation/confidence state, estimated segment vectors, projected relative velocities, changes of those velocities, and this pairwise geometric score. With a fixed camera and visible joints, a common image-plane translation cancels in `b_e`. Pose jitter, occlusions, apparent torso-scale changes, and turning toward the camera can alter the score; these require quality flags and controlled replay.

It cannot directly provide 3D motion, muscle activation, contact force, joint torque, mass-specific energy flow, intentionality, or “peak efficiency.” In particular, `a·v` from 2D motion is a signed kinematic proxy rather than measured mechanical power. A real energy-transfer claim needs additional instrumentation and a defined task. The candidate also deliberately loses coherent translation of the whole body and can miss a meaningful parent→child **time lag**; these are boundary cases for v0.

## Offline comparison and a possible refutation

1. Freeze the published controller and run its per-zone `surprise`, `a·v`, and `d` alongside `I/R/A` on the same HarMoCAP JSONL files, with identical timestamps and comparable observation filters. Start with synthetic realizations of the four sequences, then real repeated gestures. Record the exact code revisions. Do not map `I` directly to Shaper yet.
2. Have reviewers label short, context-rich windows as reinforcing, reducing, transforming, or unclear **without seeing either metric**. Include purposeful reversals and delayed shoulder→elbow→wrist waves. Report agreement and disagreements; compare both the actual controller output and a fair baseline that can combine its per-zone features.
3. Check whether the relational score survives reasonable smoothing, tracking noise, camera angle, and participant changes. Compare to shuffled parent–child pairings. If it predicts only synthetic labels built from its own formula, that is a software check, not scientific validation.

The interpretation would be **questioned** if independent observers consistently see the same organization in both cases of the “same wrist” example, if intentional turns or delayed waves are systematically misread, if camera noise or viewpoint reverses the sign, or if the candidate adds no reliable out-of-sample information beyond per-zone features and shuffled edge controls. An improvement on the original controller alone would motivate further study, not establish HIT or efficiency. The strongest next step would then be a task-specific outcome test from the larger [performance proposal](PROPOSAL-2026-09-28-hit-performance.md).

Relevant primary studies show why relative organization is worth testing without making this formula canonical: [relative phase and interjoint coordination](https://pubmed.ncbi.nlm.nih.gov/8423174/) and [gymnastics longswing learning, where successful novice coordination did not simply converge on an expert's pattern](https://pubmed.ncbi.nlm.nih.gov/26087237/).
