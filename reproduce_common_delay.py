"""Independent protocol-level reproduction of arXiv:2611.00841v1, V-B/Eq.(19).

Author record/code not supplied. Random draw ordering and secondary objective
are explicit independent choices; exact published numerical agreement is NOT
claimed. No switching-delay or ongoing-disturbance guarantee is inferred.
"""
from pathlib import Path
import csv, hashlib, json, platform, sys
import numpy as np
import cvxpy as cp
import clarabel

DELAYS=(1,2,3)
N=2
P_MEMORY=2
Q_MEMORY=5
M=7
GAMMA=.0132
ALPHA=np.array([-1.9,.88])
SOURCE='https://arxiv.org/html/2611.00841v1'


def history_model(delay,theta):
    a0=np.zeros((M,M))
    a0[1,0]=1.
    for i in range(P_MEMORY+1,M): a0[i,i-1]=1.
    e=np.eye(M)[:,[0]]
    b=np.eye(M)[:,[P_MEMORY]]
    s=np.zeros((4,M))
    s[:2,:2]=-np.eye(2)
    s[2:,P_MEMORY+delay:P_MEMORY+delay+2]=np.eye(2)
    return a0+e@np.asarray(theta).reshape(1,4)@s,b,e,s


def collect():
    # Each trial: two input amplitudes, two initial outputs, fourteen equation
    # errors. Explicit NumPy PCG64 draw order; not an author-record recovery.
    rng=np.random.default_rng(806)
    all_u=[]; all_y=[]; all_w=[]; columns={d:[] for d in DELAYS}; targets=[]
    for _ in range(12):
        u=np.tile(rng.standard_normal(2),8)
        y=np.zeros(16); y[:2]=rng.standard_normal(2)
        w=np.zeros(16); w[2:]=rng.uniform(-.01,.01,14)
        for k in range(2,16):
            control=.2*(u[k-3] if k>=3 else 0.)+.1*(u[k-4] if k>=4 else 0.)
            y[k]=-ALPHA@y[k-2:k][::-1]+control+w[k]
        for k in range(5,16):
            targets.append(y[k])
            for d in DELAYS:
                columns[d].append([-y[k-1],-y[k-2],u[k-d-1],u[k-d-2]])
        all_u.append(u); all_y.append(y); all_w.append(w)
    return np.array(targets),{d:np.array(v).T for d,v in columns.items()},np.array(all_u),np.array(all_y),np.array(all_w)


def fit(y,phi):
    u,s,vt=np.linalg.svd(phi,full_matrices=False)
    theta=(u/s)@(vt@y)
    residual=float(np.sum((y-theta@phi)**2))
    rho=GAMMA-residual
    if rho<0: raise RuntimeError('Candidate rejected by predetermined error budget')
    h_inverse_root=(u/s)@u.T
    return dict(theta=theta,residual=residual,rho=rho,condition=float(s[0]/s[-1]),
                rank=int(np.linalg.matrix_rank(phi)),inverse_root=h_inverse_root)


def certificate_matrix(p,f,l,lam,ahat,b,e_unc):
    e=np.eye(M)[:,[0]]
    return np.block([[p-lam*e@e.T,ahat@f+b@l,np.zeros((M,4))],
                     [(ahat@f+b@l).T,f+f.T-p,f.T@e_unc.T],
                     [np.zeros((4,M)),e_unc@f,lam*np.eye(4)]])


def check_positive(matrix):
    symmetric=(matrix+matrix.T)/2
    eig=float(np.linalg.eigvalsh(symmetric).min())
    scale=float(max(1.,np.linalg.norm(symmetric,2)))
    tol=100*len(matrix)*np.finfo(float).eps*scale
    return dict(min_eigenvalue=eig,scale=scale,normalized_min=eig/scale,
                tolerance=tol,passed=bool(eig>tol))


