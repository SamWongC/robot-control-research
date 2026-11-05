"""Robust affine innovation feedback after uniformly separating first action.

Numerical robust LP certificates, not an exact-arithmetic proof or new method.
"""
from pathlib import Path
import argparse,csv,hashlib,json,platform
import numpy as np
import scipy
from scipy.optimize import linprog
import cvxpy as cp
import preview_identification as old

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'/'causal_preview_certificate'
NS=(0,1,2,3,4,8)
EPS=(.0002,.000225,.0002375,.00025,.0003,.0004,.0006,.001)
FIRST=.05
INITIAL_RADIUS=2*old.NOISE # explicit stronger initial perturbation coverage
Z_SCALE=np.abs(old.B)*old.W+old.NOISE+np.abs(old.A)@old.NOISE
SEED=2026110701

def write(p,o):p.write_text(json.dumps(o,indent=2),encoding='utf-8')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def name(n,ep):return f'n{n}_ep{round(ep*1e7):05d}'

def uncertainty(t):
    # q: normalized initial perturbation[2], w[t], e[0..t-1,2].
    dim=2+3*t;H=np.vstack([np.eye(dim),-np.eye(dim)]);h=np.ones(2*dim)
    rows=[]
    for k in range(t-1):
        r=np.zeros(dim);r[2+k+1]=1;r[2+k]=-1;rows.extend([r,-r])
    if rows:H=np.vstack([H,rows]);h=np.r_[h,np.full(len(rows),old.RATE/old.W)]
    return H,h

def observation_maps(t):
    dim=2+3*t;Y=np.zeros((2,dim));Y[:,:2]=np.diag(INITIAL_RADIUS/old.NOISE)
    offset=2+t;Y[:,offset:offset+2]=np.eye(2)
    Z=np.zeros((t,2,dim))
    for k in range(1,t):
        Z[k,:,2+k-1]=old.B*old.W/Z_SCALE
        Z[k,:,offset+2*k:offset+2*k+2]+=np.diag(old.NOISE/Z_SCALE)
        Z[k,:,offset+2*(k-1):offset+2*(k-1)+2]-=(old.A*old.NOISE[None,:])/Z_SCALE[:,None]
    return Y,Z

def constraints_numpy(v,J,K,d,n,ep):
    """Independent symbolic simulation of saved controller; normalized rows."""
    t=n+2;dim=2+3*t;Y,Z=observation_maps(t)
    uc=J@Y+np.einsum('ktj,tjm->km',K,Z)
    xnom=np.zeros(2);xc=np.zeros((2,dim));xc[:,:2]=np.diag(INITIAL_RADIUS)
    rows=[]
    for k in range(t):
        rows.append((f'u{k}',float(v[k]/old.LIMIT),uc[k]/old.LIMIT))
        index=k-d
        applied=v[index] if index>=0 else 0.
        coeff=uc[index] if index>=0 else np.zeros(dim)
        xnom=old.A@xnom+old.B*applied
        xc=old.A@xc+old.B[:,None]*coeff[None,:]
        xc[:,2+k]+=old.B*old.W
        if k+1<=n:
            for j in range(2):rows.append((f'prep{k+1}_{j}',float(xnom[j]/old.PREP_BOUND[j]),xc[j]/old.PREP_BOUND[j]))
    for j,tol in enumerate((ep,old.TOL[1])):
        rows.append((f'terminal{j}',float((xnom[j]-old.TARGET[j])/tol),xc[j]/tol))
    return rows

