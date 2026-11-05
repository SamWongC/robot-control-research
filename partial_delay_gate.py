"""Three-delay research gate. New instance, not a continuation of old test data.

All guarantees below concern explicitly stated bounded linear dynamics.
No claim of a new synthesis algorithm or a global causal-policy boundary.
"""
from pathlib import Path
import csv, hashlib, itertools, json
import numpy as np
from scipy.optimize import linprog

A=np.array([[1.,1.],[0.,1.]])
B=np.array([.5,1.])
H=4
DS=(0,1,2)
X=np.array([.001,.001])
W=.002
V=np.array([.002,.002])
GOAL=np.array([.1,-.3])
TOL=np.array([.2,.05])
FIRST=.4
SEED=2026110801

def prediction(d, horizon=H):
    g=np.zeros((2,H)); e=np.zeros((2,horizon))
    for k in range(horizon):
        z=np.linalg.matrix_power(A,horizon-1-k)@B
        e[:,k]=z
        if k>=d: g[:,k-d]=z
    return g,e

def radius(horizon=H):
    return np.abs(np.linalg.matrix_power(A,horizon))@X+np.abs(prediction(0,horizon)[1]).sum(axis=1)*W

def solve(delays, first=FIRST, synthesis_limit=.9):
    g=np.vstack([prediction(d)[0] for d in delays])
    target=np.tile(GOAL,len(delays)); tol=np.tile(TOL-radius(),len(delays))
    # Scalar slack has a numerical normalization of 1 m and 1 m/s.
    # Report component-wise physical margins separately.
    au=np.vstack([np.c_[g,np.ones(len(g))],np.c_[-g,np.ones(len(g))]])
    bu=np.r_[target+tol,-target+tol]
    bounds=[(-synthesis_limit,synthesis_limit)]*H+[(None,None)]
    if first is not None: bounds[0]=(first,first)
    r=linprog([0,0,0,0,-1],A_ub=au,b_ub=bu,bounds=bounds,method='highs')
    if not r.success: raise RuntimeError(r.message)
    u=r.x[:H].copy()
    u[np.all(g==0,axis=0)]=0.
    return dict(delays=list(delays),commands=u.tolist(),normalized_slack=float(r.x[-1]),
                centers={str(d):(prediction(d)[0]@u).tolist() for d in delays},
                physical_margins={str(d):(TOL-radius()-np.abs(prediction(d)[0]@u-GOAL)).tolist() for d in delays})

def observation_intervals(time, first=FIRST):
    # For t=1 all models; t=2 only unresolved delays 1,2.
    # Those delayed models have no dependence on the command sent at k=1.
    ds=DS if time==1 else (1,2)
    rad=radius(time)[1]+V[1]
    return {str(d):[float((first if d<time else 0)-rad),
                    float((first if d<time else 0)+rad)] for d in ds}

def cells(intervals):
    endpoints=sorted({v for interval in intervals.values() for v in interval})
    out=[]
    probes=[('point',x,x,x) for x in endpoints]
    probes += [('open',a,b,(a+b)/2) for a,b in zip(endpoints[:-1],endpoints[1:])]
    for kind,a,b,mid in sorted(probes,key=lambda z:(z[1],z[2])):
        candidates=[int(d) for d,(lo,hi) in intervals.items() if lo<=mid<=hi]
        out.append(dict(kind=kind,lower=a,upper=b,candidates=candidates))
    return out

def action_interval(policies):
    lo,hi=.01,1. # strict separation requires a > .01; actual lower below is larger.
    for policy in policies:
        u=np.array(policy['commands'])
        for d in policy['delays']:
            g=prediction(d)[0]
            rest=g@u-g[:,0]*u[0]-GOAL
            for coeff,offset,bound in zip(g[:,0],rest,TOL-radius()):
                if coeff>0:
                    lo=max(lo,(-bound-offset)/coeff)
                    hi=min(hi,(bound-offset)/coeff)
                elif abs(offset)>bound: return None
    return [float(lo),float(hi)]

