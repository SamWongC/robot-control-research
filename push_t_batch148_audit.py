"""Fixed batch148, numerical sensitivity across timestep and solver settings."""
from pathlib import Path
import json,time
import numpy as np
import mujoco
from mujoco import rollout
import push_t_fixed_batch as base
ROOT=Path(__file__).resolve().parent;O=ROOT/'results'/'push_t_batch148_audit';OLD=ROOT/'results'/'push_t_confirmation'
DTS=[.01,.0025,.000625,.0003125,.00015625,.000078125,.0000390625]
CONFIGS=[dict(name='original',solver='Newton',iterations=50,tolerance=1e-10,warm=False),dict(name='tight_cold',solver='Newton',iterations=200,tolerance=1e-12,warm=False),dict(name='warm',solver='Newton',iterations=50,tolerance=1e-10,warm=True),dict(name='tight_warm',solver='Newton',iterations=200,tolerance=1e-12,warm=True),dict(name='cg_tight',solver='CG',iterations=200,tolerance=1e-12,warm=True)]
def dump(n,x):(O/n).write_text(json.dumps(x,indent=2),encoding='utf8')
def model(c,dt):
    m=base.model(dt);m.opt.solver=getattr(mujoco.mjtSolver,'mjSOL_'+c['solver'].upper());m.opt.iterations=c['iterations'];m.opt.tolerance=c['tolerance']
    if c['warm']:m.opt.disableflags &= ~int(mujoco.mjtDisableBit.mjDSBL_WARMSTART)
    return m
def trace(m,q,u):
    d=mujoco.MjData(m);d.qpos[:]=q;sub=round(.05/m.opt.timestep);states=[];rows=[]
    for k in range(20):
      d.ctrl[:]=u[k]
      for _ in range(sub):
        mujoco.mj_step(m,d);force=0.;mask=0
        for j in range(d.ncon):
          con=d.contact[j];names={mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,int(g)) for g in [con.geom1,con.geom2]}
          if 'finger' in names:
            mask |= (1 if 'bar' in names else 0)|(2 if 'stem' in names else 0)
            v=np.zeros(6);mujoco.mj_contactForce(m,d,j,v);force+=max(0,float(v[0]))
        rows.append([d.time,force,mask,int(np.max(d.solver_niter)),*d.qpos])
      states.append(np.r_[d.time,d.qpos,d.qvel])
    a=np.array(rows);active=a[:,1]>1e-5
    return a,np.array(states),dict(max_solver_iterations=int(a[:,3].max()),iteration_cap_steps=int(np.sum(a[:,3]>=m.opt.iterations)),warnings=[int(w.number) for w in d.warning],first_contact=float(a[active,0][0]) if active.any() else None,normal_impulse=float(a[:,1].sum()*m.opt.timestep),force_switches=int(np.count_nonzero(np.diff(active.astype(int)))))
def run():
    O.mkdir(parents=True,exist_ok=True)
    if (O/'protocol.json').exists():raise RuntimeError('Refuse overwrite')
    f=np.load(OLD/'fixture.npz');q=f['qpos'][148];u=f['controls'][148];g=f['goals'][148];init=base.initial(q,np.zeros(5))
    dump('protocol.json',dict(batch=148,steps=DTS,configs=CONFIGS,source_sha256=base.sha(__file__),base_sha256=base.sha(base.__file__),fixture_sha256=base.sha(OLD/'fixture.npz'),scope='Same contact parameters, friction, geometry, integrator, cost and controls. Continuous full-horizon calls avoid stage warmstart loss. Exploratory numerical audit, not physical validation.'))
    np.savez_compressed(O/'input.npz',qpos=q,controls=u,goal=g);arrays={};summary=[];trace_stats=[]
    old=np.load(OLD/'costs.npz')['costs'][148];original_ids=np.argsort(old[0],kind='stable')[:32]
    with rollout.Rollout(nthread=8) as runner:
      for c in CONFIGS:
        cc=[];ss=[]
        for dt in DTS:
          m=model(c,dt);data=[mujoco.MjData(m) for _ in range(8)];sub=round(.05/dt);start=time.perf_counter()
          raw,sensor=runner.rollout(m,data,init,np.ascontiguousarray(np.repeat(u,sub,axis=1)))
          assert np.isfinite(raw).all() and np.all(np.diff(np.c_[init[:,0],raw[:,:,0]],axis=1)>0)
          states=raw[:,sub-1::sub].copy();cost=base.costs(states,u,g);cc.append(cost);ss.append(states)
          summary.append(dict(config=c['name'],dt=dt,winner=int(cost.argmin()),cost5=float(cost[5]),cost37=float(cost[37]),cost5_minus37=float(cost[5]-cost[37]),original_top32_set_loss=float(cost[original_ids].min()-cost.min()),elapsed_seconds=time.perf_counter()-start))
          if dt in [.0025,DTS[-1]]:
            for i in [5,37]:
              arr,ds,stats=trace(m,q,u[i]);err=float(np.max(np.abs(ds-states[i])));assert err<1e-7
              np.savez_compressed(O/f"trace_{c['name']}_{dt}_{i}.npz",columns=np.array(['time','normal_force','pair_mask','solver_iterations','ox','oy','yaw','px','py']),data=arr)
              trace_stats.append(dict(config=c['name'],dt=dt,candidate=i,direct_batch_max_error=err,**stats))
          print(c['name'],dt,'winner',int(cost.argmin()),flush=True)
        arrays[c['name']+'_costs']=np.array(cc);arrays[c['name']+'_states']=np.array(ss)
        if c['name']=='original':assert np.allclose(np.array(cc)[:3],old,rtol=0,atol=1e-9)
    np.savez_compressed(O/'results.npz',**arrays);dump('rows.json',summary);dump('traces.json',trace_stats)
    dump('audit.json',dict(passed=True,checks=['Original three resolutions reproduced','Finite monotonic-time rollouts','20 direct-step traces match full batched calls within 1e-7'],trace_count=len(trace_stats)))
