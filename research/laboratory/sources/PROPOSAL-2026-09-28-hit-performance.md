---
project: harmonic-weaver
title: "Proposal for Nicolás: HIT, situated efficiency, and human performance"
type: research-proposal
date: 2026-09-28
status: proposal for discussion; findings are not presumed
---

# HIT, situated efficiency, and human performance

## The proposal in one sentence

Study whether temporal, spatial, and dynamic relationships among parts of a moving body predict effective performance **for a particular task, body, and set of constraints**, and whether those relationships can suggest changes that improve a later attempt. Beacon can make those relationships audible so a performer can explore them.

Our motivating example compares an Olympic-level gymnast, a para gymnast, and a recreational gymnast. Each may solve a comparable functional problem using different coordination. An Olympic routine is evidence of exceptional observed skill; it is not assumed to be a universal biomechanical optimum or the trajectory that either other person should copy.

Terminology: FIG recognizes Para Gymnastics, while gymnastics is not currently on the Paralympic Games programme. Use *para gymnast* unless referring to someone who is a Paralympian in another sport.

## What HIT contributes, and what must be tested

HIT proposes that some useful recurrent relations among coupled processes may help sustain organization with less corrective burden. Chapters 4 and 8 stress that consonance depends on the system and context; recurrence or a simple ratio alone does not establish efficiency. Here that idea becomes a **testable hypothesis** alongside established biomechanics and motor learning, not proof by definition.

**Primary hypothesis, to preregister:** for one defined task, dimensionless relational descriptors such as intersegment phase, proximal-to-distal sequencing, timing ratios, and correction normalized by useful output predict held-out outcomes better than absolute position, speed, and force descriptors given the same training data. Evaluate on people not used to fit the model.

**Transfer hypothesis, later:** some relational structure retains predictive value across bodies, skill levels, or tasks **after their different constraints are represented**. Success would support transfer; a well-measured failure would identify its boundary.

**Causal hypothesis, later:** a model-generated, feasible change improves a prespecified outcome in new attempts against ordinary coaching or feedback controls. A retrospective correlation, pleasant sonification, or resemblance to an elite athlete is insufficient.

“Peak performance” is a **situated frontier of tradeoffs** among task result, stability, effort, tissue loading, fatigue, expression, and the person's preferences. State the outcomes and limits before analysis. There is no single maximum independent of goals, body, equipment, and environment.

## How this connects to existing work

| Existing work | Contribution | Limit and role here |
|---|---|---|
| HarMoCAP | Pose, capture time, observation state, body normalization, and recording/replay. | A 2D camera does not measure force, torque, metabolic cost, or intention. Biomechanical validation requires appropriate 3D and/or external sensors. |
| Pads/Bands in harmonic-weaver | Geometry/activation architecture, body control, scenes, and person/hand audit. | `bands-v1` is a spatial instrument; #4 still needs a sustained two-person human run. It is not an efficiency measure. |
| `consonance/` v1 | Ballistic extrapolation error, the sign of `a·v`, continuous snap, and pitch control through Shaper's existing `/beacon/*` port. Replay and voice state were verified. | This is a musical prototype. It predicts inertial continuation, not an optimal trajectory or physical mechanical power. Nicolás described a newer sustained-drone revision as unpublished local work. |
| R1–R5 research and the ADDENDUM | Candidate metrics, camera limits, a perceptual baseline, and `f'(n,d)=f1·(n+d/2)`; extreme detuning reaches other notes in the `f1/2` series. | The existing 12–18 clip study and visual ratings can calibrate perceived movement consonance. They do not establish task success, energy cost, or peak performance. |
| #6, interference between states | Asks whether the next movement reinforces, leaves unchanged, or transforms/opposes the current pattern. | A competing or complementary model to ballistic error. Test both on the same sequences. A direction change need not be a failure. |
| HIT and Beacon | Relational theory; Beacon can be an acoustic feedback field that a body explores. | Sonification is an intervention and experience. Test its diagnostic and causal value separately. |

