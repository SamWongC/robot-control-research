"""Prospectively frozen confirmation of fixed shortlist rules; no retuning."""
from pathlib import Path
import json,time,inspect
import numpy as np
import mujoco
import push_t_fixed_batch as base
import push_t_screen_stress as stress
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results'/'push_t_confirmation'
METHODS=['fine','top8','top16','top32','hybrid16','hybrid32']
def dump(n,x):(OUT/n).write_text(json.dumps(x,indent=2),encoding='utf8')
def select(u,c,name):
    if name=='fine':return np.arange(64)
    k=int(''.join(x for x in name if x.isdigit()));order=np.argsort(c,kind='stable')
    if name.startswith('top'):return order[:k]
    ids=order[:k//2].tolist();pool=order[:min(2*k,64)];x=u.reshape(64,-1)
    while len(ids)<k:
        remaining=np.array([i for i in pool if i not in ids]);d=np.min(np.mean((x[remaining,None]-x[np.array(ids)][None])**2,axis=2),axis=1)
        ids.append(int(remaining[np.argmax(d)]))
    return np.array(ids)
def freeze():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'protocol.json').exists() or (OUT/'fixture.npz').exists():raise RuntimeError('Refuse overwrite')
    # Reuse the exact previous generator, changing only seed, split and sample count.
    src=inspect.getsource(stress.freeze).replace('2026110402','2026110403').replace("['development','test']","['confirmation']").replace('range(24)','range(64)')
    namespace=dict(stress.__dict__);namespace['OUT']=OUT;namespace['dump']=dump
    exec(compile(src,'frozen_generator','exec'),namespace);namespace['freeze']()
    dump('protocol.json',dict(seed=2026110403,batches=256,per_family=64,methods=METHODS,repeats=3,
        primary_reference=.0025,audit_reference=.000625,coarse_step=.01,reporting_tolerance=1e-4,
        hybrid='Retain best k/2 by coarse cost; fill to k using farthest minimum RMS action distance within coarse top min(2*k,64). Stable ties by coarse ordering.',
        decision='Check any losses >1e-4, worst loss and p95 latency versus all-fine; report reference sensitivity. No task-level acceptable loss or certified safety established. Zero observed misses is not proof.',
        fixture_sha256=base.sha(OUT/'fixture.npz'),source_sha256=base.sha(__file__),generator_sha256=base.sha(stress.__file__),base_sha256=base.sha(base.__file__),scope='New samples from unchanged four-family synthetic distribution; not new task, real robot or novelty validation.'))
    (OUT/'frozen_generator.py.txt').write_text(src,encoding='utf8')
