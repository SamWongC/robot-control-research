"""Contact-local refinement with end-to-end and exactly matched step budgets."""
from pathlib import Path
import json,time
import numpy as np
import mujoco
import push_t_fixed_batch as base
ROOT=Path(__file__).resolve().parent;O=ROOT/'results'/'push_t_local_refinement';OLD=ROOT/'results'/'push_t_confirmation'
LOW=.0025;HIGH=.000625;METHODS=['uniform_low','uniform_medium','uniform_high','contact_local','spread_matched','uniform_matched']
def dump(n,x):(O/n).write_text(json.dumps(x,indent=2),encoding='utf8')
def add(ev,dt):
    if dt not in ev.models:
        ev.models[dt]=base.model(dt)
        for n in [1,8]:ev.data[dt,n]=[mujoco.MjData(ev.models[dt]) for _ in range(n)]
def mask_from(states,active):
    flag=active|(base.gap(states[:,:,1:6])<.008);mask=flag.copy();mask[:,1:]|=flag[:,:-1];mask[:,:-1]|=flag[:,1:];return mask
def mixed(ev,init,u,g,mask):
    state=init.copy();record=[]
    for k in range(20):
        nxt=state.copy()
        for flag,dt in [(True,HIGH),(False,LOW)]:
            ids=np.flatnonzero(mask[:,k]==flag)
            if len(ids):nxt[ids]=ev.evaluate(state[ids],u[ids,k:k+1],g,dt)[1][:,-1]
        state=nxt;record.append(state.copy())
    states=np.stack(record,axis=1);return base.costs(states,u,g),states
def run():
    O.mkdir(parents=True,exist_ok=True)
    if (O/'protocol.json').exists():raise RuntimeError('Refuse overwrite')
    dump('protocol.json',dict(methods=METHODS,low=LOW,high=HIGH,medium=.00125,threshold=.008,dilation=1,repeats=3,
      scope='Exploratory reuse of 256 previously inspected confirmation batches; fixed rules before this run, no fresh generalization claim.',
      detector='Low-resolution force contact OR endpoint geometric gap <8mm; one-stage dilation; no reference access.',
      step_budget='All adaptive methods include same low pilot. Per candidate with n fine stages: rerun steps=400+60*n. Spread uses n evenly spaced fine stages. Uniform matched uses 20+3*n substeps per stage, exactly matching per-candidate steps.',
      source_sha256=base.sha(__file__),base_sha256=base.sha(base.__file__),fixture_sha256=base.sha(OLD/'fixture.npz'),solver='Original Newton50 tolerance1e-10, warmstart disabled consistently'))
    f=np.load(OLD/'fixture.npz');ref=np.load(OLD/'costs.npz')['costs'];ev=base.Evaluator();add(ev,HIGH)
    for count in range(21):add(ev,.05/(20+3*count))
    timings=[];quality=[];masks=[];estimates=[];budgets=[];checks=[]
    try:
      init=base.initial(f['qpos'][148],np.zeros(5));u=f['controls'][148];g=f['goals'][148]
      for flag,dt in [(False,LOW),(True,HIGH)]:
        score,ss=mixed(ev,init,u,g,np.full((64,20),flag));a,b,_,_=ev.evaluate(init,u,g,dt);err=float(np.max(np.abs(ss-b)));assert err<1e-7;checks.append(dict(dt=dt,max_state_error=err))
      # Prewarm all dynamic-step models before throughput measurement.
      for dt in ev.models:ev.evaluate(init[:1],u[:1],g,dt)
      for batch in range(256):
        init=base.initial(f['qpos'][batch],np.zeros(5));u=f['controls'][batch];g=f['goals'][batch];scores={};storedmask=None
        for rep in range(3):
          for method in np.random.default_rng(91000+3*batch+rep).permutation(METHODS):
            start=time.perf_counter();pilot_steps=0;nsteps=0
            if method.startswith('uniform_') and method!='uniform_matched':
              dt={'uniform_low':LOW,'uniform_medium':.00125,'uniform_high':HIGH}[method];cost,ss,aa,meta=ev.evaluate(init,u,g,dt);nsteps=meta['steps']
            else:
              _,ps,pa,meta=ev.evaluate(init,u,g,LOW);mask=mask_from(ps,pa);count=mask.sum(axis=1);pilot_steps=meta['steps'];nsteps=int(np.sum(400+60*count));storedmask=mask
              if method=='contact_local':cost,ss=mixed(ev,init,u,g,mask)
              elif method=='spread_matched':
                spread=np.zeros((64,20),bool)
                for i,n in enumerate(count):
                  if n:spread[i,np.floor((np.arange(n)+.5)*20/n).astype(int)]=True
                assert np.array_equal(spread.sum(axis=1),count);cost,ss=mixed(ev,init,u,g,spread)
              else:
                cost=np.zeros(64)
                for n in np.unique(count):
                  ids=np.flatnonzero(count==n);dt=.05/(20+3*int(n));cost[ids]=ev.evaluate(init[ids],u[ids],g,dt)[0]
            elapsed=time.perf_counter()-start;chosen=int(cost.argmin())
            timings.append(dict(batch=batch,method=str(method),repeat=rep,seconds=elapsed,physics_steps=nsteps+pilot_steps,pilot_steps=pilot_steps))
            if rep==0:
              scores[str(method)]=cost;quality.append(dict(batch=batch,method=str(method),chosen=chosen,reference_best=int(ref[batch,2].argmin()),regret=float(ref[batch,2,chosen]-ref[batch,2].min()),max_cost_error=float(np.max(np.abs(cost-ref[batch,2])))))
              if method=='uniform_low':assert np.allclose(cost,ref[batch,1],rtol=0,atol=1e-9)
              if method=='uniform_high':assert np.allclose(cost,ref[batch,2],rtol=0,atol=1e-9)
        estimates.append([scores[m] for m in METHODS]);masks.append(storedmask);budgets.append(dict(batch=batch,fine_stage_fraction=float(storedmask.mean())))
        same=[t['physics_steps'] for t in timings if t['batch']==batch and t['method'] in ['contact_local','spread_matched','uniform_matched']];assert len(set(same))==1
        if batch%32==31:print('completed',batch+1,flush=True)
    finally:ev.close()
    np.savez_compressed(O/'estimates.npz',costs=estimates,contact_masks=masks);dump('timings.json',timings);dump('quality.json',quality);dump('budgets.json',budgets)
    dump('audit.json',dict(passed=True,stitch_checks=checks,reference_costs_reproduced=True,matched_physics_steps=True,timing_count=len(timings)))
