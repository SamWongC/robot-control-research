"""Bounded execution feasibility: contiguous runs, prefix reuse, causal one-pass."""
from pathlib import Path
import json,time
import numpy as np
import push_t_fixed_batch as b
import push_t_local_refinement as prev
ROOT=Path(__file__).resolve().parent;O=ROOT/'results'/'push_t_execution_gate';OLD=ROOT/'results'/'push_t_confirmation'
IDS=list(range(0,256,4));METHODS=['stage_two_pass','contiguous','prefix_reuse','online_one_pass','uniform_medium','uniform_high']
def dump(n,x):(O/n).write_text(json.dumps(x,indent=2),encoding='utf8')
def segments(ev,init,u,g,mask,pilot=None):
    state=init.copy();out=np.zeros((64,20,11));starts=np.zeros(64,int);calls=0;steps=0
    if pilot is not None:
        starts=np.where(mask.any(axis=1),mask.argmax(axis=1),20)
        for i,s in enumerate(starts):
            out[i,:s]=pilot[i,:s]
            if s:state[i]=pilot[i,s-1]
    for k in range(20):
        active=np.flatnonzero(starts==k);groups={}
        for i in active:
            end=k+1
            while end<20 and mask[i,end]==mask[i,k]:end+=1
            groups.setdefault((end,bool(mask[i,k])),[]).append(int(i))
        for (end,flag),items in groups.items():
            ii=np.array(items);dt=prev.HIGH if flag else prev.LOW
            _,ss,_,meta=ev.evaluate(state[ii],u[ii,k:end],g,dt);out[ii,k:end]=ss;state[ii]=ss[:,-1];starts[ii]=end;calls+=1;steps+=meta['steps']
    return b.costs(out,u,g),out,calls,steps
def online(ev,init,u,g):
    state=init.copy();out=[];carry=np.zeros(64,bool);calls=0;steps=0;masks=[]
    for k in range(20):
        # Causal geometric lookahead heuristic, not a certified displacement bound.
        speed=np.linalg.norm(state[:,9:11],axis=1)+np.linalg.norm(state[:,6:8],axis=1)+np.linalg.norm(u[:,k],axis=1)
        flag=(b.gap(state[:,1:6])<.008+.05*speed)|carry;nxt=state.copy();contact=np.zeros(64,bool)
        for fine,dt in [(True,prev.HIGH),(False,prev.LOW)]:
            ii=np.flatnonzero(flag==fine)
            if len(ii):
                _,ss,aa,meta=ev.evaluate(state[ii],u[ii,k:k+1],g,dt);nxt[ii]=ss[:,-1];contact[ii]=aa[:,0];calls+=1;steps+=meta['steps']
        carry=contact;state=nxt;out.append(state.copy());masks.append(flag)
    out=np.stack(out,axis=1);return b.costs(out,u,g),out,calls,steps,np.stack(masks,axis=1)
