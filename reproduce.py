"""Run archived experiments in a new, isolated directory (standard library)."""
from pathlib import Path
import argparse,shutil,subprocess,sys

ROOT=Path(__file__).resolve().parent
COMMANDS={
    'minimal':[('experiment.py',)],
    'execution-gate':[('push_t_execution_gate.py','run'),('push_t_execution_gate.py','report')],
    'closed-loop-summary':[('summarize_push_t_closed_loop.py',)],
    'closed-loop':[('push_t_closed_loop_gate.py',),('push_t_closed_loop_bridge.py',),('summarize_push_t_closed_loop.py',)],
}
OMIT={'minimal':'minimal','execution-gate':'push_t_execution_gate','closed-loop':'push_t_closed_loop_gate'}

def prepare(experiment,output):
    target=Path(output).resolve()
    if target.exists():raise ValueError('Output already exists; choose a new directory')
    # Inventory before creating output, so a nested destination cannot copy itself.
    files=[]
    for p in ROOT.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(ROOT)
        if any(x in {'.git','runs','__pycache__','warp_cache'} or x.startswith('.venv') for x in rel.parts):continue
        if len(rel.parts)>1 and rel.parts[0]=='results' and rel.parts[1]==OMIT.get(experiment):continue
        if rel.name in {'RELEASE_MANIFEST.json','verify_release.py'}:continue
        files.append((p,rel))
    target.mkdir(parents=True)
    for src,rel in files:
        dst=target/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    return target

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiment',choices=COMMANDS,required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--prepare-only',action='store_true')
    args=parser.parse_args()
    target=prepare(args.experiment,args.output)
    print('Working copy:',target,flush=True)
    for command in COMMANDS[args.experiment]:
        print('Run:',sys.executable,*command,flush=True)
        if not args.prepare_only:
            subprocess.run([sys.executable,*command],cwd=target,check=True)

if __name__=='__main__':main()
