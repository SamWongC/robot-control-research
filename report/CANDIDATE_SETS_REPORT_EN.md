# Experiment 6: Frozen Delay Candidate Sets on Held-out Data

Date: 2026-11-04. Offline non-learning identification; no MPC integration.

## Methods and Information

Nine candidates (0..8 steps), 20-transition window, dt=0.05 s. Each candidate profiles a free constant disturbance. No historical estimate is retained: each window selects its own optimum, with smallest-index tie breaking. OLS is centered residual sum of squares divided by differenced-noise variance. GLS profiles a constant using the exact tridiagonal covariance of differenced iid velocity noise. Velocity-noise SD is assumed accurately known from separate calibration; no true delay or disturbance enters scoring. Noise-scale misspecification remains untested.

all retains nine; point_ols/point_gls retain the window minimizer; set_ols/set_gls retain candidates within a calibrated score increment. geometry_abstain computes the minimum pairwise weighted, constant-profiled distance between shifted command candidates. Above its frozen threshold it returns the GLS point, otherwise all nine. Geometry uses commands and known noise only, never the true candidate. Set comparisons allow 1e-10 numerical tolerance.

## Split and Freeze

144 development replays use four inputs, zero/positive-constant/slow-sine disturbance, delays 2/6, velocity-noise SD 0.005/0.020 m/s and seeds 0..2. 480 held-out replays change input parameters/frequencies, use zero/negative-constant/faster-sine/new ramp disturbances, delays 1/4/7, SD 0.008/0.025 and seeds 100..104. Every replay has 400 transitions, evaluating 300 windows after transition k=100. Data are paired across methods; inputs are not energy matched. Both parameter splits are saved before calibration. Exact parameters are in split_manifest.json; development rules are frozen before the separate test invocation.

Score increments use the higher empirical 95th percentile of true-candidate minus minimum development score. The geometry threshold is chosen from erroneous development-point selections to target at least approximately 95% overall window coverage by abstaining to all candidates. Labels are used only during calibration/evaluation. frozen_rules.json binds thresholds to source and manifest hashes, checked before test. The 95% target is empirical, not a conditional, trajectory-level, or distribution-shift coverage guarantee. No threshold is reselected after test inspection.

## Results

| Method | Dev coverage | Test coverage | Mean size (test) | Singleton fraction | Singleton accuracy | Worst group coverage |
|---|---:|---:|---:|---:|---:|---:|
| all | 100.0% | 100.0% | 9.000 | 0.0% | N/A | 100.0% |
| point_ols | 40.1% | 43.4% | 1.000 | 100.0% | 43.4% | 0.0% |
| point_gls | 40.9% | 44.0% | 1.000 | 100.0% | 44.0% | 0.0% |
| set_ols | 95.0% | 96.3% | 5.174 | 34.1% | 91.2% | 77.7% |
| set_gls | 95.0% | 96.6% | 5.193 | 33.7% | 91.0% | 65.6% |
| geometry_abstain | 95.0% | 95.1% | 5.827 | 39.7% | 87.7% | 60.6% |


Singleton accuracy conditions on set size one. Coverage is the fraction of windows containing the true delay. Worst group averages within input/disturbance/noise strata over delays/seeds; worst-replay coverage is separately saved. Overlapping windows are not independent uncertainty samples. all obtains coverage by retaining all nine, not by identification.

## Limits and Reproduction

Known noise scale, exact plant model and fixed delay within each replay simplify this test. Varying disturbances violate the fitted constant model. Evaluate coverage and size jointly; good overall coverage can conceal group failures. If held-out coverage misses the target, diagnose model/noise mismatch before connecting sets to MPC. No safety or novelty claim follows.

Run the project .venv Python with `candidate_sets.py --phase development`, then `--phase test`. Existing frozen rules cannot be overwritten; use a new experiment directory for recalibration. `--phase render` regenerates reports/plots without rerunning data. results/candidate_sets contains per-replay compressed NPZ measurements, commands, scores and set bitmasks, *_metrics.csv metadata, and *_summary.csv/json. Reports default to report/. See candidate_sets_tests.log and requirements-lock.txt.

## Post-test Findings and Artifact Audit

Frozen set_ols reaches 96.3% overall test coverage with 5.174 candidates; set_gls reaches 96.6% with 5.193. Neither dominates across groups. GLS singleton accuracy is 91.0%; a singleton is not a validated certainty claim. The geometry rule also fails to maintain the nominal target in every group. The nominal overall target was met on this declared test suite, but group reliability was not. Do not connect these rules directly to a safety-critical controller. Next diagnose varying-disturbance mismatch and noise-scale sensitivity; retain this test as observed data and use a new held-out split for any revised rule. No recalibration was performed after this test.

| Rule | Worst input | Disturbance | Velocity noise SD | Group coverage |
|---|---|---|---:|---:|
| set_ols | sine | sine | 0.008 | 77.7% |
| set_gls | sine | sine | 0.008 | 65.6% |
| geometry_abstain | sine | sine | 0.025 | 60.6% |

All 624 NPZ replay files were checked against saved coverage and mean-size metrics for every method, and frozen source/manifest hashes were verified. Analysis is descriptive; windows overlap. The clean plot is coverage_size_clean.png. To regenerate this appendix after --phase render, run analyze_candidate_sets.py.
