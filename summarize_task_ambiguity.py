"""Save bilingual mathematical definitions and reports from verified outputs."""
from pathlib import Path
import hashlib,json

ROOT=Path(__file__).resolve().parent

ZH=r'''# 问题定义 v0.1：任务相关的输入延迟歧义

日期：2026-11-04。用途：可行性机制验证；非已确认创新、非完整辨识控制算法。

## 1. 系统与信息

采用已有项目的一维双积分器：

$$x_{k+1}=Ax_k+B(u_{k-d}+w_k),\quad y_k=x_k+e_k,$$
$$x=(p,v)^T,\ A=\begin{bmatrix}1&0.05\\0&1\end{bmatrix},\ B=\begin{bmatrix}0.00125\\0.05\end{bmatrix}.$$

位置、速度、指令单位分别为 m、m/s、m/s²。未知延迟 d∈{0,1}，在采集窗口与两步任务内固定；采样周期 0.05 s。输入 |u|≤2；加速度外扰 |w|≤0.02，逐步变化 |w[k+1]−w[k]|≤0.01。测量误差逐分量有界：|e_p|≤1e-5 m、|e_v|≤1e-4 m/s，无独立性或高斯假设。

控制器知道模型、边界、目标、带样本索引的测量与自身发送指令；不知道真实延迟、真实状态、外扰与执行时刻。无执行端时间戳。评估程序可使用真值核验，但真值不进入候选筛选或控制求解。

## 2. 历史相容集合

给定窗口 y[-6..0]=0，全部历史发送指令（含窗口前）为零。定义 C 为满足上述系统方程、测量误差、外扰幅值与变化边界的某条状态/外扰轨迹所对应的延迟集合。每个候选用线性可行性规划检查。对两个延迟，x=0、w=0、e=0 是共同的显式见证，因此 C={0,1}。这是一段刻意无激励的窗口，不说明一般历史都不可辨识。

## 3. 两步终点任务与鲁棒可行性

在 k=0 收到目标 r=(p*,v*)，要求 k=2，即 0.1 s 后：

$$|p_2-p^*|\le 0.0002,\qquad |v_2-v^*|\le0.003.$$

没有中间状态约束；没有 k=2 之后的持续安全、稳定或终端不变集要求。只研究这一次短时任务。

未来不确定性取 x0∈[−ε,+ε]、w0,w1∈[−0.02,0.02]、|w1−w0|≤0.01 的笛卡尔积。它包含与历史相容的不确定性，但未强制末个历史外扰与 w0 的变化率，也未保留历史造成的状态/外扰相关性，因此是保守外包络。未来约束对这个外包络验证。

对每个延迟，x2=A²x0+G_d U+Ew，其中 U=(u0,u1)：

$$G_0=\begin{bmatrix}0.00375&0.00125\\0.05&0.05\end{bmatrix},\quad G_1=\begin{bmatrix}0.00125&0\\0.05&0\end{bmatrix},\quad E=G_0.$$

先对不确定集求每个终点分量的精确支持函数。集合中心对称，故最坏绝对偏差半径 R=(0.00012 m,0.0021 m/s)。这里两个分量系数均非负，常值外扰 ±0.02 已取得极值；变化率约束在本例的支持函数上不活跃。

定义模型专属的鲁棒控制序列集合：

$$\mathcal U_d(r)=\{U\in[-2,2]^2:\ |G_dU-r|+R\le(0.0002,0.003)^T\}.$$

共同序列集合为所有 U_d 的交集。第一步动作集合 A_d 是 U_d 在 u0 轴上的投影。交集为空意味着没有共同的开环序列；A_d 的交集为空更强，意味着这些鲁棒开环计划在当前动作上冲突。一般而言，开环投影相交不能保证存在满足所有候选的反馈策略，开环投影不相交也不能直接排除自适应反馈。下面另用无扰动、精确状态的必要动作集合，证明本次特定冲突场景对因果反馈同样成立。

## 4. 场景与可手算的独立证据

场景 A：r=(0,0)。U=(0,0) 对两个延迟均鲁棒可行；因此这次终点任务不要求消除延迟歧义。这个结论不自动推广到无限时域。

场景 B：r=(0.002,0.08)。每个模型单独可行：d=0 可用 U=(0,1.6)，d=1 可用 U=(1.6,0)。两者终点中心恰好等于目标，加上 R 后仍在容差内。d=1 的 u1 不影响本次终点，将它置零；不声称该动作保证后续任务安全。

更强的冲突证明无需依赖优化器或外扰。取允许的 x0=0、w=0、e=0。d=1 必须满足 v2=0.05u0，故 u0∈[1.54,1.66]。d=0 必有 p2−0.025v2=0.0025u0；目标恰有 p*−0.025v*=0，故 u0∈[−0.11,0.11]。两集合间隔 1.43 m/s²，没有共同第一步动作。

两个世界具有相同历史，任何因果控制器在 k=0 必须发出相同 u0。无论 k=1 得到什么信息，第二步动作都无法消除上述必要条件冲突。因此从当前信息出发，没有能够保证两模型都满足该硬期限的因果控制策略。随机化也不能给出逐情形的确定性保证。

## 5. 本次回答与尚未回答的问题

已回答：同样的延迟歧义，对保持任务可以无害，对另一个任务可以造成不可挽回的当前动作冲突。已知延迟的可行性与未知延迟的可行性确实不同。

未回答：如何主动辨识、何时触发、能否在任务开始前及时辨识、长时闭环性能是否更好、变化率预算如何影响识别。冲突不等于“此时增加探测就能补救”。下一阶段应引入目标预告时间、任务松弛或更长时域，检查获取信息是否真的能改变可行性，并与被动反馈/鲁棒控制公平对比。这两个构造例子只支撑研究动机，不是论文创新证明。
'''

