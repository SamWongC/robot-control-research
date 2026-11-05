# Common-controller baseline: independent protocol reproduction

Date: 2026-11-04. Scope: reproduce the qualitative claim of the numerical example, not author-record bitwise agreement or a new algorithm.

## Source and attribution

[Robust Data-Driven Output Feedback for Systems With Unknown Input Delays, v1](https://arxiv.org/html/2611.00841v1), Section V-B and Theorem 3, Eq. (19). We implemented its compatible-model construction and common-gain LMI. The source makes no arbitrary-switching guarantee, and synthesis applies after data collection without ongoing disturbance. This study reproduces those limited conditions.

## Independently specified implementation

The ARX recurrence is y[k]=1.9*y[k-1]-0.88*y[k-2]+0.2*u[k-3]+0.1*u[k-4]+w[k]. We generate 12 records of length 16, alternating two random input amplitudes in each. NumPy PCG64 seed 806 draws two amplitudes, two initial outputs and fourteen uniform equation errors per record, in that order. Missing past inputs are zero. Columns k=5..15 produce 132 samples. The predetermined selected-equation error-energy bound is 0.0132. Candidates have delays 1,2,3 and history dimensions (2 output,5 input), total seven. SVD constructs the least-squares fit and coefficient ellipsoid for each retained delay.

The common-gain SDP enforces Eq. (19) with shared F,L and candidate-specific P,lambda. First maximize an absolute strict margin with sum(trace(P))=3; then minimize ||L||²+0.001||F||² while retaining half that margin. This secondary surrogate and the random draw order are explicit independent choices because complete author code/data were not supplied. CVXPY and solver versions are recorded, not assumed identical to the paper.

## Results and checks

| Delay | Rank | LS residual energy | Remaining budget | Min LMI eigenvalue | Illustrated closed-loop spectral radius |
|---|---:|---:|---:|---:|---:|
| 1 | 4 | 0.003407089 | 0.009792911 | 0.000205391 | 0.894189 |
| 2 | 4 | 0.003407089 | 0.009792911 | 0.000205391 | 0.880188 |
| 3 | 4 | 0.003407089 | 0.009792911 | 0.000205391 | 0.908530 |


All candidates survive the same predetermined bound. One recovered gain is used without model switching. The illustrated plants have the same denominator; the middle delay uses numerator coefficients (0.2,0.1), and the other two use (0.1,0.2). Each is checked against the collected data. Initial history is (1,0.9,0,0,0,0,0). The plotted output is the most recent STORED output y(k-1); the horizontal axis is a sample index, with no physical sampling time assigned.

The first-stage strict margin is 0.000410782367, and the second retains 0.000205391183. All illustrated open-loop spectral radii are 1.1. The maximum sampled closed-loop radius across 3000 ellipsoid points is 0.926308, below one.

Every returned 18x18 LMI and positive-definite P is reconstructed independently using NumPy. Strictness is checked against 100*n*machine_epsilon*max(1,||matrix||₂); solver status alone is insufficient. Random interior/boundary sampling supplements this check, not a replacement for the LMI. These are floating-point checks, not interval/exact-arithmetic certificates. Trajectories illustrate three compatible plants, not every model by simulation.

## Difference from a numerical duplicate

The original printed LS residual is 0.004189; our independently generated record gives approximately 0.003407089. The paper's printed regressor condition number is 89.44; ours is approximately 89.84044. We did not search seeds/draw orders to match those numbers. The recovered controller and matrix margins can differ. This is protocol-level qualitative reproduction, not exact numerical replication. The study does not reproduce the other numerical example or sensor-noise extension.

## Consequence for the proposed project

The baseline confirms that unresolved delay is compatible with a working common controller. Therefore, candidate retention plus common control is not our novelty. A narrower proposal is saved separately. Ongoing varying disturbances, task constraints and deciding whether to identify remain open design tasks for this project; their absence from this particular example does not prove a literature gap.

## Files and reproduction

Run `.\.venv\Scripts\python.exe -m unittest -v test_common_delay_reproduction`, then `.\.venv\Scripts\python.exe reproduce_common_delay.py`, then `.\.venv\Scripts\python.exe summarize_common_delay.py`. The experiment overwrites only its own output folder on rerun. Dependencies are locked separately in requirements-reproduction-lock.txt, preserving the historical lock file.

results/common_delay_reproduction contains the complete generated data, F/L/K/P matrices, three LMI matrices, trajectories.csv, summary.json and common_controller.png. Tests check equation-error consistency across the three physical examples, ellipsoid factors, history timing and rejection of boundary matrices. Four targeted tests passed before synthesis. The complete regression log is common_delay_full_tests.log. Reports are in report/; one-page plans are RESEARCH_PROPOSAL_ZH.md and RESEARCH_PROPOSAL_EN.md.