Proposed research architecture:

```text
video/sensors → HarMoCAP + external measurements → task-labelled dataset
              → competing models (absolute / relational / combined / control)
              → predictions for unseen people and attempts
              → individual suggestion or prosthesis setting → new experiment
              → [parallel] Beacon musical mapping and feedback evaluation
```

Keep software ownership clear: HarMoCAP acquires and estimates pose; offline analysis computes research features and models; Weaver organizes control and evidence; Shaper synthesizes. A new synthesis contract is a later decision if the current slave port becomes insufficient.

## First study: one task before generalization

1. Choose **one safe, repeatable task** with coaches and, where relevant, para gymnasts and prosthetics specialists. Define a functional equivalent when apparatus or available degrees of freedom differ. Do not demand an identical joint trajectory.
2. Define the primary result and limits before capture: for example technical success, stability, and maximum load, plus perceived control, comfort, and fatigue. Match task difficulty and conditions. Keep performance and cost separate.
3. Include several participants per profile for any between-group inference. Three illustrative people can debug the protocol and generate hypotheses, not establish universality. Record repeated attempts, deliberate variations, and within-person learning over time.
4. Synchronize pose with contact forces, EMG, IMUs, or 3D capture where the question requires them. Mark occlusion, uncertainty, and task events. Use synthetic fixtures for software tests; manage real participant video under a separate consent and access protocol.
5. Compute preregistered candidates: ratios of event timing, phase differences, intersegment sequence, functional variability, and correction relative to achieved result. Distinguish measured quantities from proxies. `a·v` derived from video is not measured mechanical power without mass and external force information.
6. Compare four families with participant-level holdouts: conventional absolute biomechanics, HIT-inspired relational descriptors, a combined model, and shuffled-relation controls. Report calibration, error, noise robustness, and performance on an unseen person; only then test another task. Do not select ratios or weights using the test set.
7. If prediction is useful, generate feasible individual suggestions within safety limits and test them in later sessions against coaching or ordinary feedback. Prespecify success, adverse outcomes, and stop criteria.

## Para gymnastics, recreational training, and prostheses

A para gymnast's outcome should be defined with that athlete and the task, not as distance from an Olympic body. Compare **functions and results**, without pretending that absent or modified joints are directly interchangeable or that symmetry is always desirable. Test generalization rather than assuming it.

For a recreational gymnast, the first useful output is a narrow, testable suggestion: “During this phase of this skill, a change in segment timing is associated with more stable execution without higher measured load; let's test a small adjustment.” Do not promise a total diagnosis or a single route to elite performance.

For a prosthesis, model geometry, stiffness, damping, energy return, alignment, mass, load limits, comfort, and adaptation time. Co-design with the athlete, prosthetist, and biomechanics researcher. Treat **person and prosthesis as one coupled system**. Start with simulation and reversible adjustments to an existing device. A new physical design would require mechanical testing and a separate clinical and sporting evaluation. Human-in-the-loop studies report both successful and unsuccessful optimizations; a simulated optimum may not be preferred or safer in use.

## What a successful result would mean

1. **Association:** ratios add out-of-sample predictive value beyond conventional variables. Initial evidence for the relational descriptor.
2. **Generalization:** part of the model retains value in new bodies or tasks with explicit constraints. Stronger evidence for HIT's transversal claim; report where it fails.
3. **Intervention:** ratio-guided suggestions or feedback improve new attempts without worsening agreed limits. Applied causal evidence.
4. **Prosthesis:** proposed settings improve an outcome chosen by the athlete after adaptation and independent testing. Evidence for that body, device, and task; further generalization remains open.

Publish these claims separately. If the relational model does not beat controls, that does not refute all of HIT; this operationalization would lack support. If it improves only the musical experience, Beacon retains artistic value without being presented as a sports optimizer.

## Roadmap and dependencies

