"""Additional diagnostic declared during collection, before viewing its comparative scores.

Does the higher percentage identify the more often realised event? Same method/prefix/area sizes.
Pairs: opposite sides at equal distance and the same window; the same price band in two different windows.
Require a predicted gap >=5 percentage points. Separately report both predictions in 20-40 percent.
This does not change the frozen methods/outcomes, primary hypotheses, or any product.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from checks import HERE, RT, CELLS, METHODS, KINDS, Acc, stamp, hfile


def high_minus_low(pa,pb,ya,yb):
    return np.where(pa>=pb,ya-yb,yb-ya).astype(float)


def run():
    assert np.array_equal(high_minus_low(np.array([.8,.2]),np.array([.1,.7]),
                                       np.array([1,0]),np.array([0,1])),[1,1])
    accs={};gaps={};counts={};support={}
    for inst,block in CELLS:
        with np.load(RT/f'{inst}_{block}.npz',allow_pickle=False) as a:
            meta=json.loads(str(a['meta']));assert meta['source_hashes']==stamp()
            off,win,kind,tgt,wk,y=(a[k] for k in ('offset','window','kind','target','week','y'))
            p,nt,nk=a['p'],a['n'],a['known']
            for ki,kn in enumerate(KINDS):
                for mi,mn in enumerate(METHODS):
                    take=(kind==ki)&(nt[mi]>=20)&(nk[mi]>=20)&np.isfinite(p[mi])
                    row=support.setdefault((kn,mn),dict(answered_rows=0,rows_with_unknown_members=0,
                        member_outcomes=0,unknown_member_outcomes=0,max_unknown_fraction=0.))
                    missing=nt[mi,take].astype(np.int64)-nk[mi,take]
                    row['answered_rows']+=int(take.sum());row['rows_with_unknown_members']+=int((missing>0).sum())
                    row['member_outcomes']+=int(nt[mi,take].sum());row['unknown_member_outcomes']+=int(missing.sum())
                    if take.any():row['max_unknown_fraction']=max(row['max_unknown_fraction'],float((missing/nt[mi,take]).max()))
            ii=np.flatnonzero(off<3);jj=ii+5-2*off[ii].astype(np.int64)
            assert np.all(tgt[ii]==tgt[jj]) and np.all(a['cut'][ii]==a['cut'][jj])
            pairsets=[('opposite_sides_same_window',ii,jj)]
            for wj in (1,2):
                ii=np.flatnonzero(win==0);jj=ii+wj*12
                good=jj<len(y);ii,jj=ii[good],jj[good]
                good=(tgt[ii]==tgt[jj])&(a['cut'][ii]==a['cut'][jj])&(win[jj]==wj)&(kind[ii]==kind[jj])&(off[ii]==off[jj])
                pairsets.append(('same_price_other_time_'+str(wj),ii[good],jj[good]))
            for name,ii,jj in pairsets:
                for ki,kn in enumerate(KINDS):
                    base=kind[ii]==ki
                    unknown=(y[ii]<0)|(y[jj]<0)
                    for mi,mn in enumerate(METHODS):
                        pa,pb=p[mi,ii],p[mi,jj]
                        available=base&~unknown&np.isfinite(pa)&np.isfinite(pb)&(nt[mi,ii]>=20)&(nt[mi,jj]>=20)&(nk[mi,ii]>=20)&(nk[mi,jj]>=20)
                        diff=np.abs(pa-pb);real=high_minus_low(pa,pb,y[ii],y[jj])
                        for scope,sel in [('all_probabilities',np.ones(len(ii),bool)),
                                          ('both_20_to_40',(pa>=.2)&(pa<.4)&(pb>=.2)&(pb<.4))]:
                            take=available&sel&(diff>=.05)
                            key=(kn,mn,name,scope)
                            accs.setdefault(key,Acc()).add(real,take,tgt[ii],wk[ii],base,unknown)
                            gaps.setdefault(key,Acc()).add(diff,take,tgt[ii],wk[ii],base,unknown)
                            cc=counts.setdefault(key,dict(high_only=0,low_only=0,both=0,neither=0))
                            cc['high_only']+=int((take&(real>0)).sum());cc['low_only']+=int((take&(real<0)).sum())
                            cc['both']+=int((take&(y[ii]==1)&(y[jj]==1)).sum())
                            cc['neither']+=int((take&(y[ii]==0)&(y[jj]==0)).sum())
        print('ranked '+inst+'/'+block,flush=True)
    out=dict(scope=__doc__,source_hashes=stamp(),ranking_code_sha256=hfile(Path(__file__)),results=[],
             support_diagnostics=[dict(kind=k[0],method=k[1],**v) for k,v in support.items()])
    for key,acc in accs.items():
        kind,meth,comparison,scope=key
        out['results'].append(dict(kind=kind,method=meth,comparison=comparison,probability_scope=scope,
                                   realised_high_minus_low=acc.result(ci=True),predicted_gap=gaps[key].result(),
                                   pair_outcomes=counts[key]))
    (HERE/'ranking-results.json').write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    for r in out['results']:
        if r['method'] in ('POS_ALL','POS_GEO','STATE_K50_ALL') and r['probability_scope']=='all_probabilities':
            q=r['realised_high_minus_low'];print(r['kind'],r['method'],r['comparison'],q['mean'],q.get('ci95'),flush=True)


if __name__=='__main__':run()
