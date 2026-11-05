# 实验五文献核查与推导说明 / Literature and derivation notes

日期 / date: 2026-11-04。承接 LITERATURE_BASELINES.md。没有复现下列完整算法，不能据此宣称我们的简化实验优于文献方法。

## 2021：联合辨识

[Pandey, Liu, Wang: Parametric identification of output error model for sampled systems with integer-type time delay subject to load disturbance with unknown dynamics](https://doi.org/10.1049/cth2.12170)

本轮通过出版商索引检索到问题描述、部分分析和实验段落，比前轮摘要核查更进一步。直接全文 URL 仍不可访问；缺失公式/假设尚待完整核对。可见段落使用稳定的 SISO 输出误差模型，分析涉及持续激励，并报告带噪声和变化负载扰动的重复试验。本项目已知双积分模型不是渐近稳定的输出误差对象，不能直接套用其结论。

Indexed publisher sections reveal a stable SISO output-error setting, persistent-excitation analysis and repeated noisy/disturbed tests. The complete assumptions and algorithm remain unchecked because direct full-text access failed. Our known double integrator is not the same model class. This is prior art, not a reproduced baseline.

## 2017：扰动处理与相关辨识

[Time-delay identification in dynamic processes with disturbance via correlation analysis](https://doi.org/10.1016/j.conengprac.2017.03.007)

本轮可见出版商索引中的摘要、引言、流程及实例概述；直接访问仍为 403。可确认先处理扰动响应，再用增量数据的相关性识别延迟；尚缺完整公式和参数，不能把当前去均值实现称为其复现。

Publisher-indexed sections describe disturbance-response removal followed by correlation of incremental data. Complete equations and tuning remain unavailable. The present constant-intercept fit is not an implementation of that paper.

## 本项目可直接推导的等价条件

对同一窗口中的加速度观测 y_j，候选延迟 d 的模型为 y_j=u_(j-d)+b_d。若真实延迟为 d*，真实外扰为常数 b*，则错误候选能精确解释观测，当且仅当 u_(j-d*)-u_(j-d) 在整个窗口为常数。因为此时只需让 b_d=b*+该常数。这里没有噪声、模型误差或额外外扰约束。

For y_j=u_(j-d*)+b*, a candidate d admits an exact constant-bias fit if and only if u_(j-d*)-u_(j-d) is constant over the window. This follows by rearranging the two models. It is an elementary equivalence for this narrow setting, not a new general identifiability theorem.

- 恒定输入：所有移位序列相同，无法通过当前窗口区分。
- 线性斜坡 u_j=a*j+c：两个移位序列只差 a*(d-d*)，同样无法区分。
- 多频或正弦：本实验选定频率和候选范围内，去均值移位差非零；其他频率、混叠、短窗口和周期等价仍可能导致困难。
- 外扰可任意变化时，可令 b_d(j)=y_j-u_(j-d) 解释任何候选；必须限制外扰或获得额外信息。

这解释为什么实验中恒定/斜坡的正确率可能高，而结构分离度仍为零：启动时刻或历史先验提供的信息可被保留，当前窗口未必能重新识别。

## 噪声与置信度

若速度噪声 epsilon_j 独立且方差 sigma²，差分加速度噪声 eta_j=(epsilon_(j+1)-epsilon_j)/T，则 Var(eta_j)=2*sigma²/T²，相邻协方差为 -sigma²/T²。简单独立残差平方评分没有利用这一相关结构。0.02 m/s 的速度噪声在 T=0.05 s 时对应约 0.566 m/s² 的差分噪声标准差，不能把它当成很小的加速度误差。

评分差不等于置信概率。结构分离度使用真实延迟，只供评价；部署时不能读取它。下一步应开发不依赖真实延迟的候选间可区分指标，并在独立工况上验证候选集合覆盖和控制代价。

## 下一步文献工作

获取可合法访问的完整原文，逐项核对激励条件、噪声假设、稳定性与延迟定义后再选择复现。不要把“加激励”“去均值”“联合估计”本身当创新点。当前两篇核查属于部分正文阅读，不是完成全文精读，也未确认论文研究空白。
