# Topic decision: do not submit the present formulation as a standalone RA-L paper

Review date: 2026-11-04. This is a research judgment about the current claims, not an editorial verdict or acceptance forecast.

## Decision

**Retain the repository and reproducible evidence; stop treating the current double-integrator formulation as the core of an independent RA-L submission. Continue only after changing and justifying the contribution.** Choosing RA-L earlier was premature; the present evidence does not establish an original contribution. No deletion or abandonment of robotics/control as a field is recommended.

The synthesis is largely established machinery, the new frontier remains instance- and policy-class-specific, and stronger passive baselines remove part of the apparent active-identification advantage. No reviewed paper is asserted to duplicate every detail. Conversely, failure to find the same title or numbers does not establish novelty.

## Claim assessment

| Claim | Assessment |
|---|---|
| Delay-candidate consistency LP | Baseline specialization of set membership/model discrimination |
| One-step .048 separation threshold | Useful model/noise-specific lemma; not a general contribution |
| Shared-prefix future-branch obstruction | Valid explanatory counterexample; currently elementary low-dimensional elimination |
| Innovation feedback and polyhedral dual LP | Established affine robust-control construction after identification |
| .1 s preview / .3 mm precision frontier | Instance result, not a global all-policy exact frontier |
| Learning should serve the task | Existing motivation; not by itself a new method |
| Frozen paired tests and independent auditing | Evidence quality, not algorithmic novelty |
| Adding a neural residual or robot simulation | Requires a new problem/result, not automatic novelty |

## Primary-source comparison

The following are short claim locators, not independent re-proofs of all cited results. Accessible full text means relevant core sections were examined, not that every proof was reproduced. Preprints are public prior disclosures rather than assumed journal publications.

