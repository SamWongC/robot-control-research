"""Causal sliding-window delay identification under an unmodelled disturbance.

Four paired deterministic rollouts. Known-delay MPC is an informed reference;
the adaptive baseline receives only states and sent commands, not disturbance
or true delay. Score gaps are diagnostics, not calibrated confidence.
"""
from collections import deque
from pathlib import Path
import contextlib
import csv
import hashlib
import io
import json
import platform
import sys
import numpy as np
import osqp
import scipy
from experiment import A, B, DT, STEPS, HORIZON, DelayQueue
from delay_mismatch import BoxMPC, LIMIT, TRUE_DELAY

CANDIDATES = tuple(range(9))
WINDOW = 20
WARMUP = 20
DISTURBANCE = .5  # illustrative acceleration, 25% of commanded-input limit
START, END = 100, 160  # transitions starting at 5 <= t < 8 seconds


def disturbance_at(k, enabled):
    return DISTURBANCE if enabled and START <= k < END else 0.


class DelayEstimator:
    """At time k, use only observed transitions 0..k-1.

    For transition j: observed acceleration=(v[j+1]-v[j])/dt.
    Candidate d predicts sent_command[j-d], or zero for negative indices.
    The estimator assumes no disturbance and deliberately exposes its failure.
    Tie rule: keep previous estimate if within absolute 1e-12 MSE of minimum.
    Start with zero delay, freeze updates during the first WINDOW observations.
    """
    def __init__(self):
        self.commands = []
        self.errors = deque(maxlen=WINDOW)
        self.estimate = 0
        self.scores = np.zeros(len(CANDIDATES))
        self.gap = 0.

    def observe(self, before, after, command):
        j = len(self.commands)
        self.commands.append(float(command))
        accel = float((after[1]-before[1])/DT)
        predicted = np.array([self.commands[j-d] if j >= d else 0. for d in CANDIDATES])
        self.errors.append((predicted-accel)**2)
        self.scores = np.mean(self.errors, axis=0)
        sorted_scores = np.sort(self.scores)
        self.gap = float(sorted_scores[1]-sorted_scores[0])
        if len(self.commands) >= WARMUP:
            minimum = float(self.scores.min())
            if self.scores[self.estimate] > minimum+1e-12:
                self.estimate = int(np.argmin(self.scores))


def rollout(adaptive, disturbed):
    controllers = {d: BoxMPC(d) for d in CANDIDATES}
    plant = DelayQueue(TRUE_DELAY)
    estimator = DelayEstimator()
    x, history, states, rows = np.zeros(2), [], [np.zeros(2)], []
    for k in range(STEPS):
        estimate = estimator.estimate
        used = estimate if adaptive else TRUE_DELAY
        plan, duration, info = controllers[used].solve(x, history)
        u = float(plan[0])
        applied = plant.step(u)
        w = disturbance_at(k, disturbed)
        nx = A@x + B[:, 0]*(applied+w)
        # Scores and estimate here are available BEFORE sending command k.
        rows.append([k*DT, *x, u, applied, w, estimate*DT, used*DT,
                     estimator.gap, *estimator.scores, *nx, duration,
                     info.prim_res, info.dual_res])
        estimator.observe(x, nx, u)  # available to the next control decision
        history.append(u)
        x = nx
        states.append(x.copy())
    data, states = np.array(rows), np.array(states)
    errors = states[:, 0]-1.
    okay = (np.abs(errors) <= .02)&(np.abs(states[:, 1]) <= .02)
    suffix = np.logical_and.accumulate(okay[::-1])[::-1]
    recovery = np.flatnonzero(suffix & (np.arange(STEPS+1) >= END))
    recovered = float(recovery[0]*DT-8.) if len(recovery) and recovery[0] <= STEPS-20 else None
    metrics = dict(adaptive=adaptive, disturbed=disturbed,
        position_rmse_m=float(np.sqrt(np.mean(errors**2))),
        post_5s_position_rmse_m=float(np.sqrt(np.mean(errors[START:]**2))),
        peak_abs_error_after_5s_m=float(np.max(np.abs(errors[START:]))),
        recovery_after_8s_s=recovered,
        max_abs_command_m_s2=float(np.max(np.abs(data[:, 3]))),
        final_position_m=float(states[-1, 0]),
        estimator_switches=int(np.count_nonzero(np.diff(data[:, 6]))),
        solve_p95_ms=float(1000*np.percentile(data[:, -3], 95)),
        max_primal_residual=float(np.max(data[:, -2])),
        max_dual_residual=float(np.max(data[:, -1])))
    for label, lo, hi in [('before',WARMUP,START),('during',START,END),('after',END,STEPS)]:
        estimates = data[lo:hi, 6]/DT
        metrics[f'delay_error_{label}_s'] = float(np.mean(np.abs(estimates-TRUE_DELAY))*DT)
        metrics[f'delay_wrong_fraction_{label}'] = float(np.mean(np.abs(estimates-TRUE_DELAY)>.1))
        scores = data[lo:hi, 9:18]
        metrics[f'near_tie_fraction_{label}'] = float(np.mean(np.ptp(scores,axis=1)<1e-8))
    return data, states, metrics


