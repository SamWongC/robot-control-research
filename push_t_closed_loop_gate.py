"""Bounded closed-loop task-meaning gate; no real-time or physical-truth claim."""
from pathlib import Path
import json, time, hashlib, argparse
import numpy as np
import mujoco
from mujoco import rollout
from push_t_fixed_batch import model, costs, initial, H, K, STAGE, XML

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'/'push_t_closed_loop_gate'
METHODS=['low','medium','high','top32']
def save(p,x): p.write_text(json.dumps(x,indent=2),encoding='utf8')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def candidates(q,goal,previous,seed,k):
    rng=np.random.default_rng([seed,k]); u=np.zeros((K,H,2))
    shifted=np.concatenate([previous[1:],previous[-1:]])
    u[1]=shifted
    # Goal-directed constant proposals plus smooth warm-start perturbations.
    direction=goal[:2]-q[:2]; direction/=max(np.linalg.norm(direction),1e-9)
    for i in range(2,10):
        angle=(i-5.5)*.25; c,s=np.cos(angle),np.sin(angle)
        u[i]=np.array([[c,-s],[s,c]])@direction*.12
    toward=q[:2]+np.array([-np.sin(q[2]),np.cos(q[2])])*.025-q[3:5]
    toward/=max(np.linalg.norm(toward),1e-9)
    for i in range(10,K):
        base=shifted if i<42 else np.tile(toward*.12,(H,1))
        knots=rng.normal(0,.055 if i<42 else .10,(4,2))
        noise=np.stack([np.interp(np.linspace(0,3,H),np.arange(4),knots[:,j]) for j in range(2)],1)
        u[i]=np.clip(base+noise,-.25,.25)
    return u

class Engine:
    def __init__(self):
        self.runner=rollout.Rollout(nthread=8)
        self.models={dt:model(dt) for dt in [.01,.0025,.00125,.000625]}
        self.data={dt:[mujoco.MjData(m) for _ in range(8)] for dt,m in self.models.items()}
    def evaluate(self,q,v,u,g,dt):
        n=round(STAGE/dt)
        raw,_=self.runner.rollout(self.models[dt],self.data[dt],initial(q,v,len(u)),np.ascontiguousarray(np.repeat(u,n,axis=1)))
        assert np.isfinite(raw).all()
        return costs(raw[:,n-1::n,:],u,g)
    def episode(self,case,method,dt):
        m=model(dt); d=mujoco.MjData(m);d.qpos[:]=case['q']; mujoco.mj_forward(m,d)
        previous=np.zeros((H,2));hold=0; trace=[];lat=[]; success=False;escaped=False
        for k in range(200):
            start=time.perf_counter();u=candidates(d.qpos,case['goal'],previous,case['seed'],k)
            if method=='top32':
                coarse=self.evaluate(d.qpos,d.qvel,u,case['goal'],.01)
                ids=np.argsort(coarse,kind='stable')[:32]
                scores=self.evaluate(d.qpos,d.qvel,u[ids],case['goal'],.000625)
                chosen=int(ids[np.argmin(scores)])
            else:
                scores=self.evaluate(d.qpos,d.qvel,u,case['goal'],{'low':.0025,'medium':.00125,'high':.000625}[method])
                chosen=int(np.argmin(scores))
            previous=u[chosen].copy();lat.append(time.perf_counter()-start)
            d.ctrl[:]=previous[0]
            for _ in range(round(STAGE/dt)):mujoco.mj_step(m,d)
            assert np.isfinite(d.qpos).all() and np.isfinite(d.qvel).all()
            err=np.linalg.norm(d.qpos[:2]-case['goal'][:2]);angle=abs(np.arctan2(np.sin(d.qpos[2]-case['goal'][2]),np.cos(d.qpos[2]-case['goal'][2])))
            hold=hold+1 if err<=.02 and angle<=np.deg2rad(10) else 0
            trace.append([*d.qpos,*d.qvel,*d.ctrl,err,angle,chosen])
            escaped=bool(np.any(np.abs(d.qpos[[0,1,3,4]])>.5))
            if hold>=10:success=True;break
            if escaped:break
        return dict(success=success,escaped=escaped,steps=k+1,duration=(k+1)*STAGE,position_error=float(err),angle_error=float(angle),latency_ms=(np.array(lat)*1000).tolist()),np.array(trace)
    def close(self):self.runner.close()

