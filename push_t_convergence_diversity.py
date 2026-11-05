"""Post-hoc convergence audit and fixed ordinary diversity baselines."""
from pathlib import Path
import json,time
import numpy as np
import mujoco
import push_t_fixed_batch as base
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'results'/'push_t_convergence_diversity'; OLD=ROOT/'results'/'push_t_screen_stress'
CASES=[121,139,145,159]; DTS=[.01,.005,.0025,.00125,.000625,.0003125,.00015625]
METHODS=['fine','top8','dedup8','cluster8','top16','cluster16']
def dump(n,x):(OUT/n).write_text(json.dumps(x,indent=2),encoding='utf8')
def select(u,c,method):
    k=16 if method.endswith('16') else 8; order=np.argsort(c,kind='stable');x=u.reshape(len(u),-1)
    if method.startswith('top'):return order[:k]
    if method=='dedup8':
        ids=[]
        for i in order:
            if not ids or np.min(np.sqrt(np.mean((x[ids]-x[i])**2,axis=1)))>=.02:ids.append(int(i))
            if len(ids)==k:break
        ids+= [int(i) for i in order if i not in ids][:k-len(ids)]
        return np.array(ids)
    # Ordinary deterministic k-means in action space, farthest-point initialization.
    centers=[x[order[0]].copy()]
    for _ in range(k-1):
        dist=np.min(np.sum((x[:,None]-np.array(centers)[None])**2,axis=2),axis=1)
        centers.append(x[int(np.argmax(dist))].copy())
    centers=np.array(centers)
    for _ in range(20):
        labels=np.argmin(np.sum((x[:,None]-centers[None])**2,axis=2),axis=1)
        nxt=centers.copy()
        for j in range(k):
            if np.any(labels==j):nxt[j]=x[labels==j].mean(axis=0)
        if np.allclose(nxt,centers,rtol=0,atol=1e-12):break
        centers=nxt
    labels=np.argmin(np.sum((x[:,None]-centers[None])**2,axis=2),axis=1)
    ids=[int(order[labels[order]==j][0]) for j in range(k) if np.any(labels==j)]
    ids += [int(i) for i in order if i not in ids][:k-len(ids)]
    return np.array(ids)

