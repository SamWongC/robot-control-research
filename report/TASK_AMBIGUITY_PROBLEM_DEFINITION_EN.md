# Problem definition v0.1: task-relevant input-delay ambiguity

Date: 2026-11-04. Scope: constructed feasibility witnesses, not a new identification algorithm or a verified novelty claim.

## Dynamics and information

Use the existing one-dimensional double integrator x[k+1]=A x[k]+B(u[k-d]+w[k]), y[k]=x[k]+e[k], with x=(position,velocity), A=[[1,.05],[0,1]], B=[.00125,.05]^T and dt=.05 s. The unknown delay d∈{0,1} remains fixed over the observation window and task. Commands are bounded by 2 m/s². Acceleration disturbances satisfy |w|≤.02 m/s² and |w[k+1]−w[k]|≤.01 m/s² per sample. Componentwise measurement error bounds are 1e-5 m and 1e-4 m/s, without stochastic assumptions.

The controller knows the model, bounds, goal, sample-indexed measurements and its own sent commands. It cannot access the actual delay, disturbances, state or execution timestamps. Evaluation truth is excluded from inference and optimization inputs.

## Historical compatibility

Set all historical commands, including pre-window commands, to zero and measured states y[-6..0]=0. A delay belongs to C if there exists a state/disturbance trajectory satisfying the dynamics, error bounds and disturbance amplitude/rate constraints over this history. Linear feasibility programs verify both candidates. The explicit common witness x=w=e=0 establishes C={0,1}. This deliberately unexcited window is not a claim about arbitrary data.

## Task and future uncertainty

At k=0, a target r=(p*,v*) arrives. At k=2 (0.1 s), require position error ≤.0002 m and velocity error ≤.003 m/s. There are no intermediate state constraints and no requirement beyond this endpoint. No infinite-horizon safety or stability claim is made.

The future uncertainty set is the product of the current measurement-error box and the bounded, rate-constrained disturbance sequence (w0,w1). It conservatively contains the history-conditioned possibilities: the cross-boundary disturbance rate and historical state/disturbance correlations are omitted. Robust success over this outer envelope implies success for the conditioned subset.

Write x2=A²x0+G_d U+Ew with U=(u0,u1),
G0=[[.00375,.00125],[.05,.05]], G1=[[.00125,0],[.05,0]], E=G0.
Exact componentwise support functions give terminal uncertainty radii R=(.00012 m,.0021 m/s). Symmetry gives the corresponding negative supports. Constant extreme disturbances attain both supports, so the rate limit is inactive in these witnesses.

Define U_d(r)={U∈[-2,2]²: |G_d U−r|+R≤(.0002,.003)}. The common open-loop sequence set is their intersection. Let A_d be the projection onto u0. Empty first-action intersection is stronger than empty sequence intersection for these open-loop plans. Generally these open-loop conditions do not fully characterize adaptive feedback: intersection alone does not ensure a common feedback policy, and disjoint robust open-loop projections alone need not rule out adaptation. The specific impossibility below instead follows from nominal necessary conditions.

## Two witnesses and independent algebra

A — harmless ambiguity: r=(0,0). The common sequence U=(0,0) is robustly feasible for both delays. Identification is unnecessary for this endpoint task, with no extension to indefinite regulation implied.

B — conflicting task: r=(.002 m,.08 m/s). Each delay separately admits a robust sequence: U=(0,1.6) for d=0 and U=(1.6,0) for d=1. Both nominal terminal centers equal the goal and the uncertainty radii fit within tolerance. The last command under d=1 has no influence within the horizon and is set to zero; post-horizon behavior is outside scope.

For an optimizer-independent impossibility proof, use the admissible exact-zero state/noise/disturbance realization. Under d=1, v2=.05u0 requires u0∈[1.54,1.66]. Under d=0, p2−.025v2=.0025u0, while p*−.025v*=0, so the tolerances require u0∈[-.11,.11]. These necessary intervals are disjoint with gap 1.43 m/s².

The indistinguishable histories force any causal controller to choose the same first action in both worlds. No second-step feedback can circumvent the incompatible necessary first actions. Thus no causal policy can guarantee this deadline task under both hypotheses from the stated information. Randomization does not restore a deterministic, all-realizations guarantee.

## Interpretation and next question

Identical delay ambiguity can be harmless for one task and decisive for another. These examples do not show that probing after the conflicting task arrives can solve it: information may already be too late. A subsequent study must introduce goal preview, deadline relaxation or a longer horizon, then test whether acquiring information changes feasibility relative to robust and passive adaptive feedback. Active identification, trigger design, long-run performance and the effect of disturbance-rate budgets remain untested. The witnesses motivate research; they do not establish originality.
