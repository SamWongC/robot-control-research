# Historical research log

Archived development narrative. Earlier next steps are superseded by README.md and the final closed-loop report. No paper acceptance or affiliation is implied.

# RA-L research project

工作题目与研究边界见 [PROJECT_CHARTER.md](PROJECT_CHARTER.md)。

## 当前阶段

最小实验：一维双积分运动系统，比较无输入延迟、固定输入延迟、已知延迟补偿。采用有限时域线性二次 MPC，无输入和状态约束。已知延迟通过动作队列扩展状态处理；不是未知延迟识别算法，更不是待投稿方法。

这个实验用于检查时序、基线和结果保存。尚未实现倒立摆、四旋翼、时变延迟、学习模型、置信度控制或安全保证。固定延迟没有包冲突；未来时变网络队列必须另行定义并测试。

## 运行

建议 Python 3.12，使用项目本地虚拟环境。PowerShell，工作目录为 `C:\codex-workspace\RA-L`：

```powershell
.\.venv\Scripts\python.exe -m unittest -v
.\.venv\Scripts\python.exe experiment.py
```

若在其他电脑重新建立环境：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 输出

- `results/minimal/delay_comparison.png`：轨迹、速度、实际执行输入。
- `results/minimal/*.csv`：每一步转移前状态、发送输入和实际输入。
- `results/minimal/summary.json`：参数、环境、代码哈希和指标。

控制周期 0.05 s，预测时域 40 步，运行 20 s，延迟 6 步（0.30 s），位置目标 1 m。所有工况初始状态及队列相同，无扰动、无噪声、无随机性。普通控制器看不到队列，已知延迟参考方法可访问其确定的待执行动作。RMSE 包含初始瞬态。

## 下一里程碑

1. 精读紧邻文献，建立延迟假设、信息条件、置信度与控制机制的比较表。
2. 加入受约束 MPC 与倒立摆，确认已知延迟基线足够强。
3. 明确定义时变延迟队列，增加到达冲突、保持、过期包测试。
4. 验证延迟与外扰混淆现象，再决定候选识别与学习模型。

不从这个简单实验推断论文创新性或实际机器人性能。

## 实验二：延迟假设错误

已完成受输入约束的 MPC 五组延迟假设对比。参见 [实验报告](report/DELAY_MISMATCH_REPORT.md)。运行命令：.\.venv\Scripts\python.exe delay_mismatch.py。完整依赖见 requirements-lock.txt。

## 实验三：外扰与延迟识别

已完成四组外扰/无外扰、已知延迟/在线估计对照。[中文报告](report/DISTURBANCE_IDENTIFICATION_REPORT.md) · [English report](report/DISTURBANCE_IDENTIFICATION_REPORT_EN.md)。运行：.\.venv\Scripts\python.exe disturbance_identification.py。数据与三张图位于 results/disturbance_identification。测试记录：identification_tests.log。

## 实验一独立报告

[中文报告](report/MINIMAL_EXPERIMENT_REPORT.md) · [English report](report/MINIMAL_EXPERIMENT_REPORT_EN.md)。根据已保存的原始结果整理，包含系统、参数、三组对照、指标和限制。

## 实验四：联合延迟与外扰估计

已完成六类扰动、五种控制模式，共 30 组仿真。[中文报告](report/JOINT_ESTIMATION_REPORT.md) · [English report](report/JOINT_ESTIMATION_REPORT_EN.md) · [文献与基线表](LITERATURE_BASELINES.md)。运行：.\.venv\Scripts\python.exe joint_estimation.py。原始数据、指标与图表位于 results/joint_estimation，测试记录为 joint_estimation_tests.log。

## 实验五：可辨识性与激励

已完成四类输入、三类扰动、三档速度测量噪声，共 252 次成对回放。[中文报告](report/IDENTIFIABILITY_REPORT.md) · [English report](report/IDENTIFIABILITY_REPORT_EN.md) · [文献与推导](LITERATURE_IDENTIFIABILITY_NOTES.md)。运行：.\.venv\Scripts\python.exe identifiability_experiment.py。结果位于 results/identifiability，测试记录为 identifiability_tests.log。

## 报告保存约定

