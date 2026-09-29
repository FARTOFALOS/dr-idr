"""E2b: the anchor question with information available before the window closes.

anchor_placebo.py explained DR true across start times by the box range over the REALISED range of the next hours (a
diagnostic). Here the denominator is ex ante: for each start time, the median post-box range of the previous 20 valid
days at that same start time. Two reads:
 1) across start times: DR true vs the median ex-ante ratio, residual at 03:00 / 09:30 / 19:30;
 2) around each anchor (starts within +-45 min, 5-min steps): windows stratified by ex-ante ratio quintile; the anchored
    start's DR true minus its neighbours' inside each stratum, weighted by the anchor's count (with a day-block
    bootstrap interval: the same days appear in every start, so days are resampled, not windows).
Horizon 240 minutes after the box for every start, as in anchor_placebo.py. Aggregates only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from anchor_placebo import HOR, dense_day  # noqa: E402

rng = np.random.default_rng(3)
ANCH = {"03:00": 36, "09:30": 114, "19:30": 234}


def per_start(E, j):
    sl = slice(j, j + 12 + HOR)
    O, H, L, C = (E[x][:, sl] for x in "OHLC")
    ok = ~(np.isnan(O).any(1) | np.isnan(H).any(1) | np.isnan(L).any(1) | np.isnan(C).any(1))
    n = O.shape[0]
    drh = np.nanmax(H[:, :12], 1); drl = np.nanmin(L[:, :12], 1)
    idrh = np.nanmax(np.maximum(O[:, :12], C[:, :12]), 1); idrl = np.nanmin(np.minimum(O[:, :12], C[:, :12]), 1)
    Cp, Hp, Lp = C[:, 12:], H[:, 12:], L[:, 12:]
    with np.errstate(invalid="ignore"):
        up = Cp > drh[:, None]; dn = Cp < drl[:, None]
    BIG = 10 ** 6
    ku = np.where(up.any(1), up.argmax(1), BIG); kd = np.where(dn.any(1), dn.argmax(1), BIG)
    side = np.where(ku < kd, 1, np.where(kd < ku, -1, 0)); k = np.minimum(ku, kd)
    later = np.arange(HOR)[None, :] > k[:, None]
    with np.errstate(invalid="ignore"):
        fail = np.where(side == 1, (later & (Cp < drl[:, None])).any(1), (later & (Cp > drh[:, None])).any(1))
    conf = ok & (side != 0) & later.any(1) & (idrh > idrl)
    W = drh - drl
    R = np.nanmax(Hp, 1) - np.nanmin(Lp, 1)
    s = pd.Series(np.where(ok, R, np.nan))
    exp_R = s.dropna().shift(1).rolling(20, min_periods=10).median().reindex(range(n)).to_numpy()
    ratio = W / exp_R
    return dict(ok=ok, conf=conf, true=~fail, ratio=ratio)


def run(inst):
    A, d0 = dense_day(inst)
    E = {x: np.concatenate([v[:-1], v[1:]], axis=1) for x, v in A.items()}
    res = {"across": [], "local": {}}
    cache = {}
    for j in range(288):
        q = per_start(E, j); cache[j] = q
        m = q["conf"] & np.isfinite(q["ratio"])
        if m.sum() >= 1500:
            res["across"].append((f"{j * 5 // 60:02d}:{j * 5 % 60:02d}", float(100 * q["true"][m].mean()), float(np.median(q["ratio"][m]))))
    t = [a[0] for a in res["across"]]; y = np.array([a[1] for a in res["across"]]); x = np.log(np.array([a[2] for a in res["across"]]))
    X = np.vstack([np.ones_like(x), x, x ** 2]).T
    b, *_ = np.linalg.lstsq(X, y, rcond=None); fit = X @ b; resid = y - fit
    r2 = 1 - ((y - fit) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    res["r2"] = float(r2); res["resid_sd"] = float(resid.std())
    res["anchor_resid"] = {a: float(resid[t.index(a)]) for a in ANCH if a in t}
    for a, ja in ANCH.items():
        neigh = [j for j in range(ja - 9, ja + 10) if j != ja]
        qa = cache[ja]
        ma = qa["conf"] & np.isfinite(qa["ratio"])
        edges = np.quantile(qa["ratio"][ma], [0.2, 0.4, 0.6, 0.8])
        bins = list(zip(np.r_[-np.inf, edges], np.r_[edges, np.inf]))
        n_days = len(ma)

        def diff(pick):
            tot = wsum = 0.0
            with np.errstate(invalid="ignore"):
                for b_lo, b_hi in bins:
                    ra = qa["ratio"][pick]
                    sa = pick[ma[pick] & (ra > b_lo) & (ra <= b_hi)]
                    if len(sa) < 20: continue
                    ta = qa["true"][sa].mean()
                    tn = []
                    for jn in neigh:
                        qn = cache[jn]; rn = qn["ratio"][pick]
                        sn = pick[qn["conf"][pick] & np.isfinite(rn) & (rn > b_lo) & (rn <= b_hi)]
                        if len(sn): tn.append(qn["true"][sn].mean())
                    if not tn: continue
                    tot += len(sa) * (ta - np.mean(tn)); wsum += len(sa)
            return 100 * tot / wsum if wsum else np.nan

        est = diff(np.arange(n_days))
        boots = []
        for _ in range(100):
            boots.append(diff(rng.integers(0, n_days, n_days)))
        res["local"][a] = dict(diff_pp=float(est), ci=[float(np.nanpercentile(boots, 2.5)), float(np.nanpercentile(boots, 97.5))])
    return res


if __name__ == "__main__":
    out = {}
    for inst in ("NQ", "ES", "YM"):
        r = run(inst); out[inst] = r
        print(inst, f"across starts: R2 {r['r2']:.3f}, resid sd {r['resid_sd']:.2f} pp,", {k: round(v, 2) for k, v in r["anchor_resid"].items()})
        for a, v in r["local"].items():
            print(f"   {a}: anchored minus neighbours at equal ex-ante ratio {v['diff_pp']:+.2f} pp [{v['ci'][0]:+.2f}; {v['ci'][1]:+.2f}]", flush=True)
    Path(__file__).with_suffix(".json").write_text(json.dumps(out), encoding="utf-8")
