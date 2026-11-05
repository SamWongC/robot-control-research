"""Postprocess frozen experiment 6; never modifies calibration or replay data."""
from pathlib import Path
import csv, hashlib, json
import numpy as np


def main():
    root=Path(__file__).resolve().parent
    out=root/'results'/'candidate_sets'
    frozen=json.loads((out/'frozen_rules.json').read_text())
    assert hashlib.sha256((root/'candidate_sets.py').read_bytes()).hexdigest()==frozen['source_sha256']
    assert hashlib.sha256((out/'split_manifest.json').read_bytes()).hexdigest()==frozen['manifest_sha256']
    replay_counts={}
    for phase,expected in [('development',144),('test',480)]:
        files=sorted((out/phase).glob('replay_*.npz'))
        assert len(files)==expected
        rows=list(csv.DictReader((out/f'{phase}_metrics.csv').open()))
        assert len(rows)==expected*6
        for i,file in enumerate(files):
            with np.load(file,allow_pickle=False) as data:
                assert data['measured_velocity'].shape==(401,)
                assert data['ols_scores'].shape==data['gls_scores'].shape==(300,9)
                for row in rows[i*6:(i+1)*6]:
                    masks=data[row['method']+'_mask']
                    sets=(masks[:,None]&(1<<np.arange(9)))!=0
                    assert sets.any(axis=1).all()
                    covered=sets[:,int(row['true_delay'])]
                    assert abs(covered.mean()-float(row['coverage']))<1e-12
                    assert abs(sets.sum(axis=1).mean()-float(row['mean_size']))<1e-12
        replay_counts[phase]=len(files)
    test=json.loads((out/'test_summary.json').read_text())
    rows=list(csv.DictReader((out/'test_metrics.csv').open()))
    groups={}
    for row in rows:
        key=tuple(row[k] for k in ['method','signal','disturbance','sigma'])
        groups.setdefault(key,[]).append(float(row['coverage']))
    grouped=[dict(method=k[0],signal=k[1],disturbance=k[2],sigma=k[3],
                  coverage=float(np.mean(v)),replays=len(v)) for k,v in groups.items()]
    grouped.sort(key=lambda r:(r['method'],r['coverage']))
    with (out/'test_group_coverage.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(grouped[0])); writer.writeheader(); writer.writerows(grouped)
    worst={method:next(r for r in grouped if r['method']==method)
           for method in ['set_ols','set_gls','geometry_abstain']}
    table='| Rule | Worst input | Disturbance | Velocity noise SD | Group coverage |\n|---|---|---|---:|---:|\n'
    for m,r in worst.items(): table+=f"| {m} | {r['signal']} | {r['disturbance']} | {r['sigma']} | {r['coverage']:.1%} |\n"
    row={r['method']:r for r in test}
    en=("\n## Post-test Findings and Artifact Audit\n\n"
        f"Frozen set_ols reaches {row['set_ols']['coverage']:.1%} overall test coverage with "
        f"{row['set_ols']['mean_size']:.3f} candidates; set_gls reaches {row['set_gls']['coverage']:.1%} with "
        f"{row['set_gls']['mean_size']:.3f}. Neither dominates across groups. GLS singleton accuracy is "
        f"{row['set_gls']['singleton_accuracy']:.1%}; a singleton is not a validated certainty claim. "
        "The geometry rule also fails to maintain the nominal target in every group. The nominal overall "
        "target was met on this declared test suite, but group reliability was not. Do not connect these "
        "rules directly to a safety-critical controller. Next diagnose varying-disturbance mismatch and "
        "noise-scale sensitivity; retain this test as observed data and use a new held-out split for any "
        "revised rule. No recalibration was performed after this test.\n\n"+table+
        "\nAll 624 NPZ replay files were checked against saved coverage and mean-size metrics for every "
        "method, and frozen source/manifest hashes were verified. Analysis is descriptive; windows overlap. "
        "The clean plot is coverage_size_clean.png. To regenerate this appendix after --phase render, "
        "run analyze_candidate_sets.py.\n")
    zh=("\n## 测试后分析与文件核验\n\n"
        f"冻结的 OLS 候选集合总体覆盖率 {row['set_ols']['coverage']:.1%}、平均 "
        f"{row['set_ols']['mean_size']:.3f} 个候选；GLS 为 {row['set_gls']['coverage']:.1%}、"
        f"{row['set_gls']['mean_size']:.3f} 个。两者均未在全部组内占优。GLS 只输出单个候选时，"
        f"正确率为 {row['set_gls']['singleton_accuracy']:.1%}，不能视为确定可靠。几何规则同样不能"
        "在每组维持目标覆盖率。当前声明测试套件的总体目标达到，但组内可靠性未达到；"
        "不应直接把这些规则接入要求安全性的控制器。下一步先诊断变化外扰失配和噪声标定误差，"
        "若修改规则，应另设新的独立测试集，不能继续把本批已观察数据称为未见测试。"
        "本次未在测试后重新标定。\n\n下表为各集合规则最差的输入/扰动/噪声组。\n\n"+table+
        "\n已逐一核对 624 个 NPZ 回放与每种方法保存的覆盖率、平均集合大小，并验证冻结程序及清单哈希。"
        "分析是描述性的，重叠窗口不独立。清晰对比图为 coverage_size_clean.png。"
        "使用 --phase render 重生成报告后，再运行 analyze_candidate_sets.py 即可补回本节。\n")
    for name,marker,appendix in [('CANDIDATE_SETS_REPORT.md','\n## 测试后分析与文件核验',zh),
                                ('CANDIDATE_SETS_REPORT_EN.md','\n## Post-test Findings and Artifact Audit',en)]:
        path=root/'report'/name
        content=path.read_text(encoding='utf-8').split(marker)[0]
        content=content.replace('零/正常值/缓变正弦扰动','零扰动、正向常值扰动和缓变正弦扰动')
        path.write_text(content+appendix,encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(12,4.7),layout='constrained')
    labels=[r['method'] for r in test]
    for r in test:
        axes[0].scatter(r['mean_size'],r['coverage'],s=45)
    # Distinct annotations for the two nearly coincident score-set points.
    offsets={'point_ols':(10,-18),'point_gls':(10,8),'set_ols':(-85,22),
             'set_gls':(12,8),'geometry_abstain':(12,-28),'all':(-25,-20)}
    for r in test:
        axes[0].annotate(r['method'],(r['mean_size'],r['coverage']),xytext=offsets[r['method']],
            textcoords='offset points',fontsize=8,arrowprops=dict(arrowstyle='-',lw=.5))
    axes[0].axhline(.95,color='gray',ls='--')
    axes[0].set(xlabel='Mean candidate count',ylabel='Held-out window coverage',
                ylim=(.35,1.12),xlim=(.6,9.5),title='Held-out coverage versus candidate count')
    x=np.arange(len(test))
    axes[1].bar(x,[r['coverage'] for r in test],label='overall')
    axes[1].scatter(x,[r['worst_signal_disturbance_noise_coverage'] for r in test],
                    c='red',marker='x',label='worst group')
    axes[1].axhline(.95,c='gray',ls='--')
    axes[1].set_xticks(x,labels,rotation=35,ha='right')
    axes[1].set(ylim=(-.03,1.07),ylabel='Coverage',title='Overall success hides group failures')
    axes[1].legend(fontsize=8)
    fig.savefig(out/'coverage_size_clean.png',dpi=160); plt.close(fig)
    audit=dict(replay_files_checked=replay_counts,source_and_manifest_hashes_match=True,
               all_coverage_and_size_metrics_recomputed=True,
               frozen_rules_sha256=hashlib.sha256((out/'frozen_rules.json').read_bytes()).hexdigest(),
               analysis_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    print(json.dumps(worst,indent=2)); print(json.dumps(audit,indent=2))


if __name__=='__main__': main()
