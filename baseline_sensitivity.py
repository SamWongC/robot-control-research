"""Development -> frozen family selection -> untouched paired test.

Baseline ablations only; no information objective or novelty claim.
"""
from pathlib import Path
from time import perf_counter
import argparse,csv,hashlib,json,platform
import numpy as np
import scipy
from scipy.optimize import linprog
import preview_identification as old

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'/'baseline_sensitivity'
PREVIEWS=(0,1,2,4,8)
TEST_SEED=2026110501
TEST_CASES=64
VARIANTS=[{'name':'legacy','family':'legacy'},
          {'name':'lex_energy','family':'energy'}]
VARIANTS += [{'name':f'track_{w:g}','family':'tracking','weight':w} for w in (.01,.1,1.)]
VARIANTS += [{'name':f'progress_{b:g}','family':'progress','band':b,'weight':.1} for b in (.25,.5,1.)]

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,indent=2),encoding='utf-8')
def read(p):return json.loads(p.read_text(encoding='utf-8'))

def reference(k,total):
    """Hermite trajectory from (p,v)=(0,0) to the original absolute goal."""
    s=k/total;T=total*old.DT;p,v=old.TARGET
    return np.array([p*(3*s*s-2*s**3)+v*T*(s**3-s*s),
                     p*(6*s-6*s*s)/T+v*(3*s*s-2*s)])

def plan(y,history,candidates,h,prep_remaining,variant,total):
    if variant['family']=='legacy':return old.plan(y,history,candidates,h,prep_remaining)
    # Commands, absolute commands, terminal slack, 2h stage-error epigraphs.
    nv=4*h+1;ti=2*h;au=[];bu=[]
    for d in candidates:
        centers,gs,rs=old.lifted(y,history,d,h)
        for i in range(h):
            if i+1<=prep_remaining:
                for j in range(2):
                    for sign in (-1,1):
                        row=np.zeros(nv);row[:h]=sign*gs[i,j]
                        au.append(row);bu.append(old.PREP_BOUND[j]-rs[i,j]-sign*centers[i,j])
            ref=reference(len(history)+i+1,total)
            for j in range(2):
                for sign in (-1,1):
                    row=np.zeros(nv);row[:h]=sign*gs[i,j]/old.PREP_BOUND[j]
                    row[ti+1+2*i+j]=-1
                    band=variant.get('band',0.) if variant['family']=='progress' else 0.
                    au.append(row);bu.append(band-rs[i,j]/old.PREP_BOUND[j]-sign*(centers[i,j]-ref[j])/old.PREP_BOUND[j])
        for j in range(2):
            for sign in (-1,1):
                row=np.zeros(nv);row[:h]=sign*gs[-1,j]/old.TOL[j];row[ti]=-1
                au.append(row);bu.append(1-rs[-1,j]/old.TOL[j]-sign*(centers[-1,j]-old.TARGET[j])/old.TOL[j])
    for i in range(h):
        for sign in (-1,1):
            row=np.zeros(nv);row[i]=sign;row[h+i]=-1
            au.append(row);bu.append(0.)
    bounds=[(-old.LIMIT,old.LIMIT)]*h+[(0,old.LIMIT)]*h+[(0,None)]*(1+2*h)
    primary=np.zeros(nv);primary[ti]=1.
    options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9}
    first=linprog(primary,A_ub=np.array(au),b_ub=np.array(bu),bounds=bounds,method='highs',options=options)
    if first.status==2:return 0.,{'feasible_prep':False,'terminal_slack':None,'certified_plan':False}
    if not first.success:raise RuntimeError(first.message)
    # Lexicographic priority: no more than 1e-7 additional normalized terminal slack.
    row=np.zeros(nv);row[ti]=1;au.append(row);bu.append(first.x[ti]+1e-7)
    secondary=np.zeros(nv)
    secondary[h:2*h]=(1/h if variant['family']=='energy' else 1e-5/h)
    for i in range(h-1): # Endpoint already controlled by the primary objective.
        index=len(history)+i+1
        active=variant['family']=='tracking' or (variant['family']=='progress' and index>=total-4)
        if active:secondary[ti+1+2*i:ti+1+2*i+2]=variant.get('weight',0.)/max(1,2*(h-1))
    result=linprog(secondary,A_ub=np.array(au),b_ub=np.array(bu),bounds=bounds,method='highs',options=options)
    if not result.success:raise RuntimeError(f'Second-stage solver: {result.message}')
    residual=float(np.max(np.array(au)@result.x-np.array(bu)))
    return float(result.x[0]),{'feasible_prep':True,'terminal_slack':float(result.x[ti]),
        'certified_plan':bool(result.x[ti]<=2e-7 and residual<=1e-7),
        'primary_optimal_slack':float(first.x[ti]),'max_lp_residual':residual}

