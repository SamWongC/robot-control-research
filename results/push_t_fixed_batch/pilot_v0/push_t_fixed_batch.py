"""Fixed candidate Push-T-style evaluation. Not an Oxford controller reproduction.
CPU reference uses MuJoCo native batched rollout; heuristics have NO certificate.
"""
from pathlib import Path
import argparse,csv,hashlib,json,os,platform,subprocess,time
import numpy as np
import mujoco
from mujoco import rollout

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'/'push_t_fixed_batch'
H=20; K=64; STAGE=.05; FINE=.0025; COARSE=.01; THREADS=8
XML='''<mujoco model="planar_push_t">
<option timestep="0.0025" gravity="0 0 0" integrator="implicitfast" solver="Newton" iterations="50" tolerance="1e-10" cone="elliptic"/>
<default><geom friction=".6 .005 .0001" solref=".05 1" solimp=".9 .95 .001"/><joint limited="false"/></default>
<worldbody><light pos="0 0 2"/><camera name="top" pos="0 0 1.2"/>
<geom name="floor_visual" type="plane" size=".5 .5 .01" contype="0" conaffinity="0" rgba=".9 .9 .9 1"/>
<body name="object" pos="0 0 .025">
<joint name="ox" type="slide" axis="1 0 0" damping=".6" frictionloss=".03"/>
<joint name="oy" type="slide" axis="0 1 0" damping=".6" frictionloss=".03"/>
<joint name="yaw" type="hinge" axis="0 0 1" damping=".002" frictionloss=".0003"/>
<geom name="bar" type="box" pos="0 .055 0" size=".06 .015 .02" mass=".12" rgba=".2 .4 .8 1"/>
<geom name="stem" type="box" pos="0 -.015 0" size=".015 .055 .02" mass=".08" rgba=".2 .4 .8 1"/>
</body>
<body name="pusher" pos="0 0 .025"><joint name="px" type="slide" axis="1 0 0" damping="1"/><joint name="py" type="slide" axis="0 1 0" damping="1"/>
<geom name="finger" type="cylinder" size=".015 .02" mass=".3" rgba=".8 .2 .2 1"/>
<site name="touch_site" type="cylinder" size=".016 .023" rgba="0 0 0 0"/>
</body></worldbody>
<actuator><velocity joint="px" kv="40" ctrllimited="true" ctrlrange="-.25 .25"/><velocity joint="py" kv="40" ctrllimited="true" ctrlrange="-.25 .25"/></actuator>
<sensor><touch name="touch" site="touch_site"/></sensor>
</mujoco>'''

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path,obj):Path(path).write_text(json.dumps(obj,indent=2),encoding='utf8')

def model(dt=FINE):
    m=mujoco.MjModel.from_xml_string(XML);m.opt.timestep=dt;return m

def freeze():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'frozen_batches.npz').exists():raise RuntimeError('Frozen fixture already exists; refusing overwrite')
    rng=np.random.default_rng(2026110901)
    qs=[];goals=[];controls=[];labels=[]
    regimes=[('approach',[-.13,.055]),('near_contact',[-.077,.055]),('stem',[0,-.09]),('corner',[.079,.075])]
    for split in ['development','test']:
      for family,local in regimes:
       for repeat in range(2):
        theta=rng.uniform(-.35,.35);origin=rng.uniform(-.025,.025,2)
        rot=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
        p=origin+rot@(np.array(local)+rng.uniform(-.001,.001,2))
        q=np.r_[origin,theta,p]
        goal=np.r_[origin+rng.uniform([.06,.03],[.13,.10]),theta+rng.uniform(-.7,.7)]
        ctrl=np.zeros((K,H,2));toward=origin+rot@np.array([0.,.025])-p
        direction=np.arctan2(toward[1],toward[0])
        for i in range(1,K):
          angles=direction+rng.normal(0,.9,4)
          if i%4==0:angles[2:]+=np.pi/1.5
          speeds=rng.uniform(.04,.22,4)
          knots=np.c_[np.cos(angles),np.sin(angles)]*speeds[:,None]
          for j in range(2):ctrl[i,:,j]=np.interp(np.linspace(0,3,H),np.arange(4),knots[:,j])
        ctrl[1]=toward/np.linalg.norm(toward)*.14
        qs.append(q);goals.append(goal);controls.append(ctrl);labels.append(dict(split=split,family=family,repeat=repeat))
    np.savez_compressed(OUT/'frozen_batches.npz',qpos=qs,qvel=np.zeros((len(qs),5)),goals=goals,controls=controls)
    (OUT/'model.xml').write_text(XML,encoding='utf8')
    dump(OUT/'manifest.json',dict(seed=2026110901,batches=len(qs),candidates=K,stages=H,stage_seconds=STAGE,
         horizon_seconds=H*STAGE,fine_step=FINE,coarse_step=COARSE,cpu_threads=THREADS,labels=labels,
         source_sha256=sha(__file__),fixture_sha256=sha(OUT/'frozen_batches.npz'),model_sha256=sha(OUT/'model.xml'),
         scope='Constructed planar dynamics, no robot arm or floor contact: joint damping/friction approximate planar drag. No obstacles. Not exact Oxford/standard Push-T reproduction.'))
    print('Frozen',len(qs),'batches',flush=True)

