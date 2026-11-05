# Reproducing the archive

## Environments

Recorded platform: Windows11, Python3.12. Other platforms and fresh internet installs were not tested for this release. Pinned files record local environments, not availability on every platform. Keep control and contact environments separate:

```powershell
python -m venv .venv-control
.venv-control/Scripts/python.exe -m pip install -r requirements-reproduction-lock.txt
python -m venv .venv-contact
.venv-contact/Scripts/python.exe -m pip install -r requirements-contact-cpu.txt
```

`requirements.txt` is the initial NumPy/Matplotlib environment. `requirements-lock.txt` adds earlier control optimization tools. `requirements-reproduction-lock.txt` is the broader control/CVXPY environment. `requirements-contact-lock.txt` is the optional historical GPU environment, not required for CPU experiments. GPU and CPU results are not assumed equivalent.

## Verify and test

```powershell
python verify_release.py
.venv-control/Scripts/python.exe run_tests.py --suite control
.venv-contact/Scripts/python.exe run_tests.py --suite contact
```

Tests use bundled fixtures. See the release checklist for checks actually run. On macOS/Linux use `.venv-*/bin/python` instead.

## Isolated reruns

Historical scripts write relative to their source; some refuse overwrites, others regenerate reports. The closed-loop runner resumes existing episodes, so running it directly in the archive is not a fresh replication. Use the wrapper, which rejects an existing output directory:

```powershell
# Reconstruct statistics/reports from saved trajectories in a copy:
.venv-contact/Scripts/python.exe reproduce.py --experiment closed-loop-summary --output runs/summary-001
# Full new execution with the recorded seeds:
.venv-contact/Scripts/python.exe reproduce.py --experiment closed-loop --output runs/closed-loop-001
# Timing gate against archived prerequisites:
.venv-contact/Scripts/python.exe reproduce.py --experiment execution-gate --output runs/execution-001
# Minimal delay demonstration:
.venv-control/Scripts/python.exe reproduce.py --experiment minimal --output runs/minimal-001
```

`--prepare-only` creates the working copy and prints commands without executing them. The wrapper copies archived prerequisites and omits the selected output subtree for fresh experiments. It retains all data for summary reconstruction. Full contact runs take many minutes; hardware load affects timing. If the development gate fails in a new environment, confirmation is not run; this is an incomplete replication rather than the original counts.

## Provenance

- Release hashes describe distributed bytes; `.gitattributes` prevents newline conversion.
- Historical source hashes describe execution-time source. Use saved snapshots where present; do not rewrite old hashes to match new reporting code.
- Floating-point trajectories and latency may change across environments. Fine steps are not physical calibration.
- The inspected confirmation set cannot be relabelled unseen after tuning a new method.
- Closed-loop records contain16 development,256 confirmation-method,4 execution sensitivity and40 additional diagnostic episodes:316 total. The15/32 flips are outcome-selected diagnostics.