所有新生成的中英文实验报告统一保存到 `report/`，原始数据、图表和参数仍放在 `results/`。旧报告已位于 report；相关生成器与链接已同步修正。历史结果中的源代码哈希对应当时执行版本；本次旧生成器仅修改报告输出位置，未重跑旧实验。

## 实验六：冻结候选集合规则

[中文报告](report/CANDIDATE_SETS_REPORT.md) · [English report](report/CANDIDATE_SETS_REPORT_EN.md)。程序 candidate_sets.py 分 development/test/render 三个阶段；规则在测试前冻结。数据、阈值、清单与图表位于 results/candidate_sets；验证记录 candidate_sets_tests.log。

## 2026-11-04 创新性审查

[中文审查报告](report/NOVELTY_REVIEW_2026-11-04.md) · [English review](report/NOVELTY_REVIEW_2026-11-04_EN.md)。当前广义题目尚未确认原创，六组实验属于基线与失效分析。最新近邻已经覆盖保留相容延迟并共同控制、主动模型区分等思路。下一阶段先通过具体命题与匹配基线核查创新；不将候选方向等同于已确认贡献。两篇老近邻完整正文仍待补齐，证据记录见 results/literature_review_2026-11-04/evidence.json。

## 2026-11-04：共同控制器复现与收敛后的研究计划

已完成近邻论文 V-B / 式 (19) 的独立协议级复现：三个相容固定延迟模型使用同一增益收敛，数值 LMI 经独立重建核验。此项属于已有方法基线，不是本项目创新，也不是作者原始随机数据的逐项数值复刻。

- [中文复现报告](report/COMMON_DELAY_REPRODUCTION_REPORT.md) · [English reproduction report](report/COMMON_DELAY_REPRODUCTION_REPORT_EN.md)
- [中文一页研究计划](report/RESEARCH_PROPOSAL_ZH.md) · [English research proposal](report/RESEARCH_PROPOSAL_EN.md)
- 程序：reproduce_common_delay.py；报告生成器：summarize_common_delay.py；依赖：requirements-reproduction-lock.txt。
- 原始数据、控制器、证书矩阵和图：results/common_delay_reproduction/；完整回归 29 项通过，日志 common_delay_full_tests.log。

当前下一里程碑以本节研究计划为准：先精确定义变化外扰下的任务驱动辨识问题，草拟候选兼容/分离与任务触发命题，再建立“歧义无害 / 候选冲突”两组最小对照。先核查其与现有主动模型区分方法的差异，不直接将增加模块视作创新。

## 2026-11-04：任务相关歧义的精确定义与两个构造场景

- [中文问题定义](report/TASK_AMBIGUITY_PROBLEM_DEFINITION.md) · [English definition](report/TASK_AMBIGUITY_PROBLEM_DEFINITION_EN.md)
- [中文验证报告](report/TASK_AMBIGUITY_SCENARIOS_REPORT.md) · [English report](report/TASK_AMBIGUITY_SCENARIOS_REPORT_EN.md)
- 程序 task_ambiguity_scenarios.py；生成器 summarize_task_ambiguity.py；数据和图 results/task_ambiguity_scenarios/。
- 六步零输入历史下 d=0/1 均相容。保持任务存在共同鲁棒零输入；两步短期限移动任务各模型分别鲁棒可行，但必要第一动作区间分离。支持函数 LP、手算必要条件、物理递推及 96 次组合检查交叉核验。完整 33 项测试通过，见 task_ambiguity_tests.log。
- 这些构造例子不构成新辨识算法或创新证明；变化率约束在终点极值上不活跃。冲突到达后可能已无法补救，下一阶段应引入目标预告时间，验证获取信息是否能恢复任务可行性，并比较被动反馈。

## 2026-11-04：预告辨识与任务恢复实验