def run():
    if (OUT/'quality.json').exists():raise RuntimeError('Refuse overwrite results')
    p=json.loads((OUT/'protocol.json').read_text());assert base.sha(__file__)==p['source_sha256'];assert base.sha(OUT/'fixture.npz')==p['fixture_sha256']
    f=np.load(OUT/'fixture.npz');ev=base.Evaluator();dt=.000625;ev.models[dt]=base.model(dt)
    for n in [1,8]:ev.data[dt,n]=[mujoco.MjData(ev.models[dt]) for _ in range(n)]
    families=['grazing','reversal','near_duplicate','fast_corner'];refs=[];rows=[];timings=[]
    try:
      for b in range(256):
        u=f['controls'][b];g=f['goals'][b];init=base.initial(f['qpos'][b],np.zeros(5))
        co=ev.evaluate(init,u,g,.01)[0];fi=ev.evaluate(init,u,g)[0];au=ev.evaluate(init,u,g,dt)[0];refs.append([co,fi,au])
        for rep in range(3):
          for method in np.random.default_rng(88000+3*b+rep).permutation(METHODS):
            start=time.perf_counter()
            if method=='fine':ids=np.arange(64)
            else:ids=select(u,ev.evaluate(init,u,g,.01)[0],str(method))
            vals=ev.evaluate(init[ids],u[ids],g)[0];chosen=int(ids[vals.argmin()]);elapsed=time.perf_counter()-start
            assert len(ids)==len(set(ids)) and np.allclose(vals,fi[ids],rtol=0,atol=1e-9)
            timings.append(dict(batch=b,method=str(method),repeat=rep,seconds=elapsed))
            if rep==0:rows.append(dict(batch=b,family=families[b//64],method=str(method),chosen=chosen,ids=ids.tolist(),regret=float(fi[chosen]-fi.min()),audit_regret=float(au[chosen]-au.min()),audit_set_regret=float(au[ids].min()-au.min()),reference_winner_changed=bool(fi.argmin()!=au.argmin())))
        if b%32==31:print('completed',b+1,flush=True)
    finally:ev.close()
    np.savez_compressed(OUT/'costs.npz',costs=refs);dump('quality.json',rows);dump('timings.json',timings)
def report():
    rows=json.loads((OUT/'quality.json').read_text());tt=json.loads((OUT/'timings.json').read_text());a=np.load(OUT/'costs.npz')['costs'];summary=[]
    assert a.shape==(256,3,64) and np.isfinite(a).all() and len(tt)==256*6*3
    for r in rows:assert np.isclose(r['regret'],a[r['batch'],1,r['chosen']]-a[r['batch'],1].min())
    for m in METHODS:
      rr=[r for r in rows if r['method']==m];summary.append(dict(method=m,losses=sum(r['regret']>1e-4 for r in rr),max_regret=max(r['regret'] for r in rr),mean_regret=float(np.mean([r['regret'] for r in rr])),audit_output_losses=sum(r['audit_regret']>1e-4 for r in rr),audit_set_losses=sum(r['audit_set_regret']>1e-4 for r in rr),p95_ms=float(np.percentile([t['seconds']*1000 for t in tt if t['method']==m],95)),family_losses={fam:sum(r['regret']>1e-4 for r in rr if r['family']==fam) for fam in ['grazing','reversal','near_duplicate','fast_corner']}))
    result=dict(methods=summary,reference_winner_changes=sum(r['reference_winner_changed'] for r in rows if r['method']=='fine'),zero_loss_one_sided_95_upper=1-.05**(1/256))
    dump('summary.json',result);dump('failures.json',[r for r in rows if r['regret']>1e-4]);dump('audit.json',dict(passed=True,finite_costs=True,recomputed_regrets=True,selected_cost_reproduction=True,unique_ids=True,timed_calls=len(tt)))
    tab='| Method | Loss /256 | Max regret | Mean regret | p95 ms | Finer-reference set loss /256 |\n|---|---:|---:|---:|---:|---:|\n'
    for s in summary:tab+=f"| {s['method']} | {s['losses']} | {s['max_regret']:.6f} | {s['mean_regret']:.6f} | {s['p95_ms']:.2f} | {s['audit_set_losses']} |\n"
    raw='\n```json\n'+json.dumps(result,indent=2)+'\n```\n'
    zh='''# 新冻结确认集：前16、前32与排序/多样性混合保留

在执行前冻结种子2026110403、256个批次（四类各64，每批64候选）、方法、阈值和源代码哈希。完全复用上一轮场景生成分布，仅改变种子和数量；这是新样本确认，不是新任务或实机泛化。没有依据结果调整方法。

混合16/32：先保留粗成本前8/16，再在粗前32/64中按与已选动作序列的最小RMS距离最远原则补齐至16/32。这个简单规则同时保留排序与多样性，不使用精细真值或生成器簇标签。top8用于上下文，fine为全64精评。所有在线精评步长0.0025秒，粗步长0.01秒，额外0.000625秒全候选仅作离线参考审计。

每批每方法3次随机顺序计时，共4608次；包含粗评、筛选及精评，预热/参考构建不计入。p95为描述统计。损失阈值1e-4是数值报告阈值，不是机器人任务容许损失。更细参考集合损失指即便对所保留候选按更细模型重新排序，仍漏掉更好候选；实际输出的更细参考损失另存summary.json，包含在线精细模型自身的排序误差。
'''+tab+raw+'''
即使某方法零漏选也不能证明普遍可靠；在独立同分布伯努利假设下，256次零失败对应单侧95%失败率上界约1.16%，这里只作为规模提示，分层固定场景和有限合成模型限制其外推。参考赢家变化说明不能将0.0025秒结果当物理真值。

文件：push_t_confirmation.py；results/push_t_confirmation内保存fixture、协议、冻结生成器、三档成本、逐次计时、候选索引和失败案例。使用.venv-contact依次运行freeze/run/report；冻结和运行均拒绝覆盖已有主要输出。所有历史实验保留。成本重现、候选唯一性、有限值及回算损失检查通过。没有建立误差证书或创新性。
'''
    en='''# Fresh confirmation: top16, top32 and rank/diversity mixtures

Seed2026110403, 256 batches (64 per family, 64 candidates each), methods, threshold and source hashes frozen before execution. Exact previous generator distribution with new seed/count. New-sample confirmation, not a new task or hardware generalization; no outcome-driven tuning.

Hybrid16/32 retain coarse top8/16 and fill to16/32 by farthest minimum action-RMS distance within coarse top32/64. No fine truth or generator labels. Fine evaluates all64; top8 provides context. Online fine/coarse steps .0025/.01; offline all-candidate audit .000625.

Three randomized repetitions per method/batch, 4608 timed calls including coarse evaluation, selection and refinement. Warmup/reference construction excluded. Descriptive p95. Regret >1e-4 is a numerical reporting threshold, not a task tolerance. Finer-reference set loss remains even after ideal finer reranking within the retained subset. Actual output audit losses, including fine-model misranking, are separately in summary.json.
'''+tab+raw+'''
Zero observed losses does not establish reliability. Under iid Bernoulli assumptions, zero/256 gives a one-sided95% upper failure-rate bound about1.16%; stratified fixed families and synthetic scope limit extrapolation. Reference winner changes preclude treating the fine model as physical truth.

Artifacts under results/push_t_confirmation; code push_t_confirmation.py, .venv-contact, freeze/run/report. Main outputs refuse overwrite. Assertions check finite costs, selected cost reproduction, unique IDs and recomputed regret. Historical results preserved. No certificate or novelty established.
'''
    (ROOT/'report'/'PUSH_T_CONFIRMATION_REPORT.md').write_text(zh,encoding='utf8');(ROOT/'report'/'PUSH_T_CONFIRMATION_REPORT_EN.md').write_text(en,encoding='utf8');print(tab);print(raw)
if __name__=='__main__':
    import sys
    {'freeze':freeze,'run':run,'report':report}[sys.argv[1]]()
