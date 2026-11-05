import unittest
import numpy as np
from candidate_sets import DT,STEPS,WINDOW,scoring,observations,sets_for,metrics


class CandidateTests(unittest.TestCase):
    def test_gls_matches_direct_weighted_least_squares(self):
        rng=np.random.default_rng(5)
        u=rng.normal(size=STEPS); v=observations(u,np.full(STEPS,.4),6,.01,4)
        ols,gls,sep=scoring(v,u,.01)
        k=100; d=3
        ids=np.arange(k-WINDOW+1,k+1)
        residual=np.diff(v)[ids]/DT-u[ids-d]
        cov=(.01/DT)**2*(2*np.eye(WINDOW)-np.eye(WINDOW,k=1)-np.eye(WINDOW,k=-1))
        precision=np.linalg.inv(cov); one=np.ones(WINDOW)
        bias=(one@precision@residual)/(one@precision@one)
        expected=(residual-bias)@precision@(residual-bias)
        self.assertAlmostEqual(gls[0,d],expected,places=8)

    def test_geometry_zero_for_ramp_and_constant(self):
        for u in [np.ones(STEPS),np.arange(STEPS)*.01]:
            v=observations(u,np.zeros(STEPS),6,.01,0)
            _,_,sep=scoring(v,u,.01)
            self.assertLess(sep.max(),1e-7)

    def test_all_sets_nonempty_and_truth_not_needed(self):
        scores=np.array([[4.,1.,2.,3.,4.,5.,6.,7.,8.]])
        sets=sets_for(scores,scores,np.array([0.]),{'ols':.5,'gls':1.,'geometry':1.})
        self.assertTrue(all(s.any(axis=1).all() for s in sets.values()))
        self.assertEqual(sets['geometry_abstain'].sum(),9)
        self.assertEqual(metrics(sets['all'],6)['coverage'],1.)

    def test_causal_measurement_prefix(self):
        u=np.sin(np.arange(STEPS)*.37)
        v=observations(u,np.zeros(STEPS),6,.01,2)
        a=scoring(v,u,.01)
        changed=v.copy(); changed[250:]+=10.
        b=scoring(changed,u,.01)
        # output index n corresponds to completed transition 100+n, endpoints to 101+n
        for x,y in zip(a,b): np.testing.assert_allclose(x[:149],y[:149],atol=1e-10)


if __name__=='__main__': unittest.main()
