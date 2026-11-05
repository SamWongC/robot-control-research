"""MuJoCo Warp fixed-batch baseline; synchronized, graph-captured, CPU-reference comparison."""
import json,time,traceback
import numpy as np
import warp as wp
import mujoco_warp as mjw
from push_t_fixed_batch import OUT,K,H,FINE,COARSE,STAGE,load,model,costs,dump,sha

wp.config.kernel_cache_dir=str(OUT/'warp_cache')

@wp.kernel
def load_control(controls:wp.array3d(dtype=float),ctrl:wp.array2d(dtype=float),index:wp.array(dtype=int)):
    i,j=wp.tid();ctrl[i,j]=controls[i,index[0],j]

@wp.kernel
def save_state(q:wp.array2d(dtype=float),v:wp.array2d(dtype=float),tm:wp.array(dtype=float),states:wp.array3d(dtype=float),index:wp.array(dtype=int)):
    i=wp.tid();k=index[0];states[i,k,0]=tm[i]
    for j in range(5):
        states[i,k,1+j]=q[i,j];states[i,k,6+j]=v[i,j]

@wp.kernel
def advance_index(index:wp.array(dtype=int)):
    index[0]=index[0]+1

class GPU:
    def __init__(self,dt):
        self.cpu=model(dt);self.m=mjw.put_model(self.cpu)
        self.d=mjw.make_data(self.cpu,nworld=K,nconmax=16,njmax=96)
        self.u=wp.zeros((K,H,2),dtype=float);self.index=wp.zeros(1,dtype=int)
        self.states=wp.zeros((K,H,11),dtype=float);self.sub=round(STAGE/dt)
        # Warm all step kernels before graph capture.
        for _ in range(2):self.stage()
        wp.synchronize();self.index.zero_()
        with wp.ScopedCapture() as capture:self.stage()
        self.graph=capture.graph
        print('graph ready',dt,flush=True)
    def stage(self):
        wp.launch(load_control,dim=(K,2),inputs=[self.u,self.d.ctrl,self.index])
        for _ in range(self.sub):mjw.step(self.m,self.d)
        wp.launch(save_state,dim=K,inputs=[self.d.qpos,self.d.qvel,self.d.time,self.states,self.index])
        wp.launch(advance_index,dim=1,inputs=[self.index])
    def run(self,q,v,u,goal):
        start=time.perf_counter()
        mjw.reset_data(self.m,self.d);self.index.zero_()
        wp.copy(self.d.qpos,wp.array(np.repeat(q[None,:],K,axis=0).astype(np.float32),dtype=float))
        wp.copy(self.d.qvel,wp.array(np.repeat(v[None,:],K,axis=0).astype(np.float32),dtype=float))
        wp.copy(self.u,wp.array(u.astype(np.float32),dtype=float))
        for _ in range(H):wp.capture_launch(self.graph)
        wp.synchronize()
        states=self.states.numpy().astype(np.float64)
        values=costs(states,u,goal)
        if not np.isfinite(states).all() or np.any(np.diff(states[:,:,0],axis=1)<=0):raise RuntimeError('GPU divergent trajectory')
        return values,states,time.perf_counter()-start

def run():
    start=time.perf_counter();wp.init();f,man=load();ref=np.load(OUT/'reference.npz')['costs']
    timing=[];quality=[];arrays={};warm={}
    try:
      for dt,name in [(FINE,'warp_fine'),(COARSE,'warp_coarse')]:
        t=time.perf_counter();gpu=GPU(dt);warm[name]=time.perf_counter()-t
        gpu.run(f['qpos'][0],f['qvel'][0],f['controls'][0],f['goals'][0])
        allcost=[]
        for b in range(len(f['qpos'])):
          for repeat in range(3):
            values,states,elapsed=gpu.run(f['qpos'][b],f['qvel'][b],f['controls'][b],f['goals'][b])
            timing.append(dict(batch=b,split=man['labels'][b]['split'],method=name,repeat=repeat,total_seconds=elapsed))
            if repeat==0:
              chosen=int(np.argmin(values));allcost.append(values)
              quality.append(dict(batch=b,split=man['labels'][b]['split'],method=name,chosen=chosen,
                reference_best=int(np.argmin(ref[b])),regret=float(ref[b,chosen]-ref[b].min()),
                max_cost_error=float(np.max(np.abs(values-ref[b]))),exact_winner=bool(chosen==np.argmin(ref[b]))))
          print(name,b,flush=True)
        arrays[name]=allcost
      np.savez_compressed(OUT/'gpu_costs.npz',**arrays)
      dump(OUT/'gpu_timings.json',timing);dump(OUT/'gpu_quality.json',quality)
      dump(OUT/'gpu_status.json',dict(status='completed',warmup_build_seconds=warm,total_seconds=time.perf_counter()-start,
        warp=wp.__version__,source_sha256=sha(__file__),device=str(wp.get_device()),
        caveat='Float32 MuJoCo Warp, different backend; timings are not guaranteed quality-equivalent to float64 CPU reference. Includes reset, host-device transfer, synchronization, output and cost.'))
    except Exception:
      dump(OUT/'gpu_status.json',dict(status='failed',error=traceback.format_exc(),elapsed=time.perf_counter()-start))
      raise

if __name__=='__main__':run()