def run():
    O.mkdir(parents=True,exist_ok=True)
    if (O/'protocol.json').exists():raise RuntimeError('Refuse overwrite')
    dump('protocol.json',dict(date='2026-11-05',batches=IDS,selection='Every fourth frozen batch:16 per family, includes148; exploratory implementation gate, not new independent confirmation',methods=METHODS,repeats=3,source_sha256=b.sha(__file__),base_sha256=b.sha(b.__file__),previous_sha256=b.sha(prev.__file__),fixture_sha256=b.sha(OLD/'fixture.npz'),online_rule='Current gap <8mm+50ms*(pusher speed+object translation speed+command speed), or previous-stage contact. No reference or pilot. Not a safety bound; no angular motion bound.',gate='Actual end-to-end time and quality vs same-run uniform baselines; identical-mask equivalence for contiguous/prefix only'))
    f=np.load(OLD/'fixture.npz');ref=np.load(OLD/'costs.npz')['costs'];oldcost=np.load(ROOT/'results'/'push_t_local_refinement'/'estimates.npz')['costs'];ev=b.Evaluator();prev.add(ev,prev.HIGH)
    quality=[];times=[];masks=[];saved=[];maxerr=0.
    try:
      ini=b.initial(f['qpos'][148],np.zeros(5))
      for dt in [prev.LOW,.00125,prev.HIGH]:ev.evaluate(ini,f['controls'][148],f['goals'][148],dt)
      for batch in IDS:
        init=b.initial(f['qpos'][batch],np.zeros(5));u=f['controls'][batch];g=f['goals'][batch];cache={};allmasks={}
        for repeat in range(3):
          for method in np.random.default_rng(102000+batch*3+repeat).permutation(METHODS):
            start=time.perf_counter();calls=0;steps=0
            if method.startswith('uniform'):
                cost,ss,_,meta=ev.evaluate(init,u,g,.00125 if method=='uniform_medium' else prev.HIGH);calls=1;steps=meta['steps']
            elif method=='online_one_pass':cost,ss,calls,steps,mask=online(ev,init,u,g);allmasks[str(method)]=mask
            else:
                _,ps,pa,meta=ev.evaluate(init,u,g,prev.LOW);mask=prev.mask_from(ps,pa);steps=meta['steps'];calls=1;allmasks[str(method)]=mask
                if method=='stage_two_pass':
                    cost,ss=prev.mixed(ev,init,u,g,mask);calls+=sum(bool(np.any(mask[:,k]==v)) for k in range(20) for v in [False,True]);steps+=int(np.sum(400+60*mask.sum(axis=1)))
                else:
                    cost,ss,nc,ns=segments(ev,init,u,g,mask,ps if method=='prefix_reuse' else None);calls+=nc;steps+=ns
            elapsed=time.perf_counter()-start
            times.append(dict(batch=batch,method=str(method),repeat=repeat,seconds=elapsed,calls=calls,steps=steps))
            if repeat==0:
                cache[str(method)]=cost;chosen=int(cost.argmin());quality.append(dict(batch=batch,method=str(method),chosen=chosen,regret=float(ref[batch,2,chosen]-ref[batch,2].min())))
        for name in ['stage_two_pass','contiguous','prefix_reuse']:
            err=float(np.max(np.abs(cache[name]-oldcost[batch,3])));maxerr=max(maxerr,err);assert err<1e-8
        assert np.allclose(cache['uniform_high'],ref[batch,2],rtol=0,atol=1e-9)
        masks.append([allmasks['stage_two_pass'],allmasks['online_one_pass']]);saved.append([cache[m] for m in METHODS])
        print('completed',batch,flush=True)
    finally:ev.close()
    np.savez_compressed(O/'costs_masks.npz',batch_ids=IDS,costs=saved,masks=masks);dump('quality.json',quality);dump('timings.json',times);dump('audit.json',dict(passed=True,max_same_mask_cost_difference=maxerr,high_reference_reproduced=True,timed_calls=len(times)))
