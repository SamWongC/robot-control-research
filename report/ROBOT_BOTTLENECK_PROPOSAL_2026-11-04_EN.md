# Robot bottleneck and candidate proposition: decision-preserving rollout refinement

Date: 2026-11-04. Decision: proceed only to a small falsifiable pilot, not a confirmed RA-L contribution. This step is a literature-backed proposal; no new benchmark, installation, robot experiment or measured speedup was performed.

## Recommended task and working title

**Decision-Preserving Multi-Fidelity Rollout Evaluation for Contact-Rich Robotic Pushing.** A robot pusher translates and rotates a nonconvex planar object toward a target pose, subsequently with obstacles. Start with fixed candidate batches in a Push-T-style simulator. Do not simultaneously add unknown delay, visual perception, friction identification and whole-body control.

The target is the cost of evaluating candidates: refine only contact segments that can affect the decision, while retaining evidence about decision quality relative to a specified fine simulator.

## Physical-task evidence

- Oxford/RAI/Cornell GPC v2: a Spot chair-pushing task around a C-shaped obstacle; Section V-B reports over 90% rollout compute, dominated by contact/collision physics, and about 5 Hz. These are author measurements, not our hardware results. [Primary text](https://arxiv.org/html/2510.14643v2).
- TU Darmstadt and collaborators, 2026 preprint: physical Franka Research 3 Push-T, RTX5090 planning at 8-10 Hz; Sections III-B/V discuss integration-resolution versus horizon tradeoffs. This establishes a remaining tradeoff in that implementation, not a universal GPU limit. [Primary text](https://arxiv.org/html/2606.20712v1).
- UPenn GRASP, 2025 RA-L project: nonprehensile manipulation uses global pre-contact sampling plus local complementarity control. Combining those ingredients is already prior work. [Paper](https://arxiv.org/html/2505.13350v1), [project](https://approximating-global-ci-mpc.github.io/).

Oxford thesis/ORA downloads partly returned 403. Claims above use accessible author manuscripts. Official complete GPC code and weights were not verified; exact reproduction is not promised.

## What existing methods do and do not establish

- Learned proposals improve candidate generation; they do not automatically remove the remaining evaluation cost. Use identical candidates to isolate the latter.
- GPU batching is mandatory as a strong comparator; beating serial Python is insufficient.
- [CacheMPC, preprint](https://arxiv.org/html/2606.28300v1) certifies cached convex-QP solutions under scheduled contacts. Its hardware Table VI reports full-certificate p50 3342 microseconds versus baseline 1883, with rejected queries paying both verification and solve costs. This is a setting-specific negative timing result, not evidence that all caches fail.
- [Tube-enhanced multistage MPC](https://eldorado.tu-dortmund.de/bitstreams/92837a99-43d4-4dd9-aaeb-f0058d9e1d53/download) addresses robust branching, not automatically the elimination of expensive collision solves. Applicability to the new task must be measured, not dismissed.
- [Adaptive Dynamics Orchestration](https://arxiv.org/html/2606.00085v1), Section IV, already selects model fidelity using errors/cost and context. Merely switching cheap and expensive models is not novel.
- [Multi-Fidelity BAI, NeurIPS2022](https://proceedings.neurips.cc/paper_files/paper/2022/file/71c31ebf577ffdad5f4a74156daad518-Paper-Conference.pdf) and [NeurIPS2024](https://papers.neurips.cc/paper_files/paper/2024/file/dc9e095f668044e7a0909a4ea3926beb-Paper-Conference.pdf) already study biased cheap evaluations and elimination. The missing robot-specific obligation is a valid, cheap bias enclosure, not the elimination rule itself.

We confirmed a real task and documented bottlenecks. We did NOT confirm that every cache, tube or abstraction fails on our unrun benchmark. Different papers' timings cannot establish that conclusion.

## Explicit proposition and novelty obligation

Freeze current state and finite candidates U_1,...,U_K. Define J_H as the cost under a named fine discrete contact model with fixed horizon, step, solver tolerances and cost. This reference is not physical truth.

**P1, unproved research target:** derive L_i<=J_H(U_i)<=B_i from coarse rollouts, local contact residuals, geometry/mode margins and selective refinement without first evaluating the complete fine rollout. Mode ambiguity, grazing, ill-conditioning and contact transitions must trigger valid enclosure/refinement or refusal, not unguarded continuation of a local smooth bound.

The possible contribution is a contact-transition-aware cost enclosure that is both valid and cheaper than full fine evaluation, together with its refinement strategy. Global Lipschitz propagation, same-mode KKT sensitivity, generic confidence intervals and elimination alone are not sufficient novelty.

Initially restrict the mathematical class to planar contacts and an explicitly regularized, well-posed solver. State how uniqueness, conditioning and geometry bounds are verified. Coarse-versus-fine numerical disagreement is not automatically an upper bound. Do not assume a universal bound for arbitrary frictional rigid-body systems. A theorem excluding almost all useful contact switches may be correct but unhelpful.

**P2, standard lemma:** choosing j with B_j-min_i L_i<=epsilon gives J_H(U_j)-min_i J_H(U_i)<=epsilon. This elementary consequence is not the contribution. It certifies only the given finite batch against the reference model, not global continuous-control optimality, closed-loop success or physical safety. Collision penalties are not hard-safety guarantees.

**P3, deadline behavior:** report the current certified gap on interruption. Do not promise epsilon accuracy at every budget. If certificates are insufficient, return an explicitly uncertified outcome. Start with predictive sampling, which selects the best sample. CEM elite-set selection and MPPI weighted updates require separate arguments.

An optional small learned scheduler can prioritize which segment to refine; the verifier, not the network, must establish bounds. Compare it with greedy nonlearned refinement and omit it if it adds no benefit.

## First pilot and stopping rule

1. Freeze state snapshots and candidate batches containing contact, release and pushing-side changes. Suggested initial 64/128-candidate sizes are planning choices, not measured capacity.
2. Fully evaluate each batch offline with the fine model to obtain reference costs and events.
3. Compare full-fine, full-coarse, GPU batching, warm starts, currently validated cache reuse, fixed refinement ratios, generic multifidelity elimination and applicable local/tube approximations. Unsupported baselines are not recorded as failures.
4. Separate development/test scenes and trajectories. Include contact-edge states and geometry changes; changes outside a bound's assumptions must be marked unsupported.
5. Measure synchronized total p50/p95/p99 latency, certificate coverage, invalid enclosures, refined fraction and decision-cost gap. Fewer simulated steps can lose to full GPU batching because of divergence and small batches. Evaluate closed-loop performance separately.

A proposed project gate is >=30% reduction in total p95 at matched candidate sets/reference-error requirements, including verifier overhead, with no observed invalid certificates on held-out tests. This is an engineering gate, not a journal criterion; empirical coverage is not a proof. Stop if all cases require full refinement, bounds are uselessly wide, or GPU batching is faster.

## Resources and status

[Hydrax](https://github.com/vincekurtz/hydrax) provides candidate JAX/MJX infrastructure. Only its public documentation was inspected; local compatibility, installation and exact GPC replication are unverified. Start small and measure memory/runtime before assigning large batches to the 8GB laptop GPU. Future RWTH robot access is not yet established.

Preserve the delay project as a research asset without forcing delay into this task. Evidence status: real task confirmed; bottleneck documented by authors; superiority over existing methods untested; new enclosure theorem unproved; RA-L readiness unconfirmed. This supports a focused pilot, not an originality or acceptance guarantee.
