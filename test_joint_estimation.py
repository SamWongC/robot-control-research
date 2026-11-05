import unittest
import numpy as np
from experiment import A,B,DT
from joint_estimation import Estimator,AffineMPC,HORIZON,disturbance


class JointTests(unittest.TestCase):
    def test_joint_recovery_with_constant_disturbance(self):
        e=Estimator(True)
        commands=np.random.default_rng(4).uniform(-1,1,80)
        for k,u in enumerate(commands):
            a=(commands[k-6] if k>=6 else 0.)+.5
            e.observe(np.zeros(2),np.array([0.,a*DT]),u)
        self.assertEqual(e.estimate,6)
        self.assertAlmostEqual(e.biases[6],.5)
        self.assertLess(e.scores[6],1e-20)

    def test_linear_ramp_is_ambiguous_even_with_varying_commands(self):
        e=Estimator(True)
        for k in range(80):
            e.observe(np.zeros(2),np.array([0.,DT*(.01*(k-6)+.5)]),.01*k)
        self.assertLess(np.max(e.scores),1e-20)
        self.assertGreater(np.ptp(e.biases),.07)

    def test_affine_prediction_increment(self):
        c=AffineMPC(6)
        z=np.zeros(2); expected=[]
        for _ in range(HORIZON):
            z=A@z+B[:,0]*.5; expected.extend(z)
        np.testing.assert_allclose(.5*c.bias_response,expected,atol=1e-12)
        x=np.array([.2,.1]); c.bias=0.; q0=c.linear_term(x,[])
        c.bias=.5; q1=c.linear_term(x,[])
        np.testing.assert_allclose(q1-q0,2*c.G.T@(c.weights*np.array(expected)),atol=1e-10)

    def test_causal_prefix_and_disturbance_boundaries(self):
        def sequence(tail):
            e=Estimator(True); out=[]; u=np.r_[np.sin(np.arange(50)),tail]
            for k,v in enumerate(u):
                out.append(e.estimate)
                a=(u[k-6] if k>=6 else 0.)+.25
                e.observe(np.zeros(2),np.array([0.,a*DT]),v)
            return out[:50]
        self.assertEqual(sequence(np.ones(10)),sequence(-np.ones(10)))
        self.assertEqual(disturbance(100,'minus050'),-.5)
        self.assertEqual(disturbance(160,'plus050'),0.)


if __name__=='__main__': unittest.main()
