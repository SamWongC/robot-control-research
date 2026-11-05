import unittest
import numpy as np
import first_action_scan as fs
import preview_identification as base
from analyze_first_action_scan import branch_interval

class FirstActionTests(unittest.TestCase):
    def test_separation_threshold_and_boundary_witness(self):
        result=fs.observation_overlap_limit()
        self.assertAlmostEqual(result['max_overlapping_positive_action'],.048,places=10)
        self.assertLessEqual(result['max_constraint_residual'],1e-9)
        a=.048
        ys=[np.zeros(2),np.array([.00003,.0012])]
        self.assertTrue(base.candidate_feasible(ys,[a],0))
        self.assertTrue(base.candidate_feasible(ys,[a],1))

    def test_delay1_nominal_interval_and_common_sequence_impossibility(self):
        np.testing.assert_allclose(fs.nominal_interval([1]),[-.11,.11],atol=1e-12)
        self.assertIsNone(fs.nominal_interval([0,1]))
        self.assertTrue(fs.nominal_feasible(.1,[1]))
        self.assertFalse(fs.nominal_feasible(-.355,[1]))

    def test_invariant_against_physical_rollout(self):
        for initial in (np.array([0.,0.]),np.array([1e-5,-1e-4])):
            a=.07;commands=[a,-.31,.22];w=[.02,.01,0.];x=initial.copy()
            for k in range(3):x=base.A@x+base.B*((commands[k-1] if k else 0)+w[k])
            invariant=initial[0]+.125*initial[1]+.0025*a+.005*w[0]+.0025*w[1]
            self.assertAlmostEqual(x[0]-.025*x[1],invariant,places=14)

    def test_physical_and_robust_feasibility_are_distinct(self):
        self.assertTrue(fs.hindsight_feasible(np.zeros(2),.1,1,0.,0.))
        self.assertFalse(fs.current_robust_feasible(np.zeros(2),.1,1))
        self.assertTrue(fs.current_robust_feasible(np.zeros(2),0.,1))
        self.assertFalse(fs.hindsight_feasible(np.zeros(2),-.355,1,0.,0.))

    def test_no_reset_and_no_unsafe_preparation_scan(self):
        m,rows=fs.run(.1,1,np.zeros(3),np.zeros((4,2)))
        np.testing.assert_allclose(m['task_start_state'],[0.,0.],atol=1e-14)
        self.assertEqual(m['task_start_pending_command'],.1)
        self.assertAlmostEqual(rows[1][6],.1)
        self.assertTrue(fs.prep_admissible(1.178))
        self.assertFalse(fs.prep_admissible(1.18))

    def test_generator_bounds_with_separate_unit_seed(self):
        for _,w,e in fs.new_records(seed=77491,count=8):
            self.assertLessEqual(np.max(np.abs(w)),.02+1e-15)
            self.assertLessEqual(np.max(np.abs(np.diff(w))),.01+1e-15)
            self.assertTrue(np.all(np.abs(e)<=base.NOISE))

    def test_future_branches_require_incompatible_second_actions(self):
        a=branch_interval(.05,.02,.02,.02)
        b=branch_interval(.05,.02,.01,0.)
        np.testing.assert_allclose(a,[1.43,1.43],atol=1e-12)
        np.testing.assert_allclose(b,[1.46,1.48],atol=1e-12)
        self.assertLess(a[1],b[0])
        # The .035 endpoint is necessary only: these two branches just touch.
        a=branch_interval(.035,.02,.02,.02)
        b=branch_interval(.035,.02,.01,0.)
        self.assertAlmostEqual(a[1],b[0],places=12)

if __name__=='__main__':unittest.main()
