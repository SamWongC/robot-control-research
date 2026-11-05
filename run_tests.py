"""Run existing tests in their separate recorded environments."""
from pathlib import Path
import argparse,unittest,sys
ROOT=Path(__file__).resolve().parent
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite',choices=['control','contact'],required=True)
    args=parser.parse_args()
    names=[p.stem for p in sorted(ROOT.glob('test_*.py')) if (p.name=='test_push_t_fixed_batch.py')==(args.suite=='contact')]
    tests=unittest.defaultTestLoader.loadTestsFromNames(names)
    result=unittest.TextTestRunner(verbosity=2).run(tests)
    return 0 if result.wasSuccessful() else 1
if __name__=='__main__':sys.exit(main())
