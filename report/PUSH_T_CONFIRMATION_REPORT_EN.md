# Fresh confirmation: top16, top32 and rank/diversity mixtures

Seed2026110403, 256 batches (64 per family, 64 candidates each), methods, threshold and source hashes frozen before execution. Exact previous generator distribution with new seed/count. New-sample confirmation, not a new task or hardware generalization; no outcome-driven tuning.

Hybrid16/32 retain coarse top8/16 and fill to16/32 by farthest minimum action-RMS distance within coarse top32/64. No fine truth or generator labels. Fine evaluates all64; top8 provides context. Online fine/coarse steps .0025/.01; offline all-candidate audit .000625.

Three randomized repetitions per method/batch, 4608 timed calls including coarse evaluation, selection and refinement. Warmup/reference construction excluded. Descriptive p95. Regret >1e-4 is a numerical reporting threshold, not a task tolerance. Finer-reference set loss remains even after ideal finer reranking within the retained subset. Actual output audit losses, including fine-model misranking, are separately in summary.json.
| Method | Loss /256 | Max regret | Mean regret | p95 ms | Finer-reference set loss /256 |
|---|---:|---:|---:|---:|---:|
| fine | 0 | 0.000000 | 0.000000 | 13.86 | 0 |
| top8 | 5 | 0.300943 | 0.002549 | 6.39 | 8 |
| top16 | 1 | 0.020482 | 0.000080 | 8.07 | 3 |
| top32 | 0 | 0.000000 | 0.000000 | 11.30 | 1 |
| hybrid16 | 4 | 0.182756 | 0.001373 | 8.44 | 5 |
| hybrid32 | 1 | 0.020482 | 0.000080 | 12.68 | 2 |

```json
{
  "methods": [
    {
      "method": "fine",
      "losses": 0,
      "max_regret": 0.0,
      "mean_regret": 0.0,
      "audit_output_losses": 27,
      "audit_set_losses": 0,
      "p95_ms": 13.859854987822473,
      "family_losses": {
        "grazing": 0,
        "reversal": 0,
        "near_duplicate": 0,
        "fast_corner": 0
      }
    },
    {
      "method": "top8",
      "losses": 5,
      "max_regret": 0.3009426802927089,
      "mean_regret": 0.002548899944309289,
      "audit_output_losses": 30,
      "audit_set_losses": 8,
      "p95_ms": 6.388625060208142,
      "family_losses": {
        "grazing": 1,
        "reversal": 2,
        "near_duplicate": 1,
        "fast_corner": 1
      }
    },
    {
      "method": "top16",
      "losses": 1,
      "max_regret": 0.02048235969895118,
      "mean_regret": 8.000921757402805e-05,
      "audit_output_losses": 28,
      "audit_set_losses": 3,
      "p95_ms": 8.068085083505139,
      "family_losses": {
        "grazing": 1,
        "reversal": 0,
        "near_duplicate": 0,
        "fast_corner": 0
      }
    },
    {
      "method": "top32",
      "losses": 0,
      "max_regret": 0.0,
      "mean_regret": 0.0,
      "audit_output_losses": 27,
      "audit_set_losses": 1,
      "p95_ms": 11.298790044384077,
      "family_losses": {
        "grazing": 0,
        "reversal": 0,
        "near_duplicate": 0,
        "fast_corner": 0
      }
    },
    {
      "method": "hybrid16",
      "losses": 4,
      "max_regret": 0.18275643563420263,
      "mean_regret": 0.001373342599415895,
      "audit_output_losses": 29,
      "audit_set_losses": 5,
      "p95_ms": 8.438949921401218,
      "family_losses": {
        "grazing": 1,
        "reversal": 1,
        "near_duplicate": 1,
        "fast_corner": 1
      }
    },
    {
      "method": "hybrid32",
      "losses": 1,
      "max_regret": 0.02048235969895118,
      "mean_regret": 8.000921757402805e-05,
      "audit_output_losses": 28,
      "audit_set_losses": 2,
      "p95_ms": 12.678264954593033,
      "family_losses": {
        "grazing": 1,
        "reversal": 0,
        "near_duplicate": 0,
        "fast_corner": 0
      }
    }
  ],
  "reference_winner_changes": 27,
  "zero_loss_one_sided_95_upper": 0.011633876163163248
}
```

Zero observed losses does not establish reliability. Under iid Bernoulli assumptions, zero/256 gives a one-sided95% upper failure-rate bound about1.16%; stratified fixed families and synthetic scope limit extrapolation. Reference winner changes preclude treating the fine model as physical truth.

Artifacts under results/push_t_confirmation; code push_t_confirmation.py, .venv-contact, freeze/run/report. Main outputs refuse overwrite. Assertions check finite costs, selected cost reproduction, unique IDs and recomputed regret. Historical results preserved. No certificate or novelty established.

## Confirmation decision

Against the original .0025 reference, top32 selects the identical winner on all256 batches, p95 11.30ms versus13.86ms all-fine (about18.5% reduction). Top16 has one loss at8.07ms. Hybrid16 has four losses and hybrid32 one, both slower than plain ranking at equal budget. This does not support action diversity as a necessary contribution or a standalone RA-L claim built on this generic combination.

Important counterevidence: the .000625 audit changes27/256 winners, and even all-fine .0025 outputs incur27 audit losses. Reference-model error is distinct from shortlist loss. Top32 has one audit set miss: zero-based batch148 (near_duplicate), audit winner37 ranks43 coarsely; top32 and original all-fine choose5, with audit regret1.055643. Zero original-reference failures therefore do not imply general reliability. Audit resolution itself is not proven converged or physical truth.

The sole original-reference top16 failure is batch0 (grazing): winner52 at coarse rank20, original regret.020482, audit regret.018737. Earlier small-sample zero failures for grazing did not establish family-level safety.

Decision: pause rank/diversity mixtures as the main novelty. Retain one bounded diagnostic: finer-step, solver/contact-setting and trajectory audit of batch148 to assess whether the large ranking reversal is stable. If it is reference/model instability, repair the benchmark first. If stable, investigate inexpensive detection of coarse cost bias against top32 and equal-budget simple baselines. Existing multifidelity methods remain unexcluded; no novelty is established.

Do not tune on this confirmation set and relabel success as confirmation. New methods require a new frozen set. The1e-4 threshold is numerical; closed-loop acceptable loss, deadlines and safety requirements remain undefined, so real-task significance cannot yet be claimed.
