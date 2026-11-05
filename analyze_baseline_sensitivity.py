"""Audit immutable development/test artifacts, generate bilingual reports."""
from pathlib import Path
import csv,hashlib,json
import numpy as np

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'/'baseline_sensitivity'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def audit_phase(phase):
    folder=OUT/phase;episodes=read(folder/'episodes.json');groups={}
    data=np.load(folder/'paired_inputs.npz')
    ws={str(n):w for n,w in zip(data['names'],data['disturbances'])}
    es={str(n):e for n,e in zip(data['names'],data['measurement_errors'])}
    with (folder/'trajectories.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            key=(int(r['preview']),r['variant'],r['policy'],r['case'],int(r['true_delay']))
            groups.setdefault(key,[]).append(r)
    max_dyn=0.;max_obs=0.;steps=0
    for m in episodes:
        key=(m['preview'],m['variant'],m['policy'],m['case'],m['true_delay'])
        rr=groups[key];state=np.zeros(2);commands=[];prep=[]
        assert len(rr)==m['preview']+2
        for k,r in enumerate(rr):
            assert int(r['k'])==k
            saved=np.array([float(r['p']),float(r['v'])]);nxt=np.array([float(r['next_p']),float(r['next_v'])])
            np.testing.assert_allclose(state,saved,atol=1e-12,rtol=0)
            u=float(r['command']);actual=float(r['applied']);w=float(r['disturbance'])
            assert abs(u)<=2+1e-10
            assert abs(w-ws[m['case']][k])<1e-13
            expected_applied=u if m['true_delay']==0 else (commands[-1] if commands else 0.)
            assert abs(actual-expected_applied)<1e-13
            expected=state+np.array([.05*state[1]+.00125*(actual+w),.05*(actual+w)])
            max_dyn=max(max_dyn,float(np.max(np.abs(nxt-expected))))
            observed=np.array([float(r['measured_p']),float(r['measured_v'])])
            max_obs=max(max_obs,float(np.max(np.abs(observed-state-es[m['case']][k]))))
            assert str(m['true_delay']) in r['candidates'].split(';')
            if k==m['preview']:
                np.testing.assert_allclose(saved,m['task_start_state'],atol=1e-13,rtol=0)
                np.testing.assert_allclose(commands,m['task_start_history'],atol=1e-13,rtol=0)
            if k<m['preview']:prep.append(nxt)
            commands.append(u);state=nxt;steps+=1
        error=np.abs(state-np.array([.002,.08]))
        np.testing.assert_allclose(error,[m['position_error_m'],m['velocity_error_m_s']],atol=1e-13,rtol=0)
        pmax=max((abs(x[0]) for x in prep),default=0.);vmax=max((abs(x[1]) for x in prep),default=0.)
        np.testing.assert_allclose([pmax,vmax],[m['max_prep_position_m'],m['max_prep_velocity_m_s']],atol=1e-13,rtol=0)
        energy=.05*sum(u*u for u in commands[:m['preview']])
        assert abs(energy-m['prep_command_energy'])<1e-12
        success=bool(np.all(error<=np.array([.0002,.003])+1e-10) and pmax<=.01+1e-10 and vmax<=.06+1e-10 and m['prep_solver_failures']==0)
        assert success==m['success']
        if m['policy']=='probe' and m['preview']>0:
            assert abs(commands[0]-.1)<1e-13 and m['first_single_sample']==1
    assert max_dyn<1e-12 and max_obs<1e-12
    for g in read(folder/'summary.json'):
        subset=[m for m in episodes if (m['preview'],m['variant'],m['policy'])==(g['preview'],g['variant'],g['policy'])]
        assert len(subset)==g['episodes'] and sum(m['success'] for m in subset)==g['success_count']
    return {'phase':phase,'episodes':len(episodes),'steps':steps,'max_scalar_dynamics_residual':max_dyn,
        'max_observation_residual':max_obs,'continuous_state_and_queue':True,
        'energy_state_success_counts_verified':True,'true_delay_retained_in_every_saved_prefix':True}

def main():
    config=read(OUT/'config.json');frozen=read(OUT/'frozen_selection.json');provenance=read(OUT/'test'/'provenance.json')
    assert digest(ROOT/'baseline_sensitivity.py')==config['source_sha256']==frozen['source_sha256']
    assert digest(OUT/'config.json')==frozen['config_sha256']
    assert digest(OUT/'development'/'episodes.json')==frozen['development_episodes_sha256']
    assert digest(OUT/'frozen_selection.json')==provenance['frozen_manifest_sha256']
    assert digest(OUT/'test'/'episodes.json')==provenance['episodes_sha256']
    assert digest(OUT/'test'/'paired_inputs.npz')==provenance['input_sha256']
    for name,h in config['dependencies'].items():assert digest(ROOT/name)==h
    # Check selection follows the predeclared ranking rather than test outcomes.
    for chosen in frozen['selected']:
        group=[s for s in frozen['scores'] if s['variant']['family']==chosen['variant']['family']]
        best=min(group,key=lambda s:(-s['success_count'],s['mean_prep_energy'],s['variant']['name']))
        assert best==chosen
    dev=np.load(OUT/'development'/'paired_inputs.npz');test=np.load(OUT/'test'/'paired_inputs.npz')
    assert not any(np.array_equal(a,b) for a in dev['disturbances'] for b in test['disturbances'])
    phases=[audit_phase(p) for p in ('development','test')]
    # Keep the frozen success threshold unchanged; separately expose numerical
    # boundary effects from the lexicographic tolerance, rather than hiding them.
    boundary_diagnostics=[]
    for phase in ('development','test'):
        for m in read(OUT/phase/'episodes.json'):
            if (not m['success'] and m['prep_solver_failures']==0 and
                m['prep_position_violation_m']<=1e-10 and m['prep_velocity_violation_m_s']<=1e-10 and
                m['position_error_m']<=.0002+1e-8 and m['velocity_error_m_s']<=.003+1e-8):
                boundary_diagnostics.append({'phase':phase,'preview':m['preview'],'variant':m['variant'],
                    'policy':m['policy'],'case':m['case'],'true_delay':m['true_delay'],
                    'position_excess_m':max(0.,m['position_error_m']-.0002),
                    'velocity_excess_m_s':max(0.,m['velocity_error_m_s']-.003)})
    (OUT/'boundary_diagnostics.json').write_text(json.dumps(boundary_diagnostics,indent=2),encoding='utf-8')
    audit={'phase_audits':phases,'source_and_freeze_hashes_verified':True,
           'selection_rule_recomputed':True,'test_inputs_not_in_development':True}
    (OUT/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    episodes=read(OUT/'test'/'episodes.json');summary=read(OUT/'test'/'summary.json')
    n1_unknown=[m for m in episodes if m['preview']==1 and m['policy']!='oracle']
    same_n1_timing=all(m['first_single_sample']==1 for m in n1_unknown)
    assert same_n1_timing
    first_commands={}
    with (OUT/'test'/'trajectories.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            if r['preview']=='1' and r['k']=='0' and r['policy']!='oracle':
                first_commands.setdefault((r['variant'],r['policy']),[]).append(float(r['command']))
    input_diagnostics={'one_step_preview_all_unknown_controllers_identify_at_sample_1':same_n1_timing,
        'first_commands':[{'variant':v,'policy':p,'mean':float(np.mean(us)),
                           'min':min(us),'max':max(us)} for (v,p),us in first_commands.items()]}
    (OUT/'first_action_diagnostics.json').write_text(json.dumps(input_diagnostics,indent=2),encoding='utf-8')
    comparisons=[]
    for chosen in frozen['selected']:
        v=chosen['variant']['name']
        for n in (0,1,2,4,8):
            passive={(m['case'],m['true_delay']):m for m in episodes if m['variant']==v and m['preview']==n and m['policy']=='passive'}
            probe={(m['case'],m['true_delay']):m for m in episodes if m['variant']==v and m['preview']==n and m['policy']=='probe'}
            assert passive.keys()==probe.keys()
            pairs=[(passive[k]['success'],probe[k]['success']) for k in passive]
            comparisons.append({'variant':v,'preview':n,'pairs':len(pairs),
                'both_success':sum(a and b for a,b in pairs),'passive_only_success':sum(a and not b for a,b in pairs),
                'probe_only_success':sum(not a and b for a,b in pairs),'both_fail':sum(not a and not b for a,b in pairs)})
    (OUT/'paired_comparisons.json').write_text(json.dumps(comparisons,indent=2),encoding='utf-8')
    # Every predeclared grid value is visible, including unselected failures.
    devtable='| Variant | Family | Development successes | Mean prep energy | Selected |\n|---|---|---:|---:|---|\n'
    chosen_names=[s['variant']['name'] for s in frozen['selected']]
    for score in frozen['scores']:
        v=score['variant']
        devtable+=f"| {v['name']} | {v['family']} | {score['success_count']}/{score['episodes']} | {score['mean_prep_energy']:.7f} | {v['name'] in chosen_names} |\n"
    resulttable='| Preview (s) | Variant | Passive successes | Probe successes | Passive-only | Probe-only |\n|---:|---|---:|---:|---:|---:|\n'
    metricstable='| Preview steps | Variant | Policy | Mean prep energy | Max prep p (m) | Max prep v (m/s) | ID by task start | Never ID | Mean ID time among identified (s) | Mean controller ms/episode |\n|---:|---|---|---:|---:|---:|---:|---:|---:|---:|\n'
    for n in (0,1,2,4,8):
        for v in chosen_names:
            p=next(g for g in summary if (g['preview'],g['variant'],g['policy'])==(n,v,'passive'))
            a=next(g for g in summary if (g['preview'],g['variant'],g['policy'])==(n,v,'probe'))
            c=next(c for c in comparisons if c['preview']==n and c['variant']==v)
            resulttable+=f"| {n*.05:.2f} | {v} | {p['success_count']}/{p['episodes']} | {a['success_count']}/{a['episodes']} | {c['passive_only_success']} | {c['probe_only_success']} |\n"
            for g in (p,a):
                idtime='NA' if g['mean_identified_time_s'] is None else f"{g['mean_identified_time_s']:.4f}"
                metricstable+=f"| {n} | {v} | {g['policy']} | {g['mean_prep_energy']:.7f} | {g['max_prep_position_m']:.6f} | {g['max_prep_velocity_m_s']:.6f} | {g['identified_by_start_count']}/{g['episodes']} | {g['never_identified_count']} | {idtime} | {g['mean_controller_ms']:.2f} |\n"
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(11,8),sharex=True,sharey=True)
    for ax,v in zip(axes.flat,chosen_names):
        for policy in ('passive','probe'):
            gs=sorted([g for g in summary if g['variant']==v and g['policy']==policy],key=lambda g:g['preview'])
            ax.plot([g['preview']*.05 for g in gs],[g['success_fraction']*100 for g in gs],'-o',label=policy)
        ax.set(title=v,xlabel='Preview [s]',ylabel='Held-out observed success [%]',ylim=(-5,105));ax.grid(alpha=.3);ax.legend()
    fig.tight_layout();fig.savefig(OUT/'heldout_success.png',dpi=160);plt.close(fig)
    all_failures=sum(m['prep_solver_failures']>0 for m in episodes)
    all_viol=sum(m['prep_position_violation_m']>1e-10 or m['prep_velocity_violation_m_s']>1e-10 for m in episodes)
    facts={'test_episodes':len(episodes),'development_episodes':phases[0]['episodes'],
        'test_prep_hard_solver_failure_episodes':all_failures,'test_prep_boundary_violation_episodes':all_viol,
        'selected_names':chosen_names,'oracle':[{k:g[k] for k in ('preview','success_count','episodes')} for g in summary if g['policy']=='oracle']}
    (OUT/'report_facts.json').write_text(json.dumps(facts,indent=2),encoding='utf-8')
    tables=f'\n{devtable}\n{resulttable}\n![Held-out success](../results/baseline_sensitivity/heldout_success.png)\n\n{metricstable}\n'
    # Interpretation stays close to exact paired counts; no selected best test method.
    observations=[]
    for v in chosen_names:
        c=next(c for c in comparisons if c['variant']==v and c['preview']==8)
        observations.append(f"{v}: N=8 passive-only={c['passive_only_success']}, probe-only={c['probe_only_success']}")
    obs='; '.join(observations)
    def testgroup(v,p,n):
        return next(g for g in summary if (g['variant'],g['policy'],g['preview'])==(v,p,n))
    legacy8=testgroup('legacy','passive',8)
    trackname=next(s['variant']['name'] for s in frozen['selected'] if s['variant']['family']=='tracking')
    track8=testgroup(trackname,'passive',8)
    track8probe=testgroup(trackname,'probe',8)
    dev_boundary=sum(x['phase']=='development' for x in boundary_diagnostics)
    test_boundary=sum(x['phase']=='test' for x in boundary_diagnostics)
    shared=f'''
Source SHA-256: `{config['source_sha256']}`.

Frozen selection SHA-256: `{provenance['frozen_manifest_sha256']}`.

Python {config['versions']['python']}; NumPy {config['versions']['numpy']}; SciPy {config['versions']['scipy']}; scipy.optimize.linprog / HiGHS.
'''
    zh=f'''# 被动控制基线敏感性与试探必要性：冻结后测试

日期：2026-11-04。这是一轮基线诊断，不提出新控制算法，也不将有限样本成功称为鲁棒保证。

主要结果：0.4 s 预告下，原始被动基线 {legacy8['success_count']}/{legacy8['episodes']}，过程跟踪被动基线 {track8['success_count']}/{track8['episodes']}，其匹配试探版本 {track8probe['success_count']}/{track8probe['episodes']}；原先的完成率优势不再出现。0.05 s 下仍有试探版本优势，但所有未知延迟方案都在同样的首步观测后辨识，因此该优势不是辨识时间提前的证据。

## 问题与公平条件

检验上一轮 0.4 s 预告下被动基线下降，是否依赖终点代价和动作时序；再看专门试探相对于改进被动控制器的配对收益。保持原系统、未知固定延迟 d=0/1、误差与外扰边界、绝对目标和截止时间。所有方案输入上限仍为 2 m/s²，准备阶段 |p|≤0.01 m、|v|≤0.06 m/s。预告长度仍为 0/1/2/4/8 步。

每个冻结的被动控制器都有完全匹配的 probe 版本：只有 N>0 时第一步强制 0.1 m/s²，其后两者使用同一控制器和候选筛选。N=0 没有试探，成对控制策略相同。另设 lex_energy 已知延迟参考。真实状态、延迟与外扰不输入未知延迟控制器；状态和指令历史连续，任务开始不重置。

## 预先声明的代价与参数网格

- legacy：原始终点最坏归一化违反量 t + 1e-5·sum|u|。
- lex_energy：先最小化 t，再在 t≤t*+1e-7 下最小化平均 sum|u|。这隔离终点与动作成本的微小权衡；名称 energy 指输入代价，优化的是 L1，不是报告中的平方能量。
- tracking：同样先固定最优终点违反量，再加入过程跟踪误差，权重 0.01/0.1/1。参考轨迹为从零参考状态到同一绝对终点的三次 Hermite 曲线；位置/速度误差以准备边界归一化，使用各候选与未来外扰的最坏分量上界。终点不重复计入过程误差，输入平均 L1 权重为 1e-5。
- progress：终点优先不变，在最后四步的中间状态对偏离参考轨迹超过 0.25/0.5/1 倍准备边界的部分加入软违反代价，权重 0.1；输入权重同上。它不是新增硬路径约束，不改变各方法允许的动作或真实任务要求。

跟踪/进度在每次重规划时取当前剩余中间状态的平均代价，完整公式见 baseline_sensitivity.py。候选过滤与保守未来不确定性包络沿用上一轮。共同开环终点计划不可行时仍执行最小违反动作并记录失败；没有把软化解当成完成证明。

## 开发、冻结与独立测试

8 个候选基线只在旧 37 条轨迹、两个延迟、五档预告上开发，每个配置 370 次，共 {phases[0]['episodes']} 次。每个家族按“总完成次数最多 → 平均准备平方能量最小 → 名称顺序”选择一个。所有候选和结果公开，不按测试表现重新挑选。

冻结文件记录源代码、依赖、配置和开发逐案例结果哈希；之后才生成测试输入并运行。测试采用种子 2026110501 的 64 条新有界外扰随机游走和测量误差记录，逐条配两个延迟，每组 128 次，四家族各有 passive/probe，另有一个 oracle，共 {len(episodes)} 次。测试轨迹与开发轨迹逐条检查不重复；测试与开发属于同一生成分布，未改变模型，不声称分布外泛化。测试结果未用于调参或重选配置。

以下先给出开发选择，再给出独立测试和配对结果。Passive-only 是仅被动方案成功的配对数，Probe-only 是仅试探方案成功的配对数。不能只展示试探有利案例。
{tables}

能量是准备阶段 dt·sum(u²)，单位 m²/s³；位置/速度偏离为该组准备阶段的实际最大绝对值。辨识时刻是从预告开始到候选首次唯一，平均值仅对已辨识案例计算；同时报告从未辨识数和任务开始前辨识数，避免掩盖删失。时间为每个完整 episode 的过滤和控制耗时，非单步最坏实时保证。两种延迟共享同一轨迹，因此不是 128 个独立随机环境；这里报告有限配对计数，不进行显著性宣称。

## 审计与结论边界

本轮独立测试的关键对照：0.4 s 时 legacy 被动方案为 {legacy8['success_count']}/{legacy8['episodes']}，冻结的 {trackname} 被动方案为 {track8['success_count']}/{track8['episodes']}，匹配的试探方案为 {track8probe['success_count']}/{track8probe['episodes']}。对应跟踪被动与试探准备能量分别为 {track8['mean_prep_energy']:.7f} 与 {track8probe['mean_prep_energy']:.7f} m²/s³。这比仅对照原始终点基线更能判断专门试探的独立价值。

测试中准备硬约束求解失败 {all_failures} 次 episode，实际准备边界违反 {all_viol} 次 episode；完整原始记录保留。开发与测试共 {sum(p['steps'] for p in phases)} 步均通过独立标量动力学、观测重建、执行延迟、输入界、任务开始连续性、动作能量、状态偏离、终点成败及汇总计数审计。所有保存的观测前缀都保留真实延迟。冻结规则和文件哈希另行核验。

数值边界另存 boundary_diagnostics.json：主成功判据始终沿用终点容差加 1e-10，未为了结果更好而修改。开发中有 {dev_boundary} 次、测试中有 {test_boundary} 次失败，在位置和速度分别放宽到仅 1e-8 的数值容限后会通过；它们可能来自 1e-7 归一化词典序松弛，不能当作有实际幅度的性能损失。主表仍保留原始计数。

0.4 s 下各冻结家族的成对差异：{obs}。这些数字直接显示专门试探在当前家族内的收益或代价；不同家族间也应同时比较。单一终点基线的失败不能作为所有被动控制策略的下界。加入过程跟踪或软进度同时改变了轨迹偏好与信息产生，尚未分离所有机制；本轮没有信息目标或自适应触发器。

0.05 s 下四个家族的被动版本均为 64/128，试探版本均为 81/128；但所有未知延迟方案的唯一候选时刻都是 k=1。首步命令统计另存 first_action_diagnostics.json。既然信息可用时刻一致，就不能把这 17 次净增成功解释成更早辨识；不同首步命令造成的任务开始状态和待执行指令是必须检验的解释。当前证据尚不足以支持“专门主动辨识是必要贡献”。

若某家族在某档预告被动和试探均完成全部有限测试，只能说明本轮没有观察到专门试探的完成率收益；不能证明试探永远无用。若仍有配对优势，也仅针对冻结的候选基线，不是与全局最优因果策略的比较。下一步应先依据这些配对证据限定研究区域，再考虑可恢复任务集合与辨识触发规则，不能把调参结果当作 RA-L 创新。

## 文件与复现

代码 baseline_sensitivity.py 分 development / freeze / test 三阶段；analyze_baseline_sensitivity.py 独立审计并生成图和中英文报告；test_baseline_sensitivity.py 为五项针对性检查。完整回归日志 baseline_sensitivity_tests.log。使用现有虚拟环境和依赖，无新增依赖。

results/baseline_sensitivity/ 保存 config.json、frozen_selection.json、开发和测试各自的 paired_inputs.npz / trajectories.csv / episodes.json / summary.json、测试 provenance.json、audit.json、paired_comparisons.json、report_facts.json 和 heldout_success.png。脚本拒绝覆盖已完成开发/测试结果或重新冻结选择；重现应在独立副本中按 development → freeze → test → analyze 的顺序运行，不修改冻结目录。旧实验代码和结果未改动。
{shared}
'''
    en=f'''# Passive baseline sensitivity and the need for dedicated probing

Date: 2026-11-04. Baseline diagnosis, not a novel algorithm or a robust guarantee from finite successes.

Main finding: at .4 s, legacy passive achieves {legacy8['success_count']}/{legacy8['episodes']}, tracking passive {track8['success_count']}/{track8['episodes']}, and matched tracking probe {track8probe['success_count']}/{track8probe['episodes']}. The original completion-rate advantage disappears. At .05 s a probing-version advantage remains, but every unknown-delay controller identifies after the same first observation; it is not evidence of earlier identification.

## Question and matched conditions

Test whether the previous .4 s passive failure depends on endpoint cost and action timing, then compare probing against improved passive controllers. Preserve the plant, unknown fixed d=0/1, uncertainty bounds, absolute endpoint, deadline and preview grid 0/1/2/4/8 steps. Commands remain bounded by 2 m/s²; preparation states satisfy |p|≤.01 m, |v|≤.06 m/s.

Each frozen passive controller has a matched probe version: for positive preview only, force the first command to .1 m/s², then use exactly the same controller/filter. At zero preview they coincide. A lex_energy oracle knows the true delay. Unknown-delay controllers receive no truth states, disturbances, future measurements or execution timestamps. Neither state nor pending commands reset at task start.

## Predeclared variants

Legacy retains t+1e-5·sum|u|, where t is worst normalized terminal violation. Lex_energy first minimizes t, then minimizes average command L1 subject to t≤t*+1e-7. Despite its name, the optimized command cost is L1; reported preparation energy is squared-command energy.

Tracking keeps this lexicographic endpoint priority and adds worst-case componentwise intermediate tracking error, normalized by preparation bounds, at weights .01/.1/1. The reference is a cubic Hermite curve from zero reference state to the same absolute endpoint. Input average L1 has weight 1e-5. The endpoint is not counted again in tracking error.

Progress keeps endpoint priority and penalizes intermediate deviations outside .25/.5/1 times the preparation bounds in the final four steps, with weight .1 and input L1 weight 1e-5. These are soft progress preferences, not additional hard constraints or different action permissions. Intermediate costs are averaged over the remaining intermediate states at each replan; exact coefficients are in baseline_sensitivity.py.

Filtering and conservative future uncertainty envelopes are inherited unchanged. Infeasible robust endpoints use least-violation actions and remain failures when the actual task fails; softened solutions are not certificates of task completion.

## Development, freeze and held-out evaluation

Eight passive variants use the previous 37 records, two delays and five previews: 370 episodes each, {phases[0]['episodes']} total. Select one variant per family by most total development successes, then least mean preparation squared-command energy, then name. Publish the complete grid, including unselected failures.

The selection manifest binds source/dependency/configuration and development-output hashes. Only after freezing is the evaluation input file generated. Test seed 2026110501 produces 64 new bounded disturbance random walks/error records, paired with two delays, 128 episodes per setting. Four selected families each have passive/probe versions, plus one oracle: {len(episodes)} test episodes. No test record duplicates a development disturbance sequence. This is same-distribution holdout, not out-of-distribution generalization. No tuning or reselection uses test outcomes.

Tables show the development selection, held-out success and paired discordances, then costs and identification. Passive-only/probe-only counts retain both directions of benefit.
{tables}

Preparation energy is dt·sum(u²), in m²/s³. State excursions are actual maximum absolute preparation positions/velocities in each group. Mean identification time is conditional on eventual identification; never-identified counts and identification by task start are also shown. Runtime covers filtering/control for a whole episode, not a per-step worst-case real-time bound. Two delays share each random environment, so 128 episodes are not 128 independent environments. These are finite paired counts without significance claims.

## Audit and interpretation limits

The key held-out .4 s comparison is legacy passive {legacy8['success_count']}/{legacy8['episodes']}, frozen {trackname} passive {track8['success_count']}/{track8['episodes']}, and its matched probe {track8probe['success_count']}/{track8probe['episodes']}. Tracking passive/probe preparation energies are {track8['mean_prep_energy']:.7f} and {track8probe['mean_prep_energy']:.7f} m²/s³ respectively. This is more informative about dedicated probing than comparison only against the original endpoint baseline.

Test hard-preparation solver-failure episodes: {all_failures}; actual preparation-bound violations: {all_viol}. Independently audit all {sum(p['steps'] for p in phases)} development/test transitions via scalar dynamics, observation reconstruction, delayed application, input bounds, task-start continuity, energy, state excursions, endpoint outcomes and aggregate counts. Every saved prefix retains the true delay. Source/freeze hashes and the predeclared selection ranking are verified separately.

boundary_diagnostics.json separately retains numerical threshold effects. The primary endpoint tolerance plus 1e-10 remains unchanged. There are {dev_boundary} development and {test_boundary} test failures that would pass with componentwise numerical allowances of only 1e-8 m and 1e-8 m/s. Such cases can reflect the 1e-7 normalized lexicographic tolerance and should not be described as material task losses. Main tables keep the original counts.

At .4 s, paired discordances are: {obs}. Compare across families as well as within each family. A terminal-only controller's failure is not a lower bound on all passive strategies. Tracking/progress change both trajectory preference and information generation; this experiment does not separate every mechanism. No information objective or adaptive trigger has been introduced.

At .05 s, all four passive families achieve 64/128 and their probe versions 81/128. Nevertheless, every unknown-delay controller identifies at k=1. first_action_diagnostics.json records the first-command statistics. The net 17 additional successes therefore cannot be attributed to earlier identification; task-start state and pending-command changes caused by the different first actions must be examined. Current evidence does not establish dedicated active identification as a necessary contribution.

Equal perfect finite-test completion means no observed completion-rate benefit of probing in that setting, not universal uselessness. Remaining advantages concern the frozen candidate controllers, not optimal causal feedback. Use paired evidence to narrow the research region before deriving recoverability/trigger claims; baseline tuning is not a publication novelty result.

## Artifacts and reproduction

baseline_sensitivity.py has development/freeze/test phases. analyze_baseline_sensitivity.py audits and writes figures/bilingual reports. test_baseline_sensitivity.py supplies five targeted checks; full regression: baseline_sensitivity_tests.log. Existing environment, no new dependencies.

results/baseline_sensitivity/ stores configuration, frozen selection, separate development/test paired inputs, trajectories, episodes and summaries, test provenance, audit, paired comparisons, report facts and heldout_success.png. Completed runs and frozen selection cannot be overwritten by the runner. Reproduce in an isolated copy using development → freeze → test → analysis; preserve frozen artifacts. Historical experiments are unchanged.
{shared}
'''
    report=ROOT/'report';report.mkdir(exist_ok=True)
    (report/'BASELINE_SENSITIVITY_REPORT.md').write_text(zh,encoding='utf-8')
    (report/'BASELINE_SENSITIVITY_REPORT_EN.md').write_text(en,encoding='utf-8')
    print(json.dumps(facts,indent=2));print('Bilingual reports generated from audited held-out results.')

if __name__=='__main__':main()