def initial(q,v,n=K):return np.repeat(np.r_[0.,q,v][None,:],n,axis=0)

def costs(states,u,goal):
    # States are sampled at identical control-stage endpoints for every timestep.
    pose=states[:,:,1:4]; e=pose-goal; e[:,:,2]=np.arctan2(np.sin(e[:,:,2]),np.cos(e[:,:,2]))
    dist=np.sum(e[:,:,:2]**2,axis=2)*100+e[:,:,2]**2*.2
    effort=np.sum(u*u,axis=(1,2))*.001*STAGE
    return STAGE*np.sum(dist,axis=1)+5*dist[:,-1]+effort

def gap(q):
    # Circle-to-union-of-two-oriented-rectangles; used only as a heuristic.
    delta=q[...,3:5]-q[...,:2];c=np.cos(q[...,2]);s=np.sin(q[...,2])
    local=np.stack([c*delta[...,0]+s*delta[...,1],-s*delta[...,0]+c*delta[...,1]],axis=-1)
    ds=[]
    for center,half in [(np.array([0,.055]),np.array([.06,.015])),(np.array([0,-.015]),np.array([.015,.055]))]:
        z=np.abs(local-center)-half
        ds.append(np.linalg.norm(np.maximum(z,0),axis=-1)+np.minimum(np.max(z,axis=-1),0)-.015)
    return np.minimum(*ds)

class Evaluator:
    def __init__(self):
        self.models={dt:model(dt) for dt in [FINE,COARSE,FINE/2]}
        self.runners={n:rollout.Rollout(nthread=n) for n in [1,THREADS]}
        self.data={(dt,n):[mujoco.MjData(m) for _ in range(n)] for dt,m in self.models.items() for n in [1,THREADS]}
    def close(self):
        for runner in self.runners.values():runner.close()
    def evaluate(self,init,u,goal,dt=FINE,n=THREADS):
        t=time.perf_counter(); sub=round(STAGE/dt);control=np.ascontiguousarray(np.repeat(u,sub,axis=1))
        prep=time.perf_counter()-t;t=time.perf_counter()
        raw,sensor=self.runners[n].rollout(self.models[dt],self.data[dt,n],init,control)
        physics=time.perf_counter()-t;t=time.perf_counter()
        if not np.isfinite(raw).all() or np.any(np.diff(np.c_[init[:,0],raw[:,:,0]],axis=1)<=0):raise RuntimeError('Divergent rollout')
        states=raw[:,sub-1::sub,:]
        active=(sensor[:,:,0].reshape(len(u),u.shape[1],sub).max(axis=2)>1e-5)
        scores=costs(states,u,goal);post=time.perf_counter()-t
        return scores,states,active,dict(preparation=prep,physics=physics,cost_and_checks=post,steps=len(u)*u.shape[1]*sub)
    def mixed(self,init,u,goal,mask):
        state=init.copy();allstates=[];active=[];steps=0
        for k in range(H):
            out=state.copy();touch=np.zeros(len(u),bool)
            for flag,dt in [(True,FINE),(False,COARSE)]:
                ids=np.flatnonzero(mask[:,k]==flag)
                if len(ids)==0:continue
                _,ss,aa,meta=self.evaluate(state[ids],u[ids,k:k+1],goal,dt)
                out[ids]=ss[:,-1];touch[ids]=aa[:,0];steps+=meta['steps']
            state=out;allstates.append(state.copy());active.append(touch)
        ss=np.stack(allstates,axis=1)
        return costs(ss,u,goal),ss,np.stack(active,axis=1),steps

