# Research direction review

Independent robotics/control project | 4 November 2026 | Discussion brief, not a paper abstract

## Decision: retain the project; change the paper contribution

Do not submit the present double-integrator study as a standalone RA-L research contribution. Preserve its code, counterexamples and numerical certificates. Continue only if a distinct, generalizable claim survives a focused novelty check.

## Current question and evidence

Unknown fixed input delay (0 or 1 sample), bounded changing disturbances and sensor errors can make an informative action damage a deadline-constrained task. A fixed separating first action is followed by causal innovation-feedback control. The task uses dt=0.05 s and a two-step endpoint after preview.

Preview | Position tolerance | Current finding
0.05 s | 0.2 mm | Fixed-probe causal obstruction
0.05 s | 0.2375 / 0.25 mm | Unresolved
0.05 s | 0.3 mm | Numerically verified causal policy
0.10 s | 0.2 mm | Numerically verified causal policy
The latest study checks 48 settings, 36 numerical policies and 834 implementation cases, with 55 passing tests. Continuous uncertainty supports are independently optimized. This is floating-point certificate evidence, not an exact-arithmetic proof or a global minimum-preview theorem.

## Why the current contribution is insufficient

Affine causal output-feedback convex synthesis is established [1]. Minimum discrimination horizons and closed-loop input design already exist [2]. Tracking/discrimination feasibility conflicts were studied previously [3]. Our elementary bounds and precision map specialize these ideas to one small plant.

Stronger passive baselines remove the old 0.4 s probing advantage. In the short-preview scan, nonzero actions identify at the same time but complete different numbers of tasks. This points to state/queue compatibility, not earlier information.

## What must not be claimed

No global all-policy feasibility frontier, no new affine-control framework, no implemented task-triggered/partial identification, and no confirmed RA-L novelty. Robot simulation or a neural residual alone would not establish a contribution.


---

# Candidate pivot and decision gate

Working hypothesis only | No confirmed literature gap

## Task-preserving partial delay discrimination

Can a robot retain several delay explanations, certify a common causal task continuation, and probe only when that continuation would otherwise be lost? Unlike the current fixed-probe implementation, this question does not require a unique delay whenever the task can tolerate ambiguity.

The information set must include possible delay, pending commands, physical state and disturbance conditions. Individual-model feasibility is not common-policy feasibility. Pairwise compatible hypotheses need not make the whole candidate set compatible.

## One bounded continuation cycle

1. State a precise proposition and explain what is not a direct application of existing affine, diagnosis or dual-control methods. A definition or another parameter sweep is insufficient.

2. Establish a nontrivial recoverability/computation result against matched causal baselines: common robust control, general active discrimination, passive adaptation and an oracle reference. Avoid artificial gains from unequal information or feedback classes.

3. Specify one meaningful robot task and discuss the proposition with a robust/predictive-control researcher before expanding implementation. Roughly two weeks is a stop/go planning limit, not a publication forecast.

## Stop rule

If only plant substitution, fixed-action tuning or standard LP reuse remains, end this paper route. Retain the repository as a research prototype and seek a thesis/laboratory problem. If a defensible gap survives, then plan a robotics validation study.

## Questions for an advisor

Is partial discrimination already a direct consequence of existing theory? Which robot deadline/constraint makes it important? Which available method is the strongest information-matched baseline?

## Selected primary references

[1] Skaf and Boyd, IEEE TAC, 2010. Affine controller synthesis.

[2] Raimondo et al., Automatica, 2016. Closed-loop guaranteed diagnosis.

[3] Cheong and Manchester, IFAC, 2014. MPC with discrimination and feasibility.

[4] Safe nonlinear active discrimination, arXiv:2606.19590v1 (2026 preprint). Separate assumptions and relaxation scope must be respected.