- [中文报告](report/PREVIEW_IDENTIFICATION_REPORT.md) · [English report](report/PREVIEW_IDENTIFICATION_REPORT_EN.md)
- 代码 preview_identification.py；审计 audit_preview_identification.py；报告生成器 summarize_preview_identification.py；测试 test_preview_identification.py。
- 0/1/2/4/8 步预告，四种方法，37 条配对外扰/噪声轨迹、两个真实延迟，共 1480 次。保存目录 results/preview_identification/ 包括配置、输入记录、完整轨迹、逐案例指标、汇总、图与独立审计。
- 正预告固定试探在首步后均正确辨识，但 1 步预告仅 49/74 次完成任务；2/4/8 步均 74/74。任务自身动作亦能辨识，task_only 在 2/4 步也为 74/74。8 步下该基线因迟滞动作等限制下降，不能解释为预告本质有害或所有被动策略不可行。
- 全部 7400 步物理转移、队列连续性和任务开始状态独立审计通过，无状态或指令队列重置。完整 38 项测试通过，日志 preview_identification_tests.log。
- 以上为有限开发案例；0.1 s 是已测试点中 probe 全部成功的最短预告，不是普适保证。下一阶段检查任务动作的信息充分性、可恢复任务集合及被动规划器时序/代价敏感性。

## 2026-11-04：被动基线敏感性与冻结后独立测试

- [中文报告](report/BASELINE_SENSITIVITY_REPORT.md) · [English report](report/BASELINE_SENSITIVITY_REPORT_EN.md)
- baseline_sensitivity.py 分 development / freeze / test 阶段；analyze_baseline_sensitivity.py 审计与报告；test_baseline_sensitivity.py 为新增针对性检查。
- 旧开发轨迹比较 8 个代价配置，共 2960 次；按预先声明规则冻结 legacy / lex_energy / track_1 / progress_0.5，再生成 64 条新轨迹，分别配两个延迟，与对应试探版本及 oracle 比较，共 5760 次独立测试。
- 0.4 s 下原始被动 101/128，过程跟踪及软进度被动均 128/128；专门试探的完成率优势在这两类基线中消失。0.05 s 下各被动 64/128、试探 81/128，但都在 k=1 辨识，不能将差异解释成更早获取信息。
- 保存配置/源代码/依赖哈希、冻结选择、逐步轨迹、逐案例指标、成本、辨识时间、配对差异与数值边界诊断于 results/baseline_sensitivity/。全部 43600 步独立审计通过，完整 43 项测试通过，日志 baseline_sensitivity_tests.log。
- 主成功阈值未调整。开发中 18 次极小数值边界失败另行列出，独立测试中这种情况为零。无实际准备边界违反或准备硬约束求解失败。
- 当前证据不确认专门主动辨识的必要性或创新。下一阶段应区分首步动作对任务可恢复性的影响与信息可用时刻，避免将基线迟滞或动作形状差异误判为信息收益。冻结测试结果不得用于调参后再次宣称独立验证。

## 2026-11-04：首步动作区域、因果限制与新轨迹验证

- [中文报告与条件推导](report/FIRST_ACTION_SCAN_REPORT.md) · [English report](report/FIRST_ACTION_SCAN_REPORT_EN.md)
- 代码 first_action_scan.py 分 scan / freeze / test；analyze_first_action_scan.py 独立审计、因果分支推导与绘图；test_first_action_scan.py 为七项针对性检查。
- 扫描 107 个准备边界允许的动作，7918 次开发仿真；冻结 +0.05 m/s² 后，在 128 条新轨迹、两个延迟、四个规则下执行 1024 次新测试。各非零规则均首步辨识，任务完成分别为原任务控制 128/256、+0.1 为 163/256、冻结 +0.05 为 239/256。后续控制器完全相同，未重置状态或队列。
- 名义已知延迟可恢复与保证首步辨识的联合动作区域为 [-0.11,-0.048)∪(0.048,0.11]，不等于共同反馈或鲁棒可行区域。
- 同前缀、不同未来的合法外扰分支证明：即使初态精确为零、已知 d=1 且精确观测，保证硬期限任务仍必要 |a|≤0.035；它与当前测量盒模型的保证辨识动作 |a|>0.048 不相交。本例不能同时保证两者。+0.05 的两未来分支要求互不相容的后续动作，事后逐条可行不能代替因果保证。
- 数据、区域图、冻结哈希、事后与鲁棒可行性诊断、因果反例及全部原始轨迹位于 results/first_action_scan/。26826 步独立审计通过；完整 50 项测试通过，记录 first_action_scan_tests.log。
- 本轮机制结果尚不等于论文创新。若追求保证，需要调整预告/期限/容差并纳入因果未来分支；冻结测试不可用于调参后继续宣称独立确认。

## 2026-11-04：因果反馈充分条件与预告/精度边界

