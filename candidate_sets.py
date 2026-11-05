"""Experiment 6: development-frozen candidate sets, paired held-out replays.

No neural network or formal coverage guarantee. Noise SD is assumed known.
GLS uses the exact covariance of differenced iid velocity noise.
"""
from pathlib import Path
import argparse, csv, hashlib, json, platform, sys
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

DT=.05
STEPS=400
WINDOW=20
EVAL_START=100
METHODS=('all','point_ols','point_gls','set_ols','set_gls','geometry_abstain')
SIGNALS=('constant','ramp','sine','multisine')
TARGET=.95


def fingerprint():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def dataset_config(split):
    if split=='development':
        return dict(split=split,delays=[2,6],sigmas=[.005,.02],seeds=[0,1,2],
                    disturbances=['zero','constant','sine'],sine_frequency=.6,
                    multisine_frequencies=[.35,.9,1.4],disturbance_frequency=.08,
                    constant_disturbance=.4,ramp_disturbance_slope=None)
    return dict(split=split,delays=[1,4,7],sigmas=[.008,.025],seeds=[100,101,102,103,104],
                disturbances=['zero','constant','sine','ramp'],sine_frequency=.83,
                multisine_frequencies=[.27,1.23,1.91],disturbance_frequency=.13,
                constant_disturbance=-.55,ramp_disturbance_slope=.035)


def signal_data(signal,dist,cfg):
    t=np.arange(STEPS)*DT
    test=cfg['split']=='test'
    if signal=='constant': u=np.full(STEPS,-.4 if test else .5)
    elif signal=='ramp': u=.4-.045*t if test else -.6+.06*t
    elif signal=='sine': u=.8*np.sin(2*np.pi*cfg['sine_frequency']*t)
    else:
        u=sum(a*np.sin(2*np.pi*f*t) for a,f in zip([.4,.3,.2],cfg['multisine_frequencies']))
    if dist=='zero': w=np.zeros(STEPS)
    elif dist=='constant': w=np.full(STEPS,cfg['constant_disturbance'])
    elif dist=='sine': w=.5*np.sin(2*np.pi*cfg['disturbance_frequency']*t)
    else: w=-.35+cfg['ramp_disturbance_slope']*t
    return u,w


def scoring(velocities,commands,sigma):
    """Public information only; no true delay or true disturbance argument."""
    y=np.diff(velocities)/DT
    shifted=np.array([np.r_[np.zeros(d),commands[:STEPS-d]] if d else commands
                      for d in range(9)])
    pred=sliding_window_view(shifted,WINDOW,axis=1).transpose(1,2,0)
    residual=sliding_window_view(y,WINDOW)[:,:,None]-pred
    # Cov(delta-v/dt)=(sigma/dt)^2 * tridiagonal(2,-1,-1).
    cov=2*np.eye(WINDOW)-np.eye(WINDOW,k=1)-np.eye(WINDOW,k=-1)
    precision=np.linalg.inv(cov)/(sigma/DT)**2
    one=np.ones(WINDOW)
    wo=precision@one
    qgls=precision-np.outer(wo,wo)/(one@wo)
    qols=(np.eye(WINDOW)-np.ones((WINDOW,WINDOW))/WINDOW)/(2*(sigma/DT)**2)
    ols=np.maximum(np.einsum('nwi,wv,nvi->ni',residual,qols,residual,optimize=True),0.)
    gls=np.maximum(np.einsum('nwi,wv,nvi->ni',residual,qgls,residual,optimize=True),0.)
    # Pairwise input separation after profiling a constant bias, no truth needed.
    gram=np.einsum('nwi,wv,nvj->nij',pred,qgls,pred,optimize=True)
    diag=np.diagonal(gram,axis1=1,axis2=2)
    distances=np.maximum(diag[:,:,None]+diag[:,None,:]-2*gram,0.)
    distances[:,np.arange(9),np.arange(9)]=np.inf
    separation=np.min(distances,axis=(1,2))
    keep=np.arange(WINDOW-1,STEPS)>=EVAL_START
    return ols[keep],gls[keep],separation[keep]


