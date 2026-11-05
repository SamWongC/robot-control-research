"""Experiment 5: paired passive delay estimation and input distinguishability."""
from pathlib import Path
import csv, hashlib, json, platform, sys
import numpy as np
from experiment import A,B,DT,STEPS
from joint_estimation import Estimator,WINDOW,CANDIDATES

INPUTS=('constant','ramp','sine','multisine')
DISTURBANCES=('zero','constant','slow_sine')
NOISES=(0.,.005,.02)  # velocity measurement standard deviation [m/s]
TRUE_DELAY=6
EVAL_START=100  # evaluate completed transitions k>=100 (t>=5 s)


def commands_for(name):
    t=np.arange(STEPS)*DT
    if name=='constant': return np.full(STEPS,.5)
    if name=='ramp': return -.6+.06*t
    if name=='sine': return .8*np.sin(2*np.pi*.7*t)
    return .4*np.sin(2*np.pi*.35*t)+.3*np.sin(2*np.pi*1.1*t)+.2*np.sin(2*np.pi*1.7*t)


def disturbance_for(name):
    t=np.arange(STEPS)*DT
    if name=='zero': return np.zeros(STEPS)
    if name=='constant': return np.full(STEPS,.5)
    return .5*np.sin(2*np.pi*.1*t)


def centered_separation(commands,k,reference=TRUE_DELAY):
    """Oracle diagnostic, NOT estimator input: separation from true-delay input.

    Zero means at least one other candidate differs only by a constant in this
    window. Under a constant unknown disturbance those candidates are equivalent.
    """
    indices=np.arange(max(0,k-WINDOW+1),k+1)
    shifted=np.array([[commands[j-d] if j>=d else 0. for j in indices] for d in CANDIDATES])
    dif=shifted-shifted[reference]
    centered=dif-dif.mean(axis=1,keepdims=True)
    energy=np.mean(centered**2,axis=1)
    return float(np.min(np.delete(energy,reference)))