- [中文命题与实验报告](report/CAUSAL_PREVIEW_CERTIFICATE_REPORT.md) · [English report](report/CAUSAL_PREVIEW_CERTIFICATE_REPORT_EN.md)
- 代码 causal_preview_certificate.py 分 build / validate；analyze_causal_preview_certificate.py 独立核验实际执行映射、审计并生成三类地图；test_causal_preview_certificate.py 为五项针对性检查。
- 固定首步 +0.05，首步观测后唯一辨识延迟，执行候选分支的仿射创新量反馈。完整连续外扰幅值/变化率和噪声盒用于鲁棒对偶 LP；所有保存策略均重新求最坏支持点核验，不以仿真完成率替代保证条件。
- 原 0.2 mm 位置精度、0.003 m/s 速度精度下，0.1 s 预告已有充分策略；保持 0.05 s 预告，0.3 mm 位置容差已有充分策略。0.2375/0.25 mm 两点保留为未决。地图共 48 点：36 个独立数值核验策略、10 个作用域明确的解析阻碍、2 个未决。
- 0 预告的阻碍针对全因果策略；1 步预告的红色区域针对固定首步/首步保证辨识方案，不能外推成所有未知延迟反馈策略不可行。0.1 s 不是已证明的全策略全局最短预告。
- 证书额外覆盖 |p0|≤2e-5 m、|v0|≤2e-4 m/s 的物理初态扰动，明确包含原零初态但不混同测量误差界；控制器只读取观测前缀和发送历史。834 次新随机与最坏支持点验证全通过，3642 步独立审计通过；完整 55 项测试通过，日志 causal_preview_tests.log。
- 配置、策略 NPZ、支持点、冻结清单、逐案例验证、哈希、审计与地图位于 results/causal_preview_certificate/。数值证书是浮点支持核验，不是精确算术机器证明。本轮为标准鲁棒反馈构造，尚未确认期刊创新。

## 2026-11-04：选题去留审查决定

- [中文审查](report/TOPIC_GO_NO_GO_REVIEW_2026-11-04.md) · [English review](report/TOPIC_GO_NO_GO_REVIEW_2026-11-04_EN.md)
- [英文研究简报（Markdown；公开副本未包含PDF）](report/RESEARCH_DIRECTION_BRIEF_EN.md)
- 决定：保留研究资产，当前双积分器/固定首步辨识/仿射鲁棒反馈方案不作为独立 RA-L 投稿主体；调整并验证独立贡献后再继续。
- 新核查覆盖仿射因果输出反馈、保证模型区分、最小区分时域、跟踪与区分的可行性冲突等八个主要原始来源；区别精确问题不同与方法独立新颖性，记录了未完整访问的来源。
- 条件转向候选为保任务的部分延迟区分，尚未确认文献空白。若只能做参数调优或模型替换，应停止该论文核心；不再无上限增加小实验。完整继续/停止门槛见报告。
- 来源、定位、访问限制及本地代码哈希保存在 results/topic_review_2026-11-04/evidence.json，PDF 页数及双页视觉检查保存在 artifact_checks.json。生成器 topic_go_no_go_review.py。未重跑实验、未修改历史源代码或结果，也未联系任何人。

## 2026-11-04：三延迟部分辨识门槛试验

- [中文报告](report/PARTIAL_DELAY_GATE_REPORT.md) · [English report](report/PARTIAL_DELAY_GATE_REPORT_EN.md)
- 新增 partial_delay_gate.py、test_partial_delay_gate.py；原始数据与核验记录在 results/partial_delay_gate/。
- 三个延迟候选中，首步分离 0 与 {1,2} 后可用共同后续指令鲁棒完成任务；初态、扰动和观测误差界均非零，终点和实际输入界有正裕度。
- 反检验：同一套动作在时刻2即可免费完成唯一辨识。因此仅成立时刻1的严格分离，不能证明完整辨识妨碍任务，不能升级为 RA-L 核心创新。
- 固定首步、一维观测的端点与开区间枚举实现连续分支覆盖；不是多步反馈或可变动作的一般合成算法。
- 192个初态/扰动顶点、1536次随机实现、6144步独立轨迹审计；8项针对性测试通过。未重跑或修改历史实验。

## 2026-11-04：队列分支合并的文献与数学审查

