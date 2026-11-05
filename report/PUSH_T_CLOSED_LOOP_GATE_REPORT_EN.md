# Closed-loop task-meaning gate — 2026-11-05

## Protocol and scope
Development high-resolution successes: 13/16; predeclared gate >=12. Confirmation uses 64 new episodes, 16 per family, all frozen before development; these are new initial conditions, not new task families. Receding horizon: 64 proposals, 1 second horizon, first 50ms action executed, then replan. The identical generator mixes zero, shifted previous winner, goal-directed proposals and smooth random perturbations; common episode/time random seeds, but proposals evolve with each method's own state and warm start. No future reference states are used. This tests this particular controller, not an Oxford or standard Push-T reproduction.

Low/medium/high prediction steps .0025/.00125/.000625s. Top32 screens all64 at .01s, evaluates retained32 at .000625s. Execution step .0003125s; four development episodes additionally use .00015625s. Success: position <=2cm AND wrapped yaw <=10 degrees for 10 consecutive samples (0.5s); timeout10s; exit if object or pusher XY exceeds +/-0.5m. Perfect state sensing, simplified planar drag, no obstacles or robot arm. Success is a pose criterion without an additional velocity threshold.

Planning is idealized as instantaneous for control. Measured wall time includes proposal generation, rollout, selection and copying selected sequence; excludes simulation execution, file IO and startup. One run per method/episode, randomized method order within each episode; latency samples are correlated. Percentiles pool planning calls (longer episodes contribute more); not repeated independent hardware benchmarks. No delay-injected or real-time success claim.

## Results
| Method | Success /64 | Escape | Mean final error (m) | Mean elapsed (s)* | p95 ms | p99 ms | >50ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| low | 57 | 0 | 0.0093 | 3.328 | 18.76 | 20.75 | 0.0% |
| medium | 55 | 0 | 0.0103 | 3.410 | 36.09 | 41.75 | 0.3% |
| high | 54 | 0 | 0.0119 | 3.352 | 73.03 | 94.00 | 86.1% |
| top32 | 55 | 0 | 0.0090 | 3.320 | 40.40 | 44.14 | 0.2% |

| Method | Approach /16 | Near contact /16 | Stem /16 | Corner /16 |
|---|---:|---:|---:|---:|
| low | 16 | 16 | 16 | 9 |
| medium | 16 | 15 | 16 | 8 |
| high | 16 | 16 | 16 | 6 |
| top32 | 16 | 16 | 16 | 7 |

| Method vs high | Only method succeeds | Only high succeeds | Success difference | Bootstrap 95% | First action differs /64 |
|---|---:|---:|---:|---|---:|
| low | 4 | 1 | 4.7% | [-0.015625, 0.109375] | 1 |
| medium | 3 | 2 | 1.6% | [-0.046875, 0.078125] | 1 |
| top32 | 1 | 0 | 1.6% | [0.0, 0.046875] | 0 |

| Case | Success base / half-step | Final error base / half-step (m) | Duration base / half-step (s) |
|---|---|---|---|
| 0 | True / True | 0.0004 / 0.0004 | 1.50 / 1.50 |
| 12 | False / False | 0.0497 / 0.0953 | 10.00 / 10.00 |
| 4 | True / True | 0.0004 / 0.0004 | 1.45 / 1.45 |
| 8 | True / True | 0.0007 / 0.0036 | 1.90 / 1.65 |

*Elapsed time is observed termination time, capped at10s; not successful-completion time for failures. End errors are measured at each method's own stopping time. Bootstrap uses10000 paired episode resamples stratified by family; descriptive uncertainty, not broad generalization or multiple-comparison-adjusted inference. First-action differences compare identical initial states and proposals; later proposals are not identical after closed-loop divergence.

## Interpretation limits
Fine prediction is a baseline, not a guaranteed winning controller or physical ground truth. The execution sensitivity check covers four development cases only and cannot certify all confirmation outcomes. Any difference is conditional on candidate sampling, this objective, success tolerance and simplified model. Ranking reversals alone do not establish a publishable contribution. Do not tune on this confirmation set and relabel it unseen.

All 276 saved episode trajectories passed the post-run checks listed in audit.json. Source snapshots, model, frozen cases, per-episode traces and raw latencies are in results/push_t_closed_loop_gate. Numerical experiment only; no new literature/novelty audit performed.


## Exploratory sensitivity / 探索性敏感性检查

