"""Goal preview, delay discrimination and continuous-state task continuation.

Constructed benchmark, not a new active identification or safe control method.
"""
from pathlib import Path
from time import perf_counter
import csv, hashlib, json, platform
import numpy as np
import scipy
from scipy.optimize import linprog
from task_ambiguity_scenarios import A,B,DT,W,RATE,NOISE,TOL,LIMIT

PREVIEWS=(0,1,2,4,8)
MODES=('hold_passive','task_only','probe','oracle')
TARGET=np.array([.002,.08])
PREP_BOUND=np.array([.01,.06])
PROBE=.1
SEED=20261104
RANDOM_CASES=32

def sent(commands,index):
    return float(commands[index]) if index>=0 else 0.

def candidate_feasible(ys,commands,d):
    """Prefix-only bounded-error set membership, no truth or timestamps."""
    n=len(commands)
    if n==0:return True
    nv=2*(n+1)+n
    eq=[];beq=[]
    for k in range(n):
        for j in range(2):
            z=np.zeros(nv);z[2*(k+1)+j]=1
            z[2*k:2*k+2]-=A[j]
            z[2*(n+1)+k]=-B[j]
            eq.append(z);beq.append(B[j]*sent(commands,k-d))
    au=[]
    for k in range(n-1):
        z=np.zeros(nv);z[2*(n+1)+k+1]=1;z[2*(n+1)+k]=-1
        au.extend([z,-z])
    bounds=[(float(y[j]-NOISE[j]),float(y[j]+NOISE[j])) for y in ys for j in range(2)]+[(-W,W)]*n
    result=linprog(np.zeros(nv),A_eq=np.array(eq),b_eq=np.array(beq),
        A_ub=np.array(au) if au else None,b_ub=np.full(len(au),RATE) if au else None,
        bounds=bounds,method='highs',options={'primal_feasibility_tolerance':1e-9,
                                            'dual_feasibility_tolerance':1e-9})
    if result.status not in (0,2):raise RuntimeError(result.message)
    return result.success

def lifted(y,history,d,length):
    """All predicted states including known pending command, no queue reset."""
    centers=[];maps=[];radii=[]
    for i in range(1,length+1):
        center=np.linalg.matrix_power(A,i)@y
        g=np.zeros((2,length)); rad=np.abs(np.linalg.matrix_power(A,i))@NOISE
        for t in range(i):
            coeff=np.linalg.matrix_power(A,i-1-t)@B
            index=t-d
            if index>=0:g[:,index]+=coeff
            else:center+=coeff*sent(history,len(history)+index)
            # Exact positive-system support for a symmetric amplitude/rate set:
            # all +W and all -W satisfy every within-future rate constraint.
            rad+=np.abs(coeff)*W
        centers.append(center);maps.append(g);radii.append(rad)
    return np.array(centers),np.array(maps),np.array(radii)

