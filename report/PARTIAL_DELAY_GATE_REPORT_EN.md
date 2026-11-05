# Three-delay partial identification: separation witness and observation verification

Date: 2026-11-04. Research gate, not confirmed RA-L novelty.

## Decision

A positive-margin instance permits separating delay 0 from {1,2} at time 1 and completing the task with one continuation shared by delays 1 and 2. Guaranteed unique identification at time 1 is impossible. However, the SAME physical policy uniquely identifies all delays at time 2 using already available measurements, without changing any command. The instance therefore does NOT establish a task cost of complete identification or an advantage over a strong baseline allowed to identify later. The early distinction is caused by transport timing, not a new control principle.

## Independent instance and policy

Double integrator: sample period 1 s, A=[[1,1],[0,1]], B=[0.5,1], fixed d in {0,1,2}, zero command prehistory, horizon 4. Input bound 1; state bounds |p|<=2 m and |v|<=2 m/s. Initial box radius [0.001,0.001], acceleration disturbance bound 0.002 with no rate restriction, measurement box radius [0.002,0.002]. Goal [0.1,-0.3], terminal tolerance [0.2,0.05]. Parameters are constructed, not calibrated to a robot.

Send a=0.4. At time 1, select the delay-0 branch if measured velocity exceeds 0.2, otherwise the shared {1,2} branch. The selected suffix is open loop. True delay and disturbances are used only for evaluation. Historical experiments and their frozen test sets are unchanged.

## Proposition A: robust early partial-identification witness

At time 1, measured-velocity intervals are [0.395,0.405] for d=0 and [-0.005,0.005] for both d=1 and d=2. The full joint observations for the latter two also have identical reachable sets: neither has yet received a command. For any first action, identical admissible initial states and disturbances/noises yield identical histories for those delays. Consequently no causal controller can guarantee unique identification at time 1.

The threshold classifier never removes the true model. Terminal maps are A^4 x0+G_d U+Ew. Their exact box support radius is [0.021,0.009]. Checking |G_d U-goal|+radius<=tolerance establishes a robust sufficient certificate for each shared branch. Input and intermediate-state constraints are also checked. Positive component margins and a nonzero first-action interval demonstrate robustness, not a noiseless isolated equality. These are floating-point numerical checks, not exact-arithmetic machine proofs.

| Quantity | Result |
|---|---|
| Commands after zero-delay branch | [0.4, -0.856, 0.9, -0.7440000000000001] |
| Commands shared by delays 1 and 2 | [0.4, -0.7034285714285715, 0.013714285714285863, 0.0] |
| Terminal uncertainty radius (m, m/s) | [0.021, 0.009000000000000001] |
| Worst component terminal margins (m, m/s) | [0.030714285714285666, 0.030714285714285652] |
| Input margin below actual bound 1 | 0.09999999999999998 |
| Robust admissible first input with fixed suffixes | [0.38771428571428573, 0.4117142857142858] |
| Common open-loop slack, first fixed | -0.048142857142857154 |
| Common open-loop slack, first free | -0.039999999999999813 |
| Exhaustive initial/disturbance vertices | 192 |
| Random episodes / transition records | 1536 / 6144 |
| Branch / time-2 identification errors | 0 / 0 |

## Stronger falsification: free complete identification at time 2

For unresolved delays 1 and 2, the time-2 velocity intervals are [0.393,0.407] and [-0.007,0.007], respectively. The command sent at time 1 cannot yet affect either model at time 2. Applying the same threshold identifies the delay; the already identified delay-0 branch keeps its label. No physical action changes. Thus this policy also satisfies complete identification by time 2, well before task completion at time 4.

Common open-loop LP results concern only a single fixed command sequence, with either fixed or free first input as indicated. Infeasibility in that class is not infeasibility of general passive feedback or dual control. Comparing it against a branching policy does not isolate the benefit of partial identification.

## Proposition B: exhaustive scalar observation cells for a fixed probe

For fixed a, let each model's scalar observation projection be a closed interval I_d(a). Sort all endpoints and enumerate each endpoint as a singleton and every consecutive open interval separately. Candidate labels are constant on every open cell. Cells with no candidates are unreachable. Assigning a robust common continuation to every nonempty cell covers all admissible scalar observations. Checking endpoints explicitly avoids missing boundary ambiguity.

The summary stores every cell, including the unreachable gap. Projection may retain extra models but does not delete the true one. In this example the full joint sets for delays 1 and 2 also coincide. Continuations are certified against unconditional uncertainty boxes, a conservative but sound choice. This is a sufficient verifier for one observation branch followed by an open-loop suffix, not a complete synthesis method for arbitrary feedback.

For m closed intervals there are at most 4m-1 endpoint/interior cells, excluding the two empty exterior regions. This is standard interval-arrangement reasoning and is not claimed as novel. Higher-dimensional observations, multiple branches, and changing first actions remain unresolved.

## Core synthesis gate remains open

No action-dependent valid cuts, observation-tree compression, optimality-gap bound, or completeness theorem were obtained. A conflicting set at one action cannot simply be forbidden for all actions because state and queued commands change. Establishing valid domains for such cuts is a real remaining obligation. Merely combining interval arrangements and robust LPs would not clear the independent-contribution gate.

## Validation and next decision

Cross-check the support formula with independent stepwise propagation of all 192 initial-state/disturbance vertices. Observation-noise coverage is analytic. An additional 1536 random episodes check causal execution and classifiers, with 6144 transition records. These are implementation checks, not statistical superiority or robot validation. Targeted test outcomes are saved separately in test_results.txt.

Retain this as a research unit test and falsification asset. Do not declare RA-L readiness or start large robot experiments from this result. The next substantive gate is a nondegenerate separation under matched timing/information, or a genuinely new computable structural result. Artificially early identification deadlines alone are insufficient.

Files: partial_delay_gate.py, test_partial_delay_gate.py, results/partial_delay_gate/{summary.json,trajectories.csv,test_results.txt}. No new literature originality certification was performed in this step.
