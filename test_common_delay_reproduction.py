import unittest
import numpy as np
from reproduce_common_delay import collect,fit,history_model,check_positive,ALPHA,GAMMA


class ReproductionTests(unittest.TestCase):
    def test_true_equation_errors_and_dimensions(self):
        y,phis,u,outputs,w=collect()
        self.assertEqual(y.shape,(132,))
        self.assertEqual(u.shape,(12,16))
        for d in [1,2,3]:
            beta=[.2,.1] if d==2 else [.1,.2]
            r=y-np.r_[ALPHA,beta]@phis[d]
            np.testing.assert_allclose(r,w[:,5:16].ravel(),atol=1e-12)
            self.assertLess(r@r,GAMMA)

    def test_ellipsoid_factor_matches_information(self):
        y,phis,*_=collect()
        for d in [1,2,3]:
            model=fit(y,phis[d]); v=np.array([.2,.3,-.1,.4])
            v/=np.linalg.norm(v)
            eta=np.sqrt(model['rho'])*model['inverse_root']@v
            self.assertAlmostEqual(float(eta@(phis[d]@phis[d].T)@eta),model['rho'],places=10)
            self.assertEqual(model['rank'],4)

    def test_history_update_timing(self):
        theta=np.r_[ALPHA,[.2,.1]]
        a,b,_,_=history_model(2,theta)
        z=np.arange(7,dtype=float)/10
        nextz=a@z+b[:,0]*.7
        expected=np.r_[-theta[:2]@z[:2]+theta[2:]@z[4:6],z[0],.7,z[2:6]]
        np.testing.assert_allclose(nextz,expected)

    def test_numerical_certificate_rejects_boundary(self):
        self.assertTrue(check_positive(np.eye(3))['passed'])
        self.assertFalse(check_positive(np.diag([1.,1.,0.]))['passed'])


if __name__=='__main__': unittest.main()
