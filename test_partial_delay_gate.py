import unittest
import csv,json
from pathlib import Path
import numpy as np
import partial_delay_gate as p

class GateTests(unittest.TestCase):
    def test_lifted_dynamics_against_simulation(self):
        rng=np.random.default_rng(93)
        for d in p.DS:
            for _ in range(20):
                x0=rng.normal(size=2);u=rng.normal(size=p.H);w=rng.normal(size=p.H)
                x=x0.copy()
                for k in range(p.H):x=p.A@x+p.B*((u[k-d] if k>=d else 0)+w[k])
                g,e=p.prediction(d)
                np.testing.assert_allclose(x,np.linalg.matrix_power(p.A,p.H)@x0+g@u+e@w,atol=1e-12)

    def test_vertices_agree_with_support(self):
        s0=p.solve((0,));s12=p.solve((1,2))
        v=p.verify_corners(s0['commands'],s12['commands'])
        predicted=np.min([x for s in (s0,s12) for x in s['physical_margins'].values()],axis=0)
        np.testing.assert_allclose(v['min_terminal_margin'],predicted,atol=1e-12)
        self.assertGreater(min(predicted),0)
        self.assertLess(max(v['max_abs_state']),2)

    def test_endpoint_overlap_is_not_lost(self):
        cells=p.cells({'0':[0,1],'1':[1,2]})
        shared=[c for c in cells if c['candidates']==[0,1]]
        self.assertEqual(len(shared),1)
        self.assertEqual(shared[0]['kind'],'point')
        self.assertEqual(shared[0]['lower'],1)

    def test_first_observation_indistinguishability(self):
        for a in [-1.,0.,.4,1.]:
            intervals=p.observation_intervals(1,a)
            self.assertEqual(intervals['1'],intervals['2'])
        cells=p.cells(p.observation_intervals(1))
        self.assertEqual({tuple(c['candidates']) for c in cells},{(),(0,),(1,2)})

    def test_complete_identification_at_time_two(self):
        intervals=p.observation_intervals(2)
        self.assertGreater(intervals['1'][0],.2)
        self.assertLess(intervals['2'][1],.2)

    def test_nonzero_action_interval(self):
        policies=[p.solve((0,)),p.solve((1,2))]
        lo,hi=p.action_interval(policies)
        self.assertLess(lo,p.FIRST);self.assertGreater(hi,p.FIRST)
        for a in [lo,(lo+hi)/2,hi]:
            for policy in policies:
                u=np.array(policy['commands']);u[0]=a
                for d in policy['delays']:
                    self.assertTrue(np.all(np.abs(p.prediction(d)[0]@u-p.GOAL)+p.radius()<=p.TOL+1e-12))

    def test_rollout_uses_only_first_observation_for_branch(self):
        u0=np.array(p.solve((0,))['commands']);u12=np.array(p.solve((1,2))['commands'])
        for d in p.DS:
            r1=p.rollout(d,np.zeros(2),np.zeros(4),np.zeros((4,2)),u0,u12)
            noise=np.zeros((4,2));noise[1:]=999 # future readings cannot change commands
            r2=p.rollout(d,np.zeros(2),np.zeros(4),noise,u0,u12)
            np.testing.assert_equal(r1[2],r2[2])

    def test_saved_trajectories_independent_audit(self):
        directory=Path(p.__file__).resolve().parent/'results'/'partial_delay_gate'
        with (directory/'trajectories.csv').open() as f: rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),6144)
        sent={};previous={}
        for row in rows:
            case,d,k=(int(row[t]) for t in ['case','delay','step']);key=(case,d)
            x=np.array([float(row['p']),float(row['v'])]); xn=np.array([float(row['p_next']),float(row['v_next'])])
            u=float(row['u']);w=float(row['w'])
            if k==0:
                sent[key]=[]
                self.assertTrue(np.all(np.abs(x)<=p.X+1e-12))
            else:np.testing.assert_allclose(x,previous[key],atol=1e-12)
            sent[key].append(u);previous[key]=xn
            np.testing.assert_allclose(xn,p.A@x+p.B*((sent[key][k-d] if k>=d else 0)+w),atol=1e-12)
            np.testing.assert_allclose([float(row['yp_next']),float(row['yv_next'])],xn+np.array([float(row['ep']),float(row['ev'])]),atol=1e-12)
            self.assertLessEqual(abs(u),1+1e-12);self.assertLessEqual(abs(w),p.W+1e-12)
            self.assertTrue(np.all(np.abs(xn)<=2+1e-12))
            if k==p.H-1:self.assertTrue(np.all(np.abs(xn-p.GOAL)<=p.TOL+1e-12))

if __name__=='__main__': unittest.main()
