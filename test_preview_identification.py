import unittest
import numpy as np
from preview_identification import (A,B,W,RATE,NOISE,TOL,DT,PROBE,
    cases,candidate_feasible,lifted,plan,run)

class PreviewTests(unittest.TestCase):
    def test_lifted_queue_against_physical_steps(self):
        history=[.31,-.27];u=[.2,-.4,.5];y=np.array([.001,.003])
        for d in (0,1):
            centers,g,_=lifted(y,history,d,3)
            x=y.copy();commands=history.copy()
            for k,uk in enumerate(u):
                applied=uk if d==0 else commands[-1]
                x=A@x+B*applied;commands.append(uk)
                np.testing.assert_allclose(x,centers[k]+g[k]@u,atol=1e-15)

    def test_probe_separates_bounded_observation_intervals(self):
        self.assertGreater(PROBE,2*W+4*NOISE[1]/DT)
        for d in (0,1):
            for sign in (-1,1):
                x1=B*((PROBE if d==0 else 0)+sign*W)
                ys=[-sign*NOISE,x1+sign*NOISE]
                self.assertTrue(candidate_feasible(ys,[PROBE],d))
                self.assertFalse(candidate_feasible(ys,[PROBE],1-d))

    def test_no_reset_and_pending_probe_at_task_start(self):
        z=np.zeros(10);e=np.zeros((11,2))
        m,rows=run(1,'probe',1,z,e)
        np.testing.assert_allclose(m['task_start_state'],[0,0],atol=1e-15)
        self.assertEqual(m['task_start_sent_history'],[PROBE])
        self.assertAlmostEqual(rows[1][6],PROBE) # applied action at task start
        m0,_=run(1,'probe',0,z,e)
        np.testing.assert_allclose(m0['task_start_state'],B*PROBE,atol=1e-15)

    def test_generated_cases_obey_bounds_and_rate(self):
        for _,w,e in cases():
            self.assertLessEqual(np.max(np.abs(w)),W+1e-15)
            self.assertLessEqual(np.max(np.abs(np.diff(w))),RATE+1e-15)
            self.assertTrue(np.all(np.abs(e)<=NOISE+1e-15))

    def test_observation_prefix_and_goal_without_preview(self):
        u=[PROBE]
        ys=[np.zeros(2),B*PROBE]
        self.assertTrue(candidate_feasible(ys,u,0))
        self.assertFalse(candidate_feasible(ys,u,1))
        cmd,info=plan(np.zeros(2),[],[0,1],2,0)
        self.assertFalse(info['certified_plan'])
        self.assertGreater(info['terminal_slack'],0)
        # A known delay admits a certified initial two-step plan.
        for d in (0,1):
            _,info=plan(np.zeros(2),[],[d],2,0)
            self.assertTrue(info['certified_plan'])

if __name__=='__main__':unittest.main()
