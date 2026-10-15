"""Bounded historical check of a dynamic price/time field. Protocol: sibling README.md.

No product writes. Individual rows remain under lab/.runtime/dynamic-field-2026-10-15.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "lab"))
import now24 as N
import now24_validate as V

VERSION = "DYNAMIC-FIELD-CHECK-1"
RT = ROOT / "lab/.runtime/dynamic-field-2026-10-15"
METHODS = ("CLOCK_WD", "POS_WD", "CLOCK_ALL", "POS_ALL", "CLOCK_GEO", "POS_GEO",
           "STATE_ALL", "PATH_ALL", "GAPS_ALL", "POS_K50_ALL", "STATE_K50_ALL")
KINDS = ("WINDOW_VISIT", "END_CLOSE")
OFFSETS = np.array([-10, -5, -2, 2, 5, 10], dtype=np.int64)
WINDOWS = ((1, 2, 3), (4, 5, 6), (10, 11, 12))
CELLS = [(i, j) for i in ("NQ", "ES", "YM") for j in ("ODR", "RDR")]
PAIRS = (("POS_ALL", "CLOCK_ALL"), ("STATE_K50_ALL", "POS_K50_ALL"),
         ("POS_GEO", "POS_ALL"), ("POS_WD", "CLOCK_WD"), ("POS_WD", "POS_ALL"),
         ("STATE_ALL", "POS_ALL"), ("PATH_ALL", "POS_ALL"), ("GAPS_ALL", "POS_ALL"),
         ("POS_K50_ALL", "POS_ALL"), ("POS_GEO", "CLOCK_GEO"))
SUPPORT, REPS, SEED = 20, 2000, 20261015


def hfile(p):
    return hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def stamp():
    return {str(p.relative_to(ROOT)): hfile(p) for p in
            (HERE / "README.md", HERE / "checks.py", ROOT / "lab/now24.py",
             ROOT / "lab/now24_validate.py", ROOT / "lab/scene24.py")}


def week(date):
    y, w, _ = dt.date.fromisoformat(date).isocalendar()
    return y * 100 + w


def pack(cases, grid):
    cases = sorted(cases, key=lambda x: (x["date"], x["id"]))
    P = np.stack([c["P"] for c in cases])
    S = N.stack([N.series(c["P"], c["a"], c["oppv"]) for c in cases])
    d = dict(P=P, cl=S["cl"], r=S["r"], x=S["x"], valid=S["valid"],
             grid=np.array(grid), cases=cases)
    for name in ("a", "w", "side", "win", "weekday"):
        d[name] = np.array([int(c[name]) for c in cases], np.int64)
    d["dates"] = np.array([c["date"] for c in cases], dtype="U10")
    d["year"] = np.array([int(c["date"][:4]) for c in cases], np.int16)
    d["week"] = np.array([week(c["date"]) for c in cases], np.int32)
    return d


def load(inst, block):
    cases, grid = V.universe(inst, block, "conf")
    assert all(c["date"] <= "2025-12-31" for c in cases), "closed 2026 boundary"
    d = pack(cases, grid)
    chosen = {}
    for i, case in enumerate(d["cases"]):
        if not 2016 <= int(case["date"][:4]) <= 2025:
            continue
        score = hashlib.sha256((case["id"] + "|dynamic-field-v1").encode()).hexdigest()
        wk = int(d["week"][i])
        if wk not in chosen or score < chosen[wk][0]:
            chosen[wk] = (score, i)
    d["targets"] = np.array(sorted(i for _, i in chosen.values()), np.int32)
    d["input_digest"] = hashlib.sha256(d["P"].tobytes() + d["dates"].tobytes() +
                                       d["w"].tobytes()).hexdigest()
    return d


def labels(d, c, base_k):
    """Every outcome is a label, never a selector input. Columns = window/kind/offset."""
    P, w = d["P"], d["w"]
    low = (base_k + OFFSETS - 1)[None, :] * w[:, None]
    high = low + 2 * w[:, None]
    values, specs = [], []
    for wi, delta in enumerate(WINDOWS):
        js = c + np.array(delta)
        if js[-1] >= P.shape[1]:
            continue
        part = P[:, js]
        good = ~np.isnan(part[:, :, 0])
        lo, hi = np.nan_to_num(part[:, :, 0]), np.nan_to_num(part[:, :, 1])
        hit = (good[:, :, None] & (10 * lo[:, :, None] < high[:, None, :]) &
               (10 * hi[:, :, None] >= low[:, None, :])).any(1)
        visit = np.where(hit, 1, np.where((~good).any(1)[:, None], -1, 0)).astype(np.int8)
        cl = part[:, -1, 2]
        close = np.where(np.isnan(cl)[:, None], -1,
                         ((10 * np.nan_to_num(cl)[:, None] >= low) &
                          (10 * np.nan_to_num(cl)[:, None] < high)).astype(np.int8)).astype(np.int8)
        values.extend((visit, close))
        specs.extend((wi, ki, oi) for ki in (0, 1) for oi in range(len(OFFSETS)))
    return np.concatenate(values, axis=1), np.asarray(specs, np.uint8)


def selections(d, i, c, distances=None):
    """Only closed prefixes, date, family attributes and explicit frozen feature metrics."""
    prior = int(np.searchsorted(d["dates"], d["dates"][i], side="left"))
    geo = np.flatnonzero(d["valid"][:prior, c])
    all_ = geo[(d["side"][geo] == d["side"][i]) & (d["win"][geo] == d["win"][i])]
    wd = all_[d["weekday"][all_] == d["weekday"][i]]
    w, wt = d["w"], int(d["w"][i])

    def near(ids, name, tol=(1, 4)):
        return N._near(d[name][ids, c], w[ids], d[name][i, c], wt, tol)

    pg = geo[near(geo, "cl")]
    pa = all_[near(all_, "cl")]
    pw = wd[near(wd, "cl")]
    state = pa[near(pa, "r") & near(pa, "x")]
    m2 = all_[near(all_, "r") & near(all_, "x")]
    n = min(6, c - int(d["a"][i]))
    path = np.array([], np.int64)
    if n >= 3 and len(m2):
        start = c - n + 1
        dif = np.abs(d["cl"][m2, start:c + 1] * wt -
                     d["cl"][i, start:c + 1][None, :] * w[m2, None])
        lim = w[m2] * wt
        okay = ((d["a"][m2] < start) & (5 * dif.sum(1) <= n * lim) &
                (20 * dif.max(1) <= 7 * lim))
        path = m2[okay]
    gap_r = d["cl"][all_, c] - d["r"][all_, c]
    gap_x = d["x"][all_, c] - d["cl"][all_, c]
    gaps = all_[N._near(gap_r, w[all_], d["cl"][i, c] - d["r"][i, c], wt, (1, 10)) &
                N._near(gap_x, w[all_], d["x"][i, c] - d["cl"][i, c], wt, (1, 10))]
    kp = ks = np.array([], np.int64)
    if len(all_) >= 50:
        delta = np.stack([(d[k][all_, c] / w[all_] - d[k][i, c] / wt) for k in ("cl", "r", "x")], 1)
        dp, ds = np.abs(delta[:, 0]), np.sqrt((delta ** 2).sum(1))
        ip = np.lexsort((all_, dp))[:50]
        ix = np.lexsort((all_, ds))[:50]
        kp, ks = all_[ip], all_[ix]
        if distances is not None:
            distances[0].append(float(dp[ip[-1]]))
            distances[1].append(float(ds[ix[-1]]))
    return (wd, pw, all_, pa, geo, pg, state, path, gaps, kp, ks)


def forecast(y, ids):
    if not len(ids):
        return np.zeros(y.shape[1], np.uint16), np.zeros(y.shape[1], np.uint16)
    a = y[ids]
    return (a >= 0).sum(0).astype(np.uint16), (a == 1).sum(0).astype(np.uint16)


def collect(inst, block, dry=False):
    begin = time.time()
    d = load(inst, block)
    targets = d["targets"][:4] if dry else d["targets"]
    L = len(d["grid"])
    cap = sum(int(d["valid"][targets, c].sum()) * 12 * sum(c + w[-1] < L for w in WINDOWS)
              for c in range(L - 3))
    rec = {k: np.empty(cap, dtype) for k, dtype in
           (("target", np.uint16), ("week", np.int32), ("year", np.int16), ("cut", np.uint8),
            ("window", np.uint8), ("kind", np.uint8), ("offset", np.uint8), ("y", np.int8))}
    rec.update(p=np.full((len(METHODS), cap), np.nan, np.float32),
               n=np.zeros((len(METHODS), cap), np.uint16), known=np.zeros((len(METHODS), cap), np.uint16),
               yes=np.zeros((len(METHODS), cap), np.uint16))
    pos, cuts_count = 0, 0
    distances = ([], [])
    overlap = dict(complete_windows=0,visit_multiple_price_bands=0,close_multiple_price_bands=0,visit_not_close=0)
    print(f"{inst}/{block}: cases={len(d['cases'])}, selected_weeks={len(targets)}, capacity={cap}", flush=True)
    for c in range(L - 3):
        chosen = targets[d["valid"][targets, c]]
        keys = np.floor(10 * d["cl"][chosen, c] / d["w"][chosen]).astype(np.int64)
        for k in np.unique(keys):
            ys, specs = labels(d, c, int(k))
            qn = ys.shape[1]
            for i in chosen[keys == k]:
                s = slice(pos, pos + qn)
                rec["target"][s], rec["week"][s], rec["year"][s] = i, d["week"][i], d["year"][i]
                rec["cut"][s] = c
                rec["window"][s], rec["kind"][s], rec["offset"][s] = specs.T
                rec["y"][s] = ys[i]
                for mi, ids in enumerate(selections(d, int(i), c, distances)):
                    known, yes = forecast(ys, ids)
                    rec["n"][mi, s], rec["known"][mi, s], rec["yes"][mi, s] = len(ids), known, yes
                    rec["p"][mi, s] = np.divide(yes, known, out=np.full(qn, np.nan), where=known > 0)
                for wj in np.unique(specs[:, 0]):
                    vv = ys[i, (specs[:,0] == wj) & (specs[:,1] == 0)]
                    cc = ys[i, (specs[:,0] == wj) & (specs[:,1] == 1)]
                    if (vv >= 0).all() and (cc >= 0).all():
                        overlap["complete_windows"] += 1
                        overlap["visit_multiple_price_bands"] += int((vv == 1).sum() > 1)
                        overlap["close_multiple_price_bands"] += int((cc == 1).sum() > 1)
                        overlap["visit_not_close"] += int(np.any((vv == 1) & (cc == 0)))
                pos += qn
                cuts_count += 1
        if c % 12 == 0 and len(chosen):
            print(f"  M5={c}/{L}, rows={pos}, elapsed={time.time()-begin:.1f}s",flush=True)
    assert pos == cap
    assert overlap["close_multiple_price_bands"] == 0
    meta = dict(version=VERSION,source_hashes=stamp(),instrument=inst,block=block,methods=METHODS,
                source_cases=len(d["cases"]),target_weeks=len(targets),target_cuts=cuts_count,rows=cap,
                input_digest=d["input_digest"],maximum_source_date=str(max(d["dates"])),dry=dry,
                overlap=overlap,knn_farthest_SD={m:dict(q50=float(np.median(v)),q90=float(np.quantile(v,.9)))
                         for m,v in zip(("POS_K50_ALL","STATE_K50_ALL"),distances) if v},
                elapsed_seconds=round(time.time()-begin,2))
    if not dry:
        RT.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(RT/f"{inst}_{block}.npz",**rec,meta=np.array(json.dumps(meta)))
    print(f"  COMPLETE {inst}/{block}: {cap} rows in {time.time()-begin:.1f}s" + (" (dry; no scores)" if dry else ""),flush=True)
    return meta


def semantic_checks():
    # In a future window, two candles can gap across a band without either intersecting it.
    P = np.zeros((2, 16, 3),float)
    P[0,1:4] = [[-30,-20,-25],[20,30,25],[20,30,25]]
    P[1,1:4] = [[-20,20,15],[np.nan,np.nan,np.nan],[20,30,25]]
    d = dict(P=P,w=np.array([100,100]))
    y,s = labels(d,0,2)  # offset -0.2 gives [-0.1,+0.1)
    assert y[0,2] == 0 and y[1,2] == 1 and y[1,8] == 0
    P[1,1] = [np.nan]*3
    y,_=labels(d,0,2)
    assert y[1,2] == -1, "unknown cannot become NO"
    # Same nominal price, different box widths; affine price rescaling preserves u.
    assert N._near(50,100,100,200,(1,4))
    assert not N._near(50,100,50,200,(1,5))
    assert N._near(-50,100,-100,200,(1,4))
    assert V.scene24.directed([5,0,100,-50,25],1,0) == V.scene24.directed([5,0,50,-100,-25],-1,0)
    # Selection and its date boundary on a synthetic corpus with future-dependent labels.
    cases=[]; grid=list(range(5,101,5)); c=6
    for i in range(120):
        val=100*(i%2)
        p=np.full((20,3),val,float);p[0]=np.nan
        date=(dt.date(2010,1,1)+dt.timedelta(days=i)).isoformat()
        cases.append(dict(id=str(i),date=date,weekday=0,side=1,win=0,a=0,w=100,oppv=-200,P=p))
    z=pack(cases,grid);i=119
    before=selections(z,i,c)
    assert all(np.all(z['dates'][ids] < z['dates'][i]) for ids in before)
    scaled={k:(v.copy() if isinstance(v,np.ndarray) else v) for k,v in z.items()}
    for name in ('P','cl','r','x','w'):scaled[name]=scaled[name]*7
    assert all(np.array_equal(a,b) for a,b in zip(before,selections(scaled,i,c)))
    y0,sp=labels(z,c,10)
    pk0=forecast(y0,before[METHODS.index('POS_ALL')])
    z['P'][i,c+1:]=500
    st=N.series(z['P'][i],0,-200)
    for name in ('cl','r','x','valid'):z[name][i]=st[name]
    assert all(np.array_equal(a,b) for a,b in zip(before,selections(z,i,c)))
    yy,_=labels(z,c,10)
    assert all(np.array_equal(a,b) for a,b in zip(pk0,forecast(yy,before[METHODS.index('POS_ALL')])))
    # Change the future of a matched historical member: same membership, changed label/estimate.
    j=int(before[METHODS.index('POS_ALL')][0]);z['P'][j,c+1:]=80
    st=N.series(z['P'][j],0,-200)
    for name in ('cl','r','x','valid'):z[name][j]=st[name]
    assert all(np.array_equal(a,b) for a,b in zip(before,selections(z,i,c)))
    y1,_=labels(z,c,10)
    assert not np.array_equal(y0[j],y1[j])
    assert not np.array_equal(pk0[1],forecast(y1,before[METHODS.index('POS_ALL')])[1])
    # Positive control: a known prefix feature fully determines a synthetic outcome.
    errors=[]
    for i in range(80,118):
        sets=selections(z,i,c);target=int(z['cl'][i,c]>0)
        lab=(z['cl'][:,c]>0).astype(float)
        errors.append([(lab[sets[k]].mean()-target)**2 for k in (2,3)])
    assert np.mean(errors,axis=0)[1] < np.mean(errors,axis=0)[0]
    A=set(range(14));B0=set(range(14,36));B1=set(range(22))
    assert len(B0)==len(B1)==22 and len(A&B0)==0 and len(A&B1)==14
    A60=set(range(60));B70=set(range(30,100))
    assert len(A60)+len(B70)==130 and len(A60|B70)==100
    return dict(status="PASS",checks=["range union is not min/max envelope","visit is not close",
                "UNKNOWN retained; observed YES dominates gap","SD units and reflected frame",
                "strict earlier dates and target-future invariance","member-future invariance of selection",
                "positive control: observed position adds information","same 14/22 marginals allow 0 or 100 percent conditional",
                "overlapping 60/70 shares valid on one pool of 100"],
                synthetic_percent_examples=dict(partition=[60,40],overlap=dict(A=60,B=70,intersection=30,union=100),
                    same_marginals=dict(A=14,B=22,possible_B_given_A=[0,1])))


class Acc:
    def __init__(self):
        self.rows=self.available=self.unknown=0
        self.weeks={}
        self.ns=[]
    def add(self, values, mask, target, weeks, base_mask, unknown, support=None):
        self.rows += int(base_mask.sum());self.available += int(mask.sum())
        self.unknown += int((base_mask&unknown).sum())
        if not mask.any():return
        ids=target[mask].astype(np.int64)
        sums=np.bincount(ids,weights=values[mask]);cnt=np.bincount(ids,minlength=len(sums))
        good=cnt>0;means=sums[good]/cnt[good]
        # A target has one week. Lookup does not use any outcome.
        lookup=np.zeros(len(sums),np.int32);lookup[ids]=weeks[mask]
        wks=lookup[good]
        for wk in np.unique(wks):
            a=self.weeks.setdefault(int(wk),[0.,0]);a[0]+=float(means[wks==wk].sum());a[1]+=int((wks==wk).sum())
        if support is not None:self.ns.append(support[mask].astype(np.uint16))
    def result(self,ci=False):
        out=dict(rows=self.rows,answered_rows=self.available,coverage=self.available/self.rows if self.rows else None,
                 unknown_target_rows=self.unknown,target_cases=sum(v[1] for v in self.weeks.values()),
                 weeks=len(self.weeks),mean=None)
        if self.weeks:
            sums,cnt=np.array(list(self.weeks.values())).T
            out['mean']=float(sums.sum()/cnt.sum())
            if ci:
                rng=np.random.default_rng(SEED);bs=[]
                for _ in range(REPS//100):
                    ix=rng.integers(0,len(sums),(100,len(sums)))
                    bs.extend(sums[ix].sum(1)/cnt[ix].sum(1))
                out['ci95']=[float(v) for v in np.quantile(bs,[.025,.975])]
        if self.ns:
            n=np.concatenate(self.ns);out['support_median']=float(np.median(n));out['support_p10']=float(np.quantile(n,.1))
        return out


def report():
    stats={};pairs={};cal={};meta=[]
    for inst,block in CELLS:
        file=RT/f'{inst}_{block}.npz'
        if not file.exists():raise RuntimeError('missing full declared cell '+str(file))
        with np.load(file,allow_pickle=False) as a:
            m=json.loads(str(a['meta']));assert not m['dry'] and m['source_hashes']==stamp()
            meta.append(m)
            y=a['y'];target=a['target'];wk=a['week'];yr=a['year'];kind=a['kind'];win=a['window'];off=a['offset']
            p=a['p'];nt=a['n'];nk=a['known']
            ok=(nt>=SUPPORT)&(nk>=SUPPORT)&np.isfinite(p)&(y[None,:]>=0)
            yy=np.maximum(y,0)
            errors=(p-yy[None,:])**2
            groups=[('overall',np.ones(len(y),bool)),('cell:'+inst+'/'+block,np.ones(len(y),bool))]
            groups += [('epoch:2016-19',yr<=2019),('epoch:2020-25',yr>=2020)]
            groups += [('window:'+str(j),win==j) for j in range(3)]
            groups += [('distance:'+str(v),np.abs(OFFSETS[off])==v) for v in (2,5,10)]
            groups += [('side:below',OFFSETS[off]<0),('side:above',OFFSETS[off]>0)]
            for ki,kn in enumerate(KINDS):
                for gn,gm in groups:
                    base=gm&(kind==ki)
                    for mi,mn in enumerate(METHODS):
                        key=(kn,mn,gn);acc=stats.setdefault(key,Acc())
                        acc.add(errors[mi],ok[mi]&base,target,wk,base,y<0,nt[mi] if gn=='overall' else None)
                    for aa,bb in PAIRS:
                        ia,ib=METHODS.index(aa),METHODS.index(bb)
                        acc=pairs.setdefault((kn,aa+' - '+bb,gn),Acc())
                        acc.add(errors[ia]-errors[ib],base&ok[ia]&ok[ib],target,wk,base,y<0)
                base=kind==ki
                for mi,mn in enumerate(METHODS):
                    mask=base&ok[mi]
                    bins=np.minimum((np.nan_to_num(p[mi])*10).astype(np.int16),9)
                    for bi in range(10):
                        take=mask&(bins==bi)
                        if not take.any():continue
                        row=cal.setdefault((kn,mn,bi),dict(n=0,p=0.,y=0.,weeks={}))
                        row['n']+=int(take.sum());row['p']+=float(p[mi,take].sum());row['y']+=int(yy[take].sum())
                        for w in np.unique(wk[take]):
                            mm=take&(wk==w);v=row['weeks'].setdefault(int(w),[0.,0])
                            v[0]+=int(yy[mm].sum());v[1]+=int(mm.sum())
        print('aggregated '+inst+'/'+block,flush=True)
    out=dict(version=VERSION,source_hashes=stamp(),protocol='README.md',scope='seen-history exploration; weekly sampled targets; all closed M5; 2016-2025; NQ/ES/YM ODR/RDR; no 2026',
             weighting='Brier: target means, then cases; CI resamples entire ISO-weeks. Calibration: answered query rows, weekly CI.',
             cells=meta,semantic_checks=semantic_checks(),methods=[],comparisons=[],calibration=[])
    for (kind,meth,group),acc in stats.items():
        out['methods'].append(dict(kind=kind,method=meth,group=group,**acc.result(ci=group=='overall')))
    for (kind,pair,group),acc in pairs.items():
        out['comparisons'].append(dict(kind=kind,pair=pair,group=group,negative_is_better_for_first=True,**acc.result(ci=group=='overall' or group.startswith(('cell:','epoch:')))))
    for (kind,meth,bin_),a in cal.items():
        sums,cnt=np.array(list(a['weeks'].values())).T;rng=np.random.default_rng(SEED);bs=[]
        for _ in range(REPS//100):
            ix=rng.integers(0,len(sums),(100,len(sums)));bs.extend(sums[ix].sum(1)/cnt[ix].sum(1))
        out['calibration'].append(dict(kind=kind,method=meth,bin=[bin_/10,(bin_+1)/10],n=a['n'],
                                      predicted=a['p']/a['n'],observed=a['y']/a['n'],ci95=[float(v) for v in np.quantile(bs,[.025,.975])]))
    (HERE/'results.json').write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    for k in KINDS:
        print('\n'+k,flush=True)
        for r in out['methods']:
            if r['kind']==k and r['group']=='overall':print(r['method'],round(r['coverage'],3),r['mean'],flush=True)
        for r in out['comparisons']:
            if r['kind']==k and r['group']=='overall':print(r['pair'],r['mean'],r.get('ci95'),round(r['coverage'],3),flush=True)
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');ap.add_argument('--dry',action='store_true')
    ap.add_argument('--run',action='store_true');ap.add_argument('--report',action='store_true');ap.add_argument('--cell')
    args=ap.parse_args()
    if args.check:print(json.dumps(semantic_checks(),ensure_ascii=False,indent=1))
    if args.dry:semantic_checks();collect('NQ','RDR',dry=True)
    if args.run:
        semantic_checks()
        cells=[tuple(args.cell.split('/'))] if args.cell else CELLS
        for inst,block in cells:collect(inst,block)
        if not args.cell:report()
    if args.report:report()
    if not any((args.check,args.dry,args.run,args.report)):ap.error('choose --check, --dry, --run or --report')


if __name__=='__main__':main()
