import unittest
import numpy as np
from task_ambiguity_scenarios import (A,B,H,NOISE,TOL,DELAYS,prediction,
    actual_rollout,robust_radius,solve_task,compatibility)

class TaskWitnessTests(unittest.TestCase):
    def test_prediction_against_physical_recurrence(self):
        u=np.array([.7,-.3]);w=np.array([.012,.007]);x0=np.array([.001,-.01])
        for d in DELAYS:
            g,e=prediction(d)
            np.testing.assert_allclose(g@u+e@w+np.linalg.matrix_power(A,H)@x0,
                                       actual_rollout(u,d,x0,w)[-1],atol=1e-15)

    def test_exact_support_matches_positive_system_formula(self):
        radius,_=robust_radius()
        expected=np.abs(np.linalg.matrix_power(A,H))@NOISE+np.array([.0001,.002])
        np.testing.assert_allclose(radius,expected,atol=1e-14)

    def test_history_and_two_distinct_feasibility_cases(self):
        radius,_=robust_radius()
        self.assertTrue(all(compatibility(d)['compatible'] for d in DELAYS))
        self.assertTrue(solve_task(np.zeros(2),DELAYS,radius)['feasible'])
        target=np.array([.002,.08])
        self.assertTrue(all(solve_task(target,[d],radius)['feasible'] for d in DELAYS))
        for d,u in [(0,np.array([0.,1.6])),(1,np.array([1.6,0.]))]:
            self.assertTrue(np.all(np.abs(prediction(d)[0]@u-target)+radius<=TOL+1e-14))
        self.assertFalse(solve_task(target,DELAYS,np.zeros(2))['feasible'])

    def test_nominal_gap_independent_algebra(self):
        # At d=1: v2=.05*u0. At d=0: p2-.025*v2=.0025*u0.
        target=np.array([.002,.08])
        d0=solve_task(target,[0],np.zeros(2))['first_action_interval']
        d1=solve_task(target,[1],np.zeros(2))['first_action_interval']
        rad0=(TOL[0]+.025*TOL[1])/.0025
        np.testing.assert_allclose(d0,[-rad0,rad0],atol=1e-12)
        np.testing.assert_allclose(d1,[(.08-.003)/.05,(.08+.003)/.05],atol=1e-12)
        self.assertGreater(d1[0]-d0[1],1.)

if __name__=='__main__':unittest.main()
