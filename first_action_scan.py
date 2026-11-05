"""One-step preview: observation separation versus task recoverability.

Analytic/LP mechanisms, development scan, frozen fixed action, fresh test.
"""
from pathlib import Path
import argparse,csv,hashlib,json,platform
import numpy as np
import scipy
from scipy.optimize import linprog
import preview_identification as base

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'/'first_action_scan'
TEST_SEED=2026110601
TEST_COUNT=128
GRID=sorted(set(round(float(a),6) for a in np.r_[np.linspace(-2,2,81),
    np.linspace(-.15,.15,61),[-.355,.355,-.048,.048,-.041,.041,-.11,.11]]))
OPT={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9}

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,o):p.write_text(json.dumps(o,indent=2),encoding='utf-8')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def lp(c,au=None,bu=None,bounds=None):
    r=linprog(c,A_ub=au,b_ub=bu,bounds=bounds,method='highs',options=OPT)
    if r.status not in (0,2):raise RuntimeError(r.message)
    return r

def prep_admissible(a):
    # Uniform preparation-state bound over initial measurement box and w0.
    radius=np.abs(base.A)@base.NOISE+np.abs(base.B)*base.W
    return bool(abs(a)<=base.LIMIT and np.all(np.abs(base.B*a)+radius<=base.PREP_BOUND+1e-14))

def terminal_map(d):
    # Independent scalar map from initial zero to x3 under (a,b,c).
    return np.array([[.00625,.00375,.00125],[.05,.05,.05]]) if d==0 else np.array([[.00375,.00125,0.],[.05,.05,0.]])

def nominal_constraints(ds):
    au=[];bu=[]
    for d in ds:
        g=terminal_map(d)
        for j in range(2):
            au.extend([g[j],-g[j]])
            bu.extend([base.TARGET[j]+base.TOL[j],-base.TARGET[j]+base.TOL[j]])
    return np.array(au),np.array(bu)

def nominal_interval(ds):
    au,bu=nominal_constraints(ds)
    lo=lp([1.,0,0],au,bu,[(-2,2)]*3)
    hi=lp([-1.,0,0],au,bu,[(-2,2)]*3)
    return [float(lo.fun),float(-hi.fun)] if lo.success and hi.success else None

def nominal_feasible(a,ds):
    au,bu=nominal_constraints(ds)
    r=lp([0.,0.],au[:,1:],bu-au[:,0]*a,[(-2,2)]*2)
    return bool(r.success)

def observation_overlap_limit():
    # Variables a, x0(d0)[2], x0(d1)[2], w0(d0), w0(d1), common y1[2].
    # Common initial measurement is y0=0; each initial state is in its error box.
    au=[];bu=[]
    for d,start,wi in ((0,1,5),(1,3,6)):
        for j in range(2):
            row=np.zeros(9);row[7+j]=1;row[start:start+2]-=base.A[j]
            row[wi]-=base.B[j]
            if d==0:row[0]-=base.B[j]
            au.extend([row,-row]);bu.extend([base.NOISE[j]]*2)
    bounds=[(0,2)]+[(-base.NOISE[j],base.NOISE[j]) for _ in range(2) for j in range(2)]+[(-base.W,base.W)]*2+[(None,None)]*2
    c=np.zeros(9);c[0]=-1
    r=lp(c,np.array(au),np.array(bu),bounds)
    assert r.success
    return {'max_overlapping_positive_action':float(r.x[0]),'witness':r.x.tolist(),
            'max_constraint_residual':float(np.max(np.array(au)@r.x-np.array(bu)))}

def hindsight_feasible(x1,a,d,w1,w2):
    # Diagnostic only: true state/delay AND actual future disturbances supplied.
    # Feasibility is optimistic/clairvoyant, not implementable robust control.
    c,gs,_=base.lifted(np.array(x1),[a],d,2)
    offset=c[-1]+base.A@base.B*w1+base.B*w2
    g=gs[-1];au=np.vstack([g,-g]);bu=np.r_[base.TARGET+base.TOL-offset,-base.TARGET+base.TOL+offset]
    r=lp([0.,0.],au,bu,[(-2,2)]*2)
    return bool(r.success)

def current_robust_feasible(y1,a,d):
    # Sufficient open-loop certificate under the SAME conservative error product.
    c,gs,rad=base.lifted(np.array(y1),[a],d,2)
    g=gs[-1];offset=c[-1];radius=rad[-1]
    r=lp([0.,0.],np.vstack([g,-g]),np.r_[base.TARGET+base.TOL-offset-radius,
         -base.TARGET+base.TOL+offset-radius],[(-2,2)]*2)
    return bool(r.success)