def support(coefficient,H,h):
    r=linprog(-coefficient,A_ub=H,b_ub=h,bounds=[(None,None)]*len(coefficient),method='highs',
        options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
    if not r.success:raise RuntimeError(r.message)
    return float(-r.fun),r.x

def synthesize(n,ep):
    t=n+2;H,h=uncertainty(t);dim=H.shape[1];Y,Z=observation_maps(t)
    margin=cp.Variable();con=[margin>=0,margin<=.5];variables={};dual_records=[]
    for d in (0,1):
        v=cp.Variable(t);J=cp.Variable((t,2));K=[cp.Variable((t,2)) for _ in range(t)]
        variables[d]=(v,J,K)
        con.extend([v[0]==FIRST,J[0,:]==0])
        for k in range(t):
            for j in range(t):
                if j==0 or j>k:con.append(K[k][j,:]==0)
        uc=[J[k,:]@Y+sum((K[k][j,:]@Z[j] for j in range(1,k+1)),cp.Constant(np.zeros(dim))) for k in range(t)]
        xnom=cp.Constant(np.zeros(2));xc=cp.Constant(np.c_[np.diag(INITIAL_RADIUS),np.zeros((2,dim-2))])
        rows=[]
        for k in range(t):
            rows.append((v[k]/old.LIMIT,uc[k]/old.LIMIT))
            index=k-d
            av=v[index] if index>=0 else 0.
            ac=uc[index] if index>=0 else np.zeros(dim)
            xnom=old.A@xnom+old.B*av
            bump=np.zeros((2,dim));bump[:,2+k]=old.B*old.W
            xc=old.A@xc+old.B[:,None]@cp.reshape(ac,(1,dim),order='C')+bump
            if k+1<=n:
                for j in range(2):rows.append((xnom[j]/old.PREP_BOUND[j],xc[j,:]/old.PREP_BOUND[j]))
        for j,tol in enumerate((ep,old.TOL[1])):
            rows.append(((xnom[j]-old.TARGET[j])/tol,xc[j,:]/tol))
        for nominal,coefficient in rows:
            lam=cp.Variable(len(h),nonneg=True)
            con.extend([H.T@lam==coefficient,nominal+h@lam<=1-margin,-nominal+h@lam<=1-margin])
            dual_records.append((lam,coefficient))
    problem=cp.Problem(cp.Maximize(margin),con)
    try:problem.solve(solver='CLARABEL',tol_gap_abs=1e-9,tol_gap_rel=1e-9,tol_feas=1e-9,max_iter=300)
    except cp.error.SolverError as exc:return {'solver_status':'error','reason':str(exc)},None,None
    result={'solver_status':problem.status}
    if problem.status not in ('optimal','optimal_inaccurate'):return result,None,None
    controllers={d:{'v':np.array(v.value),'J':np.array(J.value),
        'K':np.array([k.value for k in K])} for d,(v,J,K) in variables.items()}
    worst=0.;witnesses=[]
    for d,c in controllers.items():
        for label,nom,coef in constraints_numpy(**c,d=d,n=n,ep=ep):
            val,q=support(coef,H,h);normalized=abs(nom)+val;worst=max(worst,normalized)
            witnesses.append({'delay':d,'row':label,'normalized_bound':normalized,
                              'q':(q if nom>=0 else -q).tolist()})
    dual_error=max(float(np.max(np.abs(H.T@lam.value-np.array(coef.value)))) for lam,coef in dual_records)
    dual_min=min(float(np.min(lam.value)) for lam,_ in dual_records)
    causality=max(float(np.max(np.abs(c['J'][0]))) for c in controllers.values())
    for c in controllers.values():
        causality=max(causality,abs(float(c['v'][0])-FIRST))
        for k in range(t):
            for j in range(t):
                if j==0 or j>k:causality=max(causality,float(np.max(np.abs(c['K'][k,j]))))
    verified=bool(worst<=1-1e-7 and dual_error<=1e-7 and dual_min>=-1e-8 and causality<=1e-8)
    result.update(solver_margin=float(margin.value),independent_worst_normalized_bound=worst,
        verified_margin=1-worst,max_dual_equality_residual=dual_error,min_dual_entry=dual_min,
        max_causality_residual=causality,verified=verified)
    return result,controllers,witnesses

def obstruction(n,ep):
    if n==0:
        # Nominal necessary first-action sets, before any observation can differ.
        immediate_upper=(ep+.025*old.TOL[1])/.0025
        delayed_lower=max((old.TARGET[1]-old.TOL[1])/.05,(old.TARGET[0]-ep)/.00125,-2.)
        delayed_upper=min((old.TARGET[1]+old.TOL[1])/.05,(old.TARGET[0]+ep)/.00125,2.)
        if delayed_lower>delayed_upper or immediate_upper<delayed_lower:
            return 'all_causal_policies_nominal_first_action_conflict'
    if n==1:
        # Shared-future-branch argument for fixed FIRST, exact initial zero.
        necessary_upper=400*ep+10*old.TOL[1]-.075
        if FIRST>necessary_upper+1e-12:
            return 'fixed_first_action_causal_future_branch_conflict'
    return None

def build():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'frozen_manifest.json').exists():raise RuntimeError('Preserve frozen certificates')
    config={'previews':NS,'position_tolerances':EPS,'velocity_tolerance':float(old.TOL[1]),
        'first_action':FIRST,'initial_physical_radius':INITIAL_RADIUS.tolist(),
        'initial_radius_scope':'Contains original zero physical initial state; additional perturbations are conservative proof coverage.',
        'source_sha256':digest(__file__),'dependencies':{p:digest(ROOT/p) for p in ('preview_identification.py','task_ambiguity_scenarios.py')},
        'validation_seed':SEED,'versions':{'python':platform.python_version(),'numpy':np.__version__,
            'scipy':scipy.__version__,'cvxpy':cp.__version__}}
    write(OUT/'config.json',config);cells=[];hashes={}
    for n in NS:
        for ep in EPS:
            cell={'n':n,'position_tolerance':ep,'name':name(n,ep)}
            reason=obstruction(n,ep)
            if reason:cell.update(classification='proved_obstruction',obstruction=reason)
            else:
                result,controllers,witnesses=synthesize(n,ep);cell.update(result)
                cell['classification']='certified_policy' if result.get('verified') else 'unresolved'
                if result.get('verified'):
                    path=OUT/f'{cell["name"]}.npz'
                    np.savez_compressed(path,**{f'{key}_{d}':v for d,c in controllers.items() for key,v in c.items()})
                    hashes[path.name]=digest(path)
                    write(OUT/f'{cell["name"]}_witnesses.json',witnesses)
            cells.append(cell);print(f'N={n}, ep={ep}: {cell["classification"]}',flush=True)
    write(OUT/'cells.json',cells)
    selected=[]
    fixed_ep=[c for c in cells if c['position_tolerance']==.0002 and c['classification']=='certified_policy']
    if fixed_ep:selected.append(min(fixed_ep,key=lambda c:c['n'])['name'])
    fixed_n=[c for c in cells if c['n']==1 and c['classification']=='certified_policy']
    if fixed_n:selected.append(min(fixed_n,key=lambda c:c['position_tolerance'])['name'])
    longer=[c for c in fixed_ep if c['n']==4]
    if longer:selected.append(longer[0]['name'])
    manifest={'source_sha256':digest(__file__),'config_sha256':digest(OUT/'config.json'),
        'cells_sha256':digest(OUT/'cells.json'),'policy_sha256':hashes,'validation_cells':list(dict.fromkeys(selected)),
        'validation_inputs_not_generated':not (OUT/'validation_inputs.npz').exists()}
    write(OUT/'frozen_manifest.json',manifest)
    print(json.dumps({'validation_cells':selected,'classifications':{x:sum(c['classification']==x for c in cells) for x in ('proved_obstruction','certified_policy','unresolved')}},indent=2))