| Stage | Deliverable and exit criterion | Dependency |
|---|---|---|
| 0. Technical baseline | Finish #4's human gate; listen to consonance; record the exact controller revision tested. | #4 and access to Nicolás's unpublished revision once shared. Offline research can start in parallel. |
| 1. Protocol | Preregister initial task, outcomes, population, functional equivalence, rival hypotheses, features, split, and consent. | Nicolás and domain collaborators choose the first task. |
| 2. Dataset and measurement | Synchronized schema, validity for each variable, several pilot attempts and profiles, quality and access rules. | 1. |
| 3. Models and validation | Absolute/relational/combined/shuffled comparison; blinded and unseen-person evaluation; uncertainty report. | 2; #6 supplies a candidate feature family. |
| 4. Feedback and training | Cross-over or randomized test of personalized suggestions and sonification against controls; retention and transfer. | 3; live audio validated for the sound arm. |
| 5. Prosthesis | Co-designed use case, simulation, reversible settings, measured loads and preferences, independent test. | 1–3 and a clinical/sporting team. Preparation can overlap. |
| 6. Transfer | Repeat in another skill, body, or system; describe invariants and failures. | 3–5; do not claim universality beforehand. |

## Draft issues for review — not filed on GitHub

These are candidate issue bodies. The numbers below are proposal identifiers, not GitHub issue numbers. Existing [#4](https://github.com/AlterMundi/harmonic-weaver/issues/4) owns the Bands live gate and existing [#6](https://github.com/AlterMundi/harmonic-weaver/issues/6) owns the interference idea. Neither should be duplicated. Work on the offline study can start while #4 remains open; live musical-feedback claims depend on an audible run.

### P0 — Establish the perceptual and musical consonance baseline

**Purpose.** Complete the baseline already specified in the movement-consonance handoff before treating its mapping as a scientific score of performance. Preserve the exact version of the controller used for every evaluation.

**Work.** Compare the published ballistic prototype with the most recent revision once Nicolás shares it. Listen to recorded replay and a live performer, including rest, sustained sound, intentional braking, acceleration, and a purposeful direction change. For the visual-perception study, collect the proposed 12–18 short clips in expert/consonant, neutral, and intentionally disruptive conditions, with repeated clips from the same performer where possible. Obtain blind ratings from at least three raters. Measure agreement and compare candidate descriptors with ratings without tuning on the evaluation clips. Use #6's interference measure as an additional candidate after it is specified.

**Deliverables.** Versioned run manifest; a consented clip inventory without raw participant material in git; rating protocol and de-identified ratings; a reproducible analysis of agreement and predictive association; listening notes that identify which gestures sound meaningful or confusing.

**Done when.** The report distinguishes what listeners saw, what the model estimated, and what the instrument sounded like; includes uncertainty and counterexamples; and makes no claim that perceptual preference proves task efficiency.

**Dependency.** Published driver v1 and access to Nicolás's revision when available. This issue can proceed alongside #4 and P1.

### P1 — Preregister a task-specific HIT performance hypothesis

**Purpose.** Turn “peak efficiency” into a prediction that can succeed or fail for one task. Establish the conceptual distinction between task performance, energetic economy, load, stability, and artistic expression.

**Work.** Select one repeatable functional task with athlete/coach input. Specify task success and difficulty, primary outcome, secondary outcomes, constraints that may not worsen, target population, and the functional equivalence between Olympic-level, para, and recreational participants. Preregister the relational feature families, conventional biomechanics baselines, shuffled-relation control, participant-level train/test split, minimum usable measurement quality, analysis plan, and what would count as support or non-support for HIT's added value. Define how a Pareto frontier is reported if objectives conflict. State that three example athletes are a feasibility set rather than a population estimate.

**Deliverables.** Dated preregistration, task event definitions, an outcome/constraint table, a comparison plan, and a decision log signed off by sport and research collaborators.

**Done when.** A new researcher could collect and score a trial without choosing metrics or success thresholds after seeing outcomes. The para athlete's target is defined with them, not copied from another anatomy.

**Dependency.** Nicolás chooses or approves the first task and outcome with domain collaborators. Does not depend on #4.

### P2 — Build a synchronized, consented measurement dataset

**Purpose.** Produce data capable of testing P1 and determine which variables are actually observable. Keep instrument prototypes and performance evidence distinguishable.

**Work.** Define a trial schema with participant pseudonym, task, body/equipment constraints, attempt, condition, timestamps, event labels, pose confidence and missingness, outcomes, and sensor calibration. Record repeated attempts across skill profiles and within-person variations. Synchronize HarMoCAP pose with 3D motion capture, force plates, IMUs, EMG, or metabolic measurements only as required by P1. Quantify calibration error, time alignment, occlusion, and repeatability. Specify consent, recording access, retention, and whether public footage has suitable rights; raw images and identifiable measurements stay out of git. Include a small synthetic example dataset and parser checks in the repository.

**Deliverables.** Schema and data dictionary, capture protocol, quality-control report, reproducible import/validation scripts, synthetic fixture, and a private dataset manifest with access rules.

**Done when.** Every model input can be traced to a sensor or labelled estimate, with units and uncertainty. A 2D `a·v` proxy is never labelled physical power; trials with insufficient evidence are excluded by predefined criteria.

**Dependency.** P1 defines the first task and required outcomes. Coordinate interface changes with HarMoCAP; no unneeded contract change.

### P3 — Compare relational HIT features with conventional predictors

**Purpose.** Test whether relational structure adds predictive information rather than merely redescribing a successful athlete after the fact.

**Work.** Implement prespecified dimensionless timing/phase/sequence/correction features; include the published ballistic error and #6's interference feature once defined. Build matched-capacity baselines from conventional absolute kinematics/kinetics, a combined model, and a shuffled-ratio or phase control. Use participant-level held-out evaluation and nested selection of model settings; do not tune on the held-out person. Report uncertainty, calibration, noise sensitivity, and failures by body/equipment profile. Compare both measured task outcomes and blind perceptual ratings, but report them separately. Add ablations to determine which relation matters and whether its sign/direction is stable.

**Deliverables.** Reproducible analysis code, frozen data split, benchmark report with confidence intervals, model cards listing required sensors and limits, and counterexamples where a surprising or reversed gesture improves the task.

**Done when.** The report can answer: “Does the relational model improve held-out prediction over the strongest fair alternative, by how much, and for whom?” A null or negative result is a complete result. No claim of cross-task transfer yet.

**Dependency.** P1 and P2; coordinate with existing #6 rather than redefining it here.

### P4 — Test individualized coaching and Beacon feedback prospectively

**Purpose.** Determine whether predictions can guide useful change in a new performance, and separately whether hearing the relationship helps a performer explore it.

**Work.** From P3, generate small, feasible changes for an individual rather than an idealized elite pose. Have athlete and coach review feasibility. Compare at least three conditions in randomized or counterbalanced order: ordinary coaching/control feedback, a model-informed suggestion, and model-informed Beacon sound where suitable. Include a non-informative or conventional sound control if interpreting a specific sonification effect. Measure later attempts, adaptation, retention, subjective agency, and prespecified load/stability constraints. Keep musical “tuned/detuned” movement expressive; do not present it as a moralized pass/fail signal. Run the audible Beacon path only after its hardware gate is checked.

**Deliverables.** Study protocol, versioned controller and sound mapping, session records, prespecified analysis, and a report of gains, harms, and individual variation.

**Done when.** Any claimed benefit comes from new attempts against a suitable control and includes the person's experience. Predictive accuracy, coaching improvement, and musical value are reported as distinct outcomes.

**Dependency.** P3 for model suggestions; #4's live validation for the sound arm. P0 informs sound design. May begin as a coaching-only pilot.

### P5 — Study person–prosthesis optimization as a separate use case

**Purpose.** Test whether the relational model can inform a prosthesis setting or design parameter for a specific athlete and task. Avoid treating the non-disabled athlete as a target trajectory.

**Work.** Co-define a functional goal and constraints with a prosthesis user, prosthetist, and biomechanics team. Choose a small, reversible parameter space on an existing device, such as stiffness, alignment, or control timing, and measure body–device coupling, interface comfort, loading, task result, and adaptation. Build a model or simulation with uncertainty and compare proposed settings against the current device and established fitting practice. Test promising settings only through a separate approved physical protocol. Document when preference and mechanical or metabolic measures disagree. New device fabrication is a later project following engineering and clinical review.

**Deliverables.** Athlete-defined objective, device parameter and constraint specification, validation plan, simulation/bench findings, and a separately reported human pilot if feasible.

**Done when.** A proposed setting has an explicit prediction, an independent test, and a report of benefit and tradeoffs for that person. A simulation alone does not satisfy this criterion.

**Dependency.** P1–P3 and a user/device/clinical collaboration. Planning may run in parallel with P4; physical experiments have their own gate.

### P6 — Test transfer across tasks, bodies, and then domains

**Purpose.** Address the transversal claim of HIT without assuming a universal ratio or conflating different meanings of “efficiency.”

**Work.** Freeze the strongest P3 model. Test it first on a second gymnastics skill, then on an additional movement setting with different constraints, and only later consider a non-movement system. Before each transfer, state which variables correspond functionally, what normalization preserves units, which outcome is analogous, and what adaptation is allowed. Compare zero-shot prediction, limited recalibration, and a new task-specific model. Include a conventional baseline and shuffled relations in each domain. Map failures to differences in dynamics, sensing, goals, or receivers, rather than hiding them in a new score.

**Deliverables.** Transfer specification for each pair of systems, frozen evaluation datasets, comparative results, and an explicit list of invariant relationships and boundary conditions.

**Done when.** The study can state exactly which relationships transferred, the size of their advantage over controls, what recalibration was required, and where they failed. A general claim about “any system” requires a programme of repeated independent replications, not one successful example.

**Dependency.** P3; P4 and P5 provide stronger intervention and device cases but are not required for the first observational transfer test.

## Concrete decisions requested from Nicolás

1. Which skill and functional outcome should be the first pilot? A short, coach-selected balance/transition task is a practical starting suggestion before a complex routine.
2. What counts as improvement, and which limits must not worsen: load, pain, fatigue, stability, or something else?
3. Which collaborators and consented recordings are actually available across the three profiles? Do not assume access to Olympic or para gymnastics footage or rights to reuse it.
4. Should Beacon first serve musical exploration, training feedback, or both in separately evaluated conditions?
5. For #6, which representation of state and interference should be compared first with the current ballistic model? Keep the formula provisional until the pilot.

## Starting references

- HIT, chapters 4 and 8: https://github.com/AlterMundi/book/blob/main/libro/Harmonic_Information_Theory_Foundations_Primera_edici%C3%B3n_digital.md
- Existing research and driver: `research/movement-consonance/`, `docs/CODEX_HANDOFF_MOVEMENT_CONSONANCE.md`.
- Current work: https://github.com/AlterMundi/harmonic-weaver/issues/4 and https://github.com/AlterMundi/harmonic-weaver/issues/6
- Gymnastics coordination learning: https://pubmed.ncbi.nlm.nih.gov/31226902/
- Landing strategies and forces: https://pubmed.ncbi.nlm.nih.gov/27863284/
- Prosthesis stiffness and athlete biomechanics: https://pubmed.ncbi.nlm.nih.gov/28659414/
- Prosthesis optimization with null results: https://pubmed.ncbi.nlm.nih.gov/34035945/
- Optimization and comfort/metabolic cost: https://pubmed.ncbi.nlm.nih.gov/41643358/
- FIG Para Gymnastics: https://www.gymnastics.sport/publicdir/rules/files/en_0.1%20-%20Statutes%20Edition%202025.pdf
- Current Paralympic programme: https://www.paralympic.org/sports
