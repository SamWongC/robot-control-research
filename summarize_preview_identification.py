"""Bilingual report generated from frozen experiment artifacts."""
from pathlib import Path
import hashlib,json

def main():
    root=Path(__file__).resolve().parent;out=root/'results'/'preview_identification';report=root/'report'
    s=json.loads((out/'summary.json').read_text());audit=json.loads((out/'audit.json').read_text())
    episodes=json.loads((out/'episodes.json').read_text())
    assert s['config']['source_sha256']==hashlib.sha256((root/'preview_identification.py').read_bytes()).hexdigest()
    table='| Preview steps (s) | hold_passive | task_only | probe | oracle |\n|---|---:|---:|---:|---:|\n'
    for p in (0,1,2,4,8):
        cells=[]
        for mode in ('hold_passive','task_only','probe','oracle'):
            g=next(g for g in s['groups'] if g['preview']==p and g['mode']==mode and g['scope']=='all')
            cells.append(f"{g['success_count']}/{g['episodes']} ({100*g['success_fraction']:.1f}%)")
        table+=f'| {p} ({p*.05:.2f}) | '+' | '.join(cells)+' |\n'
    energy='| Preview steps | task_only energy | probe energy |\n|---|---:|---:|\n'
    for p in (1,2,4,8):
        cells=[]
        for mode in ('task_only','probe'):
            g=next(g for g in s['groups'] if g['preview']==p and g['mode']==mode and g['scope']=='all')
            cells.append(f"{g['mean_prep_energy']:.7f}")
        energy+=f'| {p} | '+' | '.join(cells)+' |\n'
    # Save the exact clean long-preview commands supporting the waiting diagnosis.
    import csv
    with (out/'trajectories.csv').open(newline='') as f:
        rows=list(csv.DictReader(f))
    clean8=[r for r in rows if r['preview']=='8' and r['mode']=='task_only' and r['case']=='clean' and r['true_delay']=='1']
    commands=', '.join(f"{float(r['command']):.5f}" for r in clean8[:8])
    common=f'''
{table}

![Observed task success](../results/preview_identification/preview_success.png)

{energy}

Source SHA-256: `{s['config']['source_sha256']}`.

Python {s['versions']['python']}; NumPy {s['versions']['numpy']}; SciPy {s['versions']['scipy']}; HiGHS via scipy.optimize.linprog.
'''
    zh=f'''# 预告时间、延迟辨识与任务恢复：实验报告

日期：2026-11-04。性质：构造任务的开发集实验，非独立确认性测试，非新算法或创新性证明。

## 结论

提前预告配合固定试探，能在本轮有限样本中恢复此前冲突任务的完成能力。所有正预告条件下，probe 在首步观测后保留唯一正确延迟；但一个采样周期的预告仍有任务失败。被动任务控制也能通过自身动作辨识：在 2、4 个采样周期时与 probe 同样完成全部测试。因此不能将辨识成功或恢复可行性单独作为主动辨识方法优越性的证据。

## 系统、任务与信息

继承 [问题定义](TASK_AMBIGUITY_PROBLEM_DEFINITION.md)：双积分器 dt=0.05 s，固定未知延迟 d=0/1，输入上限 2 m/s²，外扰幅值 0.02 m/s²、每步增量上限 0.01 m/s²，位置/速度测量误差上限 1e-5 m / 1e-4 m/s。

预告长度 N=0/1/2/4/8 步。用全局索引 k=0 表示预告到来，原任务开始于 k=N，截止于 N+2。目标仍为位置 0.002 m、速度 0.08 m/s，终点误差容限分别 0.0002 m、0.003 m/s。目标是相同的绝对状态，未随预告或初始偏离移动。预告越长，总准备时间越长，故不把效果全部归因于信息。

各方法拥有相同预告、动作上限与准备阶段约束：所有准备阶段状态满足 |p|≤0.01 m、|v|≤0.06 m/s；任务开始的边界状态也计入准备检查。目标任务内没有新增路径约束。仿真从同一个物理零状态出发，控制器只得到带界噪声的测量。历史输入零；延迟候选初始为两个，过滤器只用从当前预告开始的测量前缀，丢弃更早历史是一项保守选择。

## 四组方法

- hold_passive：准备阶段人为保持零输入，任务开始后才进行任务控制及候选更新；它是“等待准备”的参照，不是最强被动控制器。
- task_only：从预告到来就进行任务控制，每步根据测量更新候选，不额外优化可辨识性。任务动作本身可能产生辨识信息，是更重要的对照。
- probe：N>0 时第一步固定发送 0.1 m/s²，随后使用与 task_only 相同的候选过滤和任务控制。N=0 时没有试探，等同 task_only。
- oracle：从第一步知道真实延迟，其余任务控制器与约束相同。仅这组允许使用真实延迟作为控制输入信息；不是全局最优策略。

候选筛选是有界误差线性可行性检查：存在满足所有已观测状态区间、系统方程、外扰幅值/变化率的轨迹才保留候选。真值、执行时间戳、未来观测不输入未知延迟控制器。控制律每步求共同开环计划，最小化归一化终点最坏违反量 t，加 1e-5 倍输入绝对值和以选择动作；准备阶段状态边界作为硬约束。t=0 且残差通过检查，只表示当前求出的计划具有充分的鲁棒终点证据，不等于已证明整套重规划策略递归可行。

未来预测用当前测量误差盒与未来外扰序列的保守乘积包络。双积分器的分量支持由全正/全负常值极值达到，故幅值外包络与未来窗口内的变化率约束给出相同支持；未利用跨当前时刻的外扰相关性。若终点鲁棒可行集为空，仍执行最小违反计划并记录实际成败，不把软化后的解当作任务保证。若准备硬约束 LP 不可行，返回零输入并显式记录失败；本轮这种失败为零。

## 可手算的辨识条件

首步之前发送历史为零。由速度增量估计实际加速度，每个延迟假设的观测区间半径为 W+2ε_v/dt=0.024 m/s²。两区间不相交的充分条件为 |probe|>2W+4ε_v/dt=0.048 m/s²。固定 0.1 超过此界。因此在模型和误差边界成立时，首步即可区分两候选；这与后续任务是否仍可行是两个问题。该结论只针对本例的两个延迟和零历史条件。

## 配对设计与结果

每个预告/方法组合包含 37 条外扰与误差轨迹，分别配两个真实延迟，共 74 次。包括无扰动无噪声、正负极值常值外扰及交替误差、交替外扰、爬坡外扰，以及固定种子 20261104 的 32 条有界随机游走外扰和均匀有界测量误差。四组方法逐案例使用相同真实延迟、初态、外扰和测量误差，共 {s['episodes']} 次；不同预告共享外扰/误差前缀，但截止时间不同。

以下为所有案例的任务完成次数，要求终点容差和准备边界均满足；比例是本构造测试集的观测频率，不是概率保证。
{common}

能量为准备阶段 dt·sum(u²)，单位 m²/s³，包含全部准备动作，不单独把固定试探算作唯一成本；全部输入序列保留。正预告的 probe 均在 k=1 辨识正确。无准备边界违反，也无准备硬约束求解失败，真实延迟始终保留。

N=1：probe 在干净情况 2/2 成功，但有外扰/误差的 72 次中仅 47 次成功；task_only 对应 1/2 与 36/72。信息已经可用，但状态、队列、期限及控制器保守性仍限制任务完成。N=2 与 N=4：probe 和 task_only 均 74/74；说明任务输入本身在这些设置下足够。

N=8 的 task_only 降至 55/74。干净 d=1 案例准备命令依次为 [{commands}]，唯一延迟直到 k=9 才获得，已经晚于 k=8 的任务开始。这个现象与当前仅终点代价、无信息目标且含微小输入代价的重规划器相符：它可能推迟动作。不能推断预告越长本质上越差，也不能将此特定控制器的失败当作所有被动方法的下界。oracle 在本轮全部案例完成任务。

## 独立审计与边界

保存后另用标量物理递推审计 {audit['episodes_audited']} 次、{audit['transitions_audited']} 步：位置/速度转移、测量误差、配对外扰、实际延迟执行、指令历史连续性、任务开始状态、终点与准备指标、汇总计数均通过。物理递推最大残差 {audit['max_scalar_recurrence_residual']:.3g}。没有在任务开始重置状态或队列。五项针对性测试覆盖延迟队列预测、首步分离、任务开始连续性、生成边界、初始共同计划与已知延迟参考。完整测试见 preview_identification_tests.log。

在已测试的离散预告和有限案例中，probe 最短全部完成点是 N=2（0.1 s）；这不是连续预告时间或所有允许扰动下的最小保证时间。未设计最优试探、任务触发规则、全局最优被动策略或递归可行性证明。结果没有显示 probe 相对强被动基线在所有预告条件下严格更优。所有结果为开发数据，后续方法若据此调整，需要新的独立测试。

下一步应直接比较“无需额外试探即可完成”的区域和“任务动作信息不足”的区域，并引入辨识时间与可恢复任务集合的联系；同时加入被动控制器的代价/时序敏感性对照，避免把等待行为误判为主动辨识的普遍优势。

## 保存与运行

results/preview_identification/：config.json、paired_inputs.npz、trajectories.csv、episodes.json、summary.json、audit.json、preview_success.png。代码 preview_identification.py；审计 audit_preview_identification.py；报告生成 summarize_preview_identification.py；测试 test_preview_identification.py。沿用 requirements-reproduction-lock.txt 的现有环境，无新增依赖。

运行顺序：`.\\.venv\\Scripts\\python.exe -B preview_identification.py`、`.\\.venv\\Scripts\\python.exe -B audit_preview_identification.py`、`.\\.venv\\Scripts\\python.exe -B summarize_preview_identification.py`。完整回归：`.\\.venv\\Scripts\\python.exe -B -m unittest -v`。只写本次结果目录，不重跑旧实验。
'''
    en=f'''# Goal preview, delay identification and task recovery

Date: 2026-11-04. Constructed development benchmark; not a new identification method or an originality claim.

## Finding

Fixed probing with advance goal notice recovers task completion in the tested cases. Every positive-preview probe episode identifies the correct delay after the first observation, yet one-step preview still permits task failures. Task-only control also identifies through its own actions and matches probe at two- and four-step preview. Identification accuracy or recovery alone therefore does not establish superiority of dedicated active identification.

## Model, information and deadline

Use the existing [problem definition](TASK_AMBIGUITY_PROBLEM_DEFINITION_EN.md): double integrator dt=.05 s, fixed unknown d=0/1, command bound 2 m/s², disturbance bound .02 m/s² and increment bound .01 m/s² per sample. Measurement error bounds are 1e-5 m and 1e-4 m/s. Preview N∈{{0,1,2,4,8}} arrives at global k=0; the original task starts at k=N and ends at N+2. The absolute target remains (.002 m,.08 m/s), with tolerances (.0002 m,.003 m/s).

All methods share preparation state limits |p|≤.01 m, |v|≤.06 m/s, including the state at task start. No new within-task path constraints are imposed. The physical state initially equals zero; controllers only observe noisy measurements. Historical commands are zero. The prefix filter deliberately discards observations preceding preview, a conservative information choice. Longer preview supplies more preparation time as well as potential information.

## Methods and inference

- hold_passive: hold zero commands throughout preparation, then use task control and candidate updates. This is a waiting reference, not an optimal passive controller.
- task_only: use task control and candidate updates immediately on receiving preview, without a dedicated information objective. Its task actions can identify the delay.
- probe: when N>0 send a fixed .1 m/s² first command, then use the same controller/filter as task_only. At N=0 this equals task_only.
- oracle: know the true delay from the outset; otherwise use the same planner and constraints. This is not a globally optimal reference.

The prefix-only filter retains a delay if some state/disturbance trajectory fits every measured interval, the dynamics and the disturbance amplitude/rate constraints. Evaluation truth, future observations and execution timestamps are excluded from unknown-delay control. Each step solves a common open-loop minimax plan: normalized terminal violation t plus 1e-5 times command absolute sum, with hard preparation state envelopes. A zero-slack verified plan is a sufficient certificate for that plan, not a proof of recursive feasibility of the replanning policy.

Future uncertainty is conservatively bounded by a product of the present measurement-error box and future disturbance sequences. Positive double-integrator component supports are attained by constant extreme disturbances, satisfying the within-future rate limit. Cross-boundary correlations are omitted. When the robust endpoint is infeasible, the least-violation command is executed and actual failures remain in the record. Hard preparation LP infeasibility triggers a logged zero fallback; no such failures occurred here.

## First-step discrimination

With zero command history, the acceleration inferred from velocity increments has half-width W+2ε_v/dt=.024 m/s² under each hypothesis. A command magnitude greater than 2W+4ε_v/dt=.048 separates these intervals. The fixed .1 probe exceeds that bound. This suffices for one-step discrimination under the stated bounds; it does not suffice for task recovery.

## Paired evaluation

Each preview/method has 37 disturbance/error records and two true delays, giving 74 episodes. Records include a clean case, positive/negative extreme constant disturbances with alternating error corners, alternating disturbances, a ramp, and 32 bounded random walks with bounded uniform errors (seed 20261104). Methods share each physical initial state, delay, disturbance and error sequence. Preview settings share sequence prefixes but have different deadlines. Total: {s['episodes']} episodes.

Success requires both terminal tolerances and preparation bounds. Counts below are finite-set observations, not probability guarantees.
{common}

Preparation energy is dt·sum(u²) in m²/s³ and includes all preparation commands. Positive-preview probe identifies at k=1 in every case. No preparation boundary or hard-constraint solver failures occurred; the true delay was always retained.

At N=1, probe succeeds in 2/2 clean and 47/72 non-clean episodes; task_only succeeds in 1/2 and 36/72 respectively. Information is available, but the physical state, pending command, deadline and planning conservatism still matter. At N=2 and N=4, both methods succeed in 74/74: task-generated information is sufficient here.

At N=8, task_only drops to 55/74. In the clean d=1 episode, preparation commands are [{commands}], and identification only occurs at k=9, after the k=8 task start. This is consistent with delayed action under this terminal-only replanner with a small command penalty and no information objective. It is not evidence that additional preview fundamentally hurts, nor a bound on all passive methods. Oracle succeeds in every tested episode.

## Independent audit and scope

Saved records were independently audited over {audit['episodes_audited']} episodes and {audit['transitions_audited']} transitions using scalar physical updates. Measurement errors, paired disturbances, delayed application, sent-command continuity, task-start states, endpoint/preparation metrics and aggregate counts passed. Maximum recurrence residual: {audit['max_scalar_recurrence_residual']:.3g}. Neither state nor pending commands are reset at task start. Five targeted tests check queue prediction, interval separation, continuation, generated bounds and initial common/known-delay feasibility; full regression is recorded in preview_identification_tests.log.

The earliest tested preview at which probe completes every finite case is N=2 (.1 s). This is not a minimum guaranteed preview over continuous choices or all admissible uncertainties. Optimal probing, a task trigger, optimal passive control and recursive feasibility remain unproved. Results do not show strict probe superiority over the stronger passive baseline at every preview. These are development cases, so any data-informed revision requires fresh testing.

Next, map where ordinary task actions suffice and where information acquisition changes recoverability. Link identification time to recoverable task sets and test passive planner timing/cost sensitivity before claiming a general active-identification benefit.

## Artifacts

results/preview_identification/: config.json, paired_inputs.npz, trajectories.csv, episodes.json, summary.json, audit.json, preview_success.png. Scripts: preview_identification.py, audit_preview_identification.py, summarize_preview_identification.py; tests: test_preview_identification.py. Existing requirements-reproduction-lock.txt environment, no new dependencies.

Run these three scripts in that order using `.\\.venv\\Scripts\\python.exe -B`. Full regression: `.\\.venv\\Scripts\\python.exe -B -m unittest -v`. Historical experiment outputs are preserved.
'''
    report.mkdir(exist_ok=True)
    (report/'PREVIEW_IDENTIFICATION_REPORT.md').write_text(zh,encoding='utf-8')
    (report/'PREVIEW_IDENTIFICATION_REPORT_EN.md').write_text(en,encoding='utf-8')
    print('Saved Chinese and English reports from audited results.')

if __name__=='__main__':main()
