"""Generate bilingual reports from saved independent reproduction outputs."""
from pathlib import Path
import hashlib,json
import numpy as np


def main():
    root=Path(__file__).resolve().parent
    out=root/'results'/'common_delay_reproduction'
    record=json.loads((out/'summary.json').read_text())
    assert hashlib.sha256((root/'reproduce_common_delay.py').read_bytes()).hexdigest()==record['source_sha256']
    table='| Delay | Rank | LS residual energy | Remaining budget | Min LMI eigenvalue | Illustrated closed-loop spectral radius |\n|---|---:|---:|---:|---:|---:|\n'
    for d,m in record['audit'].items():
        matrix=np.load(out/f'certificate_delay{d}.npy',allow_pickle=False)
        eig=np.linalg.eigvalsh((matrix+matrix.T)/2).min()
        assert abs(eig-m['certificate']['min_eigenvalue'])<1e-12
        table+=f"| {d} | {m['rank']} | {m['ls_residual']:.9f} | {m['radius_squared']:.9f} | {eig:.9f} | {m['illustrated_spectral_radius']:.6f} |\n"
    info=record['solve_info']
    worst=max(m['sampled_max_spectral_radius'] for m in record['audit'].values())
    en='''# Common-controller baseline: independent protocol reproduction

Date: 2026-11-04. Scope: reproduce the qualitative claim of the numerical example, not author-record bitwise agreement or a new algorithm.

## Source and attribution

[Robust Data-Driven Output Feedback for Systems With Unknown Input Delays, v1](https://arxiv.org/html/2611.00841v1), Section V-B and Theorem 3, Eq. (19). We implemented its compatible-model construction and common-gain LMI. The source makes no arbitrary-switching guarantee, and synthesis applies after data collection without ongoing disturbance. This study reproduces those limited conditions.

## Independently specified implementation

The ARX recurrence is y[k]=1.9*y[k-1]-0.88*y[k-2]+0.2*u[k-3]+0.1*u[k-4]+w[k]. We generate 12 records of length 16, alternating two random input amplitudes in each. NumPy PCG64 seed 806 draws two amplitudes, two initial outputs and fourteen uniform equation errors per record, in that order. Missing past inputs are zero. Columns k=5..15 produce 132 samples. The predetermined selected-equation error-energy bound is 0.0132. Candidates have delays 1,2,3 and history dimensions (2 output,5 input), total seven. SVD constructs the least-squares fit and coefficient ellipsoid for each retained delay.

The common-gain SDP enforces Eq. (19) with shared F,L and candidate-specific P,lambda. First maximize an absolute strict margin with sum(trace(P))=3; then minimize ||L||²+0.001||F||² while retaining half that margin. This secondary surrogate and the random draw order are explicit independent choices because complete author code/data were not supplied. CVXPY and solver versions are recorded, not assumed identical to the paper.

## Results and checks

TABLE

All candidates survive the same predetermined bound. One recovered gain is used without model switching. The illustrated plants have the same denominator; the middle delay uses numerator coefficients (0.2,0.1), and the other two use (0.1,0.2). Each is checked against the collected data. Initial history is (1,0.9,0,0,0,0,0). The plotted output is the most recent STORED output y(k-1); the horizontal axis is a sample index, with no physical sampling time assigned.

NUMERICS

Every returned 18x18 LMI and positive-definite P is reconstructed independently using NumPy. Strictness is checked against 100*n*machine_epsilon*max(1,||matrix||₂); solver status alone is insufficient. Random interior/boundary sampling supplements this check, not a replacement for the LMI. These are floating-point checks, not interval/exact-arithmetic certificates. Trajectories illustrate three compatible plants, not every model by simulation.

## Difference from a numerical duplicate

The original printed LS residual is 0.004189; our independently generated record gives approximately 0.003407089. The paper's printed regressor condition number is 89.44; ours is approximately 89.84044. We did not search seeds/draw orders to match those numbers. The recovered controller and matrix margins can differ. This is protocol-level qualitative reproduction, not exact numerical replication. The study does not reproduce the other numerical example or sensor-noise extension.

## Consequence for the proposed project

The baseline confirms that unresolved delay is compatible with a working common controller. Therefore, candidate retention plus common control is not our novelty. A narrower proposal is saved separately. Ongoing varying disturbances, task constraints and deciding whether to identify remain open design tasks for this project; their absence from this particular example does not prove a literature gap.

## Files and reproduction

Run `.\\.venv\\Scripts\\python.exe -m unittest -v test_common_delay_reproduction`, then `.\\.venv\\Scripts\\python.exe reproduce_common_delay.py`, then `.\\.venv\\Scripts\\python.exe summarize_common_delay.py`. The experiment overwrites only its own output folder on rerun. Dependencies are locked separately in requirements-reproduction-lock.txt, preserving the historical lock file.

results/common_delay_reproduction contains the complete generated data, F/L/K/P matrices, three LMI matrices, trajectories.csv, summary.json and common_controller.png. Tests check equation-error consistency across the three physical examples, ellipsoid factors, history timing and rejection of boundary matrices. Four targeted tests passed before synthesis. The complete regression log is common_delay_full_tests.log. Reports are in report/; one-page plans are RESEARCH_PROPOSAL_ZH.md and RESEARCH_PROPOSAL_EN.md.
'''
    zh='''# 共同控制器基线：论文数值协议独立复现

日期：2026-11-04。范围：复现数值例子的定性结论，不是逐位恢复作者数据，也不是提出新算法。

## 来源与归属

[Robust Data-Driven Output Feedback for Systems With Unknown Input Delays，v1](https://arxiv.org/html/2611.00841v1)，V-B 节、定理 3 与式 (19)。本次实现其相容模型和共同增益 LMI。该结果不保证任意延迟切换，合成对象为采数后无持续扰动的系统。本次保持这些限制。

## 独立实现的明确选择

ARX 递推为 y[k]=1.9*y[k-1]-0.88*y[k-2]+0.2*u[k-3]+0.1*u[k-4]+w[k]。生成 12 条长度 16 的记录，每条交替使用两个随机输入幅值。采用 NumPy PCG64、种子 806，每条依次抽取两个幅值、两个初始输出和十四个均匀方程误差。缺失历史输入为零。选择 k=5..15，共 132 列，选中方程误差能量预设上界 0.0132。候选延迟为 1/2/3，记录两步输出和五步输入，共七维历史状态。用 SVD 构造每个延迟的最小二乘估计和系数椭球。

共同控制器 SDP 使用共享 F/L、每候选独立的 P/lambda，满足式 (19)。第一阶段在 sum(trace(P))=3 下最大化绝对严格裕度；第二阶段保持至少一半裕度，最小化 ||L||²+0.001||F||²。原始作者数据与完整代码未提供，抽样顺序与次级目标为本次明确的独立实现选择。依赖版本见结果记录，不假定与论文完全一致。

## 结果与核验

列为延迟、秩、拟合残差能量、剩余预算、LMI 最小特征值、展示模型闭环谱半径。

TABLE

三个候选均满足相同预设误差上界。恢复一个共同增益，不按模型切换。展示对象分母一致，中间延迟用分子系数 (0.2,0.1)，另两个用 (0.1,0.2)，逐一核对它们与采集数据相容。初始历史状态 (1,0.9,0,0,0,0,0)。图中为最近一次已存储输出 y(k-1)，横轴为离散样本索引，没有指定物理周期。

NUMERICS

独立用 NumPy 重建每个 18x18 LMI 与 P，检查最小特征值大于 100*n*机器精度*max(1,矩阵二范数)，不把求解器成功直接视为证书。椭球内部/边界随机抽样只作补充，不能代替 LMI。这是浮点核验，不是区间/精确算术证明。三条轨迹展示具体相容对象，不能通过这三条仿真声称已枚举整个椭球。

## 与逐项数值复刻的区别

原文打印的拟合残差能量为 0.004189，本次独立数据约为 0.003407089；原文条件数 89.44，本次约 89.84044。没有搜索随机种子或调用顺序去匹配数字。共同增益和矩阵裕度也可不同。因此标记为协议级、定性独立复现，不声称精确数值复刻。没有复现论文的另一数值例子或传感器噪声扩展。

## 对项目的含义

基线证实延迟仍有歧义时可以存在共同稳定控制器，因此“保留候选再控制”不是本项目创新。另存一页研究计划。持续变化外扰、任务约束和何时值得辨识仍是本项目需要解决的问题；它们未出现在这个例子中，不代表整个文献没有覆盖。

## 文件与复现

运行 `.\\.venv\\Scripts\\python.exe -m unittest -v test_common_delay_reproduction`，再运行 `.\\.venv\\Scripts\\python.exe reproduce_common_delay.py` 和 `.\\.venv\\Scripts\\python.exe summarize_common_delay.py`。重跑仅覆盖本实验输出目录。新增依赖锁定在 requirements-reproduction-lock.txt，保留原历史锁定文件。

results/common_delay_reproduction 保存全部生成数据、F/L/K/P、三个 LMI 矩阵、轨迹 CSV、summary.json 和 common_controller.png。四个针对性测试已在合成前通过，覆盖三对象方程误差一致性、椭球因子、历史时序、边界矩阵拒绝。完整回归记录见 common_delay_full_tests.log。报告位于 report；一页计划为 RESEARCH_PROPOSAL_ZH.md 与 RESEARCH_PROPOSAL_EN.md。
'''
    numeric_en=(f"The first-stage strict margin is {info['first_margin']:.9g}, and the second retains "
        f"{info['secondary_margin']:.9g}. All illustrated open-loop spectral radii are 1.1. "
        f"The maximum sampled closed-loop radius across 3000 ellipsoid points is {worst:.6f}, below one.")
    numeric_zh=(f"第一阶段严格裕度 {info['first_margin']:.9g}，第二阶段保持 "
        f"{info['secondary_margin']:.9g}。展示对象的开环谱半径均为 1.1；"
        f"3000 个椭球抽样点的闭环最大谱半径 {worst:.6f}，小于一。")
    report=root/'report'; report.mkdir(exist_ok=True)
    (report/'COMMON_DELAY_REPRODUCTION_REPORT.md').write_text(zh.replace('TABLE',table).replace('NUMERICS',numeric_zh),encoding='utf-8')
    (report/'COMMON_DELAY_REPRODUCTION_REPORT_EN.md').write_text(en.replace('TABLE',table).replace('NUMERICS',numeric_en),encoding='utf-8')
    print('Bilingual reports generated from saved outputs and verified matrices.')


if __name__=='__main__': main()