def report():
    q=json.loads((O/'quality.json').read_text());t=json.loads((O/'timings.json').read_text());summary=[]
    for m in METHODS:
        rr=[r for r in q if r['method']==m];tt=[x for x in t if x['method']==m];c=next(r for r in rr if r['batch']==148)
        summary.append(dict(method=m,losses=sum(r['regret']>1e-4 for r in rr),max_regret=max(r['regret'] for r in rr),mean_regret=float(np.mean([r['regret'] for r in rr])),p50_ms=float(np.median([x['seconds']*1000 for x in tt])),p95_ms=float(np.percentile([x['seconds']*1000 for x in tt],95)),mean_calls=float(np.mean([x['calls'] for x in tt])),mean_steps=float(np.mean([x['steps'] for x in tt])),case148_winner=c['chosen'],case148_ms=float(np.median([x['seconds']*1000 for x in tt if x['batch']==148]))))
    dump('summary.json',summary);tab='| Method | Loss /64 | p50 ms | p95 ms | Mean calls | Mean steps | Case148 winner |\n|---|---:|---:|---:|---:|---:|---:|\n'
    for s in summary:tab+=f"| {s['method']} | {s['losses']} | {s['p50_ms']:.2f} | {s['p95_ms']:.2f} | {s['mean_calls']:.1f} | {s['mean_steps']:.0f} | {s['case148_winner']} |\n"
    raw='\n```json\n'+json.dumps(summary,indent=2)+'\n```\n'
    zh='''# 单遍与连续段执行可行性检查（2026-11-05）

固定取已有256批中的每第四批，共64批（每类16，包含148）；这是有界实现检查，非新确认集。每方法每批3次随机顺序，所有计时含必要的预计算、选择、分组和实际积分。阈值1e-4仅用于报告成本损失，参考为0.000625秒全时域结果。

stage_two_pass为上一逐段两遍实现。contiguous保持相同掩码，按每条轨迹相邻同精度段合并，并将具有相同起止时间与精度的轨迹批处理。prefix_reuse进一步直接复用预计算中第一次精细段之前的低精度状态；不复用精细段之后已失效的预计算状态。两者仍需预计算，不能称为单遍。三者输出均与历史同掩码结果核验至1e-8。

online_one_pass没有预计算，每段从当前状态决定精度：几何间隙小于8mm+50ms×(推杆速度+物体平移速度+当前指令速度)，或上一段有接触，则精细；否则低精度。速度采用向量范数；规则不包括角运动的可靠界，不是安全证书。它消除预计算重复积分，但保留按段调用，且改变了加密位置，所以与旧方法质量不保证一致。

uniform_medium为0.00125秒，uniform_high为0.000625秒；局部低步长0.0025秒。所有求解器统一禁用热启动，完整控制段边界一致。
'''+tab+raw+'''
数据results/push_t_execution_gate，代码push_t_execution_gate.py；.venv-contact执行run/report，run拒绝覆盖。成本、掩码、逐次时间、调用数、步数、协议与审计均已保存。历史结果不变。本实验没有实机、闭环安全性或新颖性证据。
'''
    en='''# Single-pass and contiguous-run execution gate (2026-11-05)

Every fourth existing confirmation batch:64 total,16 per family, including148. Bounded implementation check, not fresh confirmation. Three randomized repeats per method/batch; all necessary pilot, selection, grouping and integration costs included. Loss threshold1e-4 is numerical; reference uses uniform .000625s.

Stage-two-pass is the previous implementation. Contiguous merges adjacent same-resolution stages per trajectory, batching identical start/end/resolution groups. Prefix-reuse additionally copies pilot states preceding the first fine stage; never reuses stale states after refinement. Both still require a pilot. All three reproduce historical same-mask costs within1e-8.

Online-one-pass has no pilot: current gap<8mm+50ms*(pusher speed+object translational speed+current command speed), or previous-stage contact, triggers fine resolution. Speeds are vector norms; no sound angular-motion bound or safety guarantee. It eliminates pilot reintegration, retains per-stage dispatch, and changes refinement locations, so output equivalence is not assumed.

Uniform medium/high steps=.00125/.000625; local low=.0025. Warmstart uniformly disabled, same control boundaries.
'''+tab+raw+'''
Artifacts results/push_t_execution_gate; push_t_execution_gate.py run/report in .venv-contact. Run refuses overwrite. Saved costs,masks,timings,calls,steps,protocol,audit. No hardware,closed-loop safety or novelty evidence.
'''
    zh+='''
## 去留结论

单遍确实消除了预计算重复积分：平均81114步，对比全精细102400步减少20.8%，相较原两遍p95从72.14ms降至61.29ms。但全精细p95仅54.63ms，单遍仍慢12.2%；中位耗时也更慢。64批相对精细参考均无选择损失，仅说明这一已查看子集上的一致性，不是完整256批或独立验证结果。

连续段合并没有减少总调用：平均52.2次，对比原逐段40.5次；步数不变，p95反而154.59ms。各轨迹切换边界不同，按相同起止段分组产生更多小批次；这是本调度实现的实测失败，不代表所有原生连续段实现都不可能。前缀复用仅降至49.4次、93671步，p95仍151.44ms，收益不足。

批次148所有方法都选37；统一中等步长26.80ms，单遍56.13ms，全精细53.20ms。因此148已不能作为更复杂实现必要性的证据。统一中等步长在64批仍有4次损失，说明精度/时间取舍存在，但未产生已被当前方法有效填补的缺口。

明确建议：本次可行性检查完成后，暂停以当前Python调度的接触自适应积分为主线追加算法、神经网络或论文包装。现有证据只有数值步数节省和有限样本排名一致，没有端到端速度优势、保证或独立创新。若未来已有原生批处理内核/合作资源，可另立工程任务评估；其投入不属于本轮已证明值得进行的新算法研究。保留代码、负结果和稳定反例，先重新审查真实任务的时限与允许损失，再决定研究方向。
'''
    en+='''
## Go/no-go decision

Single-pass removes the pilot: mean81114 steps versus102400 all-fine,20.8% fewer. Its p95 improves from72.14ms two-pass to61.29ms, but remains12.2% slower than all-fine54.63ms; median is slower too. Zero selection loss on64 inspected batches is not full256-batch or independent validation.

Contiguous grouping increases calls from40.5 to52.2 with unchanged steps; p95 worsens to154.59ms. Different trajectory switch boundaries create additional small batches in this scheduler. This rejects this implementation, not every possible native implementation. Prefix reuse only reaches49.4 calls,93671 steps and151.44ms p95.

All methods recover37 on148: uniform medium26.80ms, single-pass56.13ms, all-fine53.20ms. Thus148 does not establish necessity for the more complex implementation. Medium still loses on4/64 batches, but the present methods do not establish a superior end-to-end tradeoff.

Recommendation: pause further algorithms/networks/paper framing around this Python-scheduled contact-adaptive integration route. Evidence supports fewer steps and finite-sample ranking agreement, not latency advantage, guarantees or standalone novelty. Native batched kernels could be a separate engineering project if resources become available, not an investment justified by this gate. Preserve negative results and counterexamples; reassess real-task deadlines and acceptable loss before choosing the next research direction.
'''
    (ROOT/'report'/'PUSH_T_EXECUTION_GATE_REPORT.md').write_text(zh,encoding='utf8');(ROOT/'report'/'PUSH_T_EXECUTION_GATE_REPORT_EN.md').write_text(en,encoding='utf8');print(tab);print(raw)
if __name__=='__main__':
    import sys
    {'run':run,'report':report}[sys.argv[1]]()
