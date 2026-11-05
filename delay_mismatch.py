"""Input-constrained MPC with a fixed, possibly incorrect, delay assumption."""
from pathlib import Path
from time import perf_counter
import csv
import hashlib
import json
import platform
import sys
import numpy as np
import scipy
from scipy import sparse
import osqp
from experiment import A, B, DT, HORIZON, STEPS, DelayQueue, augmented_model

LIMIT = 2.0  # illustrative acceleration limit [m/s²], not hardware calibrated
TRUE_DELAY = 6
ASSUMED_DELAYS = (0, 2, 4, 6, 8)


class BoxMPC:
    def __init__(self, delay, limit=LIMIT):
        self.delay, self.limit = delay, limit
        aa, bb = augmented_model(delay)
        n, h = aa.shape[0], HORIZON
        self.F = np.zeros((2*h, n))
        self.G = np.zeros((2*h, h))
        for i in range(h):
            self.F[2*i:2*i+2] = np.linalg.matrix_power(aa, i+1)[:2]
            for j in range(i+1):
                self.G[2*i:2*i+2, j] = (np.linalg.matrix_power(aa, i-j) @ bb)[:2, 0]
        self.weights = np.tile([20., 1.], h)
        self.P = 2 * (self.G.T @ (self.weights[:, None]*self.G) + .2*np.eye(h))
        self.solver = osqp.OSQP()
        self.solver.setup(P=sparse.csc_matrix(self.P), q=np.zeros(h),
                          A=sparse.eye(h, format='csc'),
                          l=np.full(h, -limit), u=np.full(h, limit),
                          eps_abs=1e-8, eps_rel=1e-8, max_iter=20000,
                          polishing=True, verbose=False, warm_starting=True)

    def linear_term(self, x, history):
        # Reconstruct only the ASSUMED queue from sent commands. The controller
        # never accesses the physical queue or true delay.
        recent = ([0.] * self.delay + list(history))[-self.delay:] if self.delay else []
        z = np.r_[x - [1., 0.], recent]
        return 2 * self.G.T @ (self.weights * (self.F @ z))

    def solve(self, x, history):
        q = self.linear_term(x, history)
        self.solver.update(q=q)
        start = perf_counter()
        result = self.solver.solve(raise_error=True)
        elapsed = perf_counter() - start
        if result.info.status_val != 1:
            raise RuntimeError(f'QP not solved: {result.info.status}')
        if np.max(np.abs(result.x)) > self.limit + 2e-6:
            raise RuntimeError('QP returned infeasible command')
        return result.x.copy(), elapsed, result.info