def load_controller(cell):
    data=np.load(OUT/f'{cell["name"]}.npz')
    return {d:{key:data[f'{key}_{d}'] for key in ('v','J','K')} for d in (0,1)}

def rollout(cell,controller,true_delay,x0,w,errors):
    n=cell['n'];t=n+2;x=np.array(x0,dtype=float);ys=[x+errors[0]];history=[]
    innovations=[np.zeros(2)];dhat=None;rows=[];pmax=0.;vmax=0.;energy=0.
    for k in range(t):
        if k==0:u=FIRST
        else:
            if k==1:
                candidates=[d for d in (0,1) if old.candidate_feasible(ys,history,d)]
                if len(candidates)!=1:raise RuntimeError(f'Identification failed: {candidates}')
                dhat=candidates[0]
            applied_previous=old.sent(history,k-1-dhat)
            z=(ys[-1]-old.A@ys[-2]-old.B*applied_previous)/Z_SCALE
            innovations.append(z)
            c=controller[dhat]
            u=float(c['v'][k]+c['J'][k]@(ys[0]/old.NOISE)+sum(c['K'][k,j]@innovations[j] for j in range(1,k+1)))
        # No clipping: bounds must follow from the certificate, not saturation.
        applied=u if true_delay==0 else old.sent(history,k-1)
        nxt=old.A@x+old.B*(applied+w[k])
        if k<n:pmax=max(pmax,abs(nxt[0]));vmax=max(vmax,abs(nxt[1]));energy+=old.DT*u*u
        rows.append([k,*x,*ys[-1],u,applied,w[k],dhat if dhat is not None else -1,*nxt])
        history.append(u);x=nxt;ys.append(x+errors[k+1])
    err=np.abs(x-old.TARGET);inputmax=max(abs(u) for u in history)
    success=bool(err[0]<=cell['position_tolerance']+1e-9 and err[1]<=old.TOL[1]+1e-9 and
        pmax<=old.PREP_BOUND[0]+1e-9 and vmax<=old.PREP_BOUND[1]+1e-9 and inputmax<=old.LIMIT+1e-9 and dhat==true_delay)
    return {'cell':cell['name'],'true_delay':true_delay,'success':success,'position_error_m':float(err[0]),
        'velocity_error_m_s':float(err[1]),'max_command':float(inputmax),'max_prep_p':float(pmax),
        'max_prep_v':float(vmax),'prep_energy':float(energy),'identified_delay':dhat},rows