def load():
    man=json.loads((OUT/'manifest.json').read_text());assert sha(OUT/'frozen_batches.npz')==man['fixture_sha256']
    return np.load(OUT/'frozen_batches.npz'),man

def run_cpu():
    f,man=load();ev=Evaluator();NB=len(f['qpos']);refs=[];states=[];events=[];coarses=[];old=[]
    build=[]
    try:
      for b in range(NB):
        init=initial(f['qpos'][b],f['qvel'][b]);u=f['controls'][b];goal=f['goals'][b]
        r,ss,aa,meta=ev.evaluate(init,u,goal);refs.append(r);states.append(ss);events.append(aa)
        coarse=ev.evaluate(init,u,goal,COARSE)[0];coarses.append(coarse)
        oldinit=init.copy();oldinit[:,1]+=.003;oldinit[:,3]+=.02
        old.append(ev.evaluate(oldinit,u,goal)[0])
        finer=ev.evaluate(init,u,goal,FINE/2)[0]
        build.append(dict(batch=b,halfstep_max_error=float(np.max(np.abs(finer-r))),halfstep_regret=float(finer[np.argmin(r)]-np.min(finer)),fine_best=int(np.argmin(r)),halfstep_best=int(np.argmin(finer))))
        print('reference',b,flush=True)
      refs=np.array(refs);coarses=np.array(coarses);old=np.array(old)
      np.savez_compressed(OUT/'reference.npz',costs=refs,states=states,contact=events,coarse_costs=coarses,nearby_cache_costs=old)
      # This max error is empirical calibration, NOT a verified or probabilistic bound.
      dev=[b for b,x in enumerate(man['labels']) if x['split']=='development']
      bias=float(np.max(np.abs(refs[dev]-coarses[dev])))
      dump(OUT/'frozen_calibration.json',dict(development_indices=dev,empirical_cost_error=bias,
          development_only=True,not_a_certificate=True,top_count=8,gap_threshold=.008,reference_checks=build))
      timing=[];quality=[];diagnostics=[]
      methods=['fine_serial','fine_cpu8','coarse_cpu8','coarse_top8','coarse_empirical_interval','contact_segment','fixed_segment','cached_proposal']
      rng=np.random.default_rng(2026110902)
      # Warm all thread pools/models before timing. Timings include allocations/costs/checks.
      for b in range(NB):
        init=initial(f['qpos'][b],f['qvel'][b]);u=f['controls'][b];goal=f['goals'][b]
        for rep in range(3):
          for method in rng.permutation(methods):
            start=time.perf_counter();details={};steps=0;refined=0;estimate=None
            if method.startswith('fine_'):
              estimate,ss,aa,details=ev.evaluate(init,u,goal,FINE,1 if method=='fine_serial' else THREADS)
              chosen=int(np.argmin(estimate));steps=details['steps']
            elif method=='cached_proposal':
              # Cache built offline at a displaced state with IDENTICAL controls.
              chosen=int(np.argmin(old[b]));cached=float(old[b,chosen]);
              estimate,ss,aa,details=ev.evaluate(init[chosen:chosen+1],u[chosen:chosen+1],goal)
              steps=details['steps'];refined=1;estimate=None
            else:
              coarse,cs,ca,cm=ev.evaluate(init,u,goal,COARSE);steps=cm['steps'];estimate=coarse
              if method=='coarse_cpu8':chosen=int(np.argmin(coarse))
              elif method in ['coarse_top8','coarse_empirical_interval']:
                ids=(np.argsort(coarse)[:8] if method=='coarse_top8' else np.flatnonzero(coarse<=np.min(coarse)+2*bias))
                vals,_,_,fm=ev.evaluate(init[ids],u[ids],goal);steps+=fm['steps'];refined=len(ids)
                chosen=int(ids[np.argmin(vals)]);estimate=None
              else:
                if method=='contact_segment':
                  near=gap(cs[:,:,1:6])<.008
                  flag=near|ca
                  # Dilate one segment each way, based only on coarse results.
                  mask=flag.copy();mask[:,1:]|=flag[:,:-1];mask[:,:-1]|=flag[:,1:]
                else:mask=np.broadcast_to((np.arange(H)%2==0),(K,H)).copy()
                estimate,ss,aa,count=ev.mixed(init,u,goal,mask);steps+=count;refined=int(mask.sum())
                chosen=int(np.argmin(estimate))
            elapsed=time.perf_counter()-start
            timing.append(dict(batch=b,split=man['labels'][b]['split'],method=str(method),repeat=rep,total_seconds=elapsed,steps=steps,refined=refined,**{k:v for k,v in details.items() if k!='steps'}))
            if rep==0:
              quality.append(dict(batch=b,split=man['labels'][b]['split'],family=man['labels'][b]['family'],method=str(method),chosen=chosen,
                  reference_best=int(np.argmin(refs[b])),regret=float(refs[b,chosen]-refs[b].min()),
                  exact_winner=bool(chosen==np.argmin(refs[b])),max_cost_error=(float(np.max(np.abs(estimate-refs[b]))) if estimate is not None and len(estimate)==K else None)))
        # Inspect true-reference event association, strictly retrospective, not used by heuristics.
        changes=np.zeros_like(events[b]);changes[:,0]=events[b][:,0];changes[:,1:]=events[b][:,1:]!=events[b][:,:-1]
        _,cs,ca,_=ev.evaluate(init,u,goal,COARSE)
        # State error at each aligned boundary; increments are not additive causal error attribution.
        err=np.linalg.norm(np.array(states[b])[:,:,1:4]-cs[:,:,1:4],axis=2)
        win=changes.copy();win[:,1:]|=changes[:,:-1];win[:,:-1]|=changes[:,1:]
        positive=np.maximum(np.diff(np.c_[np.zeros(K),err],axis=1),0)
        diagnostics.append(dict(batch=b,event_window_fraction=float(win.mean()),positive_error_growth_in_event_windows=float(positive[win].sum()/max(positive.sum(),1e-15)),
          contact_stage_fraction=float(np.mean(events[b])),contact_mismatch_fraction=float(np.mean(ca!=events[b])),coarse_error=float(np.max(np.abs(refs[b]-coarses[b])))))
        print('benchmarked',b,flush=True)
      dump(OUT/'cpu_quality.json',quality);dump(OUT/'cpu_timings.json',timing);dump(OUT/'event_diagnostics.json',diagnostics)
      # Native timers: profiling only; Python callback affects timing, not throughput records above.
      m=model();d=mujoco.MjData(m);mujoco.set_mjcb_time(time.perf_counter)
      try:
        b=8;d.qpos[:]=f['qpos'][b];d.qvel[:]=0
        for k in range(H):
          d.ctrl[:]=f['controls'][b,1,k]
          for _ in range(round(STAGE/FINE)):mujoco.mj_step(m,d)
        timers={name:dict(seconds=float(d.timer[int(value)].duration),calls=int(d.timer[int(value)].number)) for name,value in mujoco.mjtTimer.__members__.items() if name!='mjNTIMER'}
        dump(OUT/'native_profile.json',dict(batch=b,candidate=1,timers=timers,scope='Instrumented single trajectory, timers overlap; callback perturbs runtime. Not aggregate benchmark shares.'))
      finally:mujoco.set_mjcb_time(None)
      metadata=dict(python=platform.python_version(),platform=platform.platform(),logical_cpus=os.cpu_count(),mujoco=mujoco.__version__,numpy=np.__version__,source_sha256=sha(__file__),gpu_info=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader'],text=True).strip())
      dump(OUT/'environment.json',metadata)
    finally:ev.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','cpu']);args=p.parse_args()
    freeze() if args.action=='freeze' else run_cpu()