EN=r'''# Problem definition v0.1: task-relevant input-delay ambiguity

Date: 2026-11-04. Scope: constructed feasibility witnesses, not a new identification algorithm or a verified novelty claim.

## Dynamics and information

Use the existing one-dimensional double integrator x[k+1]=A x[k]+B(u[k-d]+w[k]), y[k]=x[k]+e[k], with x=(position,velocity), A=[[1,.05],[0,1]], B=[.00125,.05]^T and dt=.05 s. The unknown delay d∈{0,1} remains fixed over the observation window and task. Commands are bounded by 2 m/s². Acceleration disturbances satisfy |w|≤.02 m/s² and |w[k+1]−w[k]|≤.01 m/s² per sample. Componentwise measurement error bounds are 1e-5 m and 1e-4 m/s, without stochastic assumptions.

The controller knows the model, bounds, goal, sample-indexed measurements and its own sent commands. It cannot access the actual delay, disturbances, state or execution timestamps. Evaluation truth is excluded from inference and optimization inputs.

## Historical compatibility

Set all historical commands, including pre-window commands, to zero and measured states y[-6..0]=0. A delay belongs to C if there exists a state/disturbance trajectory satisfying the dynamics, error bounds and disturbance amplitude/rate constraints over this history. Linear feasibility programs verify both candidates. The explicit common witness x=w=e=0 establishes C={0,1}. This deliberately unexcited window is not a claim about arbitrary data.

## Task and future uncertainty

At k=0, a target r=(p*,v*) arrives. At k=2 (0.1 s), require position error ≤.0002 m and velocity error ≤.003 m/s. There are no intermediate state constraints and no requirement beyond this endpoint. No infinite-horizon safety or stability claim is made.

The future uncertainty set is the product of the current measurement-error box and the bounded, rate-constrained disturbance sequence (w0,w1). It conservatively contains the history-conditioned possibilities: the cross-boundary disturbance rate and historical state/disturbance correlations are omitted. Robust success over this outer envelope implies success for the conditioned subset.

Write x2=A²x0+G_d U+Ew with U=(u0,u1),
G0=[[.00375,.00125],[.05,.05]], G1=[[.00125,0],[.05,0]], E=G0.
Exact componentwise support functions give terminal uncertainty radii R=(.00012 m,.0021 m/s). Symmetry gives the corresponding negative supports. Constant extreme disturbances attain both supports, so the rate limit is inactive in these witnesses.

Define U_d(r)={U∈[-2,2]²: |G_d U−r|+R≤(.0002,.003)}. The common open-loop sequence set is their intersection. Let A_d be the projection onto u0. Empty first-action intersection is stronger than empty sequence intersection for these open-loop plans. Generally these open-loop conditions do not fully characterize adaptive feedback: intersection alone does not ensure a common feedback policy, and disjoint robust open-loop projections alone need not rule out adaptation. The specific impossibility below instead follows from nominal necessary conditions.

## Two witnesses and independent algebra

A — harmless ambiguity: r=(0,0). The common sequence U=(0,0) is robustly feasible for both delays. Identification is unnecessary for this endpoint task, with no extension to indefinite regulation implied.

B — conflicting task: r=(.002 m,.08 m/s). Each delay separately admits a robust sequence: U=(0,1.6) for d=0 and U=(1.6,0) for d=1. Both nominal terminal centers equal the goal and the uncertainty radii fit within tolerance. The last command under d=1 has no influence within the horizon and is set to zero; post-horizon behavior is outside scope.

For an optimizer-independent impossibility proof, use the admissible exact-zero state/noise/disturbance realization. Under d=1, v2=.05u0 requires u0∈[1.54,1.66]. Under d=0, p2−.025v2=.0025u0, while p*−.025v*=0, so the tolerances require u0∈[-.11,.11]. These necessary intervals are disjoint with gap 1.43 m/s².

The indistinguishable histories force any causal controller to choose the same first action in both worlds. No second-step feedback can circumvent the incompatible necessary first actions. Thus no causal policy can guarantee this deadline task under both hypotheses from the stated information. Randomization does not restore a deterministic, all-realizations guarantee.

## Interpretation and next question

Identical delay ambiguity can be harmless for one task and decisive for another. These examples do not show that probing after the conflicting task arrives can solve it: information may already be too late. A subsequent study must introduce goal preview, deadline relaxation or a longer horizon, then test whether acquiring information changes feasibility relative to robust and passive adaptive feedback. Active identification, trigger design, long-run performance and the effect of disturbance-rate budgets remain untested. The witnesses motivate research; they do not establish originality.
'''