def run(n,variant,policy,d,w,errors):
    x=np.zeros(2);ys=[x+errors[0]];history=[];cand=[0,1];rows=[]
    first_single=None;failures=0;ever=False;energy=0.;pmax=0.;vmax=0.;elapsed=0.
    start_state=None;start_history=None
    for k in range(n+2):
        tick=perf_counter()
        if policy=='oracle':cand=[d]
        else:cand=[c for c in cand if old.candidate_feasible(ys,history,c)]
        if not cand:raise RuntimeError('Empty candidate set')
        if len(cand)==1 and first_single is None:first_single=k
        if k==n:start_state=x.tolist();start_history=history.copy()
        if policy=='probe' and n>0 and k==0:
            u=old.PROBE;info={'feasible_prep':True,'terminal_slack':None,'certified_plan':False}
        else:u,info=plan(ys[-1],history,cand,n+2-k,max(0,n-k),variant,n+2)
        elapsed+=perf_counter()-tick;failures+=not info['feasible_prep'];ever|=info['certified_plan']
        applied=u if d==0 else (history[-1] if history else 0.)
        nxt=old.A@x+old.B*(applied+w[k])
        if k<n:
            energy+=old.DT*u*u;pmax=max(pmax,abs(nxt[0]));vmax=max(vmax,abs(nxt[1]))
        rows.append([k,*x,*ys[-1],u,applied,w[k],';'.join(map(str,cand)),info['terminal_slack'],
                     int(info['certified_plan']),*nxt])
        history.append(u);x=nxt;ys.append(x+errors[k+1])
    if policy!='oracle':cand=[c for c in cand if old.candidate_feasible(ys,history,c)]
    if len(cand)==1 and first_single is None:first_single=n+2
    if d not in cand:raise RuntimeError('True delay excluded')
    err=np.abs(x-old.TARGET)
    pvi=max(0.,pmax-old.PREP_BOUND[0]);vvi=max(0.,vmax-old.PREP_BOUND[1])
    return {'preview':n,'variant':variant['name'],'family':variant['family'],'policy':policy,'true_delay':d,
        'success':bool(np.all(err<=old.TOL+1e-10) and pvi<=1e-10 and vvi<=1e-10 and failures==0),
        'position_error_m':float(err[0]),'velocity_error_m_s':float(err[1]),
        'prep_command_energy':float(energy),'max_prep_position_m':float(pmax),'max_prep_velocity_m_s':float(vmax),
        'prep_position_violation_m':float(pvi),'prep_velocity_violation_m_s':float(vvi),
        'first_single_sample':first_single,'identified_by_start':bool(first_single is not None and first_single<=n),
        'final_candidates':cand,'prep_solver_failures':int(failures),'ever_certified_plan':ever,
        'controller_seconds':float(elapsed),'task_start_state':start_state,'task_start_history':start_history},rows

def summary(episodes):
    groups=[]
    keys=sorted(set((m['preview'],m['variant'],m['policy']) for m in episodes))
    for n,v,p in keys:
        group=[m for m in episodes if (m['preview'],m['variant'],m['policy'])==(n,v,p)]
        groups.append({'preview':n,'variant':v,'policy':p,'episodes':len(group),
            'success_count':sum(m['success'] for m in group),
            'success_fraction':float(np.mean([m['success'] for m in group])),
            'mean_prep_energy':float(np.mean([m['prep_command_energy'] for m in group])),
            'max_prep_position_m':max(m['max_prep_position_m'] for m in group),
            'max_prep_velocity_m_s':max(m['max_prep_velocity_m_s'] for m in group),
            'mean_identified_time_s':float(np.mean([m['first_single_sample']*.05 for m in group if m['first_single_sample'] is not None])) if any(m['first_single_sample'] is not None for m in group) else None,
            'never_identified_count':sum(m['first_single_sample'] is None for m in group),
            'identified_by_start_count':sum(m['identified_by_start'] for m in group),
            'prep_solver_failure_episodes':sum(m['prep_solver_failures']>0 for m in group),
            'prep_boundary_violation_episodes':sum(m['prep_position_violation_m']>1e-10 or m['prep_velocity_violation_m_s']>1e-10 for m in group),
            'mean_controller_ms':1000*float(np.mean([m['controller_seconds'] for m in group]))})
    return groups