def run_case(assumed, steps=STEPS):
    ctrl, plant_queue = BoxMPC(assumed), DelayQueue(TRUE_DELAY)
    x, history, rows = np.zeros(2), [], []
    states = [x.copy()]
    for k in range(steps):
        plan, duration, info = ctrl.solve(x, history)
        u = float(plan[0])
        applied = plant_queue.step(u)
        nx = A @ x + B[:, 0]*applied
        rows.append([k*DT, *x, u, applied, *nx, duration,
                     info.prim_res, info.dual_res, info.iter])
        history.append(u)
        x = nx
        states.append(x.copy())
    data, states = np.array(rows), np.array(states)
    error = states[:, 0]-1.
    acceptable = (np.abs(error) <= .02) & (np.abs(states[:, 1]) <= .02)
    suffix = np.logical_and.accumulate(acceptable[::-1])[::-1]
    indices = np.flatnonzero(suffix)
    # Require at least one second of observed residence, not just final sample.
    settled = float(indices[0]*DT) if len(indices) and indices[0] <= steps-20 else None
    metrics = dict(
        assumed_delay_s=assumed*DT, mismatch_s=(assumed-TRUE_DELAY)*DT,
        position_rmse_m=float(np.sqrt(np.mean(error**2))),
        tail_5s_rmse_m=float(np.sqrt(np.mean(error[-101:]**2))),
        overshoot_m=float(max(0., np.max(states[:, 0])-1.)),
        settling_time_s=settled, final_position_m=float(states[-1, 0]),
        final_velocity_m_s=float(states[-1, 1]),
        command_bound_fraction=float(np.mean(np.abs(data[:, 3]) >= LIMIT-1e-5)),
        applied_bound_duration_s=float(DT*np.sum(np.abs(data[:, 4]) >= LIMIT-1e-5)),
        max_abs_command_m_s2=float(np.max(np.abs(data[:, 3]))),
        max_bound_violation_m_s2=float(max(0., np.max(np.abs(data[:, 3:5]))-LIMIT)),
        command_total_variation=float(np.sum(np.abs(np.diff(data[:, 3])))),
        solve_median_ms=float(1000*np.median(data[:, 7])),
        solve_p95_ms=float(1000*np.percentile(data[:, 7], 95)),
        solve_max_ms=float(1000*np.max(data[:, 7])),
        qp_solves=int(steps), max_primal_residual=float(data[:, 8].max()),
        max_dual_residual=float(data[:, 9].max()),
    )
    return data, states, metrics


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out = Path(__file__).resolve().parent/'results'/'delay_mismatch'
    out.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    metrics = []
    for d in ASSUMED_DELAYS:
        data, states, record = run_case(d)
        metrics.append(record)
        with (out/f'assumed_{d:02d}_steps.csv').open('w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['time_s','position_m','velocity_m_s','command_m_s2',
                        'applied_m_s2','next_position_m','next_velocity_m_s',
                        'solve_s','primal_residual','dual_residual','qp_iterations'])
            w.writerows(data)
        label = f'assumed {d*DT:.2f} s'
        axes[0].plot(np.arange(STEPS+1)*DT, states[:, 0], label=label)
        axes[1].plot(np.arange(STEPS+1)*DT, states[:, 1])
        axes[2].plot(data[:, 0], data[:, 4])
    axes[0].axhline(1., c='black', ls='--', lw=1, label='reference')
    axes[0].legend(ncol=3, fontsize=9)
    for ax, label in zip(axes, ['Position [m]','Velocity [m/s]','Applied acceleration [m/s²]']):
        ax.set_ylabel(label)
        ax.grid(alpha=.25)
    for sign in [-1, 1]:
        axes[2].axhline(sign*LIMIT, c='black', ls='--', lw=.8)
    axes[2].set_xlabel('Time [s]')
    fig.suptitle('Delay mismatch with input-constrained MPC\nTrue delay 0.30 s; acceleration bound ±2 m/s²')
    fig.tight_layout()
    fig.savefig(out/'trajectories.png', dpi=170)
    plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    for ax, key, title in zip(axes, ['position_rmse_m','overshoot_m','applied_bound_duration_s'],
                               ['Position RMSE [m]','Overshoot [m]','Time at input bound [s]']):
        ax.plot([m['assumed_delay_s'] for m in metrics], [m[key] for m in metrics], 'o-')
        ax.axvline(TRUE_DELAY*DT, c='black', ls='--', lw=1)
        ax.set(xlabel='Assumed delay [s]', title=title)
        ax.grid(alpha=.25)
    fig.suptitle('Fixed true delay 0.30 s; deterministic single rollout per assumption')
    fig.tight_layout()
    fig.savefig(out/'performance.png', dpi=170)
    plt.close(fig)
    with (out/'metrics.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(metrics[0]))
        w.writeheader()
        w.writerows(metrics)
    source = Path(__file__)
    record = dict(config=dict(dt_s=DT, steps=STEPS, horizon_steps=HORIZON,
        true_delay_steps=TRUE_DELAY, assumed_delay_steps=ASSUMED_DELAYS,
        acceleration_bound=LIMIT, Q=[20., 1.], R=.2, terminal_cost='Q',
        state_constraints=None, disturbance=None, noise=None, randomness=None,
        initial_state=[0., 0.], initial_queue='zeros', reference=[1., 0.],
        controller_information='state and sent command history only',
        settling_definition='position and speed within 0.02 through end, at least 1 s residence',
        timing_scope='solver.solve only, warm starts, excludes model/update/logging'),
        environment=dict(python=sys.version, platform=platform.platform(), numpy=np.__version__,
                         scipy=scipy.__version__, osqp=osqp.__version__, matplotlib=matplotlib.__version__),
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in [source, source.with_name('experiment.py')]}, metrics=metrics)
    (out/'summary.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    main()
