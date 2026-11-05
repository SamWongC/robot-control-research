# Single-pass and contiguous-run execution gate (2026-11-05)

Every fourth existing confirmation batch:64 total,16 per family, including148. Bounded implementation check, not fresh confirmation. Three randomized repeats per method/batch; all necessary pilot, selection, grouping and integration costs included. Loss threshold1e-4 is numerical; reference uses uniform .000625s.

Stage-two-pass is the previous implementation. Contiguous merges adjacent same-resolution stages per trajectory, batching identical start/end/resolution groups. Prefix-reuse additionally copies pilot states preceding the first fine stage; never reuses stale states after refinement. Both still require a pilot. All three reproduce historical same-mask costs within1e-8.

Online-one-pass has no pilot: current gap<8mm+50ms*(pusher speed+object translational speed+current command speed), or previous-stage contact, triggers fine resolution. Speeds are vector norms; no sound angular-motion bound or safety guarantee. It eliminates pilot reintegration, retains per-stage dispatch, and changes refinement locations, so output equivalence is not assumed.

Uniform medium/high steps=.00125/.000625; local low=.0025. Warmstart uniformly disabled, same control boundaries.
| Method | Loss /64 | p50 ms | p95 ms | Mean calls | Mean steps | Case148 winner |
|---|---:|---:|---:|---:|---:|---:|
| stage_two_pass | 0 | 58.84 | 72.14 | 40.5 | 94872 | 37 |
| contiguous | 0 | 110.19 | 154.59 | 52.2 | 94872 | 37 |
| prefix_reuse | 0 | 108.90 | 151.44 | 49.4 | 93671 | 37 |
| online_one_pass | 0 | 51.08 | 61.29 | 36.3 | 81114 | 37 |
| uniform_medium | 4 | 24.01 | 27.70 | 1.0 | 51200 | 37 |
| uniform_high | 0 | 48.15 | 54.63 | 1.0 | 102400 | 37 |

```json
[
  {
    "method": "stage_two_pass",
    "losses": 0,
    "max_regret": 0.0,
    "mean_regret": 0.0,
    "p50_ms": 58.84479993255809,
    "p95_ms": 72.13712000520898,
    "mean_calls": 40.453125,
    "mean_steps": 94871.5625,
    "case148_winner": 37,
    "case148_ms": 67.06959998700768
  },
  {
    "method": "contiguous",
    "losses": 0,
    "max_regret": 0.0,
    "mean_regret": 0.0,
    "p50_ms": 110.19110004417598,
    "p95_ms": 154.58711996325292,
    "mean_calls": 52.21875,
    "mean_steps": 94871.5625,
    "case148_winner": 37,
    "case148_ms": 82.54329999908805
  },
  {
    "method": "prefix_reuse",
    "losses": 0,
    "max_regret": 0.0,
    "mean_regret": 0.0,
    "p50_ms": 108.9032999589108,
    "p95_ms": 151.43822497338988,
    "mean_calls": 49.375,
    "mean_steps": 93670.625,
    "case148_winner": 37,
    "case148_ms": 80.95000009052455
  },
  {
    "method": "online_one_pass",
    "losses": 0,
    "max_regret": 0.0,
    "mean_regret": 0.0,
    "p50_ms": 51.08269996708259,
    "p95_ms": 61.28651998587884,
    "mean_calls": 36.265625,
    "mean_steps": 81114.0625,
    "case148_winner": 37,
    "case148_ms": 56.13320006523281
  },
  {
    "method": "uniform_medium",
    "losses": 4,
    "max_regret": 0.1297107939525759,
    "mean_regret": 0.005187424853551106,
    "p50_ms": 24.012550013139844,
    "p95_ms": 27.70167005364783,
    "mean_calls": 1.0,
    "mean_steps": 51200.0,
    "case148_winner": 37,
    "case148_ms": 26.802299893461168
  },
  {
    "method": "uniform_high",
    "losses": 0,
    "max_regret": 0.0,
    "mean_regret": 0.0,
    "p50_ms": 48.14745002659038,
    "p95_ms": 54.633055021986365,
    "mean_calls": 1.0,
    "mean_steps": 102400.0,
    "case148_winner": 37,
    "case148_ms": 53.197499946691096
  }
]
```

Artifacts results/push_t_execution_gate; push_t_execution_gate.py run/report in .venv-contact. Run refuses overwrite. Saved costs,masks,timings,calls,steps,protocol,audit. No hardware,closed-loop safety or novelty evidence.

## Go/no-go decision

Single-pass removes the pilot: mean81114 steps versus102400 all-fine,20.8% fewer. Its p95 improves from72.14ms two-pass to61.29ms, but remains12.2% slower than all-fine54.63ms; median is slower too. Zero selection loss on64 inspected batches is not full256-batch or independent validation.

Contiguous grouping increases calls from40.5 to52.2 with unchanged steps; p95 worsens to154.59ms. Different trajectory switch boundaries create additional small batches in this scheduler. This rejects this implementation, not every possible native implementation. Prefix reuse only reaches49.4 calls,93671 steps and151.44ms p95.

All methods recover37 on148: uniform medium26.80ms, single-pass56.13ms, all-fine53.20ms. Thus148 does not establish necessity for the more complex implementation. Medium still loses on4/64 batches, but the present methods do not establish a superior end-to-end tradeoff.

Recommendation: pause further algorithms/networks/paper framing around this Python-scheduled contact-adaptive integration route. Evidence supports fewer steps and finite-sample ranking agreement, not latency advantage, guarantees or standalone novelty. Native batched kernels could be a separate engineering project if resources become available, not an investment justified by this gate. Preserve negative results and counterexamples; reassess real-task deadlines and acceptable loss before choosing the next research direction.
