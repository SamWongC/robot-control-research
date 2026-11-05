"""Evidence-linked topic review and a two-page English advisor brief.

No experiments are rerun and no historical research outputs are modified.
"""
from pathlib import Path
import hashlib,json,re
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parent
REPORT=ROOT/'report'
OUT=ROOT/'results'/'topic_review_2026-11-04'

SOURCES=[
 {'id':'P1','year':2010,'title':'Design of Affine Controllers via Convex Optimization',
  'url':'https://stanford.edu/~boyd/papers/pdf/affine_contr.pdf',
  'access':'Full text accessible; relevant sections II-V examined; proofs not independently reproduced.',
  'locator':'PDF pp.3-6, sections II-V; worst-case problem (7), convex reformulation (16).',
  'finding':'Causal affine output feedback and worst-case convex synthesis are established.',
  'difference':'Does not establish the exact unknown-delay task-preview frontier of this project.'},
 {'id':'P2','year':2014,'title':'Input design for guaranteed fault diagnosis using zonotopes',
  'url':'https://web.mit.edu/braatzgroup/input_design_for_guaranteed_fault_diagnosis_using_zonotopes.pdf',
  'access':'Full text accessible; introduction and sections 2-4 examined.',
  'locator':'Automatica 50:1580-1589; sections 2-4, reachable output sets and separating inputs.',
  'finding':'Bounded-error separating inputs are optimized with control-impact considerations.',
  'difference':'Not a proof of our exact numerical deadline/precision boundaries.'},
 {'id':'P3','year':2016,'title':'Closed-loop input design for guaranteed fault diagnosis using set-valued observers',
  'url':'https://web.mit.edu/braatzgroup/Raimondo_Automatica_2016.pdf',
  'access':'Full text accessible; sections 3-4 and relevant proof/constraints examined.',
  'locator':'PDF pp.3-5, minimum separation horizon, eqs.(15)-(20), Theorem 1, Algorithm 1.',
  'finding':'Minimum separation horizons, general polytopic uncertainties and measurement-updated input design are established.',
  'difference':'Minimum diagnosis time is not the same optimization as task-recovery preview time.'},
 {'id':'P4','year':2014,'title':'Model Predictive Control Combined with Model Discrimination and Fault Detection',
  'url':'https://skoge.folk.ntnu.no/prost/proceedings/ifac2014/media/files/1342.pdf',
  'access':'Full text accessible; sections 3-4, feasibility example and conclusion examined.',
  'locator':'PDF pp.3-4, eqs.(11)-(14), Fig.1 and soft discrimination treatment.',
  'finding':'Combining tracking and discrimination, including feasibility loss, predates this project.',
  'difference':'Its formulation is not identical to our rate-bounded delayed-actuator problem.'},
 {'id':'P5','year':2005,'title':'Finite Horizon Control Design for Optimal Model Discrimination',
  'url':'https://groups.csail.mit.edu/mers/papers/Blackmore_Williams_CDCECC05.pdf',
  'access':'Full text accessible; model assumptions, constraint treatment and discussion examined.',
  'locator':'PDF p.2 Gaussian assumptions; pp.5 and 8 expected-state task constraints and limitations.',
  'finding':'Task-constrained discrimination is an old problem family.',
  'difference':'Expected-state/Gaussian statements are not our all-realizations bounded-noise guarantees.'},
 {'id':'P6','year':2019,'title':'MPC with active learning for stochastic systems with structural model uncertainty: Online model discrimination',
  'url':'https://static1.squarespace.com/static/5d4488dc0d24df0001719b1f/t/5d59c15afd93c4000193886c/1566163294489/CACE_2019_1.pdf',
  'access':'Reopened full text; sections 2-4 and baseline comparison passages examined.',
  'locator':'PDF pp.2-4 active/passive value and model hypotheses; section 5.3 baseline definitions.',
  'finding':'The value of active versus passive learning depends on task and uncertainty.',
  'difference':'Stochastic Bayesian formulation differs from bounded-error certification.'},
 {'id':'P7','year':2026,'title':'Robust Data-Driven Output Feedback for Systems With Unknown Input Delays',
  'url':'https://arxiv.org/html/2611.00841v1',
  'access':'Reopened preprint v1; assumption paragraph and Theorem 3 examined.',
  'locator':'Equation-error bound assumption; Theorem 3 / eq.(19).',
  'finding':'Compatible unknown delays can share a stabilizing controller.',
  'difference':'Synthesis addresses disturbance-free post-collection plants, not our ongoing disturbed endpoint task.'},
 {'id':'P8','year':2026,'title':'Safe, Real-Time Active Model Discrimination and Fault Diagnosis for Nonlinear Systems via Differentiable Reachability',
  'url':'https://arxiv.org/html/2606.19590v1',
  'access':'Reopened preprint v1; sections III-V and result scope examined.',
  'locator':'Section III Problem 2 / eq.(3); section V, consistency relaxed to a separation objective.',
  'finding':'Set-based discrimination with nonlinear dynamics and robust constraints is already an active research area.',
  'difference':'Its separating objective relaxation is not a certificate of every task-preview boundary.'}
]