def rollout(d,x,w,errors,p0,p12):
    x=np.array(x).copy(); ys=[]; states=[x.copy()]; sent=[]; u=None
    branch=None
    for k in range(H):
        if k==0: command=FIRST
        else:
            if k==1:
                branch=0 if ys[-1][1]>.2 else 12
                u=p0 if branch==0 else p12
            command=u[k]
        sent.append(command)
        applied=sent[k-d] if k>=d else 0.
        x=A@x+B*(applied+w[k]); states.append(x.copy())
        ys.append(x+errors[k])
    return np.array(states),np.array(ys),np.array(sent),branch

def verify_corners(p0,p12):
    # Every vertex of initial-state and disturbance boxes: exact affine maxima.
    minima=np.full(2,np.inf); max_state=np.zeros(2); count=0
    for d in DS:
        u=p0 if d==0 else p12
        for signs in itertools.product((-1.,1.),repeat=H+2):
            x=X*np.array(signs[:2]); w=W*np.array(signs[2:]); sent=[]
            for k in range(H):
                sent.append(u[k]); x=A@x+B*((sent[k-d] if k>=d else 0)+w[k])
                max_state=np.maximum(max_state,np.abs(x))
            minima=np.minimum(minima,TOL-np.abs(x-GOAL)); count+=1
    return dict(vertices=count,min_terminal_margin=minima.tolist(),max_abs_state=max_state.tolist())

