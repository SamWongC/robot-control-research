# Experiment 2: Effects of Delay Estimation Errors on Constrained MPC

Date: 2026-11-03. Scope: a deterministic baseline comparison, not a proposed paper method or a real-robot validation.

## Problem and Setup

The true input delay is fixed at 0.30 s. The controller assumes delays of 0, 0.10, 0.20, 0.30, and 0.40 s, respectively. The model, cost weights, initial conditions, reference, and input constraints are identical across cases.

A one-dimensional double-integrator system moves from rest at 0 m to a reference of rest at 1 m. The sampling period is 0.05 s, the simulation duration is 20 s, and the prediction horizon is 40 steps (2 s). The state weight is diag(20,1), the input weight is 0.2, and the terminal state weight equals the stage state weight. No state constraints are imposed; the predicted input sequence is constrained by -2 ≤ u ≤ 2 m/s². This is an illustrative bound for method development, not a hardware-calibrated limit.

OSQP solves a strictly convex quadratic program. The constraints are included in the optimization, rather than enforced by clipping an unconstrained action afterward. The controller constructs its assumed queue from its own sent-command history and does not read the true queue. The true queue is initialized with zeros and has a fixed delay of six sampling periods. Full-state measurements are available without noise. There are no external disturbances, learning components, or delay adaptation.

## Results

| Assumed delay (s) | Full-run position RMSE (m) | Overshoot (m) | Settling time (s) | Total time at the applied-input bound (s) |
|---|---:|---:|---:|---:|
| 0.00 | 0.34406 | 0.71262 | Criterion not met within 20 s | 15.15 |
| 0.10 | 0.24125 | 0.44473 | Criterion not met within 20 s | 6.10 |
| 0.20 | 0.20927 | 0.16776 | 4.95 | 1.25 |
| 0.30 | 0.20951 | 0.01505 | 2.65 | 0.50 |
| 0.40 | 0.21454 | 0.03058 | 6.20 | 0.40 |

Settling criterion: the absolute position error is at most 0.02 m and the absolute velocity is at most 0.02 m/s, with both conditions remaining satisfied until the end of the simulation and with at least 1 s of observed residence. Overshoot is max(0, maximum position - 1 m). RMSE includes the initial transient and uses 401 state samples, including the final state; input statistics use 400 control steps. A numerical tolerance of 1e-5 m/s² is used to identify inputs at the bound. These results are not statistical confidence intervals or general conclusions across different tasks.

## Interpretation

1. With these parameters, substantial delay underestimation produces sustained oscillations and prolonged operation at the input bounds. The input constraints prevent the extremely large accelerations observed in the preceding unconstrained experiment.
2. The correct delay assumption gives the smallest overshoot and the shortest settling time. Overestimating the delay as 0.40 s still leads to settling, but with more slowly decaying oscillations.
3. The full-run RMSE for the 0.20 s assumption is slightly lower than for the correct assumption, by approximately 0.00023 m. Therefore, correct compensation cannot be claimed to be optimal on every metric. However, the overshoot in this case is approximately 0.168 m, about eleven times the approximately 0.015 m obtained with the correct assumption, and settling is slower. The metrics reflect different trade-offs.
4. The current cases are insufficient to establish a general delay-tolerance threshold or to prove that underestimation is always worse than overestimation. They also provide no proof of ultimate stability or safety.

## Files and Reproduction

Run the following commands in PowerShell from the project root:

```powershell
.\.venv\Scripts\python.exe -m unittest -v
.\.venv\Scripts\python.exe delay_mismatch.py
```

Use the project's requirements-lock.txt to recreate the environment. The original requirements.txt retains the dependencies for the earlier minimal experiment. This experiment additionally requires OSQP/SciPy; the lock file is preferred.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

- delay_mismatch.py: constrained MPC, the five assumptions, metrics, and plotting.
- test_delay_mismatch.py: consistency between prediction matrices and stepwise propagation, comparison with an independent coordinate-descent solution, comparison with the analytical solution when constraints are inactive, and checks of the true queue delay and input bounds.
- results/delay_mismatch/trajectories.png: position, velocity, and applied acceleration.
- results/delay_mismatch/performance.png: delay assumptions versus three performance metrics.
- results/delay_mismatch/assumed_*_steps.csv: stepwise data for the five cases. States are logged before action execution; post-execution states are also saved.
- results/delay_mismatch/metrics.csv: aggregate metrics.
- results/delay_mismatch/summary.json: configuration, dependency versions, source-code hashes, and complete metrics.

Timing measures only solver.solve and includes the effects of warm starting. It excludes model construction, parameter updates, and logging, so it cannot be interpreted as the real-time performance of the complete controller. Each case involves 400 optimization solves. An unsuccessful solver status or an input exceeding the feasibility tolerance causes the program to raise an error, rather than silently use a failed solution.

## Next Steps

First perform a finer delay sweep and sensitivity checks with different control weights and reference tasks, then introduce clearly defined external disturbances. Study unknown-delay identification and confidence only after the baseline behavior has been established. The present results support further investigation of delay mismatch; they do not establish the necessity or novelty of the proposed AI method.
