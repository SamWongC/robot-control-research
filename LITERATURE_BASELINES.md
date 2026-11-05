> 本文件保留初次检索记录。最新正文核查与选题结论见 [创新性审查](report/NOVELTY_REVIEW_2026-11-04.md)。

# 初步文献与基线比较 / Preliminary Literature and Baseline Matrix

核查日期 / checked: 2026-11-04。这是定向检索及初步比较，不是系统综述或完整新颖性审查。以下“未确认”不表示论文没有该内容。实验四是基础最小二乘基线，没有复现下列完整算法。

| 工作 / primary source | 已核查范围 / access | 与项目的关系 / relevance | 后续需要核查 / next check |
|---|---|---|---|
| [Parametric identification of output error model for sampled systems with integer-type time delay subject to load disturbance with unknown dynamics (2021)](https://doi.org/10.1049/cth2.12170) | 出版商检索结果含摘要和引言；直接访问 403。未核查全文公式 / abstract and introduction excerpt, full text unavailable | 联合估计有扰动系统的模型与整数延迟，是最直接的已有工作；不能把联合估计本身视为创新 / jointly estimates model, integer delay and disturbance response | 获取可合法访问全文；核查噪声、收敛条件、在线开销与本实验假设，决定复现方式 |
| [Time-delay identification in dynamic processes with disturbance via correlation analysis (2017)](https://doi.org/10.1016/j.conengprac.2017.03.007) | 出版商摘要及 highlights；直接访问 403 / publisher abstract and highlights | 先估计并消除过程扰动响应，再通过相关分析识别延迟；是非学习对照方向 / disturbance removal before correlation-based identification | 获取全文；核查激励条件、闭环偏差、变化延迟适用性 |
| [Adaptive-Robust Control of a Class of Nonlinear Systems with Unknown Input Delay (2016 journal reference)](https://arxiv.org/abs/1509.06542) | arXiv 摘要页 / abstract page | 在未知输入延迟和有界扰动下设计鲁棒控制，包含移动机器人实验 / control may tolerate uncertainty without explicitly identifying exact delay | 核查具体稳定性假设与允许延迟范围；是否可构造匹配机器人基线 |
| [Fixed-time Disturbance Observer-Based MPC Robust Trajectory Tracking Control of Quadrotor (2024 preprint)](https://arxiv.org/html/2408.15019v2) | HTML 全文可访问；初读摘要、引言、结构和验证章节 / full text available, preliminary reading | 外扰观测进入 MPC 预测，并报告仿真和实机；说明“估计外扰加 MPC”已有成熟研究 / disturbance-aware MPC reference | 本次未复现；需核对观测器参数和证明。没有据此确认其研究未知输入延迟 |
| [Adaptive Reinforcement Learning for Unobservable Random Delays (2026 version)](https://arxiv.org/abs/2506.14411) | arXiv 摘要与版本记录 / abstract and version metadata | ACDA 面向不可观测变化延迟，涉及动作包与执行语义 / modern delay-adaptive learning reference | 读全文与代码，对齐数据、执行器接口和训练预算；不假设与当前九候选队列直接等价 |

## 当前决定 / Current decision

实验三暴露的是忽略外扰的基础估计器缺陷，不能把这个缺陷直接包装为文献空白。实验四用候选残差去均值拟合常值外扰，作为必须保留的传统基线。外扰观测器、相关辨识和鲁棒控制仍需要更完整的匹配比较。

Experiment 3 demonstrates a weakness of a disturbance-blind baseline, not an established gap in the literature. Experiment 4 profiles a constant bias for each delay candidate. This baseline must remain in later comparisons. Matched disturbance-observer, correlation-based and robust-control baselines still need investigation.

## 下一轮文献表应增加的字段

已知/未知模型、输入/观测延迟、固定/变化延迟、是否有执行时间戳、扰动模型、测量噪声、持续激励、可辨识条件、估计不确定性的校准、估计如何进入控制、理论范围、实机、代码许可。先读最接近的 2021/2017 工作，再决定论文具体创新点。

注意术语：time-delay estimation (TDE) 也常指用相邻时刻信息估计集总动力学，并不一定是在识别通信或执行时延。检索时必须核查数学定义。