- [中文审查](report/QUEUE_MERGE_FEASIBILITY_REVIEW.md) · [English review](report/QUEUE_MERGE_FEASIBILITY_REVIEW_EN.md)
- 定向核查6份原始全文的相关模型、算法与定理；来源和范围在 results/queue_merge_review_2026-11-04/evidence.json。
- 宽泛的“队列合并+保证+加速”未通过独立贡献门槛。固定共同开环策略的支持函数收紧成立，但为标准工具；一般多步反馈的无损合并和便宜的最优性差距仍未解决。
- 明确纠正固定延迟候选数与独立切换树规模的混淆；区分缓存、策略合并和集合外包络。
- queue_merge_math_audit.py完成5组精确有理数检查，包含队列清空、终点签名、硬可行性和满秩路径映射反例；结果位于 math_checks.json。未重跑旧实验。

## 2026-11-04：真实机器人瓶颈与候选命题

- [中文研究建议](report/ROBOT_BOTTLENECK_PROPOSAL_2026-11-04.md) · [English proposal](report/ROBOT_BOTTLENECK_PROPOSAL_2026-11-04_EN.md)
- 从Oxford/RAI/Cornell推动任务和TU Darmstadt实机Push-T工作定位接触轨迹评估的计算瓶颈。候选方向为决策保持多精度轨迹评估，关键待证部分是接触切换时廉价有效的成本包络。
- 核查GPU、缓存、管束、自适应模型与多精度候选识别近邻；不将通用上下界淘汰当作创新，不声称所有现有方法已经在本项目上失败。
- 决定仅支持小规模可证伪试验，非创新确认或投稿就绪。没有安装新环境或运行新实验。来源和访问范围保存在 results/robot_bottleneck_review_2026-11-04/evidence.json。

## 2026-11-04：固定候选批次瓶颈复现

- [中文报告](report/PUSH_T_FIXED_BATCH_REPORT.md) · [English report](report/PUSH_T_FIXED_BATCH_REPORT_EN.md)
- 自建平面接触推动任务：16个冻结批次，每批64条候选，8开发/8测试；实际运行CPU与MuJoCo Warp GPU对照，7项针对性测试通过。
- 精细8线程CPU测试p95为14.12ms；普通粗筛后精评前8为6.88ms，在8个测试批次保持同一最优候选；接触片段细化24.07ms，未通过速度门槛。未建立原创性、可靠包络或闭环性能。
- 数据、图表、环境记录、哈希与原始日志在results/push_t_fixed_batch/；首轮warmstart一致性问题与原始输出保留于pilot_v0。当前统一关闭warmstart，候选数组未变。
- 独立环境.venv-contact与requirements-contact-lock.txt；代码push_t_fixed_batch.py、push_t_gpu_batch.py、analyze_push_t_fixed_batch.py、test_push_t_fixed_batch.py。历史环境和实验保留。

## 2026-11-04：独立困难批次粗筛漏选测试

- [中文报告](report/PUSH_T_SCREEN_STRESS_REPORT.md) · [English report](report/PUSH_T_SCREEN_STRESS_REPORT_EN.md)
- 192个新冻结批次，96开发/96测试；4档步长、1728次计时，数据及复核在results/push_t_screen_stress/。
- 测试集反转3/24、近重复2/24漏选；4/5在更细步长下仍有损失。中等精度报警抓到4/5，但含回退p95高于全精细；仅成本间距误报较多。未证明可靠廉价识别或新颖性。
- 10/96参考赢家对步长敏感；下一步先审计数值收敛并比较候选多样性基线。代码push_t_screen_stress.py；沿用.venv-contact，历史输出保留。

## 2026-11-04：四案例收敛与候选多样性审计

- [中文报告](report/PUSH_T_CONVERGENCE_DIVERSITY_REPORT.md) · [English report](report/PUSH_T_CONVERGENCE_DIVERSITY_REPORT_EN.md)
- 四个案例、64候选、七档步长至0.00015625秒；赢家稳定、漏选持续，但全候选成本尚未证明充分收敛。保存逐步接触对、法向力、冲量及事件记录。
- 96批探索性复用比较：top8损失5次，dedup8为14次、cluster8为16次、cluster16为14次；top16为2次。多样性修复部分案例但整体恶化，不能宣称简单方案已经穷尽。
- 1728次新计时，历史成本、逐步/批量状态与候选精评重现检查通过；数据results/push_t_convergence_diversity/，代码push_t_convergence_diversity.py。下一步需要新确认集与更强简单对照。

