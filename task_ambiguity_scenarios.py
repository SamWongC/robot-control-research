"""Analytic/LP task ambiguity witnesses; no new identification algorithm."""
from pathlib import Path
import csv, hashlib, json, platform
import numpy as np
import scipy
from scipy.optimize import linprog

DT=.05
A=np.array([[1.,DT],[0.,1.]])
B=np.array([.5*DT**2, DT])
H=2
LIMIT=2.
W=.02
RATE=.01
NOISE=np.array([1e-5,1e-4])
TOL=np.array([.0002,.003])
DELAYS=(0,1)

def lp(c, aub=None, bub=None, bounds=None, aeq=None, beq=None):
    r=linprog(c,A_ub=aub,b_ub=bub,A_eq=aeq,b_eq=beq,
              bounds=bounds,method='highs')
    if r.status not in (0,2):
        raise RuntimeError(r.message)
    return r

def prediction(delay):
    """x_H=A^H*x0 + G_d*U + E*w, with known prehistory u[-1]=0."""
    g=np.zeros((2,H)); e=np.zeros((2,H))
    for k in range(H):
        v=np.linalg.matrix_power(A,H-1-k)@B
        e[:,k]=v
        if k-delay>=0: g[:,k-delay]+=v
    return g,e

def disturbance_polytope():
    # No known previous disturbance; only within-future-window rate limits.
    rows=[]
    for j in range(H-1):
        z=np.zeros(H); z[j+1]=1; z[j]=-1
        rows.extend([z,-z])
    return np.array(rows),np.full(2*(H-1),RATE)

def robust_radius():
    _,e=prediction(0)
    au,bu=disturbance_polytope()
    radius=np.abs(np.linalg.matrix_power(A,H))@NOISE
    witnesses=[]
    for j in range(2):
        r=lp(-e[j],au,bu,[(-W,W)]*H)
        assert r.success
        radius[j]+=-r.fun
        witnesses.append(r.x.tolist())
    return radius,witnesses

def constraints(target, delays, radius):
    rows=[]; rhs=[]
    for d in delays:
        g,_=prediction(d)
        for j in range(2):
            rows.extend([g[j],-g[j]])
            rhs.extend([target[j]+TOL[j]-radius[j],
                        -target[j]+TOL[j]-radius[j]])
    return np.array(rows),np.array(rhs)

def solve_task(target,delays,radius):
    au,bu=constraints(target,delays,radius)
    # Minimize infinity norm of commands; gives zero at stationary target.
    a3=np.c_[au,np.zeros(len(au))]
    a3=np.vstack([a3,np.c_[np.eye(H),-np.ones(H)],
                 np.c_[-np.eye(H),-np.ones(H)]])
    b3=np.r_[bu,np.zeros(2*H)]
    r=lp([0.,0.,1.],a3,b3,[(-LIMIT,LIMIT)]*H+[(0.,LIMIT)])
    result={'feasible':bool(r.success),'status':int(r.status)}
    if r.success:
        u=r.x[:H]
        # Commands with no effect within the declared horizon are set to zero.
        unused=np.all(np.vstack([prediction(d)[0] for d in delays])==0,axis=0)
        u[unused]=0.
        result.update(commands=u.tolist(),
            max_constraint_residual=float(np.max(au@u-bu)),
            terminal_centers={str(d):(prediction(d)[0]@u).tolist() for d in delays})
    lo=lp([1.,0.],au,bu,[(-LIMIT,LIMIT)]*H)
    hi=lp([-1.,0.],au,bu,[(-LIMIT,LIMIT)]*H)
    result['first_action_interval']=([float(lo.fun),float(-hi.fun)] if lo.success and hi.success else None)
    return result

def compatibility(delay,window=6):
    # Measurements y[-window..0]=0, all sent commands in/before window=0.
    # Variables x_0..x_window, w_0..w_(window-1).
    n=2*(window+1)+window
    eq=[]
    for k in range(window):
        for j in range(2):
            z=np.zeros(n);z[2*(k+1)+j]=1
            z[2*k:2*k+2]-=A[j]
            z[2*(window+1)+k]=-B[j]
            eq.append(z)
    au=[]
    for k in range(window-1):
        z=np.zeros(n);z[2*(window+1)+k+1]=1;z[2*(window+1)+k]=-1
        au.extend([z,-z])
    bounds=[(-float(NOISE[j]),float(NOISE[j])) for _ in range(window+1) for j in range(2)]+[(-W,W)]*window
    r=lp(np.zeros(n),np.array(au),np.full(len(au),RATE),bounds,np.array(eq),np.zeros(len(eq)))
    return {'delay':delay,'compatible':bool(r.success),'window_transitions':window,
            'note':'All historical commands are zero, so both delayed regressors coincide.',
            'witness_max_equation_residual':float(np.max(np.abs(np.array(eq)@r.x))) if r.success else None}

