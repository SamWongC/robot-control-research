"""Deterministic delay-control plumbing experiment; not a research result.

Unconstrained finite-horizon linear quadratic MPC, exact ZOH double integrator.
Known-delay baseline uses state augmentation. No hidden delay is estimated here.
"""
from pathlib import Path
import csv
import hashlib
import json
import platform
import sys
import numpy as np

DT = 0.05
HORIZON = 40
STEPS = 400
DELAY = 6
A = np.array([[1., DT], [0., 1.]])
B = np.array([[0.5 * DT**2], [DT]])


class DelayQueue:
    """FIFO with constant integer delay d: action k is applied at step k+d.

    One enqueue/dequeue per sample; initial pending commands are zero.
    This class intentionally does not implement changing network delay.
    """
    def __init__(self, delay):
        if not isinstance(delay, int) or delay < 0:
            raise ValueError('delay must be a nonnegative integer')
        self.pending = [0.] * delay

    def step(self, command):
        self.pending.append(float(command))
        return self.pending.pop(0)


def augmented_model(delay):
    if delay == 0:
        return A.copy(), B.copy()
    n = 2 + delay
    aa, bb = np.zeros((n, n)), np.zeros((n, 1))
    aa[:2, :2] = A
    aa[:2, 2] = B[:, 0]
    for j in range(delay - 1):
        aa[2+j, 3+j] = 1.
    bb[-1, 0] = 1.
    return aa, bb


def mpc_gain(delay):
    """Finite-horizon tracking of constant r=1, terminal state cost Q.

    Backward Riccati recursion is an exact solution for this unconstrained
    linear quadratic problem; the receding-horizon first gain is reused.
    No saturation is applied, so this is NOT a constrained MPC benchmark.
    """
    aa, bb = augmented_model(delay)
    qq = np.zeros_like(aa)
    qq[:2, :2] = np.diag([20., 1.])
    pp = qq.copy()
    rr = np.array([[0.2]])
    for _ in range(HORIZON):
        gain = np.linalg.solve(rr + bb.T @ pp @ bb, bb.T @ pp @ aa)
        pp = qq + aa.T @ pp @ aa - aa.T @ pp @ bb @ gain
    return gain


def simulate(plant_delay, controller_delay):
    if controller_delay not in (0, plant_delay):
        raise ValueError('Only nominal or exact known-delay baseline supported')
    queue = DelayQueue(plant_delay)
    gain = mpc_gain(controller_delay)
    x = np.zeros(2)
    rows = []
    for k in range(STEPS):
        err = x - np.array([1., 0.])
        z = np.r_[err, queue.pending] if controller_delay else err
        u = -(gain @ z).item()
        applied = queue.step(u)
        # Log the pre-transition state and the input used for this transition.
        rows.append([k*DT, x[0], x[1], 1., u, applied])
        x = A @ x + B[:, 0] * applied
    if not np.isfinite(rows).all():
        raise RuntimeError('Non-finite rollout')
    return np.array(rows)


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out = Path(__file__).resolve().parent / 'results' / 'minimal'
    out.mkdir(parents=True, exist_ok=True)
    cases = [('no_delay_nominal', 0, 0),
             ('delayed_nominal', DELAY, 0),
             ('delayed_known_delay', DELAY, DELAY)]
    summary = {}
    fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    for name, delay, assumed in cases:
        data = simulate(delay, assumed)
        with (out / f'{name}.csv').open('w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['time_s','position_m','velocity_m_s','reference_m',
                             'command_m_s2','applied_m_s2'])
            writer.writerows(data)
        error = data[:, 1] - data[:, 3]
        summary[name] = {
            'position_rmse_m': float(np.sqrt(np.mean(error**2))),
            'max_abs_position_error_m': float(np.max(np.abs(error))),
            'last_position_m': float(data[-1, 1]),
            'max_abs_command_m_s2': float(np.max(np.abs(data[:, 4]))),
        }
        for ax, col in zip(axes, [1, 2, 5]):
            ax.plot(data[:, 0], data[:, col], label=name)
    axes[0].axhline(1., color='black', linestyle='--', label='reference')
    for ax, label in zip(axes, ['Position [m]', 'Velocity [m/s]', 'Applied acceleration [m/s²]']):
        ax.set_ylabel(label)
        ax.grid(alpha=.3)
        ax.set_yscale('symlog', linthresh=2.)
    axes[0].legend(fontsize=8)
    axes[-1].set_xlabel('Time [s]')
    fig.suptitle('Minimal linear control experiment: fixed input delay = 0.30 s\n'
                 'Unconstrained MPC; symmetric-log y axes show nominal divergence')
    fig.tight_layout()
    fig.savefig(out / 'delay_comparison.png', dpi=160)
    plt.close(fig)
    record = {
        'purpose': 'Implementation sanity check, not publication evidence',
        'config': {'dt_s': DT, 'horizon_steps': HORIZON, 'steps': STEPS,
                   'delay_steps': DELAY, 'reference_m': 1., 'Q': [20., 1.],
                   'R': 0.2, 'initial_state': [0., 0.], 'initial_queue': 'zeros',
                   'terminal_cost': 'Q', 'constraints': None,
                   'noise': None, 'disturbance': None, 'randomness': None},
        'environment': {'python': sys.version, 'executable': sys.executable,
                        'platform': platform.platform(), 'numpy': np.__version__,
                        'matplotlib': matplotlib.__version__},
        'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'metrics': summary,
    }
    (out / 'summary.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    print(f'Results: {out}')


if __name__ == '__main__':
    main()

