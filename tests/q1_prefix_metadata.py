"""The confirmed PR6 counterexample is fixed without modifying market metadata or old issues."""
import copy
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab'))
from q1.engine import BaseProvider,SyntheticProvider


def main():
    p=BaseProvider('NQ','RDR');k=p.B['idx'][('2025-12-17','RDR')]
    q=copy.copy(p);q.B=dict(p.B);q.B['boxes']=list(p.B['boxes']);q.B['boxes'][k]=dict(p.B['boxes'][k]);q._dig={}
    q.B['boxes'][k]['complete']=not p.B['boxes'][k]['complete'];q.B['boxes'][k]['fail']=999
    assert p.prefix_digest(k,0,670)==q.prefix_digest(k,0,670)
    print('PASS real closed prefix identity is independent of future complete/fail metadata')
    q.B['boxes'][k]['idr_low']+=1
    assert p.prefix_digest(k,0,670)!=q.prefix_digest(k,0,670)
    print('PASS a changed known frame changes prefix identity')
    grid=[605,610,615];a=dict(id='a',date='2020-01-01',a=0,w=100,side=1,win=0,weekday=2,oppv=-100,
                            complete=True,fail=None,P=np.array([[0,10,5]]*3,dtype=float))
    b=copy.deepcopy(a);b['complete']=False;b['fail']=615;b['P'][2]=[-200,100,0]
    x,y=SyntheticProvider([a],grid),SyntheticProvider([b],grid)
    assert x.prefix_digest('a',1,610)==y.prefix_digest('a',1,610)
    assert x.session_digest('a')!=y.session_digest('a')
    print('PASS target prefix stays fixed while the complete outcome source revision changes')
    print('ALL GOOD')


if __name__=='__main__':main()
