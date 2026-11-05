import unittest
import numpy as np
from scipy.optimize import linprog
import causal_preview_certificate as c

class CausalCertificateTests(unittest.TestCase):
    def test_uncertainty_encodes_rate_and_noise_box(self):
        t=4;H,h=c.uncertainty(t);q=np.zeros(2+3*t)
        self.assertTrue(np.all(H@q<=h))
        q[2]=1;q[3]=-1
        self.assertTrue(np.any(H@q>h))
        q[3]=.5
        self.assertTrue(np.all(H@q<=h))

    def test_innovations_do_not_depend_on_unknown_state_or_past_controls(self):
        t=4;q=np.linspace(-.4,.4,2+3*t);Y,Z=c.observation_maps(t)
        x=q[:2]*c.INITIAL_RADIUS;w=q[2:2+t]*c.old.W;e=q[2+t:].reshape(t,2)*c.old.NOISE
        for d in (0,1):
            state=x.copy();ys=[state+e[0]];history=[]
            np.testing.assert_allclose(ys[0]/c.old.NOISE,Y@q,atol=1e-14)
            for k,u in enumerate([.05,.2,-.1]):
                applied=u if d==0 else (history[-1] if history else 0.)
                state=c.old.A@state+c.old.B*(applied+w[k]);ys.append(state+e[k+1]);history.append(u)
                z=(ys[-1]-c.old.A@ys[-2]-c.old.B*applied)/c.Z_SCALE
                np.testing.assert_allclose(z,Z[k+1]@q,atol=1e-13)

    def test_support_includes_rate_constraints(self):
        t=3;H,h=c.uncertainty(t);coef=np.zeros(2+3*t);coef[2]=1;coef[3]=-1
        val,q=c.support(coef,H,h)
        self.assertAlmostEqual(val,.5,places=10)
        self.assertTrue(np.all(H@q<=h+1e-9))

    def test_obstruction_scope_and_exact_branch_threshold(self):
        self.assertIn('all_causal',c.obstruction(0,.0002))
        self.assertIn('fixed_first',c.obstruction(1,.000225))
        self.assertIsNone(c.obstruction(1,.0002375))
        self.assertIsNone(c.obstruction(2,.0002))

    def test_saved_row_maps_match_independent_physical_execution(self):
        n=2;t=4;dim=2+3*t;rng=np.random.default_rng(773)
        q=rng.uniform(-.2,.2,dim);Y,Z=c.observation_maps(t)
        v=np.array([.05,.1,-.2,.3]);J=rng.normal(size=(t,2))*.01;J[0]=0
        K=np.zeros((t,t,2))
        for k in range(1,t):K[k,1:k+1]=rng.normal(size=(k,2))*.01
        u=v+J@(Y@q)+np.einsum('ktj,tj->k',K,Z@q)
        for d in (0,1):
            x=q[:2]*c.INITIAL_RADIUS;states=[]
            for k in range(t):
                x=c.old.A@x+c.old.B*((u[k-d] if k>=d else 0)+q[2+k]*c.old.W);states.append(x.copy())
            rows=c.constraints_numpy(v,J,K,d,n,.0002)
            evaluated={label:nom+coef@q for label,nom,coef in rows}
            for k in range(t):self.assertAlmostEqual(evaluated[f'u{k}'],u[k]/2,places=12)
            self.assertAlmostEqual(evaluated['terminal0'],(x[0]-.002)/.0002,places=11)
            self.assertAlmostEqual(evaluated['prep1_0'],states[0][0]/.01,places=12)

if __name__=='__main__':unittest.main()