def observations(u,w,delay,sigma,seed):
    applied=np.r_[np.zeros(delay),u[:STEPS-delay]] if delay else u.copy()
    velocity=np.r_[0.,np.cumsum((applied+w)*DT)]
    measured=velocity+np.random.default_rng(seed).normal(0.,sigma,STEPS+1)
    return measured


def iterate(cfg):
    for signal in SIGNALS:
        for dist in cfg['disturbances']:
            u,w=signal_data(signal,dist,cfg)
            for d in cfg['delays']:
                for sigma in cfg['sigmas']:
                    for seed in cfg['seeds']:
                        meta=dict(signal=signal,disturbance=dist,true_delay=d,sigma=sigma,seed=seed)
                        measured=observations(u,w,d,sigma,seed)
                        ols,gls,sep=scoring(measured,u,sigma)
                        yield meta,u,w,measured,ols,gls,sep


def calibrate(ols,gls,separation,truth):
    thresholds={}
    for name,scores in [('ols',ols),('gls',gls)]:
        delta=scores[np.arange(len(truth)),truth]-scores.min(axis=1)
        thresholds[name]=float(np.quantile(delta,TARGET,method='higher'))
    wrong=np.argmin(gls,axis=1)!=truth
    # Choose the smallest empirical separation threshold allowing <=5% errors
    # overall: output all candidates on low separation, otherwise the GLS point.
    nwrong=int(wrong.sum())
    thresholds['geometry']=float(np.quantile(separation[wrong],
        max(0.,1-(1-TARGET)*len(truth)/nwrong),method='higher')) if nwrong>(1-TARGET)*len(truth) else 0.
    return thresholds


def sets_for(ols,gls,sep,thresholds):
    n=len(ols)
    p=np.eye(9,dtype=bool)[np.argmin(ols,axis=1)]
    g=np.eye(9,dtype=bool)[np.argmin(gls,axis=1)]
    return dict(all=np.ones((n,9),dtype=bool),point_ols=p,point_gls=g,
        set_ols=(ols-ols.min(axis=1,keepdims=True)<=thresholds['ols']+1e-10),
        set_gls=(gls-gls.min(axis=1,keepdims=True)<=thresholds['gls']+1e-10),
        geometry_abstain=np.where((sep>thresholds['geometry'])[:,None],g,True))


def metrics(sets,truth):
    size=sets.sum(axis=1)
    covered=sets[:,truth]
    singleton=size==1
    return dict(coverage=float(covered.mean()),mean_size=float(size.mean()),
        singleton_fraction=float(singleton.mean()),
        singleton_accuracy=float(covered[singleton].mean()) if singleton.any() else None,
        singleton_count=int(singleton.sum()),singleton_correct=int(np.sum(covered&singleton)),
        windows=len(size))


def summarize(records):
    summary=[]
    for method in METHODS:
        group=[r for r in records if r['method']==method]
        n=sum(r['singleton_count'] for r in group)
        row=dict(method=method,coverage=float(np.mean([r['coverage'] for r in group])),
            mean_size=float(np.mean([r['mean_size'] for r in group])),
            singleton_fraction=float(np.mean([r['singleton_fraction'] for r in group])),
            singleton_accuracy=sum(r['singleton_correct'] for r in group)/n if n else None,
            worst_replay_coverage=min(r['coverage'] for r in group),replays=len(group))
        strata={}
        for r in group: strata.setdefault((r['signal'],r['disturbance'],r['sigma']),[]).append(r['coverage'])
        row['worst_signal_disturbance_noise_coverage']=min(np.mean(v) for v in strata.values())
        summary.append(row)
    return summary


def write_csv(path,records):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0])); w.writeheader(); w.writerows(records)


