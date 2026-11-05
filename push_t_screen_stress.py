"""Independent frozen stress batches and development-only miss detectors."""
from pathlib import Path
import json,time,hashlib
import numpy as np
import mujoco
import push_t_fixed_batch as base

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'/'push_t_screen_stress'
def dump(name,x): (OUT/name).write_text(json.dumps(x,indent=2),encoding='utf8')
def freeze():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'fixture.npz').exists(): raise RuntimeError('Refuse overwrite frozen experiment')
    rng=np.random.default_rng(2026110402); qs=[]; us=[]; gs=[]; labels=[]
    for split in ['development','test']:
      for family in ['grazing','reversal','near_duplicate','fast_corner']:
       for rep in range(24):
        theta=rng.uniform(-np.pi,np.pi); c,s=np.cos(theta),np.sin(theta); R=np.array([[c,-s],[s,c]])
        origin=rng.uniform(-.03,.03,2)
        local=({'grazing':[-.078,.071],'reversal':[0,-.088],'near_duplicate':[-.078,.055],'fast_corner':[.077,.073]})[family]
        p=origin+R@(np.array(local)+rng.uniform(-.001,.001,2))
        q=np.r_[origin,theta,p]; target=origin+R@np.array([0,.025]); angle=np.arctan2(*(target-p)[::-1])
        u=np.zeros((64,20,2))
        for i in range(1,64):
          a=angle+rng.normal(0,1.2,5); speed=rng.uniform(.08,.24,5)
          if family=='reversal': a[2:]+=np.pi
          if family=='grazing': a+=rng.choice([-1,1])*.8
          if family=='fast_corner':speed[:]=rng.uniform(.20,.245,5)
          knots=np.c_[np.cos(a),np.sin(a)]*speed[:,None]
          for j in range(2):u[i,:,j]=np.interp(np.linspace(0,4,20),np.arange(5),knots[:,j])
        if family=='near_duplicate':
          # Eight clusters of close actions: rank crowding, selected without reference costs.
          seeds=u[1:9].copy()
          u=np.repeat(seeds,8,axis=0)+rng.normal(0,.006,(64,20,2));u=np.clip(u,-.245,.245)
        goal=np.r_[origin+R@rng.uniform([-.09,-.09],[.12,.12]),theta+rng.uniform(-1.2,1.2)]
        qs.append(q);us.append(u);gs.append(goal);labels.append(dict(split=split,family=family,repeat=rep))
    np.savez_compressed(OUT/'fixture.npz',qpos=qs,controls=us,goals=gs)
    dump('protocol.json',dict(seed=2026110402,labels=labels,base_source_sha256=base.sha(base.__file__),source_sha256=base.sha(__file__),fixture_sha256=base.sha(OUT/'fixture.npz'),
      detector='margin threshold calibrated on development misses only; medium winner outside coarse top8; no test tuning',
      meaningful_regret=1e-4,steps=[.01,.005,.0025,.00125],scope='Same simplified model; independent states/actions; no obstacles or hardware'))