def replay(commands,disturbance,sigma,seed):
    states=[np.zeros(2)]
    for k in range(STEPS):
        u=commands[k-TRUE_DELAY] if k>=TRUE_DELAY else 0.
        states.append(A@states[-1]+B[:,0]*(u+disturbance[k]))
    states=np.array(states)
    noise=np.random.default_rng(seed).normal(0.,sigma,STEPS+1)
    measured=states.copy(); measured[:,1]+=noise
    estimators=[Estimator(False),Estimator(True)]
    rows=[]
    for k in range(STEPS):
        for e in estimators: e.observe(measured[k],measured[k+1],commands[k])
        raw,joint=estimators
        gap=np.sort(joint.scores)[1]-np.min(joint.scores)
        rows.append([(k+1)*DT,commands[k],disturbance[k],states[k,0],states[k,1],
            measured[k,1],measured[k+1,1],raw.estimate,joint.estimate,
            raw.biases[raw.estimate],joint.biases[joint.estimate],gap,
            centered_separation(commands,k),*raw.scores,*joint.scores])
    return np.array(rows)


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    root=Path(__file__).resolve().parent
    out=root/'results'/'identifiability'
    out.mkdir(parents=True,exist_ok=True)
    records=[]; deterministic={}
    for signal in INPUTS:
        for dist in DISTURBANCES:
            for sigma in NOISES:
                for seed in ([0] if sigma==0 else range(10)):
                    data=replay(commands_for(signal),disturbance_for(dist),sigma,seed)
                    ev=data[EVAL_START:]
                    record=dict(signal=signal,disturbance=dist,sigma_velocity=sigma,seed=seed,
                        raw_accuracy=float(np.mean(ev[:,7]==TRUE_DELAY)),
                        joint_accuracy=float(np.mean(ev[:,8]==TRUE_DELAY)),
                        raw_delay_mae_s=float(DT*np.mean(np.abs(ev[:,7]-TRUE_DELAY))),
                        joint_delay_mae_s=float(DT*np.mean(np.abs(ev[:,8]-TRUE_DELAY))),
                        joint_disturbance_rmse=float(np.sqrt(np.mean((ev[:,10]-ev[:,2])**2))),
                        raw_disturbance_rmse=float(np.sqrt(np.mean((ev[:,9]-ev[:,2])**2))),
                        joint_gap_mean=float(np.mean(ev[:,11])),
                        mean_oracle_separation=float(np.mean(ev[:,12])),
                        zero_separation_fraction=float(np.mean(ev[:,12]<1e-12)),
                        high_gap_accuracy=float(np.mean(ev[ev[:,11]>=np.quantile(ev[:,11],.75),8]==TRUE_DELAY)))
                    records.append(record)
                    if sigma==0: deterministic[signal,dist]=data
                    name=f'{signal}_{dist}_sigma{sigma:g}_seed{seed:02d}.csv'
                    with (out/name).open('w',newline='') as f:
                        w=csv.writer(f)
                        w.writerow(['observation_available_time_s','sent_command','true_disturbance',
                            'true_position_before','true_velocity_before','measured_velocity_before',
                            'measured_velocity_after','raw_delay_steps','joint_delay_steps',
                            'raw_selected_bias','joint_selected_bias','joint_score_gap',
                            'oracle_centered_input_separation',*[f'raw_score_{d}' for d in CANDIDATES],
                            *[f'joint_score_{d}' for d in CANDIDATES]])
                        w.writerows(data)
    with (out/'metrics.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0])); w.writeheader(); w.writerows(records)
    aggregated=[]
    for signal in INPUTS:
        for dist in DISTURBANCES:
            for sigma in NOISES:
                group=[m for m in records if (m['signal'],m['disturbance'],m['sigma_velocity'])==(signal,dist,sigma)]
                m=dict(signal=signal,disturbance=dist,sigma_velocity=sigma,runs=len(group))
                for key in ['raw_accuracy','joint_accuracy','joint_delay_mae_s','joint_disturbance_rmse','high_gap_accuracy']:
                    values=[r[key] for r in group]
                    m[key+'_mean']=float(np.mean(values)); m[key+'_seed_sd']=float(np.std(values,ddof=1)) if len(values)>1 else None
                aggregated.append(m)
    with (out/'aggregated.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(aggregated[0])); w.writeheader(); w.writerows(aggregated)
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for ax,key in zip(axes,['raw_accuracy','joint_accuracy']):
        array=np.array([[next(m[key] for m in records if m['signal']==s and m['disturbance']==d and m['sigma_velocity']==0) for d in DISTURBANCES] for s in INPUTS])
        im=ax.imshow(array,vmin=0,vmax=1,cmap='viridis')
        ax.set_xticks(range(3),DISTURBANCES); ax.set_yticks(range(4),INPUTS); ax.set_title(key+' (no noise)')
        for i in range(4):
            for j in range(3): ax.text(j,i,f'{array[i,j]:.0%}',ha='center',va='center',color='white' if array[i,j]<.6 else 'black')
    fig.colorbar(im,ax=axes,label='Fraction correct; retained estimates can mask ambiguity')
    fig.savefig(out/'noiseless_accuracy.png',dpi=150); plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(13,4),layout='constrained')
    for ax,dist in zip(axes,DISTURBANCES):
        for signal in INPUTS:
            g=[m for m in aggregated if m['signal']==signal and m['disturbance']==dist]
            ax.plot(NOISES,[m['joint_accuracy_mean'] for m in g],'o-',label=signal)
        ax.set_xticks(NOISES,['0','0.005','0.020'])
        ax.set(title=dist,xlabel='Velocity noise SD [m/s]',ylim=(-.03,1.03)); ax.grid(alpha=.25)
    axes[0].set_ylabel('Joint estimator accuracy (mean over seeds)'); axes[-1].legend(fontsize=8)
    fig.savefig(out/'noise_sensitivity.png',dpi=150); plt.close(fig)
    fig,axes=plt.subplots(3,1,figsize=(10,8),sharex=True,layout='constrained')
    for signal in INPUTS:
        data=deterministic[signal,'constant']
        axes[0].plot(data[:,0],data[:,1],label=signal)
        axes[1].plot(data[:,0],data[:,8]*DT)
        axes[2].plot(data[:,0],data[:,12])
    axes[0].legend(ncol=4,fontsize=8); axes[1].axhline(.3,c='black',ls='--')
    axes[2].set_yscale('symlog',linthresh=1e-12)
    for ax,label in zip(axes,['Command [m/s²]','Joint delay estimate [s]','Oracle input separation']):
        ax.set_ylabel(label); ax.axvline(5,c='gray',ls=':'); ax.grid(alpha=.25)
    axes[-1].set_xlabel('Observation availability time [s]')
    fig.suptitle('Constant external acceleration 0.5 m/s²; no noise; oracle separation is evaluation only',fontsize=10)
    fig.savefig(out/'excitation_detail.png',dpi=150); plt.close(fig)
    # Descriptive score-gap check without selecting a threshold for deployment.
    fig,ax=plt.subplots(figsize=(8,4),layout='constrained')
    for dist in DISTURBANCES:
        g=[m for m in records if m['disturbance']==dist]
        ax.scatter([m['joint_gap_mean'] for m in g],[m['joint_accuracy'] for m in g],label=dist,alpha=.5,s=18)
    ax.set_xscale('symlog',linthresh=1e-12)
    ax.set(xlabel='Mean best/second-best score gap',ylabel='Delay accuracy',title='Gap is not calibrated confidence (each point is a replay)')
    ax.legend(); fig.savefig(out/'gap_diagnostic.png',dpi=150); plt.close(fig)
    summary=dict(config=dict(dt=DT,steps=STEPS,window=WINDOW,true_delay=TRUE_DELAY,
        candidates=CANDIDATES,inputs=INPUTS,disturbances=DISTURBANCES,noise_velocity_sd=NOISES,
        seeds_noisy=list(range(10)),seed_noiseless=[0],eval_transition_indices=[EVAL_START,STEPS-1],
        noise_model='iid velocity measurement noise at all 401 states; differences share endpoints',
        measured_position='exact, unused for identification',pairing='identical data for both estimators, common noise by seed',
        gap_high_definition='within-run top quartile, descriptive only, ties included'),
        environment=dict(python=sys.version,numpy=np.__version__,matplotlib=matplotlib.__version__,platform=platform.platform()),
        source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['identifiability_experiment.py','joint_estimation.py','experiment.py']},
        replay_count=len(records),aggregated=aggregated)
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    make_reports(root,records,aggregated)
    for m in aggregated: print(m['signal'],m['disturbance'],m['sigma_velocity'],round(m['joint_accuracy_mean'],3))


