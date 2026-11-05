# Nearest-neighbor literature and novelty review

Date: 2026-11-04. Decision: several broad claims are already prior art; this project does not yet have a verified publishable contribution. A bounded search cannot establish that no equivalent work exists.

## Decision

The original confidence-aware learning-based MPC title is too broad. Experiments 1–6 are useful baselines and failure studies, not an established novel method. Setting RA-L as a target before this review was a planning decision, not a novelty finding.

Provisional research question: when disturbances vary and recent actions are weakly informative, how can a robot retain plausible delay explanations and identify only distinctions that matter for task control? This is a hypothesis, not confirmed originality.

## Access and review scope

F means full-text access and examination of core problem, method/theorem, validation and limitations; it does not mean every proof was independently re-proved or code reproduced. M means main text and selected relevant appendices. P means partial publisher text only. S denotes adjacent statistical work. Preprints are prior public disclosures, not necessarily peer-reviewed results.

| ID | Primary source | Scope | Consequence for this project |
|---|---|---|---|
| R1 | [Robust Data-Driven Output Feedback for Systems With Unknown Input Delays, v1, 31 Oct 2026](https://arxiv.org/html/2611.00841v1) | F: II-A, IV, Theorems 2/3, V-B | Retaining compatible delays and stabilizing them jointly is already addressed. Its synthesis concerns a disturbance-free plant after data collection, unlike ongoing disturbed tracking. That distinction alone does not establish our novelty. |
| R2 | [Heirung, Santos, Mesbah: MPC with active learning… Online model discrimination, 2019](https://static1.squarespace.com/static/5d4488dc0d24df0001719b1f/t/5d59c15afd93c4000193886c/1566163294489/CACE_2019_1.pdf) | F: §§3–6 | Active discrimination within predictive control is established; adding an information objective is insufficient. |
| R3 | [Safe, Real-Time Active Model Discrimination… Differentiable Reachability, v1, 2026](https://arxiv.org/html/2606.19590v1) | F: III, V, VI | Disturbed, constrained active discrimination has a general framework. A delay-specific contribution needs more than substituting delay candidates. |
| R4 | [Adaptive Reinforcement Learning for Unobservable Random Delays, v2](https://arxiv.org/html/2506.14411v2) | M: §§3–5 and interface appendices | Its hindsight delay reporting and packet interface differ from state/command-only inference. Baselines require matched information conditions. |
| R5 | [Adaptive-Robust Control… Unknown Input Delay](https://arxiv.org/html/1509.06542v1) | F: II-B, Theorems 1/2, III | Robot control under unknown varying delay and disturbances is not new. |
| R6 | [Delay Structure Conditions for Identifiability of Closed Loop Systems, 1992](https://publications.pvandenhof.nl/Paperfiles/Schoen-Autom92.pdf) | F: §2, Theorem 4.1, §5, appendix | Identifiability has established closed-loop foundations; this is not the same finite-window problem. |
| R7 | [Parametric identification… integer-type time delay… load disturbance, 2021](https://doi.org/10.1049/cth2.12170) | P: indexed model/analysis/example fragments | Joint identification is prior art. Complete assumptions and equations remain unverified. |
| R8 | [Time-delay identification… disturbance via correlation analysis, 2017](https://doi.org/10.1016/j.conengprac.2017.03.007) | P: introduction/procedure/example snippets | Disturbance treatment before delay estimation is prior art; our centering baseline is not a reproduction. |
| R9 | [Selecting informative conformal prediction sets with false coverage rate control](https://arxiv.org/html/2403.12295v2) | S: definitions, exchangeability and selection | Marginal versus selected-set reliability is an existing distinction; its guarantees cannot simply be transferred to dependent windows. |
| R10 | [Confidence-Aware Arbitration under Network Delay, RA-L 2025](https://elib.dlr.de/215438/) | P: institutional record and paper fragments | Confidence concerns shared-autonomy intent/arbitration, not delay-candidate confidence; keyword similarity is not method equivalence. |

R7/R8 remain incomplete despite publisher-page, legal PDF-link and public-author-version searches. Access failures were not bypassed. No assertion of complete full-text review is made for them.

## Claims to retire

Do not claim novelty for delay-induced oscillation; joint delay/disturbance estimation; constant-bias profiling or GLS; elementary constant/ramp ambiguity; candidate retention alone; controlling before unique identification; probing plus MPC; or overall coverage differing from conditional coverage. Independent test splits are research practice, not an algorithmic contribution. A residual neural network alone is also insufficient.

## Provisional narrower direction

**Task-Driven Predictive Control under Delay Ambiguity and Time-Varying Disturbances.**

Focus on whether identification is necessary for the task, not identification at every instant. Retain task-equivalent hypotheses and investigate only hypotheses that cause materially conflicting control consequences. This may still overlap with general discrimination and robust control; it is not yet a confirmed gap.

Start with known low-dimensional dynamics, delay constant within each identification window, explicit actuator semantics for later delay switches, bounded disturbance amplitude/rate, and specified measurement-noise assumptions. Do not conflate Gaussian measurement noise with unconditional hard bounds. No execution-delay labels are available to the estimator.

Candidate C1 is a finite-window distinguishability result with time-varying disturbance constraints and correlated differenced noise. It must do more than define a compatible set and observe that the true model satisfies its constraints. Useful results would quantify ambiguity or required excitation/window duration beyond elementary profiling.

Candidate C2 is a task-based criterion for deciding which delay distinctions warrant probing, with demonstrable control or computation benefits over common robust control and general active discrimination. A residual-score threshold is insufficient. Constraint guarantees require valid candidate containment, feasible control and a justified fallback.

Candidate C3, residual learning with a justified error budget, is optional. It should be considered only after a specific limitation of non-learning baselines has been established. Learning must not silently absorb delay mismatch into dynamics.

## Two-week novelty gate

Obtain the complete R7/R8 texts legally; reproduce or match an R1/R3 baseline. Write a precise C1 proposition and proof outline, checking whether it is a direct corollary of existing theory. Construct closed-loop cases where ambiguity is harmless and where it matters; compare always-probe, never-probe and task-driven probing. Then extend beyond the one-dimensional model. If differences reduce to straightforward application of general methods, change the contribution rather than adding modules.

The honest current description is: a study of how finite-window delay ambiguity under changing disturbances affects robot task control, with candidate management and task-driven identification under investigation. Existing results are baseline evidence. RA-L publication readiness and originality have not been established.

## Files and remaining work

The Chinese review contains the detailed claim map and reading locators. Evidence is recorded in results/literature_review_2026-11-04/evidence.json. Historical experiments and frozen rules are unchanged. Complete R7/R8 PDFs obtained through RWTH access would allow those missing checks to be finished. Further searches must test the provisional C1/C2 formulation; novelty cannot presently be certified.