def run(root):
    output=root/'results'/'partial_delay_gate'; output.mkdir(parents=True,exist_ok=True)
    report=root/'report'; report.mkdir(exist_ok=True)
    p0=solve((0,)); p12=solve((1,2)); common=solve(DS,synthesis_limit=1.); common_free=solve(DS,None,synthesis_limit=1.)
    u0=np.array(p0['commands']); u12=np.array(p12['commands'])
    corners=verify_corners(u0,u12)
    rng=np.random.default_rng(SEED); rows=[]; branch_fail=0; late_id_fail=0; task_fail=0
    for case in range(512):
        x=rng.uniform(-X,X); w=rng.uniform(-W,W,H); errors=rng.uniform(-V,V,(H,2))
        for d in DS:
            states,ys,sent,branch=rollout(d,x,w,errors,u0,u12)
            branch_fail+=int(branch!=(0 if d==0 else 12))
            late_id=(0 if branch==0 else (1 if ys[1,1]>.2 else 2))
            late_id_fail+=int(late_id!=d)
            task_fail+=int(np.any(np.abs(states[-1]-GOAL)>TOL+1e-12) or np.any(np.abs(states)>2+1e-12) or np.any(np.abs(sent)>1+1e-12))
            for k in range(H):
                rows.append([case,d,k,*states[k],sent[k],w[k],*errors[k],*ys[k],*states[k+1]])
    with (output/'trajectories.csv').open('w',newline='',encoding='utf8') as f:
        writer=csv.writer(f); writer.writerow(['case','delay','step','p','v','u','w','ep','ev','yp_next','yv_next','p_next','v_next']);writer.writerows(rows)
    summary=dict(config=dict(dt=1.,horizon=H,delays=DS,initial_radius=X.tolist(),disturbance=W,
        measurement_radius=V.tolist(),target=GOAL.tolist(),tolerance=TOL.tolist(),input_limit=1.,
        state_limits=[2.,2.],first=FIRST,seed=SEED,prehistory='zero',disturbance_rate_limit=None),
        terminal_radius=radius().tolist(),policy_zero=p0,policy_unresolved=p12,
        common_open_loop_fixed_first=common,common_open_loop_free_first=common_free,
        first_observation_intervals=observation_intervals(1),first_observation_cells=cells(observation_intervals(1)),
        second_observation_intervals=observation_intervals(2),fixed_suffix_feasible_first_interval=action_interval([p0,p12]),
        corner_verification=corners,simulation=dict(episodes=1536,transitions=len(rows),branch_errors=branch_fail,late_identification_errors=late_id_fail,task_failures=task_fail),
        input_margin=float(1-max(np.max(np.abs(u0)),np.max(np.abs(u12)))),
        decision='FOUND strict tau=1 separation; REJECTED as evidence that unique identification by task completion harms the task',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    assert min(corners['min_terminal_margin'])>0
    assert np.all(np.array(corners['max_abs_state'])<2)
    assert branch_fail==late_id_fail==task_fail==0
    (output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    write_reports(report,summary)
    print(json.dumps(summary,indent=2))

def write_reports(report,s):
    p0=s['policy_zero'];p12=s['policy_unresolved'];corner=s['corner_verification'];interval=s['fixed_suffix_feasible_first_interval']
    numeric=f"""
| Quantity | Result |
|---|---|
| Commands after zero-delay branch | {p0['commands']} |
| Commands shared by delays 1 and 2 | {p12['commands']} |
| Terminal uncertainty radius (m, m/s) | {s['terminal_radius']} |
| Worst component terminal margins (m, m/s) | {corner['min_terminal_margin']} |
| Input margin below actual bound 1 | {s['input_margin']} |
| Robust admissible first input with fixed suffixes | {interval} |
| Common open-loop slack, first fixed | {s['common_open_loop_fixed_first']['normalized_slack']} |
| Common open-loop slack, first free | {s['common_open_loop_free_first']['normalized_slack']} |
| Exhaustive initial/disturbance vertices | {corner['vertices']} |
| Random episodes / transition records | 1536 / 6144 |
| Branch / time-2 identification errors | 0 / 0 |
"""
    zh="""# 三延迟部分辨识：分离实例与观测分支验证

日期：2026-11-04。状态：研究门槛试验，不是已确认的 RA-L 创新。

## 结论

构造出有正裕度的实例：时刻1区分 d=0 与 {1,2}，后两者使用同一后续指令即可保证完成任务。要求时刻1唯一辨识全部候选不可能。

但更强的审查发现：同一控制策略不改变任何动作，只利用时刻2已经到达的观测，就能保证唯一辨识全部延迟。因此该实例不能证明“完整辨识损害任务”，也不能证明部分辨识优于允许稍晚完成辨识的强基线。它仅证明首个决策时刻不必已经知道全部延迟。该差异由传播时序造成，不能作为主要创新。

## 模型与范围

新建独立实例，不复用旧实验的测试集。双积分器采样1秒，A=[[1,1],[0,1]]，B=[0.5,1]。d∈{0,1,2}固定，指令前史为0；4步期限；|u|≤1；|p|≤2米、|v|≤2米/秒。初态盒半径[0.001,0.001]，每步加速度扰动|w|≤0.002，观测噪声盒半径[0.002,0.002]。无额外扰动变化率假设。目标[0.1,-0.3]，终点容差[0.2,0.05]。这些是构造参数，没有声称来自机器人实测。

先发送 a=0.4；时刻1测得速度>0.2时采用零延迟分支，否则采用{1,2}共同分支。之后发送分支固定指令，不再根据后续观测改动作。没有访问真实延迟或扰动；仿真中的真值仅供评价。

## 定理A：有正裕度的早期部分辨识可行实例

时刻1速度观测集合分别为 d=0:[0.395,0.405]，d=1与2:[-0.005,0.005]。后两者完整的时刻1观测集合也完全相同，因为首条命令均尚未作用。任何因果首步输入都不能保证时刻1区分1和2；相同初态、扰动与噪声给出完全相同历史。

对上述阈值分支，真实模型不被错分。每个分支的终点映射为 A^4 x0+G_d U+Ew；盒不确定性的精确支持半径为[0.021,0.009]。逐模型核验 |G_d U-goal|+radius≤tolerance，且中间状态和输入满足界。由此得到全盒的鲁棒充分保证，不靠随机成功率替代证明。

下表最小终点裕度严格为正；保持其他参数和后续指令不变，首步存在非零宽度可行区间。初态、噪声和扰动界非零，因此不是无噪声单点巧合。数值计算为浮点核验，未声称精确算术机器证明。
"""+numeric+"""
## 更强反检验：时刻2完整辨识不需要额外动作

对仍未决的1与2，时刻2速度观测分别落在[0.393,0.407]和[-0.007,0.007]；时刻1发送的指令此时还不影响这两个模型的速度。使用同一个0.2阈值即可确定真实延迟。已识别为0的分支保持标签即可。因此同一物理策略也属于“时刻2前完成唯一辨识”的可行策略类。不能把时刻1不可辨识外推到期限4不可辨识。

共同开环 LP 仅检验固定整个指令序列的策略类；其不可行不表示一般被动反馈或一般双重控制不可行。表中分别给出了固定首步和自由首步的结果。不得把开环与反馈的差异包装为部分辨识算法优势。

## 命题B：固定首步、一次分支策略的连续观测验证

对固定动作a，每个模型的标量观测投影是闭区间I_d(a)。将全部端点排序，分别检查每个端点及相邻端点间的开区间；区间内部候选标签恒定，两侧无候选区域不可能发生。端点必须单独检查，不能只采样网格。每个非空单元采用对其全部候选及相容不确定性安全的共同后续策略，则所有合法连续标量观测均被覆盖。

代码保存了完整单元表，含没有候选的中间空隙。这里按速度投影可能保留额外候选，但不会删除真实模型；本例1与2的联合观测集合也完全相同。后续策略使用未条件化初态/扰动盒验证，因而保守但安全，不会因错误条件化而遗漏轨迹。这是一次分支、分支内开环策略的充分验证，不是一般反馈策略的完备判定。

对m个闭区间，端点及内部开单元最多4m-1个（不计两侧空区域），因此这个特殊问题不需枚举无穷观测。此结论属于标准区间排列，不能当成新算法贡献；多维、多步及动作依赖分区尚未解决。

## 对上一轮核心算法命题的约束

本轮只给出固定首步的一维分支验证。没有实现动作可变时有效的反例约束，没有证明多步观测树压缩、上下界收敛或相对完整策略类的完备性。由某个a下的失败候选组合，不能直接推导所有a都须分离该组合：状态与队列会改变。下一项真正有价值的工作应是形式化这类动作依赖约束及其有效域；若只能使用区间排列加鲁棒LP，仍不满足论文核心贡献门槛。

## 验证与去留

精确仿射支持公式与独立逐步传播的192个初态/扰动顶点交叉核验；观测误差全范围由解析区间覆盖；额外1536次随机实现检查因果时序、分支与时刻2辨识。随机样本不是统计优越性试验，不是独立机器人测试。针对性单元测试另存test_results.txt。

决定：保留为基础单元测试和反例审查资产；不升级为RA-L创新确认，不立即启动大规模机器人实验。下一门槛应检查：同样的任务、观测和可等待时间下，是否存在非退化的真正分离，或是否能得到新的可计算结构结果。若只有提前人为规定辨识截止时刻的优势，不能作为核心结果。

文件：partial_delay_gate.py；test_partial_delay_gate.py；results/partial_delay_gate/summary.json、trajectories.csv、test_results.txt。历史实验不变。本轮没有新增文献原创性认证。
"""
    en="""# Three-delay partial identification: separation witness and observation verification

Date: 2026-11-04. Research gate, not confirmed RA-L novelty.

## Decision

A positive-margin instance permits separating delay 0 from {1,2} at time 1 and completing the task with one continuation shared by delays 1 and 2. Guaranteed unique identification at time 1 is impossible. However, the SAME physical policy uniquely identifies all delays at time 2 using already available measurements, without changing any command. The instance therefore does NOT establish a task cost of complete identification or an advantage over a strong baseline allowed to identify later. The early distinction is caused by transport timing, not a new control principle.

## Independent instance and policy

Double integrator: sample period 1 s, A=[[1,1],[0,1]], B=[0.5,1], fixed d in {0,1,2}, zero command prehistory, horizon 4. Input bound 1; state bounds |p|<=2 m and |v|<=2 m/s. Initial box radius [0.001,0.001], acceleration disturbance bound 0.002 with no rate restriction, measurement box radius [0.002,0.002]. Goal [0.1,-0.3], terminal tolerance [0.2,0.05]. Parameters are constructed, not calibrated to a robot.

Send a=0.4. At time 1, select the delay-0 branch if measured velocity exceeds 0.2, otherwise the shared {1,2} branch. The selected suffix is open loop. True delay and disturbances are used only for evaluation. Historical experiments and their frozen test sets are unchanged.

## Proposition A: robust early partial-identification witness

At time 1, measured-velocity intervals are [0.395,0.405] for d=0 and [-0.005,0.005] for both d=1 and d=2. The full joint observations for the latter two also have identical reachable sets: neither has yet received a command. For any first action, identical admissible initial states and disturbances/noises yield identical histories for those delays. Consequently no causal controller can guarantee unique identification at time 1.

The threshold classifier never removes the true model. Terminal maps are A^4 x0+G_d U+Ew. Their exact box support radius is [0.021,0.009]. Checking |G_d U-goal|+radius<=tolerance establishes a robust sufficient certificate for each shared branch. Input and intermediate-state constraints are also checked. Positive component margins and a nonzero first-action interval demonstrate robustness, not a noiseless isolated equality. These are floating-point numerical checks, not exact-arithmetic machine proofs.
"""+numeric+"""
## Stronger falsification: free complete identification at time 2

For unresolved delays 1 and 2, the time-2 velocity intervals are [0.393,0.407] and [-0.007,0.007], respectively. The command sent at time 1 cannot yet affect either model at time 2. Applying the same threshold identifies the delay; the already identified delay-0 branch keeps its label. No physical action changes. Thus this policy also satisfies complete identification by time 2, well before task completion at time 4.

Common open-loop LP results concern only a single fixed command sequence, with either fixed or free first input as indicated. Infeasibility in that class is not infeasibility of general passive feedback or dual control. Comparing it against a branching policy does not isolate the benefit of partial identification.

## Proposition B: exhaustive scalar observation cells for a fixed probe

For fixed a, let each model's scalar observation projection be a closed interval I_d(a). Sort all endpoints and enumerate each endpoint as a singleton and every consecutive open interval separately. Candidate labels are constant on every open cell. Cells with no candidates are unreachable. Assigning a robust common continuation to every nonempty cell covers all admissible scalar observations. Checking endpoints explicitly avoids missing boundary ambiguity.

The summary stores every cell, including the unreachable gap. Projection may retain extra models but does not delete the true one. In this example the full joint sets for delays 1 and 2 also coincide. Continuations are certified against unconditional uncertainty boxes, a conservative but sound choice. This is a sufficient verifier for one observation branch followed by an open-loop suffix, not a complete synthesis method for arbitrary feedback.

For m closed intervals there are at most 4m-1 endpoint/interior cells, excluding the two empty exterior regions. This is standard interval-arrangement reasoning and is not claimed as novel. Higher-dimensional observations, multiple branches, and changing first actions remain unresolved.

## Core synthesis gate remains open

No action-dependent valid cuts, observation-tree compression, optimality-gap bound, or completeness theorem were obtained. A conflicting set at one action cannot simply be forbidden for all actions because state and queued commands change. Establishing valid domains for such cuts is a real remaining obligation. Merely combining interval arrangements and robust LPs would not clear the independent-contribution gate.

## Validation and next decision

Cross-check the support formula with independent stepwise propagation of all 192 initial-state/disturbance vertices. Observation-noise coverage is analytic. An additional 1536 random episodes check causal execution and classifiers, with 6144 transition records. These are implementation checks, not statistical superiority or robot validation. Targeted test outcomes are saved separately in test_results.txt.

Retain this as a research unit test and falsification asset. Do not declare RA-L readiness or start large robot experiments from this result. The next substantive gate is a nondegenerate separation under matched timing/information, or a genuinely new computable structural result. Artificially early identification deadlines alone are insufficient.

Files: partial_delay_gate.py, test_partial_delay_gate.py, results/partial_delay_gate/{summary.json,trajectories.csv,test_results.txt}. No new literature originality certification was performed in this step.
"""
    (report/'PARTIAL_DELAY_GATE_REPORT.md').write_text(zh,encoding='utf8')
    (report/'PARTIAL_DELAY_GATE_REPORT_EN.md').write_text(en,encoding='utf8')

if __name__=='__main__': run(Path(__file__).resolve().parent)
