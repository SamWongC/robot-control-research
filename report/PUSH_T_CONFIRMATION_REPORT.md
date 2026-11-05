# 新冻结确认集：前16、前32与排序/多样性混合保留

在执行前冻结种子2026110403、256个批次（四类各64，每批64候选）、方法、阈值和源代码哈希。完全复用上一轮场景生成分布，仅改变种子和数量；这是新样本确认，不是新任务或实机泛化。没有依据结果调整方法。

混合16/32：先保留粗成本前8/16，再在粗前32/64中按与已选动作序列的最小RMS距离最远原则补齐至16/32。这个简单规则同时保留排序与多样性，不使用精细真值或生成器簇标签。top8用于上下文，fine为全64精评。所有在线精评步长0.0025秒，粗步长0.01秒，额外0.000625秒全候选仅作离线参考审计。

每批每方法3次随机顺序计时，共4608次；包含粗评、筛选及精评，预热/参考构建不计入。p95为描述统计。损失阈值1e-4是数值报告阈值，不是机器人任务容许损失。更细参考集合损失指即便对所保留候选按更细模型重新排序，仍漏掉更好候选；实际输出的更细参考损失另存summary.json，包含在线精细模型自身的排序误差。
| Method | Loss /256 | Max regret | Mean regret | p95 ms | Finer-reference set loss /256 |
|---|---:|---:|---:|---:|---:|
| fine | 0 | 0.000000 | 0.000000 | 13.86 | 0 |
| top8 | 5 | 0.300943 | 0.002549 | 6.39 | 8 |
| top16 | 1 | 0.020482 | 0.000080 | 8.07 | 3 |
| top32 | 0 | 0.000000 | 0.000000 | 11.30 | 1 |
| hybrid16 | 4 | 0.182756 | 0.001373 | 8.44 | 5 |
| hybrid32 | 1 | 0.020482 | 0.000080 | 12.68 | 2 |

```json
{
  "methods": [
    {
      "method": "fine",
      "losses": 0,
      "max_regret": 0.0,
      "mean_regret": 0.0,
      "audit_output_losses": 27,
      "audit_set_losses": 0,
      "p95_ms": 13.859854987822473,
      "family_losses": {
        "grazing": 0,
        "reversal": 0,
        "near_duplicate": 0,
        "fast_corner": 0
      }
    },
    {
      "method": "top8",
      "losses": 5,
      "max_regret": 0.3009426802927089,
      "mean_regret": 0.002548899944309289,
      "audit_output_losses": 30,
      "audit_set_losses": 8,
      "p95_ms": 6.388625060208142,
      "family_losses": {
        "grazing": 1,
        "reversal": 2,
        "near_duplicate": 1,
        "fast_corner": 1
      }
    },
    {
      "method": "top16",
      "losses": 1,
      "max_regret": 0.02048235969895118,
      "mean_regret": 8.000921757402805e-05,
      "audit_output_losses": 28,
      "audit_set_losses": 3,
      "p95_ms": 8.068085083505139,
      "family_losses": {
        "grazing": 1,
        "reversal": 0,
        "near_duplicate": 0,
        "fast_corner": 0
      }
    },
    {
      "method": "top32",
      "losses": 0,
      "max_regret": 0.0,
      "mean_regret": 0.0,
      "audit_output_losses": 27,
      "audit_set_losses": 1,
      "p95_ms": 11.298790044384077,
      "family_losses": {
        "grazing": 0,
        "reversal": 0,
        "near_duplicate": 0,
        "fast_corner": 0
      }
    },
    {
      "method": "hybrid16",
      "losses": 4,
      "max_regret": 0.18275643563420263,
      "mean_regret": 0.001373342599415895,
      "audit_output_losses": 29,
      "audit_set_losses": 5,
      "p95_ms": 8.438949921401218,
      "family_losses": {
        "grazing": 1,
        "reversal": 1,
        "near_duplicate": 1,
        "fast_corner": 1
      }
    },
    {
      "method": "hybrid32",
      "losses": 1,
      "max_regret": 0.02048235969895118,
      "mean_regret": 8.000921757402805e-05,
      "audit_output_losses": 28,
      "audit_set_losses": 2,
      "p95_ms": 12.678264954593033,
      "family_losses": {
        "grazing": 1,
        "reversal": 0,
        "near_duplicate": 0,
        "fast_corner": 0
      }
    }
  ],
  "reference_winner_changes": 27,
  "zero_loss_one_sided_95_upper": 0.011633876163163248
}
```

即使某方法零漏选也不能证明普遍可靠；在独立同分布伯努利假设下，256次零失败对应单侧95%失败率上界约1.16%，这里只作为规模提示，分层固定场景和有限合成模型限制其外推。参考赢家变化说明不能将0.0025秒结果当物理真值。

文件：push_t_confirmation.py；results/push_t_confirmation内保存fixture、协议、冻结生成器、三档成本、逐次计时、候选索引和失败案例。使用.venv-contact依次运行freeze/run/report；冻结和运行均拒绝覆盖已有主要输出。所有历史实验保留。成本重现、候选唯一性、有限值及回算损失检查通过。没有建立误差证书或创新性。

## 确认集结论与选题判断

原0.0025秒参考下，top32在256批均选择同一赢家，p95为11.30ms，对比全精细13.86ms减少约18.5%。top16仅漏1批，p95为8.07ms；hybrid16漏4批、hybrid32漏1批，均比同预算普通排序更慢。因此本轮不支持“增加动作多样性”的必要性，也不支持围绕这套通用筛选组合直接立独立RA-L命题。

必须保留的反证：更细0.000625秒参考改变27/256个赢家，连全量0.0025秒精评的输出也有27次更细参考损失。这与筛选漏选是不同问题。top32在更细参考下有1次集合漏选，批次148（near_duplicate，0编号）：更细赢家37在粗排序第43名；top32和原全精细均选5，更细参考损失为1.055643。因此不能把top32的原参考零失败写成一般可靠性结论。更细参考也未证明收敛，更不是物理真值。

top16的唯一原参考失败为批次0（grazing）：赢家52粗排第20，损失0.020482，更细参考仍损失0.018737。它在此前擦边场景未出错之后出现，说明上一小样本中的零失败不能解释为场景类别安全。

去留建议：暂停把“排序+多样性混合保留”当主创新。只保留一个有界诊断任务：对批次148进行更细步长、求解器/接触数值设置与接触轨迹审计，确认大幅排名变化是否稳定。若只是当前参考/模型数值不稳定，应先修复基准；若稳定存在，再研究能否以小于全精细代价识别粗模型乐观/悲观偏差，并与top32和同预算简单基线比较。尚未排除已有多精度方法，也未建立创新性。

不继续根据本确认集调参后宣称确认成功。若设计新方法，应另冻结验证集。1e-4仅数值阈值；用户尚未定义闭环任务允许的性能损失、时限和安全要求，因此目前不能判断剩余损失是否具有真实任务价值。