def trace(q,u,dt):
    m=base.model(dt);d=mujoco.MjData(m);d.qpos[:]=q;mujoco.mj_forward(m,d)
    sub=round(.05/dt);poses=[];masks=[];forces=[];times=[];out=[]
    for k in range(20):
      d.ctrl[:]=u[k]
      for _ in range(sub):
        mujoco.mj_step(m,d);mask=0;normal=0.
        for j in range(d.ncon):
          con=d.contact[j];names={mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,int(g)) for g in [con.geom1,con.geom2]}
          if 'finger' in names:
            if 'bar' in names:mask|=1
            if 'stem' in names:mask|=2
            force=np.zeros(6);mujoco.mj_contactForce(m,d,j,force);normal+=max(0,float(force[0]))
        poses.append(d.qpos.copy());masks.append(mask);forces.append(normal);times.append(d.time)
      state=np.zeros(11);state[0]=d.time;state[1:6]=d.qpos;state[6:]=d.qvel;out.append(state)
    active=np.array(forces)>1e-5;change=np.flatnonzero(np.r_[active[0],active[1:]!=active[:-1]])
    return dict(time=np.array(times),qpos=np.array(poses),mask=np.array(masks),normal_force=np.array(forces)),dict(first_force_contact=float(np.array(times)[active][0]) if active.any() else None,
      force_transitions=[dict(time=float(times[j]),active=bool(active[j])) for j in change],normal_impulse=float(np.sum(forces)*dt),contact_fraction=float(active.mean()),pair_mask_transitions=int(np.count_nonzero(np.diff(masks)))),np.array(out)

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'protocol.json').exists():raise RuntimeError('Refusing overwrite')
    f=np.load(OLD/'fixture.npz'); old=np.load(OLD/'costs.npz')['costs'];labels=json.loads((OLD/'protocol.json').read_text())['labels']
    dump('protocol.json',dict(cases=CASES,steps=DTS,methods=METHODS,dedup_rms_threshold=.02,kmeans_iterations=20,fixture_sha256=base.sha(OLD/'fixture.npz'),source_sha256=base.sha(__file__),base_source_sha256=base.sha(base.__file__),scope='Exploratory reuse of previously inspected test batches; not a fresh confirmatory test. Fixed parameters before this run; no tuning.'))
    ev=base.Evaluator()
    for dt in DTS:
      if dt not in ev.models:
        ev.models[dt]=base.model(dt)
        for n in [1,8]:ev.data[dt,n]=[mujoco.MjData(ev.models[dt]) for _ in range(n)]
    conv=[];traces=[];quality=[];timing=[];arrays={}
    try:
      for b in CASES:
        init=base.initial(f['qpos'][b],np.zeros(5));u=f['controls'][b];g=f['goals'][b];cc=[];ss=[];aa=[]
        for dt in DTS:
          costs,states,contact,_=ev.evaluate(init,u,g,dt);cc.append(costs);ss.append(states);aa.append(contact)
        cc=np.array(cc);ss=np.array(ss);aa=np.array(aa);assert np.allclose(cc[:4],old[b],rtol=0,atol=1e-9)
        arrays[f'costs_{b}']=cc;arrays[f'states_{b}']=ss;arrays[f'contact_{b}']=aa
        ids=np.argsort(cc[0])[:8];picked=int(ids[np.argmin(cc[2,ids])]);winner=int(np.argmin(cc[-1]));orig=int(cc[2].argmin())
        steps=[]
        for j,dt in enumerate(DTS):steps.append(dict(dt=dt,winner=int(cc[j].argmin()),old_top8_choice_regret=float(cc[j,picked]-cc[j].min()),best_available_in_coarse_top8_regret=float(cc[j,ids].min()-cc[j].min()),max_cost_delta_to_finest=float(np.max(np.abs(cc[j]-cc[-1]))),max_pose_delta_to_finest=float(np.max(np.linalg.norm(ss[j,:,:,:][:,:,1:4]-ss[-1,:,:,1:4],axis=2)))))
        conv.append(dict(batch=b,family=labels[b]['family'],coarse_top8=ids.tolist(),old_top8_choice=picked,original_fine_winner=orig,finest_winner=winner,finest_winner_coarse_rank=int(np.flatnonzero(np.argsort(cc[0])==winner)[0])+1,steps=steps,
          coarse_finest_contact_stage_disagreement=float(np.mean(aa[0]!=aa[-1])),last_two_max_cost_delta=float(np.max(np.abs(cc[-2]-cc[-1]))),last_two_winner_equal=bool(cc[-2].argmin()==winner)))
        for i in sorted(set([picked,orig,winner])):
          for j in [0,2,6]:
            data,meta,state=trace(f['qpos'][b],u[i],DTS[j]);np.savez_compressed(OUT/f'trace_b{b}_c{i}_d{j}.npz',**data)
            assert np.allclose(state,ss[j,i],rtol=0,atol=1e-8)
            traces.append(dict(batch=b,candidate=i,dt=DTS[j],**meta))
        print('audited case',b,flush=True)
      for b in range(96,192):
        init=base.initial(f['qpos'][b],np.zeros(5));u=f['controls'][b];g=f['goals'][b]
        for rep in range(3):
          for method in np.random.default_rng(55000+b*3+rep).permutation(METHODS):
            t=time.perf_counter()
            if method=='fine':ids=np.arange(64)
            else:
              c=ev.evaluate(init,u,g,.01)[0];ids=select(u,c,str(method))
            vals=ev.evaluate(init[ids],u[ids],g)[0];chosen=int(ids[vals.argmin()]);elapsed=time.perf_counter()-t
            assert len(set(ids))==len(ids);assert np.allclose(vals,old[b,2,ids],rtol=0,atol=1e-9)
            timing.append(dict(batch=b,method=str(method),repeat=rep,seconds=elapsed))
            if rep==0:quality.append(dict(batch=b,family=labels[b]['family'],method=str(method),ids=ids.tolist(),chosen=chosen,regret=float(old[b,2,chosen]-old[b,2].min()),halfstep_regret=float(old[b,3,chosen]-old[b,3].min())))
        if b%24==23:print('baseline batches',b-95,flush=True)
    finally:ev.close()
    np.savez_compressed(OUT/'convergence.npz',**arrays);dump('convergence.json',conv);dump('contact_traces.json',traces);dump('quality.json',quality);dump('timings.json',timing)
    dump('audit.json',dict(passed=True,checks=['All four old cost arrays reproduced at 1e-9','Selected individual mj_step traces match batched states at 1e-8','All baseline selected costs reproduce saved reference at 1e-9','Unique candidate IDs'],timed_calls=len(timing)))

