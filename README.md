# Robot Control Research: Reproducible Experiments and Failure Analysis

[中文说明](README.zh-CN.md) · [Reproduction guide](docs/REPRODUCING.md) · [Research summary](report/PUBLIC_RESEARCH_SUMMARY_EN.md)

An independent research archive by Lufei Wang ([SamWongC](https://github.com/SamWongC)), exploring delayed control, model ambiguity, and numerical fidelity in contact-based planning. Includes Python implementations, frozen synthetic inputs, raw results, bilingual reports, and numerical checks—including methods that did **not** improve the baselines.

**Status:** exploratory research, not an accepted paper or a demonstrated novel algorithm. The original local folder was named `RA-L`; that was an aspiration, not a publication status. This is not an official RWTH or Robot Companion project.

## Research questions

1. When can input delay and external disturbance be distinguished, and when does this matter to the task?
2. Can coarse screening or contact-local refinement reduce planning cost without losing useful actions?
3. Do open-loop ranking differences translate into improved closed-loop outcomes?

## Selected findings

| Experiment | Evidence | Interpretation |
|---|---|---|
| Stronger passive baselines | Some apparent active-identification benefits disappeared | Baseline choice matters; established machinery is not a new contribution |
| Frozen screening confirmation | Top32 matched all256 winners at the .0025s reference; .000625s audit changed27 reference winners | Numerical agreement is not physical correctness |
| Batch148 convergence audit | Ranking reversal persisted across five solver settings and finer-step grid | A numerical counterexample, not a general error bound |
| Single-pass refinement |20.8% fewer steps; p95=61.29ms vs54.63ms uniform fine | Fewer steps did not lower end-to-end latency |
| Closed-loop confirmation | Low/medium/high/top32 succeeded57/55/54/55 of64 episodes | No demonstrated overall benefit from finer prediction |
| Post-hoc sensitivity |15/32 outcome labels flipped in eight selected disagreement cases | Difficult results need robustness checks; this is not a population rate |

Compare timing **within** each recorded experiment, not across stages. Closed-loop latency was measured but not injected into dynamics. Fine-controller p95=73.03ms does not demonstrate a50ms real-time loop.

## Evidence

- [Closed-loop task-meaning report](report/PUSH_T_CLOSED_LOOP_GATE_REPORT_EN.md)
- [Execution feasibility gate](report/PUSH_T_EXECUTION_GATE_REPORT_EN.md)
- [Batch148 numerical audit](report/PUSH_T_BATCH148_AUDIT_REPORT_EN.md)
- [Topic go/no-go review](report/TOPIC_GO_NO_GO_REVIEW_2026-11-04_EN.md)
- [Experiment map](docs/EXPERIMENTS.md) and [historical log](RESEARCH_HISTORY.md)

## Quick start

From the repository root, verify distributed files with Python's standard library:

```sh
python verify_release.py
```

This checks SHA-256 integrity, not scientific correctness. Reports and raw results are included; no private dataset, ROS installation or GPU is needed to read them. To reconstruct closed-loop statistics in a separate copy:

```powershell
python -m venv .venv-contact
.venv-contact/Scripts/python.exe -m pip install -r requirements-contact-cpu.txt
.venv-contact/Scripts/python.exe reproduce.py --experiment closed-loop-summary --output runs/summary-001
```

Python3.12 was used. On macOS/Linux use `.venv-contact/bin/python`; those platforms have not been tested here. See [full installation, tests and reruns](docs/REPRODUCING.md). `reproduce.py` creates a new directory and does not overwrite the distributed evidence.

## Layout

```text
*.py                    Experiment implementations and tests
requirements*.txt       Separate control / CPU contact / historical GPU environments
report/                 Chinese and English research reports
results/                Frozen inputs, outputs, figures and execution snapshots
docs/                   Experiment map and reproduction notes
RELEASE_MANIFEST.json   SHA-256 inventory
```

Code stays at the root to preserve imports and provenance. Historical hashes refer to execution-time source, not necessarily current reporting scripts. Earlier plans in the historical log are superseded by the final reports.

## Limitations and attribution

The contact task is custom planar T-shaped pushing with ideal state sensing, zero gravity and joint friction/damping approximating planar drag. There is no robot arm, physical floor contact or obstacle-avoidance validation. It is **not** the standard Push-T benchmark or an exact reproduction of another lab's controller. Finer simulation is not calibrated physical truth. No hardware validation, general safety/reliability guarantee or publication novelty is claimed.

Code and reports were developed with AI coding assistance; automated checks do not replace independent scientific validation. Literature notes are bounded historical reviews with stated access limits, not exhaustive novelty certification.

No open-source license has been selected: see [LICENSE_NOTICE.md](LICENSE_NOTICE.md). Dependencies and cited work retain their own licenses and attribution. No third-party papers, private correspondence, credentials or environments are bundled. There is no associated accepted paper or DOI; identify the repository revision and specific experiment when referring to these results.
