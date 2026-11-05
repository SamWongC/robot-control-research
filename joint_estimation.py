"""Experiment 4: profiled constant-disturbance least squares, no learning."""
from collections import deque
from pathlib import Path
import contextlib, csv, hashlib, io, json, platform, sys
import numpy as np
import osqp, scipy
from experiment import A, B, DT, STEPS, HORIZON, DelayQueue
from delay_mismatch import BoxMPC, TRUE_DELAY, LIMIT

WINDOW=20
CANDIDATES=tuple(range(9))
SCENARIOS=('clean','plus025','plus050','minus025','minus050','slow_hump')
MODES=('fixed','raw','joint','joint_ff','fixed_ff')


def disturbance(k, scenario):
    if not 100 <= k < 160 or scenario=='clean': return 0.
    if scenario=='slow_hump': return .5*np.sin(np.pi*(k*DT-5)/3)
    return {'plus025':.25,'plus050':.5,'minus025':-.25,'minus050':-.5}[scenario]


class Estimator:
    def __init__(self, joint):
        self.joint=joint
        self.commands=[]
        self.residuals=deque(maxlen=WINDOW)
        self.estimate=0
        self.biases=np.zeros(9)
        self.scores=np.zeros(9)

    def observe(self, before, after, command):
        j=len(self.commands)
        self.commands.append(float(command))
        y=(after[1]-before[1])/DT
        pred=np.array([self.commands[j-d] if j>=d else 0. for d in CANDIDATES])
        self.residuals.append(y-pred)
        r=np.array(self.residuals)
        self.biases=r.mean(axis=0)  # unconstrained LS intercept for each delay
        self.scores=np.mean((r-self.biases if self.joint else r)**2,axis=0)
        if len(self.commands)>=WINDOW:
            if self.scores[self.estimate]>self.scores.min()+1e-12:
                self.estimate=int(np.argmin(self.scores))


class AffineMPC(BoxMPC):
    def __init__(self, delay):
        super().__init__(delay)
        self.bias=0.
        z=np.zeros(2)
        response=[]
        for _ in range(HORIZON):
            z=A@z+B[:,0]
            response.extend(z)
        self.bias_response=np.array(response)

    def linear_term(self,x,history):
        return super().linear_term(x,history)+2*self.G.T@(self.weights*self.bias_response*self.bias)


def run(scenario,mode):
    ctrls={d:AffineMPC(d) for d in CANDIDATES}
    raw,joint=Estimator(False),Estimator(True)
    queue=DelayQueue(TRUE_DELAY)
    history=[]
    x=np.zeros(2)
    states=[x.copy()]
    rows=[]
    for k in range(STEPS):
        d=TRUE_DELAY if mode.startswith('fixed') else (raw.estimate if mode=='raw' else joint.estimate)
        b=joint.biases[d] if mode.endswith('_ff') and k>=WINDOW else 0.
        ctrls[d].bias=float(b)
        plan,elapsed,info=ctrls[d].solve(x,history)
        u=float(plan[0])
        applied=queue.step(u)
        w=disturbance(k,scenario)
        nx=A@x+B[:,0]*(applied+w)
        rows.append([k*DT,*x,u,applied,w,d*DT,b,raw.estimate*DT,joint.estimate*DT,
                     joint.biases[joint.estimate],*raw.scores,*joint.scores,*joint.biases,
                     *nx,elapsed,info.prim_res,info.dual_res])
        raw.observe(x,nx,u)
        joint.observe(x,nx,u)
        history.append(u)
        states.append(nx.copy())
        x=nx
    data,states=np.array(rows),np.array(states)
    err=states[:,0]-1
    okay=(np.abs(err)<=.02)&(np.abs(states[:,1])<=.02)
    suffix=np.logical_and.accumulate(okay[::-1])[::-1]
    ii=np.flatnonzero(suffix & (np.arange(STEPS+1)>=160))
    m=dict(scenario=scenario,mode=mode,post5_rmse_m=float(np.sqrt(np.mean(err[100:]**2))),
           peak_post5_m=float(np.max(np.abs(err[100:]))),
           recovery_s=float(ii[0]*DT-8) if len(ii) and ii[0]<=380 else None,
           raw_wrong_5to8=float(np.mean(np.abs(data[100:160,8]-.3)>1e-8)),
           joint_wrong_5to8=float(np.mean(np.abs(data[100:160,9]-.3)>1e-8)),
           joint_bias_rmse_5to8=float(np.sqrt(np.mean((data[100:160,10]-data[100:160,5])**2))),
           joint_wrong_plateau=float(np.mean(np.abs(data[120:160,9]-.3)>1e-8)),
           joint_bias_rmse_plateau=float(np.sqrt(np.mean((data[120:160,10]-data[120:160,5])**2))),
           max_input_violation=float(max(0.,np.max(np.abs(data[:,3:5]))-LIMIT)),
           max_primal_residual=float(data[:,-2].max()),max_dual_residual=float(data[:,-1].max()),
           qp_solves=STEPS)
    return data,states,m