def report():
    conv=json.loads((OUT/'convergence.json').read_text());q=json.loads((OUT/'quality.json').read_text());tt=json.loads((OUT/'timings.json').read_text())
    stats=[]
    for method in METHODS:
      rows=[r for r in q if r['method']==method];stats.append(dict(method=method,misses=sum(r['regret']>1e-4 for r in rows),mean_regret=float(np.mean([r['regret'] for r in rows])),max_regret=max(r['regret'] for r in rows),halfstep_losses=sum(r['halfstep_regret']>1e-4 for r in rows),p95_ms=float(np.percentile([t['seconds']*1000 for t in tt if t['method']==method],95)),case_regrets={str(r['batch']):r['regret'] for r in rows if r['batch'] in CASES}))
    dump('summary.json',stats)
    tab='| Method | Loss >1e-4 /96 | Mean regret | Max regret | p95 ms |\n|---|---:|---:|---:|---:|\n'
    for s in stats:tab+=f"| {s['method']} | {s['misses']} | {s['mean_regret']:.6f} | {s['max_regret']:.6f} | {s['p95_ms']:.2f} |\n"
    ct='| Batch | Fine winner | Finest winner | Coarse rank | Finest top8-set loss | Last two max cost delta |\n|---|---:|---:|---:|---:|---:|\n'
    for c in conv:ct+=f"| {c['batch']} | {c['original_fine_winner']} | {c['finest_winner']} | {c['finest_winner_coarse_rank']} | {c['steps'][-1]['best_available_in_coarse_top8_regret']:.6f} | {c['last_two_max_cost_delta']:.6f} |\n"
    detail='\n```json\n'+json.dumps(stats,indent=2)+'\n```\n'
    zh='''# 四个持续失败案例：数值收敛、接触审计与候选多样性基线

本轮复用已查看过的96个测试批次，因此是探索性后续分析，不是新的独立确认集。没有在这些结果上调参；原始输出全部保留。案例为121、139、145、159（从0编号）。沿用简化模型，非实机证据。

## 数值审计

所有64条候选分别使用0.01、0.005、0.0025、0.00125、0.000625、0.0003125、0.00015625秒步长；保持同一控制和代价采样时刻。下表最后一列是所有候选在最后两档间的最大成本变化，不能仅凭赢家相同声称数值收敛。最细结果仍是离散参考。Top8-set loss指即使在粗前8里按最细模型重新挑选，仍不可避免的损失。
'''+ct+'''
对原精细赢家、最细赢家和原top8输出逐步记录了接触几何对（bar/stem）、法向力、接触建立/释放时刻和法向冲量，分别在粗、原精细、最细步长下重放。逐步状态与批量接口一致。原始轨迹在trace_*.npz，事件表在contact_traces.json。几何接触与力阈值接触分别记录；事件时刻有步长量化。接触序列不同只支持接触数值敏感性，不能单凭相关性断言是唯一原因。没有更改接触刚度/摩擦做因果干预，也没有物理验证。

## 普通候选筛选基线

- top8/top16：粗成本排序前8/16。
- dedup8：按粗成本遍历，动作序列逐元素RMS距离至少0.02 m/s才保留；不足8条时按粗排序补齐。阈值固定，没有用测试标签选择。
- cluster8/cluster16：动作序列展平成40维，最远点初始化、最多20轮普通k-means，每簇选粗成本最低者，空缺按粗排名补齐。分簇不读取候选生成时的真实簇标签，也不读取精细成本。
- 所有方法仅用0.0025秒精评保留候选；计时包含粗计算、筛选/分簇和精评。fine为全64条同档精评。每批每方法3次，顺序打乱，p95是288次调用的描述统计。
'''+tab+detail+'''
成本损失阈值1e-4仅用于数值报告。必须同时检查96批总体表现和4案例，不能只展示修好的案例。半步参考损失包括精细模型本身排名偏差，不能全归因于筛选。

代码push_t_convergence_diversity.py，使用.venv-contact执行run、report；run拒绝覆盖。数据在results/push_t_convergence_diversity。旧四档成本重现、逐步轨迹重现、各基线精评成本重现和候选唯一性均有断言，audit.json保存检查结果。当前没有建立认证误差界或论文原创性。
'''
    en='''# Four persistent failures: convergence, contact traces and diversity baselines

Exploratory reuse of the previously inspected 96 test batches, not new independent confirmation. Fixed parameters, no tuning on these results. Cases 121,139,145,159, zero-based. Historical files preserved. Simplified model, no hardware evidence.

## Numerical audit

All 64 candidates at seven steps: .01,.005,.0025,.00125,.000625,.0003125,.00015625 seconds. Identical action and cost sampling. Last-two maximum cost difference concerns all candidates; stable winners alone do not establish convergence. Finest remains a discrete reference. Top8-set loss is unavoidable even after reranking the coarse shortlist with the finest model.
'''+ct+'''
Original fine winner, finest winner and original top-eight output were independently stepped at coarse/original-fine/finest resolution. Saved geometric contact-pair masks (bar/stem), normal forces, force-based onset/release times and integrated normal impulses. Direct-step states reproduce batched states. Raw trace_*.npz and contact_traces.json retain evidence. Contact times are quantized; changed contact sequences demonstrate numerical sensitivity, not unique causal attribution. No stiffness/friction intervention or physical validation.

## Ordinary baselines

top8/top16 retain the cheapest coarse candidates. dedup8 greedily retains candidates with action RMS distance >=.02 m/s and fills missing slots by cost. cluster8/cluster16 use action-space k-means (farthest initialization, <=20 iterations), cheapest coarse member per cluster, and cost-based fill. No true generator labels or fine costs are used. Parameters fixed before this run. Retained candidates are evaluated at .0025 seconds. All timing includes coarse evaluation, selection/clustering and fine refinement; three randomized repeats per batch (288 calls per method). Fine evaluates all 64 candidates.
'''+tab+detail+'''
The 1e-4 reporting threshold is not a physical task tolerance. Evaluate all 96 batches, not only repaired cases. Half-step losses also include fine-model ranking discrepancies. Run push_t_convergence_diversity.py run then report in .venv-contact; run refuses overwrite. Data under results/push_t_convergence_diversity. Assertions verify old four-resolution costs, direct-step traces, baseline reference costs and unique candidate IDs; audit.json records success. No certificate or novelty established.
'''
    zh+='''
## 本轮证据支持的机制与结论

四案例在0.005秒及全部更细档位上赢家一致，最细模型下粗前8集合的不可避免损失分别为0.240107、0.136916、0.270848、0.019125。因此漏选不是原0.0025秒参考独有的排序现象。然而最后两档的全候选最大成本变化仍为0.027–0.074，不能说全部成本已充分收敛，更不能给出可靠误差界。

- 121：赢家49的首次有力接触从粗模型0.100秒变为最细0.08969秒；粗模型法向冲量约0.04253，最细0.03963。其粗排第19，当前所有多样性方法及top16均未恢复赢家。支持粗接触积分改变排名，尚不能唯一归因于某次事件。
- 139：赢家36首次接触从0.140秒变为0.11516秒，冲量从0.01380变为0.01144；原筛选最终选静止候选0。cluster8及top16能修复。粗模型低估了这个有效推动候选的相对价值。
- 145：粗前8的ID为[6,1,0,7,4,5,2,3]，全部来自生成器簇0；赢家54属于簇6。簇0被选代表6全程无有力接触，赢家54则有接触，粗冲量0.02688对比最细0.01686。去重、cluster8、cluster16均修复该案例，而top16仍失败。这里有直接的跨簇覆盖缺失证据；簇标签只用于事后解释，没有输入筛选器。
- 159：粗前8为[13,11,8,9,12,15,14,27]，已包含赢家10所在的簇1，却排除了10。因此不仅是跨簇覆盖问题，还存在簇内粗排序失真。赢家10的首次接触0.040秒对比0.03031秒；去重/分簇将原损失0.01682扩大到0.05382，top16可修复。

接触切换计数随采样精度变化，也可能反映力阈值附近的数值抖动，不能把更多切换直接解释为真实机器人事件。没有做接触干预实验，所以以上是已定位的筛选机制与接触数值差异，不是完整因果证明。

全96批：top8损失5次，dedup8为14次、cluster8为16次、cluster16为14次；普通top16降为2次，p95约8.02ms（全精细13.74ms）。这说明本轮固定的多样性基线没有整体解决问题，并不证明所有去重/分簇方法无效。top16是更强的简单对照，且剩余失败集中在121、145。

下一步应在新冻结确认集上比较更强的简单策略（例如前32、排序与多样性混合保留），并预先定义任务容许损失；同时继续收敛审计。当前应研究的是接触模型误差引起的候选价值错序，不能把单纯增加多样性当成论文创新，也不能宣称排除了所有已有方法。
'''
    en+='''
## Evidence-supported mechanisms and decision

All four winners are stable from .005 seconds through every finer level. Finest coarse-top-eight set losses are .240107,.136916,.270848,.019125. Thus misses persist beyond the original .0025 reference. Last-two all-candidate maximum cost differences remain .027–.074: full cost convergence and certified error bounds are not established.

- 121: winner49 first force contact is .100s coarse versus .08969s finest; normal impulse .04253 versus .03963. Coarse rank19; all tested diversity methods and top16 fail. Contact integration/ranking discrepancy is supported, but no unique causal event is established.
- 139: winner36 onset .140 versus .11516s; impulse .01380 versus .01144. Original shortlist selects stationary candidate0. Cluster8 and top16 recover the winner.
- 145: coarse top-eight IDs [6,1,0,7,4,5,2,3] all belong to generator cluster0, while winner54 belongs to cluster6. Chosen candidate6 has no force contact; winner54 does, with coarse/finest impulses .02688/.01686. Dedup8, cluster8 and cluster16 recover it; top16 does not. This directly supports cross-cluster coverage failure. Generator labels are retrospective only.
- 159: coarse top-eight [13,11,8,9,12,15,14,27] already covers winner10's cluster1 but excludes10. Within-cluster coarse misranking remains. Winner onset .040 versus .03031s. Diversity baselines worsen original regret .01682 to .05382; top16 recovers the winner.

Transition counts can reflect sampling and force-threshold chatter, not additional physical events. No causal contact intervention was performed. These are localized selection mechanisms and numerical contact differences, not a complete causal proof.

Across 96 batches top8 has five losses, dedup8 fourteen, cluster8 sixteen, cluster16 fourteen. Ordinary top16 has two, p95 about8.02ms versus13.74ms all-fine. Fixed diversity baselines do not solve the aggregate problem; this does not invalidate all diversity methods. Top16 is a stronger simple baseline; remaining cases are121 and145.

Next use a newly frozen confirmation set for stronger ordinary strategies (top32 and rank/diversity mixtures), predefine task-level acceptable loss, and continue convergence checks. Do not claim novelty from diversity or infer that all existing approaches have been excluded.
'''
    (ROOT/'report'/'PUSH_T_CONVERGENCE_DIVERSITY_REPORT.md').write_text(zh,encoding='utf8');(ROOT/'report'/'PUSH_T_CONVERGENCE_DIVERSITY_REPORT_EN.md').write_text(en,encoding='utf8')
    print(ct);print(tab)

if __name__=='__main__':
    import sys
    {'run':run,'report':report}[sys.argv[1]]()