def synthesize(fits):
    f=cp.Variable((M,M)); l=cp.Variable((1,M)); margin=cp.Variable()
    ps={d:cp.Variable((M,M),symmetric=True) for d in DELAYS}
    lambdas={d:cp.Variable(nonneg=True) for d in DELAYS}
    matrices={}; constants={}
    constraints=[sum(cp.trace(p) for p in ps.values())==3.,margin>=0]
    for d in DELAYS:
        ahat,b,e,s=history_model(d,fits[d]['theta'])
        e_unc=np.sqrt(fits[d]['rho'])*fits[d]['inverse_root']@s
        p=ps[d]; lam=lambdas[d]
        matrices[d]=cp.bmat([[p-lam*(e@e.T),ahat@f+b@l,np.zeros((M,4))],
                            [(ahat@f+b@l).T,f+f.T-p,f.T@e_unc.T],
                            [np.zeros((4,M)),e_unc@f,lam*np.eye(4)]])
        constraints += [p >> margin*np.eye(M),lam>=margin,matrices[d] >> margin*np.eye(2*M+4)]
        constants[d]=(ahat,b,e_unc)
    settings=dict(solver='CLARABEL',tol_gap_abs=1e-9,tol_gap_rel=1e-9,tol_feas=1e-9,max_iter=500)
    first=cp.Problem(cp.Maximize(margin),constraints)
    first.solve(**settings)
    if first.status not in ['optimal','optimal_inaccurate'] or margin.value is None or margin.value<=1e-8:
        raise RuntimeError(f'No positive synthesis margin: {first.status}, {margin.value}')
    optimum=float(margin.value)
    # Explicit secondary surrogate, not asserted identical to authors' choice.
    second=cp.Problem(cp.Minimize(cp.sum_squares(l)+1e-3*cp.sum_squares(f)),constraints+[margin>=.5*optimum])
    second.solve(**settings)
    if second.status not in ['optimal','optimal_inaccurate']: raise RuntimeError(second.status)
    fv,lv=np.array(f.value),np.array(l.value)
    k=np.linalg.solve(fv.T,lv.T).T
    checks={}
    for d in DELAYS:
        ahat,b,e_unc=constants[d]
        p=np.array(ps[d].value); lam=float(lambdas[d].value)
        matrix=certificate_matrix(p,fv,lv,lam,ahat,b,e_unc)
        checks[d]=check_positive(matrix)
        checks[d]['P']=check_positive(p)
        checks[d]['lambda']=lam
        if not checks[d]['passed'] or not checks[d]['P']['passed'] or lam<=0:
            raise RuntimeError('Independent floating-point certificate verification failed')
    return k,{d:np.array(ps[d].value) for d in DELAYS},fv,lv,dict(
        first_margin=optimum,secondary_margin=float(margin.value),
        first_status=first.status,second_status=second.status,checks=checks,
        lambdas={d:float(lambdas[d].value) for d in DELAYS})


