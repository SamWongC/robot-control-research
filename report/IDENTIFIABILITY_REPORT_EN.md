# Experiment 5: Identifiability, Excitation and Measurement Noise

Date: 2026-11-04. Passive open-loop mechanism study; no controller, learning or novelty claim.

## Protocol

Four commands, applied for 20 s at dt=0.05 s: constant 0.5; ramp -0.6+0.06*t; sine 0.8*sin(2*pi*0.7*t); multisine 0.4*sin(2*pi*0.35*t)+0.3*sin(2*pi*1.1*t)+0.2*sin(2*pi*1.7*t). They are NOT energy matched. True input delay is six steps, initial pending commands zero. Known double-integrator plant, initial state zero. Disturbance acts throughout: zero, constant +0.5, or 0.5*sin(2*pi*0.1*t) m/s². These are identification probes, not position-limited robot tasks.

Independent Gaussian velocity measurement noise has SD 0, 0.005 or 0.02 m/s. Both estimators receive exactly the same state measurements and sent commands in each replay. Position is exact and unused by identification. Acceleration is obtained by velocity differencing: its noise SD is sqrt(2)*sigma/0.05 and consecutive differences have correlated errors. One noiseless run and ten fixed seeds per noisy condition give 252 replays. Common noise samples are used across scenarios at a given seed and SD. Seed SD measures measurement-noise variation, not training or task variation.

Raw and constant-bias-profiled estimators are unchanged from Experiment 4 (20-transition window, zero initial estimate, warm-up, tie retention). Each output is logged AFTER observing transition k at time (k+1)*dt, available for a future action; no future measurement is used. Evaluation uses completed transitions k=100..399 (availability times 5.05..20 s), excluding startup. Scores, biases and all nine candidates are saved. Disturbance error compares the selected bias with the last completed transition's true disturbance.

## Structural Diagnostic

For each window, form the shifted command sequence for every candidate. Compare each with the TRUE candidate after removing their mean difference; take the smallest mean squared difference. This oracle separation is evaluation-only, never supplied to the estimator. Zero means another candidate is exactly equivalent under a free constant disturbance in that window. Constant input and a linear ramp both have zero separation after startup: shifting a ramp changes its intercept, which the disturbance estimate absorbs. Nonzero separation distinguishes candidates only in the noiseless constant-disturbance model; it is not a general identifiability theorem for unknown varying disturbances.

## Noiseless Results

| Input | Disturbance | Raw accuracy | Joint accuracy | Zero-separation fraction |
|---|---|---:|---:|---:|
| constant | zero | 100.0% | 100.0% | 100.0% |
| constant | constant | 0.0% | 100.0% | 100.0% |
| constant | slow_sine | 100.0% | 100.0% | 100.0% |
| ramp | zero | 100.0% | 100.0% | 100.0% |
| ramp | constant | 0.0% | 100.0% | 100.0% |
| ramp | slow_sine | 0.0% | 100.0% | 100.0% |
| sine | zero | 100.0% | 100.0% | 0.0% |
| sine | constant | 19.3% | 100.0% | 0.0% |
| sine | slow_sine | 26.0% | 70.0% | 0.0% |
| multisine | zero | 100.0% | 100.0% | 0.0% |
| multisine | constant | 22.0% | 100.0% | 0.0% |
| multisine | slow_sine | 44.3% | 86.0% | 0.0% |

Correct retained estimates during zero separation reflect startup memory and the tie rule, not fresh identification. Failed estimates under uninformative input cannot simply be fixed by a larger network.

## Noise Sensitivity

| Input | Disturbance | Velocity noise SD | Joint accuracy mean | Across-seed SD |
|---|---|---:|---:|---:|
| constant | zero | 0.005 | 100.0% | 0.0000 |
| constant | zero | 0.02 | 40.0% | 0.5164 |
| constant | constant | 0.005 | 100.0% | 0.0000 |
| constant | constant | 0.02 | 40.0% | 0.5164 |
| constant | slow_sine | 0.005 | 60.0% | 0.5164 |
| constant | slow_sine | 0.02 | 30.0% | 0.4830 |
| ramp | zero | 0.005 | 100.0% | 0.0000 |
| ramp | zero | 0.02 | 20.0% | 0.4216 |
| ramp | constant | 0.005 | 100.0% | 0.0000 |
| ramp | constant | 0.02 | 20.0% | 0.4216 |
| ramp | slow_sine | 0.005 | 90.0% | 0.3162 |
| ramp | slow_sine | 0.02 | 20.0% | 0.4216 |
| sine | zero | 0.005 | 100.0% | 0.0011 |
| sine | zero | 0.02 | 78.4% | 0.0255 |
| sine | constant | 0.005 | 100.0% | 0.0011 |
| sine | constant | 0.02 | 78.4% | 0.0255 |
| sine | slow_sine | 0.005 | 71.7% | 0.0213 |
| sine | slow_sine | 0.02 | 60.1% | 0.0331 |
| multisine | zero | 0.005 | 99.4% | 0.0047 |
| multisine | zero | 0.02 | 71.4% | 0.0546 |
| multisine | constant | 0.005 | 99.4% | 0.0047 |
| multisine | constant | 0.02 | 71.4% | 0.0546 |
| multisine | slow_sine | 0.005 | 86.6% | 0.0152 |
| multisine | slow_sine | 0.02 | 63.7% | 0.0472 |

No confidence intervals are inferred by treating overlapping windows as independent. The best/second-best score gap is uncalibrated. gap_diagnostic.png and per-run top-quartile-gap accuracy are descriptive; thresholds were not trained or validated for deployment. A varying disturbance can select the wrong candidate with a nonzero score gap.

## Main Findings

Both constant and ramp inputs show 100% retained joint-estimator accuracy without noise, yet zero oracle separation in every evaluated window. Startup padding/turn-on provides initial information; the subsequent correct tie-retained value is not re-identification. For zero disturbance and velocity-noise SD 0.02 m/s, mean accuracy is 78.4% for sine and 71.4% for multisine. Under slow varying disturbance without noise it is 70.0% and 86.0%, respectively. Thus varying input alone neither guarantees rejection of varying disturbance nor noise robustness. No universal waveform ranking is supported.

## Verification, Files and Next Step

Run `.\.venv\Scripts\python.exe -m unittest -v`, then `.\.venv\Scripts\python.exe identifiability_experiment.py`. Requirements remain requirements-lock.txt. Results in results/identifiability: 252 replay CSVs, metrics.csv, aggregated.csv, summary.json with formulas/configuration references and code hashes, four PNGs. Tests verify ramp/constant ambiguity, distinguishability of multisine input, exact noiseless prediction and paired deterministic noise. Tests also verify a mean-cancelling bias fit. Signals and test conditions were predeclared, not optimized after inspecting outcomes. No state safety or stability claim is made.

Next: formalize the constant-disturbance equivalence condition, investigate noise-aware residual scoring and varying-disturbance models, and evaluate calibrated candidate sets on genuinely held-out data before allowing confidence to influence control. Literature status is documented in LITERATURE_IDENTIFIABILITY_NOTES.md; earlier claims of novelty remain unverified.