def save_reports(out, records):
    lines = ['| Case | Post-5 s RMSE (m) | Peak error after 5 s (m) | Recovery after 8 s (s) | Wrong-delay fraction during 5–8 s |',
             '|---|---:|---:|---:|---:|']
    for name, m in records.items():
        recovery = 'not reached' if m['recovery_after_8s_s'] is None else f"{m['recovery_after_8s_s']:.2f}"
        lines.append(f"| {name} | {m['post_5s_position_rmse_m']:.6f} | {m['peak_abs_error_after_5s_m']:.6f} | {recovery} | {m['delay_wrong_fraction_during']:.1%} |")
    table = '\n'.join(lines)
    en = '''# Experiment 3: External Disturbance and Delay Identification

Date: 2026-11-03. Deterministic mechanism experiment; no learned model or proposed confidence-aware controller.

## Setup

The same 1D double integrator tracks a constant 1 m reference from rest. Sampling 0.05 s; duration 20 s; horizon 40 steps; Q=diag(20,1), R=0.2, terminal Q. Command and delayed actuator input bounds are ±2 m/s². No state constraints or measurement noise. True delay is fixed at six steps (0.30 s) in all four runs. A positive external acceleration of 0.5 m/s² acts during transitions starting at 5 ≤ t < 8 s. The amplitude is illustrative (25% of the command limit), not hardware calibrated. External acceleration is added after the actuator; total acceleration can exceed the actuator command limit without violating that limit.

Four runs pair disturbance off/on with an informed fixed-delay MPC and an adaptive single-estimate MPC. The informed reference knows the true delay, but has no disturbance feedforward/observer. All other settings are matched. Thus absolute disturbance rejection performance is not a comparison against a strong disturbance-aware controller.

## Estimator and Information

Nine candidates, 0..8 steps. Each observed velocity transition gives an acceleration estimate. Each candidate predicts that acceleration using only the appropriately shifted sent command. The score is mean squared acceleration error over the last 20 transitions (one second); initial negative-index commands are zero. Start at assumed delay zero and freeze updates for the first 20 observations. Keep the previous estimate when it is within 1e-12 of the best MSE; otherwise select the smallest-index minimizer. Scores at time k use only transitions completed before k. The adaptive controller never receives true delay, actual applied input, or external disturbance. These quantities appear only in evaluation logs. The fixed controller also hosts the same estimator passively, isolating estimation behavior from adaptive control feedback. The best/second-best score gap is an uncalibrated diagnostic, not a probability or safety certificate.

## Results

TABLE

Metrics use 401 states including the final state; estimator statistics use decisions after warm-up. Post-5 s RMSE includes t=5..20 s. Recovery is the first time after t=8 s with |position error|≤0.02 m and |speed|≤0.02 m/s through the end, with at least one second residence. Wrong-delay fraction compares the pre-command estimate with six steps. A correct retained estimate during a near tie is not evidence of identifiability. No statistical uncertainty is claimed from these deterministic single rollouts.

## Interpretation and Limits

Read identification errors separately for the passive and adaptive estimator: their command histories differ. Compare paired disturbance/no-disturbance runs before attributing degradation to disturbance. Tracking error can arise directly from external force as well as from delay misidentification. These four trajectories alone cannot separate all causal pathways or establish universal failure. In particular, the warm-up estimate is zero by design, and startup adaptation itself can affect closed-loop behavior. A constant reference becomes weakly informative near rest. Additional reference trajectories, disturbance amplitudes/signs, window sizes and a disturbance-observer baseline are needed. An online delay estimator is not automatically superior to an informed fixed-delay controller.

## Verification and Reproduction

Run `.\\.venv\\Scripts\\python.exe -m unittest -v`, then `.\\.venv\\Scripts\\python.exe disturbance_identification.py` from the project root. Use requirements-lock.txt. Tests check disturbance timing, noiseless recovery on excited synthetic data, invariance to adding future observations, and an explicit disturbance/incorrect-delay ambiguity. Original MPC/queue tests remain applicable. Optimization failures or infeasible returned inputs raise errors. Solver-only timings exclude parameter updates and estimator work.

Files in results/disturbance_identification: four case CSVs (pre-action states and scores plus post-action states); metrics.json; summary.json with configuration/environment/code hashes; tracking.png; identification.png; passive_scores.png. Full reports are saved in report/ in Chinese and English.

Next: inspect whether the passive estimator misidentifies delay during disturbance and whether the adaptive baseline incurs additional tracking cost. Then add disturbance-aware identification and controlled excitation; evaluate on held-out settings before developing confidence-aware control.
'''.replace('TABLE',table)
    zh = '''# 实验三：外部扰动与延迟识别

日期：2026-11-03。确定性的机制实验；尚无学习模型或拟议置信度控制器。

## 设置

一维双积分系统从静止追踪 1 m 固定目标。周期 0.05 s，运行 20 s，预测 40 步；Q=diag(20,1)，R=0.2，末端 Q。指令及延迟执行输入限制为 ±2 m/s²，不设状态约束，无测量噪声。四组真实延迟均固定为六步（0.30 s）。在 5≤t<8 s 的状态转移中加入正向 0.5 m/s² 外部加速度。幅值为示例，等于指令上限的 25%，未经硬件标定。外力在执行器之后作用；总加速度可以超过执行器输入限制，并不代表指令越界。

四组为“已知固定延迟 MPC / 自适应单点延迟 MPC”分别配对“无扰动 / 有扰动”。固定延迟参考方法知道真实延迟，但没有外扰前馈或观测器，其他条件匹配。因此绝对抗扰性能不能视为与强抗扰控制器的比较。

## 估计器与信息条件

候选为 0..8 步；用每次观测到的速度增量计算加速度，对每个候选按历史发送指令预测加速度。最近 20 次转移（一秒）的加速度误差平方均值为评分，负索引指令视为零。初始估计零步，前 20 次观测冻结；原估计评分在最小值 1e-12 内则保留，否则选择评分最小且索引最小的候选。时刻 k 的评分仅使用 k 之前已完成的转移。自适应控制器不知道真实延迟、实际执行输入和外扰；这些仅供记录评价。固定延迟控制器也被动运行同一个估计器，帮助区分识别问题与自适应反馈。最优与次优评分差只是未经校准的诊断量，不是概率或安全证明。

## 结果

下表英文 case 名称：fixed_clean=已知延迟、无扰动；fixed_disturbed=已知延迟、有扰动；adaptive_clean=自适应、无扰动；adaptive_disturbed=自适应、有扰动。列依次为 5 s 后 RMSE、5 s 后峰值误差、8 s 后恢复时间、5–8 s 延迟误判比例。

TABLE

状态指标统计 401 个样本（含末状态），延迟指标排除初始预热。5 s 后 RMSE 使用 t=5..20 s。恢复定义为 8 s 后位置误差≤0.02 m 且速度绝对值≤0.02 m/s，此后一直保持至终点且至少保持一秒。误判率比较发送指令前估计与真实六步。近乎平局时保留正确估计，不能证明延迟可辨识。每组仅一次确定性运行，没有统计不确定性结论。

## 解释与限制

被动估计器与自适应估计器的动作历史不同，识别误差必须分开看；归因于外扰前应先比较成对的有/无扰动实验。轨迹误差可能直接由外力造成，也可能来自延迟误判，四条轨迹不足以区分所有因果路径或证明普遍失效。预热估计人为设为零，启动自适应本身也会影响闭环表现。固定目标在接近静止时提供的信息较少。仍需改变参考轨迹、扰动幅值/符号、窗口长度，并加入外扰观测器基线。在线估计不必然优于知道真实延迟的固定控制器。

## 验证与复现

项目根目录运行 `.\\.venv\\Scripts\\python.exe -m unittest -v`，再运行 `.\\.venv\\Scripts\\python.exe disturbance_identification.py`；环境见 requirements-lock.txt。测试包括扰动起止时间、充分变化的合成指令下的无噪声识别、追加未来观测不改变已有估计、显式外扰与错误延迟的混淆反例。原有 MPC 与队列测试继续有效。求解失败或输入越界时报错。计算耗时仅为求解器部分，不含参数更新和估计。

results/disturbance_identification 中保存四组 CSV（动作前状态与评分以及动作后状态）、metrics.json、配置/环境/代码哈希 summary.json、tracking.png、identification.png 和 passive_scores.png。中英文完整报告位于 report 文件夹。

下一步：检查被动估计是否在扰动期误判，以及自适应基线是否增加跟踪代价，再加入考虑外扰的识别与可控激励，在未见条件下检验后才开发置信度控制。
'''.replace('TABLE',table)
    fixed=records['fixed_disturbed']
    adaptive=records['adaptive_disturbed']
    increase=(adaptive['post_5s_position_rmse_m']/fixed['post_5s_position_rmse_m']-1)*100
    en_findings=(f"In the paired clean runs, the estimate is correct after warm-up. With the disturbance, "
        f"the passive estimator selects an incorrect delay on {fixed['delay_wrong_fraction_during']:.1%} "
        f"of decisions during 5–8 s, while the adaptive estimator does so on "
        f"{adaptive['delay_wrong_fraction_during']:.1%}. The adaptive disturbed run has "
        f"{increase:.1f}% higher post-5 s RMSE than the informed disturbed reference. "
        "This is an observed association under different feedback trajectories, not a full causal isolation "
        "of identification error. Near rest, all candidate scores become nearly identical, so retention "
        "of the correct delay must not be interpreted as successful fresh identification.\n\n")
    zh_findings=(f"无扰动两组在预热后估计正确。加入扰动后，5–8 s 被动估计器误判比例为 "
        f"{fixed['delay_wrong_fraction_during']:.1%}，自适应估计器为 "
        f"{adaptive['delay_wrong_fraction_during']:.1%}。自适应有扰动组的 5 s 后 RMSE "
        f"比已知延迟有扰动参考高 {increase:.1f}%。这是不同反馈轨迹下的观测关联，"
        "尚未完全隔离识别错误的因果作用。接近静止后候选评分几乎相同，因此保留正确延迟"
        "不能理解为仍在成功进行新的识别。\n\n")
    en=en.replace('## Interpretation and Limits\n\n','## Interpretation and Limits\n\n'+en_findings)
    zh=zh.replace('## 解释与限制\n\n','## 解释与限制\n\n'+zh_findings)
    root = out.parent.parent
    (root/'report').mkdir(exist_ok=True)
    (root/'report'/'DISTURBANCE_IDENTIFICATION_REPORT_EN.md').write_text(en,encoding='utf-8')
    (root/'report'/'DISTURBANCE_IDENTIFICATION_REPORT.md').write_text(zh,encoding='utf-8')


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    root=Path(__file__).resolve().parent
    out=root/'results'/'disturbance_identification'
    out.mkdir(parents=True,exist_ok=True)
    results, metrics = {}, {}
    for adaptive in [False, True]:
        for disturbed in [False, True]:
            name=('adaptive' if adaptive else 'fixed')+('_disturbed' if disturbed else '_clean')
            with contextlib.redirect_stdout(io.StringIO()):
                data,states,m=rollout(adaptive,disturbed)
            results[name]=(data,states)
            metrics[name]=m
            with (out/f'{name}.csv').open('w',newline='') as f:
                w=csv.writer(f)
                w.writerow(['time_s','position_m','velocity_m_s','command_m_s2','applied_m_s2',
                            'disturbance_m_s2','estimated_delay_s','control_delay_s','score_gap',
                            *[f'mse_delay_{d}' for d in CANDIDATES], 'next_position_m',
                            'next_velocity_m_s','solve_s','primal_residual','dual_residual'])
                w.writerows(data)
    for filename,cols in [('tracking',[1,2,3]),('identification',[6,7,8])]:
        fig,axes=plt.subplots(3,1,figsize=(11,9),sharex=True)
        labels=['Position [m]','Velocity [m/s]','Command [m/s²]'] if filename=='tracking' else ['Estimated delay [s]','Control delay [s]','Score gap [(m/s²)²]']
        for name,(data,states) in results.items():
            for ax,col in zip(axes,cols):
                if filename=='tracking' and col in [1,2]:
                    ax.plot(np.arange(STEPS+1)*DT,states[:,col-1],label=name)
                else:
                    ax.plot(data[:,0],data[:,col],label=name,alpha=.85)
        if filename=='tracking':
            axes[0].axhline(1.,color='black',ls='--',lw=1)
        else:
            for ax in axes[:2]: ax.axhline(.3,color='black',ls='--',lw=1)
            axes[2].set_yscale('symlog',linthresh=1e-8)
        for ax,label in zip(axes,labels):
            ax.axvspan(5,8,color='gray',alpha=.15)
            ax.set_ylabel(label)
            ax.grid(alpha=.25)
        axes[0].legend(fontsize=8,ncol=2)
        axes[-1].set_xlabel('Time [s]')
        fig.suptitle('Fixed true input delay 0.30 s; external acceleration +0.5 m/s² during 5–8 s\n'+
                     ('Tracking comparison' if filename=='tracking' else 'Causal estimator; score gap is NOT calibrated confidence'))
        fig.tight_layout(rect=(0,0,1,.94))
        fig.savefig(out/f'{filename}.png',dpi=150)
        plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(11,7),sharex=True)
    for ax,name in zip(axes,['fixed_clean','fixed_disturbed']):
        data,_=results[name]
        for d in CANDIDATES: ax.plot(data[:,0],data[:,9+d],label=f'{d*DT:.2f} s')
        ax.axvspan(5,8,color='gray',alpha=.15)
        ax.set_yscale('symlog',linthresh=1e-8)
        ax.set(title=name,ylabel='Acceleration MSE')
        ax.grid(alpha=.25)
    axes[0].legend(ncol=5,fontsize=8)
    axes[-1].set_xlabel('Time [s]')
    fig.suptitle('Candidate scores on informed-controller trajectories (passive estimation)')
    fig.tight_layout()
    fig.savefig(out/'passive_scores.png',dpi=150)
    plt.close(fig)
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    record=dict(config=dict(dt_s=DT,steps=STEPS,horizon=HORIZON,true_delay_steps=TRUE_DELAY,
        candidates=CANDIDATES,window=WINDOW,warmup=WARMUP,initial_estimate=0,
        disturbance_acceleration=DISTURBANCE,disturbance_interval_s=[5,8],limit=LIMIT,
        tie_tolerance=1e-12,near_tie_score_range_threshold=1e-8,
        score_units='squared acceleration',noise=None,randomness=None),
        environment=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,
                         osqp=osqp.__version__,matplotlib=matplotlib.__version__,platform=platform.platform()),
        source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest()
                       for name in ['experiment.py','delay_mismatch.py','disturbance_identification.py']},
        metrics=metrics)
    (out/'summary.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    save_reports(out,metrics)
    print(json.dumps(metrics,indent=2))


if __name__=='__main__': main()