def main():
    out=ROOT/'results'/'task_ambiguity_scenarios'
    s=json.loads((out/'summary.json').read_text(encoding='utf-8'))
    assert s['source_sha256']==hashlib.sha256((ROOT/'task_ambiguity_scenarios.py').read_bytes()).hexdigest()
    report=ROOT/'report';report.mkdir(exist_ok=True)
    (report/'TASK_AMBIGUITY_PROBLEM_DEFINITION.md').write_text(ZH,encoding='utf-8')
    (report/'TASK_AMBIGUITY_PROBLEM_DEFINITION_EN.md').write_text(EN,encoding='utf-8')
    table='| Scenario | d=0 robust first-action interval | d=1 robust first-action interval | Common robust plan |\n|---|---|---|---|\n'
    for name,r in s['scenarios'].items():
        intervals=[r['individual_robust'][str(d)]['first_action_interval'] for d in (0,1)]
        table+=f"| {name} | [{intervals[0][0]:.3f}, {intervals[0][1]:.3f}] | [{intervals[1][0]:.3f}, {intervals[1][1]:.3f}] | {r['common_robust']['feasible']} |\n"
    common=f'''\n{table}\n![First-action intervals](../results/task_ambiguity_scenarios/first_action_sets.png)

Source SHA-256: `{s['source_sha256']}`.

Environment: Python {s['versions']['python']}, NumPy {s['versions']['numpy']}, SciPy {s['versions']['scipy']}; scipy.optimize.linprog / HiGHS. No random sampling is used.
'''
    zh='''# 两个任务相关延迟歧义场景：验证报告

日期：2026-11-04。结果：保持任务存在共同鲁棒控制；短期限移动任务中，两个模型分别鲁棒可行，但第一步动作发生冲突。

## 设置与结果

完整方程、边界和证明见 [问题定义](TASK_AMBIGUITY_PROBLEM_DEFINITION.md)。两场景的系统、历史、输入约束、外扰和噪声边界完全相同，只改变终点目标。候选 d=0/1 均与六步历史相容。预测两步，即 0.1 s。
'''+common+f'''
区间单位为 m/s²，列出的是鲁棒开环计划在第一步动作上的精确 LP 投影，不是经验阈值。当前状态和扰动外包络导致的终点半径为 {s['terminal_uncertainty_radius'][0]:.5f} m 和 {s['terminal_uncertainty_radius'][1]:.4f} m/s。

## 独立核验

保持目标为 (0,0)，共同零输入在全部不确定性下满足终点要求。冲突目标为 (0.002 m,0.08 m/s)，单模型显式序列 (0,1.6) 与 (1.6,0) 分别鲁棒满足要求。

不用求解器也可证明冲突：无扰动、精确状态条件下，d=0 必须 u0∈[−0.11,0.11]，d=1 必须 u0∈[1.54,1.66]。必要区间间隔 {s['nominal_first_action_gap']:.2f} m/s²。无论下一步如何反馈，当前共同动作都无法同时满足两个世界的任务。

支持函数 LP 检查连续不确定集，逐步物理递推验证预测矩阵，手算必要区间独立检查 LP 结果。另保存 {s['cross_checks']} 次确定性组合检查，包含两个计划假设、两个实际延迟、当前误差角点及满足变化率的扰动网格；其中正确模型计划的位置最大违反 {s['matched_plan_max_position_violation_m']:.3g} m，速度最大违反 {s['matched_plan_max_velocity_violation_m_s']:.3g} m/s（浮点舍入量级）。有限网格仅作补充，不代替支持函数证据。四项针对性测试及完整回归记录见 task_ambiguity_tests.log。

## 边界与下一步

这是构造性可行性证据，不是完整闭环控制器对比。第一步的必要动作冲突证明适用于本例的因果策略；不能将一般的共同开环计划不可行直接解释成所有反馈策略不可行。变化率约束虽写入可行性问题，但在本例支持函数上不活跃，因此本例不证明针对变化外扰的新贡献。

两步硬期限刻意放大任务差异，未校准真实硬件。未来不确定集为历史条件集的保守外包络；没有终点后的安全/稳定保证。主动辨识尚未实现，而冲突任务在当前时刻已无法保证；下一步应增加目标预告时间，检验提前获取信息能否改变任务可行性，并比较被动反馈。

## 文件与运行

代码 task_ambiguity_scenarios.py；定义/报告生成器 summarize_task_ambiguity.py；测试 test_task_ambiguity_scenarios.py。输出目录 results/task_ambiguity_scenarios 包含 summary.json、cross_model_checks.csv、first_action_sets.png；CSV 的位置和速度违反分别保留物理单位。

运行：`.\\.venv\\Scripts\\python.exe -B task_ambiguity_scenarios.py`，然后 `.\\.venv\\Scripts\\python.exe -B summarize_task_ambiguity.py`。测试：`.\\.venv\\Scripts\\python.exe -B -m unittest -v`。既有实验结果未重跑或覆盖。
'''
    en='''# Verification report: two task-relevant delay-ambiguity scenarios

Date: 2026-11-04. Outcome: a common robust plan exists for stationary regulation, whereas the short-deadline motion task has conflicting necessary first actions despite separate robust feasibility.

## Setup and results

See the [problem definition](TASK_AMBIGUITY_PROBLEM_DEFINITION_EN.md) for equations, assumptions and proof. Both cases share the dynamics, history, uncertainty sets and command limits. Only the terminal goal changes. Both delays are compatible with six observed transitions. The prediction horizon is two steps (0.1 s).
'''+common+f'''
Intervals are exact LP projections of robust open-loop plans onto the first command, in m/s². The terminal uncertainty radii are {s['terminal_uncertainty_radius'][0]:.5f} m and {s['terminal_uncertainty_radius'][1]:.4f} m/s.

## Independent verification

For target (0,0), the common zero sequence meets the task for every allowed uncertainty. For target (.002 m,.08 m/s), explicit model-specific sequences (0,1.6) and (1.6,0) robustly meet their respective tasks.

Nominal algebra independently gives necessary first-action intervals [-.11,.11] and [1.54,1.66], separated by {s['nominal_first_action_gap']:.2f} m/s². Identical histories force a common first action, and no second-step feedback can repair this particular contradiction.

Continuous uncertainty is checked via support-function LPs. Physical recurrences independently check the lifted prediction matrices; hand-derived intervals check the optimizer. A supplementary deterministic grid contains {s['cross_checks']} cross-model checks using initial error corners and admissible disturbance values. Matched-model plans have maximum position violation {s['matched_plan_max_position_violation_m']:.3g} m and velocity violation {s['matched_plan_max_velocity_violation_m_s']:.3g} m/s, at floating-point roundoff scale. This finite grid does not replace support-function verification. Four targeted tests and the full regression record are saved in task_ambiguity_tests.log.

## Limits and next experiment

These are constructed feasibility witnesses, not a full closed-loop controller comparison. The causal impossibility follows from nominal necessary first-action conditions specific to this case, not merely from infeasibility of a common open-loop sequence. The disturbance-rate constraint is inactive in the terminal support extrema; this experiment establishes no new result about varying disturbances.

The short deadline is deliberately demanding and not hardware calibrated. Future uncertainty is a conservative outer envelope of the historical conditional set. There is no post-terminal safety/stability guarantee. Active identification has not been implemented; after the conflicting task arrives, guaranteed completion is already impossible. A subsequent experiment must introduce goal preview and test whether earlier information acquisition restores feasibility compared with passive feedback.

## Artifacts and reproduction

Implementation: task_ambiguity_scenarios.py. Definition/report generator: summarize_task_ambiguity.py. Tests: test_task_ambiguity_scenarios.py. Data: results/task_ambiguity_scenarios/summary.json, cross_model_checks.csv, first_action_sets.png. Position and velocity violations retain separate physical units.

Run `.\\.venv\\Scripts\\python.exe -B task_ambiguity_scenarios.py`, then `.\\.venv\\Scripts\\python.exe -B summarize_task_ambiguity.py`. Tests: `.\\.venv\\Scripts\\python.exe -B -m unittest -v`. Historical experiment outputs were not rerun or overwritten.
'''
    (report/'TASK_AMBIGUITY_SCENARIOS_REPORT.md').write_text(zh,encoding='utf-8')
    (report/'TASK_AMBIGUITY_SCENARIOS_REPORT_EN.md').write_text(en,encoding='utf-8')
    print('Saved bilingual definitions and verification reports.')

if __name__=='__main__':main()
