"""Attach post-result research decision without changing the frozen experiment."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parent;O=ROOT/'results'/'push_t_confirmation';R=ROOT/'report'
zh='''
## 确认集结论与选题判断

原0.0025秒参考下，top32在256批均选择同一赢家，p95为11.30ms，对比全精细13.86ms减少约18.5%。top16仅漏1批，p95为8.07ms；hybrid16漏4批、hybrid32漏1批，均比同预算普通排序更慢。因此本轮不支持“增加动作多样性”的必要性，也不支持围绕这套通用筛选组合直接立独立RA-L命题。

必须保留的反证：更细0.000625秒参考改变27/256个赢家，连全量0.0025秒精评的输出也有27次更细参考损失。这与筛选漏选是不同问题。top32在更细参考下有1次集合漏选，批次148（near_duplicate，0编号）：更细赢家37在粗排序第43名；top32和原全精细均选5，更细参考损失为1.055643。因此不能把top32的原参考零失败写成一般可靠性结论。更细参考也未证明收敛，更不是物理真值。

top16的唯一原参考失败为批次0（grazing）：赢家52粗排第20，损失0.020482，更细参考仍损失0.018737。它在此前擦边场景未出错之后出现，说明上一小样本中的零失败不能解释为场景类别安全。

去留建议：暂停把“排序+多样性混合保留”当主创新。只保留一个有界诊断任务：对批次148进行更细步长、求解器/接触数值设置与接触轨迹审计，确认大幅排名变化是否稳定。若只是当前参考/模型数值不稳定，应先修复基准；若稳定存在，再研究能否以小于全精细代价识别粗模型乐观/悲观偏差，并与top32和同预算简单基线比较。尚未排除已有多精度方法，也未建立创新性。

不继续根据本确认集调参后宣称确认成功。若设计新方法，应另冻结验证集。1e-4仅数值阈值；用户尚未定义闭环任务允许的性能损失、时限和安全要求，因此目前不能判断剩余损失是否具有真实任务价值。
'''
en='''
## Confirmation decision

Against the original .0025 reference, top32 selects the identical winner on all256 batches, p95 11.30ms versus13.86ms all-fine (about18.5% reduction). Top16 has one loss at8.07ms. Hybrid16 has four losses and hybrid32 one, both slower than plain ranking at equal budget. This does not support action diversity as a necessary contribution or a standalone RA-L claim built on this generic combination.

Important counterevidence: the .000625 audit changes27/256 winners, and even all-fine .0025 outputs incur27 audit losses. Reference-model error is distinct from shortlist loss. Top32 has one audit set miss: zero-based batch148 (near_duplicate), audit winner37 ranks43 coarsely; top32 and original all-fine choose5, with audit regret1.055643. Zero original-reference failures therefore do not imply general reliability. Audit resolution itself is not proven converged or physical truth.

The sole original-reference top16 failure is batch0 (grazing): winner52 at coarse rank20, original regret.020482, audit regret.018737. Earlier small-sample zero failures for grazing did not establish family-level safety.

Decision: pause rank/diversity mixtures as the main novelty. Retain one bounded diagnostic: finer-step, solver/contact-setting and trajectory audit of batch148 to assess whether the large ranking reversal is stable. If it is reference/model instability, repair the benchmark first. If stable, investigate inexpensive detection of coarse cost bias against top32 and equal-budget simple baselines. Existing multifidelity methods remain unexcluded; no novelty is established.

Do not tune on this confirmation set and relabel success as confirmation. New methods require a new frozen set. The1e-4 threshold is numerical; closed-loop acceptable loss, deadlines and safety requirements remain undefined, so real-task significance cannot yet be claimed.
'''
for suffix,body in [('',zh),('_EN',en)]:
    p=R/f'PUSH_T_CONFIRMATION_REPORT{suffix}.md';s=p.read_text(encoding='utf8');heading=body.splitlines()[1]
    if heading in s:s=s[:s.index(heading)].rstrip()+'\n'
    p.write_text(s+body,encoding='utf8')
    (O/f'decision{suffix}.md').write_text(body,encoding='utf8')
files=[p for p in O.iterdir() if p.is_file() and p.name!='artifact_hashes.json']+[ROOT/'push_t_confirmation.py',Path(__file__),R/'PUSH_T_CONFIRMATION_REPORT.md',R/'PUSH_T_CONFIRMATION_REPORT_EN.md']
(O/'artifact_hashes.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2),encoding='utf8')
print('Decision and artifact hashes saved')
