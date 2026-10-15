"""A saved outcome cannot be illustrated with candles from another source revision."""
import copy
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab'))


def main():
    with tempfile.TemporaryDirectory(prefix='q1-reveal-') as directory:
        os.environ['Q1_STORE']=directory
        from q1 import server as S
        issue=dict(payload=dict(target=dict(instrument='NQ',block='RDR',date='2025-12-17'),cut=dict(index=0)))
        outcomes=[dict(payload=dict(revision=1,basis=dict(target_rows_digest='saved-source')))]
        original=copy.deepcopy(outcomes)
        S.STORE=SimpleNamespace(get_issue=lambda rid:issue,outcomes=lambda **kw:outcomes)
        provider=SimpleNamespace(session_digest=lambda key:'new-source',physical=lambda key:[[665,1,2,0,1],[670,1,2,0,1]])
        S.tbl=lambda *args:SimpleNamespace(row=lambda date:0,grid=[670],keys=['case'],provider=provider)
        different=S.outcome_view('issue',False)
        assert different['reveal_status']=='SOURCE_REVISION_MISMATCH' and 'after' not in different
        assert outcomes==original
        print('PASS changed source withdraws reveal and preserves the saved outcome')
        provider.session_digest=lambda key:'saved-source'
        same=S.outcome_view('issue',False)
        assert same['reveal_status']=='SOURCE_IDENTICAL' and same['after']==[[670,1,2,0,1]]
        print('PASS matching source reveals only candles after the saved cut')
        outcomes[0]['payload'].pop('basis')
        assert S.outcome_view('issue',False)['reveal_status']=='SOURCE_REVISION_MISMATCH'
        print('PASS an old outcome without a source basis is not illustrated by current candles')
    print('ALL GOOD')


if __name__=='__main__':main()
