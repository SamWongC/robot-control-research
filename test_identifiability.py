import unittest
import numpy as np
from identifiability_experiment import commands_for,centered_separation,replay,disturbance_for


class PassiveTests(unittest.TestCase):
    def test_constant_and_ramp_have_zero_centered_separation(self):
        for signal in ['constant','ramp']:
            for k in [40,100,399]:
                self.assertLess(centered_separation(commands_for(signal),k),1e-25)

    def test_multisine_is_distinguishable(self):
        for k in [40,100,399]:
            self.assertGreater(centered_separation(commands_for('multisine'),k),1e-5)

    def test_noise_free_excited_identification(self):
        a=replay(commands_for('multisine'),disturbance_for('constant'),0.,0)
        np.testing.assert_array_equal(a[100:,8],6)
        np.testing.assert_allclose(a[100:,10],.5,atol=1e-11)
        self.assertLess(np.max(a[100:,28]),1e-20)  # centered score for delay six

    def test_paired_noise_and_reproducibility(self):
        u=commands_for('sine'); w=disturbance_for('zero')
        a=replay(u,w,.005,3); b=replay(u,w,.005,3)
        np.testing.assert_array_equal(a,b)
        c=replay(u,w,.005,4)
        self.assertGreater(np.max(np.abs(a[:,5]-c[:,5])),.001)
        np.testing.assert_array_equal(a[:,3:5],c[:,3:5])


if __name__=='__main__': unittest.main()
