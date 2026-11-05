# Four persistent failures: convergence, contact traces and diversity baselines

Exploratory reuse of the previously inspected 96 test batches, not new independent confirmation. Fixed parameters, no tuning on these results. Cases 121,139,145,159, zero-based. Historical files preserved. Simplified model, no hardware evidence.

## Numerical audit

All 64 candidates at seven steps: .01,.005,.0025,.00125,.000625,.0003125,.00015625 seconds. Identical action and cost sampling. Last-two maximum cost difference concerns all candidates; stable winners alone do not establish convergence. Finest remains a discrete reference. Top8-set loss is unavoidable even after reranking the coarse shortlist with the finest model.
| Batch | Fine winner | Finest winner | Coarse rank | Finest top8-set loss | Last two max cost delta |
|---|---:|---:|---:|---:|---:|
| 121 | 49 | 49 | 19 | 0.240107 | 0.038801 |
| 139 | 36 | 36 | 11 | 0.136916 | 0.027287 |
| 145 | 54 | 54 | 17 | 0.270848 | 0.074497 |
| 159 | 10 | 10 | 10 | 0.019125 | 0.047949 |

Original fine winner, finest winner and original top-eight output were independently stepped at coarse/original-fine/finest resolution. Saved geometric contact-pair masks (bar/stem), normal forces, force-based onset/release times and integrated normal impulses. Direct-step states reproduce batched states. Raw trace_*.npz and contact_traces.json retain evidence. Contact times are quantized; changed contact sequences demonstrate numerical sensitivity, not unique causal attribution. No stiffness/friction intervention or physical validation.

## Ordinary baselines

top8/top16 retain the cheapest coarse candidates. dedup8 greedily retains candidates with action RMS distance >=.02 m/s and fills missing slots by cost. cluster8/cluster16 use action-space k-means (farthest initialization, <=20 iterations), cheapest coarse member per cluster, and cost-based fill. No true generator labels or fine costs are used. Parameters fixed before this run. Retained candidates are evaluated at .0025 seconds. All timing includes coarse evaluation, selection/clustering and fine refinement; three randomized repeats per batch (288 calls per method). Fine evaluates all 64 candidates.
| Method | Loss >1e-4 /96 | Mean regret | Max regret | p95 ms |
|---|---:|---:|---:|---:|
| fine | 0 | 0.000000 | 0.000000 | 13.74 |
| top8 | 5 | 0.007776 | 0.301907 | 6.28 |
| dedup8 | 14 | 0.013546 | 0.301907 | 6.85 |
| cluster8 | 16 | 0.012867 | 0.301907 | 7.29 |
| top16 | 2 | 0.005774 | 0.301907 | 8.02 |
| cluster16 | 14 | 0.015393 | 0.301907 | 9.58 |

```json
[
  {
    "method": "fine",
    "misses": 0,
    "mean_regret": 0.0,
    "max_regret": 0.0,
    "halfstep_losses": 10,
    "p95_ms": 13.738915038993582,
    "case_regrets": {
      "121": 0.0,
      "139": 0.0,
      "145": 0.0,
      "159": 0.0
    }
  },
  {
    "method": "top8",
    "misses": 5,
    "mean_regret": 0.007775735578072471,
    "max_regret": 0.301907017180191,
    "halfstep_losses": 13,
    "p95_ms": 6.276684952899813,
    "case_regrets": {
      "121": 0.301907017180191,
      "139": 0.14238990545554486,
      "145": 0.25238581774705215,
      "159": 0.016820984205953238
    }
  },
  {
    "method": "dedup8",
    "misses": 14,
    "mean_regret": 0.013545518500923873,
    "max_regret": 0.301907017180191,
    "halfstep_losses": 18,
    "p95_ms": 6.852359988261014,
    "case_regrets": {
      "121": 0.301907017180191,
      "139": 0.14238990545554486,
      "145": 0.0,
      "159": 0.05381919446779371
    }
  },
  {
    "method": "cluster8",
    "misses": 16,
    "mean_regret": 0.01286722088321197,
    "max_regret": 0.301907017180191,
    "halfstep_losses": 16,
    "p95_ms": 7.28987498441711,
    "case_regrets": {
      "121": 0.301907017180191,
      "139": 0.0,
      "145": 0.0,
      "159": 0.05381919446779371
    }
  },
  {
    "method": "top16",
    "misses": 2,
    "mean_regret": 0.005773883697158783,
    "max_regret": 0.301907017180191,
    "halfstep_losses": 12,
    "p95_ms": 8.022274967515841,
    "case_regrets": {
      "121": 0.301907017180191,
      "139": 0.0,
      "145": 0.25238581774705215,
      "159": 0.0
    }
  },
  {
    "method": "cluster16",
    "misses": 14,
    "mean_regret": 0.015392918094936795,
    "max_regret": 0.301907017180191,
    "halfstep_losses": 17,
    "p95_ms": 9.576290013501419,
    "case_regrets": {
      "121": 0.301907017180191,
      "139": 0.0,
      "145": 0.0,
      "159": 0.05381919446779371
    }
  }
]
```

The 1e-4 reporting threshold is not a physical task tolerance. Evaluate all 96 batches, not only repaired cases. Half-step losses also include fine-model ranking discrepancies. Run push_t_convergence_diversity.py run then report in .venv-contact; run refuses overwrite. Data under results/push_t_convergence_diversity. Assertions verify old four-resolution costs, direct-step traces, baseline reference costs and unique candidate IDs; audit.json records success. No certificate or novelty established.

## Evidence-supported mechanisms and decision

All four winners are stable from .005 seconds through every finer level. Finest coarse-top-eight set losses are .240107,.136916,.270848,.019125. Thus misses persist beyond the original .0025 reference. Last-two all-candidate maximum cost differences remain .027–.074: full cost convergence and certified error bounds are not established.

- 121: winner49 first force contact is .100s coarse versus .08969s finest; normal impulse .04253 versus .03963. Coarse rank19; all tested diversity methods and top16 fail. Contact integration/ranking discrepancy is supported, but no unique causal event is established.
- 139: winner36 onset .140 versus .11516s; impulse .01380 versus .01144. Original shortlist selects stationary candidate0. Cluster8 and top16 recover the winner.
- 145: coarse top-eight IDs [6,1,0,7,4,5,2,3] all belong to generator cluster0, while winner54 belongs to cluster6. Chosen candidate6 has no force contact; winner54 does, with coarse/finest impulses .02688/.01686. Dedup8, cluster8 and cluster16 recover it; top16 does not. This directly supports cross-cluster coverage failure. Generator labels are retrospective only.
- 159: coarse top-eight [13,11,8,9,12,15,14,27] already covers winner10's cluster1 but excludes10. Within-cluster coarse misranking remains. Winner onset .040 versus .03031s. Diversity baselines worsen original regret .01682 to .05382; top16 recovers the winner.

Transition counts can reflect sampling and force-threshold chatter, not additional physical events. No causal contact intervention was performed. These are localized selection mechanisms and numerical contact differences, not a complete causal proof.

Across 96 batches top8 has five losses, dedup8 fourteen, cluster8 sixteen, cluster16 fourteen. Ordinary top16 has two, p95 about8.02ms versus13.74ms all-fine. Fixed diversity baselines do not solve the aggregate problem; this does not invalidate all diversity methods. Top16 is a stronger simple baseline; remaining cases are121 and145.

Next use a newly frozen confirmation set for stronger ordinary strategies (top32 and rank/diversity mixtures), predefine task-level acceptable loss, and continue convergence checks. Do not claim novelty from diversity or infer that all existing approaches have been excluded.