def plan(y,history,candidates,remaining,prep_remaining):
    """Minimax normalized terminal violation; hard prep-state envelopes.

    Decision: remaining commands, their absolute values, terminal slack t>=0.
    If t=0, the particular common open-loop plan has a robust endpoint certificate.
    The future uncertainty product is an outer bound, not the conditional set.
    """
    h=remaining; nv=2*h+1; au=[];bu=[]
    for d in candidates:
        centers,gs,rs=lifted(y,history,d,h)
        for i in range(h):
            if i+1<=prep_remaining:
                for j in range(2):
                    for sign in (-1,1):
                        row=np.zeros(nv);row[:h]=sign*gs[i,j]
                        au.append(row);bu.append(PREP_BOUND[j]-rs[i,j]-sign*centers[i,j])
        for j in range(2):
            for sign in (-1,1):
                row=np.zeros(nv);row[:h]=sign*gs[-1,j]/TOL[j];row[-1]=-1
                au.append(row);bu.append(1-rs[-1,j]/TOL[j]-sign*(centers[-1,j]-TARGET[j])/TOL[j])
    for i in range(h):
        for sign in (-1,1):
            row=np.zeros(nv);row[i]=sign;row[h+i]=-1
            au.append(row);bu.append(0.)
    objective=np.r_[np.zeros(h),np.full(h,1e-5),1.]
    r=linprog(objective,A_ub=np.array(au),b_ub=np.array(bu),
        bounds=[(-LIMIT,LIMIT)]*h+[(0,LIMIT)]*h+[(0,None)],method='highs',
        options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
    if r.status not in (0,2):raise RuntimeError(r.message)
    if not r.success:
        return 0.,{'feasible_prep':False,'terminal_slack':None,'certified_plan':False}
    cmd=r.x[:h].copy()
    # If every model leaves a command outside the endpoint horizon, set it to 0.
    if all(np.all(lifted(y,history,d,h)[1][:,:,0]==0) for d in candidates):cmd[0]=0.
    residual=float(np.max(np.array(au)@r.x-np.array(bu)))
    return float(cmd[0]),{'feasible_prep':True,'terminal_slack':float(r.x[-1]),
        'certified_plan':bool(r.x[-1]<=1e-7 and residual<=1e-7),
        'max_lp_residual':residual}

def cases():
    length=max(PREVIEWS)+2
    zero=np.zeros(length);err=np.zeros((length+1,2))
    result=[('clean',zero.copy(),err.copy())]
    for sign in (-1,1):
        errors=np.array([sign*(-1)**k*NOISE for k in range(length+1)])
        result.append((f'constant_{sign:+d}',np.full(length,sign*W),errors))
    result.append(('alternating',np.array([.005*(-1)**k for k in range(length)]),
                   np.array([(-1)**k*NOISE for k in range(length+1)])))
    result.append(('ramp',np.clip(-W+RATE*np.arange(length),-W,W),err.copy()))
    rng=np.random.default_rng(SEED)
    for i in range(RANDOM_CASES):
        w=[rng.uniform(-W,W)]
        for _ in range(length-1):w.append(np.clip(w[-1]+rng.uniform(-RATE,RATE),-W,W))
        errors=rng.uniform(-1,1,(length+1,2))*NOISE
        result.append((f'random_{i:02d}',np.array(w),errors))
    return result

def run(preview,mode,true_delay,w,errors):
    # The physical initial state is zero in all paired cases. Its value is not
    # passed to inference/planning; the controller uses y0 and the error bounds.
    x=np.zeros(2);ys=[x+errors[0]];history=[];cand=[0,1]
    first_single=None;rows=[];ever_cert=False;prep_failures=0;solver_seconds=0.
    prep_energy=0.;prep_p=0.;prep_v=0.;recovery_state=None;recovery_history=None
    for k in range(preview+2):
        tick=perf_counter()
        if mode=='oracle':cand=[true_delay]
        else:
            cand=[d for d in cand if candidate_feasible(ys,history,d)]
            if not cand:raise RuntimeError('Empty candidate set under in-bound generated data')
        if len(cand)==1 and first_single is None:first_single=k
        if k==preview:
            recovery_state=x.copy();recovery_history=history.copy()
        if mode=='hold_passive' and k<preview:
            u=0.;info={'feasible_prep':True,'terminal_slack':None,'certified_plan':False}
        elif mode=='probe' and preview>0 and k==0:
            u=PROBE;info={'feasible_prep':True,'terminal_slack':None,'certified_plan':False}
        else:
            u,info=plan(ys[-1],history,cand,preview+2-k,max(0,preview-k))
        solver_seconds+=perf_counter()-tick
        ever_cert|=info['certified_plan'];prep_failures+=int(not info['feasible_prep'])
        if k<preview:prep_energy+=DT*u*u
        applied=sent(history,k-true_delay) if true_delay else u
        nxt=A@x+B*(applied+w[k])
        if k<preview:
            prep_p=max(prep_p,abs(nxt[0]));prep_v=max(prep_v,abs(nxt[1]))
        rows.append([k,*x,*ys[-1],u,applied,w[k],';'.join(map(str,cand)),
                     info['terminal_slack'],int(info['certified_plan']),*nxt])
        history.append(u);x=nxt;ys.append(x+errors[k+1])
    # Audit final causal observations as well, but count timely identification
    # using the time of first singleton relative to task start.
    if mode!='oracle':
        cand=[d for d in cand if candidate_feasible(ys,history,d)]
        if len(cand)==1 and first_single is None:first_single=preview+2
    true_kept=true_delay in cand
    if not true_kept:raise RuntimeError('True delay excluded')
    error=np.abs(x-TARGET)
    pv=max(0.,prep_p-PREP_BOUND[0]);vv=max(0.,prep_v-PREP_BOUND[1])
    success=bool(np.all(error<=TOL+1e-10) and pv<=1e-10 and vv<=1e-10 and prep_failures==0)
    metrics={'preview':preview,'mode':mode,'true_delay':true_delay,
        'success':success,'position_error_m':float(error[0]),'velocity_error_m_s':float(error[1]),
        'terminal_position_m':float(x[0]),'terminal_velocity_m_s':float(x[1]),
        'identified_by_task_start':bool(first_single is not None and first_single<=preview),
        'first_single_sample':first_single,'final_candidates':cand,'true_delay_retained':true_kept,
        'ever_certified_plan':ever_cert,'prep_solver_failures':prep_failures,
        'prep_command_energy':float(prep_energy),'max_prep_position_m':float(prep_p),
        'max_prep_velocity_m_s':float(prep_v),'prep_position_violation_m':float(pv),
        'prep_velocity_violation_m_s':float(vv),'controller_seconds':float(solver_seconds),
        'task_start_state':recovery_state.tolist(),'task_start_sent_history':recovery_history}
    return metrics,rows

def main():
    root=Path(__file__).resolve().parent;out=root/'results'/'preview_identification'
    out.mkdir(parents=True,exist_ok=True)
    config={'previews_steps':PREVIEWS,'modes':MODES,'target':TARGET.tolist(),
        'prep_state_bounds':PREP_BOUND.tolist(),'probe_amplitude':PROBE,'seed':SEED,
        'random_cases':RANDOM_CASES,'dt':DT,'disturbance_amplitude':W,
        'disturbance_increment_bound':RATE,'noise_bounds':NOISE.tolist(),
        'terminal_tolerances':TOL.tolist(),'input_bound':LIMIT,
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'dependency_sha256':hashlib.sha256((root/'task_ambiguity_scenarios.py').read_bytes()).hexdigest()}
    (out/'config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    fixed_cases=cases()
    np.savez_compressed(out/'paired_inputs.npz',names=np.array([c[0] for c in fixed_cases]),
        disturbances=np.array([c[1] for c in fixed_cases]),measurement_errors=np.array([c[2] for c in fixed_cases]))
    metrics=[]
    with (out/'trajectories.csv').open('w',newline='') as f:
        wr=csv.writer(f);wr.writerow(['preview','mode','case','true_delay','k','p','v','measured_p','measured_v',
            'command','applied','disturbance','candidates','terminal_slack','certified_plan','next_p','next_v'])
        for preview in PREVIEWS:
            for mode in MODES:
                for name,w,errors in fixed_cases:
                    for d in (0,1):
                        m,rows=run(preview,mode,d,w,errors);m['case']=name;metrics.append(m)
                        wr.writerows([[preview,mode,name,d,*r] for r in rows])
            print(f'Completed preview={preview} ({preview*DT:.2f} s)',flush=True)
    groups=[]
    for p in PREVIEWS:
        for mode in MODES:
            for scope in ('clean','stress','all'):
                group=[m for m in metrics if m['preview']==p and m['mode']==mode and
                    (scope=='all' or (m['case']=='clean')==(scope=='clean'))]
                groups.append({'preview':p,'mode':mode,'scope':scope,'episodes':len(group),
                    'success_count':sum(m['success'] for m in group),
                    'success_fraction':float(np.mean([m['success'] for m in group])),
                    'identified_by_start_fraction':float(np.mean([m['identified_by_task_start'] for m in group])),
                    'mean_prep_energy':float(np.mean([m['prep_command_energy'] for m in group])),
                    'prep_bound_violation_episodes':sum(m['prep_position_violation_m']>1e-10 or m['prep_velocity_violation_m_s']>1e-10 for m in group),
                    'prep_solver_failure_episodes':sum(m['prep_solver_failures']>0 for m in group),
                    'mean_controller_ms':float(1000*np.mean([m['controller_seconds'] for m in group]))})
    (out/'episodes.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    summary={'config':config,'episodes':len(metrics),'cases_per_delay':len(fixed_cases),
        'groups':groups,'all_true_delays_retained':all(m['true_delay_retained'] for m in metrics),
        'versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}}
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
    for ax,scope in zip(axes,('clean','stress')):
        for mode in MODES:
            g=[x for x in groups if x['scope']==scope and x['mode']==mode]
            ax.plot([x['preview']*DT for x in g],[100*x['success_fraction'] for x in g],'-o',label=mode)
        ax.set(title=scope,xlabel='Goal preview [s]',ylabel='Observed task success [%]',ylim=(-5,105))
        ax.grid(alpha=.3)
    axes[1].legend();fig.tight_layout();fig.savefig(out/'preview_success.png',dpi=160);plt.close(fig)
    print(f'Saved {len(metrics)} episodes; no resets at task start.',flush=True)

if __name__=='__main__':main()