def actual_rollout(u,delay,x0,w):
    x=np.array(x0,dtype=float); states=[x.copy()]
    for k in range(H):
        applied=u[k-delay] if k>=delay else 0.
        x=A@x+B*(applied+w[k]);states.append(x.copy())
    return np.array(states)

def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    root=Path(__file__).resolve().parent
    out=root/'results'/'task_ambiguity_scenarios';out.mkdir(parents=True,exist_ok=True)
    radius,witnesses=robust_radius()
    results={}
    for name,target in [('harmless',np.zeros(2)),('conflict',np.array([.002,.08]))]:
        results[name]={'target':target.tolist(),
            'individual_robust':{str(d):solve_task(target,[d],radius) for d in DELAYS},
            'common_robust':solve_task(target,DELAYS,radius),
            'individual_nominal':{str(d):solve_task(target,[d],np.zeros(2)) for d in DELAYS},
            'common_nominal':solve_task(target,DELAYS,np.zeros(2))}
    # Deterministic extreme checks; LP support (not this grid) establishes robustness.
    rows=[]
    for name,res in results.items():
        target=np.array(res['target'])
        for source in DELAYS:
            u=res['individual_robust'][str(source)]['commands']
            for actual in DELAYS:
                for ep in (-1,1):
                    for ev in (-1,1):
                        for w0 in (-W,0.,W):
                            for w1 in (-W,0.,W):
                                if abs(w1-w0)>RATE+1e-12:continue
                                xx=actual_rollout(u,actual,NOISE*np.array([ep,ev]),[w0,w1])
                                violation=np.maximum(0,np.abs(xx[-1]-target)-TOL)
                                rows.append([name,source,actual,ep,ev,w0,w1,*u,*xx[-1],*violation])
    with (out/'cross_model_checks.csv').open('w',newline='') as f:
        wr=csv.writer(f);wr.writerow(['scenario','plan_delay','actual_delay','initial_p_sign','initial_v_sign','w0','w1','u0','u1','terminal_p','terminal_v','position_violation_m','velocity_violation_m_s']);wr.writerows(rows)
    assert all(compatibility(d)['compatible'] for d in DELAYS)
    assert results['harmless']['common_robust']['feasible']
    assert all(results['conflict']['individual_robust'][str(d)]['feasible'] for d in DELAYS)
    assert not results['conflict']['common_nominal']['feasible']
    ints=[results['conflict']['individual_nominal'][str(d)]['first_action_interval'] for d in DELAYS]
    assert ints[0][1]<ints[1][0]
    self_rows=[r for r in rows if r[1]==r[2]]
    assert max(max(r[-2:]) for r in self_rows)<1e-9
    summary={'scope':'Constructed feasibility witnesses; no online identification policy or publication novelty claim.',
        'dt_s':DT,'horizon_steps':H,'input_limit':LIMIT,'disturbance_bound':W,
        'disturbance_increment_bound':RATE,'measurement_error_bounds':NOISE.tolist(),
        'terminal_tolerances':TOL.tolist(),'terminal_uncertainty_radius':radius.tolist(),
        'support_witnesses':witnesses,'history_compatibility':[compatibility(d) for d in DELAYS],
        'scenarios':results,'nominal_first_action_gap':float(ints[1][0]-ints[0][1]),
        'cross_checks':len(rows),
        'matched_plan_max_position_violation_m':float(max(r[-2] for r in self_rows)),
        'matched_plan_max_velocity_violation_m_s':float(max(r[-1] for r in self_rows)),
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}}
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    fig,axes=plt.subplots(1,2,figsize=(11,4),sharex=True,sharey=True)
    for ax,(name,res) in zip(axes,results.items()):
        for d in DELAYS:
            for offset,key,color in [(-.08,'individual_nominal','tab:blue'),(.08,'individual_robust','tab:orange')]:
                a,b=res[key][str(d)]['first_action_interval']
                ax.plot([a,b],[d+offset]*2,lw=6,color=color,
                        label=key.replace('individual_','') if d==0 else None)
        ax.set(title=name,xlabel='Admissible first command [m/s^2]',yticks=[0,1],ylabel='Assumed delay [steps]')
        ax.grid(alpha=.3)
    axes[0].legend();fig.suptitle('First-action feasibility: stationary vs short-deadline task')
    fig.tight_layout();fig.savefig(out/'first_action_sets.png',dpi=160);plt.close(fig)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