def run(a,d,w,errors):
    x=np.zeros(2);ys=[x+errors[0]];history=[];candidates=[0,1];rows=[]
    x1=None;hindsight=None;robust=None;first_candidates=None
    for k in range(3):
        candidates=[c for c in candidates if base.candidate_feasible(ys,history,c)]
        if d not in candidates:raise RuntimeError('True delay excluded')
        if k==0:u=float(a);info={'terminal_slack':None}
        else:
            if k==1:
                x1=x.copy();first_candidates=candidates.copy()
                hindsight=hindsight_feasible(x,a,d,w[1],w[2])
                robust=current_robust_feasible(ys[-1],a,d)
            u,info=base.plan(ys[-1],history,candidates,3-k,0)
        applied=u if d==0 else (history[-1] if history else 0.)
        nxt=base.A@x+base.B*(applied+w[k])
        rows.append([k,*x,*ys[-1],u,applied,w[k],';'.join(map(str,candidates)),info['terminal_slack'],*nxt])
        history.append(u);x=nxt;ys.append(x+errors[k+1])
    error=np.abs(x-base.TARGET)
    prep_ok=bool(np.all(np.abs(x1)<=base.PREP_BOUND+1e-10))
    success=bool(prep_ok and np.all(error<=base.TOL+1e-10))
    # Tiny solver threshold effects retained separately; a successful trajectory
    # must itself be a witness of hindsight feasibility up to numerical tolerance.
    if success and not hindsight:raise RuntimeError('Success contradicts hindsight LP')
    return {'action':float(a),'true_delay':d,'identified_after_first':len(first_candidates)==1,
        'first_candidates':first_candidates,'hindsight_feasible':hindsight,'current_robust_known_delay_feasible':robust,
        'success':success,'prep_ok':prep_ok,'position_error_m':float(error[0]),'velocity_error_m_s':float(error[1]),
        'task_start_state':x1.tolist(),'task_start_pending_command':float(a),
        'prep_energy':float(base.DT*a*a),'final_position_m':float(x[0]),'final_velocity_m_s':float(x[1])},rows

def batch(folder,records,rules):
    folder.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(folder/'paired_inputs.npz',names=np.array([r[0] for r in records]),
        disturbances=np.array([r[1][:3] for r in records]),measurement_errors=np.array([r[2][:4] for r in records]))
    metrics=[]
    with (folder/'trajectories.csv').open('w',newline='') as f:
        wr=csv.writer(f);wr.writerow(['rule','case','true_delay','k','p','v','measured_p','measured_v',
            'command','applied','disturbance','candidates','terminal_slack','next_p','next_v'])
        for index,(name,action) in enumerate(rules):
            for case,w,errors in records:
                # The task-only first action uses only y0, independent of delay.
                a=base.plan(errors[0],[],[0,1],3,1)[0] if action is None else action
                for d in (0,1):
                    m,rows=run(a,d,w,errors);m.update(rule=name,case=case);metrics.append(m)
                    wr.writerows([[name,case,d,*row] for row in rows])
            if (index+1)%15==0:print(f'{folder.name}: {index+1}/{len(rules)} actions/rules',flush=True)
    write(folder/'episodes.json',metrics)
    groups=[]
    for name,_ in rules:
        group=[m for m in metrics if m['rule']==name]
        groups.append({'rule':name,'action_mean':float(np.mean([m['action'] for m in group])),
            'episodes':len(group),'success_count':sum(m['success'] for m in group),
            'identified_count':sum(m['identified_after_first'] for m in group),
            'hindsight_feasible_count':sum(m['hindsight_feasible'] for m in group),
            'robust_known_delay_feasible_count':sum(m['current_robust_known_delay_feasible'] for m in group),
            'hindsight_infeasible_failure_count':sum(not m['success'] and not m['hindsight_feasible'] for m in group),
            'hindsight_feasible_controller_failure_count':sum(not m['success'] and m['hindsight_feasible'] for m in group),
            'mean_prep_energy':float(np.mean([m['prep_energy'] for m in group])),
            'prep_failure_count':sum(not m['prep_ok'] for m in group)})
    write(folder/'summary.json',groups)
    return groups

