"""Report and scientific figures from frozen fixed-batch results; no retuning."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Circle

ROOT=Path(__file__).resolve().parent;O=ROOT/'results'/'push_t_fixed_batch';R=ROOT/'report'
def read(name):return json.loads((O/name).read_text(encoding='utf8'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    m=read('manifest.json');quality=read('cpu_quality.json')+read('gpu_quality.json');times=read('cpu_timings.json')+read('gpu_timings.json')
    names=['fine_serial','fine_cpu8','coarse_cpu8','coarse_top8','coarse_empirical_interval','contact_segment','fixed_segment','cached_proposal','warp_fine','warp_coarse']
    summary=[]
    for name in names:
        tt=[t for t in times if t['method']==name and t['split']=='test'];qq=[q for q in quality if q['method']==name and q['split']=='test']
        arr=np.array([t['total_seconds']*1000 for t in tt]);reg=np.array([q['regret'] for q in qq])
        summary.append(dict(method=name,p50_ms=float(np.median(arr)),p95_ms=float(np.percentile(arr,95)),p99_ms=float(np.percentile(arr,99)),
            mean_regret=float(reg.mean()),max_regret=float(reg.max()),exact_winners=sum(q['exact_winner'] for q in qq),test_batches=len(qq),timing_repeats=len(arr)))
    ref=np.load(O/'reference.npz');cal=read('frozen_calibration.json');diag=read('event_diagnostics.json')[8:]
    reference_checks=cal['reference_checks'][8:]
    empirical_violations=int(np.sum(np.abs(ref['coarse_costs'][8:]-ref['costs'][8:])>cal['empirical_cost_error']+1e-12))
    fine=[t for t in times if t['method']=='fine_cpu8' and t['split']=='test']
    physics_share=float(np.median([t['physics']/t['total_seconds'] for t in fine]))
    native=read('native_profile.json')['timers'];profile_collision=native['mjTIMER_POS_COLLISION']['seconds']/native['mjTIMER_STEP']['seconds']
    speed=1-next(s['p95_ms'] for s in summary if s['method']=='coarse_top8')/next(s['p95_ms'] for s in summary if s['method']=='fine_cpu8')
    fixed_before=np.load(O/'pilot_v0'/'frozen_batches.npz');fixed_now=np.load(O/'frozen_batches.npz')
    unchanged=all(np.array_equal(fixed_before[k],fixed_now[k]) for k in fixed_now.files)
    assert unchanged
    stats=dict(methods=summary,native_rollout_median_share=physics_share,instrumented_collision_share=profile_collision,
       mean_event_window_fraction=float(np.mean([d['event_window_fraction'] for d in diag])),
       mean_positive_error_growth_in_event_windows=float(np.mean([d['positive_error_growth_in_event_windows'] for d in diag])),
       empirical_interval_test_violations=empirical_violations,empirical_interval_test_count=512,
       halfstep_winner_changes=sum(r['fine_best']!=r['halfstep_best'] for r in reference_checks),
       halfstep_max_cost_difference=max(r['halfstep_max_error'] for r in reference_checks),
       coarse_top8_p95_reduction=speed,fixture_identical_after_warmstart_fix=unchanged,
       decision='Mechanism reproduced at small scale; generic coarse top-8 succeeds here; proposed contact-segment heuristic fails the speed gate; no novelty or general certificate established.')
    (O/'summary.json').write_text(json.dumps(stats,indent=2),encoding='utf8')
    table='| Method | p50 ms | p95 ms | Mean regret | Max regret | Same winner / 8 |\n|---|---:|---:|---:|---:|---:|\n'
    for s in summary:table+=f"| {s['method']} | {s['p50_ms']:.2f} | {s['p95_ms']:.2f} | {s['mean_regret']:.6f} | {s['max_regret']:.6f} | {s['exact_winners']} |\n"
    zh=f'''# 固定候选批次：Push-T类接触推动瓶颈复现实验

日期：2026-11-04。这是自建最小MuJoCo任务的机制复现，不是Oxford GPC论文、标准Push-T任务或实机控制器的精确复现。以下全部数字来自本机本轮测量。

## 结论

**轨迹评估是该小任务的主要计算开销；但现成的“粗评全部、精评前8名”已提供有效加速，尚未显示需要新的接触感知算法。** 接触片段细化启发式没有通过速度门槛。当前结果不支持直接声称独立RA-L创新。

8线程精细CPU相对串行有明显收益；普通粗筛前8策略在8个测试批次均选择与精细参考相同的候选，p95时间减少{speed:.1%}。这只是有限样本的排名保持，不是误差证书，也不是闭环成功率。对照门槛应提高到打败这个简单方法，而不是仅打败全精细串行实现。

## 冻结协议与任务

- 16个批次：8开发、8测试；每批64条固定控制序列，总计1024条不同状态-动作配对。四类状态为approach、near_contact、stem、corner，每个集合每类2个。
- 每条序列20个控制段，每段0.05秒，总时域1秒。精细步长0.0025秒（400步），粗步长0.01秒（100步）；额外0.00125秒用于参考敏感性检查。
- 几何为两块矩形组成的T物体和圆柱推杆。物体受平面x/y/yaw关节约束；关节阻尼与摩擦损耗近似桌面阻力，没有真实机械臂、障碍物、视觉或桌面接触模型。不能将本轮扩展成已证明绕障性能。
- 目标为随机固定位置/角度，代价在相同的控制段终点计算，包含位置、姿态、输入代价与终点权重。不同步长不改变成本采样时刻。成本单位为此自定义加权目标的无量纲数值。
- 候选在任何结果计算前冻结，开发/测试集合及种子见manifest.json。测试集未用于调整top8、接触阈值或经验误差上界。
- 每方法每批计时3次；CPU方法顺序打乱，GPU后端单独运行。p95由测试集合24次调用计算，是描述统计，8个批次才是独立场景单位。未给出显著性或置信度结论。

## 测试批次结果

{table}

regret = 精细CPU参考下被选候选成本减去同批精细参考最优成本。GPU也按同一CPU参考计分，并不将后端差异隐藏在各自参考里。

## 各方法实际做了什么

- fine_serial/fine_cpu8：同一个MuJoCo原生C++ rollout接口，1/8线程；不是Python逐步循环的弱基线。
- coarse_cpu8：同批全部粗评，直接选择。
- coarse_top8：粗评后固定精评成本最低的8条，在精评结果中选最优；全部粗评与精评开销均计入。
- coarse_empirical_interval：开发集最大成本误差作为经验半宽，精评可能竞争的候选；**不是可靠上界或统计保证**。测试候选中有{empirical_violations}/512条误差超出开发半宽。
- contact_segment：先粗评，再按接触信号/几何间隙与相邻段决定细化，重跑混合轨迹；无精细真值泄漏，但多次调用、分组和重跑开销可能超过收益。没有认证误差界。
- fixed_segment：每隔一段用精细步长，作为固定细化对照。
- cached_proposal：在位移3毫米、角度偏移0.02弧度的旧状态离线计算相同候选的成本；在线选缓存第一名，只精评这一个。计时不含离线缓存构造；这不是完整缓存MPC，也不保证当前状态下的最优性或安全。
- warp_fine/warp_coarse：RTX5070 Laptop上的MuJoCo Warp，CUDA图、预热、同步，包含重置、输入传输、输出回传和成本。单批64条轨迹，float32与CPU float64/求解后端不同；观察到成本/排名差异，不能将它宣称为质量完全等价的GPU替代。未进行大批量或充分后端调优，不代表GPU普遍比CPU慢。

## 瓶颈与误差是否集中在接触片段

精细8线程调用中，原生rollout部分占总时间的中位数为{physics_share:.1%}，其余为控制展开、输出分配/检查及代价计算。rollout时间含状态记录，不应全部称为碰撞时间。

单条插桩轨迹的碰撞计时占STEP约{profile_collision:.1%}；计时器嵌套不可相加，Python时间回调也有扰动。这不是全测试集碰撞耗时占比，更不是复现了Oxford的90%碰撞开销。未开启渲染。

按精细轨迹的接触建立/脱离事件及左右相邻段，事件窗口平均覆盖{stats['mean_event_window_fraction']:.1%}的候选-时间段；其中包含的正状态误差增长平均为{stats['mean_positive_error_growth_in_event_windows']:.1%}。这是事后相关性，误差使用1米/1弧度归一化；不是因果归因，也不证明只细化这些片段足够。事件真值没有输入在线启发式。

## 数值审计与修正记录

首次一致性测试发现分段调用丢失求解器warmstart，而连续调用保留该内部数值状态。pilot_v0保留首轮代码、数据和失败测试。最终所有方法统一关闭solver warmstart，重新冻结模型、重跑CPU/GPU；所有状态、目标和控制数组与首轮逐元素一致。分段全精细与连续全精细、串行与并行均通过针对性一致性检查。

禁用warmstart是为隔离积分细化效应，不能推断已打败调优后的热启动求解器。最终有7项针对性测试，包括逐步mj_step独立复核、几何间隙、冻结划分、后端排名记录等，结果见test_results.txt。GPU运行日志保留首次编译记录在pilot_v0，最终计时排除编译预热。

参考敏感性：将精细步长再减半，测试批次有{stats['halfstep_winner_changes']}/8个最优候选改变；候选最大成本差为{stats['halfstep_max_cost_difference']:.6f}。因此fine仅是明确定义的离散参考，不能当作物理真值。所有结果应按这一范围解读。

## 去留与下一步

本轮完成固定批次、CPU/GPU和多种启发式的实际对照。尚未实现管束/抽象基线、正式多精度BAI算法、闭环机器人任务或可靠误差包络，不能把它们记作失败。经验区间筛选只是简化工程对照。

最有价值的下一步是检验普通top8筛选在独立的更困难场景中何时会漏掉真正好候选，并检查是否存在廉价、有效的漏选识别方法。不能根据本轮成功样本宣布原创，也不应立刻叠加神经网络。若top8等简单方案始终满足任务需求，新的接触片段算法缺乏必要性。

## 文件与复现

代码：push_t_fixed_batch.py、push_t_gpu_batch.py、analyze_push_t_fixed_batch.py、test_push_t_fixed_batch.py。独立环境.venv-contact；requirements-contact-lock.txt记录版本，未修改旧环境。

数据：results/push_t_fixed_batch/。包含冻结NPZ/XML/清单、精细状态与接触记录、全部候选参考/粗成本、开发校准、CPU/GPU逐次时间与质量、事件诊断、日志和图。图为benchmark.png与scenes.png。

执行：已有冻结批次上运行 `.venv-contact\\Scripts\\python.exe push_t_fixed_batch.py cpu`，随后同环境运行 `push_t_gpu_batch.py` 与 `-m unittest test_push_t_fixed_batch -v`。图文生成器使用已有科研环境 `.venv\\Scripts\\python.exe analyze_push_t_fixed_batch.py`。freeze拒绝覆盖已有批次；重跑会改写当前结果，若要保留本次输出应先归档。

后端依据：[MuJoCo原生rollout文档](https://mujoco.readthedocs.io/en/stable/python.html)、[MuJoCo Warp文档](https://mujoco.readthedocs.io/en/stable/mjwarp/index.html)。本机没有WSL；[JAX官方平台表](https://docs.jax.dev/en/latest/installation.html)不支持原生Windows NVIDIA GPU，因此本轮GPU采用Warp。
'''
    en=f'''# Fixed candidate batches: Push-T-style contact-evaluation bottleneck

Date: 2026-11-04. A constructed minimal MuJoCo mechanism replication, not an exact Oxford GPC, standard Push-T or hardware-controller reproduction. All numbers below were measured locally.

## Outcome

Trajectory evaluation dominates this small workload, but the generic coarse-screen/top-8-fine method already improves latency without changing the winner on the eight held-out batches. Its total p95 reduction versus native eight-thread fine CPU is {speed:.1%}. This is empirical finite-batch agreement, not a certificate or closed-loop success result. The contact-segment heuristic fails the speed gate. No independent RA-L novelty has been established.

## Frozen protocol

Sixteen snapshots: eight development and eight test, four contact regimes with two instances per split. Each batch contains 64 frozen velocity sequences (1024 distinct state/control pairs), 20 control intervals of 0.05s, horizon 1s. Fine/coarse steps are 0.0025/0.01s; an additional 0.00125s reference sensitivity check is retained. Costs are sampled at identical control-stage endpoints and use weighted position, yaw, effort and terminal terms.

The T object is two boxes, constrained to planar translation/yaw; the pusher is cylindrical. Joint damping/friction approximate planar drag. There is no full arm, obstacle, vision, or table-contact model. No obstacle-task conclusion follows. Candidate arrays and splits were frozen before evaluation. Top-8, geometric threshold and empirical development error were not tuned on test snapshots.

Each method/batch is timed three times. CPU method order is randomized; GPU runs are separate. Test p95 pools 24 calls, while eight scenarios are the independent units. These are descriptive timings, not inferential confidence intervals.

## Held-out results

{table}

Regret is the chosen candidate's fine CPU-reference cost minus the best fine cost within that same batch. GPU decisions are also scored against this common reference; backend discrepancies are not hidden.

## Implemented methods

- fine_serial/fine_cpu8: native C++ MuJoCo rollout on one/eight threads, not a weak Python stepping baseline.
- coarse_cpu8: evaluate all candidates coarsely and select directly.
- coarse_top8: evaluate all coarsely, reevaluate the cheapest eight finely, then select among those eight. Both phases are timed.
- coarse_empirical_interval: use the largest development cost error as a heuristic interval halfwidth and refine possible competitors. This is NOT a verified or statistical bound; {empirical_violations}/512 test candidates exceed it.
- contact_segment: coarse contact/geometry screening, neighboring-stage dilation, then a mixed-step rerun. No fine-reference leakage. Dispatch, grouping and rerun costs are included. There is no certified enclosure.
- fixed_segment: alternate fine and coarse intervals.
- cached_proposal: offline costs at a state shifted by 3mm and 0.02rad, with identical candidate actions; choose its winner and finely evaluate just that proposal online. Offline build cost is excluded. This is not a complete cache-MPC baseline or an optimality/safety certificate.
- warp_fine/warp_coarse: RTX5070 Laptop, MuJoCo Warp, graph capture, warmup and synchronization. Timing includes reset, transfers, output and cost evaluation. Float32 and backend differences cause observed ranking/cost differences versus float64 CPU. This is a 64-world small-batch baseline, not evidence that GPU simulation is generally slower; large-batch and backend tuning were not performed.

## Bottleneck and event association

The median native rollout fraction of total fine-eight-thread time is {physics_share:.1%}. It includes state recording; it is not all collision handling. An instrumented single trajectory gives collision/STEP approximately {profile_collision:.1%}. Timers overlap and a Python clock callback perturbs them, so this is not an aggregate workload share or a reproduction of Oxford's percentage. Rendering is excluded.

Reference contact-onset/release windows, dilated one stage each way, occupy on average {stats['mean_event_window_fraction']:.1%} of candidate-stage pairs and contain {stats['mean_positive_error_growth_in_event_windows']:.1%} of positive state-error growth. This is retrospective association, not causal attribution or proof that refining only those windows suffices. State error uses normalization of 1m and 1rad. Fine event information was not used by online heuristics.

## Numerical audit and correction

The first stitching test exposed solver warmstart-state loss between native rollout calls. pilot_v0 preserves all initial code/results and the failing test. Final CPU/GPU models uniformly disable solver warmstart to isolate step-size effects. Frozen state/goal/control arrays are elementwise unchanged. All-fine stitched and continuous rollouts now agree, as do serial/parallel runs. This comparison does not establish superiority over a tuned warm-start solver.

Seven targeted tests cover direct mj_step replay, thread/stage consistency, geometry, frozen split, costs, contact records and saved GPU rankings. Compilation/warmup is excluded from steady-state measurements; first compilation logs remain in pilot_v0. Half-step sensitivity changes the winner in {stats['halfstep_winner_changes']}/8 test batches; the maximum candidate cost difference is {stats['halfstep_max_cost_difference']:.6f}. Fine is therefore a defined discrete reference, not physical truth.

## Research decision

The requested fixed-batch experiment has CPU/GPU and heuristic comparisons. Tube/abstraction baselines, formal multifidelity BAI, closed-loop robot trials and sound cost enclosures are not implemented and are not labeled failures. The empirical-interval filter is only a simplified engineering comparator.

The next meaningful question is whether ordinary top-8 screening misses important candidates on separately frozen harder scenarios, and whether a cheap valid miss detector exists. If simple screening already meets the task needs, a more complicated contact-segment method has no demonstrated necessity. Do not add a network or claim novelty from these successful batches.

## Artifacts and reproduction

Code: push_t_fixed_batch.py, push_t_gpu_batch.py, analyze_push_t_fixed_batch.py, test_push_t_fixed_batch.py. Isolated .venv-contact and requirements-contact-lock.txt; historical environments remain unchanged. Frozen NPZ/XML, all reference states/contact labels/costs, raw timings, quality metrics, calibration, event diagnostics, logs and benchmark/scenes PNGs are under results/push_t_fixed_batch/.

Using the existing fixture, run `.venv-contact\\Scripts\\python.exe push_t_fixed_batch.py cpu`, then the GPU script and targeted unittest in that environment. Generate plots/reports using `.venv\\Scripts\\python.exe analyze_push_t_fixed_batch.py`. freeze refuses to overwrite existing fixtures; archive current results before rerunning evaluation if preservation is required.

Backend references: [native rollout](https://mujoco.readthedocs.io/en/stable/python.html), [MuJoCo Warp](https://mujoco.readthedocs.io/en/stable/mjwarp/index.html), [JAX platform support](https://docs.jax.dev/en/latest/installation.html). WSL is absent and native Windows NVIDIA JAX is unsupported; Warp supplies the GPU baseline.
'''
    (R/'PUSH_T_FIXED_BATCH_REPORT.md').write_text(zh,encoding='utf8');(R/'PUSH_T_FIXED_BATCH_REPORT_EN.md').write_text(en,encoding='utf8')
    plt.rcParams.update({'font.size':10})
    fig,ax=plt.subplots(1,2,figsize=(13,5),layout='constrained')
    ax[0].barh(names,[s['p95_ms'] for s in summary]);ax[0].set_xscale('log');ax[0].set_xlabel('End-to-end p95 latency (ms, log scale)');ax[0].invert_yaxis()
    ax[1].barh(names,[s['mean_regret'] for s in summary],color='#c85f3f');ax[1].set_xlabel('Mean cost regret against CPU fine reference');ax[1].invert_yaxis()
    fig.suptitle('Fixed 64-candidate batches | 8 held-out snapshots | not closed-loop performance')
    fig.savefig(O/'benchmark.png',dpi=170);plt.close(fig)
    f=np.load(O/'frozen_batches.npz');fig,axes=plt.subplots(2,2,figsize=(9,8),layout='constrained')
    for b,ax in zip([8,10,12,14],axes.flat):
        q=f['qpos'][b];theta=q[2];rot=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
        for center,half in [(np.array([0,.055]),np.array([.06,.015])),(np.array([0,-.015]),np.array([.015,.055]))]:
            corners=np.array([[-1,-1],[1,-1],[1,1],[-1,1]])*half+center
            ax.add_patch(Polygon(corners@rot.T+q[:2],color='#578cbf',alpha=.6))
        ax.add_patch(Circle(q[3:5],.015,color='#d05a40'));best=int(np.argmin(ref['costs'][b]))
        for i in range(m['candidates']):ax.plot(ref['states'][b,i,:,4],ref['states'][b,i,:,5],color='gray',alpha=.12,lw=.6)
        ax.plot(ref['states'][b,best,:,4],ref['states'][b,best,:,5],color='#d05a40',label='Fine winner: pusher')
        ax.plot(ref['states'][b,best,:,1],ref['states'][b,best,:,2],color='#244f80',label='Fine winner: object')
        ax.scatter(*f['goals'][b,:2],marker='x',color='green',label='Object target');ax.set_aspect('equal');ax.set_title(m['labels'][b]['family']);ax.set_xlabel('x (m)');ax.set_ylabel('y (m)');ax.grid(alpha=.2)
    axes[0,0].legend(fontsize=8);fig.suptitle('Constructed planar scenes and frozen candidate trajectories')
    fig.savefig(O/'scenes.png',dpi=170);plt.close(fig)
    artifacts={p.name:digest(p) for p in O.iterdir() if p.is_file() and p.name!='artifact_hashes.json'}
    for p in [ROOT/'push_t_fixed_batch.py',ROOT/'push_t_gpu_batch.py',ROOT/'test_push_t_fixed_batch.py',Path(__file__),R/'PUSH_T_FIXED_BATCH_REPORT.md',R/'PUSH_T_FIXED_BATCH_REPORT_EN.md']:artifacts[str(p)]=digest(p)
    (O/'artifact_hashes.json').write_text(json.dumps(artifacts,indent=2),encoding='utf8')
    print(json.dumps(stats,indent=2))

if __name__=='__main__':main()