def report():
    a=np.load(O/'results.npz');rows=json.loads((O/'rows.json').read_text());tr=json.loads((O/'traces.json').read_text());summary=[]
    table='| Config | Winners, decreasing step | Last-two max cost delta | Finest winner margin | Finest original-top32 set loss |\n|---|---|---:|---:|---:|\n'
    for c in CONFIGS:
      v=a[c['name']+'_costs'];marg=float(np.sort(v[-1])[1]-np.min(v[-1]));delta=float(np.max(np.abs(v[-1]-v[-2])))
      rr=[r for r in rows if r['config']==c['name']]; own=np.argsort(v[0])[:32]
      item=dict(config=c['name'],winners=np.argmin(v,axis=1).tolist(),last_two_max_cost_delta=delta,finest_best_runnerup_margin=marg,finest_original_top32_loss=rr[-1]['original_top32_set_loss'],finest_own_coarse_top32_loss=float(v[-1,own].min()-v[-1].min()),finest_cost5_minus37=float(v[-1,5]-v[-1,37]));summary.append(item)
      table+=f"| {c['name']} | {item['winners']} | {delta:.6g} | {marg:.6g} | {item['finest_original_top32_loss']:.6f} |\n"
    cross=float(np.max(np.ptp(np.array([a[c['name']+'_costs'][-1] for c in CONFIGS]),axis=0)))
    result=dict(settings=summary,max_cross_setting_finest_cost_range=cross,any_trace_warning=any(any(r['warnings']) for r in tr),trace_iteration_cap_steps=sum(r['iteration_cap_steps'] for r in tr));dump('summary.json',result)
    raw='\n```json\n'+json.dumps(result,indent=2)+'\n```\n'
    zh='''# 批次148：排名变化的步长与求解器核查

固定新确认集批次148的全部64条候选、初态、目标、接触参数和积分器。七档步长：0.01、0.0025、0.000625、0.0003125、0.00015625、0.000078125、0.0000390625秒。每条轨迹完整连续求解，不分段重置热启动。

五设置：原Newton50次/1e-10/无热启动；Newton200次/1e-12/无热启动；原精度开启热启动；收紧Newton开启热启动；CG200次/1e-12/热启动。前四用于分离热启动和终止精度影响，CG提供另一求解算法检查。保持物理模型不变；这些是数值敏感性设置，不声称对真实机器人已校准。

表中赢家按上述步长顺序排列。最后两档成本差是经验差异，不是对真实解的误差上界；最优与次优成本间距用于判断排名稳健程度。原top32集合始终使用上一确认实验的粗排序，另记录各设置自身粗top32的漏选。
'''+table+raw+'''
独立逐步重放候选5与37，在原精细和本轮最细步长下记录法向力、几何接触对、每步求解迭代数、报警计数。20条逐步轨迹与批量输出在1e-7内一致；原三档全部成本重现至1e-9。迭代上限/报警检查仅覆盖这些重放轨迹，不应扩展成全部候选的求解器保证。

数据：results/push_t_batch148_audit；代码push_t_batch148_audit.py，.venv-contact执行run、report，run拒绝覆盖。输入、协议、35组全部候选成本与控制段状态、20条逐步轨迹均保存。未改动历史结果。

设置依据：[MuJoCo option文档](https://mujoco.readthedocs.io/en/stable/XMLreference.html#option)、[建模文档](https://mujoco.readthedocs.io/en/stable/modeling.html)。本轮没有改变接触刚度、摩擦或任务，也没有物理实验，不能将单案例数值稳定性当作论文新颖性或现实有效性。
'''
    en='''# Batch148: timestep and solver sensitivity of ranking reversal

All64 frozen candidates, state, target, contact parameters and integrator unchanged. Steps .01,.0025,.000625,.0003125,.00015625,.000078125,.0000390625 seconds. Continuous full-horizon calls preserve within-trajectory warmstart.

Five settings: original Newton50/1e-10/cold; Newton200/1e-12/cold; original accuracy warm; tight Newton warm; CG200/1e-12/warm. First four isolate termination and warmstart effects; CG supplies a different solver. Numerical sensitivity settings, not physical calibration.

Winner lists follow decreasing steps. Last-two cost differences are empirical, not error bounds. Runner-up margin helps assess ranking stability. Original shortlist uses the previously frozen coarse top32; each setting's own coarse shortlist loss is separately recorded.
'''+table+raw+'''
Candidates5 and37 were independently stepped at original-fine and finest resolutions for each setting; saved normal force, contact-pair masks, solver iterations and warning counts. All20 direct traces match batched states within1e-7; original three-resolution costs reproduce within1e-9. Iteration-limit/warning diagnostics cover these traces only.

Artifacts results/push_t_batch148_audit; push_t_batch148_audit.py run/report in .venv-contact. Run refuses overwrite. Frozen input, protocol,35 full-candidate evaluations and20 direct traces retained; history unchanged.

Sources: [MuJoCo options](https://mujoco.readthedocs.io/en/stable/XMLreference.html#option), [modeling](https://mujoco.readthedocs.io/en/stable/modeling.html). No contact stiffness/friction interventions, hardware validation or novelty claim.
'''
    zh+='''
## 核查结论

在本轮全部5种设置下，0.0025秒选候选5，而0.000625秒及以下连续5档均选37。最细参考中，原top32集合损失为1.04856–1.05007，各设置按自身粗模型重新筛前32也有相同损失。因此排名反转与前32漏选跨本轮步长/求解器设置持续存在，不是只在原冷启动Newton50设置下出现。

重放轨迹中Newton每步最多3次迭代，CG最多38次，均未达到上限且没有MuJoCo报警。提高到200次并收紧容差没有消除反转；证据不支持把该现象简单归结为迭代次数不足。

接触差异集中在候选37：原设置的法向冲量从0.0025秒的0.06802降至最细档0.01781，首次接触从0.04000秒变为0.03566秒；候选5冲量约0.03196/0.03199，变化小得多。提示37对接触时间离散更敏感；尚未做局部接触干预，不能宣称已唯一确定因果机制。

限制：最细档最优/次优成本差0.507–0.539，但最后两档全候选最大成本变化仍约0.101，跨设置最大成本差约0.115。因此可以报告“赢家和漏选现象在所测网格内稳定”，不能报告完整成本收敛、严格误差证书或真实机器人最优动作。

选题判断：这个案例可以保留为接触轨迹评估的数值反例，尚不足以构成独立论文创新。下一步应先检验能否通过接触阶段局部加密，在比全时域细化更低的计算开销下恢复正确排名，并与统一中等步长、普通前32及同预算细化对照；同时评估是否能在新样本中稳定复现，而不是只针对148定制算法。
'''
    en+='''
## Audit conclusion

All5 settings select candidate5 at .0025s and candidate37 at every one of the five tested resolutions <=.000625s. Finest original-top32 set loss ranges1.04856–1.05007; recomputing the coarse shortlist for each setting leaves the same loss. The reversal and miss persist across this grid, not only original cold Newton50.

Direct traces use at most3 Newton or38 CG iterations per step, never the configured cap, with no MuJoCo warnings. Tightening tolerance and increasing the iteration limit do not remove the reversal. Insufficient iteration budget alone is not supported as the explanation.

Candidate37's original-setting normal impulse drops from.06802 at .0025s to.01781 at the finest step; first contact shifts .04000 to.03566s. Candidate5's impulse remains about.03196/.03199. This suggests stronger contact-discretization sensitivity for37, without unique causal proof or local intervention.

Finest winner/runner-up margins are.507–.539, but last-two all-candidate maximum cost changes remain about.101 and cross-setting spread about.115. Report stable winner/miss over the tested grid, not full cost convergence, error certification or physical optimality.

Retain as a numerical counterexample, not standalone novelty. A subsequent bounded test could compare local contact-stage refinement against uniform medium resolution, top32 and equal-budget refinement, including total overhead, then check new samples. Do not tailor an algorithm only to148.
'''
    (ROOT/'report'/'PUSH_T_BATCH148_AUDIT_REPORT.md').write_text(zh,encoding='utf8');(ROOT/'report'/'PUSH_T_BATCH148_AUDIT_REPORT_EN.md').write_text(en,encoding='utf8');print(table);print(raw)
if __name__=='__main__':
    import sys
    {'run':run,'report':report}[sys.argv[1]]()