def validate():
    manifest=read(OUT/'frozen_manifest.json');config=read(OUT/'config.json')
    assert digest(__file__)==manifest['source_sha256'] and digest(OUT/'config.json')==manifest['config_sha256']
    assert digest(OUT/'cells.json')==manifest['cells_sha256'] and manifest['validation_inputs_not_generated']
    for p,h in config['dependencies'].items():assert digest(ROOT/p)==h
    for p,h in manifest['policy_sha256'].items():assert digest(OUT/p)==h
    if (OUT/'validation_summary.json').exists():raise RuntimeError('Preserve completed validation')
    cells=read(OUT/'cells.json');rng=np.random.default_rng(SEED);length=max(NS)+2
    initial=[];disturbances=[];errors=[]
    for i in range(128):
        initial.append(np.zeros(2) if i<64 else rng.uniform(-1,1,2)*INITIAL_RADIUS)
        w=[rng.uniform(-old.W,old.W)]
        for _ in range(length-1):w.append(float(np.clip(w[-1]+rng.uniform(-old.RATE,old.RATE),-old.W,old.W)))
        disturbances.append(w);errors.append(rng.uniform(-1,1,(length+1,2))*old.NOISE)
    np.savez_compressed(OUT/'validation_inputs.npz',initial=np.array(initial),disturbances=np.array(disturbances),errors=np.array(errors))
    metrics=[]
    with (OUT/'validation_trajectories.csv').open('w',newline='') as f:
        wr=csv.writer(f);wr.writerow(['cell','case','true_delay','k','p','v','measured_p','measured_v','command','applied','disturbance','identified_delay','next_p','next_v'])
        for cellname in manifest['validation_cells']:
            cell=next(c for c in cells if c['name']==cellname);t=cell['n']+2;c=load_controller(cell)
            for i,(x0,w,e) in enumerate(zip(initial,disturbances,errors)):
                for d in (0,1):
                    m,rows=rollout(cell,c,d,x0,np.array(w[:t]),np.array(e[:t+1]));m.update(case=f'random_{i:03d}',initial_scope='zero' if i<64 else 'perturbed')
                    metrics.append(m);wr.writerows([[cellname,m['case'],d,*r] for r in rows])
            # Exact support optimizers are also executable disturbance/noise cases.
            witnesses=read(OUT/f'{cellname}_witnesses.json')
            for i,wit in enumerate(witnesses):
                q=np.array(wit['q']);x0=q[:2]*INITIAL_RADIUS;w=q[2:2+t]*old.W
                e=q[2+t:].reshape(t,2)*old.NOISE;e=np.vstack([e,np.zeros(2)])
                d=wit['delay'];m,rows=rollout(cell,c,d,x0,w,e)
                m.update(case=f'support_{i:03d}',initial_scope='support_optimizer')
                metrics.append(m);wr.writerows([[cellname,m['case'],d,*r] for r in rows])
    write(OUT/'validation_episodes.json',metrics)
    summaries=[]
    for cellname in manifest['validation_cells']:
        for scope in ('zero','perturbed','support_optimizer'):
            g=[m for m in metrics if m['cell']==cellname and m['initial_scope']==scope]
            summaries.append({'cell':cellname,'scope':scope,'episodes':len(g),'success_count':sum(m['success'] for m in g),
                'max_position_error_m':max(m['position_error_m'] for m in g),'max_velocity_error_m_s':max(m['velocity_error_m_s'] for m in g)})
    write(OUT/'validation_summary.json',summaries)
    write(OUT/'validation_provenance.json',{'manifest_sha256':digest(OUT/'frozen_manifest.json'),
        'input_sha256':digest(OUT/'validation_inputs.npz'),'episodes_sha256':digest(OUT/'validation_episodes.json')})
    print(json.dumps(summaries,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('build','validate'))
    phase=parser.parse_args().phase;{'build':build,'validate':validate}[phase]()
