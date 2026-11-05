import unittest
import numpy as np
from disturbance_identification import DelayEstimator, disturbance_at, DT


class IdentificationTests(unittest.TestCase):
    def test_disturbance_interval(self):
        self.assertEqual(disturbance_at(99,True),0.)
        self.assertEqual(disturbance_at(100,True),.5)
        self.assertEqual(disturbance_at(159,True),.5)
        self.assertEqual(disturbance_at(160,True),0.)
        self.assertEqual(disturbance_at(100,False),0.)

    def test_recovery_with_excited_exact_data(self):
        e=DelayEstimator()
        commands=np.random.default_rng(123).uniform(-2,2,80)
        for k,u in enumerate(commands):
            actual=commands[k-6] if k>=6 else 0.
            e.observe(np.zeros(2),np.array([0.,actual*DT]),u)
        self.assertEqual(e.estimate,6)
        self.assertLess(e.scores[6],1e-20)

    def test_no_future_data_influence(self):
        def prefix(tail):
            e=DelayEstimator()
            estimates=[]
            commands=np.r_[np.sin(np.arange(50)*.7),tail]
            for k,u in enumerate(commands):
                estimates.append(e.estimate)
                actual=commands[k-6] if k>=6 else 0.
                e.observe(np.zeros(2),np.array([0.,actual*DT]),u)
            return estimates[:50]
        self.assertEqual(prefix(np.ones(20)),prefix(-np.ones(20)))

    def test_disturbance_can_exactly_mimic_wrong_delay(self):
        commands=np.sin(np.arange(80)*.35)
        e=DelayEstimator()
        for k,u in enumerate(commands):
            true=commands[k-6] if k>=6 else 0.
            alternative=commands[k-2] if k>=2 else 0.
            disturbance=alternative-true
            e.observe(np.zeros(2),np.array([0.,DT*(true+disturbance)]),u)
        self.assertEqual(e.estimate,2)
        self.assertGreater(e.scores[6],e.scores[2])


if __name__=='__main__': unittest.main()
