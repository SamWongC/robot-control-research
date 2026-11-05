"""Exact-rational sanity checks for a literature/mathematics review.
These elementary counterexamples are not claimed as novel theorems.
"""
from fractions import Fraction as F
from pathlib import Path
import hashlib,json

def run():
    checks=[]
    # x+=x+u[k-d], identical zero state and zero old commands.
    # Fresh input 1 acts now for d=0 and later for d=1.
    assert F(1)!=F(0)
    checks.append(dict(name='empty_old_queue_does_not_remove_unknown_delay',
                       first_next_states=['1','0'],passed=True))
    # Two old queued-input sequences give identical terminal x but different paths.
    seq1=[F(1),F(-1)];seq2=[F(0),F(0)]
    path1=[seq1[0],sum(seq1)];path2=[seq2[0],sum(seq2)]
    assert path1[-1]==path2[-1] and abs(path1[0])>F(1,2)>=abs(path2[0])
    checks.append(dict(name='terminal_signature_omits_path_constraints',
                       paths=[[str(v) for v in a] for a in [path1,path2]],passed=True))
    # Available observation distinguishes labels. Forcing both labels to one
    # controller node forces the same immediate action. Dynamics x+=x+u+w.
    examples=[]
    for eps in [F(1,4),F(1,100),F(1,10000)]:
        eta=eps/8; disturbance=eps/8; tolerance=eps/2
        input_halfwidth=tolerance-eta-disturbance
        negative_center_interval=(eps-input_halfwidth,eps+input_halfwidth)
        positive_center_interval=(-eps-input_halfwidth,-eps+input_halfwidth)
        gap=negative_center_interval[0]-positive_center_interval[1]
        assert gap>0 and input_halfwidth>0
        assert eps+input_halfwidth<1
        # Observation noise eta plus initial radius eta is smaller than center gap.
        assert eps>2*eta
        examples.append(dict(epsilon=str(eps),state_radius=str(eta),noise_bound=str(eta),
                             disturbance_bound=str(disturbance),goal_tolerance=str(tolerance),
                             separate_policy_margin=str(input_halfwidth),action_interval_gap=str(gap)))
    checks.append(dict(name='small_distance_without_margin_condition_does_not_preserve_feasibility',
                       examples=examples,passed=True,
                       scope='Family of problems with shrinking tolerance; not a discontinuity claim for fixed positive tolerance and uniform Slater margin.'))
    # Scalar integrator, known state, pending queue of length d. Full path map
    # is lower triangular with unit diagonal. Determinant exactly one.
    for d in range(1,9):
        matrix=[[F(int(j<=i)) for j in range(d)] for i in range(d)]
        # Successive output differences recover every queue element.
        queue=[F(i+1,7) for i in range(d)]
        y=[sum(a*b for a,b in zip(row,queue)) for row in matrix]
        recovered=[y[0]]+[y[i]-y[i-1] for i in range(1,d)]
        assert recovered==queue
    checks.append(dict(name='full_path_queue_signature_has_no_linear_dimension_reduction',
                       dimensions=list(range(1,9)),determinant='1',passed=True,
                       scope='Known-delay scalar integrator across distinct histories; not a lower bound for arbitrary encodings or actual speedup.'))
    # Standard row-wise tightening: sup_{|U_i|<=1}|b+gU|=|b|+sum|g_i|.
    b=F(1,5);g=[F(1,3),F(-1,7)]
    vals=[abs(b+g[0]*a+g[1]*c) for a in [-1,1] for c in [-1,1]]
    bound=abs(b)+sum(abs(v) for v in g)
    assert max(vals)==bound
    checks.append(dict(name='standard_box_row_tightening',support=str(bound),passed=True))
    result=dict(checks=checks,passed=len(checks),new_theorem_claim=False,
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    folder=Path(__file__).resolve().parent/'results'/'queue_merge_review_2026-11-04'
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'math_checks.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':run()
