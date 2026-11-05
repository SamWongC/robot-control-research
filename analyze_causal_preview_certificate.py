"""Independent support checks of executable causal gains and trajectory audit."""
from pathlib import Path
import csv,hashlib,json
import numpy as np
import causal_preview_certificate as exp

ROOT=Path(__file__).resolve().parent
OUT=exp.OUT
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def projected_controller(controller):
    # Runtime ignores these slots; verify the exact executable causal structure.
    result={}
    for d,c in controller.items():
        p={k:v.copy() for k,v in c.items()};p['v'][0]=exp.FIRST;p['J'][0]=0
        for k in range(len(p['v'])):
            p['K'][k,0]=0;p['K'][k,k+1:]=0
        result[d]=p
    return result

def main():
    config=read(OUT/'config.json');manifest=read(OUT/'frozen_manifest.json');prov=read(OUT/'validation_provenance.json')
    assert digest(ROOT/'causal_preview_certificate.py')==manifest['source_sha256']==config['source_sha256']
    assert digest(OUT/'config.json')==manifest['config_sha256'] and digest(OUT/'cells.json')==manifest['cells_sha256']
    assert digest(OUT/'frozen_manifest.json')==prov['manifest_sha256']
    assert digest(OUT/'validation_inputs.npz')==prov['input_sha256']
    assert digest(OUT/'validation_episodes.json')==prov['episodes_sha256']
    for p,h in config['dependencies'].items():assert digest(ROOT/p)==h
    for p,h in manifest['policy_sha256'].items():assert digest(OUT/p)==h
    cells=read(OUT/'cells.json');supports=[];policy={}
    for cell in cells:
        if cell['classification']!='certified_policy':continue
        c=projected_controller(exp.load_controller(cell));policy[cell['name']]=c
        H,h=exp.uncertainty(cell['n']+2);worst=0.;worstrow=''
        for d,cc in c.items():
            for label,nom,coef in exp.constraints_numpy(**cc,d=d,n=cell['n'],ep=cell['position_tolerance']):
                val,_=exp.support(coef,H,h)
                if abs(nom)+val>worst:worst=abs(nom)+val;worstrow=f'd{d}/{label}'
        assert worst<1-1e-7
        supports.append({'cell':cell['name'],'worst_executable_normalized_bound':worst,
                         'verified_margin':1-worst,'worst_row':worstrow})
    # Every saved witness belongs to the uncertainty polytope.
    for cellname in manifest['validation_cells']:
        cell=next(c for c in cells if c['name']==cellname);H,h=exp.uncertainty(cell['n']+2)
        for w in read(OUT/f'{cellname}_witnesses.json'):
            assert np.max(H@np.array(w['q'])-h)<1e-8
    inputs=np.load(OUT/'validation_inputs.npz');episodes=read(OUT/'validation_episodes.json');groups={}
    # Check actual fresh disturbances against previous test records.
    previous=np.load(ROOT/'results'/'first_action_scan'/'test'/'paired_inputs.npz')
    assert not any(np.array_equal(a[:3],b) for a in inputs['disturbances'] for b in previous['disturbances'])
    with (OUT/'validation_trajectories.csv').open(newline='') as f:
        for r in csv.DictReader(f):groups.setdefault((r['cell'],r['case'],int(r['true_delay'])),[]).append(r)
    maxdyn=0.;maxcommand=0.;steps=0
    for m in episodes:
        cell=next(c for c in cells if c['name']==m['cell']);t=cell['n']+2;rr=groups[(m['cell'],m['case'],m['true_delay'])]
        assert len(rr)==t
        if m['case'].startswith('random_'):
            i=int(m['case'].split('_')[1]);x0=inputs['initial'][i];ws=inputs['disturbances'][i,:t];errors=inputs['errors'][i,:t]
        else:
            i=int(m['case'].split('_')[1]);q=np.array(read(OUT/f'{cell["name"]}_witnesses.json')[i]['q'])
            x0=q[:2]*exp.INITIAL_RADIUS;ws=q[2:2+t]*exp.old.W;errors=q[2+t:].reshape(t,2)*exp.old.NOISE
        state=x0.copy();history=[];ys=[];zs=[np.zeros(2)];pp=0.;vv=0.;energy=0.;umax=0.;dhat=None
        for k,r in enumerate(rr):
            assert int(r['k'])==k
            x=np.array([float(r['p']),float(r['v'])]);nx=np.array([float(r['next_p']),float(r['next_v'])])
            np.testing.assert_allclose(x,state,atol=1e-12,rtol=0)
            y=np.array([float(r['measured_p']),float(r['measured_v'])])
            np.testing.assert_allclose(y,state+errors[k],atol=1e-12,rtol=0);ys.append(y)
            u=float(r['command']);applied=float(r['applied']);w=float(r['disturbance'])
            assert abs(w-ws[k])<1e-12
            if k==0:expected=exp.FIRST
            else:
                if k==1:
                    candidates=[d for d in (0,1) if exp.old.candidate_feasible(ys,history,d)]
                    assert candidates==[m['true_delay']];dhat=candidates[0]
                idx=k-1-dhat;past=history[idx] if idx>=0 else 0.
                zs.append((ys[-1]-exp.old.A@ys[-2]-exp.old.B*past)/exp.Z_SCALE)
                c=policy[cell['name']][dhat]
                expected=c['v'][k]+c['J'][k]@(ys[0]/exp.old.NOISE)+sum(c['K'][k,j]@zs[j] for j in range(1,k+1))
                assert int(r['identified_delay'])==dhat
            maxcommand=max(maxcommand,abs(expected-u))
            expected_applied=u if m['true_delay']==0 else (history[-1] if history else 0.)
            assert abs(applied-expected_applied)<1e-12
            physical=state+np.array([.05*state[1]+.00125*(applied+w),.05*(applied+w)])
            maxdyn=max(maxdyn,float(np.max(np.abs(nx-physical))))
            if k<cell['n']:pp=max(pp,abs(nx[0]));vv=max(vv,abs(nx[1]));energy+=.05*u*u
            history.append(u);state=nx;umax=max(umax,abs(u));steps+=1
        err=np.abs(state-exp.old.TARGET)
        success=bool(err[0]<=cell['position_tolerance']+1e-9 and err[1]<=.003+1e-9 and pp<=.01+1e-9 and vv<=.06+1e-9 and umax<=2+1e-9 and dhat==m['true_delay'])
        assert success==m['success'] and success
        np.testing.assert_allclose(err,[m['position_error_m'],m['velocity_error_m_s']],atol=1e-12,rtol=0)
        assert abs(energy-m['prep_energy'])<1e-12
    assert maxdyn<1e-12 and maxcommand<1e-10
    audit={'certified_policies_rechecked':supports,'episodes_audited':len(episodes),'transitions_audited':steps,
        'max_scalar_dynamics_residual':maxdyn,'max_executable_control_residual':maxcommand,
        'all_frozen_hashes_verified':True,'fresh_inputs_distinct':True,
        'first_step_identification_and_prefix_only_control_verified':True,'no_state_queue_reset_or_command_clipping':True}
    (OUT/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap,BoundaryNorm
    matrix=np.array([[{'proved_obstruction':0,'unresolved':1,'certified_policy':2}[next(c for c in cells if c['n']==n and c['position_tolerance']==ep)['classification']] for n in exp.NS] for ep in exp.EPS])
    fig,ax=plt.subplots(figsize=(9,6));cmap=ListedColormap(['#d97878','#d1d1d1','#77bd94'])
    ax.imshow(matrix,origin='lower',aspect='auto',cmap=cmap,norm=BoundaryNorm([-.5,.5,1.5,2.5],3))
    ax.set(xticks=np.arange(len(exp.NS)),xticklabels=[f'{n*.05:.2f}' for n in exp.NS],
        yticks=np.arange(len(exp.EPS)),yticklabels=[f'{ep*1000:g}' for ep in exp.EPS],
        xlabel='Preview [s] (discrete settings)',ylabel='Position tolerance [mm] (discrete settings)',
        title='Fixed +0.05 first action: causal-policy certificate map')
    for j,ep in enumerate(exp.EPS):
        for i,n in enumerate(exp.NS):
            label={0:('All-policy\nobstruction' if n==0 else 'Fixed-probe\nobstruction'),1:'Unresolved',2:'Verified\npolicy'}[matrix[j,i]]
            ax.text(i,j,label,ha='center',va='center',fontsize=8)
    fig.tight_layout();fig.savefig(OUT/'causal_feasibility_map.png',dpi=180);plt.close(fig)
    table='| Preview (s) | Position tolerance (mm) | Classification | Executable verified margin |\n|---:|---:|---|---:|\n'
    for cell in cells:
        if cell['position_tolerance']==.0002 or cell['n']==1:
            v=next((s['verified_margin'] for s in supports if s['cell']==cell['name']),None)
            table+=f"| {cell['n']*.05:.2f} | {cell['position_tolerance']*1000:g} | {cell['classification']} | {v if v is not None else '—'} |\n"
    valtable='| Setting | Initial scope | Validation successes | Max position error (mm) | Max velocity error (m/s) |\n|---|---|---:|---:|---:|\n'
    for g in read(OUT/'validation_summary.json'):
        valtable+=f"| {g['cell']} | {g['scope']} | {g['success_count']}/{g['episodes']} | {g['max_position_error_m']*1000:.6f} | {g['max_velocity_error_m_s']:.6f} |\n"
    selected=[next(c for c in cells if c['name']==x) for x in manifest['validation_cells']]
    core=next(c for c in selected if c['position_tolerance']==.0002)
    relaxed=next(c for c in selected if c['n']==1)
    common=f'''\n{table}\n![Causal feasibility map](../results/causal_preview_certificate/causal_feasibility_map.png)\n\n{valtable}

Source SHA-256: `{config['source_sha256']}`.

Frozen manifest SHA-256: `{prov['manifest_sha256']}`.
'''
    zh=f'''# 因果反馈充分条件：预告时间与任务精度边界

日期：2026-11-04。状态：标准鲁棒仿射反馈构造的数学充分条件与浮点数值证书，不是精确算术机器证明，也不声明论文创新。

## 结果

原位置容差 0.2 mm、速度容差 0.003 m/s 下，{core['n']*.05:.2f} s 预告已构造可执行策略并通过连续不确定集的独立支持函数核验。保持 0.05 s 预告时，放宽位置容差到 {relaxed['position_tolerance']*1000:g} mm 也有证书；速度容差与其他输入、外扰、测量误差边界不变。0.2375 与 0.25 mm 两点只标为尚不能判定，不能当成所有策略不可行。

## 精确的问题范围

沿用双积分器 dt=0.05 s，d=0/1 固定，|u|≤2 m/s²；|w|≤0.02 m/s²，逐步变化≤0.01 m/s²；测量误差逐分量为 (1e-5 m,1e-4 m/s)。目标始终是绝对状态 (0.002 m,0.08 m/s)，截止为预告 N 步加原任务两步。准备状态 |p|≤0.01 m、|v|≤0.06 m/s，包含任务开始状态；无终点后的稳定或持续安全要求。

除原来精确零物理初态外，证书额外覆盖 |p0|≤2e-5 m、|v0|≤2e-4 m/s；这是明确的额外初态扰动覆盖，不能由测量噪声界自动推出。旧物理零初态是其子集。对原零初态下可能的初始测量 y0∈[−ε,+ε]，旧测量盒中的状态也落在这个额外初态范围内。控制器仍只使用测量，不读取真实初态。验证分别报告原零初态与新增扰动，避免混合比较。

## 命题：可核验的充分条件

固定首步 a=+0.05 m/s²。它严格超过保证区分阈值 0.048。根据 y0、y1 和发送指令的候选 LP，k=1 时得到唯一正确延迟。对每个候选分支预先合成下列控制律，实际只执行辨识到的分支：

u0=a；对 k≥1，u[k]=v[d,k]+J[d,k]·(y0/ε)+sum(t=1..k) K[d,k,t]·z[t]。

归一化创新量为 z[t]=(y[t]−A y[t−1]−B u[t−1−d])/s，其中 s=|B|W+ε+|A|ε=(0.00005,0.0012)。由系统方程消去状态和已发输入，可得 z[t]=(B w[t−1]+e[t]−A e[t−1])/s。它只含当前及过去已产生的不确定性，因此 u[k] 不依赖未来；延迟队列完全由已发送历史重建，没有重置。

将初态、外扰和测量误差写成归一化向量 q，满足 Hq≤h：分量盒界与全部 |w[k+1]−w[k]|≤0.01。两个延迟分支的每个输入、准备状态和终点误差都可以写为标量 c+gq。将它除以对应约束界后，要求 |c|+max(Hq≤h)gq≤1。

若对每行存在 λ≥0，Hᵀλ=g、hᵀλ+|c|≤1−m，且 m>0，则所有允许初态、噪声和变化外扰都满足输入/准备/终点要求。证明：λᵀHq≤λᵀh 给出 gq 的统一上界；不确定集中心对称，同时界住负方向；把界代回因果递推即可。唯一延迟判别保证实际选择的是被验证分支。该命题给出有限时域任务保证，不推导递归可行性或无限时域稳定性。

## 计算与独立核验

合成用鲁棒 LP 的对偶变量最大化归一化严格裕度，CLARABEL 只负责求候选解。随后独立用 NumPy 重建状态与输入系数，SciPy/HiGHS 对每行在完整连续 Hq≤h 上重新求最坏支持；检查对偶残差、非负性与因果零结构。最终审计把运行时不使用的未来反馈系数精确置零，重新核验实际执行映射。只有最坏归一化值≤1−1e-7 且数值残差通过时才标为 verified_policy。

本轮 48 个设置中，36 个有独立核验策略，10 个有解析阻碍，2 个尚不能判定。求解器报 infeasible 的两点仍属于未决，因为这里搜索的是限定的仿射策略族，且没有独立核验的全策略不可行证明。{sum(c.get('solver_status')=='optimal_inaccurate' for c in cells)} 个点求解器为 optimal_inaccurate，但仍通过独立支持函数核验；不以求解器状态单独认定证书。浮点支持 LP 不是区间算术；严格数值裕度提供可检查证据，但不表述成精确机器证明。

## 不可行区域的作用域

N=0：此前名义模型的必要首动作集合分离，在本图全部容差点排除任何因果策略的确定性任务保证；这是全策略阻碍。

N=1：同前缀 w0=0.02、两条合法未来 (w1,w2)=(0.02,0.02) 与 (0.01,0) 要求同一个后续动作 b。同一个正首步 a 必须满足 b≤(p*+εp−0.00375a−0.000225)/0.00125，同时 b≥(v*−εv)/0.05−a−0.03。合并得 a≤400εp+10εv−0.075。固定 a=0.05、εv=0.003 时必要 εp≥0.0002375 m。因此 0.2、0.225 mm 点对固定首步策略不可保证；即使给控制器真实延迟和精确零初态，这个未来分支冲突仍成立。它不排除采用其他首步动作、允许不唯一延迟的其他策略。

原 0.2 mm 精度下，N=1 的必要界 |a|≤0.035 与保证首步区分的 |a|>0.048 冲突，而 N=2 已有充分策略。因此在“首步保证唯一辨识后控制”的限定方案内，0.1 s 是最短整数采样预告；没有证明它是任意因果未知延迟控制器的全局最短预告。
{common}

## 新轨迹和最坏支持点验证

全部策略和网格分类先冻结并记录源代码、依赖、策略文件哈希，再用新种子 2026110701 生成验证数据。每个选定设置用 64 条原零初态轨迹与 64 条额外扰动初态轨迹，每条配两个真实延迟；另执行支持函数最坏优化点。这些连续集支持点可以同时含边界测量误差、边界初态和变化外扰，不是只抽随机噪声。新随机前缀与上一轮测试检查不重复。

共 {len(episodes)} 次实现验证全部通过，{steps} 步标量物理递推、测量重建、首步候选判别、观测前缀控制重建、输入执行顺序、准备/终点约束、动作能量通过独立审计。没有指令饱和裁剪来掩盖违反。仿真只核验实现；保证证据来自上述连续集条件与支持函数核验。

## 研究意义与限制

当前已得到一个命题、可执行策略和带未决区域的边界图，说明增加预告或放宽精度可以恢复可保证任务。但这主要是标准有限时域鲁棒控制工具对构造例子的应用，不构成 RA-L 创新确认。地图不是全局精确可行域，未决不能涂成不可行，不能把限定策略族的最短预告称为全局最优。继续立论文前需要检查更一般的可恢复任务集合、任务驱动辨识与机器人场景中的非平凡贡献。

## 文件与复现

causal_preview_certificate.py 分 build / validate；analyze_causal_preview_certificate.py 独立核验实际因果策略并生成报告/图；test_causal_preview_certificate.py 包含五项针对性检查。完整测试日志 causal_preview_tests.log。沿用 requirements-reproduction-lock.txt，无新增依赖。

results/causal_preview_certificate/ 保存配置、cells.json、每个已核验策略 NPZ 与支持点、冻结清单、新验证输入/轨迹/逐案例汇总、来源哈希、audit.json 和 causal_feasibility_map.png。build/validate 拒绝覆盖已完成的冻结结果，复现应在独立副本运行。旧实验未覆盖。
'''
    en=f'''# Causal feedback sufficiency: preview time versus task precision

Date: 2026-11-04. Mathematical sufficient conditions and floating-point certificates using standard robust affine feedback; not an exact-arithmetic machine proof or an originality claim.

## Result and scope

At the original .2 mm position/.003 m/s velocity tolerances, {core['n']*.05:.2f} s preview admits an executable strategy with independently verified continuous-set support bounds. Keeping .05 s preview and relaxing position tolerance to {relaxed['position_tolerance']*1000:g} mm also admits one. The .2375 and .25 mm points remain unresolved, not globally infeasible.

Preserve the double integrator dt=.05 s, fixed d=0/1, input bound 2 m/s², disturbance amplitude .02 m/s² and increment .01 m/s², componentwise measurement errors (1e-5 m,1e-4 m/s). The absolute target is (.002 m,.08 m/s), deadline N+2, preparation bounds (.01 m,.06 m/s), including task start. No post-terminal safety or stability requirement is added.

Beyond the original exact zero physical initial state, the certificate explicitly covers |p0|≤2e-5 m and |v0|≤2e-4 m/s. This extra initial perturbation coverage is not inferred automatically from measurement-noise bounds. It contains the original zero state, and for original initial observations y0∈[-ε,ε] it contains their measurement-box states. Control uses measured y0, never true initial state. Validation separates original-zero from additional perturbed initial states.

## Proposition: checkable sufficient condition

Fix u0=a=.05 m/s², strictly above the .048 guaranteed separation threshold. The prefix membership LP identifies the unique correct delay at k=1. For each delay synthesize a branch and execute only the identified one:

u[k]=v[d,k]+J[d,k](y0/ε)+sum(t=1..k)K[d,k,t]z[t], k≥1.

The normalized innovation z[t]=(y[t]−A y[t−1]−B u[t−1−d])/s, with s=(.00005,.0012), equals (B w[t−1]+e[t]−A e[t−1])/s. Thus it contains only uncertainty already generated and the command is causal. Pending inputs are reconstructed from sent history and are not reset.

Normalize initial perturbations, disturbances and sensor errors into q with Hq≤h, including every within-horizon disturbance-rate constraint. Each normalized input, preparation-state or terminal-error row becomes c+gq. If there exists λ≥0 for each row with Hᵀλ=g and hᵀλ+|c|≤1−m for m>0, every allowed realization satisfies the task constraints. Indeed λᵀHq≤λᵀh bounds gq, symmetry bounds its negative, and substitution in the causal dynamics completes the argument. Correct first-step identification selects the verified branch. This is a finite-horizon condition, not recursive feasibility or infinite-horizon stability.

## Synthesis and independent numerical verification

Use a robust dual LP to maximize normalized strict margin with CLARABEL. Independently reconstruct coefficients with NumPy and maximize every support over the entire continuous polytope with SciPy/HiGHS. Check dual residual/nonnegativity and causal zero structure. The final audit projects unused future-feedback slots exactly to zero and rechecks the actual executable map. Acceptance requires an independent worst normalized bound≤1−1e-7 plus residual checks.

Of 48 settings, 36 have verified policies, 10 have analytic obstructions and two are unresolved. Solver infeasibility at the latter two does not prove all-policy impossibility: only a restricted affine family was searched. {sum(c.get('solver_status')=='optimal_inaccurate' for c in cells)} solves report optimal_inaccurate but pass the independent support checks; solver status alone never certifies a policy. Floating-point LP support is not interval/exact arithmetic. Strict numerical margins provide checkable evidence, not a formal machine proof.

## Obstruction scopes

At N=0, separated nominal necessary first actions rule out a deterministic task guarantee for every causal policy over all plotted tolerances.

At N=1, a shared prefix w0=.02 and future branches (w1,w2)=(.02,.02) versus (.01,0) require a common second action b. Position in the first branch gives b≤(p*+εp−.00375a−.000225)/.00125; velocity in the second gives b≥(v*−εv)/.05−a−.03. Hence a≤400εp+10εv−.075. With a=.05 and εv=.003 this requires εp≥.0002375 m. The .2/.225 mm settings therefore obstruct the fixed-first-action strategy, even with known delay and exact zero initial state. This does not exclude other first actions or policies retaining delay ambiguity.

At the original .2 mm tolerance, the N=1 necessary |a|≤.035 contradicts guaranteed first-step separation |a|>.048, whereas N=2 has a sufficient policy. Thus .1 s is the minimum integer-sample preview in the restricted uniform-first-step-identification scheme, not a proven global minimum over arbitrary unknown-delay causal controllers.
{common}

## Fresh implementation validation

Freeze every policy, classification and source/dependency hash before generating validation inputs (seed 2026110701). Each selected setting uses 64 fresh original-zero and 64 perturbed-initial records, each paired with two delays, plus executable worst-support optimizers. These include boundary sensor errors, initial perturbations and rate-constrained disturbances. Fresh random prefixes are distinct from the previous test.

All {len(episodes)} episodes pass. Independently audit {steps} transitions through scalar dynamics, measurement reconstruction, causal identification, prefix-only command reconstruction, queue ordering, preparation/terminal constraints and energy. No command clipping conceals violations. Simulation checks the implementation; the continuous-set sufficient condition/support checks supply the guarantee evidence.

## Interpretation and artifacts

The deliverables are a precise sufficient-condition proposition, an executable causal policy and a map retaining unresolved cells. Additional preview or relaxed precision can restore certified performance. This is primarily a standard robust-control construction on a synthetic plant, not confirmed RA-L novelty or a globally exact feasibility frontier. Broader recoverability conditions and a nontrivial robotics contribution remain necessary before claiming a paper contribution.

causal_preview_certificate.py has build/validate phases; analyze_causal_preview_certificate.py audits executable maps and writes reports/figure; test_causal_preview_certificate.py provides five targeted checks. Full regression: causal_preview_tests.log. Existing requirements-reproduction-lock.txt environment; no new dependencies.

results/causal_preview_certificate/ contains config, grid classifications, policy NPZs/support witnesses, frozen manifest, validation inputs/trajectories/episodes/summary, provenance, audit and causal_feasibility_map.png. Completed frozen runs cannot be overwritten by the runner; reproduce in an isolated copy. Historical outputs are preserved.
'''
    report=ROOT/'report';report.mkdir(exist_ok=True)
    (report/'CAUSAL_PREVIEW_CERTIFICATE_REPORT.md').write_text(zh,encoding='utf-8')
    (report/'CAUSAL_PREVIEW_CERTIFICATE_REPORT_EN.md').write_text(en,encoding='utf-8')
    print(json.dumps({'certificates_independently_rechecked':len(supports),'episodes_audited':len(episodes),
          'transitions_audited':steps,'max_scalar_residual':maxdyn,'max_control_residual':maxcommand},indent=2))
    print('Saved bilingual proposition, scope-aware map and audited policy reports.')

if __name__=='__main__':main()
