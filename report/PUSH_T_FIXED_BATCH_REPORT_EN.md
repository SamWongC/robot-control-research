# Fixed candidate batches: Push-T-style contact-evaluation bottleneck

Date: 2026-11-04. A constructed minimal MuJoCo mechanism replication, not an exact Oxford GPC, standard Push-T or hardware-controller reproduction. All numbers below were measured locally.

## Outcome

Trajectory evaluation dominates this small workload, but the generic coarse-screen/top-8-fine method already improves latency without changing the winner on the eight held-out batches. Its total p95 reduction versus native eight-thread fine CPU is 51.3%. This is empirical finite-batch agreement, not a certificate or closed-loop success result. The contact-segment heuristic fails the speed gate. No independent RA-L novelty has been established.

## Frozen protocol

Sixteen snapshots: eight development and eight test, four contact regimes with two instances per split. Each batch contains 64 frozen velocity sequences (1024 distinct state/control pairs), 20 control intervals of 0.05s, horizon 1s. Fine/coarse steps are 0.0025/0.01s; an additional 0.00125s reference sensitivity check is retained. Costs are sampled at identical control-stage endpoints and use weighted position, yaw, effort and terminal terms.

The T object is two boxes, constrained to planar translation/yaw; the pusher is cylindrical. Joint damping/friction approximate planar drag. There is no full arm, obstacle, vision, or table-contact model. No obstacle-task conclusion follows. Candidate arrays and splits were frozen before evaluation. Top-8, geometric threshold and empirical development error were not tuned on test snapshots.

Each method/batch is timed three times. CPU method order is randomized; GPU runs are separate. Test p95 pools 24 calls, while eight scenarios are the independent units. These are descriptive timings, not inferential confidence intervals.

## Held-out results

| Method | p50 ms | p95 ms | Mean regret | Max regret | Same winner / 8 |
|---|---:|---:|---:|---:|---:|
| fine_serial | 86.13 | 95.88 | 0.000000 | 0.000000 | 8 |
| fine_cpu8 | 12.59 | 14.12 | 0.000000 | 0.000000 | 8 |
| coarse_cpu8 | 3.48 | 3.99 | 0.006620 | 0.052958 | 7 |
| coarse_top8 | 5.47 | 6.88 | 0.000000 | 0.000000 | 8 |
| coarse_empirical_interval | 14.40 | 18.17 | 0.000000 | 0.000000 | 8 |
| contact_segment | 22.14 | 24.07 | 0.000000 | 0.000000 | 8 |
| fixed_segment | 16.13 | 17.90 | 0.006991 | 0.055928 | 7 |
| cached_proposal | 1.46 | 1.75 | 0.013611 | 0.055928 | 6 |
| warp_fine | 182.54 | 238.16 | 0.013611 | 0.055928 | 6 |
| warp_coarse | 47.61 | 56.97 | 0.020784 | 0.113312 | 6 |


Regret is the chosen candidate's fine CPU-reference cost minus the best fine cost within that same batch. GPU decisions are also scored against this common reference; backend discrepancies are not hidden.

## Implemented methods

- fine_serial/fine_cpu8: native C++ MuJoCo rollout on one/eight threads, not a weak Python stepping baseline.
- coarse_cpu8: evaluate all candidates coarsely and select directly.
- coarse_top8: evaluate all coarsely, reevaluate the cheapest eight finely, then select among those eight. Both phases are timed.
- coarse_empirical_interval: use the largest development cost error as a heuristic interval halfwidth and refine possible competitors. This is NOT a verified or statistical bound; 2/512 test candidates exceed it.
- contact_segment: coarse contact/geometry screening, neighboring-stage dilation, then a mixed-step rerun. No fine-reference leakage. Dispatch, grouping and rerun costs are included. There is no certified enclosure.
- fixed_segment: alternate fine and coarse intervals.
- cached_proposal: offline costs at a state shifted by 3mm and 0.02rad, with identical candidate actions; choose its winner and finely evaluate just that proposal online. Offline build cost is excluded. This is not a complete cache-MPC baseline or an optimality/safety certificate.
- warp_fine/warp_coarse: RTX5070 Laptop, MuJoCo Warp, graph capture, warmup and synchronization. Timing includes reset, transfers, output and cost evaluation. Float32 and backend differences cause observed ranking/cost differences versus float64 CPU. This is a 64-world small-batch baseline, not evidence that GPU simulation is generally slower; large-batch and backend tuning were not performed.

## Bottleneck and event association

The median native rollout fraction of total fine-eight-thread time is 96.9%. It includes state recording; it is not all collision handling. An instrumented single trajectory gives collision/STEP approximately 24.6%. Timers overlap and a Python clock callback perturbs them, so this is not an aggregate workload share or a reproduction of Oxford's percentage. Rendering is excluded.

Reference contact-onset/release windows, dilated one stage each way, occupy on average 26.2% of candidate-stage pairs and contain 43.0% of positive state-error growth. This is retrospective association, not causal attribution or proof that refining only those windows suffices. State error uses normalization of 1m and 1rad. Fine event information was not used by online heuristics.

## Numerical audit and correction

The first stitching test exposed solver warmstart-state loss between native rollout calls. pilot_v0 preserves all initial code/results and the failing test. Final CPU/GPU models uniformly disable solver warmstart to isolate step-size effects. Frozen state/goal/control arrays are elementwise unchanged. All-fine stitched and continuous rollouts now agree, as do serial/parallel runs. This comparison does not establish superiority over a tuned warm-start solver.

Seven targeted tests cover direct mj_step replay, thread/stage consistency, geometry, frozen split, costs, contact records and saved GPU rankings. Compilation/warmup is excluded from steady-state measurements; first compilation logs remain in pilot_v0. Half-step sensitivity changes the winner in 0/8 test batches; the maximum candidate cost difference is 1.758619. Fine is therefore a defined discrete reference, not physical truth.

## Research decision

The requested fixed-batch experiment has CPU/GPU and heuristic comparisons. Tube/abstraction baselines, formal multifidelity BAI, closed-loop robot trials and sound cost enclosures are not implemented and are not labeled failures. The empirical-interval filter is only a simplified engineering comparator.

The next meaningful question is whether ordinary top-8 screening misses important candidates on separately frozen harder scenarios, and whether a cheap valid miss detector exists. If simple screening already meets the task needs, a more complicated contact-segment method has no demonstrated necessity. Do not add a network or claim novelty from these successful batches.

## Artifacts and reproduction

Code: push_t_fixed_batch.py, push_t_gpu_batch.py, analyze_push_t_fixed_batch.py, test_push_t_fixed_batch.py. Isolated .venv-contact and requirements-contact-lock.txt; historical environments remain unchanged. Frozen NPZ/XML, all reference states/contact labels/costs, raw timings, quality metrics, calibration, event diagnostics, logs and benchmark/scenes PNGs are under results/push_t_fixed_batch/.

Using the existing fixture, run `.venv-contact\Scripts\python.exe push_t_fixed_batch.py cpu`, then the GPU script and targeted unittest in that environment. Generate plots/reports using `.venv\Scripts\python.exe analyze_push_t_fixed_batch.py`. freeze refuses to overwrite existing fixtures; archive current results before rerunning evaluation if preservation is required.

Backend references: [native rollout](https://mujoco.readthedocs.io/en/stable/python.html), [MuJoCo Warp](https://mujoco.readthedocs.io/en/stable/mjwarp/index.html), [JAX platform support](https://docs.jax.dev/en/latest/installation.html). WSL is absent and native Windows NVIDIA JAX is unsupported; Warp supplies the GPU baseline.