def make_reports(root,records,agg):
    table='| Input | Disturbance | Raw accuracy | Joint accuracy | Zero-separation fraction |\n|---|---|---:|---:|---:|\n'
    table+='\n'.join(f"| {m['signal']} | {m['disturbance']} | {m['raw_accuracy']:.1%} | {m['joint_accuracy']:.1%} | {m['zero_separation_fraction']:.1%} |" for m in records if m['sigma_velocity']==0)
    noise='| Input | Disturbance | Velocity noise SD | Joint accuracy mean | Across-seed SD |\n|---|---|---:|---:|---:|\n'
    noise+='\n'.join(f"| {m['signal']} | {m['disturbance']} | {m['sigma_velocity']} | {m['joint_accuracy_mean']:.1%} | {m['joint_accuracy_seed_sd']:.4f} |" for m in agg if m['sigma_velocity']>0)
    en='''# Experiment 5: Identifiability, Excitation and Measurement Noise

Date: 2026-11-04. Passive open-loop mechanism study; no controller, learning or novelty claim.

## Protocol

Four commands, applied for 20 s at dt=0.05 s: constant 0.5; ramp -0.6+0.06*t; sine 0.8*sin(2*pi*0.7*t); multisine 0.4*sin(2*pi*0.35*t)+0.3*sin(2*pi*1.1*t)+0.2*sin(2*pi*1.7*t). They are NOT energy matched. True input delay is six steps, initial pending commands zero. Known double-integrator plant, initial state zero. Disturbance acts throughout: zero, constant +0.5, or 0.5*sin(2*pi*0.1*t) m/s². These are identification probes, not position-limited robot tasks.

Independent Gaussian velocity measurement noise has SD 0, 0.005 or 0.02 m/s. Both estimators receive exactly the same state measurements and sent commands in each replay. Position is exact and unused by identification. Acceleration is obtained by velocity differencing: its noise SD is sqrt(2)*sigma/0.05 and consecutive differences have correlated errors. One noiseless run and ten fixed seeds per noisy condition give 252 replays. Common noise samples are used across scenarios at a given seed and SD. Seed SD measures measurement-noise variation, not training or task variation.

Raw and constant-bias-profiled estimators are unchanged from Experiment 4 (20-transition window, zero initial estimate, warm-up, tie retention). Each output is logged AFTER observing transition k at time (k+1)*dt, available for a future action; no future measurement is used. Evaluation uses completed transitions k=100..399 (availability times 5.05..20 s), excluding startup. Scores, biases and all nine candidates are saved. Disturbance error compares the selected bias with the last completed transition's true disturbance.

## Structural Diagnostic

For each window, form the shifted command sequence for every candidate. Compare each with the TRUE candidate after removing their mean difference; take the smallest mean squared difference. This oracle separation is evaluation-only, never supplied to the estimator. Zero means another candidate is exactly equivalent under a free constant disturbance in that window. Constant input and a linear ramp both have zero separation after startup: shifting a ramp changes its intercept, which the disturbance estimate absorbs. Nonzero separation distinguishes candidates only in the noiseless constant-disturbance model; it is not a general identifiability theorem for unknown varying disturbances.

## Noiseless Results

TABLE

Correct retained estimates during zero separation reflect startup memory and the tie rule, not fresh identification. Failed estimates under uninformative input cannot simply be fixed by a larger network.

## Noise Sensitivity

NOISE

No confidence intervals are inferred by treating overlapping windows as independent. The best/second-best score gap is uncalibrated. gap_diagnostic.png and per-run top-quartile-gap accuracy are descriptive; thresholds were not trained or validated for deployment. A varying disturbance can select the wrong candidate with a nonzero score gap.

## Verification, Files and Next Step

Run `.\\.venv\\Scripts\\python.exe -m unittest -v`, then `.\\.venv\\Scripts\\python.exe identifiability_experiment.py`. Requirements remain requirements-lock.txt. Results in results/identifiability: 252 replay CSVs, metrics.csv, aggregated.csv, summary.json with formulas/configuration references and code hashes, four PNGs. Tests verify ramp/constant ambiguity, distinguishability of multisine input, exact noiseless prediction and paired deterministic noise. Tests also verify a mean-cancelling bias fit. Signals and test conditions were predeclared, not optimized after inspecting outcomes. No state safety or stability claim is made.

Next: formalize the constant-disturbance equivalence condition, investigate noise-aware residual scoring and varying-disturbance models, and evaluate calibrated candidate sets on genuinely held-out data before allowing confidence to influence control. Literature status is documented in LITERATURE_IDENTIFIABILITY_NOTES.md; earlier claims of novelty remain unverified.
'''.replace('TABLE',table).replace('NOISE',noise)
    zh='''# 实验五：可辨识性、输入激励与测量噪声

日期：2026-11-04。开环被动识别机制实验，不含控制器、学习或新颖性结论。

## 协议

四种指令持续 20 s，周期 0.05 s：恒定 0.5；斜坡 -0.6+0.06*t；正弦 0.8*sin(2*pi*0.7*t)；多频 0.4*sin(2*pi*0.35*t)+0.3*sin(2*pi*1.1*t)+0.2*sin(2*pi*1.7*t)。不同信号没有匹配能量，不能据此宣称多频普遍最优。真实延迟六步，初始等待动作为零，双积分模型已知，初始状态零。外扰全程作用：零、常值 +0.5、缓变 0.5*sin(2*pi*0.1*t) m/s²。这是辨识探针，不是有位置限制的机器人任务。

速度测量加入独立高斯噪声，标准差 0、0.005、0.02 m/s。每次回放两个估计器接收完全相同的状态与发送动作。位置精确，估计器不用位置。速度差分所得加速度噪声标准差为 sqrt(2)*sigma/0.05，相邻差分噪声因共享端点而相关。每个无噪声工况一次，有噪声工况十个固定种子，共 252 次回放。同一标准差/种子在不同工况使用相同噪声样本。跨种子标准差仅描述测量噪声变化，不代表训练或任务变化。

原估计器与去均值拟合常值外扰的联合估计器均沿用实验四：20 次转移窗口、初始零延迟、预热及平局保留。观测完成第 k 次转移后，在 (k+1)*dt 时记录估计，可用于未来动作；没有使用未来测量。评价 k=100..399，即数据可用时刻 5.05..20 s，排除启动过程。保存九个候选的评分与所选外扰估计。外扰误差以最后完成转移的真实扰动为参考。

## 结构诊断

每个窗口中，构造九个延迟对应的移位指令。各候选与真实候选作差，去掉差值均值，再求平方均值并取非真实候选最小值。这是只供评估的真实候选分离度，不提供给估计器。为零意味着至少一个错误候选可通过改变常值外扰完全解释同一窗口。启动后恒定与斜坡输入都为零：斜坡移位只改变截距，能被外扰吸收。分离度大于零仅针对无噪声、常值外扰模型区分候选，不能推广为任意变化外扰下的可辨识性定理。

## 无噪声结果

列为输入、扰动、原方法正确率、联合方法正确率、分离度为零的窗口比例。

TABLE

分离度为零时保留正确估计，来自启动记忆与平局规则，不代表持续获得了识别信息。信息不足导致的错误不能简单用更大网络消除。

## 噪声敏感性

列为输入、扰动、速度噪声标准差、联合识别正确率均值、跨种子标准差。

NOISE

没有把重叠窗口当独立样本计算置信区间。最优与次优评分差未经校准，gap_diagnostic.png 与每次回放中评分差最高四分之一的正确率仅供描述，未训练或验证部署阈值。变化扰动可能在评分差不为零时仍选择错误候选。

## 验证、文件与后续

运行 `.\\.venv\\Scripts\\python.exe -m unittest -v`，再运行 `.\\.venv\\Scripts\\python.exe identifiability_experiment.py`；依赖仍为 requirements-lock.txt。results/identifiability 保存 252 个回放 CSV、metrics.csv、aggregated.csv、配置及代码哈希 summary.json、四张 PNG。测试覆盖恒定/斜坡混淆、多频可分离、无噪声精确预测、成对可重复噪声以及残差去均值。信号与条件在运行前声明，没有根据结果优化工况。不声称状态安全或闭环稳定。

下一步应形式化常值外扰下的候选等价条件，研究考虑差分噪声的评分与变化外扰模型，在真正独立数据上验证候选集合的可靠性后再让置信度影响控制。文献核查见 LITERATURE_IDENTIFIABILITY_NOTES.md，目前尚未确认论文创新点。
'''.replace('TABLE',table).replace('NOISE',noise)
    lookup={(m['signal'],m['disturbance'],m['sigma_velocity']):m for m in agg}
    s=lookup['sine','zero',.02]['joint_accuracy_mean']
    multi=lookup['multisine','zero',.02]['joint_accuracy_mean']
    ns=lookup['sine','slow_sine',0.]['joint_accuracy_mean']
    nm=lookup['multisine','slow_sine',0.]['joint_accuracy_mean']
    findings_en=(f"Both constant and ramp inputs show 100% retained joint-estimator accuracy without noise, "
        "yet zero oracle separation in every evaluated window. Startup padding/turn-on provides initial "
        "information; the subsequent correct tie-retained value is not re-identification. "
        f"For zero disturbance and velocity-noise SD 0.02 m/s, mean accuracy is {s:.1%} for sine and "
        f"{multi:.1%} for multisine. Under slow varying disturbance without noise it is {ns:.1%} and "
        f"{nm:.1%}, respectively. Thus varying input alone neither guarantees rejection of varying "
        "disturbance nor noise robustness. No universal waveform ranking is supported.\n\n")
    findings_zh=("恒定和斜坡输入在无噪声时保留正确延迟的比例均为 100%，但全部评价窗口的真实候选"
        "分离度为零。启动前零指令与启动后的变化提供了初始信息，之后平局保留正确值不能当成"
        f"重新识别。无外扰、速度噪声标准差 0.02 m/s 时，正弦正确率 {s:.1%}，多频 {multi:.1%}；"
        f"无噪声缓变外扰下分别为 {ns:.1%} 和 {nm:.1%}。输入变化并不自动保证抗变化外扰或抗噪，"
        "不同输入能量未匹配，不能给出普遍波形排名。\n\n")
    en=en.replace('## Verification, Files and Next Step\n\n','## Main Findings\n\n'+findings_en+'## Verification, Files and Next Step\n\n')
    zh=zh.replace('## 验证、文件与后续\n\n','## 主要发现\n\n'+findings_zh+'## 验证、文件与后续\n\n')
    (root/'report').mkdir(exist_ok=True)
    (root/'report'/'IDENTIFIABILITY_REPORT_EN.md').write_text(en,encoding='utf-8')
    (root/'report'/'IDENTIFIABILITY_REPORT.md').write_text(zh,encoding='utf-8')


if __name__=='__main__': main()
