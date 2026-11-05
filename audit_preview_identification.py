"""Independent saved-trajectory audit; no simulator rerun."""
from pathlib import Path
import csv,hashlib,json
import numpy as np

def main():
    root=Path(__file__).resolve().parent;out=root/'results'/'preview_identification'
    config=json.loads((out/'config.json').read_text())
    assert config['source_sha256']==hashlib.sha256((root/'preview_identification.py').read_bytes()).hexdigest()
    assert config['dependency_sha256']==hashlib.sha256((root/'task_ambiguity_scenarios.py').read_bytes()).hexdigest()
    data=np.load(out/'paired_inputs.npz')
    noise={str(n):e for n,e in zip(data['names'],data['measurement_errors'])}
    dist={str(n):w for n,w in zip(data['names'],data['disturbances'])}
    episodes=json.loads((out/'episodes.json').read_text())
    grouped={}
    with (out/'trajectories.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            key=(int(r['preview']),r['mode'],r['case'],int(r['true_delay']))
            grouped.setdefault(key,[]).append(r)
    max_recurrence=0.;max_measurement=0.;transitions=0
    for m in episodes:
        key=(m['preview'],m['mode'],m['case'],m['true_delay'])
        rows=grouped[key];commands=[];previous=np.zeros(2);prep=[]
        assert len(rows)==m['preview']+2
        for k,r in enumerate(rows):
            assert int(r['k'])==k
            state=np.array([float(r['p']),float(r['v'])])
            nxt=np.array([float(r['next_p']),float(r['next_v'])])
            measured=np.array([float(r['measured_p']),float(r['measured_v'])])
            u=float(r['command']);actual=float(r['applied']);w=float(r['disturbance'])
            assert abs(u)<=2+1e-10
            np.testing.assert_allclose(state,previous,atol=1e-13,rtol=0)
            expected_u=u if m['true_delay']==0 else (commands[-1] if commands else 0.)
            assert abs(actual-expected_u)<1e-13
            assert abs(w-dist[m['case']][k])<1e-13
            # Independent scalar recurrence, not the simulator's matrix helper.
            expected=state+np.array([.05*state[1]+.00125*(actual+w),.05*(actual+w)])
            max_recurrence=max(max_recurrence,float(np.max(np.abs(nxt-expected))))
            expected_measurement=state+noise[m['case']][k]
            max_measurement=max(max_measurement,float(np.max(np.abs(measured-expected_measurement))))
            assert str(m['true_delay']) in r['candidates'].split(';')
            if k==m['preview']:
                np.testing.assert_allclose(state,m['task_start_state'],atol=1e-13,rtol=0)
                np.testing.assert_allclose(commands,m['task_start_sent_history'],atol=1e-13,rtol=0)
            if k<m['preview']:prep.append(nxt)
            previous=nxt;commands.append(u);transitions+=1
        err=np.abs(previous-np.array([.002,.08]))
        np.testing.assert_allclose(err,[m['position_error_m'],m['velocity_error_m_s']],atol=1e-13,rtol=0)
        prep_ok=not prep or bool(np.all(np.abs(prep)<=np.array([.01,.06])+1e-10))
        success=bool(np.all(err<=np.array([.0002,.003])+1e-10) and prep_ok and m['prep_solver_failures']==0)
        assert success==m['success']
        if m['mode']=='probe' and m['preview']>0:
            assert commands[0]==.1 and m['first_single_sample']==1
    assert max_recurrence<1e-13 and max_measurement<1e-13
    # Recompute every saved aggregate success count from episode records.
    summary=json.loads((out/'summary.json').read_text())
    for g in summary['groups']:
        subset=[m for m in episodes if m['preview']==g['preview'] and m['mode']==g['mode'] and
            (g['scope']=='all' or (m['case']=='clean')==(g['scope']=='clean'))]
        assert len(subset)==g['episodes'] and sum(m['success'] for m in subset)==g['success_count']
    audit={'episodes_audited':len(episodes),'transitions_audited':transitions,
        'max_scalar_recurrence_residual':max_recurrence,'max_measurement_reconstruction_residual':max_measurement,
        'queue_continuity_and_task_start_no_reset':True,'paired_disturbances_verified':True,
        'true_delay_in_every_saved_prefix':True,'all_positive_preview_probe_singletons_at_sample_1':True,
        'summary_counts_recomputed':True}
    (out/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    print(json.dumps(audit,indent=2))

if __name__=='__main__':main()
