"""Exploratory bridge from archived batch148 to receding-horizon control."""
import json
from pathlib import Path
import numpy as np
import push_t_closed_loop_gate as gate
OUT=gate.OUT
old=np.load(gate.ROOT/'results'/'push_t_batch148_audit'/'input.npz')
original=gate.candidates
def candidates(q,goal,previous,seed,k):
    if k==0:return old['controls'].copy()
    return original(q,goal,previous,seed,k)
gate.candidates=candidates
case=dict(id=148,q=old['qpos'].tolist(),goal=old['goal'].tolist(),seed=2026110511,family='archived148')
gate.save(OUT/'bridge_protocol.json',dict(scope='Post-confirmation exploratory bridge, not independent validation',initial_candidates='archived batch148 all64',later_candidates='new closed-loop generator; method-specific warm start and states',seed=case['seed'],first_action_difference_mps=float(np.linalg.norm(old['controls'][5,0]-old['controls'][37,0])),source_sha=gate.digest(Path(__file__))))
e=gate.Engine()
try:
    gate.execute(e,[(case,m,dt,phase) for dt,phase in [(.0003125,'bridge'),(.00015625,'bridge_half')] for m in gate.METHODS])
    cases=json.loads((OUT/'cases.json').read_text());disagreements=[]
    for c in cases:
        if c['split']!='confirmation':continue
        values=[json.loads((OUT/f"confirm_{c['id']}_{m}.json").read_text())['success'] for m in gate.METHODS]
        if len(set(values))>1:disagreements.append(c['id'])
    selected=disagreements[:8]
    gate.save(OUT/'diagnostic_protocol.json',dict(all_disagreement_ids=disagreements,selected_ids=selected,rule='first eight IDs with any success disagreement; all four methods at half execution timestep',scope='post-hoc sensitivity, not independent validation'))
    gate.execute(e,[(cases[i],m,.00015625,'diagnostic') for i in selected for m in gate.METHODS])
finally:e.close()
rows=[]
for phase in ['bridge','bridge_half']:
    for method in gate.METHODS:
        p=OUT/f'{phase}_148_{method}.json';r=json.loads(p.read_text());t=np.load(p.with_suffix('.npz'))['trace']
        r['first_choice']=int(t[0,-1]);r['phase']=phase
        rows.append({k:v for k,v in r.items() if k!='latency_ms'})
gate.save(OUT/'bridge_summary.json',rows)
print(json.dumps(rows,indent=2))
