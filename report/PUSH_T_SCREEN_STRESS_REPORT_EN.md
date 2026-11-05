# Independent stress batches: screening misses and inexpensive alarms

New frozen experiment: 192 batches of 64 candidates, 96 development and 96 held-out test, 24 per family per split. Same simplified planar MuJoCo model, objective and one-second horizon; no obstacles or hardware. Families are grazing, reversal, near-duplicate action clusters, and fast corner pushing. These are hypothesized mechanisms, not causal conclusions. Near-duplicate candidates comprise eight clusters of eight actions.

Fine/coarse/medium/audit steps: 0.0025/0.01/0.005/0.00125 seconds. Exact miss means the fine winner lies outside the coarse top eight. Regret > 1e-4 is a fixed numerical reporting tolerance, not a task-level tolerance. No test tuning or resampling of failures.

The coarse-margin alarm triggers when the ninth-to-first coarse cost gap is below the maximum such gap among development batches with regret > 1e-4 (disabled if none). Its fallback latency is not implemented. The medium-disagreement alarm reevaluates all candidates at medium resolution and triggers if its winner lies outside the coarse top eight. On alarm it evaluates all candidates finely; otherwise it refines only eight. Reported medium_alarm latency includes all stages and fallback. It uses no reference labels for decisions.

| Family | Test batches | Exact misses | Regret > 1e-4 | Max regret | Worst coarse rank |
|---|---:|---:|---:|---:|---:|
| fast_corner | 24 | 0 | 0 | 0.000000 | 8 |
| grazing | 24 | 0 | 0 | 0.000000 | 2 |
| near_duplicate | 24 | 2 | 2 | 0.252386 | 17 |
| reversal | 24 | 3 | 3 | 0.301907 | 19 |

```json
{
  "development_meaningful_misses": 4,
  "margin_threshold": 0.30325799200924397,
  "test_families": {
    "fast_corner": {
      "batches": 24,
      "exact_misses": 0,
      "meaningful_misses": 0,
      "max_regret": 0.0,
      "max_rank": 8
    },
    "grazing": {
      "batches": 24,
      "exact_misses": 0,
      "meaningful_misses": 0,
      "max_regret": 0.0,
      "max_rank": 2
    },
    "near_duplicate": {
      "batches": 24,
      "exact_misses": 2,
      "meaningful_misses": 2,
      "max_regret": 0.25238581774705215,
      "max_rank": 17
    },
    "reversal": {
      "batches": 24,
      "exact_misses": 3,
      "meaningful_misses": 3,
      "max_regret": 0.301907017180191,
      "max_rank": 19
    }
  },
  "detectors": {
    "coarse_margin": {
      "tp": 3,
      "fp": 26,
      "fn": 2,
      "tn": 65,
      "alarms": 29,
      "recall": 0.6,
      "remaining_max_regret": 0.301907017180191
    },
    "medium_disagreement": {
      "tp": 4,
      "fp": 1,
      "fn": 1,
      "tn": 90,
      "alarms": 5,
      "recall": 0.8,
      "remaining_max_regret": 0.03296689090621596
    }
  },
  "p95_ms": {
    "fine": 13.637645001290366,
    "top8": 6.109704996924847,
    "medium_alarm": 18.10411500046014
  },
  "halfstep_best_changes": 10,
  "misses_persist_halfstep": 4
}
```

TP/FN refer to detected/missed regret > 1e-4; FP means alarm without such regret. Low missed alarms alone is insufficient: false alarms and total latency also matter. Zero observed misses does not certify general reliability. Coarse and medium models may agree while both are wrong; cost margins do not bound model error.

halfstep_best_changes reports reference sensitivity; misses_persist_halfstep counts fine-regret failures that remain under the finer audit reference. No physical-truth, closed-loop, tube/abstraction failure or novelty claim follows.

All frozen inputs, four-resolution costs, raw timings, protocol and numerical audit are in results/push_t_screen_stress. Run push_t_screen_stress.py freeze, run, analyze in .venv-contact; freeze refuses overwrite. Three repeats per method per batch, 288 test calls per method; descriptive p95, not confidence intervals. Historical results are preserved.

## Measured decision

Five of 96 test batches miss the fine winner: reversal 3/24 and near-duplicate 2/24; grazing and fast-corner each 0/24, not universal safety. Worst coarse rank is 19. Zero-based batch 121 has winner 49 at coarse rank 19, regret 0.301907, persisting at 0.416679 with the half step. Batch 145 has coarse rank 17 for the fine winner and a coarse margin about 6.39e-6.

Margin alarm detects 3/5, misses 2/5 and raises 26 false alarms. Medium alarm detects 4/5, misses 1/5 and raises one false alarm. Its fallback-inclusive p95 is 18.10ms versus 13.64ms all-fine and 6.11ms top-eight. No detector is demonstrated to be both reliable and cheap here.

The finer step changes 10/96 winners. Four of five failures persist; the sole medium-alarm false negative (batch 138) disappears under the finer reference. It is not a stable physical counterexample. Catching all four persistent failures does not establish general reliability.

Next prioritize numerical convergence/contact-event audits of the four persistent failures and a standard candidate deduplication/cluster-diversity baseline. Do not claim an original certified method or RA-L contribution before these checks.
