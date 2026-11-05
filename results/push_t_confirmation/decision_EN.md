
## Confirmation decision

Against the original .0025 reference, top32 selects the identical winner on all256 batches, p95 11.30ms versus13.86ms all-fine (about18.5% reduction). Top16 has one loss at8.07ms. Hybrid16 has four losses and hybrid32 one, both slower than plain ranking at equal budget. This does not support action diversity as a necessary contribution or a standalone RA-L claim built on this generic combination.

Important counterevidence: the .000625 audit changes27/256 winners, and even all-fine .0025 outputs incur27 audit losses. Reference-model error is distinct from shortlist loss. Top32 has one audit set miss: zero-based batch148 (near_duplicate), audit winner37 ranks43 coarsely; top32 and original all-fine choose5, with audit regret1.055643. Zero original-reference failures therefore do not imply general reliability. Audit resolution itself is not proven converged or physical truth.

The sole original-reference top16 failure is batch0 (grazing): winner52 at coarse rank20, original regret.020482, audit regret.018737. Earlier small-sample zero failures for grazing did not establish family-level safety.

Decision: pause rank/diversity mixtures as the main novelty. Retain one bounded diagnostic: finer-step, solver/contact-setting and trajectory audit of batch148 to assess whether the large ranking reversal is stable. If it is reference/model instability, repair the benchmark first. If stable, investigate inexpensive detection of coarse cost bias against top32 and equal-budget simple baselines. Existing multifidelity methods remain unexcluded; no novelty is established.

Do not tune on this confirmation set and relabel success as confirmation. New methods require a new frozen set. The1e-4 threshold is numerical; closed-loop acceptable loss, deadlines and safety requirements remain undefined, so real-task significance cannot yet be claimed.