Archived148 uses its original64 proposals only at the first decision; subsequent decisions use the new rolling controller. This is not a pure first-action intervention because later methods differ too. / 旧148仅首轮使用原64候选，随后使用新闭环控制器；后续方法也不同，因此不是只改变首动作的因果干预。

| Execution step | Method | First choice | Success | Duration s | Final error m |
|---|---|---:|---|---:|---:|
| 0.0003125 | low | 5 | False | 10.00 | 0.0298 |
| 0.0003125 | medium | 37 | False | 10.00 | 0.0312 |
| 0.0003125 | high | 37 | True | 3.90 | 0.0173 |
| 0.0003125 | top32 | 5 | False | 10.00 | 0.0397 |
| 0.00015625 | low | 5 | False | 10.00 | 0.0203 |
| 0.00015625 | medium | 37 | False | 10.00 | 0.0347 |
| 0.00015625 | high | 37 | True | 9.55 | 0.0021 |
| 0.00015625 | top32 | 5 | True | 9.05 | 0.0016 |

Post-hoc half-step checks use the first eight (or fewer) disagreement IDs; selection is outcome-dependent, not a new test set. / 事后取最多8个成功标签不一致的任务复查，按编号选取；不是新确认集。

| Case | Method | Success base / half | Error base / half (m) |
|---|---|---|---|
| 47 | high | True / True | 0.0184 / 0.0049 |
| 47 | low | True / True | 0.0185 / 0.0039 |
| 47 | medium | False / True | 0.0185 / 0.0041 |
| 47 | top32 | True / True | 0.0184 / 0.0049 |
| 65 | high | False / False | 0.1040 / 0.1033 |
| 65 | low | True / False | 0.0080 / 0.1033 |
| 65 | medium | True / False | 0.0017 / 0.1033 |
| 65 | top32 | True / False | 0.0072 / 0.1033 |
| 68 | high | False / False | 0.0048 / 0.0332 |
| 68 | low | False / False | 0.0893 / 0.1085 |
| 68 | medium | True / False | 0.0026 / 0.0372 |
| 68 | top32 | False / False | 0.0125 / 0.0969 |
| 70 | high | True / False | 0.0021 / 0.0586 |
| 70 | low | True / True | 0.0005 / 0.0004 |
| 70 | medium | False / True | 0.0461 / 0.0180 |
| 70 | top32 | True / False | 0.0021 / 0.0590 |
| 71 | high | False / False | 0.0280 / 0.0306 |
| 71 | low | False / True | 0.0294 / 0.0166 |
| 71 | medium | True / False | 0.0124 / 0.0267 |
| 71 | top32 | False / False | 0.0233 / 0.0306 |
| 73 | high | False / False | 0.0718 / 0.0690 |
| 73 | low | True / False | 0.0037 / 0.0532 |
| 73 | medium | False / True | 0.0706 / 0.0030 |
| 73 | top32 | False / False | 0.0705 / 0.0690 |
| 77 | high | False / True | 0.1059 / 0.0073 |
| 77 | low | True / True | 0.0141 / 0.0021 |
| 77 | medium | False / False | 0.1009 / 0.1163 |
| 77 | top32 | False / True | 0.0124 / 0.0035 |
| 78 | high | True / True | 0.0079 / 0.0001 |
| 78 | low | False / False | 0.0723 / 0.0722 |
| 78 | medium | True / False | 0.0143 / 0.0709 |
| 78 | top32 | True / True | 0.0079 / 0.0001 |

Label flips after halving execution step / 执行步长减半后的标签变化：15/32. Additional trajectories audited / 额外审计轨迹：40.


## Research decision
This confirmation set does not support improving task success merely by refining prediction integration, or restarting the contact-local acceleration paper. Success counts are57/55/54/55 for low/medium/high/top32. The low-minus-high paired interval includes zero; low is not established as universally superior. High p95 exceeds the50ms period and delay was not injected, so idealized success is not a deployment result.

Archived148 has controller-dependent outcome differences, but later replanning and warm starts also change; this does not isolate the causal effect of its first ranking reversal. Top32 changes from failure to success after halving execution step. Selected confirmation discrepancies must also be interpreted with their sensitivity results.

Pause algorithm work motivated by ranking repair alone. Further work requires a meaningful task/controller bottleneck and model validation. Most initial actions coincide in these ordinary tasks; they are not a newly frozen distribution of specifically difficult ranking cases. The experiment does not prove that replanning always removes ranking errors, establish novelty, or validate a real robot.
