# 闭环任务意义验证 — 2026-11-05

## 实验定义
细步长开发集成功13/16，预先规定至少12/16后运行确认。64个新确认任务每类16个，在开发前已冻结；仅初值是新的，任务家族不是全新。64条候选、1秒预测，只执行首50毫秒后重规划。所有方法使用相同候选生成规则（零动作、上次最优轨迹平移、朝向目标的动作、平滑随机扰动）和共同随机种子。状态分岔后候选随各自状态及热启动变化，不强行使用相同绝对轨迹。

low/medium/high预测步长分别为.0025/.00125/.000625秒；top32先以.01秒筛64条，再以.000625秒精算32条。执行环境步长.0003125秒，另取四个开发案例以.00015625秒作敏感性检查。位置误差<=2cm且角度误差<=10度连续保持0.5秒视为成功；10秒截止；物体或推杆XY超出±0.5米终止。成功没有额外速度阈值。理想状态观测、平面阻尼摩擦模型，无机械臂、真实地板接触或障碍物。

控制中暂不注入计算延迟；计时包含候选生成、仿真评估、选择及复制动作，不含执行环境积分、文件保存和初始化。每任务每方法运行一次，方法顺序随机。计时样本相关，百分位按全部规划调用汇总，长任务权重更高。超过50ms的比例不是实测实时闭环失败率。

## 结果
| Method | Success /64 | Escape | Mean final error (m) | Mean elapsed (s)* | p95 ms | p99 ms | >50ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| low | 57 | 0 | 0.0093 | 3.328 | 18.76 | 20.75 | 0.0% |
| medium | 55 | 0 | 0.0103 | 3.410 | 36.09 | 41.75 | 0.3% |
| high | 54 | 0 | 0.0119 | 3.352 | 73.03 | 94.00 | 86.1% |
| top32 | 55 | 0 | 0.0090 | 3.320 | 40.40 | 44.14 | 0.2% |

| Method | Approach /16 | Near contact /16 | Stem /16 | Corner /16 |
|---|---:|---:|---:|---:|
| low | 16 | 16 | 16 | 9 |
| medium | 16 | 15 | 16 | 8 |
| high | 16 | 16 | 16 | 6 |
| top32 | 16 | 16 | 16 | 7 |

| Method vs high | Only method succeeds | Only high succeeds | Success difference | Bootstrap 95% | First action differs /64 |
|---|---:|---:|---:|---|---:|
| low | 4 | 1 | 4.7% | [-0.015625, 0.109375] | 1 |
| medium | 3 | 2 | 1.6% | [-0.046875, 0.078125] | 1 |
| top32 | 1 | 0 | 1.6% | [0.0, 0.046875] | 0 |

| Case | Success base / half-step | Final error base / half-step (m) | Duration base / half-step (s) |
|---|---|---|---|
| 0 | True / True | 0.0004 / 0.0004 | 1.50 / 1.50 |
| 12 | False / False | 0.0497 / 0.0953 | 10.00 / 10.00 |
| 4 | True / True | 0.0004 / 0.0004 | 1.45 / 1.45 |
| 8 | True / True | 0.0007 / 0.0036 | 1.90 / 1.65 |

表中elapsed是各方法终止时长（最长10秒），失败任务不解释为成功完成时间。终点误差在各自终止时刻测量。成功率差区间采用按四个家族分层的10000次配对episode自助采样，只作描述，不是总体可靠性保证或多重检验校正结果。首动作比较发生在完全相同的初态和候选集；后续候选不再相同。

## 限制与审计
细步长规划不是物理真值，也不保证闭环表现最好。执行半步检查只有4个开发案例，不能证明全部确认任务数值收敛。结论依赖当前采样控制器、代价函数、容差和简化模型。旧排名反例不自动构成论文贡献；本确认集后续不可重复声称为未见数据。

已独立重算276条保存轨迹的位姿误差、连续成功条件、越界、控制限幅及数据完整性，并检查冻结数据与执行源码哈希。审计见results/push_t_closed_loop_gate/audit.json。代码、冻结初值、原始时延、轨迹和执行源码快照均保留。本次未进行新的文献新颖性审查。


## Exploratory sensitivity / 探索性敏感性检查

Archived148 uses its original64 proposals only at the first decision; subsequent decisions use the new rolling controller. This is not a pure first-action intervention because later methods differ too. / 旧148仅首轮使用原64候选，随后使用新闭环控制器；后续方法也不同，因此不是只改变首动作的因果干预。