## 2026-11-04：新冻结确认集筛选比较

- [中文报告](report/PUSH_T_CONFIRMATION_REPORT.md) · [English report](report/PUSH_T_CONFIRMATION_REPORT_EN.md)
- 种子2026110403，256个新批次，规则和源代码哈希在执行前冻结；6方法、4608次计时。
- 原精细参考下top32为0/256损失，p95 11.30ms（全精细13.86ms）；top16为1次，混合16/32分别4/1次，均不优于同预算排序。
- 更细参考改变27个赢家；top32在批次148有集合漏选，更细参考损失1.055643。参考仍未证明收敛，不应把0/256当可靠性保证。
- 暂停将通用排序/多样性组合当主创新；剩余诊断重点是批次148的数值稳定性与模型偏差。数据results/push_t_confirmation，代码push_t_confirmation.py与finalize_push_t_confirmation.py；历史输出保留。

## 2026-11-04：批次148步长与求解器审计

- [中文报告](report/PUSH_T_BATCH148_AUDIT_REPORT.md) · [English report](report/PUSH_T_BATCH148_AUDIT_REPORT_EN.md)
- 64候选、7档步长、5种Newton/CG及热启动设置。0.0025秒均选5；0.000625秒及以下均选37，原top32最细参考损失约1.049。
- 20条逐步轨迹通过批量重现检查，未触发迭代上限或报警；赢家稳定但全候选成本尚不能宣称完全收敛。不构成真实机器人或创新性证明。
- 数据results/push_t_batch148_audit；执行时源代码快照保留。当前代码push_t_batch148_audit.py增加双语解释，未修改已运行数值部分。历史实验保留。

## 2026-11-04：接触局部加密与同预算对照

- [中文报告](report/PUSH_T_LOCAL_REFINEMENT_REPORT.md) · [English report](report/PUSH_T_LOCAL_REFINEMENT_REPORT_EN.md)
- 完整256批探索性复用、6方法、4608次计时；三种自适应方法逐条匹配仿真步数，包含预计算与重算开销。
- 局部加密恢复148但69.44ms慢于全高精度58.20ms；统一中等步长也恢复且30.42ms。全体损失2批，比同预算对照14/10批少，但p95仍慢于全精细。
- 平均精细段57.10%，含初筛步数仅减少7.17%；当前实现未通过速度门槛。代码push_t_local_refinement.py；数据results/push_t_local_refinement，保留执行源代码快照。

## 2026-11-05：单遍与连续段可行性门槛

- [中文报告](report/PUSH_T_EXECUTION_GATE_REPORT.md) · [English report](report/PUSH_T_EXECUTION_GATE_REPORT_EN.md)
- 固定64批，每类16，含148；6方法、1152次计时。连续段和前缀复用与历史同掩码成本重现；单遍无预计算。
- 单遍步数减少20.8%，但p95 61.29ms仍慢于全精细54.63ms。连续段平均调用反增至52.2次，未通过速度门槛。
- 建议暂停当前Python调度路线的新算法投入，保留负结果并重新审查真实任务需求。数据results/push_t_execution_gate；代码push_t_execution_gate.py，执行快照保留。

## 2026-11-05：闭环任务意义验证

- [中文报告](report/PUSH_T_CLOSED_LOOP_GATE_REPORT.md) · [English report](report/PUSH_T_CLOSED_LOOP_GATE_REPORT_EN.md)
- 16个开发任务（细步长13个成功）；64个新冻结确认任务、四方法；另有执行半步检查和旧148桥接。
- low/medium/high/top32成功数57/55/54/55，p95规划时延18.76/36.09/73.03/40.40ms。规划延迟未注入控制，不是实时部署结果。
- 不支持更细预测步长带来整体闭环成功率改善；个别结果对执行步长敏感，暂停以排名修复为核心的新算法投入。
- 代码push_t_closed_loop_gate.py、push_t_closed_loop_bridge.py、summarize_push_t_closed_loop.py；原始结果results/push_t_closed_loop_gate，历史结果未修改。
