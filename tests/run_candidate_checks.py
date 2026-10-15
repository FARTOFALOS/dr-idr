"""Run unchanged PR7 acceptance tests in the separately proposed registry, never promote it in the normal server."""
import runpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab'))
import contract as C
from integration24 import REVIEW_ROOT,REVIEW_EDITION
C.BUILD=REVIEW_ROOT/'build'; C.REG_DIR=REVIEW_ROOT/'registry'
C.REGISTRY_FILE=C.BUILD/'registry.json'; C.SPEC_FILE=C.BUILD/'runtime_spec.json'; C.EDITION=REVIEW_EDITION
runpy.run_path(str(ROOT/'tests/arrive24.py'),run_name='__main__')
