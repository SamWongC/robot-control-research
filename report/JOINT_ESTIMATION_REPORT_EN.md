# Experiment 4: Joint Delay and Constant-Disturbance Estimation

Date: 2026-11-04. Non-learning baseline study; not a novel algorithm or real-robot result.

## Method

For every candidate delay d=0..8, compute residual r[j,d]=(v[j+1]-v[j])/0.05-u[j-d] on the last 20 transitions. Profile out a constant disturbance: b[d]=mean(r[:,d]); score[d]=mean((r[:,d]-b[d])²). This is elementary least squares with an intercept, not a full moving-horizon state estimator. The raw baseline scores mean(r²). Both start at zero delay, update only after 20 observations, and retain the previous candidate if within 1e-12 of the minimum. Constant commands, and even linear ramps whose shifted sequences differ by constants, cannot generally separate delay and constant disturbance. No score is a calibrated probability.

## Protocol

Same double integrator, 1 m step target, dt=0.05 s, 400 transitions, horizon 40, Q=diag(20,1), R=0.2, terminal Q, actuator bounds ±2 m/s². No state constraint, noise, randomness or changing true delay (always six steps). Disturbances act for 5≤t<8 s: zero, constant ±0.25 and ±0.50 m/s², or a smooth positive half-sine 0.5*sin(pi*(t-5)/3). These are declared mechanism probes, not held-out tests or hardware-calibrated conditions.

Five modes per scenario (30 rollouts, 12000 QPs): fixed uses known delay without disturbance compensation; raw uses the original single-delay estimate; joint uses the new delay estimate without disturbance compensation; joint_ff additionally predicts constant external acceleration using its selected candidate's bias; fixed_ff uses the true delay and an estimated bias for that candidate, giving an informed disturbance-aware reference. Bias is incorporated in every predicted state transition inside the constrained optimization, not subtracted from the final action. Both estimators run passively on every trajectory. Compare them on fixed trajectories to hold input history constant; compare raw/joint for changes to identification alone, joint/joint_ff for compensation (feedback histories subsequently differ). Fixed modes know true delay; adaptive modes never receive it or true disturbance. All scores and biases at k use transitions completed before k. Negative command indices are zero. Bias is unconstrained; no regularization or online parameter tuning is used.

## Results

| Scenario | Mode | Post-5 s RMSE (m) | Recovery after 8 s (s) | Raw wrong-delay fraction | Joint wrong-delay fraction |
|---|---|---:|---:|---:|---:|
| clean | fixed | 0.000001 | 0.0 | 0.0% | 0.0% |
| clean | raw | 0.000063 | 0.0 | 0.0% | 0.0% |
| clean | joint | 0.000063 | 0.0 | 0.0% | 0.0% |
| clean | joint_ff | 0.000063 | 0.0 | 0.0% | 0.0% |
| clean | fixed_ff | 0.000001 | 0.0 | 0.0% | 0.0% |
| plus025 | fixed | 0.033343 | 1.3000000000000007 | 96.7% | 28.3% |
| plus025 | raw | 0.036146 | 1.5 | 61.7% | 26.7% |
| plus025 | joint | 0.034956 | 1.5 | 85.0% | 26.7% |
| plus025 | joint_ff | 0.018321 | 2.1500000000000004 | 80.0% | 25.0% |
| plus025 | fixed_ff | 0.016927 | 2.1000000000000014 | 93.3% | 26.7% |
| plus050 | fixed | 0.066687 | 1.450000000000001 | 96.7% | 28.3% |
| plus050 | raw | 0.072495 | 1.700000000000001 | 63.3% | 26.7% |
| plus050 | joint | 0.069943 | 1.700000000000001 | 86.7% | 26.7% |
| plus050 | joint_ff | 0.036196 | 2.3500000000000014 | 93.3% | 25.0% |
| plus050 | fixed_ff | 0.033854 | 2.3000000000000007 | 93.3% | 26.7% |
| minus025 | fixed | 0.033343 | 1.3000000000000007 | 98.3% | 30.0% |
| minus025 | raw | 0.036686 | 1.200000000000001 | 58.3% | 26.7% |
| minus025 | joint | 0.034260 | 1.5 | 80.0% | 25.0% |
| minus025 | joint_ff | 0.016700 | 2.1500000000000004 | 91.7% | 23.3% |
| minus025 | fixed_ff | 0.016926 | 2.1000000000000014 | 95.0% | 28.3% |
| minus050 | fixed | 0.066686 | 1.450000000000001 | 98.3% | 30.0% |
| minus050 | raw | 0.072798 | 1.3499999999999996 | 56.7% | 26.7% |
| minus050 | joint | 0.068565 | 1.700000000000001 | 80.0% | 25.0% |
| minus050 | joint_ff | 0.033540 | 2.3500000000000014 | 91.7% | 23.3% |
| minus050 | fixed_ff | 0.033853 | 2.3000000000000007 | 95.0% | 28.3% |
| slow_hump | fixed | 0.048104 | 1.0999999999999996 | 95.0% | 91.7% |
| slow_hump | raw | 0.055811 | 1.0 | 80.0% | 71.7% |
| slow_hump | joint | 0.047057 | 1.25 | 66.7% | 53.3% |
| slow_hump | joint_ff | 0.029936 | 1.950000000000001 | 88.3% | 46.7% |
| slow_hump | fixed_ff | 0.028806 | 1.9000000000000004 | 95.0% | 90.0% |

