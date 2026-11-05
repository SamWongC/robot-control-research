"""Audit first-action scan, derive causal obstruction, create bilingual reports."""
from pathlib import Path
import csv,hashlib,json
import numpy as np

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'/'first_action_scan'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def branch_interval(a,w0,w1,w2):
    """Allowed second command b, exact initial zero and d=1, fixed future.

    The third command is pending after the deadline and cannot change x3.
    """
    offp=.00375*a+.00625*w0+.00375*w1+.00125*w2
    offv=.05*(a+w0+w1+w2)
    lo=max(-2.,(.002-.0002-offp)/.00125,(.08-.003-offv)/.05)
    hi=min(2.,(.002+.0002-offp)/.00125,(.08+.003-offv)/.05)
    return [float(lo),float(hi)]

def audit_phase(phase):
    folder=OUT/phase;episodes=read(folder/'episodes.json');data=np.load(folder/'paired_inputs.npz')
    ws={str(n):w for n,w in zip(data['names'],data['disturbances'])}
    es={str(n):e for n,e in zip(data['names'],data['measurement_errors'])}
    groups={}
    with (folder/'trajectories.csv').open(newline='') as f:
        for r in csv.DictReader(f):groups.setdefault((r['rule'],r['case'],int(r['true_delay'])),[]).append(r)
    maxres=0.;steps=0
    for m in episodes:
        rr=groups[(m['rule'],m['case'],m['true_delay'])];assert len(rr)==3
        state=np.zeros(2);history=[]
        for k,r in enumerate(rr):
            assert int(r['k'])==k
            x=np.array([float(r['p']),float(r['v'])]);nx=np.array([float(r['next_p']),float(r['next_v'])])
            np.testing.assert_allclose(x,state,atol=1e-12,rtol=0)
            u=float(r['command']);applied=float(r['applied']);w=float(r['disturbance'])
            assert abs(u)<=2+1e-10 and abs(w-ws[m['case']][k])<1e-13
            expected_applied=u if m['true_delay']==0 else (history[-1] if history else 0.)
            assert abs(applied-expected_applied)<1e-13
            expected=x+np.array([.05*x[1]+.00125*(applied+w),.05*(applied+w)])
            maxres=max(maxres,float(np.max(np.abs(nx-expected))))
            obs=np.array([float(r['measured_p']),float(r['measured_v'])])
            np.testing.assert_allclose(obs,x+es[m['case']][k],atol=1e-13,rtol=0)
            assert str(m['true_delay']) in r['candidates'].split(';')
            if k==0:assert abs(u-m['action'])<1e-13
            if k==1:
                np.testing.assert_allclose(x,m['task_start_state'],atol=1e-13,rtol=0)
                assert len(history)==1 and abs(history[0]-m['task_start_pending_command'])<1e-13
                assert r['candidates'].split(';')==[str(d) for d in m['first_candidates']]
            history.append(u);state=nx;steps+=1
        error=np.abs(state-np.array([.002,.08]))
        np.testing.assert_allclose(error,[m['position_error_m'],m['velocity_error_m_s']],atol=1e-13,rtol=0)
        prep_ok=bool(np.all(np.abs(m['task_start_state'])<=np.array([.01,.06])+1e-10))
        assert prep_ok==m['prep_ok']
        assert bool(prep_ok and np.all(error<=np.array([.0002,.003])+1e-10))==m['success']
        assert abs(.05*m['action']**2-m['prep_energy'])<1e-12
        if m['success']:assert m['hindsight_feasible']
    for g in read(folder/'summary.json'):
        group=[m for m in episodes if m['rule']==g['rule']]
        assert len(group)==g['episodes'] and sum(m['success'] for m in group)==g['success_count']
        assert sum(m['identified_after_first'] for m in group)==g['identified_count']
        assert sum(m['hindsight_feasible'] for m in group)==g['hindsight_feasible_count']
    assert maxres<1e-12
    return {'phase':phase,'episodes':len(episodes),'transitions':steps,'max_scalar_recurrence_residual':maxres,
            'states_measurements_queue_costs_success_and_counts_verified':True,'true_delay_retained':True}

