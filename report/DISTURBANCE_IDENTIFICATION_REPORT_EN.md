# Experiment 3: External Disturbance and Delay Identification

Date: 2026-11-03. Deterministic mechanism experiment; no learned model or proposed confidence-aware controller.

## Setup

The same 1D double integrator tracks a constant 1 m reference from rest. Sampling 0.05 s; duration 20 s; horizon 40 steps; Q=diag(20,1), R=0.2, terminal Q. Command and delayed actuator input bounds are ±2 m/s². No state constraints or measurement noise. True delay is fixed at six steps (0.30 s) in all four runs. A positive external acceleration of 0.5 m/s² acts during transitions starting at 5 ≤ t < 8 s. The amplitude is illustrative (25% of the command limit), not hardware calibrated. External acceleration is added after the actuator; total acceleration can exceed the actuator command limit without violating that limit.

Four runs pair disturbance off/on with an informed fixed-delay MPC and an adaptive single-estimate MPC. The informed reference knows the true delay, but has no disturbance feedforward/observer. All other settings are matched. Thus absolute disturbance rejection performance is not a comparison against a strong disturbance-aware controller.

## Estimator and Information

Nine candidates, 0..8 steps. Each observed velocity transition gives an acceleration estimate. Each candidate predicts that acceleration using only the appropriately shifted sent command. The score is mean squared acceleration error over the last 20 transitions (one second); initial negative-index commands are zero. Start at assumed delay zero and freeze updates for the first 20 observations. Keep the previous estimate when it is within 1e-12 of the best MSE; otherwise select the smallest-index minimizer. Scores at time k use only transitions completed before k. The adaptive controller never receives true delay, actual applied input, or external disturbance. These quantities appear only in evaluation logs. The fixed controller also hosts the same estimator passively, isolating estimation behavior from adaptive control feedback. The best/second-best score gap is an uncalibrated diagnostic, not a probability or safety certificate.

## Results

| Case | Post-5 s RMSE (m) | Peak error after 5 s (m) | Recovery after 8 s (s) | Wrong-delay fraction during 5–8 s |
|---|---:|---:|---:|---:|
| fixed_clean | 0.000001 | 0.000006 | 0.00 | 0.0% |
| fixed_disturbed | 0.066687 | 0.160720 | 1.45 | 96.7% |
| adaptive_clean | 0.000063 | 0.000642 | 0.00 | 0.0% |
| adaptive_disturbed | 0.072495 | 0.202574 | 1.70 | 63.3% |

Metrics use 401 states including the final state; estimator statistics use decisions after warm-up. Post-5 s RMSE includes t=5..20 s. Recovery is the first time after t=8 s with |position error|≤0.02 m and |speed|≤0.02 m/s through the end, with at least one second residence. Wrong-delay fraction compares the pre-command estimate with six steps. A correct retained estimate during a near tie is not evidence of identifiability. No statistical uncertainty is claimed from these deterministic single rollouts.

## Interpretation and Limits

In the paired clean runs, the estimate is correct after warm-up. With the disturbance, the passive estimator selects an incorrect delay on 96.7% of decisions during 5–8 s, while the adaptive estimator does so on 63.3%. The adaptive disturbed run has 8.7% higher post-5 s RMSE than the informed disturbed reference. This is an observed association under different feedback trajectories, not a full causal isolation of identification error. Near rest, all candidate scores become nearly identical, so retention of the correct delay must not be interpreted as successful fresh identification.

Read identification errors separately for the passive and adaptive estimator: their command histories differ. Compare paired disturbance/no-disturbance runs before attributing degradation to disturbance. Tracking error can arise directly from external force as well as from delay misidentification. These four trajectories alone cannot separate all causal pathways or establish universal failure. In particular, the warm-up estimate is zero by design, and startup adaptation itself can affect closed-loop behavior. A constant reference becomes weakly informative near rest. Additional reference trajectories, disturbance amplitudes/signs, window sizes and a disturbance-observer baseline are needed. An online delay estimator is not automatically superior to an informed fixed-delay controller.

## Verification and Reproduction

Run `.\.venv\Scripts\python.exe -m unittest -v`, then `.\.venv\Scripts\python.exe disturbance_identification.py` from the project root. Use requirements-lock.txt. Tests check disturbance timing, noiseless recovery on excited synthetic data, invariance to adding future observations, and an explicit disturbance/incorrect-delay ambiguity. Original MPC/queue tests remain applicable. Optimization failures or infeasible returned inputs raise errors. Solver-only timings exclude parameter updates and estimator work.

Files in results/disturbance_identification: four case CSVs (pre-action states and scores plus post-action states); metrics.json; summary.json with configuration/environment/code hashes; tracking.png; identification.png; passive_scores.png. Full reports are saved at the project root in Chinese and English.

Next: inspect whether the passive estimator misidentifies delay during disturbance and whether the adaptive baseline incurs additional tracking cost. Then add disturbance-aware identification and controlled excitation; evaluate on held-out settings before developing confidence-aware control.