def run():
    f=np.load(OUT/'fixture.npz'); protocol=json.loads((OUT/'protocol.json').read_text());assert base.sha(OUT/'fixture.npz')==protocol['fixture_sha256']
    ev=base.Evaluator();dt=.005;ev.models[dt]=base.model(dt)
    for n in [1,8]:ev.data[dt,n]=[mujoco.MjData(ev.models[dt]) for _ in range(n)]
    rows=[];allcost=[];timings=[]
    try:
      for b,label in enumerate(protocol['labels']):
        init=base.initial(f['qpos'][b],np.zeros(5));u=f['controls'][b];g=f['goals'][b]
        scores={}
        for step in [.01,.005,.0025,.00125]:scores[step]=ev.evaluate(init,u,g,step)[0]
        co,mid,fi,half=[scores[x] for x in [.01,.005,.0025,.00125]];ids=np.argsort(co)[:8];best=int(fi.argmin());chosen=int(ids[fi[ids].argmin()])
        margin=float(np.sort(co)[8]-np.sort(co)[0]);rank=int(np.flatnonzero(np.argsort(co)==best)[0])+1
        rows.append(dict(batch=b,**label,miss=best not in ids,regret=float(fi[chosen]-fi[best]),coarse_rank=rank,margin=margin,
          medium_alarm=bool(int(mid.argmin()) not in ids),halfstep_regret=float(half[chosen]-half.min()),halfstep_best=int(half.argmin()),fine_best=best))
        allcost.append([co,mid,fi,half])
        # Three paired repeats, randomized order; every method includes its own coarse stage.
        rng=np.random.default_rng(74000+b)
        for repeat in range(3):
          for method in rng.permutation(['fine','top8','medium_alarm']):
            start=time.perf_counter()
            if method=='fine':ev.evaluate(init,u,g)
            else:
              cc=ev.evaluate(init,u,g,.01)[0];ii=np.argsort(cc)[:8]
              if method=='medium_alarm':
                mm=ev.evaluate(init,u,g,.005)[0]
                if int(mm.argmin()) not in ii:ii=np.arange(64)
              ev.evaluate(init[ii],u[ii],g)
            timings.append(dict(batch=b,split=label['split'],method=str(method),repeat=repeat,seconds=time.perf_counter()-start))
        if b%24==23:print('finished',b+1,flush=True)
    finally:ev.close()
    np.savez_compressed(OUT/'costs.npz',costs=allcost)
    dump('rows.json',rows);dump('timings.json',timings)