def main():
    config=read(OUT/'config.json');frozen=read(OUT/'frozen_rule.json');prov=read(OUT/'test'/'provenance.json')
    assert digest(ROOT/'first_action_scan.py')==config['source_sha256']==frozen['source_sha256']
    assert digest(OUT/'config.json')==frozen['config_sha256']
    assert digest(OUT/'scan'/'episodes.json')==frozen['scan_episodes_sha256']
    assert digest(OUT/'frozen_rule.json')==prov['frozen_sha256']
    assert digest(OUT/'test'/'paired_inputs.npz')==prov['test_inputs_sha256']
    assert digest(OUT/'test'/'episodes.json')==prov['test_episodes_sha256']
    for p,h in config['dependencies'].items():assert digest(ROOT/p)==h
    best=min(frozen['eligible'],key=lambda c:(-c['success_count'],round(c['prep_energy'],12),-c['action']))
    assert best==frozen['selected']
    scan_data=np.load(OUT/'scan'/'paired_inputs.npz');test_data=np.load(OUT/'test'/'paired_inputs.npz')
    assert not any(np.array_equal(a,b) for a in scan_data['disturbances'] for b in test_data['disturbances'])
    # Also exclude records used in the previous held-out baseline experiment.
    previous=np.load(ROOT/'results'/'baseline_sensitivity'/'test'/'paired_inputs.npz')
    assert not any(np.array_equal(a,b[:3]) for a in test_data['disturbances'] for b in previous['disturbances'])
    audits=[audit_phase(p) for p in ('scan','test')]
    (OUT/'audit.json').write_text(json.dumps({'phases':audits,'hashes_verified':True,
        'selection_recomputed':True,'new_inputs_distinct_from_scan_and_previous_test':True},indent=2),encoding='utf-8')
    # Stronger causal obstruction, retaining the benchmark's exact zero initial
    # state. Give the controller the delay and exact x1: impossibility persists.
    a=best['action'];intervals=[branch_interval(a,.02,.02,.02),branch_interval(a,.02,.01,0.)]
    obstruction={'scope':'Necessary bound for causal control, even with exact initial zero, known delay=1 and exact prefix state.',
        'same_prefix_disturbance':.02,'future_branches':[[.02,.02],[.01,0.]],
        'action':a,'second_command_intervals':intervals,
        'intersection_empty':max(i[0] for i in intervals)>min(i[1] for i in intervals)+1e-12,
        'necessary_abs_action_bound_from_symmetric_branch_pairs':.035,
        'positive_proof':'b>=1.51-a from branch (w1=.01,w2=0); b<=1.58-3a from branch (w1=.02,w2=.02); hence a<=.035.',
        'negative_proof':'Mirror disturbances give b>=1.62-3a and b<=1.69-a; hence a>=-.035.',
        'no_sufficiency_claim':True}
    assert obstruction['intersection_empty']
    (OUT/'causal_obstruction.json').write_text(json.dumps(obstruction,indent=2),encoding='utf-8')
    regions=read(OUT/'regions.json');analytic=read(OUT/'analytic.json');scan=read(OUT/'scan'/'summary.json');test=read(OUT/'test'/'summary.json')
    episodes=read(OUT/'test'/'episodes.json')
    table='| Rule | Mean first action | Success | ID at task start | Hindsight feasible | Known-delay robust plan exists | Hindsight-infeasible failures | Hindsight-feasible failures | Prep energy |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|\n'
    for g in test:
        table+=f"| {g['rule']} | {g['action_mean']:.6f} | {g['success_count']}/{g['episodes']} | {g['identified_count']}/{g['episodes']} | {g['hindsight_feasible_count']}/{g['episodes']} | {g['robust_known_delay_feasible_count']}/{g['episodes']} | {g['hindsight_infeasible_failure_count']} | {g['hindsight_feasible_controller_failure_count']} | {g['mean_prep_energy']:.7f} |\n"
    counterfactuals=[]
    for g in test:
        group=[m for m in episodes if m['rule']==g['rule']]
        counterfactuals.append({'rule':g['rule'],'failed_despite_known_delay_robust_plan':sum(not m['success'] and m['current_robust_known_delay_feasible'] for m in group),
            'note':'Known-delay plan is an oracle diagnostic when the actual candidates remain ambiguous.'})
    (OUT/'failure_diagnostics.json').write_text(json.dumps(counterfactuals,indent=2),encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    colors={'both_nominal':'tab:green','identify_only':'tab:orange','nominal_task_only':'tab:blue','neither':'tab:red','prep_inadmissible':'lightgray'}
    labels={'both_nominal':'ID + known-delay nominal feasibility','identify_only':'ID only','nominal_task_only':'Known-delay nominal feasibility only','neither':'Neither','prep_inadmissible':'Outside robust preparation envelope'}
    for ax,xlim in zip(axes[0],((-2.05,2.05),(-.16,.16))):
        for r in regions:ax.scatter(r['action'],0,c=colors[r['region']],s=35)
        ax.axhline(.6,color='0.8',lw=1)
        ax.plot([-.035,.035],[.6,.6],lw=7,color='purple')
        if xlim[1]<1:
            ax.text(0,.78,'Necessary causal bound (not sufficient)',ha='center',fontsize=9)
        for x in (-.048,.048):ax.axvline(x,color='black',ls='--',alpha=.5)
        ax.set(xlim=xlim,ylim=(-.4,1.2),yticks=[],xlabel='First command a [m/s^2]')
    axes[0,0].set_title('Nominal map: separate known-delay continuations')
    axes[0,1].set_title('Zoom: nominal joint region vs causal necessary bound')
    axes[0,0].legend(handles=[Patch(color=colors[k],label=labels[k]) for k in colors],loc='upper left',fontsize=7)
    scan_sorted=sorted(scan,key=lambda g:g['action_mean'])
    xs=[g['action_mean'] for g in scan_sorted]
    for field,label in [('success_count','Controller completion'),('identified_count','Observed identification'),('hindsight_feasible_count','Hindsight feasibility')]:
        axes[1,0].plot(xs,[100*g[field]/g['episodes'] for g in scan_sorted],label=label)
    axes[1,0].set(xlim=(-.4,.2),ylim=(-5,105),xlabel='First command [m/s^2]',ylabel='Development cases [%]',title='Development scan (zero physical initial state)')
    axes[1,0].axvline(a,color='purple',ls='--',label='Frozen action');axes[1,0].legend(fontsize=8);axes[1,0].grid(alpha=.3)
    names=[g['rule'] for g in test];xx=np.arange(len(names))
    axes[1,1].bar(xx-.18,[100*g['success_count']/g['episodes'] for g in test],width=.36,label='Completion')
    axes[1,1].bar(xx+.18,[100*g['hindsight_feasible_count']/g['episodes'] for g in test],width=.36,label='Hindsight feasibility')
    axes[1,1].set(xticks=xx,xticklabels=names,ylim=(0,110),ylabel='Fresh-test cases [%]',title='Frozen-rule evaluation');axes[1,1].tick_params(axis='x',labelsize=8);axes[1,1].legend(fontsize=8)
    fig.tight_layout();fig.savefig(OUT/'first_action_regions.png',dpi=180);plt.close(fig)
    auditsteps=sum(x['transitions'] for x in audits)
    shared=f'''\n{table}\n\n![First action regions](../results/first_action_scan/first_action_regions.png)

Source SHA-256: `{config['source_sha256']}`.

Frozen-rule SHA-256: `{prov['frozen_sha256']}`.

Python {config['versions']['python']}; NumPy {config['versions']['numpy']}; SciPy {config['versions']['scipy']}; HiGHS via scipy.optimize.linprog.
'''
    zh=f'''# 首步动作：延迟可辨识性与任务可恢复性

日期：2026-11-04。范围：0.05 s 预告、原两步终点任务的机制分析。没有提出新方法或确认创新。

## 核心结果

旧案例扫描后冻结的首步动作是 {a:+.3f} m/s²；128 条全新轨迹配两个延迟时，完成 239/256，固定 +0.1 为 163/256，原任务控制为 128/256。三个非零方案全部在同一首步后辨识正确，表现差异不能解释为更早获得延迟信息。

名义条件下存在既能区分延迟又允许已知延迟后续控制的动作区域。但考虑全部允许外扰，即使初态精确为零、控制器知道延迟并精确观测状态，也没有能同时保证首步辨识与截止任务的固定首步动作：首步辨识阈值为 |a|>0.048，而任务保证的一个必要条件为 |a|≤0.035。后者是必要条件，不把其内部标成保证可行区域。

## 问题与信息

沿用已有双积分器、dt=0.05 s、延迟 d=0/1 固定、输入 |u|≤2 m/s²、外扰 |w|≤0.02 m/s² 且逐步变化 ≤0.01 m/s²、测量误差 (1e-5 m,1e-4 m/s)。预告只持续一步：k=0 发送首步 a，k=1 原任务开始，k=3 截止。绝对目标 (0.002 m,0.08 m/s)，终点容差 (0.0002 m,0.003 m/s)。准备边界 |p1|≤0.01 m、|v1|≤0.06 m/s。

记录首步产生的真实 x1 与待执行指令 a，此后继续原系统，未重置。所有方案在 k=1、2 使用上一轮 legacy 任务控制器和相同的前缀候选 LP 过滤；诊断用真值单独计算，不传给控制器。测试物理初态固定为零，但控制器只有测量盒；下面分别说明精确零初态的名义几何与测量盒下的一致辨识条件。

## 一、首步辨识阈值

由速度增量得到的两假设加速度区间半径为 W+2ε_v/dt=0.024 m/s²。首步动作使两中心相差 |a|；|a|>0.048 保证区间不相交。另用包含位置和速度的两个世界相容 LP 最大化仍可能共享 y0=0、y1 的正动作，结果也是 0.048。边界点的显式共同观测 y1=(0.00003,0.0012) 同时与两候选相容，故等号不能算保证区分。负方向由对称性得到。这里的阈值对控制器声明的初始测量盒和误差模型成立，不是任意动力学的通式。

## 二、先计算名义已知延迟可恢复性

令后两步动作是 b、c，精确初态零、无外扰，则终点满足：

- d=0：p3=0.00625a+0.00375b+0.00125c，v3=0.05(a+b+c)。
- d=1：p3=0.00375a+0.00125b，v3=0.05(a+b)；c 不在本次期限内执行。

对给定 a 解剩余动作可行性 LP，并将 a 一并作为变量投影，得到 d=0 的区间 [−1.055,0.57]、d=1 的区间 [−0.11,0.11]。d=1 也能独立手算：p3−0.025v3=0.0025a，目标的该线性组合为零，容差组合为 0.000275，因此 |a|≤0.11。

两模型分别已知延迟时都名义可行，并且保证首步区分的联合动作范围为 [−0.11,−0.048)∪(0.048,0.11]。这是两套模型专属后续动作的区域，绝不意味着同一个后续序列可以满足两种延迟。LP 核验本例共同开环 (a,b,c) 集合为空；这本身也不能替代任意反馈策略的不可行证明。

图中的“nominal_task_only”只表示已知延迟后名义任务可行但首步不保证区分，不能标成“无需辨识也能完成”。同理 identify_only 只证明信息可得而两模型中至少一个名义任务不可恢复。

## 三、最坏外扰下的因果限制

首先，d=1 有与 b、c 无关的不变量：

p3−0.025v3 = p0+0.125v0+0.0025a+0.005w0+0.0025w1。

初态测量盒和极值常值外扰给出保证任务的必要界 |a|≤0.041；即便初态精确为零，这一简单不变量也要求 |a|≤0.05。这些只是不变量必要界。

更强的因果证明直接保持本实验的精确零初态：假定控制器甚至已知 d=1，并精确看到共同前缀 w0=0.02 产生的状态。考虑两条均满足幅值与变化率的未来：A 为 (w1,w2)=(0.02,0.02)，B 为 (0.01,0)。在 k=1 选择 b 时两世界信息完全一样，因此必须选择相同 b；k=2 的 c 来不及影响终点。

A 的位置上界要求 b≤1.58−3a；B 的速度下界要求 b≥1.51−a，所以 a≤0.035。对称的负外扰分支要求 a≥−0.035。因此 |a|≤0.035 是本次硬期限任务对全部允许外扰可保证完成的必要条件，即使给了更多信息仍成立。它与保证首步区分的动作集合不相交。

冻结动作 a={a} 时，两个分支分别允许 b∈[{intervals[0][0]:.6f},{intervals[0][1]:.6f}] 和 [{intervals[1][0]:.6f},{intervals[1][1]:.6f}]，交集为空。两分支分别在知道未来时可行，但同一个因果 b 无法保证两者。这解释了为什么“每条样本事后可行”不能当成“存在统一的因果保证”。这些推导都是本次构造系统的基础几何，不视作已确认论文贡献。

## 四、开发扫描、冻结与新轨迹测试

粗网格覆盖 [−2,2]、步长 0.05；[−0.15,0.15] 加密到 0.005，补上 ±0.041/0.048/0.355 等诊断点。准备边界按初始测量盒与首步外扰做保守校验，允许区间为 [−1.178,1.178]。不允许点只用于解析地图，不向仿真发送。共 {len(scan)} 个允许动作，每个配旧 37 条轨迹和两个延迟，{audits[0]['episodes']} 次开发仿真。

从保证区分且两模型分别名义可行的网格中，按开发完成次数最多、准备平方能量最小、再优先正号，冻结动作 {a}；开发结果 {best['success_count']}/{best['episodes']}。冻结文件绑定代码、配置和全部开发逐案例数据哈希，冻结后才生成 128 条新有界随机游走外扰与均匀有界误差（种子 2026110601），每条配两个延迟，共 256 次/规则、{audits[1]['episodes']} 次新测试。没有使用新测试结果调参。

与零首步、原任务控制首步、固定 +0.1 比较，后续控制器完全相同。新轨迹与开发及上一轮独立测试轨迹均检查不重复；仍是同分布测试，不代表分布外或真实机器人泛化。
{shared}

准备能量为 dt·a²，单位 m²/s³。表中“hindsight”使用真实 x1、真实延迟和已发生的未来外扰计算剩余动作可行性，仅作乐观事后诊断；它的不可行能排除该真实轨迹上的任何后续动作，它的可行不能证明存在可执行的保证策略。“Known-delay robust plan”用当时测量盒及未来外扰包络，假设延迟已知，给出一个共同开环鲁棒后续计划存在的充分证据；它不可行不代表真实任务不可行，候选仍不唯一时它是 oracle 诊断而非控制器可用方案。

## 五、失败归因与验证

原任务首步约 −0.354 后的 128 次失败，全部连真实未来已知的事后 LP 都不可行。固定 +0.1 的 93 次失败中，55 次事后不可行，38 次事后可行。冻结 +0.05 的 17 次失败均事后可行，但当时的保守已知延迟鲁棒计划 LP 不可行。后两类失败只能归为信息/不确定性/控制策略的剩余缺口，不能仅凭事后可行就断言是控制实现错误。零首步 256 次都事后可行，但没有首步辨识，原控制策略全部失败；这也不构成所有未知延迟策略都失败的证明。

独立审计全部 {auditsteps} 步的标量物理递推、观测、执行延迟、真实候选保留、准备边界、首步能量、任务开始状态/队列、终点成败和汇总计数；冻结规则与源文件哈希另行检查。针对性测试覆盖边界共同观测、名义投影、不变量、可行性层次、队列连续性、生成边界及不可预知未来分支。完整回归记录 first_action_scan_tests.log。

结论：本轮改进主要来自选择同时有信息且较少损害任务的首步动作，而不是辨识时刻更早；0.05 的高有限样本完成率不提供最坏情形保证。下一阶段若继续追求保证，需要改变任务条件（例如增加预告/放宽期限或容差），并显式考虑因果未来分支；不能在当前矛盾的条件下直接声称存在保证式触发算法。任何基于本轮数据调整的方法都需要新的测试。

## 文件

代码 first_action_scan.py（scan → freeze → test），analyze_first_action_scan.py 为独立审计、推导、绘图与报告；测试 test_first_action_scan.py。results/first_action_scan/ 保存 config.json、analytic.json、regions.json、开发/测试输入、轨迹、逐案例与汇总、frozen_rule.json、audit.json、causal_obstruction.json、failure_diagnostics.json、first_action_regions.png。使用现有环境，无新增依赖；已完成运行和冻结选择拒绝覆盖，复现应使用独立副本。旧结果未覆盖。
'''
    en=f'''# First action: delay discrimination versus task recoverability

Date: 2026-11-04. Mechanism analysis of the existing .05 s preview/two-step endpoint task. No novel method or verified originality claim.

## Main findings

Freeze a={a:+.3f} m/s² after scanning development records. On 128 new records paired with two delays it completes 239/256 episodes, versus 163/256 for +.1 and 128/256 for the original task-generated first action. All three nonzero strategies identify after the same first observation. Their different outcomes are not due to earlier identification.

There is a nominal region allowing both discrimination and model-specific known-delay continuation. With all allowed disturbances, however, no fixed first action simultaneously guarantees one-step identification and this deadline task: discrimination requires |a|>.048 under the declared measurement-box model; a necessary causal recovery condition is |a|≤.035, even with exact zero initial state, known delay and exact prefix observation. The latter is necessary, not sufficient.

## Setup

Keep the double integrator, dt=.05 s, fixed d=0/1, command bound 2 m/s², acceleration disturbance bound .02 m/s² and increment .01 m/s², measurement error bounds (1e-5 m,1e-4 m/s). At k=0 apply a, the original task starts at k=1, and the endpoint is k=3. Absolute target (.002 m,.08 m/s), tolerances (.0002 m,.003 m/s). Preparation bounds: |p1|≤.01 m, |v1|≤.06 m/s.

Carry the resulting physical x1 and pending a into the task without resetting. Every strategy uses the same legacy planner and causal prefix membership filter at k=1,2. Ground truth enters only separate diagnostics. Physical test initial states equal zero; controllers only observe bounded-error measurements. Nominal geometry and uniform measurement-box guarantees are distinguished below.

## Observation separation

The acceleration inferred from velocity increments has half-width W+2ε_v/dt=.024 under either hypothesis; |a|>.048 separates them. A two-world LP using both position and velocity maximizes the action for which a shared y0=0,y1 remains possible and obtains exactly .048. At equality y1=(.00003,.0012) is an explicit common observation, so equality is not guaranteed identification. Negative actions follow by symmetry. This threshold is specific to the declared initial measurement box and this plant.

## Nominal known-delay recovery

With exact zero initial state and no disturbance, subsequent commands (b,c) give d=0: p3=.00625a+.00375b+.00125c, v3=.05(a+b+c); d=1: p3=.00375a+.00125b, v3=.05(a+b). The last command c does not reach the delayed plant before the deadline.

LP projection yields a∈[-1.055,.57] for d=0 and [-.11,.11] for d=1. Independently, under d=1, p3−.025v3=.0025a while the target combination is zero and its tolerance is .000275, yielding |a|≤.11.

Thus guaranteed separation and separate known-delay nominal feasibility intersect on [-.11,-.048)∪(.048,.11]. This is not a common continuation sequence: each model may use different b,c. The common nominal open-loop (a,b,c) set is empty, which alone does not prove arbitrary feedback impossibility. The plot label nominal_task_only denotes known-delay nominal feasibility without guaranteed first-step separation, not completion without identification.

## Causal worst-case obstruction

The d=1 invariant is p3−.025v3=p0+.125v0+.0025a+.005w0+.0025w1, independent of b,c. Initial measurement-box uncertainty and constant extreme disturbances require |a|≤.041 for a guarantee; exact zero initial state gives the weaker necessary |a|≤.05.

A stronger nonanticipation argument retains exact zero initial state. Give the controller even more information: d=1 and the exact prefix state. Let w0=.02. Future A is (w1,w2)=(.02,.02), future B is (.01,0); both obey amplitude/rate bounds. At k=1 their information is identical, so b must be shared, and c is too late to help. A's position upper bound requires b≤1.58−3a; B's velocity lower bound requires b≥1.51−a, hence a≤.035. Mirrored negative disturbances give a≥−.035. This is a necessary all-disturbance causal recovery bound, not a sufficiency theorem.

For the frozen action {a}, the two branch intervals for b are [{intervals[0][0]:.6f},{intervals[0][1]:.6f}] and [{intervals[1][0]:.6f},{intervals[1][1]:.6f}], with empty intersection. Each future is individually feasible with hindsight, yet no causal b guarantees both. This basic constructed-system geometry is not asserted as a research novelty.

## Development, freeze and fresh evaluation

Use .05 spacing on [-2,2], .005 spacing on [-.15,.15], and diagnostic boundary/actions including ±.041/.048/.355. Uniform preparation-envelope checks give admissible a∈[-1.178,1.178]. Outside points appear only in the analytic map and are not sent to the plant. Scan {len(scan)} admissible actions on the previous 37 records and two delays: {audits[0]['episodes']} development episodes.

Among the separating, separately nominally viable grid actions choose most development completions, then least preparation squared-command energy, then positive sign. Freeze {a}, development {best['success_count']}/{best['episodes']}, with source/configuration/development hashes. Only then generate 128 fresh bounded disturbance random walks/uniform error records (seed 2026110601), paired with two delays: 256 episodes per rule, {audits[1]['episodes']} total. Compare zero, task-generated, +.1 and frozen action with identical continuation control. Inputs are distinct from development and previous held-out records; this remains same-distribution evaluation. No retuning uses these outcomes.
{shared}

Preparation energy is dt·a², in m²/s³. Hindsight feasibility supplies true x1, delay and realized future disturbances to an optimistic LP. Infeasibility excludes all subsequent actions on that fixed realized path; feasibility does not establish an implementable robust policy. Known-delay robust-plan feasibility uses the current measured box and future disturbance envelope to certify existence of a sufficient open-loop continuation. Its infeasibility is not physical impossibility; when candidates remain ambiguous it is an oracle diagnostic.

## Failure attribution and audit

All 128 failed task-generated-action episodes are hindsight infeasible. Of 93 failures for +.1, 55 are hindsight infeasible and 38 hindsight feasible. All 17 failures for +.05 are hindsight feasible but lack the conservative current known-delay robust-plan certificate. Such gaps include uncertainty/information/planning effects and do not alone prove implementation defects. With zero action all 256 paths are hindsight feasible, but first-step identification never occurs and this controller fails; this does not prove all unknown-delay policies fail.

Independently audit {auditsteps} transitions via scalar dynamics, measurements, delay application, true-candidate retention, preparation bounds, energy, task-start state/queue, terminal outcomes and aggregate counts. Source/freeze hashes and selection ranking are checked. Targeted tests cover boundary overlap, nominal projections, invariant algebra, feasibility layers, continuity, generated bounds and nonanticipating future branches. Full regression: first_action_scan_tests.log.

The observed improvement comes from a more task-compatible informative first action, not earlier identification. High finite-test success at .05 gives no worst-case guarantee. To pursue guarantees, change task conditions such as preview, deadline or tolerances and explicitly handle causal future branches. Do not claim a guaranteed trigger under the present incompatible requirements. Further data-informed changes require fresh evaluation.

## Artifacts

first_action_scan.py runs scan → freeze → test. analyze_first_action_scan.py audits, derives bounds, plots and generates bilingual reports. Tests: test_first_action_scan.py. results/first_action_scan/ stores configuration, analytic boundaries, regions, separate development/test inputs/trajectories/metrics, frozen rule, audit, causal obstruction, failure diagnostics and first_action_regions.png. Existing environment, no new dependencies. Completed runs/freeze refuse overwrite; reproduce in an isolated copy. Historical results are preserved.
'''
    report=ROOT/'report';report.mkdir(exist_ok=True)
    (report/'FIRST_ACTION_SCAN_REPORT.md').write_text(zh,encoding='utf-8')
    (report/'FIRST_ACTION_SCAN_REPORT_EN.md').write_text(en,encoding='utf-8')
    print(json.dumps({'scan_episodes':audits[0]['episodes'],'test_episodes':audits[1]['episodes'],
         'audited_transitions':auditsteps,'selected':best,'causal_obstruction':obstruction},indent=2))
    print('Saved audited region figure and bilingual reports.')

if __name__=='__main__':main()
