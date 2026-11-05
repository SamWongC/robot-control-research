# Research summary for public review

This project studies how uncertainty and numerical approximations affect control decisions. It progressed from delayed linear dynamics to frozen-candidate contact simulation and closed-loop pushing. Its deliverable is a reproducible record of experiments and rejected hypotheses, rather than a newly validated algorithm.

Control studies implemented delay queues, constrained predictive control, delay/disturbance estimation, consistency sets and causal checks. Stronger passive baselines removed some initial apparent benefits. Literature and mathematical reviews did not establish a standalone contribution beyond existing robust-control/discrimination frameworks.

Contact studies separated screening error from numerical reference error, audited ranking reversal across solver/timestep settings, and measured complete execution cost. Local refinement improved selection in some cases but did not yield end-to-end acceleration. In64 new closed-loop tasks, low/medium/high/top32 succeeded57/55/54/55 times. Selected disagreement cases were sensitive to execution discretization.

Reusable components include batched rollouts, frozen protocols, paired comparisons, full-cost timing, convergence diagnostics and trajectory audits. Rankings, integration counts and reference agreement were insufficient proxies for task performance.

Limitations: synthetic systems, custom planar pushing without a robot arm or physical floor contact, ideal state feedback, no delay-injected validation and no hardware. No general safety/reliability theorem, physical validity or novelty certification follows. Individual reports contain the detailed evidence and primary references.
