# Batch148: timestep and solver sensitivity of ranking reversal

All64 frozen candidates, state, target, contact parameters and integrator unchanged. Steps .01,.0025,.000625,.0003125,.00015625,.000078125,.0000390625 seconds. Continuous full-horizon calls preserve within-trajectory warmstart.

Five settings: original Newton50/1e-10/cold; Newton200/1e-12/cold; original accuracy warm; tight Newton warm; CG200/1e-12/warm. First four isolate termination and warmstart effects; CG supplies a different solver. Numerical sensitivity settings, not physical calibration.

Winner lists follow decreasing steps. Last-two cost differences are empirical, not error bounds. Runner-up margin helps assess ranking stability. Original shortlist uses the previously frozen coarse top32; each setting's own coarse shortlist loss is separately recorded.
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

Candidates5 and37 were independently stepped at original-fine and finest resolutions for each setting; saved normal force, contact-pair masks, solver iterations and warning counts. All20 direct traces match batched states within1e-7; original three-resolution costs reproduce within1e-9. Iteration-limit/warning diagnostics cover these traces only.

Artifacts results/push_t_batch148_audit; push_t_batch148_audit.py run/report in .venv-contact. Run refuses overwrite. Frozen input, protocol,35 full-candidate evaluations and20 direct traces retained; history unchanged.

Sources: [MuJoCo options](https://mujoco.readthedocs.io/en/stable/XMLreference.html#option), [modeling](https://mujoco.readthedocs.io/en/stable/modeling.html). No contact stiffness/friction interventions, hardware validation or novelty claim.

## Audit conclusion

All5 settings select candidate5 at .0025s and candidate37 at every one of the five tested resolutions <=.000625s. Finest original-top32 set loss ranges1.04856–1.05007; recomputing the coarse shortlist for each setting leaves the same loss. The reversal and miss persist across this grid, not only original cold Newton50.

Direct traces use at most3 Newton or38 CG iterations per step, never the configured cap, with no MuJoCo warnings. Tightening tolerance and increasing the iteration limit do not remove the reversal. Insufficient iteration budget alone is not supported as the explanation.

Candidate37's original-setting normal impulse drops from.06802 at .0025s to.01781 at the finest step; first contact shifts .04000 to.03566s. Candidate5's impulse remains about.03196/.03199. This suggests stronger contact-discretization sensitivity for37, without unique causal proof or local intervention.

Finest winner/runner-up margins are.507–.539, but last-two all-candidate maximum cost changes remain about.101 and cross-setting spread about.115. Report stable winner/miss over the tested grid, not full cost convergence, error certification or physical optimality.

Retain as a numerical counterexample, not standalone novelty. A subsequent bounded test could compare local contact-stage refinement against uniform medium resolution, top32 and equal-budget refinement, including total overhead, then check new samples. Do not tailor an algorithm only to148.
