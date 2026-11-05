# Queue-driven branch merging: literature and mathematical feasibility review

Date: 2026-11-04. This is a research gate, not a new robot benchmark.

## Decision

Do not promote the current broad claim, "merge branches using command queues while retaining guarantees and reducing computation," to an independent RA-L contribution. Conservative sufficient conditions are available, but their immediate construction is standard lifting, robust tightening, and policy restriction. General lossless compression or unconditional performance-gap guarantees have not been established.

This is neither an impossibility theorem for all queue-related improvements nor a claim that one existing paper solves the exact project. No publication-ready proposition beyond direct framework application has been identified. Robot expansion is not justified by this claim alone.

## Primary-source neighbors and access scope

All six sources below were accessible in full. Targeted sections were inspected; their proofs were not all independently re-established. evidence.json records the scope.

- [S1: Speeding up POMDP Planning via Simplification, IROS 2022](https://indelman.github.io/ANPL-Website/Publications/Sztyglic22iros.pdf): bounds, pruning algorithm, Theorem 1. Bound-guided simplification preserving the solution of a given belief tree predates this proposal. This is not a bounded-adversarial hard-constraint certificate.
- [S2: Simplified POMDP Planning with an Alternative Observation Space and Formal Performance Guarantees, 2024 preprint v1](https://arxiv.org/html/2410.07630v1): observation topologies, policy spaces, Q bounds and proofs. Changing observation spaces with value guarantees is already a direct neighboring framework. Its probabilistic, bounded-reward assumptions differ from robust feasibility.
- [S3: Open-loop POMDP Simplification and Safe Skipping of Replanning with Formal Performance Guarantees, 2026 preprint v1](https://arxiv.org/html/2604.01352v1): Sections IV-V, Theorems 5.1/5.2 and supporting appendices. Adaptive observation omission and replanning omission have guarantees; relevant skipping bounds use positive Q values and likelihood-ratio conditions. "Safe" here must not be reinterpreted as all-disturbance hard safety.
- [S4: Symbolic Models for Nonlinear Time-Varying Time-Delay Systems via Alternating Approximate Bisimulation, author preprint](https://arxiv.org/pdf/1011.5835): model/stability assumptions and Theorems 5.8/6.2. Delay-system aggregation and policy transfer have an established theory. Incremental input-delay-to-state stability and its state-delay/known-input-delay structure do not directly match our uncertain fixed input delay under partial observation.
- [S5: Tube-enhanced multi-stage MPC, 2021 institutional full text](https://eldorado.tu-dortmund.de/bitstreams/92837a99-43d4-4dd9-aaeb-f0058d9e1d53/download): construction, robust horizon, Section 5 recursive feasibility and stability. Replacing later branching with tubes and retaining guarantees is established. Information timing and feedback assumptions require matching before use as a baseline.
- [S6: Scenario Tree Reduction via Wasserstein Barycenters, author manuscript](https://dan-mim.github.io/files/reduction_tree.pdf): nested-distance formulation and reduction algorithms. Information-structure-aware stochastic tree reduction is established. Distributional proximity alone does not certify every bounded disturbance realization.

These sources defeat broad novelty wording, not every possible narrow result. Different assumptions alone are not a contribution.

## Correct the information and complexity model first

A fixed delay with m candidates has m delay realizations, not m^H independent switching sequences. Observations, disturbances and adapted policies can still create a large tree. An artificially inflated switching tree is not a fair baseline.

Sent commands are known at each history. For a given delay, its pending queue follows from that history; it is not an additional bank of independent unknown continuous variables. Distinct histories can have distinct queues. Within-node and across-node uncertainty must be separated.

Distinguish computation caching (retaining history), policy merging (forcing a shared continuation), and uncertainty outer approximation (covering multiple nodes by a larger set). Losslessness of caching does not establish losslessness of discarding information. If a supposedly merged controller still uses the original history to choose different actions, it has not imposed the stated policy restriction.

## Four elementary obstructions

**A. Empty old queues do not eliminate unknown delay.** For x[k+1]=x[k]+u[k-d], d in {0,1}, x=0 and all old inputs zero, a fresh command 1 yields next states 1 and 0. Future command delivery still depends on delay after old queues have flushed.

**B. Identical terminal signatures do not preserve path constraints or observations.** Pending effective inputs (1,-1) and (0,0) both produce terminal state zero after two steps from zero. Their first states are 1 and 0. Only the latter meets |x|<=0.5. Equal terminal effects cannot justify full-history merging.

**C. Small distance alone does not preserve hard feasibility.** Consider x+=x+u+w, |u|<=1. Two distinguishable histories have state intervals centered at +/-epsilon, radius epsilon/8. Process disturbance and measurement-noise bounds are epsilon/8. The target is |x+|<=epsilon/2, with 0<epsilon<=1/4. Separate actions -/+epsilon work with margin epsilon/4. A forced common immediate action must lie in both [-5epsilon/4,-3epsilon/4] and [3epsilon/4,5epsilon/4], which is impossible. State distances can shrink while merging destroys feasibility. With infeasibility assigned infinite cost, no uniform finite value-loss guarantee follows from distance alone.

This is a family with shrinking tolerance. It is NOT a claim of discontinuity under fixed positive tolerance, a uniform strict-feasibility margin and suitable regularity assumptions. Those assumptions cannot simply be omitted.

**D. Full-path queue signatures need not admit linear dimension reduction.** For a scalar integrator with known state and delay d, the d pending commands map to the next d states through a unit-diagonal lower triangular matrix. Successive state differences recover every command. Its rank is d. If every path state matters, no nontrivial linear lossless reduction of that queue exists. This does not exclude approximation, task projections or caching; nor is it a lower bound for arbitrary encodings.

## A valid but standard restricted certificate

For fixed horizon and a common future OPEN-LOOP input vector U, lift each branch as

    X_i = b_i + G_i U + E_i w_i.

The offset includes current state and already issued commands. State-set uncertainty must be represented explicitly, not silently replaced by a known point. For each constraint row f_j, a bound

    delta_ij >= sup f_j^T (X_i-X_r)

over the declared input and uncertainty domains implies safety of branch i whenever the representative obeys

    sup f_j^T X_r <= b_j-delta_ij.

This follows by addition. Box support uses absolute-value weighted sums; polytopic support uses LPs. Apply every row at every constrained time. Bounding over all candidate inputs avoids solving the original control problem first but may be highly conservative. A check at one chosen input is not a globally valid merge rule.

This is standard robust tightening, not a new theorem. The same feedback law can produce DIFFERENT input values under different observations, so the open-loop difference bound cannot be transplanted without closed-loop and observation-update analysis. Exact information-state quotients also need successor, observation, and control/disturbance quantifier compatibility, the substance of existing simulation/abstraction frameworks.

A Lipschitz cost bound compares a transferable fixed policy on matched trajectories. It does not by itself compare an optimal merged policy with a more-informed original optimum. That requires policy transfer, common feasibility or valid bounds. For minimization with only additional policy restrictions, J_merged>=J_original is merely inclusion. Solving both problems globally to compute their difference is not a cheap certification algorithm.

## Claim disposition

| Claim | Assessment |
|---|---|
| Delete delay labels after flushing old commands | False in general: A |
| Equal terminal effect permits lossless merging | False in general: B |
| Small distance ensures hard feasibility/small optimal-value loss | Missing margin and policy conditions: C |
| A low-dimensional linear signature always preserves the full path | False in general: D |
| Common open-loop controls plus support tightening certify safety | Valid but standard |
| Exact quotient preserving tasks, observations and successors | Possible under sufficient structure; already an abstraction framework; no cheap new special criterion obtained |
| Nontrivial gap bound without expanding the full tree | Unresolved, with direct prior neighbors |

## Research decision and reproducibility

Do not automatically replace this claim with another promising paper title. Do not yet build a generic tree compressor or expand robot experiments to compensate for the missing contribution. Reopen only with a concrete robot bottleneck that remains after appropriate caching/tube/abstraction baselines, or a precise structural theorem not obtained by simple substitution. Neither is currently available. A focused discussion with a robust-control or planning supervisor is a better next investment than more toy examples.

Five exact-rational check groups are implemented in queue_merge_math_audit.py, with output in results/queue_merge_review_2026-11-04/math_checks.json. They reproduce counterexamples and standard bounds, not a new synthesis algorithm or a general machine proof. Historical experiments were not rerun or modified. This was a targeted literature review, not an exhaustive originality certification; the 2024/2026 entries are treated as preprints.