def link(i):
    s=next(s for s in SOURCES if s['id']==i)
    return f"[{i}: {s['title']}]({s['url']})"

def create_reports():
    OUT.mkdir(parents=True,exist_ok=True);REPORT.mkdir(exist_ok=True)
    cells=json.loads((ROOT/'results'/'causal_preview_certificate'/'cells.json').read_text())
    audit=json.loads((ROOT/'results'/'causal_preview_certificate'/'audit.json').read_text())
    sourcehash={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in (
        'first_action_scan.py','baseline_sensitivity.py','causal_preview_certificate.py')}
    rawlog=(ROOT/'causal_preview_tests.log').read_bytes()
    testlog=rawlog.decode('utf-16' if rawlog.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig')
    tests=re.search(r'Ran (\d+) tests',testlog)
    facts={'grid_points':len(cells),'certified':sum(c['classification']=='certified_policy' for c in cells),
        'unresolved':sum(c['classification']=='unresolved' for c in cells),
        'implementation_episodes':audit['episodes_audited'],'regression_tests':int(tests.group(1)) if tests else None}
    evidence={'date':'2026-11-04','decision':'NO_GO_CURRENT_RA_L_MANUSCRIPT_CONDITIONAL_PIVOT',
        'scope':'Bounded primary-source review of the current claims, not exhaustive novelty certification.',
        'new_experiments_run':False,'proofs_of_external_papers_independently_reproved':False,
        'queries':['affine disturbance feedback robust constrained control',
            'affine output feedback purified outputs convex synthesis',
            'active model discrimination task constraints minimum horizon',
            'dual adaptive MPC active versus passive learning',
            'unknown input delay compatible models common controller',
            'task-preserving partial delay discrimination'],
        'sources':SOURCES,'local_code_hashes':sourcehash,'local_facts':facts,
        'access_limits':[
            'Harirchi et al. IFAC 2017 author PDF timed out twice; not treated as full-text evidence.',
            'Heirung et al. 2017 author PDF redirected to a JS-only repository; no new full-text claim.',
            'Previous review DOI 10.1049/cth2.12170 and 10.1016/j.conengprac.2017.03.007 remain incompletely accessed.',
            'No paper was found with the exact local numeric frontier; this does not establish an original general result.']}
    (OUT/'evidence.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    source_zh={
        'P1':'因果仿射输出反馈的最坏情形凸合成已有通用框架。当前创新量策略在辨识完成后属于此类专门化；该文不等于已经证明我们的未知延迟边界。',
        'P2':'有界误差下的分离输入与控制影响已有联合考虑。精确终点任务不同，但不能把“试探不能过度损害控制”作为新思想。',
        'P3':'已有最小区分时域和观测更新后的闭环输入设计。区分时域不等同任务预告；单纯扫描预告长度并不足以构成新算法。',
        'P4':'跟踪、模型区分及可行性损失已有直接先例。其保证假设不同，不把它说成完全解决本项目，但它排除了宽泛的新颖性表述。',
        'P5':'任务约束下的模型区分并非新问题。该文的期望状态与高斯设定不能冒充本项目的有界最坏情形保证。',
        'P6':'主动学习收益随状态、模型不确定性和任务变化已有研究。仅展示主动/被动收益区域不是足够的新贡献。',
        'P7':'保留延迟歧义并共同稳定已有先例。该预印本的采数后无扰动范围不同于持续外扰终点控制；这个区别本身不证明原创。',
        'P8':'非线性、集合模型区分和鲁棒约束已有近期框架。该预印本的分离惩罚不等于完全保证本项目边界，仍是必须比较的近邻。'}
    srczh='\n'.join(f"- {link(s['id'])}：{source_zh[s['id']]} 定位：{s['locator']}" for s in SOURCES)
    srcen='\n'.join(f"- {link(s['id'])}: {s['finding']} {s['difference']} Locator: {s['locator']}" for s in SOURCES)
    zh=f'''# 选题去留审查：当前方案不作为 RA-L 投稿主体

日期：2026-11-04；审查对象为最新命题与策略，不重复原先宽泛选题。结论是研究判断，不是期刊编辑决定或录用概率预测。

## 决定

**保留仓库、实验和可复现基线；停止把当前双积分器方案作为独立 RA-L 论文主体，调整核心贡献后再决定是否继续。** 这不是要求删除已做工作，也不是认定机器人控制方向不适合你。此前过早以 RA-L 作为立项目标；现有证据还不足以支持当前方案的独立研究贡献。

理由有三条：主要合成工具属于已有框架；新得到的边界仍是特定双积分器、任务与策略族的结果；加强被动基线后部分“主动辨识优势”消失，剩余收益又不能解释成更早获得信息。

本次不将“搜索没有找到完全相同标题或数字”作为原创证明。没有证据表明某一篇论文逐项覆盖本项目所有实现，也不需要据此推断存在可发表的新贡献。

## 现有成果的贡献级别

| 结果或候选主张 | 去留判断 | 原因与证据 |
|---|---|---|
| 残差集合保留相容延迟 | 保留为基线，不作创新 | 属于集合成员判别；P2/P3/P8已有一般框架 |
| 首步辨识阈值 0.048 | 保留为专门化引理 | 两假设输出集合的区间分离；数值由当前模型与误差界决定 |
| 非预知未来分支造成动作冲突 | 保留为有效反例 | 纠正了事后可行与因果可保证的混淆，但当前证明是低维线性消元 |
| 创新量反馈 + 多面体对偶 LP | 不作新算法主张 | 辨识后为已知模型的仿射输出反馈与标准鲁棒对偶，见P1 |
| 0.1秒预告、0.3mm容差可行 | 保留为实例结果 | 不是全局最小预告/精度边界，仍有未决点且限定首步策略 |
| 学习/控制应看任务而非一味辨识 | 仅作研究动机 | P4/P5/P6已有直接相关思想，不是独立贡献 |
| 仿真冻结、配对数据、独立审计 | 保留为研究质量证据 | 支持可信度，不替代算法或理论新颖性 |
| 给现有方法增加神经网络或机器人仿真 | 不据此自动立项 | 需要解决新问题或得到非平凡结论；换模块/对象本身不够 |

## 新核查的近邻与边界

下面只简述直接影响判断的内容；原文可访问不代表每个证明均独立重证。F/M范围与访问失败记录在 evidence.json。预印本按公开披露对待，不冒充已同行评审的期刊成果。

{srczh}

其中P1直接削弱当前控制器的新算法主张；P3直接削弱“寻找最小区分时域”这一宽泛主张；P4直接削弱“辨识可能损害控制可行性”作为新发现的表述。这是判断当前稿件 No-Go 的主要证据，而不是因为没有硬件。

## 对当前命题的具体审查

**充分条件。** Hᵀλ=g、λ≥0、hᵀλ+|c|≤1−m 来自鲁棒线性不等式的对偶上界。将噪声和外扰归一化、采用创新量消去过去控制，再合成下三角反馈，构成正确且有用的实现，但目前没有超出标准仿射鲁棒控制的独立结论。把外扰变化率写成额外多面体行也是当前数学模型的结构代入；不是声称每个近邻原代码无需改动就支持它。

**必要条件。** 两条共享观测前缀、未来不同的合法外扰要求不同后续动作，给出因果反例。它比逐样本事后 LP 更正确，值得保留。但 |a|≤0.035 是当前两步任务的特定消元结果，尚未推广到一类机器人、任意延迟集合或一般目标集。

**“最短预告”。** 0.1 s 只在首步保证唯一辨识后控制的限定方案内有相应结论；N=0阻碍针对全因果策略，N=1部分阻碍针对固定首步/保证首步辨识方案，不能合并成全策略精确前沿。48个点中36个数值可行证书、2个未决，不是一个完全刻画的可行集。浮点证书也不是精确机器证明。

**与最初动机的偏差。** 最初想判断何时不必唯一辨识；当前实现却固定发送可区分首步并在k=1唯一辨识，再进入已知延迟分支。它没有实现任务触发、部分区分或保留任务无害歧义的策略。因此不能把尚未实现的动机写进贡献列表。

## 项目证据，而非论文贡献

最新结果包含 {facts['grid_points']} 个设置、{facts['certified']} 个独立浮点支持核验策略、{facts['unresolved']} 个未决点；{facts['implementation_episodes']} 次实现核验、{facts['regression_tests']} 项回归检查通过。这些说明原型可审查，但不能提升为“已达到期刊水平”。

先前0.4 s预告实验中，原被动基线101/128，过程跟踪与软进度被动均128/128；原有完成率优势不稳健。首步扫描中 +0.05 为239/256、+0.1为163/256、原任务首步128/256，但三者均首步辨识；这主要指向动作对后续任务状态与队列的影响。最新证书策略又改变了控制器类别，不能把不同时期的结果拼成一次公平算法对照。

本项目还缺少真实机器人任务动机的参数依据、匹配一般主动模型区分方法的对照、非平凡的一般结果。硬件不是本审查设定的必要门槛，机器人仿真也能作为后续验证；但把双积分器换成机器人不会自动解决创新问题。

## 建议的转向：只有条件继续，不直接立新论文

候选问题：**有限期限机器人任务中的保任务部分延迟区分**。英文工作标题：Task-Preserving Partial Delay Discrimination for Deadline-Constrained Robot Control。这是待核查的候选，不是已确认空白。

改变的不是再找一个固定试探幅值，而是允许多个延迟保留下来：只区分会妨碍任务的假设，并证明剩余信息集仍允许共同的因果后续策略。信息集必须同时记录延迟、候选动作队列、状态与外扰条件；不能把每个模型分别可行误当成共同策略可行，也不能把两两兼容误当成整个候选集合可行。

定义任务可恢复信息集或套用已有鲁棒LP本身也不够。继续的必要门槛是：给出一项不能通过简单代入近邻获得的计算或理论改进，并在信息、因果性和约束完全匹配的强基线下保留收益。该方向仍可能被双重控制、信念空间可达性或一般主动模型区分覆盖，需进一步专门核查。

## 一轮有终点的去留门槛

建议最多再给一个约两周的论证窗口，具体按可投入时间调整，不把它当成发表时间表。只交付以下三项，不继续无限追加小实验：

1. 一页精确问题和候选命题，明确哪项结论不是P1/P3/P4/P8的直接应用；若写不清，停止此论文路线。
2. 一个严格匹配的分离实例：完整区分方法受任务限制，而保留多个候选的共同因果策略仍完成任务；或一个有界误差/复杂度的改进结果。不能仅比较弱开环基线与更强反馈方法。
3. 一个具有可解释期限与约束的机器人任务设计，并获得一次熟悉鲁棒/预测控制者的具体反馈。无须先买硬件，也无须先加神经网络。

如果只能得到已知方法换参数、换模型或固定幅值调优，**终止当前论文核心，保留仓库作为复现/研究原型，转向与硕士论文或实验室具体问题相连的新题**。若门槛满足，再规划机器人验证和投稿。不要在通过门槛前继续用“可发表题目”描述它。

## 给潜在指导者的三个问题

- 部分区分与任务可恢复性的候选命题，是否只是已有鲁棒自适应/双重控制的直接推论？
- 哪个真实机器人任务会在允许的动作/期限内遇到这种信息与控制冲突？
- 在哪些信息条件下，应当使用哪种现成算法作为最强公平基线？

英文两页简报已备好，可由你用于交流；本次没有替你联系任何人。

## 证据与限制

本次是有界的原始文献核查，不是穷尽检索或数学新颖性认证。2017 Harirchi作者PDF访问超时；另一2017作者稿链接重定向到需JS页面，未算全文核查。上轮2021/2017两篇延迟与扰动识别论文完整访问缺口仍存在。没有精确重复当前数字的论文，不代表有新理论。过去实验和哈希保持不变；本次没有重跑实验。

证据：results/topic_review_2026-11-04/evidence.json；英文简报 RESEARCH_DIRECTION_BRIEF_EN.pdf；本报告英文版 TOPIC_GO_NO_GO_REVIEW_2026-11-04_EN.md。
'''
    en=f'''# Topic decision: do not submit the present formulation as a standalone RA-L paper

Review date: 2026-11-04. This is a research judgment about the current claims, not an editorial verdict or acceptance forecast.

## Decision

**Retain the repository and reproducible evidence; stop treating the current double-integrator formulation as the core of an independent RA-L submission. Continue only after changing and justifying the contribution.** Choosing RA-L earlier was premature; the present evidence does not establish an original contribution. No deletion or abandonment of robotics/control as a field is recommended.

The synthesis is largely established machinery, the new frontier remains instance- and policy-class-specific, and stronger passive baselines remove part of the apparent active-identification advantage. No reviewed paper is asserted to duplicate every detail. Conversely, failure to find the same title or numbers does not establish novelty.

## Claim assessment

| Claim | Assessment |
|---|---|
| Delay-candidate consistency LP | Baseline specialization of set membership/model discrimination |
| One-step .048 separation threshold | Useful model/noise-specific lemma; not a general contribution |
| Shared-prefix future-branch obstruction | Valid explanatory counterexample; currently elementary low-dimensional elimination |
| Innovation feedback and polyhedral dual LP | Established affine robust-control construction after identification |
| .1 s preview / .3 mm precision frontier | Instance result, not a global all-policy exact frontier |
| Learning should serve the task | Existing motivation; not by itself a new method |
| Frozen paired tests and independent auditing | Evidence quality, not algorithmic novelty |
| Adding a neural residual or robot simulation | Requires a new problem/result, not automatic novelty |

## Primary-source comparison

The following are short claim locators, not independent re-proofs of all cited results. Accessible full text means relevant core sections were examined, not that every proof was reproduced. Preprints are public prior disclosures rather than assumed journal publications.

{srcen}

P1 is decisive for the controller claim; P3 for broad minimum-discrimination-horizon claims; P4 for the general observation that discrimination can damage feasibility. None is claimed to solve the exact local rate-bounded delay/endpoint problem without adaptation.

## What the current theorem actually adds

The condition H^T lambda=g, lambda>=0, h^T lambda+|c|<=1-m is a robust linear-inequality dual bound. Innovation purification and lower-triangular gains provide an implementable instance. Adding disturbance-rate rows remains a polytopic specialization in our formulation, not a demonstrated new synthesis principle or a claim that every cited implementation directly handles the same correlations.

The two-future obstruction correctly distinguishes hindsight feasibility from causal guarantees. The bound |a|<=.035 still comes from this specific two-step task. It has not become a theorem for a useful general class of robots, delay sets or goals. The .1 s conclusion is restricted to guaranteed first-step identification; the N=0 and N=1 obstruction scopes differ. Unresolved cells remain unresolved, and floating-point support checks are not exact-arithmetic proofs.

There is also a gap between motivation and implementation: the original question allowed harmless delay ambiguity, but the current controller forces a separating first command, identifies a unique delay at k=1, then executes a known-model branch. Task-triggered or partial identification is not implemented and cannot be listed as an existing contribution.

## Project evidence and remaining gaps

The latest experiment has {facts['grid_points']} settings, {facts['certified']} independently checked numerical policies, {facts['unresolved']} unresolved cells, {facts['implementation_episodes']} successful implementation checks and {facts['regression_tests']} passing regression tests. These support reviewability, not publication readiness.

At .4 s preview, the old passive baseline scored 101/128 while tracking/progress passive baselines reached 128/128. In the first-action scan, +.05 scored 239/256, +.1 scored 163/256 and task-generated actions 128/256, with identical first-step identification timing. Action-induced state/queue changes therefore matter. The latest certified policy changes the controller family again; results from different stages cannot be pooled into a single fair algorithm comparison.

The current work lacks a calibrated robotics task, matched general active-discrimination baselines and a nontrivial general result. Hardware is not an absolute gate in this review. A meaningful simulated robot may be sufficient for a later study, but changing the plant alone does not resolve novelty.

## Conditional pivot, not an approved new paper

Provisional question: **Task-Preserving Partial Delay Discrimination for Deadline-Constrained Robot Control.** Allow multiple delays to remain when a common causal task policy is certified; identify only distinctions that threaten task recovery. The information state must include possible delay, pending commands, physical state and disturbance conditions. Separate model feasibility and pairwise compatibility do not establish a common policy for the entire candidate set.

Merely defining task recoverability or reusing a robust LP is insufficient. Progress requires a demonstrably nontrivial theoretical/computational improvement and retained benefits against strong, information-matched causal baselines. Dual control, belief-space reachability and general discrimination may already cover the proposal; this is an unverified candidate gap.

## Bounded continuation gate

Allow at most one further argument-building cycle of roughly two weeks, adjustable to available time, not a publication timetable:

1. Write a precise candidate proposition and identify what is not a direct application of P1/P3/P4/P8. Stop this paper route if that distinction cannot be stated.
2. Supply a matched separation example or a bounded-error/complexity improvement. Full identification should be task-limited while a common causal policy retaining multiple models succeeds; do not manufacture gains by comparing weak open-loop with stronger feedback.
3. Specify one robot task with meaningful deadlines/constraints and obtain concrete feedback from someone familiar with robust/predictive control. Hardware purchases and neural additions are unnecessary at this stage.

If the outcome is only parameter tuning or a new plant for existing methods, terminate the current paper core and preserve the code as a reproduction/research prototype. Seek a problem linked to a thesis or laboratory task. If the gate succeeds, plan robotics validation before discussing a submission.

## Questions for a potential advisor

Is the proposed partial-discrimination/recoverability statement a direct corollary of existing dual/adaptive control? Which robot task makes the conflict important under realistic limits? What is the strongest baseline with exactly matched information?

A two-page English brief is provided for the user's own discussions; no messages were sent to anyone.

## Limits and artifacts

Bounded primary-source review, not exhaustive novelty certification. The Harirchi 2017 author PDF timed out; another 2017 author manuscript redirected to a JS-only repository. The previous 2021/2017 delay/disturbance full-text gaps remain. No experiments were rerun or historical hashes changed. Evidence: results/topic_review_2026-11-04/evidence.json.
'''
    (REPORT/'TOPIC_GO_NO_GO_REVIEW_2026-11-04.md').write_text(zh,encoding='utf-8')
    (REPORT/'TOPIC_GO_NO_GO_REVIEW_2026-11-04_EN.md').write_text(en,encoding='utf-8')
    return facts

def create_brief(facts):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether
    from reportlab.lib.enums import TA_LEFT
    from pypdf import PdfReader
    path=REPORT/'RESEARCH_DIRECTION_BRIEF_EN.pdf'
    styles={'title':ParagraphStyle('title',fontName='Helvetica-Bold',fontSize=20,leading=24,textColor=colors.HexColor('#173D49'),spaceAfter=9),
        'sub':ParagraphStyle('sub',fontName='Helvetica',fontSize=9,leading=12,textColor=colors.HexColor('#53616A'),spaceAfter=12),
        'head':ParagraphStyle('head',fontName='Helvetica-Bold',fontSize=11,leading=14,textColor=colors.HexColor('#173D49'),spaceBefore=10,spaceAfter=5),
        'body':ParagraphStyle('body',fontName='Helvetica',fontSize=9.4,leading=13,spaceAfter=7),
        'small':ParagraphStyle('small',fontName='Helvetica',fontSize=8,leading=10.5,spaceAfter=4)}
    pages=[
        [('title','Research direction review'),('sub','Independent robotics/control project | 4 November 2026 | Discussion brief, not a paper abstract'),
         ('head','Decision: retain the project; change the paper contribution'),
         ('body','Do not submit the present double-integrator study as a standalone RA-L research contribution. Preserve its code, counterexamples and numerical certificates. Continue only if a distinct, generalizable claim survives a focused novelty check.'),
         ('head','Current question and evidence'),
         ('body','Unknown fixed input delay (0 or 1 sample), bounded changing disturbances and sensor errors can make an informative action damage a deadline-constrained task. A fixed separating first action is followed by causal innovation-feedback control. The task uses dt=0.05 s and a two-step endpoint after preview.'),
         ('table',[['Preview','Position tolerance','Current finding'],['0.05 s','0.2 mm','Fixed-probe causal obstruction'],['0.05 s','0.2375 / 0.25 mm','Unresolved'],['0.05 s','0.3 mm','Numerically verified causal policy'],['0.10 s','0.2 mm','Numerically verified causal policy']]),
         ('body',f"The latest study checks 48 settings, 36 numerical policies and {facts['implementation_episodes']} implementation cases, with {facts['regression_tests']} passing tests. Continuous uncertainty supports are independently optimized. This is floating-point certificate evidence, not an exact-arithmetic proof or a global minimum-preview theorem."),
         ('head','Why the current contribution is insufficient'),
         ('body','Affine causal output-feedback convex synthesis is established [1]. Minimum discrimination horizons and closed-loop input design already exist [2]. Tracking/discrimination feasibility conflicts were studied previously [3]. Our elementary bounds and precision map specialize these ideas to one small plant.'),
         ('body','Stronger passive baselines remove the old 0.4 s probing advantage. In the short-preview scan, nonzero actions identify at the same time but complete different numbers of tasks. This points to state/queue compatibility, not earlier information.'),
         ('head','What must not be claimed'),
         ('body','No global all-policy feasibility frontier, no new affine-control framework, no implemented task-triggered/partial identification, and no confirmed RA-L novelty. Robot simulation or a neural residual alone would not establish a contribution.')],
        [('title','Candidate pivot and decision gate'),('sub','Working hypothesis only | No confirmed literature gap'),
         ('head','Task-preserving partial delay discrimination'),
         ('body','Can a robot retain several delay explanations, certify a common causal task continuation, and probe only when that continuation would otherwise be lost? Unlike the current fixed-probe implementation, this question does not require a unique delay whenever the task can tolerate ambiguity.'),
         ('body','The information set must include possible delay, pending commands, physical state and disturbance conditions. Individual-model feasibility is not common-policy feasibility. Pairwise compatible hypotheses need not make the whole candidate set compatible.'),
         ('head','One bounded continuation cycle'),
         ('body','1. State a precise proposition and explain what is not a direct application of existing affine, diagnosis or dual-control methods. A definition or another parameter sweep is insufficient.'),
         ('body','2. Establish a nontrivial recoverability/computation result against matched causal baselines: common robust control, general active discrimination, passive adaptation and an oracle reference. Avoid artificial gains from unequal information or feedback classes.'),
         ('body','3. Specify one meaningful robot task and discuss the proposition with a robust/predictive-control researcher before expanding implementation. Roughly two weeks is a stop/go planning limit, not a publication forecast.'),
         ('head','Stop rule'),
         ('body','If only plant substitution, fixed-action tuning or standard LP reuse remains, end this paper route. Retain the repository as a research prototype and seek a thesis/laboratory problem. If a defensible gap survives, then plan a robotics validation study.'),
         ('head','Questions for an advisor'),
         ('body','Is partial discrimination already a direct consequence of existing theory? Which robot deadline/constraint makes it important? Which available method is the strongest information-matched baseline?'),
         ('head','Selected primary references'),
         ('small','[1] Skaf and Boyd, IEEE TAC, 2010. <link href="https://stanford.edu/~boyd/papers/pdf/affine_contr.pdf" color="#126A80">Affine controller synthesis</link>.'),
         ('small','[2] Raimondo et al., Automatica, 2016. <link href="https://web.mit.edu/braatzgroup/Raimondo_Automatica_2016.pdf" color="#126A80">Closed-loop guaranteed diagnosis</link>.'),
         ('small','[3] Cheong and Manchester, IFAC, 2014. <link href="https://skoge.folk.ntnu.no/prost/proceedings/ifac2014/media/files/1342.pdf" color="#126A80">MPC with discrimination and feasibility</link>.'),
         ('small','[4] <link href="https://arxiv.org/html/2606.19590v1" color="#126A80">Safe nonlinear active discrimination</link>, arXiv:2606.19590v1 (2026 preprint). Separate assumptions and relaxation scope must be respected.')]
    ]
    story=[];md=[]
    for index,parts in enumerate(pages):
        if index:story.append(PageBreak());md.append('\n---\n')
        for kind,value in parts:
            if kind=='table':
                rows=[[Paragraph(escape(x),styles['small']) for x in row] for row in value]
                t=Table(rows,colWidths=[70,120,290],hAlign='LEFT')
                t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E7F0F2')),
                    ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),
                    ('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),
                    ('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#8CA8AF')),
                    ('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#DCE4E7'))]))
                story.extend([t,Spacer(1,9)]);md.extend([' | '.join(row) for row in value])
            else:
                story.append(Paragraph(value,styles[kind]));md.append(('# ' if kind=='title' else '## ' if kind=='head' else '')+re.sub('<[^>]+>','',value)+'\n')
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor('#B8C9CD'));canvas.line(42,42,A4[0]-42,42)
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#53616A'))
        canvas.drawString(42,28,'Research decision brief | Not a novelty certification')
        canvas.drawRightString(A4[0]-42,28,f'{doc.page} / 2')
    SimpleDocTemplate(str(path),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=35,bottomMargin=54).build(story,onFirstPage=footer,onLaterPages=footer)
    reader=PdfReader(str(path));assert len(reader.pages)==2,f'Expected 2 pages, got {len(reader.pages)}'
    assert all(len(p.extract_text())>500 for p in reader.pages)
    (REPORT/'RESEARCH_DIRECTION_BRIEF_EN.md').write_text('\n'.join(md),encoding='utf-8')
    write={'pdf_pages':2,'pdf_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'decision':'Retain research assets; no-go for the current standalone RA-L manuscript; conditional contribution pivot.',
        'new_experiments_run':False,'source_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (OUT/'artifact_checks.json').write_text(json.dumps(write,indent=2),encoding='utf-8')
    print(json.dumps(write,indent=2))

if __name__=='__main__':create_brief(create_reports())
