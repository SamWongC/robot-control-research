# Experiment map

Start with the final reports; earlier plans may be superseded. All named reports are under `report/`, with `.md` and usually `_EN.md`. Matching data directories are under `results/`.

| Theme | Main source | Report |
|---|---|---|
| Delay compensation | `experiment.py`, `delay_mismatch.py` | MINIMAL_EXPERIMENT_REPORT, DELAY_MISMATCH_REPORT |
| Delay/disturbance estimation | `disturbance_identification.py`, `joint_estimation.py`, `identifiability_experiment.py` | DISTURBANCE_IDENTIFICATION_REPORT, JOINT_ESTIMATION_REPORT, IDENTIFIABILITY_REPORT |
| Candidate consistency | `candidate_sets.py` | CANDIDATE_SETS_REPORT |
| Common delay controller reproduction | `reproduce_common_delay.py` | COMMON_DELAY_REPRODUCTION_REPORT |
| Task ambiguity / preview | `task_ambiguity_scenarios.py`, `preview_identification.py` | TASK_AMBIGUITY_SCENARIOS_REPORT, PREVIEW_IDENTIFICATION_REPORT |
| Baseline / first-action sensitivity | `baseline_sensitivity.py`, `first_action_scan.py` | BASELINE_SENSITIVITY_REPORT, FIRST_ACTION_SCAN_REPORT |
| Causal / partial-delay gates | `causal_preview_certificate.py`, `partial_delay_gate.py` | CAUSAL_PREVIEW_CERTIFICATE_REPORT, PARTIAL_DELAY_GATE_REPORT |
| Queue argument audit | `queue_merge_math_audit.py` | QUEUE_MERGE_FEASIBILITY_REVIEW |
| Fixed-batch pushing / GPU check | `push_t_fixed_batch.py`, `push_t_gpu_batch.py` | PUSH_T_FIXED_BATCH_REPORT |
| Stress / diversity | `push_t_screen_stress.py`, `push_t_convergence_diversity.py` | PUSH_T_SCREEN_STRESS_REPORT, PUSH_T_CONVERGENCE_DIVERSITY_REPORT |
| Frozen confirmation | `push_t_confirmation.py` | PUSH_T_CONFIRMATION_REPORT |
| Convergence audit | `push_t_batch148_audit.py` | PUSH_T_BATCH148_AUDIT_REPORT |
| Local refinement / execution | `push_t_local_refinement.py`, `push_t_execution_gate.py` | PUSH_T_LOCAL_REFINEMENT_REPORT, PUSH_T_EXECUTION_GATE_REPORT |
| Closed-loop meaning | `push_t_closed_loop_gate.py`, `push_t_closed_loop_bridge.py` | PUSH_T_CLOSED_LOOP_GATE_REPORT |

`results/push_t_fixed_batch/pilot_v0` is a failed early pilot, not the accepted reference. Common-delay reproduction is protocol-level, not the original authors' random data. GPU work did not establish matching CPU accuracy/performance. Saved execution snapshots intentionally differ from some current report-generating sources.
