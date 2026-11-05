# One-page proposal: Task-driven management of delay ambiguity under varying disturbances

Date: 2026-11-04. Status: a research hypothesis, not established novelty.

**Problem.** A robot's recent measurements may be consistent with several input delays when disturbances vary. Unique identification is not always necessary for control, while continuous probing can incur task deviation and computation. We ask when distinguishing remaining delay hypotheses is worth its cost.

**Starting point.** Six mechanism studies and an independent protocol-level reproduction of a common-controller example establish baselines. Retaining compatible delays and controlling them jointly is already prior art. Our empirical candidate sets also show weak group reliability under changing disturbances.

**Scope.** Begin with known low-dimensional dynamics, measured states and sent commands only. Assume delay is fixed within an identification window, with explicit disturbance-amplitude/rate and measurement-error assumptions. No execution timestamps are available. Learning and arbitrary delay switching are outside the initial scope.

**Hypothesis.** Additional identification may be unnecessary when plausible delays admit a common feasible action sequence with similar task cost. It becomes valuable when control consequences conflict. A task-based, computable trigger must be justified; a residual-score threshold alone is insufficient.

**Candidate contributions.** First, derive finite-window compatibility/separation conditions under disturbance variation budgets beyond elementary constant-bias profiling. Second, connect the necessity of discrimination to task cost or feasibility. Neither contribution is accepted if it is merely a direct application of existing model-discrimination results.

**Minimum experiment.** Construct harmless-ambiguity and conflicting-hypothesis cases. Compare common robust control, continuous active discrimination, task-triggered discrimination and an informed-delay reference. Pair disturbance/noise realizations and report task error, constraint violations, probing energy, trigger count and runtime. Reduced probing must not be obtained by materially degrading task performance. Extend to a planar quadrotor or mobile robot only after the mechanism is established.

**Two-week gate.** Week 1: verify matched baselines and formulate a precise proposition. Week 2: implement both cases and fair comparisons. If the trigger lacks justification or consistent benefit, revise the contribution. Previously inspected data are development data; subsequent claims require a fresh held-out evaluation. Deliverables are a precise question, proof outline and minimal comparison, not a promise of journal acceptance.
