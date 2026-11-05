import unittest
import numpy as np
import baseline_sensitivity as bs
import preview_identification as old

class BaselineSensitivityTests(unittest.TestCase):
    def test_reference_endpoints_and_derivatives(self):
        for total in (2,3,4,6,10):
            np.testing.assert_allclose(bs.reference(0,total),[0,0],atol=1e-14)
            np.testing.assert_allclose(bs.reference(total,total),old.TARGET,atol=1e-14)
            k=total*.37;delta=1e-5
            derivative=(bs.reference(k+delta,total)[0]-bs.reference(k-delta,total)[0])/(2*delta*old.DT)
            self.assertAlmostEqual(derivative,bs.reference(k,total)[1],places=9)

    def test_legacy_plan_identical(self):
        args=(np.array([.0001,-.001]),[.1],[0,1],3,1)
        a,ia=old.plan(*args);b,ib=bs.plan(*args,bs.VARIANTS[0],4)
        self.assertAlmostEqual(a,b,places=13)
        self.assertEqual(ia,ib)

    def test_lexicographic_priority_and_known_delay(self):
        for variant in bs.VARIANTS[1:]:
            _,info=bs.plan(np.zeros(2),[],[0,1],2,0,variant,2)
            self.assertFalse(info['certified_plan'])
            self.assertLessEqual(info['terminal_slack']-info['primary_optimal_slack'],1.01e-7)
            for d in (0,1):
                _,info=bs.plan(np.zeros(2),[],[d],2,0,variant,2)
                self.assertTrue(info['certified_plan'])

    def test_heldout_disjoint_and_bounds(self):
        # Separate unit-test seed; evaluation inputs remain ungenerated here.
        data=bs.test_records(seed=880129,count=8);dev=old.cases()
        self.assertEqual(len(data),8)
        for _,w,e in data:
            self.assertLessEqual(np.max(np.abs(w)),old.W+1e-15)
            self.assertLessEqual(np.max(np.abs(np.diff(w))),old.RATE+1e-15)
            self.assertTrue(np.all(np.abs(e)<=old.NOISE))
            self.assertFalse(any(np.array_equal(w,dw) for _,dw,_ in dev))

    def test_no_reset_pending_command_and_probe_off_at_zero_preview(self):
        w=np.zeros(10);e=np.zeros((11,2));v=bs.VARIANTS[1]
        m,rows=bs.run(1,v,'probe',1,w,e)
        self.assertEqual(m['task_start_history'],[.1])
        self.assertAlmostEqual(rows[1][6],.1)
        np.testing.assert_allclose(m['task_start_state'],[0,0],atol=1e-14)
        a,ra=bs.run(0,v,'passive',0,w,e);b,rb=bs.run(0,v,'probe',0,w,e)
        self.assertEqual(ra,rb)

if __name__=='__main__':unittest.main()