| Execution step | Method | First choice | Success | Duration s | Final error m |
|---|---|---:|---|---:|---:|
| 0.0003125 | low | 5 | False | 10.00 | 0.0298 |
| 0.0003125 | medium | 37 | False | 10.00 | 0.0312 |
| 0.0003125 | high | 37 | True | 3.90 | 0.0173 |
| 0.0003125 | top32 | 5 | False | 10.00 | 0.0397 |
| 0.00015625 | low | 5 | False | 10.00 | 0.0203 |
| 0.00015625 | medium | 37 | False | 10.00 | 0.0347 |
| 0.00015625 | high | 37 | True | 9.55 | 0.0021 |
| 0.00015625 | top32 | 5 | True | 9.05 | 0.0016 |

Post-hoc half-step checks use the first eight (or fewer) disagreement IDs; selection is outcome-dependent, not a new test set. / 事后取最多8个成功标签不一致的任务复查，按编号选取；不是新确认集。

| Case | Method | Success base / half | Error base / half (m) |
|---|---|---|---|
| 47 | high | True / True | 0.0184 / 0.0049 |
| 47 | low | True / True | 0.0185 / 0.0039 |
| 47 | medium | False / True | 0.0185 / 0.0041 |
| 47 | top32 | True / True | 0.0184 / 0.0049 |
| 65 | high | False / False | 0.1040 / 0.1033 |
| 65 | low | True / False | 0.0080 / 0.1033 |
| 65 | medium | True / False | 0.0017 / 0.1033 |
| 65 | top32 | True / False | 0.0072 / 0.1033 |
| 68 | high | False / False | 0.0048 / 0.0332 |
| 68 | low | False / False | 0.0893 / 0.1085 |
| 68 | medium | True / False | 0.0026 / 0.0372 |
| 68 | top32 | False / False | 0.0125 / 0.0969 |
| 70 | high | True / False | 0.0021 / 0.0586 |
| 70 | low | True / True | 0.0005 / 0.0004 |
| 70 | medium | False / True | 0.0461 / 0.0180 |
| 70 | top32 | True / False | 0.0021 / 0.0590 |
| 71 | high | False / False | 0.0280 / 0.0306 |
| 71 | low | False / True | 0.0294 / 0.0166 |
| 71 | medium | True / False | 0.0124 / 0.0267 |
| 71 | top32 | False / False | 0.0233 / 0.0306 |
| 73 | high | False / False | 0.0718 / 0.0690 |
| 73 | low | True / False | 0.0037 / 0.0532 |
| 73 | medium | False / True | 0.0706 / 0.0030 |
| 73 | top32 | False / False | 0.0705 / 0.0690 |
| 77 | high | False / True | 0.1059 / 0.0073 |
| 77 | low | True / True | 0.0141 / 0.0021 |
| 77 | medium | False / False | 0.1009 / 0.1163 |
| 77 | top32 | False / True | 0.0124 / 0.0035 |
| 78 | high | True / True | 0.0079 / 0.0001 |
| 78 | low | False / False | 0.0723 / 0.0722 |
| 78 | medium | True / False | 0.0143 / 0.0709 |
| 78 | top32 | True / True | 0.0079 / 0.0001 |

Label flips after halving execution step / 执行步长减半后的标签变化：15/32. Additional trajectories audited / 额外审计轨迹：40.


## 去留判断
本确认集不支持“提高预测积分精度即可提高闭环任务成功率”，也不支持据此重启接触局部加密加速论文。粗、中、细和top32成功数分别为57、55、54、55；粗与细的配对成功率差区间包含0，不能宣称粗步长普遍更优。细步长p95超过50ms，本实验没有计入延迟，不能将理想闭环成功率当作可部署结果。

旧148的桥接结果只能证明在这一控制器下个案有差异；后续重规划及热启动也随方法变化，不能把所有后果归因于第一次候选排名。top32在执行半步检查中恢复成功，说明单一离散化设置的失败标签不可靠。确认集差异任务的半步结果也须一并报告。

下一步建议停止为当前“修复排名=改善任务”的主张追加算法。若保留此方向，需先说明真实任务的控制器瓶颈，并验证任务/接触模型，而非继续调当前反例。此次首动作在多数普通任务中相同；这组任务不是专门冻结的独立困难排名分布，因此不证明所有排名误差均可被重规划消除。没有论文级创新或真实机器人结论。