def reports(root,records):
    header='| Scenario | Mode | Post-5 s RMSE (m) | Recovery after 8 s (s) | Raw wrong-delay fraction | Joint wrong-delay fraction |\n|---|---|---:|---:|---:|---:|\n'
    table=header+'\n'.join(f"| {m['scenario']} | {m['mode']} | {m['post5_rmse_m']:.6f} | {m['recovery_s'] if m['recovery_s'] is not None else 'not reached'} | {m['raw_wrong_5to8']:.1%} | {m['joint_wrong_5to8']:.1%} |" for m in records)
    en='''# Experiment 4: Joint Delay and Constant-Disturbance Estimation

Date: 2026-11-04. Non-learning baseline study; not a novel algorithm or real-robot result.

## Method

For every candidate delay d=0..8, compute residual r[j,d]=(v[j+1]-v[j])/0.05-u[j-d] on the last 20 transitions. Profile out a constant disturbance: b[d]=mean(r[:,d]); score[d]=mean((r[:,d]-b[d])²). This is elementary least squares with an intercept, not a full moving-horizon state estimator. The raw baseline scores mean(r²). Both start at zero delay, update only after 20 observations, and retain the previous candidate if within 1e-12 of the minimum. Constant commands, and even linear ramps whose shifted sequences differ by constants, cannot generally separate delay and constant disturbance. No score is a calibrated probability.

## Protocol

Same double integrator, 1 m step target, dt=0.05 s, 400 transitions, horizon 40, Q=diag(20,1), R=0.2, terminal Q, actuator bounds ±2 m/s². No state constraint, noise, randomness or changing true delay (always six steps). Disturbances act for 5≤t<8 s: zero, constant ±0.25 and ±0.50 m/s², or a smooth positive half-sine 0.5*sin(pi*(t-5)/3). These are declared mechanism probes, not held-out tests or hardware-calibrated conditions.

Five modes per scenario (30 rollouts, 12000 QPs): fixed uses known delay without disturbance compensation; raw uses the original single-delay estimate; joint uses the new delay estimate without disturbance compensation; joint_ff additionally predicts constant external acceleration using its selected candidate's bias; fixed_ff uses the true delay and an estimated bias for that candidate, giving an informed disturbance-aware reference. Bias is incorporated in every predicted state transition inside the constrained optimization, not subtracted from the final action. Both estimators run passively on every trajectory. Compare them on fixed trajectories to hold input history constant; compare raw/joint for changes to identification alone, joint/joint_ff for compensation (feedback histories subsequently differ). Fixed modes know true delay; adaptive modes never receive it or true disturbance. All scores and biases at k use transitions completed before k. Negative command indices are zero. Bias is unconstrained; no regularization or online parameter tuning is used.

## Results

TABLE

Wrong-delay fractions above use decisions at 5≤t<8 s; estimates at t=5 s predate the first disturbed transition. Both passive estimators are reported even when they do not control the plant. Post-5 s RMSE uses 301 state samples t=5..20 s. Recovery requires position error≤0.02 m and |velocity|≤0.02 m/s through the end with at least 1 s residence. Plateau diagnostics in metrics.csv use 6≤t<8 s, when the one-second window excludes the disturbance onset. Disturbance RMSE compares the pre-command estimate with disturbance acting in the next transition: change-point lag is included. Commands and delayed actuator inputs are bounded; total acceleration includes external force and may exceed those bounds.

## Limits and Verification

This is a small, noiseless, known-model, constant-delay experiment. Centering residuals can reject constant bias while removing information about delay. A better fit is not necessarily a correct or identifiable delay. Smoothly varying disturbances violate the local-constant assumption; switches at 5/8 s also straddle windows. Direct velocity differencing may amplify measurement noise. No universal improvement, safety, stability or novelty follows from these runs. Existing and new tests cover excitation-based recovery, ramp ambiguity, disturbance response, causality and constrained optimization; see joint_estimation_tests.log. Full configurations and source hashes are saved. Intermediate QP failures and returned input violations raise errors.

## Reproduction and Files

From the project root run `.\\.venv\\Scripts\\python.exe -m unittest -v`, then `.\\.venv\\Scripts\\python.exe joint_estimation.py`. Dependencies: requirements-lock.txt. Results in results/joint_estimation include 30 CSV trajectories, metrics.csv, summary.json, passive_comparison.png, control_comparison.png, and plus050_detail.png. All cases are retained. The literature matrix is LITERATURE_BASELINES.md; it distinguishes abstract-level checks from full-text checks and does not constitute a systematic novelty review.
'''.replace('TABLE',table)
    zh='''# 实验四：延迟与常值外扰联合估计

日期：2026-11-04。非学习基线实验，不是新算法或实机结果。

## 方法

每个候选延迟 d=0..8 的残差为 r[j,d]=(v[j+1]-v[j])/0.05-u[j-d]。最近 20 次转移内，外扰估计 b[d]=残差均值，候选评分=去均值残差的平方均值。原方法直接用残差平方均值。新方法是带截距的基础最小二乘，不是完整的移动窗状态估计器。初始零延迟，满 20 次观测才更新；原候选在最小评分 1e-12 内则保留。恒定指令、甚至移位后仅相差常数的线性斜坡指令，均可能无法区分常值外扰与延迟。评分不是概率。

## 协议

沿用一维双积分系统，1 m 阶跃目标，周期 0.05 s，400 次转移，预测 40 步，Q=diag(20,1)，R=0.2，末端 Q，执行器限制 ±2 m/s²。无状态约束、噪声、随机性；真实延迟始终六步。5≤t<8 s 分别加入零外扰、±0.25、±0.50 m/s² 常值外扰，以及 0.5*sin(pi*(t-5)/3) 正向半正弦缓变外扰。这些是预先声明的机制工况，不是未见测试集，也未根据硬件标定。

每工况五种模式，共 30 条轨迹、12000 次 QP：fixed 知道延迟但不补偿外扰；raw 使用原延迟估计；joint 使用联合估计但不补偿外扰；joint_ff 同时在 MPC 预测中加入所选候选的常值外扰估计；fixed_ff 知道真实延迟并使用该候选的外扰估计，作为知情抗扰参考。外扰进入每个预测状态转移，参与受约束优化，并非事后从输出减去估计值。每条轨迹上同时被动运行两个估计器；在 fixed 轨迹上比较可保持动作历史一致。raw/joint 比较识别机制，joint/joint_ff 比较补偿，但后续反馈轨迹会不同。固定模式知道真实延迟，自适应模式不知道真实延迟或真实外扰。k 时刻的估计仅使用已完成转移，负索引指令为零。外扰估计无界，无正则化或在线调参。

## 结果

表中列为工况、模式、5 s 后 RMSE、8 s 后恢复时间、原估计器与联合估计器的延迟误判比例。clean=无扰动，plus/minus=正负常值，slow_hump=缓变半正弦。

TABLE

误判率使用 5≤t<8 s 发送动作前的估计，t=5 s 估计尚未看到首次扰动转移。即使估计器未参与控制也报告其被动识别结果。5 s 后 RMSE 使用 t=5..20 s 的 301 个状态。恢复标准为位置误差≤0.02 m 且速度绝对值≤0.02 m/s，保持到末尾且至少一秒。metrics.csv 中额外报告 6≤t<8 s 平台期，此时一秒窗口已排除突变起点。外扰 RMSE 比较动作前估计和当前即将作用的外扰，包含突变滞后。执行器动作受限，总加速度另含外力，可能超过指令限制。

## 限制与验证

这是小规模、无噪声、已知模型且真实延迟固定的实验。去均值可消除常值偏差，也可能去掉延迟识别信息；预测拟合更好不等于延迟正确或可辨识。缓变外扰不完全满足窗口内常值假设，5/8 s 突变也会跨越窗口。速度差分在有噪声时可能放大误差。不能由此声称普遍改善、安全、稳定或新颖性。原有及新增测试覆盖充分激励识别、斜坡混淆、外扰响应、因果性与受约束优化；见 joint_estimation_tests.log。配置与代码哈希均保存，求解失败或超容差输入会报错。

## 复现与文件

项目根目录运行 `.\\.venv\\Scripts\\python.exe -m unittest -v`，再运行 `.\\.venv\\Scripts\\python.exe joint_estimation.py`，环境见 requirements-lock.txt。results/joint_estimation 保存 30 组 CSV、metrics.csv、summary.json、passive_comparison.png、control_comparison.png、plus050_detail.png，保留全部工况。文献对照见 LITERATURE_BASELINES.md，区分摘要核查与全文核查，不构成系统新颖性审查。
'''.replace('TABLE',table)
    by={(m['scenario'],m['mode']):m for m in records}
    p=by['plus050','fixed']; raw=by['plus050','raw']; j=by['plus050','joint']; ff=by['plus050','joint_ff']; fff=by['plus050','fixed_ff']; slow=by['slow_hump','fixed']
    en_findings=(f"On the SAME fixed-controller positive-0.50 trajectory, disturbance-period wrong-delay "
        f"fraction falls from {p['raw_wrong_5to8']:.1%} to {p['joint_wrong_5to8']:.1%}; the joint plateau "
        f"fraction is {p['joint_wrong_plateau']:.1%}. In closed loop, post-5 s RMSE is "
        f"{raw['post5_rmse_m']:.6f} m (raw), {j['post5_rmse_m']:.6f} m (joint), "
        f"{ff['post5_rmse_m']:.6f} m (joint_ff), and {fff['post5_rmse_m']:.6f} m (fixed_ff). "
        f"However, recovery after pulse removal is {ff['recovery_s']:.2f} s with joint_ff versus "
        f"{j['recovery_s']:.2f} s with joint: the window retains obsolete disturbance estimates. "
        f"For the smooth hump on the fixed trajectory, joint plateau misidentification is "
        f"{slow['joint_wrong_plateau']:.1%}. Thus constant-bias estimation resolves much of the original "
        "constant-disturbance failure, but not changing-disturbance ambiguity. This elementary baseline "
        "must be included before attributing benefits to AI or confidence mechanisms.\n\n")
    zh_findings=(f"同一条已知延迟控制器的正向 0.50 轨迹上，扰动期误判率从 "
        f"{p['raw_wrong_5to8']:.1%} 降至 {p['joint_wrong_5to8']:.1%}，联合估计平台期误判率 "
        f"{p['joint_wrong_plateau']:.1%}。闭环 5 s 后 RMSE：原方法 "
        f"{raw['post5_rmse_m']:.6f} m，联合识别 {j['post5_rmse_m']:.6f} m，联合识别加补偿 "
        f"{ff['post5_rmse_m']:.6f} m，已知延迟加估计外扰补偿 {fff['post5_rmse_m']:.6f} m。"
        f"但去掉外扰后的恢复时间，联合识别加补偿为 {ff['recovery_s']:.2f} s，"
        f"联合识别不补偿为 {j['recovery_s']:.2f} s，窗口仍保留过时外扰估计。"
        f"缓变半正弦在固定控制轨迹上的平台期联合识别误判率为 {slow['joint_wrong_plateau']:.1%}。"
        "简单常值偏差估计已解决原常值扰动问题的一大部分，但未解决变化扰动的混淆。"
        "应把它作为基线，再判断 AI 或置信度机制的额外价值。\n\n")
    en=en.replace('## Limits and Verification\n\n','## Main Findings\n\n'+en_findings+'## Limits and Verification\n\n')
    zh=zh.replace('## 限制与验证\n\n','## 主要发现\n\n'+zh_findings+'## 限制与验证\n\n')
    (root/'report').mkdir(exist_ok=True)
    (root/'report'/'JOINT_ESTIMATION_REPORT_EN.md').write_text(en,encoding='utf-8')
    (root/'report'/'JOINT_ESTIMATION_REPORT.md').write_text(zh,encoding='utf-8')


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    root=Path(__file__).resolve().parent
    out=root/'results'/'joint_estimation'
    out.mkdir(parents=True,exist_ok=True)
    records=[]
    saved={}
    for scenario in SCENARIOS:
        for mode in MODES:
            with contextlib.redirect_stdout(io.StringIO()): data,states,m=run(scenario,mode)
            records.append(m)
            saved[scenario,mode]=(data,states)
            with (out/f'{scenario}_{mode}.csv').open('w',newline='') as f:
                w=csv.writer(f)
                w.writerow(['time_s','position_m','velocity_m_s','command','applied','true_disturbance',
                    'control_delay_s','control_bias','raw_delay_s','joint_delay_s','joint_bias',
                    *[f'raw_score_{d}' for d in CANDIDATES],*[f'joint_score_{d}' for d in CANDIDATES],
                    *[f'bias_{d}' for d in CANDIDATES],'next_position','next_velocity','solve_s','primal','dual'])
                w.writerows(data)
    with (out/'metrics.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0])); w.writeheader(); w.writerows(records)
    fig,axes=plt.subplots(1,2,figsize=(12,4),layout='constrained')
    fixed=[m for m in records if m['mode']=='fixed']
    x=np.arange(len(SCENARIOS))
    for ax,keys,title in [(axes[0],['raw_wrong_5to8','joint_wrong_5to8'],'Passive identification: 5–8 s'),
                          (axes[1],['joint_wrong_5to8','joint_wrong_plateau'],'Joint estimator: onset window vs plateau')]:
        for i,key in enumerate(keys): ax.bar(x+(i-.5)*.35,[m[key] for m in fixed],width=.35,label=key)
        ax.set_xticks(x,SCENARIOS,rotation=25)
        ax.set(title=title,ylabel='Wrong-delay fraction',ylim=(0,1.05)); ax.legend(fontsize=7)
    fig.savefig(out/'passive_comparison.png',dpi=150); plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,4),layout='constrained')
    for mode in MODES:
        ax.plot(x,[m['post5_rmse_m'] for m in records if m['mode']==mode],'o-',label=mode)
    ax.set_xticks(x,SCENARIOS,rotation=20); ax.set(ylabel='Post-5 s position RMSE [m]',title='Closed-loop comparison: all scenarios')
    ax.legend(); ax.grid(alpha=.25); fig.savefig(out/'control_comparison.png',dpi=150); plt.close(fig)
    fig,axes=plt.subplots(3,1,figsize=(11,8),sharex=True,layout='constrained')
    for mode in MODES:
        data,states=saved['plus050',mode]
        axes[0].plot(np.arange(STEPS+1)*DT,states[:,0],label=mode)
        axes[1].plot(data[:,0],data[:,6],label=mode)
        axes[2].plot(data[:,0],data[:,7],label=mode)
    axes[0].axhline(1.,c='black',ls='--'); axes[1].axhline(.3,c='black',ls='--')
    axes[2].plot(data[:,0],data[:,5],'k--',label='true disturbance')
    for ax,label in zip(axes,['Position [m]','Control delay [s]','Bias used by controller [m/s²]']):
        ax.set_ylabel(label); ax.axvspan(5,8,color='gray',alpha=.15); ax.grid(alpha=.25)
    axes[0].legend(ncol=5,fontsize=8); axes[2].legend(fontsize=8); axes[-1].set_xlabel('Time [s]')
    fig.suptitle('Positive 0.50 m/s² pulse: estimation and compensation are separate changes',fontsize=11)
    fig.savefig(out/'plus050_detail.png',dpi=150); plt.close(fig)
    record=dict(config=dict(dt=DT,steps=STEPS,horizon=HORIZON,candidates=CANDIDATES,window=WINDOW,
        true_delay=TRUE_DELAY,scenarios=SCENARIOS,modes=MODES,limit=LIMIT,noise=None,randomness=None,
        Q=[20,1],R=.2,terminal='Q',state_constraints=None,initial_delay=0,warmup=WINDOW,
        bias='unconstrained window mean',tie_tolerance=1e-12,disturbance_interval=[5,8]),
        environment=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,osqp=osqp.__version__,matplotlib=matplotlib.__version__,platform=platform.platform()),
        source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['experiment.py','delay_mismatch.py','joint_estimation.py']},metrics=records)
    (out/'summary.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    reports(root,records)
    for m in records: print(m['scenario'],m['mode'],round(m['post5_rmse_m'],6),round(m['raw_wrong_5to8'],3),round(m['joint_wrong_5to8'],3))


if __name__=='__main__': main()
