"""Tests for timing semantics and controller/plant consistency."""
import unittest
import numpy as np
from experiment import DelayQueue, augmented_model, A, B, simulate


class ExperimentTests(unittest.TestCase):
    def test_zero_delay(self):
        q = DelayQueue(0)
        self.assertEqual([q.step(u) for u in [1, 2, 3]], [1, 2, 3])

    def test_fixed_delay_impulse(self):
        q = DelayQueue(3)
        self.assertEqual([q.step(u) for u in [1, 0, 0, 0, 0]], [0, 0, 0, 1, 0])

    def test_augmented_model_matches_physical_queue(self):
        for d in [0, 1, 6]:
            q = DelayQueue(d)
            aa, bb = augmented_model(d)
            x = np.array([0.2, -0.3])
            for u in [1., -2., 0., 3., 4., -1., 0., 2.]:
                z = np.r_[x, q.pending]
                predicted = aa @ z + bb[:, 0] * u
                x = A @ x + B[:, 0] * q.step(u)
                np.testing.assert_allclose(predicted, np.r_[x, q.pending], atol=1e-12)

    def test_determinism_and_known_delay_convergence(self):
        a, b = simulate(6, 6), simulate(6, 6)
        np.testing.assert_array_equal(a, b)
        self.assertLess(abs(a[-1, 1]-1.), 1e-3)
        self.assertTrue(np.isfinite(a).all())

    def test_invalid_delay(self):
        with self.assertRaises(ValueError):
            DelayQueue(-1)


if __name__ == '__main__':
    unittest.main()