- [P1: Design of Affine Controllers via Convex Optimization](https://stanford.edu/~boyd/papers/pdf/affine_contr.pdf): Causal affine output feedback and worst-case convex synthesis are established. Does not establish the exact unknown-delay task-preview frontier of this project. Locator: PDF pp.3-6, sections II-V; worst-case problem (7), convex reformulation (16).
- [P2: Input design for guaranteed fault diagnosis using zonotopes](https://web.mit.edu/braatzgroup/input_design_for_guaranteed_fault_diagnosis_using_zonotopes.pdf): Bounded-error separating inputs are optimized with control-impact considerations. Not a proof of our exact numerical deadline/precision boundaries. Locator: Automatica 50:1580-1589; sections 2-4, reachable output sets and separating inputs.
- [P3: Closed-loop input design for guaranteed fault diagnosis using set-valued observers](https://web.mit.edu/braatzgroup/Raimondo_Automatica_2016.pdf): Minimum separation horizons, general polytopic uncertainties and measurement-updated input design are established. Minimum diagnosis time is not the same optimization as task-recovery preview time. Locator: PDF pp.3-5, minimum separation horizon, eqs.(15)-(20), Theorem 1, Algorithm 1.
- [P4: Model Predictive Control Combined with Model Discrimination and Fault Detection](https://skoge.folk.ntnu.no/prost/proceedings/ifac2014/media/files/1342.pdf): Combining tracking and discrimination, including feasibility loss, predates this project. Its formulation is not identical to our rate-bounded delayed-actuator problem. Locator: PDF pp.3-4, eqs.(11)-(14), Fig.1 and soft discrimination treatment.
- [P5: Finite Horizon Control Design for Optimal Model Discrimination](https://groups.csail.mit.edu/mers/papers/Blackmore_Williams_CDCECC05.pdf): Task-constrained discrimination is an old problem family. Expected-state/Gaussian statements are not our all-realizations bounded-noise guarantees. Locator: PDF p.2 Gaussian assumptions; pp.5 and 8 expected-state task constraints and limitations.
- [P6: MPC with active learning for stochastic systems with structural model uncertainty: Online model discrimination](https://static1.squarespace.com/static/5d4488dc0d24df0001719b1f/t/5d59c15afd93c4000193886c/1566163294489/CACE_2019_1.pdf): The value of active versus passive learning depends on task and uncertainty. Stochastic Bayesian formulation differs from bounded-error certification. Locator: PDF pp.2-4 active/passive value and model hypotheses; section 5.3 baseline definitions.
- [P7: Robust Data-Driven Output Feedback for Systems With Unknown Input Delays](https://arxiv.org/html/2611.00841v1): Compatible unknown delays can share a stabilizing controller. Synthesis addresses disturbance-free post-collection plants, not our ongoing disturbed endpoint task. Locator: Equation-error bound assumption; Theorem 3 / eq.(19).
- [P8: Safe, Real-Time Active Model Discrimination and Fault Diagnosis for Nonlinear Systems via Differentiable Reachability](https://arxiv.org/html/2606.19590v1): Set-based discrimination with nonlinear dynamics and robust constraints is already an active research area. Its separating objective relaxation is not a certificate of every task-preview boundary. Locator: Section III Problem 2 / eq.(3); section V, consistency relaxed to a separation objective.

P1 is decisive for the controller claim; P3 for broad minimum-discrimination-horizon claims; P4 for the general observation that discrimination can damage feasibility. None is claimed to solve the exact local rate-bounded delay/endpoint problem without adaptation.

## What the current theorem actually adds

The condition H^T lambda=g, lambda>=0, h^T lambda+|c|<=1-m is a robust linear-inequality dual bound. Innovation purification and lower-triangular gains provide an implementable instance. Adding disturbance-rate rows remains a polytopic specialization in our formulation, not a demonstrated new synthesis principle or a claim that every cited implementation directly handles the same correlations.

The two-future obstruction correctly distinguishes hindsight feasibility from causal guarantees. The bound |a|<=.035 still comes from this specific two-step task. It has not become a theorem for a useful general class of robots, delay sets or goals. The .1 s conclusion is restricted to guaranteed first-step identification; the N=0 and N=1 obstruction scopes differ. Unresolved cells remain unresolved, and floating-point support checks are not exact-arithmetic proofs.

There is also a gap between motivation and implementation: the original question allowed harmless delay ambiguity, but the current controller forces a separating first command, identifies a unique delay at k=1, then executes a known-model branch. Task-triggered or partial identification is not implemented and cannot be listed as an existing contribution.

## Project evidence and remaining gaps

The latest experiment has 48 settings, 36 independently checked numerical policies, 2 unresolved cells, 834 successful implementation checks and 55 passing regression tests. These support reviewability, not publication readiness.

At .4 s preview, the old passive baseline scored 101/128 while tracking/progress passive baselines reached 128/128. In the first-action scan, +.05 scored 239/256, +.1 scored 163/256 and task-generated actions 128/256, with identical first-step identification timing. Action-induced state/queue changes therefore matter. The latest certified policy changes the controller family again; results from different stages cannot be pooled into a single fair algorithm comparison.

The current work lacks a calibrated robotics task, matched general active-discrimination baselines and a nontrivial general result. Hardware is not an absolute gate in this review. A meaningful simulated robot may be sufficient for a later study, but changing the plant alone does not resolve novelty.

## Conditional pivot, not an approved new paper

Provisional question: **Task-Preserving Partial Delay Discrimination for Deadline-Constrained Robot Control.** Allow multiple delays to remain when a common causal task policy is certified; identify only distinctions that threaten task recovery. The information state must include possible delay, pending commands, physical state and disturbance conditions. Separate model feasibility and pairwise compatibility do not establish a common policy for the entire candidate set.

Merely defining task recoverability or reusing a robust LP is insufficient. Progress requires a demonstrably nontrivial theoretical/computational improvement and retained benefits against strong, information-matched causal baselines. Dual control, belief-space reachability and general discrimination may already cover the proposal; this is an unverified candidate gap.

## Bounded continuation gate

Allow at most one further argument-building cycle of roughly two weeks, adjustable to available time, not a publication timetable:

1. Write a precise candidate proposition and identify what is not a direct application of P1/P3/P4/P8. Stop this paper route if that distinction cannot be stated.
2. Supply a matched separation example or a bounded-error/complexity improvement. Full identification should be task-limited while a common causal policy retaining multiple models succeeds; do not manufacture gains by comparing weak open-loop with stronger feedback.
3. Specify one robot task with meaningful deadlines/constraints and obtain concrete feedback from someone familiar with robust/predictive control. Hardware purchases and neural additions are unnecessary at this stage.

If the outcome is only parameter tuning or a new plant for existing methods, terminate the current paper core and preserve the code as a reproduction/research prototype. Seek a problem linked to a thesis or laboratory task. If the gate succeeds, plan robotics validation before discussing a submission.

## Questions for a potential advisor

Is the proposed partial-discrimination/recoverability statement a direct corollary of existing dual/adaptive control? Which robot task makes the conflict important under realistic limits? What is the strongest baseline with exactly matched information?

A two-page English brief is provided for the user's own discussions; no messages were sent to anyone.

## Limits and artifacts

Bounded primary-source review, not exhaustive novelty certification. The Harirchi 2017 author PDF timed out; another 2017 author manuscript redirected to a JS-only repository. The previous 2021/2017 delay/disturbance full-text gaps remain. No experiments were rerun or historical hashes changed. Evidence: results/topic_review_2026-11-04/evidence.json.