def run_phase(phase):
    root=Path(__file__).resolve().parent
    out=root/'results'/'candidate_sets'; out.mkdir(parents=True,exist_ok=True)
    frozen=out/'frozen_rules.json'
    if phase=='development':
        if frozen.exists(): raise RuntimeError('Frozen rules already exist; use a new experiment directory for recalibration.')
        # Both split specifications are written before opening test observations.
        manifest=dict(development=dataset_config('development'),test=dataset_config('test'),
                      dt=DT,steps=STEPS,window=WINDOW,eval_start=EVAL_START,target=TARGET,
                      source_sha256=fingerprint())
        (out/'split_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        batches=list(iterate(manifest['development']))
        o=np.concatenate([b[4] for b in batches]); g=np.concatenate([b[5] for b in batches]); s=np.concatenate([b[6] for b in batches])
        truth=np.concatenate([np.full(len(b[4]),b[0]['true_delay'],dtype=int) for b in batches])
        thresholds=calibrate(o,g,s,truth)
        rule=dict(thresholds=thresholds,target=TARGET,source_sha256=fingerprint(),
                  manifest_sha256=hashlib.sha256((out/'split_manifest.json').read_bytes()).hexdigest(),
                  note='Empirical development-window coverage, not guaranteed conditional or trajectory coverage.')
        frozen.write_text(json.dumps(rule,indent=2),encoding='utf-8')
    else:
        rule=json.loads(frozen.read_text(encoding='utf-8'))
        if rule['source_sha256']!=fingerprint(): raise RuntimeError('Source changed after freeze.')
        if rule['manifest_sha256']!=hashlib.sha256((out/'split_manifest.json').read_bytes()).hexdigest(): raise RuntimeError('Manifest changed after freeze.')
        manifest=json.loads((out/'split_manifest.json').read_text(encoding='utf-8'))
        thresholds=rule['thresholds']
        batches=iterate(manifest['test'])
    records=[]
    folder=out/phase; folder.mkdir(exist_ok=True)
    for index,(meta,u,w,v,o,g,s) in enumerate(batches):
        sets=sets_for(o,g,s,thresholds)
        for method,selected in sets.items(): records.append(dict(**meta,method=method,**metrics(selected,meta['true_delay'])))
        # Full measurement trace and all candidate scores; bit masks recover sets.
        np.savez_compressed(folder/f'replay_{index:04d}.npz',commands=u,true_disturbance=w,
            measured_velocity=v,ols_scores=o,gls_scores=g,pairwise_separation=s,
            **{f'{name}_mask':np.sum(selected*(1<<np.arange(9)),axis=1).astype(np.uint16) for name,selected in sets.items()})
    write_csv(out/f'{phase}_metrics.csv',records)
    summary=summarize(records)
    write_csv(out/f'{phase}_summary.csv',summary)
    (out/f'{phase}_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
    if phase=='test': render(root,out)


def render(root,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    development=json.loads((out/'development_summary.json').read_text())
    test=json.loads((out/'test_summary.json').read_text())
    fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
    for label,rows in [('development',development),('held-out test',test)]:
        axes[0].scatter([r['mean_size'] for r in rows],[r['coverage'] for r in rows],label=label)
        for r in rows: axes[0].annotate(r['method'],(r['mean_size'],r['coverage']),fontsize=7,xytext=(3,3),textcoords='offset points')
    axes[0].axhline(TARGET,c='gray',ls='--'); axes[0].set(xlabel='Mean candidate count (1..9)',ylabel='Window coverage',ylim=(0,1.05),title='Frozen empirical rules under distribution shift'); axes[0].legend()
    x=np.arange(len(test)); axes[1].bar(x,[r['coverage'] for r in test],label='overall')
    axes[1].scatter(x,[r['worst_signal_disturbance_noise_coverage'] for r in test],c='red',marker='x',label='worst signal/disturbance/noise group')
    axes[1].set_xticks(x,[r['method'] for r in test],rotation=35,ha='right'); axes[1].set(ylim=(0,1.05),ylabel='Coverage',title='Held-out coverage and group failures'); axes[1].legend(fontsize=8)
    fig.savefig(out/'coverage_size.png',dpi=160); plt.close(fig)
    table='| Method | Dev coverage | Test coverage | Mean size (test) | Singleton fraction | Singleton accuracy | Worst group coverage |\n|---|---:|---:|---:|---:|---:|---:|\n'
    for dev,t in zip(development,test):
        acc='N/A' if t['singleton_accuracy'] is None else f"{t['singleton_accuracy']:.1%}"
        table+=f"| {t['method']} | {dev['coverage']:.1%} | {t['coverage']:.1%} | {t['mean_size']:.3f} | {t['singleton_fraction']:.1%} | {acc} | {t['worst_signal_disturbance_noise_coverage']:.1%} |\n"
    rules=json.loads((out/'frozen_rules.json').read_text())
    zh='''# 实验六：冻结规则下的延迟候选集合与独立测试

日期：2026-11-04。非学习、离线被动识别实验，尚未接入 MPC。

## 方法与信息条件

候选延迟 0..8 步，20 次转移窗口，周期 0.05 s。直接窗口选最优，不保留历史估计，因此可避免启动记忆造成的虚假持续识别。每个候选均拟合自由常值外扰。OLS 使用去均值残差平方和除以差分噪声方差；GLS 使用速度差分噪声的三对角协方差，并在加权意义下消除常值项。假设速度噪声标准差由独立标定准确知道，估计器不读取真实延迟或真实外扰。该已知噪声条件需在后续做失配测试。

方法：all 始终保留九个；point_ols/point_gls 仅选窗口最优，平局选较小索引；set_ols/set_gls 保留与最优评分差不超过开发集阈值的候选。geometry_abstain 用所有候选移位指令两两之间的加权去常值距离最小值：高于开发阈值时输出 GLS 单点，否则保留全部候选。这个距离仅依赖指令和已知噪声，不使用真实候选。所有集合允许 1e-10 数值容差。

## 数据隔离与规则冻结

开发集 144 次回放：四类输入，零/正常值/缓变正弦扰动，延迟 2/6，噪声标准差 0.005/0.020 m/s，种子 0..2。独立测试 480 次：更换输入参数与正弦/多频频率，零/负常值/更快正弦/新增线性外扰，延迟 1/4/7，噪声 0.008/0.025，种子 100..104。每次 400 次转移，从完成转移 k=100 开始评价 300 个窗口。不同方法使用完全相同测量。不同输入未匹配能量。详尽参数在 split_manifest.json；先保存两套参数，再仅访问开发数据、冻结规则，随后单独执行测试。

评分差阈值为开发窗口中“真实候选评分减去最优评分”的 95% 分位（higher）。几何阈值按开发集中误选样本的分离度选择，使总体窗口覆盖接近至少 95%，信息不足输出全部候选。开发真值仅用于标定。frozen_rules.json 保存阈值、程序和清单哈希；测试前验证一致。95% 是经验标定目标，不是概率或保证，不能推广为条件、轨迹或变化分布覆盖保证。没有根据测试结果重新选择阈值。

## 结果

TABLE

单点准确率只统计集合大小为一的时刻；覆盖率是包含真实候选的窗口比例。最差组按输入/扰动/噪声分组再对其延迟与种子平均，另保存最差回放覆盖。不把重叠窗口当独立样本构造置信区间。all 的满覆盖需保留全部九个，不代表成功识别。

## 限制与验收

这一步只检验候选规则是否有用，不证明安全或论文创新。已知噪声、准确模型、真实延迟每条轨迹固定，变化外扰违反常值拟合假设。必须同时看覆盖、集合大小和单点错误；总体 95% 也可能掩盖组内失败。若独立测试明显低于目标，下一步先诊断失配和噪声模型，不直接把集合接入控制。

## 复现与文件

运行 `python candidate_sets.py --phase development` 再 `python candidate_sets.py --phase test`；使用 .venv 中的 Python。已存在冻结规则时禁止覆盖标定，需新实验目录。只重画图和报告可用 `--phase render`。数据在 results/candidate_sets；每次回放保存压缩 NPZ、评分、观测、指令和集合位掩码，元信息在 *_metrics.csv，汇总在 *_summary.csv/json。报告默认保存 report。测试见 candidate_sets_tests.log，依赖仍为 requirements-lock.txt。
'''.replace('TABLE',table)
    en='''# Experiment 6: Frozen Delay Candidate Sets on Held-out Data

Date: 2026-11-04. Offline non-learning identification; no MPC integration.

## Methods and Information

Nine candidates (0..8 steps), 20-transition window, dt=0.05 s. Each candidate profiles a free constant disturbance. No historical estimate is retained: each window selects its own optimum, with smallest-index tie breaking. OLS is centered residual sum of squares divided by differenced-noise variance. GLS profiles a constant using the exact tridiagonal covariance of differenced iid velocity noise. Velocity-noise SD is assumed accurately known from separate calibration; no true delay or disturbance enters scoring. Noise-scale misspecification remains untested.

all retains nine; point_ols/point_gls retain the window minimizer; set_ols/set_gls retain candidates within a calibrated score increment. geometry_abstain computes the minimum pairwise weighted, constant-profiled distance between shifted command candidates. Above its frozen threshold it returns the GLS point, otherwise all nine. Geometry uses commands and known noise only, never the true candidate. Set comparisons allow 1e-10 numerical tolerance.

## Split and Freeze

144 development replays use four inputs, zero/positive-constant/slow-sine disturbance, delays 2/6, velocity-noise SD 0.005/0.020 m/s and seeds 0..2. 480 held-out replays change input parameters/frequencies, use zero/negative-constant/faster-sine/new ramp disturbances, delays 1/4/7, SD 0.008/0.025 and seeds 100..104. Every replay has 400 transitions, evaluating 300 windows after transition k=100. Data are paired across methods; inputs are not energy matched. Both parameter splits are saved before calibration. Exact parameters are in split_manifest.json; development rules are frozen before the separate test invocation.

Score increments use the higher empirical 95th percentile of true-candidate minus minimum development score. The geometry threshold is chosen from erroneous development-point selections to target at least approximately 95% overall window coverage by abstaining to all candidates. Labels are used only during calibration/evaluation. frozen_rules.json binds thresholds to source and manifest hashes, checked before test. The 95% target is empirical, not a conditional, trajectory-level, or distribution-shift coverage guarantee. No threshold is reselected after test inspection.

## Results

TABLE

Singleton accuracy conditions on set size one. Coverage is the fraction of windows containing the true delay. Worst group averages within input/disturbance/noise strata over delays/seeds; worst-replay coverage is separately saved. Overlapping windows are not independent uncertainty samples. all obtains coverage by retaining all nine, not by identification.

## Limits and Reproduction

Known noise scale, exact plant model and fixed delay within each replay simplify this test. Varying disturbances violate the fitted constant model. Evaluate coverage and size jointly; good overall coverage can conceal group failures. If held-out coverage misses the target, diagnose model/noise mismatch before connecting sets to MPC. No safety or novelty claim follows.

Run the project .venv Python with `candidate_sets.py --phase development`, then `--phase test`. Existing frozen rules cannot be overwritten; use a new experiment directory for recalibration. `--phase render` regenerates reports/plots without rerunning data. results/candidate_sets contains per-replay compressed NPZ measurements, commands, scores and set bitmasks, *_metrics.csv metadata, and *_summary.csv/json. Reports default to report/. See candidate_sets_tests.log and requirements-lock.txt.
'''.replace('TABLE',table)
    report=root/'report'; report.mkdir(exist_ok=True)
    (report/'CANDIDATE_SETS_REPORT.md').write_text(zh,encoding='utf-8')
    (report/'CANDIDATE_SETS_REPORT_EN.md').write_text(en,encoding='utf-8')
    (out/'environment.json').write_text(json.dumps(dict(python=sys.version,numpy=np.__version__,matplotlib=matplotlib.__version__,platform=platform.platform(),frozen_rules_sha256=hashlib.sha256((out/'frozen_rules.json').read_bytes()).hexdigest()),indent=2),encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--phase',choices=['development','test','render'],required=True)
    phase=parser.parse_args().phase
    if phase=='render':
        root=Path(__file__).resolve().parent; render(root,root/'results'/'candidate_sets')
    else: run_phase(phase)