def scan():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'scan'/'summary.json').exists():raise RuntimeError('Preserve completed scan')
    config={'grid':GRID,'test_seed':TEST_SEED,'test_count':TEST_COUNT,
        'source_sha256':digest(__file__),'dependencies':{p:digest(ROOT/p) for p in ('preview_identification.py','task_ambiguity_scenarios.py')},
        'selection':'Among prep-admissible uniformly separating, both-delay nominally viable grid actions: most development successes, then lowest squared first-action energy, then positive sign.',
        'versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}}
    write(OUT/'config.json',config)
    overlap=observation_overlap_limit()
    # d=1 invariant: p3-.025*v3=p0+.125*v0+.0025*a+.005*w0+.0025*w1.
    allowed=base.TOL[0]+.025*base.TOL[1]
    uncertain=base.NOISE[0]+.125*base.NOISE[1]+.0075*base.W
    necessary=(allowed-uncertain)/.0025
    analytic={'uniform_observation_overlap':overlap,'discrimination_threshold':2*base.W+4*base.NOISE[1]/base.DT,
        'nominal_known_delay_intervals':{str(d):nominal_interval([d]) for d in (0,1)},
        'nominal_both_delays_interval':nominal_interval([0,1]),
        'note_common_interval':'This is the common OPEN-LOOP (a,b,c) set, not intersection of model-specific action projections.',
        'delay1_robust_all_policy_necessary_abs_action_bound':float(necessary),
        'delay1_exact_initial_zero_necessary_abs_action_bound':float((allowed-.0075*base.W)/.0025),
        'nominal_delay1_abs_action_bound':float(allowed/.0025)}
    write(OUT/'analytic.json',analytic)
    regions=[]
    for a in GRID:
        prep=prep_admissible(a);known=[nominal_feasible(a,[d]) for d in (0,1)]
        ident=bool(abs(a)>analytic['discrimination_threshold']+1e-12)
        viable=all(known)
        label=('both_nominal' if ident and viable else 'identify_only' if ident else 'nominal_task_only' if viable else 'neither') if prep else 'prep_inadmissible'
        regions.append({'action':a,'prep_admissible':prep,'uniform_first_observation_separation':ident,
            'nominal_known_delay_feasible':known,'both_model_specific_nominal_feasible':viable,
            'common_nominal_open_loop':nominal_feasible(a,[0,1]),'region':label})
    write(OUT/'regions.json',regions)
    rules=[(f'a_{r["action"]:+.6f}',r['action']) for r in regions if r['prep_admissible']]
    batch(OUT/'scan',base.cases(),rules)
    print(f'Scanned {len(rules)} admissible actions; unsafe points analytic-only.',flush=True)

def freeze():
    if (OUT/'frozen_rule.json').exists():raise RuntimeError('Rule already frozen')
    config=read(OUT/'config.json');assert config['source_sha256']==digest(__file__)
    regions=read(OUT/'regions.json');groups=read(OUT/'scan'/'summary.json')
    eligible=[r for r in regions if r['region']=='both_nominal']
    candidates=[]
    for r in eligible:
        group=next(g for g in groups if g['rule']==f'a_{r["action"]:+.6f}')
        candidates.append({'action':r['action'],'success_count':group['success_count'],'episodes':group['episodes'],
                           'prep_energy':base.DT*r['action']**2})
    best=min(candidates,key=lambda c:(-c['success_count'],round(c['prep_energy'],12),-c['action']))
    frozen={'selected':best,'eligible':candidates,'source_sha256':digest(__file__),
        'config_sha256':digest(OUT/'config.json'),'scan_episodes_sha256':digest(OUT/'scan'/'episodes.json'),
        'test_inputs_not_generated':not (OUT/'test'/'paired_inputs.npz').exists()}
    write(OUT/'frozen_rule.json',frozen);print(json.dumps(best,indent=2))

def new_records(seed=TEST_SEED,count=TEST_COUNT):
    rng=np.random.default_rng(seed);records=[]
    for i in range(count):
        w=[rng.uniform(-base.W,base.W)]
        for _ in range(2):w.append(float(np.clip(w[-1]+rng.uniform(-base.RATE,base.RATE),-base.W,base.W)))
        errors=rng.uniform(-1,1,(4,2))*base.NOISE
        records.append((f'fresh_{i:03d}',np.array(w),errors))
    return records

def test():
    frozen=read(OUT/'frozen_rule.json');config=read(OUT/'config.json')
    assert frozen['source_sha256']==digest(__file__) and frozen['config_sha256']==digest(OUT/'config.json')
    assert frozen['scan_episodes_sha256']==digest(OUT/'scan'/'episodes.json') and frozen['test_inputs_not_generated']
    for p,h in config['dependencies'].items():assert digest(ROOT/p)==h
    if (OUT/'test'/'summary.json').exists():raise RuntimeError('Preserve completed test')
    rules=[('zero',0.),('task_only',None),('fixed_0.1',.1),('frozen_selected',frozen['selected']['action'])]
    batch(OUT/'test',new_records(),rules)
    write(OUT/'test'/'provenance.json',{'frozen_sha256':digest(OUT/'frozen_rule.json'),
         'test_inputs_sha256':digest(OUT/'test'/'paired_inputs.npz'),'test_episodes_sha256':digest(OUT/'test'/'episodes.json')})
    print('Fresh test complete.',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('scan','freeze','test'))
    phase=parser.parse_args().phase
    {'scan':scan,'freeze':freeze,'test':test}[phase]()