def freeze():
    if OUT.exists():raise RuntimeError('Refusing overwrite')
    OUT.mkdir(parents=True)
    rng=np.random.default_rng(2026110507); cases=[]
    for split,count in [('development',4),('confirmation',16)]:
      for family,p in [('approach',[-.13,.055]),('near_contact',[-.077,.055]),('stem',[0,-.09]),('corner',[.079,.075])]:
       for j in range(count):
        theta=rng.uniform(-.25,.25);r=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
        xy=rng.uniform(-.02,.02,2);q=np.r_[xy,theta,xy+r@(np.array(p)+rng.uniform(-.001,.001,2))]
        goal=np.r_[xy+rng.uniform([.06,.03],[.13,.10]),theta+rng.uniform(-.5,.5)]
        cases.append(dict(id=len(cases),split=split,family=family,q=q.tolist(),goal=goal.tolist(),seed=int(rng.integers(1,2**31))))
    save(OUT/'cases.json',cases)
    save(OUT/'protocol.json',dict(source_sha=digest(Path(__file__)),base_sha=digest(ROOT/'push_t_fixed_batch.py'),cases_sha=digest(OUT/'cases.json'),development_gate='at least 12/16 successes with high; otherwise no confirmatory comparison',execution_dt=.0003125,sensitivity_dt=.00015625,success_position_m=.02,success_angle_deg=10,hold_seconds=.5,episode_seconds=10,workspace_abs_m=.5,candidates=64,horizon_seconds=1,control_period_seconds=.05,mode='ideal instantaneous planning; latency measured but not injected',scope='synthetic planar drag model; no hardware, obstacles, physical calibration or novelty claim'))
    (OUT/'execution_source.py.txt').write_bytes(Path(__file__).read_bytes())
    (OUT/'model.xml').write_text(XML)

def run():
    if not OUT.exists():freeze()
    cases=json.loads((OUT/'cases.json').read_text());e=Engine()
    try:
      # Warm-up excluded from timing; all model paths exercised.
      q=np.array(cases[0]['q']);g=np.array(cases[0]['goal']);u=candidates(q,g,np.zeros((H,2)),1,0)
      for dt in e.models:e.evaluate(q,np.zeros(5),u,g,dt)
      jobs=[(c,'high',.0003125,'dev') for c in cases if c['split']=='development']
      execute(e,jobs)
      dev=[json.loads((OUT/f"dev_{c['id']}_high.json").read_text()) for c in cases if c['split']=='development']
      passed=sum(x['success'] for x in dev)>=12
      save(OUT/'gate.json',dict(passed=passed,successes=sum(x['success'] for x in dev),total=16))
      # Matched half-step check for all four families, before interpreting success.
      execute(e,[(cases[i],'high',.00015625,'sensitivity') for i in [0,4,8,12]])
      if passed:
        jobs=[];rng=np.random.default_rng(2026110508)
        for c in cases:
          if c['split']=='confirmation':
            for method in rng.permutation(METHODS): jobs.append((c,str(method),.0003125,'confirm'))
        execute(e,jobs)
    finally:e.close()
def execute(e,jobs):
    for c,method,dt,phase in jobs:
        p=OUT/f"{phase}_{c['id']}_{method}.json"
        if p.exists():continue
        result,trace=e.episode(c,method,dt);result.update(case=c['id'],family=c['family'],method=method,execution_dt=dt)
        np.savez_compressed(p.with_suffix('.npz'),trace=trace)
        save(p,result);print(phase,c['id'],method,result['success'],round(result['position_error'],4),flush=True)
if __name__=='__main__':run()
