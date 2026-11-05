# 批次148：排名变化的步长与求解器核查

固定新确认集批次148的全部64条候选、初态、目标、接触参数和积分器。七档步长：0.01、0.0025、0.000625、0.0003125、0.00015625、0.000078125、0.0000390625秒。每条轨迹完整连续求解，不分段重置热启动。

五设置：原Newton50次/1e-10/无热启动；Newton200次/1e-12/无热启动；原精度开启热启动；收紧Newton开启热启动；CG200次/1e-12/热启动。前四用于分离热启动和终止精度影响，CG提供另一求解算法检查。保持物理模型不变；这些是数值敏感性设置，不声称对真实机器人已校准。

表中赢家按上述步长顺序排列。最后两档成本差是经验差异，不是对真实解的误差上界；最优与次优成本间距用于判断排名稳健程度。原top32集合始终使用上一确认实验的粗排序，另记录各设置自身粗top32的漏选。
| Config | Winners, decreasing step | Last-two max cost delta | Finest winner margin | Finest original-top32 set loss |
|---|---|---:|---:|---:|
| original | [3, 5, 37, 37, 37, 37, 37] | 0.100883 | 0.539486 | 1.048680 |
| tight_cold | [3, 5, 37, 37, 37, 37, 37] | 0.100851 | 0.539486 | 1.048680 |
| warm | [7, 5, 37, 37, 37, 37, 37] | 0.100992 | 0.507005 | 1.050065 |
| tight_warm | [7, 5, 37, 37, 37, 37, 37] | 0.100992 | 0.533054 | 1.050002 |
| cg_tight | [7, 5, 37, 37, 37, 37, 37] | 0.100872 | 0.526375 | 1.048563 |

```json
{
  "settings": [
    {
      "config": "original",
      "winners": [
        3,
        5,
        37,
        37,
        37,
        37,
        37
      ],
      "last_two_max_cost_delta": 0.10088263714686363,
      "finest_best_runnerup_margin": 0.5394858760275376,
      "finest_original_top32_loss": 1.0486802934739163,
      "finest_own_coarse_top32_loss": 1.0486802934739163,
      "finest_cost5_minus37": 1.0486802934739163
    },
    {
      "config": "tight_cold",
      "winners": [
        3,
        5,
        37,
        37,
        37,
        37,
        37
      ],
      "last_two_max_cost_delta": 0.10085055070229743,
      "finest_best_runnerup_margin": 0.5394858754263034,
      "finest_original_top32_loss": 1.0486802928726822,
      "finest_own_coarse_top32_loss": 1.0486802928726822,
      "finest_cost5_minus37": 1.0486802928726822
    },
    {
      "config": "warm",
      "winners": [
        7,
        5,
        37,
        37,
        37,
        37,
        37
      ],
      "last_two_max_cost_delta": 0.1009915434908022,
      "finest_best_runnerup_margin": 0.5070048816699666,
      "finest_original_top32_loss": 1.0500653827756832,
      "finest_own_coarse_top32_loss": 1.0500653827756832,
      "finest_cost5_minus37": 1.0500653827756832
    },
    {
      "config": "tight_warm",
      "winners": [
        7,
        5,
        37,
        37,
        37,
        37,
        37
      ],
      "last_two_max_cost_delta": 0.1009915434908022,
      "finest_best_runnerup_margin": 0.5330540451185888,
      "finest_original_top32_loss": 1.0500023314242837,
      "finest_own_coarse_top32_loss": 1.0500023314242837,
      "finest_cost5_minus37": 1.0500023314242837
    },
    {
      "config": "cg_tight",
      "winners": [
        7,
        5,
        37,
        37,
        37,
        37,
        37
      ],
      "last_two_max_cost_delta": 0.1008720049353915,
      "finest_best_runnerup_margin": 0.5263745546149772,
      "finest_original_top32_loss": 1.048562919013575,
      "finest_own_coarse_top32_loss": 1.048562919013575,
      "finest_cost5_minus37": 1.048562919013575
    }
  ],
  "max_cross_setting_finest_cost_range": 0.11515765076979001,
  "any_trace_warning": false,
  "trace_iteration_cap_steps": 0
}
```

独立逐步重放候选5与37，在原精细和本轮最细步长下记录法向力、几何接触对、每步求解迭代数、报警计数。20条逐步轨迹与批量输出在1e-7内一致；原三档全部成本重现至1e-9。迭代上限/报警检查仅覆盖这些重放轨迹，不应扩展成全部候选的求解器保证。

数据：results/push_t_batch148_audit；代码push_t_batch148_audit.py，.venv-contact执行run、report，run拒绝覆盖。输入、协议、35组全部候选成本与控制段状态、20条逐步轨迹均保存。未改动历史结果。

设置依据：[MuJoCo option文档](https://mujoco.readthedocs.io/en/stable/XMLreference.html#option)、[建模文档](https://mujoco.readthedocs.io/en/stable/modeling.html)。本轮没有改变接触刚度、摩擦或任务，也没有物理实验，不能将单案例数值稳定性当作论文新颖性或现实有效性。

## 核查结论

在本轮全部5种设置下，0.0025秒选候选5，而0.000625秒及以下连续5档均选37。最细参考中，原top32集合损失为1.04856–1.05007，各设置按自身粗模型重新筛前32也有相同损失。因此排名反转与前32漏选跨本轮步长/求解器设置持续存在，不是只在原冷启动Newton50设置下出现。

重放轨迹中Newton每步最多3次迭代，CG最多38次，均未达到上限且没有MuJoCo报警。提高到200次并收紧容差没有消除反转；证据不支持把该现象简单归结为迭代次数不足。

接触差异集中在候选37：原设置的法向冲量从0.0025秒的0.06802降至最细档0.01781，首次接触从0.04000秒变为0.03566秒；候选5冲量约0.03196/0.03199，变化小得多。提示37对接触时间离散更敏感；尚未做局部接触干预，不能宣称已唯一确定因果机制。

限制：最细档最优/次优成本差0.507–0.539，但最后两档全候选最大成本变化仍约0.101，跨设置最大成本差约0.115。因此可以报告“赢家和漏选现象在所测网格内稳定”，不能报告完整成本收敛、严格误差证书或真实机器人最优动作。

选题判断：这个案例可以保留为接触轨迹评估的数值反例，尚不足以构成独立论文创新。下一步应先检验能否通过接触阶段局部加密，在比全时域细化更低的计算开销下恢复正确排名，并与统一中等步长、普通前32及同预算细化对照；同时评估是否能在新样本中稳定复现，而不是只针对148定制算法。