Wrong-delay fractions above use decisions at 5≤t<8 s; estimates at t=5 s predate the first disturbed transition. Both passive estimators are reported even when they do not control the plant. Post-5 s RMSE uses 301 state samples t=5..20 s. Recovery requires position error≤0.02 m and |velocity|≤0.02 m/s through the end with at least 1 s residence. Plateau diagnostics in metrics.csv use 6≤t<8 s, when the one-second window excludes the disturbance onset. Disturbance RMSE compares the pre-command estimate with disturbance acting in the next transition: change-point lag is included. Commands and delayed actuator inputs are bounded; total acceleration includes external force and may exceed those bounds.

## Main Findings

On the SAME fixed-controller positive-0.50 trajectory, disturbance-period wrong-delay fraction falls from 96.7% to 28.3%; the joint plateau fraction is 0.0%. In closed loop, post-5 s RMSE is 0.072495 m (raw), 0.069943 m (joint), 0.036196 m (joint_ff), and 0.033854 m (fixed_ff). However, recovery after pulse removal is 2.35 s with joint_ff versus 1.70 s with joint: the window retains obsolete disturbance estimates. For the smooth hump on the fixed trajectory, joint plateau misidentification is 95.0%. Thus constant-bias estimation resolves much of the original constant-disturbance failure, but not changing-disturbance ambiguity. This elementary baseline must be included before attributing benefits to AI or confidence mechanisms.

## Limits and Verification

This is a small, noiseless, known-model, constant-delay experiment. Centering residuals can reject constant bias while removing information about delay. A better fit is not necessarily a correct or identifiable delay. Smoothly varying disturbances violate the local-constant assumption; switches at 5/8 s also straddle windows. Direct velocity differencing may amplify measurement noise. No universal improvement, safety, stability or novelty follows from these runs. Existing and new tests cover excitation-based recovery, ramp ambiguity, disturbance response, causality and constrained optimization; see joint_estimation_tests.log. Full configurations and source hashes are saved. Intermediate QP failures and returned input violations raise errors.

## Reproduction and Files

From the project root run `.\.venv\Scripts\python.exe -m unittest -v`, then `.\.venv\Scripts\python.exe joint_estimation.py`. Dependencies: requirements-lock.txt. Results in results/joint_estimation include 30 CSV trajectories, metrics.csv, summary.json, passive_comparison.png, control_comparison.png, and plus050_detail.png. All cases are retained. The literature matrix is LITERATURE_BASELINES.md; it distinguishes abstract-level checks from full-text checks and does not constitute a systematic novelty review.
