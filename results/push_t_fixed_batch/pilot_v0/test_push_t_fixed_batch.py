import unittest,json,hashlib
import numpy as np
import mujoco
from push_t_fixed_batch import OUT,load,model,Evaluator,initial,costs,FINE,COARSE,STAGE,H,K,gap

class FixedBatchTests(unittest.TestCase):
    def test_frozen_fixture_and_split(self):
        f,m=load();self.assertEqual(f['controls'].shape,(16,64,20,2))
        self.assertTrue(np.all(np.abs(f['controls'])<=.25));self.assertTrue(np.isfinite(f['qpos']).all())
        self.assertEqual(sum(x['split']=='test' for x in m['labels']),8)
        cal=json.loads((OUT/'frozen_calibration.json').read_text())
        self.assertEqual(cal['development_indices'],list(range(8)))
        self.assertTrue(cal['not_a_certificate'])

    def test_native_reference_against_direct_steps(self):
        f,_=load();ref=np.load(OUT/'reference.npz')
        for b,i in [(0,1),(8,1),(12,17),(15,42)]:
            m=model();d=mujoco.MjData(m);d.qpos[:]=f['qpos'][b];d.qvel[:]=f['qvel'][b]
            ss=[]
            for k in range(H):
                d.ctrl[:]=f['controls'][b,i,k]
                for _ in range(round(STAGE/FINE)):mujoco.mj_step(m,d)
                ss.append(np.r_[d.time,d.qpos,d.qvel])
            np.testing.assert_allclose(ss,ref['states'][b,i],atol=1e-10)
            val=costs(np.array(ss)[None],f['controls'][b,i:i+1],f['goals'][b])[0]
            self.assertAlmostEqual(val,ref['costs'][b,i],places=9)

    def test_thread_count_and_stage_stitching(self):
        f,_=load();ev=Evaluator()
        try:
            init=initial(f['qpos'][8],f['qvel'][8]);u=f['controls'][8];goal=f['goals'][8]
            a=ev.evaluate(init,u,goal,FINE,1)[0];b=ev.evaluate(init,u,goal,FINE,8)[0]
            c=ev.mixed(init,u,goal,np.ones((K,H),bool))[0]
            np.testing.assert_allclose(a,b,atol=1e-10)
            np.testing.assert_allclose(a,c,atol=1e-7,rtol=1e-7)
        finally:ev.close()

    def test_gap_geometry(self):
        # Crossbar left face at -.06, pusher radius .015.
        self.assertAlmostEqual(gap(np.array([0,0,0,-.085,.055])),.01)
        self.assertAlmostEqual(gap(np.array([0,0,0,-.075,.055])),0)

    def test_regrets_and_finite_reference(self):
        ref=np.load(OUT/'reference.npz')['costs'];self.assertTrue(np.isfinite(ref).all())
        quality=json.loads((OUT/'cpu_quality.json').read_text())
        self.assertEqual(len(quality),16*8)
        for row in quality:
            r=ref[row['batch']];self.assertAlmostEqual(row['regret'],r[row['chosen']]-min(r),places=12)
            self.assertGreaterEqual(row['regret'],-1e-12)
        times=json.loads((OUT/'cpu_timings.json').read_text())
        self.assertEqual(len(times),16*8*3)
        self.assertTrue(all(r['total_seconds']>0 for r in times))

    def test_sensor_records_and_duration(self):
        ref=np.load(OUT/'reference.npz')
        self.assertEqual(ref['contact'].shape,(16,K,H))
        self.assertGreater(ref['contact'].mean(),.01)
        np.testing.assert_allclose(ref['states'][:,:,-1,0],H*STAGE,atol=1e-12)

if __name__=='__main__':unittest.main()
