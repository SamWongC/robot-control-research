# 机器人控制研究：可复现实验与失效分析

[English README](README.md) · [复现说明](docs/REPRODUCING.md) · [研究总结](report/PUBLIC_RESEARCH_SUMMARY.md)

本仓库整理Lufei Wang（[SamWongC](https://github.com/SamWongC)）关于输入延迟辨识、任务相关模型歧义、接触仿真精度和候选筛选的独立探索。包括代码、冻结输入、原始数据、中英文报告和验证脚本。

**这是一份研究档案，不是已发表论文或已确认创新算法。** 本地目录名RA-L代表早期目标，不代表录用。本仓库不是RWTH或Robot Companion官方项目。

## 核心结果

- 强化基线后，部分主动辨识优势消失；当前构造未建立超出既有框架的贡献。
- 粗筛在一个参考步长上选对动作，不代表在更细步长或真实物理中也正确。
- 单遍局部加密减少20.8%积分步，但仍慢于统一细步长。
- 64个新闭环任务中，粗/中/细/top32成功数57/55/54/55，没有细步长的整体优势证据。
- 8个选定差异案例的32次复查中，执行步长减半导致15次成功标签变化；这不是总体概率。

这些结果记录失效机制和投入判断，不包装成正向收益。不同阶段的计时不可直接比较。

## 使用

1. 阅读[公开研究总结](report/PUBLIC_RESEARCH_SUMMARY.md)和[闭环报告](report/PUSH_T_CLOSED_LOOP_GATE_REPORT.md)。
2. 运行`python verify_release.py`核对文件哈希，只需Python标准库。
3. 按[复现指南](docs/REPRODUCING.md)安装对应环境，用`reproduce.py`在新目录重算。
4. 通过[实验地图](docs/EXPERIMENTS.md)定位源码和数据。

接触任务是简化平面模型，无机械臂或真实地板接触，不是标准Push-T复现。计算延迟没有反馈到控制，因此不是实时部署结果。没有真实机器人、安全保证或可发表性承诺。

代码与报告使用了AI编程辅助。私人邮件及thesis联络材料不在公开副本中。历史哈希对应当时执行版本；原项目完整保留。暂未选择开源许可证，见[许可说明](LICENSE_NOTICE.md)。