def report():
    q=json.loads((O/'quality.json').read_text());t=json.loads((O/'timings.json').read_text());b=json.loads((O/'budgets.json').read_text());finecase=np.load(ROOT/'results'/'push_t_batch148_audit'/'results.npz')['original_costs'][-1];summary=[]
    for m in METHODS:
      rr=[r for r in q if r['method']==m];tt=[x for x in t if x['method']==m];case=next(r for r in rr if r['batch']==148)
      summary.append(dict(method=m,losses=sum(r['regret']>1e-4 for r in rr),mean_regret=float(np.mean([r['regret'] for r in rr])),max_regret=max(r['regret'] for r in rr),p50_ms=float(np.median([x['seconds']*1000 for x in tt])),p95_ms=float(np.percentile([x['seconds']*1000 for x in tt],95)),mean_physics_steps=float(np.mean([x['physics_steps'] for x in tt])),case148_chosen=case['chosen'],case148_regret=case['regret'],case148_finest_regret=float(finecase[case['chosen']]-finecase.min()),case148_median_ms=float(np.median([x['seconds']*1000 for x in tt if x['batch']==148]))))
    result=dict(methods=summary,mean_fine_stage_fraction=float(np.mean([x['fine_stage_fraction'] for x in b])),case148_fraction=b[148]['fine_stage_fraction']);dump('summary.json',result)
    table='| Method | Loss /256 | Mean regret | p95 ms | Mean physics steps | Case148 winner | Case148 median ms |\n|---|---:|---:|---:|---:|---:|---:|\n'
    for s in summary:table+=f"| {s['method']} | {s['losses']} | {s['mean_regret']:.6f} | {s['p95_ms']:.2f} | {s['mean_physics_steps']:.0f} | {s['case148_chosen']} | {s['case148_median_ms']:.2f} |\n"
    raw='\n```json\n'+json.dumps(result,indent=2)+'\n```\n'
    zh='''# 接触阶段局部加密：端到端时间与同预算对照

复用256个已查看的确认批次，属于探索性后续实验，不是新的独立确认。规则在运行前固定，无精细真值输入。

uniform_low/medium/high分别全时域使用0.0025/0.00125/0.000625秒。contact_local先用0.0025秒评估全部64条；有力接触或段末间隙<8mm的时间段加左右一段，然后从原初态重算：标记段0.000625秒，其余0.0025秒。没有缓存跳步，计时包含初筛、几何检测、分组和完整重算。

spread_matched使用同一次数的初筛，每条轨迹将相同数量的精细段均匀分布到整个时域，不使用接触位置；uniform_matched使用同样初筛，以每段20+3n个子步全时域均匀积分，n为该轨迹被标记精细段数。后二者与contact_local逐条轨迹有相同仿真步数，总重算步数400+60n，加初筛400步。步数相同不代表墙钟时间相同，特别是接触密度和调用分组不同；本轮同时实际计时。全部统一关闭求解热启动，避免分段内部状态丢失。

每批每方法3次随机顺序，预热所有使用的模型后计时，共4608次调用。主质量参考为全0.000625秒结果；批次148另外按此前最细0.0000390625秒成本核验。成本损失>1e-4只是数值阈值；没有任务级容忍度或物理真值保证。
'''+table+raw+'''
代码push_t_local_refinement.py，.venv-contact执行run、report；数据results/push_t_local_refinement。全精细/全低精度分段与连续状态在1e-7内一致；新评估重现已有两档成本至1e-9；三种自适应对照逐批总步数精确相等。历史结果保留。

本实验比较固定实现，不足以否定所有接触自适应算法。没有安全证书、闭环实验或独立创新性结论。完整确认集已被查看，不可将本轮结果作为新方法的无偏泛化证明。
'''
    en='''# Contact-local refinement: end-to-end and matched-step comparisons

Exploratory reuse of256 previously inspected batches, not fresh confirmation. Rules frozen before execution; no fine-reference access.

Uniform low/medium/high steps=.0025/.00125/.000625. Contact-local runs all64 at low resolution, marks force-contact or endpoint gap<8mm plus neighboring stages, then reruns from the original initial state with high steps on marked stages and low elsewhere. Timing includes pilot, geometry, grouping and full rerun.

Spread-matched uses the same pilot and per-trajectory number of fine stages placed evenly in time. Uniform-matched uses the same pilot and20+3n substeps per control stage, where n is the number of marked stages. All three have exactly400+60n rerun steps plus400 pilot steps per trajectory. Equal steps are not equal wall time: grouping and contact work differ, so actual timings are recorded. Warmstart uniformly disabled to avoid missing internal state at stage boundaries.

Three randomized repeats per batch/method, all models prewarmed,4608 calls. Primary reference=.000625; case148 additionally checked against archived .0000390625 reference. Regret>1e-4 is numerical, not task tolerance or physical truth.
'''+table+raw+'''
Code push_t_local_refinement.py run/report in .venv-contact. Data results/push_t_local_refinement. All-low/all-high stitched versus continuous states agree within1e-7; saved reference costs reproduce within1e-9; three adaptive methods have identical per-batch total steps. Historical outputs preserved.

Fixed implementations only; no universal rejection of adaptive refinement, safety certificate, closed-loop result or novelty claim. Inspected batches do not provide unbiased new-method generalization evidence.
'''
    zh+='''
## 实测结论

批次148：局部加密选37，按先前最细参考损失为0；但中位耗时69.44ms，高于全高精度58.20ms。统一中等步长也选37，仅30.42ms。两个同预算对照也都选37，因此该案例不能证明接触定位特有优势。

全部256批：局部加密损失2批，对比同预算均匀铺段14批、同预算均匀步长10批，支持接触位置选择在本批次集上提高计算分配质量。但局部p95为98.63ms，高于全高精度87.09ms；统一中等精度43.95ms但损失12批。不存在本实现已同时达到完整参考质量与更低总耗时的证据。

局部方法平均标记57.10%的时间段，批次148标记64.14%。包含预计算后，全体平均步数95056对比全高精度102400，仅减少7.17%；批次148约100460步，仅减少1.89%。分组、重新调用和重复积分吃掉了有限的步数节省。计时为本轮实际测量，应与本轮对照比较，不应跨实验直接比较绝对毫秒数。

去留：质量分配信号值得记录，但当前两遍接触加密实现没有通过速度门槛，批次148可由更简单的统一中等步长解决。不能据此声称独立RA-L贡献。若继续，只宜先做有界的单遍/连续段实现可行性评估，保留同预算与统一步长基线，并在另一个新冻结集验证；不要先叠加神经网络，也不要用仅积分步数下降替代端到端加速。
'''
    en+='''
## Measured conclusion

Case148: contact-local selects37, zero regret under the archived finest reference, but median69.44ms exceeds all-high58.20ms. Uniform medium also selects37 at30.42ms. Both matched-step comparators also recover37, so this case shows no unique advantage from contact localization.

Across256 batches contact-local has2 losses versus14 spread-matched and10 uniform-matched, supporting more useful compute placement on these inspected batches. However its p95 is98.63ms versus87.09ms all-high. Uniform medium takes43.95ms but has12 losses. No demonstrated joint achievement of full reference quality and lower total latency.

Fine-stage fraction averages57.10%,64.14% for148. Including the pilot, mean steps95056 versus102400 save only7.17%; case148 uses about100460, saving1.89%. Grouping, repeated calls and reintegration consume the limited savings. Compare timings within this run, not absolute milliseconds across prior runs.

Decision: retain the quality-allocation signal, but the two-pass prototype fails the speed gate; uniform medium already solves148. No standalone RA-L contribution is established. A bounded single-pass/contiguous-segment feasibility check could precede further work, retaining matched-budget and uniform baselines and a fresh frozen validation set. Do not replace end-to-end acceleration with step-count claims.
'''
    (ROOT/'report'/'PUSH_T_LOCAL_REFINEMENT_REPORT.md').write_text(zh,encoding='utf8');(ROOT/'report'/'PUSH_T_LOCAL_REFINEMENT_REPORT_EN.md').write_text(en,encoding='utf8');print(table);print(raw)
if __name__=='__main__':
    import sys
    {'run':run,'report':report}[sys.argv[1]]()
