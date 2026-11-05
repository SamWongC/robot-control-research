# Contact-local refinement: end-to-end and matched-step comparisons

Exploratory reuse of256 previously inspected batches, not fresh confirmation. Rules frozen before execution; no fine-reference access.

Uniform low/medium/high steps=.0025/.00125/.000625. Contact-local runs all64 at low resolution, marks force-contact or endpoint gap<8mm plus neighboring stages, then reruns from the original initial state with high steps on marked stages and low elsewhere. Timing includes pilot, geometry, grouping and full rerun.

Spread-matched uses the same pilot and per-trajectory number of fine stages placed evenly in time. Uniform-matched uses the same pilot and20+3n substeps per control stage, where n is the number of marked stages. All three have exactly400+60n rerun steps plus400 pilot steps per trajectory. Equal steps are not equal wall time: grouping and contact work differ, so actual timings are recorded. Warmstart uniformly disabled to avoid missing internal state at stage boundaries.

Three randomized repeats per batch/method, all models prewarmed,4608 calls. Primary reference=.000625; case148 additionally checked against archived .0000390625 reference. Regret>1e-4 is numerical, not task tolerance or physical truth.
| Method | Loss /256 | Mean regret | p95 ms | Mean physics steps | Case148 winner | Case148 median ms |
|---|---:|---:|---:|---:|---:|---:|
| uniform_low | 27 | 0.009536 | 22.08 | 25600 | 5 | 15.63 |
| uniform_medium | 12 | 0.003661 | 43.95 | 51200 | 37 | 30.42 |
| uniform_high | 0 | 0.000000 | 87.09 | 102400 | 37 | 58.20 |
| contact_local | 2 | 0.000027 | 98.63 | 95056 | 37 | 69.44 |
| spread_matched | 14 | 0.001259 | 98.25 | 95056 | 37 | 69.34 |
| uniform_matched | 10 | 0.002061 | 134.51 | 95056 | 37 | 80.62 |

```json
{
  "methods": [
    {
      "method": "uniform_low",
      "losses": 27,
      "mean_regret": 0.009536406746682852,
      "max_regret": 1.0556425114458428,
      "p50_ms": 12.991649971809238,
      "p95_ms": 22.07945502595976,
      "mean_physics_steps": 25600.0,
      "case148_chosen": 5,
      "case148_regret": 1.0556425114458428,
      "case148_finest_regret": 1.0486802934739163,
      "case148_median_ms": 15.62510000076145
    },
    {
      "method": "uniform_medium",
      "losses": 12,
      "mean_regret": 0.0036610384031183054,
      "max_regret": 0.3671489039689053,
      "p50_ms": 24.733649974223226,
      "p95_ms": 43.95485498826019,
      "mean_physics_steps": 51200.0,
      "case148_chosen": 37,
      "case148_regret": 0.0,
      "case148_finest_regret": 0.0,
      "case148_median_ms": 30.41859995573759
    },
    {
      "method": "uniform_high",
      "losses": 0,
      "mean_regret": 0.0,
      "max_regret": 0.0,
      "p50_ms": 50.04324996843934,
      "p95_ms": 87.08992498577572,
      "mean_physics_steps": 102400.0,
      "case148_chosen": 37,
      "case148_regret": 0.0,
      "case148_finest_regret": 0.0,
      "case148_median_ms": 58.195099933072925
    },
    {
      "method": "contact_local",
      "losses": 2,
      "mean_regret": 2.700552271495257e-05,
      "max_regret": 0.005649408343887052,
      "p50_ms": 60.71299995528534,
      "p95_ms": 98.62952999537809,
      "mean_physics_steps": 95056.484375,
      "case148_chosen": 37,
      "case148_regret": 0.0,
      "case148_finest_regret": 0.0,
      "case148_median_ms": 69.44099999964237
    },
    {
      "method": "spread_matched",
      "losses": 14,
      "mean_regret": 0.00125898174461272,
      "max_regret": 0.12649561097327844,
      "p50_ms": 59.00219996692613,
      "p95_ms": 98.24963994324206,
      "mean_physics_steps": 95056.484375,
      "case148_chosen": 37,
      "case148_regret": 0.0,
      "case148_finest_regret": 0.0,
      "case148_median_ms": 69.34449996333569
    },
    {
      "method": "uniform_matched",
      "losses": 10,
      "mean_regret": 0.0020606477584067646,
      "max_regret": 0.17582656517675765,
      "p50_ms": 89.63999996194616,
      "p95_ms": 134.5137899799738,
      "mean_physics_steps": 95056.484375,
      "case148_chosen": 37,
      "case148_regret": 0.0,
      "case148_finest_regret": 0.0,
      "case148_median_ms": 80.62120003160089
    }
  ],
  "mean_fine_stage_fraction": 0.5710479736328125,
  "case148_fraction": 0.64140625
}
```

Code push_t_local_refinement.py run/report in .venv-contact. Data results/push_t_local_refinement. All-low/all-high stitched versus continuous states agree within1e-7; saved reference costs reproduce within1e-9; three adaptive methods have identical per-batch total steps. Historical outputs preserved.

Fixed implementations only; no universal rejection of adaptive refinement, safety certificate, closed-loop result or novelty claim. Inspected batches do not provide unbiased new-method generalization evidence.

## Measured conclusion

Case148: contact-local selects37, zero regret under the archived finest reference, but median69.44ms exceeds all-high58.20ms. Uniform medium also selects37 at30.42ms. Both matched-step comparators also recover37, so this case shows no unique advantage from contact localization.

Across256 batches contact-local has2 losses versus14 spread-matched and10 uniform-matched, supporting more useful compute placement on these inspected batches. However its p95 is98.63ms versus87.09ms all-high. Uniform medium takes43.95ms but has12 losses. No demonstrated joint achievement of full reference quality and lower total latency.

Fine-stage fraction averages57.10%,64.14% for148. Including the pilot, mean steps95056 versus102400 save only7.17%; case148 uses about100460, saving1.89%. Grouping, repeated calls and reintegration consume the limited savings. Compare timings within this run, not absolute milliseconds across prior runs.

Decision: retain the quality-allocation signal, but the two-pass prototype fails the speed gate; uniform medium already solves148. No standalone RA-L contribution is established. A bounded single-pass/contiguous-segment feasibility check could precede further work, retaining matched-budget and uniform baselines and a fresh frozen validation set. Do not replace end-to-end acceleration with step-count claims.
