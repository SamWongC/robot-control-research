"""Audit saved trajectories and summarize the frozen closed-loop experiment."""
from pathlib import Path
import json,hashlib,platform,sys
import numpy as np
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'results'/'push_t_closed_loop_gate'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,x):p.write_text(json.dumps(x,indent=2),encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protocol=read(OUT/'protocol.json');cases=read(OUT/'cases.json')
assert sha(OUT/'cases.json')==protocol['cases_sha']
assert sha(OUT/'execution_source.py.txt')==protocol['source_sha']
assert sha(ROOT/'push_t_fixed_batch.py')==protocol['base_sha']
records=[]
for p in sorted(OUT.glob('dev_*_high.json'))+sorted(OUT.glob('sensitivity_*_high.json'))+sorted(OUT.glob('confirm_*.json')):
    if p.name in [x[0] for x in records]:continue
    r=read(p);t=np.load(p.with_suffix('.npz'))['trace'];case=cases[r['case']]
    assert t.shape==(r['steps'],15) and np.isfinite(t).all()
    errors=np.linalg.norm(t[:,:2]-np.array(case['goal'])[:2],axis=1)
    angles=abs(np.arctan2(np.sin(t[:,2]-case['goal'][2]),np.cos(t[:,2]-case['goal'][2])))
    assert np.allclose(errors,t[:,12]) and np.allclose(angles,t[:,13])
    ok=(errors<=.02)&(angles<=np.deg2rad(10))
    hold=0;success=False
    for flag in ok:
        hold=hold+1 if flag else 0
        success|=hold>=10
    assert bool(success)==r['success']
    assert bool(np.any(np.abs(t[:,[0,1,3,4]])>.5))==r['escaped']
    assert np.all(np.abs(t[:,10:12])<=.25+1e-12)
    assert len(r['latency_ms'])==len(t)
    assert np.isclose(errors[-1],r['position_error'])
    records.append((p.name,r))
gate=read(OUT/'gate.json');dev=[r for name,r in records if name.startswith('dev_')]
sensitivity=[]
for name,r in records:
    if name.startswith('sensitivity_'):
        baseline=next(x for x in dev if x['case']==r['case'])
        sensitivity.append(dict(case=r['case'],base_success=baseline['success'],halfstep_success=r['success'],base_error=baseline['position_error'],halfstep_error=r['position_error'],base_duration=baseline['duration'],halfstep_duration=r['duration']))
methods={m:sorted([r for name,r in records if name.startswith('confirm_') and r['method']==m],key=lambda r:r['case']) for m in ['low','medium','high','top32']}
summary=[];paired=[]
for method,rows in methods.items():
    if not rows:continue
    assert len(rows)==64
    lat=np.concatenate([r['latency_ms'] for r in rows]);success=sum(r['success'] for r in rows)
    summary.append(dict(method=method,n=len(rows),success=success,escapes=sum(r['escaped'] for r in rows),mean_final_error_m=float(np.mean([r['position_error'] for r in rows])),mean_duration_capped_s=float(np.mean([r['duration'] for r in rows])),p50_ms=float(np.percentile(lat,50)),p95_ms=float(np.percentile(lat,95)),p99_ms=float(np.percentile(lat,99)),over50_fraction=float(np.mean(lat>50)),family_success={f:sum(r['success'] for r in rows if r['family']==f) for f in ['approach','near_contact','stem','corner']}))
    if method!='high':
        high=methods['high'];delta=np.array([int(a['success'])-int(b['success']) for a,b in zip(rows,high)])
        assert [r['case'] for r in rows]==[r['case'] for r in high]
        rng=np.random.default_rng(2026110510);boot=[]
        # Preserve four-family composition in episode-level paired resampling.
        groups=[np.array([i for i,r in enumerate(rows) if r['family']==f]) for f in ['approach','near_contact','stem','corner']]
        for _ in range(10000):boot.append(np.mean(delta[np.concatenate([rng.choice(g,len(g)) for g in groups])]))
        first_action_changes=0
        for r in rows:
            a=np.load(OUT/f"confirm_{r['case']}_{method}.npz")['trace'][0,10:12]
            b=np.load(OUT/f"confirm_{r['case']}_high.npz")['trace'][0,10:12]
            first_action_changes+=int(np.linalg.norm(a-b)>1e-8)
        paired.append(dict(method=method,only_method_success=int(np.sum(delta==1)),only_high_success=int(np.sum(delta==-1)),success_difference=float(np.mean(delta)),stratified_paired_bootstrap_95=np.percentile(boot,[2.5,97.5]).tolist(),different_first_action=first_action_changes))
save(OUT/'summary.json',dict(gate=gate,sensitivity=sensitivity,methods=summary,paired=paired))
save(OUT/'audit.json',dict(episodes_checked=len(records),all_trajectory_checks_pass=True,protocol_hash=sha(OUT/'protocol.json'),summary_source_hash=sha(Path(__file__)),python=sys.version,platform=platform.platform(),numpy=np.__version__,checks=['frozen fixture and execution source hashes','trajectory shapes and finite values','recomputed pose errors and consecutive success','workspace exits','control limits','latency count'],limitations='No physical validation; bootstrap is descriptive for these four synthetic families; only four development episodes checked at half execution step.'))
table='| Method | Success /64 | Escape | Mean final error (m) | Mean elapsed (s)* | p95 ms | p99 ms | >50ms |\n|---|---:|---:|---:|---:|---:|---:|---:|\n'
for r in summary:table+=f"| {r['method']} | {r['success']} | {r['escapes']} | {r['mean_final_error_m']:.4f} | {r['mean_duration_capped_s']:.3f} | {r['p95_ms']:.2f} | {r['p99_ms']:.2f} | {r['over50_fraction']:.1%} |\n"
pairtable='| Method vs high | Only method succeeds | Only high succeeds | Success difference | Bootstrap 95% | First action differs /64 |\n|---|---:|---:|---:|---|---:|\n'
for r in paired:pairtable+=f"| {r['method']} | {r['only_method_success']} | {r['only_high_success']} | {r['success_difference']:.1%} | {r['stratified_paired_bootstrap_95']} | {r['different_first_action']} |\n"
sens='| Case | Success base / half-step | Final error base / half-step (m) | Duration base / half-step (s) |\n|---|---|---|---|\n'
for r in sensitivity:sens+=f"| {r['case']} | {r['base_success']} / {r['halfstep_success']} | {r['base_error']:.4f} / {r['halfstep_error']:.4f} | {r['base_duration']:.2f} / {r['halfstep_duration']:.2f} |\n"
familytable='| Method | Approach /16 | Near contact /16 | Stem /16 | Corner /16 |\n|---|---:|---:|---:|---:|\n'
for r in summary:familytable+='| '+r['method']+' | '+' | '.join(str(r['family_success'][f]) for f in ['approach','near_contact','stem','corner'])+' |\n'
common=table+'\n'+familytable+'\n'+pairtable+'\n'+sens
en=f'''# Closed-loop task-meaning gate — 2026-11-05

## Protocol and scope
Development high-resolution successes: {gate['successes']}/16; predeclared gate >=12. Confirmation uses 64 new episodes, 16 per family, all frozen before development; these are new initial conditions, not new task families. Receding horizon: 64 proposals, 1 second horizon, first 50ms action executed, then replan. The identical generator mixes zero, shifted previous winner, goal-directed proposals and smooth random perturbations; common episode/time random seeds, but proposals evolve with each method's own state and warm start. No future reference states are used. This tests this particular controller, not an Oxford or standard Push-T reproduction.

Low/medium/high prediction steps .0025/.00125/.000625s. Top32 screens all64 at .01s, evaluates retained32 at .000625s. Execution step .0003125s; four development episodes additionally use .00015625s. Success: position <=2cm AND wrapped yaw <=10 degrees for 10 consecutive samples (0.5s); timeout10s; exit if object or pusher XY exceeds +/-0.5m. Perfect state sensing, simplified planar drag, no obstacles or robot arm. Success is a pose criterion without an additional velocity threshold.

Planning is idealized as instantaneous for control. Measured wall time includes proposal generation, rollout, selection and copying selected sequence; excludes simulation execution, file IO and startup. One run per method/episode, randomized method order within each episode; latency samples are correlated. Percentiles pool planning calls (longer episodes contribute more); not repeated independent hardware benchmarks. No delay-injected or real-time success claim.

## Results
{common}
*Elapsed time is observed termination time, capped at10s; not successful-completion time for failures. End errors are measured at each method's own stopping time. Bootstrap uses10000 paired episode resamples stratified by family; descriptive uncertainty, not broad generalization or multiple-comparison-adjusted inference. First-action differences compare identical initial states and proposals; later proposals are not identical after closed-loop divergence.

## Interpretation limits
Fine prediction is a baseline, not a guaranteed winning controller or physical ground truth. The execution sensitivity check covers four development cases only and cannot certify all confirmation outcomes. Any difference is conditional on candidate sampling, this objective, success tolerance and simplified model. Ranking reversals alone do not establish a publishable contribution. Do not tune on this confirmation set and relabel it unseen.

All {len(records)} saved episode trajectories passed the post-run checks listed in audit.json. Source snapshots, model, frozen cases, per-episode traces and raw latencies are in results/push_t_closed_loop_gate. Numerical experiment only; no new literature/novelty audit performed.
'''
zh=f'''# 闭环任务意义验证 — 2026-11-05

## 实验定义
细步长开发集成功{gate['successes']}/16，预先规定至少12/16后运行确认。64个新确认任务每类16个，在开发前已冻结；仅初值是新的，任务家族不是全新。64条候选、1秒预测，只执行首50毫秒后重规划。所有方法使用相同候选生成规则（零动作、上次最优轨迹平移、朝向目标的动作、平滑随机扰动）和共同随机种子。状态分岔后候选随各自状态及热启动变化，不强行使用相同绝对轨迹。

low/medium/high预测步长分别为.0025/.00125/.000625秒；top32先以.01秒筛64条，再以.000625秒精算32条。执行环境步长.0003125秒，另取四个开发案例以.00015625秒作敏感性检查。位置误差<=2cm且角度误差<=10度连续保持0.5秒视为成功；10秒截止；物体或推杆XY超出±0.5米终止。成功没有额外速度阈值。理想状态观测、平面阻尼摩擦模型，无机械臂、真实地板接触或障碍物。

控制中暂不注入计算延迟；计时包含候选生成、仿真评估、选择及复制动作，不含执行环境积分、文件保存和初始化。每任务每方法运行一次，方法顺序随机。计时样本相关，百分位按全部规划调用汇总，长任务权重更高。超过50ms的比例不是实测实时闭环失败率。

## 结果
{common}
表中elapsed是各方法终止时长（最长10秒），失败任务不解释为成功完成时间。终点误差在各自终止时刻测量。成功率差区间采用按四个家族分层的10000次配对episode自助采样，只作描述，不是总体可靠性保证或多重检验校正结果。首动作比较发生在完全相同的初态和候选集；后续候选不再相同。

## 限制与审计
细步长规划不是物理真值，也不保证闭环表现最好。执行半步检查只有4个开发案例，不能证明全部确认任务数值收敛。结论依赖当前采样控制器、代价函数、容差和简化模型。旧排名反例不自动构成论文贡献；本确认集后续不可重复声称为未见数据。

已独立重算{len(records)}条保存轨迹的位姿误差、连续成功条件、越界、控制限幅及数据完整性，并检查冻结数据与执行源码哈希。审计见results/push_t_closed_loop_gate/audit.json。代码、冻结初值、原始时延、轨迹和执行源码快照均保留。本次未进行新的文献新颖性审查。
'''
(ROOT/'report'/'PUSH_T_CLOSED_LOOP_GATE_REPORT_EN.md').write_text(en,encoding='utf8')
(ROOT/'report'/'PUSH_T_CLOSED_LOOP_GATE_REPORT.md').write_text(zh,encoding='utf8')
if (OUT/'bridge_summary.json').exists():
    bridges=read(OUT/'bridge_summary.json');dproto=read(OUT/'diagnostic_protocol.json');diagnostics=[]
    extra=[]
    for phase in ['bridge','bridge_half','diagnostic']:
      for p in sorted(OUT.glob(phase+'_*.json')):
        if p.name.startswith('bridge_half') and phase=='bridge':continue
        if p.name in ['bridge_summary.json','bridge_protocol.json','diagnostic_protocol.json']:continue
        r=read(p)
        if 'case' not in r:continue
        t=np.load(p.with_suffix('.npz'))['trace']
        goal=np.load(ROOT/'results'/'push_t_batch148_audit'/'input.npz')['goal'] if phase.startswith('bridge') else np.array(cases[r['case']]['goal'])
        errors=np.linalg.norm(t[:,:2]-goal[:2],axis=1)
        angles=abs(np.arctan2(np.sin(t[:,2]-goal[2]),np.cos(t[:,2]-goal[2])))
        assert np.allclose(errors,t[:,12]) and np.allclose(angles,t[:,13])
        hold=0;ok=False
        for flag in ((errors<=.02)&(angles<=np.deg2rad(10))):
            hold=hold+1 if flag else 0;ok|=hold>=10
        assert bool(ok)==r['success'] and len(t)==r['steps']
        extra.append(p.name)
        if phase=='diagnostic':
            base=read(OUT/f"confirm_{r['case']}_{r['method']}.json")
            diagnostics.append(dict(case=r['case'],method=r['method'],base_success=base['success'],half_success=r['success'],base_error=base['position_error'],half_error=r['position_error']))
    appendix='\n\n## Exploratory sensitivity / 探索性敏感性检查\n\n'
    appendix+='Archived148 uses its original64 proposals only at the first decision; subsequent decisions use the new rolling controller. This is not a pure first-action intervention because later methods differ too. / 旧148仅首轮使用原64候选，随后使用新闭环控制器；后续方法也不同，因此不是只改变首动作的因果干预。\n\n'
    appendix+='| Execution step | Method | First choice | Success | Duration s | Final error m |\n|---|---|---:|---|---:|---:|\n'
    for r in bridges:appendix+=f"| {r['execution_dt']} | {r['method']} | {r['first_choice']} | {r['success']} | {r['duration']:.2f} | {r['position_error']:.4f} |\n"
    appendix+='\nPost-hoc half-step checks use the first eight (or fewer) disagreement IDs; selection is outcome-dependent, not a new test set. / 事后取最多8个成功标签不一致的任务复查，按编号选取；不是新确认集。\n\n'
    appendix+='| Case | Method | Success base / half | Error base / half (m) |\n|---|---|---|---|\n'
    for r in diagnostics:appendix+=f"| {r['case']} | {r['method']} | {r['base_success']} / {r['half_success']} | {r['base_error']:.4f} / {r['half_error']:.4f} |\n"
    flips=sum(r['base_success']!=r['half_success'] for r in diagnostics)
    appendix+=f'\nLabel flips after halving execution step / 执行步长减半后的标签变化：{flips}/{len(diagnostics)}. Additional trajectories audited / 额外审计轨迹：{len(extra)}.\n'
    save(OUT/'diagnostic_summary.json',dict(selected=dproto,results=diagnostics,label_flips=flips,extra_trajectories_audited=len(extra)))
    for suffix in ['','_EN']:
        p=ROOT/'report'/f'PUSH_T_CLOSED_LOOP_GATE_REPORT{suffix}.md'
        with p.open('a',encoding='utf8') as f:f.write(appendix)
zh_decision='''

## 去留判断
本确认集不支持“提高预测积分精度即可提高闭环任务成功率”，也不支持据此重启接触局部加密加速论文。粗、中、细和top32成功数分别为57、55、54、55；粗与细的配对成功率差区间包含0，不能宣称粗步长普遍更优。细步长p95超过50ms，本实验没有计入延迟，不能将理想闭环成功率当作可部署结果。

旧148的桥接结果只能证明在这一控制器下个案有差异；后续重规划及热启动也随方法变化，不能把所有后果归因于第一次候选排名。top32在执行半步检查中恢复成功，说明单一离散化设置的失败标签不可靠。确认集差异任务的半步结果也须一并报告。

下一步建议停止为当前“修复排名=改善任务”的主张追加算法。若保留此方向，需先说明真实任务的控制器瓶颈，并验证任务/接触模型，而非继续调当前反例。此次首动作在多数普通任务中相同；这组任务不是专门冻结的独立困难排名分布，因此不证明所有排名误差均可被重规划消除。没有论文级创新或真实机器人结论。
'''
en_decision='''

## Research decision
This confirmation set does not support improving task success merely by refining prediction integration, or restarting the contact-local acceleration paper. Success counts are57/55/54/55 for low/medium/high/top32. The low-minus-high paired interval includes zero; low is not established as universally superior. High p95 exceeds the50ms period and delay was not injected, so idealized success is not a deployment result.

Archived148 has controller-dependent outcome differences, but later replanning and warm starts also change; this does not isolate the causal effect of its first ranking reversal. Top32 changes from failure to success after halving execution step. Selected confirmation discrepancies must also be interpreted with their sensitivity results.

Pause algorithm work motivated by ranking repair alone. Further work requires a meaningful task/controller bottleneck and model validation. Most initial actions coincide in these ordinary tasks; they are not a newly frozen distribution of specifically difficult ranking cases. The experiment does not prove that replanning always removes ranking errors, establish novelty, or validate a real robot.
'''
if (OUT/'bridge_summary.json').exists():
    for suffix,decision in [('',zh_decision),('_EN',en_decision)]:
        with (ROOT/'report'/f'PUSH_T_CLOSED_LOOP_GATE_REPORT{suffix}.md').open('a',encoding='utf8') as f:f.write(decision)
print(json.dumps(dict(gate=gate,sensitivity=sensitivity,summary=summary,paired=paired),indent=2))