def run():
    root=Path(__file__).resolve().parent
    out=root/'results'/'common_delay_reproduction'; out.mkdir(parents=True,exist_ok=True)
    y,phis,inputs,outputs,errors=collect()
    fits={d:fit(y,phis[d]) for d in DELAYS}
    gain,ps,f,l,solve_info=synthesize(fits)
    audit={}; simulations=[]
    rng=np.random.default_rng(781)
    for d in DELAYS:
        ahat,b,e,s=history_model(d,fits[d]['theta'])
        e_unc=np.sqrt(fits[d]['rho'])*fits[d]['inverse_root']@s
        lam=solve_info['lambdas'][d]
        numerical=certificate_matrix(ps[d],f,l,lam,ahat,b,e_unc)
        check=check_positive(numerical)
        if not check['passed']: raise RuntimeError('Recovered certificate not strictly positive')
        beta=np.array([.2,.1]) if d==2 else np.array([.1,.2])
        theta=np.r_[ALPHA,beta]
        actual_residual=float(np.sum((y-theta@phis[d])**2))
        if actual_residual>GAMMA+1e-12: raise RuntimeError('Illustrated plant not data-compatible')
        a,b,_,_=history_model(d,theta)
        closed=a+b@gain
        z=np.array([1.,.9,0.,0.,0.,0.,0.])
        for step in range(201):
            command=float((gain@z).item())
            simulations.append([d,step,float(z[0]),command,float(np.linalg.norm(z))])
            z=closed@z
        # Random boundary/interior checks supplement, never replace, the LMI.
        max_radius=0.; min_decay=np.inf
        pinv=np.linalg.inv(ps[d])
        for _ in range(1000):
            direction=rng.standard_normal(4); direction/=np.linalg.norm(direction)
            radius=1. if _<500 else rng.random()**.25
            sample=fits[d]['theta']+np.sqrt(fits[d]['rho'])*fits[d]['inverse_root']@direction*radius
            sa,_,_,_=history_model(d,sample)
            ac=sa+b@gain
            max_radius=max(max_radius,float(np.max(np.abs(np.linalg.eigvals(ac)))))
            min_decay=min(min_decay,float(np.linalg.eigvalsh(pinv-ac.T@pinv@ac).min()))
        if max_radius>=1 or min_decay<=0: raise RuntimeError('Ellipsoid sample verification failed')
        audit[d]=dict(rank=fits[d]['rank'],condition=fits[d]['condition'],ls_residual=fits[d]['residual'],
            radius_squared=fits[d]['rho'],illustrated_residual=actual_residual,
            certificate=check,lambda_recovered=lam,
            illustrated_spectral_radius=float(np.max(np.abs(np.linalg.eigvals(closed)))),
            sampled_max_spectral_radius=max_radius,sampled_min_lyapunov_decay=min_decay,
            open_loop_spectral_radius=float(np.max(np.abs(np.linalg.eigvals(a)))))
        np.save(out/f'certificate_delay{d}.npy',numerical)
    np.savez_compressed(out/'data_and_controller.npz',Y=y,inputs=inputs,outputs=outputs,
        equation_errors=errors,K=gain,F=f,L=l,**{f'Phi{d}':phis[d] for d in DELAYS},
        **{f'P{d}':ps[d] for d in DELAYS})
    with (out/'trajectories.csv').open('w',newline='') as file:
        w=csv.writer(file); w.writerow(['delay_steps','sample','last_output_in_history','command','history_norm']); w.writerows(simulations)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    data=np.array(simulations)
    fig,axes=plt.subplots(2,1,figsize=(10,6),sharex=True,layout='constrained')
    for d in DELAYS:
        sub=data[data[:,0]==d]
        axes[0].plot(sub[:,1],sub[:,2],label=f'delay {d}')
        axes[1].semilogy(sub[:,1],np.maximum(sub[:,4],1e-16),label=f'delay {d}')
    axes[0].set_ylabel('Stored output y(k-1)'); axes[1].set_ylabel('History-state norm')
    axes[0].legend(); axes[1].set_xlabel('Discrete sample (no physical dt assigned)')
    for ax in axes: ax.grid(alpha=.25)
    fig.suptitle('One verified common gain; three distinct fixed-delay compatible plants',fontsize=11)
    fig.savefig(out/'common_controller.png',dpi=160); plt.close(fig)
    record=dict(source=SOURCE,scope='independent protocol-level reproduction, not exact author-record recovery',
        config=dict(seed=806,draw_order='per trial: two input amplitudes, two initial outputs, fourteen errors',
            experiments=12,length=16,columns=list(range(5,16)),gamma=GAMMA,delays=DELAYS,
            secondary_objective='norm(L)^2+0.001 norm(F)^2, at least half first-stage strict margin',
            trace_sum_P=3,sample_seed=781,samples_per_ellipsoid=1000,online_disturbance=False,
            state_input_constraints=False,switching_delay=False),
        environment=dict(python=sys.version,numpy=np.__version__,cvxpy=cp.__version__,clarabel=clarabel.__version__,platform=platform.platform()),
        gain=gain.tolist(),F_condition=float(np.linalg.cond(f)),solve_info=solve_info,audit=audit,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out/'summary.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps(record,indent=2))


if __name__=='__main__': run()
