import unittest
import numpy as np
from delay_mismatch import BoxMPC, LIMIT, run_case
from experiment import A, B, augmented_model, HORIZON


class ConstrainedTests(unittest.TestCase):
    def test_lifted_predictions_match_stepwise_model(self):
        for d in [0, 2, 6, 8]:
            c = BoxMPC(d)
            aa, bb = augmented_model(d)
            z = np.linspace(-.3, .2, 2+d)
            inputs = np.linspace(-1., 1., HORIZON)
            actual, state = [], z.copy()
            for u in inputs:
                state = aa@state + bb[:, 0]*u
                actual.extend(state[:2])
            np.testing.assert_allclose(c.F@z+c.G@inputs, actual, atol=1e-12)

    def test_qp_against_independent_coordinate_solver_and_clipping(self):
        c = BoxMPC(6)
        q = c.linear_term(np.zeros(2), [])
        plan, _, _ = c.solve(np.zeros(2), [])
        objective = lambda u: .5*u@c.P@u+q@u
        # Independent cyclic coordinate descent for a strictly convex box QP.
        other = np.zeros(HORIZON)
        gradient = q.copy()
        for _ in range(10000):
            for j in range(HORIZON):
                value = np.clip(other[j]-gradient[j]/c.P[j,j], -LIMIT, LIMIT)
                delta = value-other[j]
                other[j] = value
                gradient += c.P[:,j]*delta
            residual = other-np.clip(other-(c.P@other+q), -LIMIT, LIMIT)
            if np.max(np.abs(residual)) < 1e-7:
                break
        self.assertLess(np.max(np.abs(residual)), 1e-7)
        self.assertLess(abs(objective(plan)-objective(other)), 1e-6)
        clipped = np.clip(np.linalg.solve(c.P, -q), -LIMIT, LIMIT)
        self.assertLess(objective(plan), objective(clipped)-1e-3)

    def test_unconstrained_optimum_when_bounds_inactive(self):
        c = BoxMPC(2)
        x = np.array([.999, 0.])
        plan, _, _ = c.solve(x, [])
        exact = np.linalg.solve(c.P, -c.linear_term(x, []))
        np.testing.assert_allclose(plan, exact, atol=1e-6)

    def test_rollout_input_bounds_and_actual_fixed_delay(self):
        data, _, _ = run_case(2, steps=40)
        self.assertLessEqual(np.max(np.abs(data[:, 3:5])), LIMIT+2e-6)
        np.testing.assert_allclose(data[:6, 4], 0., atol=1e-12)
        np.testing.assert_allclose(data[6:, 4], data[:-6, 3], atol=1e-12)
        for row in data:
            np.testing.assert_allclose(A@row[1:3]+B[:,0]*row[4], row[5:7], atol=1e-12)


if __name__ == '__main__':
    unittest.main()
