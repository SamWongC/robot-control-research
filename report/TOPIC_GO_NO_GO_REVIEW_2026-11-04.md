# 选题去留审查：当前方案不作为 RA-L 投稿主体

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

- [P1: Design of Affine Controllers via Convex Optimization](https://stanford.edu/~boyd/papers/pdf/affine_contr.pdf)：因果仿射输出反馈的最坏情形凸合成已有通用框架。当前创新量策略在辨识完成后属于此类专门化；该文不等于已经证明我们的未知延迟边界。 定位：PDF pp.3-6, sections II-V; worst-case problem (7), convex reformulation (16).
- [P2: Input design for guaranteed fault diagnosis using zonotopes](https://web.mit.edu/braatzgroup/input_design_for_guaranteed_fault_diagnosis_using_zonotopes.pdf)：有界误差下的分离输入与控制影响已有联合考虑。精确终点任务不同，但不能把“试探不能过度损害控制”作为新思想。 定位：Automatica 50:1580-1589; sections 2-4, reachable output sets and separating inputs.
- [P3: Closed-loop input design for guaranteed fault diagnosis using set-valued observers](https://web.mit.edu/braatzgroup/Raimondo_Automatica_2016.pdf)：已有最小区分时域和观测更新后的闭环输入设计。区分时域不等同任务预告；单纯扫描预告长度并不足以构成新算法。 定位：PDF pp.3-5, minimum separation horizon, eqs.(15)-(20), Theorem 1, Algorithm 1.
- [P4: Model Predictive Control Combined with Model Discrimination and Fault Detection](https://skoge.folk.ntnu.no/prost/proceedings/ifac2014/media/files/1342.pdf)：跟踪、模型区分及可行性损失已有直接先例。其保证假设不同，不把它说成完全解决本项目，但它排除了宽泛的新颖性表述。 定位：PDF pp.3-4, eqs.(11)-(14), Fig.1 and soft discrimination treatment.
- [P5: Finite Horizon Control Design for Optimal Model Discrimination](https://groups.csail.mit.edu/mers/papers/Blackmore_Williams_CDCECC05.pdf)：任务约束下的模型区分并非新问题。该文的期望状态与高斯设定不能冒充本项目的有界最坏情形保证。 定位：PDF p.2 Gaussian assumptions; pp.5 and 8 expected-state task constraints and limitations.
- [P6: MPC with active learning for stochastic systems with structural model uncertainty: Online model discrimination](https://static1.squarespace.com/static/5d4488dc0d24df0001719b1f/t/5d59c15afd93c4000193886c/1566163294489/CACE_2019_1.pdf)：主动学习收益随状态、模型不确定性和任务变化已有研究。仅展示主动/被动收益区域不是足够的新贡献。 定位：PDF pp.2-4 active/passive value and model hypotheses; section 5.3 baseline definitions.
- [P7: Robust Data-Driven Output Feedback for Systems With Unknown Input Delays](https://arxiv.org/html/2611.00841v1)：保留延迟歧义并共同稳定已有先例。该预印本的采数后无扰动范围不同于持续外扰终点控制；这个区别本身不证明原创。 定位：Equation-error bound assumption; Theorem 3 / eq.(19).
- [P8: Safe, Real-Time Active Model Discrimination and Fault Diagnosis for Nonlinear Systems via Differentiable Reachability](https://arxiv.org/html/2606.19590v1)：非线性、集合模型区分和鲁棒约束已有近期框架。该预印本的分离惩罚不等于完全保证本项目边界，仍是必须比较的近邻。 定位：Section III Problem 2 / eq.(3); section V, consistency relaxed to a separation objective.

其中P1直接削弱当前控制器的新算法主张；P3直接削弱“寻找最小区分时域”这一宽泛主张；P4直接削弱“辨识可能损害控制可行性”作为新发现的表述。这是判断当前稿件 No-Go 的主要证据，而不是因为没有硬件。

## 对当前命题的具体审查

**充分条件。** Hᵀλ=g、λ≥0、hᵀλ+|c|≤1−m 来自鲁棒线性不等式的对偶上界。将噪声和外扰归一化、采用创新量消去过去控制，再合成下三角反馈，构成正确且有用的实现，但目前没有超出标准仿射鲁棒控制的独立结论。把外扰变化率写成额外多面体行也是当前数学模型的结构代入；不是声称每个近邻原代码无需改动就支持它。

**必要条件。** 两条共享观测前缀、未来不同的合法外扰要求不同后续动作，给出因果反例。它比逐样本事后 LP 更正确，值得保留。但 |a|≤0.035 是当前两步任务的特定消元结果，尚未推广到一类机器人、任意延迟集合或一般目标集。

**“最短预告”。** 0.1 s 只在首步保证唯一辨识后控制的限定方案内有相应结论；N=0阻碍针对全因果策略，N=1部分阻碍针对固定首步/保证首步辨识方案，不能合并成全策略精确前沿。48个点中36个数值可行证书、2个未决，不是一个完全刻画的可行集。浮点证书也不是精确机器证明。

**与最初动机的偏差。** 最初想判断何时不必唯一辨识；当前实现却固定发送可区分首步并在k=1唯一辨识，再进入已知延迟分支。它没有实现任务触发、部分区分或保留任务无害歧义的策略。因此不能把尚未实现的动机写进贡献列表。

## 项目证据，而非论文贡献

最新结果包含 48 个设置、36 个独立浮点支持核验策略、2 个未决点；834 次实现核验、55 项回归检查通过。这些说明原型可审查，但不能提升为“已达到期刊水平”。

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