def analyze():
    rows=json.loads((OUT/'rows.json').read_text());times=json.loads((OUT/'timings.json').read_text());dev=[r for r in rows if r['split']=='development'];test=[r for r in rows if r['split']=='test']
    misses=[r for r in dev if r['regret']>1e-4]
    threshold=max((r['margin'] for r in misses),default=-1)
    stats={}
    for name,pred in [('coarse_margin',lambda r:r['margin']<=threshold),('medium_disagreement',lambda r:r['medium_alarm'])]:
      tp=sum(pred(r) and r['regret']>1e-4 for r in test);fp=sum(pred(r) and r['regret']<=1e-4 for r in test);fn=sum(not pred(r) and r['regret']>1e-4 for r in test);tn=96-tp-fp-fn
      stats[name]=dict(tp=tp,fp=fp,fn=fn,tn=tn,alarms=tp+fp,recall=tp/(tp+fn) if tp+fn else None,remaining_max_regret=max((r['regret'] for r in test if not pred(r)),default=0))
    families={fam:dict(batches=24,exact_misses=sum(r['miss'] for r in test if r['family']==fam),meaningful_misses=sum(r['regret']>1e-4 for r in test if r['family']==fam),max_regret=max(r['regret'] for r in test if r['family']==fam),max_rank=max(r['coarse_rank'] for r in test if r['family']==fam)) for fam in sorted(set(r['family'] for r in test))}
    latency={m:float(np.percentile([t['seconds']*1000 for t in times if t['split']=='test' and t['method']==m],95)) for m in ['fine','top8','medium_alarm']}
    summary=dict(development_meaningful_misses=len(misses),margin_threshold=threshold,test_families=families,detectors=stats,p95_ms=latency,halfstep_best_changes=sum(r['halfstep_best']!=r['fine_best'] for r in test),misses_persist_halfstep=sum(r['regret']>1e-4 and r['halfstep_regret']>1e-4 for r in test))
    dump('summary.json',summary)
    # Audits verify saved calculations against the independent frozen cost arrays.
    arr=np.load(OUT/'costs.npz')['costs'];assert arr.shape==(192,4,64) and np.isfinite(arr).all()
    for r,a in zip(rows,arr):
      ii=np.argsort(a[0])[:8];assert np.isclose(r['regret'],a[2,ii].min()-a[2].min());assert r['medium_alarm']==(int(a[1].argmin()) not in ii)
    assert len(dev)==len(test)==96 and len(times)==192*9
    dump('audit.json',dict(passed=True,checks=['192 frozen batches and finite costs','saved regrets independently recomputed','medium alarm recomputed','96/96 split','1728 timed calls'],source_sha256=base.sha(__file__)))
    table='| Family | Test batches | Exact misses | Regret > 1e-4 | Max regret | Worst coarse rank |\n|---|---:|---:|---:|---:|---:|\n'
    for name,x in families.items():table+=f"| {name} | 24 | {x['exact_misses']} | {x['meaningful_misses']} | {x['max_regret']:.6f} | {x['max_rank']} |\n"
    details=json.dumps(summary,indent=2)
    common=f'\n{table}\n```json\n{details}\n```\n'
    zh='''# 独立困难批次：粗筛漏选与廉价报警

本轮为新的冻结实验，保留上一轮结果。192个批次，每批64条候选；96开发、96测试，四类各24个。沿用简化平面MuJoCo模型、1秒时域和代价，未加入障碍或实机。场景为擦边接触、动作反转、近重复候选挤占排名、高速角点推动；这些是机制假设，不能由相关性证明因果。近重复候选包含8个簇，每簇8条，容易让粗排序前8集中于一个簇。

精细参考步长0.0025秒，粗步长0.01秒；中等精度0.005秒用于报警，0.00125秒仅事后审计。漏选表示精细最优不在粗前8；另报告成本损失超过1e-4的次数，该阈值只是固定数值容差，不是机器人任务容忍度。没有在测试集上挑选参数或补抽失败样本。

报警一仅用粗成本第9名与第1名的间距：开发集有实际损失的批次中最大间距作为阈值，低于阈值就报警。它便宜但可能频繁误报；若开发集没有失败则不开启。
报警二重新计算全部候选的中等精度成本；若中等精度第一名不在粗前8就报警。报警后回退全部精细计算，否则仅精算前8。它无需标签调参，但必须计入中等精度计算开销。表中medium_alarm计时包含整个流程。报警一尚未实现回退计时，不可宣称端到端加速。
'''+common+'''
解读：tp为抓到的实际损失，fn为漏报，fp为无实际损失时报警，tn为正确不报警。只有同时具有低漏报、低误报且含回退的总耗时更低，才能称为有效的廉价识别。有限测试上的零漏报也不是可靠性证书。中等精度与粗精度可能一致地犯错，成本间距也不直接约束模型误差。

halfstep_best_changes反映参考离散敏感性；misses_persist_halfstep表示粗筛损失在更细参考下仍存在的批次数。任何结果都不是物理真值或闭环控制成功率。没有测试管束/抽象方法，也没有据此证明新颖性。

原始批次、四档全部成本、逐次计时、结果、协议及审计在results/push_t_screen_stress。运行代码push_t_screen_stress.py：freeze、run、analyze依次执行；freeze拒绝覆盖。环境沿用.venv-contact。输出单位与上一实验一致；每方法每批3次，p95来自96个测试批次的288次调用，仅为描述统计。
'''
    en='''# Independent stress batches: screening misses and inexpensive alarms

New frozen experiment: 192 batches of 64 candidates, 96 development and 96 held-out test, 24 per family per split. Same simplified planar MuJoCo model, objective and one-second horizon; no obstacles or hardware. Families are grazing, reversal, near-duplicate action clusters, and fast corner pushing. These are hypothesized mechanisms, not causal conclusions. Near-duplicate candidates comprise eight clusters of eight actions.

Fine/coarse/medium/audit steps: 0.0025/0.01/0.005/0.00125 seconds. Exact miss means the fine winner lies outside the coarse top eight. Regret > 1e-4 is a fixed numerical reporting tolerance, not a task-level tolerance. No test tuning or resampling of failures.

The coarse-margin alarm triggers when the ninth-to-first coarse cost gap is below the maximum such gap among development batches with regret > 1e-4 (disabled if none). Its fallback latency is not implemented. The medium-disagreement alarm reevaluates all candidates at medium resolution and triggers if its winner lies outside the coarse top eight. On alarm it evaluates all candidates finely; otherwise it refines only eight. Reported medium_alarm latency includes all stages and fallback. It uses no reference labels for decisions.
'''+common+'''
TP/FN refer to detected/missed regret > 1e-4; FP means alarm without such regret. Low missed alarms alone is insufficient: false alarms and total latency also matter. Zero observed misses does not certify general reliability. Coarse and medium models may agree while both are wrong; cost margins do not bound model error.

halfstep_best_changes reports reference sensitivity; misses_persist_halfstep counts fine-regret failures that remain under the finer audit reference. No physical-truth, closed-loop, tube/abstraction failure or novelty claim follows.

All frozen inputs, four-resolution costs, raw timings, protocol and numerical audit are in results/push_t_screen_stress. Run push_t_screen_stress.py freeze, run, analyze in .venv-contact; freeze refuses overwrite. Three repeats per method per batch, 288 test calls per method; descriptive p95, not confidence intervals. Historical results are preserved.
'''
    failures=[r for r in test if r['regret']>1e-4]
    dump('failure_cases.json',failures)
    zh+='''
## 本次实测判断

96个测试批次有5次漏选：反转3/24，近重复2/24；擦边与高速角点各0/24，不能宣称后两类普遍安全。最优候选的粗排名最差到第19。批次121（从0编号）中粗排名第19的候选49实际最好，损失0.301907，在减半步长后仍损失0.416679。批次145的精细最优粗排第17；其粗成本间距仅约6.39e-6。

仅用成本间距：抓到3/5、漏掉2/5、误报26次。中等精度报警：抓到4/5、漏掉1/5、误报1次，但含回退p95为18.10ms，高于全部精细13.64ms和普通top8的6.11ms。因此本轮没有得到同时可靠且便宜的识别器。

重要限制：更细步长改变10/96个参考赢家；5个失败中4个在更细参考下仍有损失。唯一被中等精度漏报的批次138，其损失在更细参考下消失。不能把这个例子包装为稳定的物理漏报反例，也不能因4个持久失败均报警就宣称可靠识别。

下一步优先对4个持久失败做数值收敛和接触事件审计，并加入普通的候选去重/分簇保留代表基线，检验近重复问题是否只是候选多样性不足。在这两项审计前，不提出新的认证算法或RA-L创新结论。
'''
    en+='''
## Measured decision

Five of 96 test batches miss the fine winner: reversal 3/24 and near-duplicate 2/24; grazing and fast-corner each 0/24, not universal safety. Worst coarse rank is 19. Zero-based batch 121 has winner 49 at coarse rank 19, regret 0.301907, persisting at 0.416679 with the half step. Batch 145 has coarse rank 17 for the fine winner and a coarse margin about 6.39e-6.

Margin alarm detects 3/5, misses 2/5 and raises 26 false alarms. Medium alarm detects 4/5, misses 1/5 and raises one false alarm. Its fallback-inclusive p95 is 18.10ms versus 13.64ms all-fine and 6.11ms top-eight. No detector is demonstrated to be both reliable and cheap here.

The finer step changes 10/96 winners. Four of five failures persist; the sole medium-alarm false negative (batch 138) disappears under the finer reference. It is not a stable physical counterexample. Catching all four persistent failures does not establish general reliability.

Next prioritize numerical convergence/contact-event audits of the four persistent failures and a standard candidate deduplication/cluster-diversity baseline. Do not claim an original certified method or RA-L contribution before these checks.
'''
    (ROOT/'report'/'PUSH_T_SCREEN_STRESS_REPORT.md').write_text(zh,encoding='utf8');(ROOT/'report'/'PUSH_T_SCREEN_STRESS_REPORT_EN.md').write_text(en,encoding='utf8')
    print(details)

if __name__=='__main__':
    import sys
    {'freeze':freeze,'run':run,'analyze':analyze}[sys.argv[1]]()