def batch(folder,records,controllers):
    folder.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(folder/'paired_inputs.npz',names=np.array([r[0] for r in records]),
        disturbances=np.array([r[1] for r in records]),measurement_errors=np.array([r[2] for r in records]))
    episodes=[]
    with (folder/'trajectories.csv').open('w',newline='') as f:
        wr=csv.writer(f);wr.writerow(['preview','variant','policy','case','true_delay','k','p','v','measured_p','measured_v',
            'command','applied','disturbance','candidates','terminal_slack','certified_plan','next_p','next_v'])
        for n in PREVIEWS:
            for variant,policy in controllers:
                for name,w,errors in records:
                    for d in (0,1):
                        m,rows=run(n,variant,policy,d,w,errors);m['case']=name;episodes.append(m)
                        wr.writerows([[n,variant['name'],policy,name,d,*row] for row in rows])
            print(f'{folder.name}: completed N={n}, episodes={len(episodes)}',flush=True)
    write(folder/'episodes.json',episodes);write(folder/'summary.json',summary(episodes))
    return episodes

def development():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'development'/'summary.json').exists():raise RuntimeError('Development outputs already exist; preserve frozen runs.')
    config={'variants':VARIANTS,'previews':PREVIEWS,'test_seed':TEST_SEED,'test_cases':TEST_CASES,
        'selection_rule':'Within each family: most development successes, then least mean prep squared-command energy, then name.',
        'lex_slack_tolerance':1e-7,'tracking_reference':'Cubic Hermite from zero initial reference to absolute endpoint.',
        'progress_window_last_steps':4,'no_information_objective':True,
        'source_sha256':digest(__file__),'dependencies':{p:digest(ROOT/p) for p in ('preview_identification.py','task_ambiguity_scenarios.py')},
        'versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}}
    write(OUT/'config.json',config)
    batch(OUT/'development',old.cases(),[(v,'passive') for v in VARIANTS])

def freeze():
    config=read(OUT/'config.json');assert config['source_sha256']==digest(__file__)
    episodes=read(OUT/'development'/'episodes.json')
    scores=[]
    for v in VARIANTS:
        group=[m for m in episodes if m['variant']==v['name']]
        scores.append({'variant':v,'success_count':sum(m['success'] for m in group),'episodes':len(group),
                       'mean_prep_energy':float(np.mean([m['prep_command_energy'] for m in group]))})
    chosen=[]
    for family in ('legacy','energy','tracking','progress'):
        group=[s for s in scores if s['variant']['family']==family]
        chosen.append(sorted(group,key=lambda s:(-s['success_count'],s['mean_prep_energy'],s['variant']['name']))[0])
    manifest={'source_sha256':digest(__file__),'config_sha256':digest(OUT/'config.json'),
        'development_episodes_sha256':digest(OUT/'development'/'episodes.json'),
        'scores':scores,'selected':chosen,'test_not_generated_at_selection':not (OUT/'test'/'paired_inputs.npz').exists()}
    if (OUT/'frozen_selection.json').exists():raise RuntimeError('Selection already frozen')
    write(OUT/'frozen_selection.json',manifest)
    print(json.dumps(chosen,indent=2))

def test_records(seed=TEST_SEED,count=TEST_CASES):
    # Only called after selection is frozen. Same bounded generator family,
    # independent records; no claim of out-of-distribution evaluation.
    rng=np.random.default_rng(seed);records=[];length=max(PREVIEWS)+2
    for i in range(count):
        w=[rng.uniform(-old.W,old.W)]
        for _ in range(length-1):w.append(float(np.clip(w[-1]+rng.uniform(-old.RATE,old.RATE),-old.W,old.W)))
        error=rng.uniform(-1,1,(length+1,2))*old.NOISE
        records.append((f'heldout_{i:03d}',np.array(w),error))
    return records

def test():
    manifest=read(OUT/'frozen_selection.json');config=read(OUT/'config.json')
    assert manifest['source_sha256']==digest(__file__) and manifest['config_sha256']==digest(OUT/'config.json')
    assert manifest['development_episodes_sha256']==digest(OUT/'development'/'episodes.json')
    assert manifest['test_not_generated_at_selection']
    for p,h in config['dependencies'].items():assert digest(ROOT/p)==h
    if (OUT/'test'/'summary.json').exists():raise RuntimeError('Held-out run already exists; do not retune/retest it.')
    controllers=[(s['variant'],p) for s in manifest['selected'] for p in ('passive','probe')]
    controllers.append((next(v for v in VARIANTS if v['name']=='lex_energy'),'oracle'))
    batch(OUT/'test',test_records(),controllers)
    write(OUT/'test'/'provenance.json',{'frozen_manifest_sha256':digest(OUT/'frozen_selection.json'),
        'source_sha256':digest(__file__),'input_sha256':digest(OUT/'test'/'paired_inputs.npz'),
        'episodes_sha256':digest(OUT/'test'/'episodes.json'),'generator_seed':TEST_SEED})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('development','freeze','test'))
    phase=parser.parse_args().phase
    {'development':development,'freeze':freeze,'test':test}[phase]()
