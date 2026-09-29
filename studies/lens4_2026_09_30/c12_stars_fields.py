"""Checks 1 and 2 of lens 4.

1) What a star's price means. The screen (design/sozvezdiya-22/src/app.js arrivalsOf) puts a star of a similar session
   at the open of the first M5 bar that reached a place's near edge, at that bar's high (low for a pullback) clipped to
   the place. So the star's height inside the place is how far that ONE first bar went in, not where price first came
   (which is the near edge). Measured: that depth, and how it compares with how deep price went later.
2) A field of first visits and a field of visits built on a plain grid (0.1 IDR x 5 min), without the screen's three
   places, for comparison with the star field. Everything for confirmed states with the price matched ±0.25 IDR (●),
   walk-forward cohorts (years before the test year), test sessions 2016-2025, every 15 minutes.

Output: printed aggregates (-> c12_stars_fields.log) and fields.npz (mean fields over states, aggregates only).
python -B c12_stars_fields.py
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from lenscommon import INST, TEST_YEARS, Screen, dense, edges_conf, slot

HERE = Path(__file__).parent
ROWS = np.round(np.arange(-2.0, 3.0, 0.1), 2)            # row lower bounds, 50 rows of 0.1 IDR
IMG = {"RDR": 660, "ODR": 300}                           # picture moment: 11:00 RDR, 05:00 ODR; u0 in [0.25, 0.5)


def first_idx(hit):
    anyh = hit.any(1)
    return np.where(anyh, hit.argmax(1), -1)


def run(inst, sess, agg, img):
    d = dense(inst, sess)
    S = Screen(d)
    start, formed, end = d["start"], d["formed"], d["end"]
    grid = list(range(formed + 15, end - 14, 15))
    conf, fail, year = d["conf"], d["fail"], d["year"]
    K_img = (end - IMG[sess]) // 5
    acc = {k: np.zeros((len(ROWS), K_img)) for k in ("OC", "FV", "ST")}
    n_img = 0
    modes = []
    rng = np.random.default_rng(5)
    for Y in TEST_YEARS:
        test = np.flatnonzero((year == Y) & d["complete"] & (conf >= 0) & (d["side"] != 0))
        ok_years = year < Y
        for t in grid:
            s = slot(d, t)
            av = S.avail(s)
            for i in test:
                if conf[i] > t or (0 <= fail[i] <= t) or not av[i]: continue
                sel, band, u0 = S.cohort(i, t, ok_years.copy())
                if band != 0.25: continue
                up, dn = S.up[sel, s + 1:], S.dn[sel, s + 1:]
                upn, dnn = np.nan_to_num(up, nan=-np.inf), np.nan_to_num(dn, nan=np.inf)
                ar = np.arange(len(sel))
                for role, lo, hi in edges_conf(u0):
                    if role == "cont":
                        k = first_idx(upn >= lo); e = k >= 0
                        if not e.any(): continue
                        v = upn[ar[e], k[e]]; depth = np.minimum(v, hi) - lo
                        deeper = [(upn >= lo + 0.1 * r).any(1)[e].mean() for r in range(1, 5)]
                        width = hi - lo
                    else:
                        k = first_idx(dnn <= hi); e = k >= 0
                        if not e.any(): continue
                        v = dnn[ar[e], k[e]]; depth = hi - np.maximum(v, lo)
                        deeper = [(dnn <= hi - 0.1 * r).any(1)[e].mean() for r in range(1, 5)]
                        width = hi - lo
                    key = (role, "bounded" if np.isfinite(width) else "open")
                    a = agg.setdefault(key, dict(depth=[], first_bar=[], later=[], clipped=0, stars=0, row0_top=0, bands=0))
                    a["depth"].append(depth.astype(np.float32))
                    a["first_bar"].append([(depth >= 0.1 * r).mean() for r in range(1, 5)])
                    a["later"].append(deeper)
                    a["stars"] += len(depth); a["bands"] += 1
                    if np.isfinite(width): a["clipped"] += int((depth >= width - 1e-9).sum())
                    rows = np.minimum((depth / 0.1).astype(int), 4)
                    a["row0_top"] += int(np.bincount(rows, minlength=5).argmax() == 0)
                # the pictures and the modes of the visit field: one moment, u0 in [0.25, 0.5)
                if t == IMG[sess] and 0.25 <= u0 < 0.5:
                    n = len(sel); K = up.shape[1]
                    b = ROWS[None, None, :]
                    inter = (dnn[:, :, None] <= b + 0.1) & (upn[:, :, None] >= b)
                    OC = inter.mean(0).T
                    first = np.where(inter.any(1), inter.argmax(1), -1)
                    FV = np.zeros((len(ROWS), K))
                    for j in range(n):
                        m = first[j] >= 0
                        FV[np.flatnonzero(m), first[j][m]] += 1
                    FV /= n
                    ST = np.zeros((len(ROWS), K))
                    for role, lo, hi in edges_conf(u0):
                        if role == "cont":
                            k = first_idx(upn >= lo); e = k >= 0; v = np.minimum(upn[ar[e], k[e]], hi)
                        else:
                            k = first_idx(dnn <= hi); e = k >= 0; v = np.maximum(dnn[ar[e], k[e]], lo)
                        r = np.clip(np.searchsorted(ROWS, v, side="right") - 1, 0, len(ROWS) - 1)
                        np.add.at(ST, (r, k[e]), 1.0 / n)
                    for nm, F in (("OC", OC), ("FV", FV), ("ST", ST)):
                        acc[nm] += F
                    n_img += 1
                    # modes of the visit field along price, per 15-minute column from 60 minutes on, stable under a
                    # bootstrap of the similar sessions (>= 80 % of 30 resamples)
                    for c0 in range(12, K - 2, 3):
                        cnt, pos_list = 0, []
                        for bb in range(30):
                            ix = rng.integers(0, n, n)
                            col = inter[ix][:, c0:c0 + 3].any(1).mean(0)
                            pk = peaks(col)
                            cnt += len(pk) >= 2
                            if bb == 0: pos_list = [float(ROWS[p] + 0.05) for p in pk]
                        modes.append(dict(stable2=cnt >= 24, pos=pos_list, u0=float(u0)))
    img[f"{inst}-{sess}"] = dict(n=n_img, **{k: v / max(1, n_img) for k, v in acc.items()}, modes=modes)


def peaks(col):
    v = np.convolve(col, [0.25, 0.5, 0.25], mode="same")
    if v.max() <= 0: return []
    cand = [r for r in range(1, len(v) - 1) if v[r] >= v[r - 1] and v[r] > v[r + 1] and v[r] >= 0.2 * v.max()]
    out = []
    for r in cand:
        if out and v[out[-1]:r + 1].min() > 0.75 * min(v[out[-1]], v[r]):
            if v[r] > v[out[-1]]: out[-1] = r
            continue
        out.append(r)
    return out


if __name__ == "__main__":
    t0 = time.time()
    lines, save = [], {}
    for inst in INST:
        for sess in ("RDR", "ODR"):
            agg, img = {}, {}
            run(inst, sess, agg, img)
            key = f"{inst}-{sess}"
            for (role, kind), a in sorted(agg.items()):
                dep = np.concatenate(a["depth"])
                fb = np.mean(a["first_bar"], 0); lt = np.mean(a["later"], 0)
                lines.append(f"{key} {role:4s} {kind:7s} places {a['bands']:6d} stars {a['stars']:8d} | star height above the "
                             f"near edge (IDR): median {np.median(dep):.2f}, 75% {np.quantile(dep, .75):.2f}, 90% {np.quantile(dep, .9):.2f}; "
                             f"< 0.1: {100 * (dep < 0.1).mean():.0f}% | densest 0.1-row is the edge row in {100 * a['row0_top'] / a['bands']:.0f}% of places"
                             + (f" | whole place crossed by the first bar: {100 * a['clipped'] / a['stars']:.0f}%" if kind == "bounded" else ""))
                lines.append(f"{'':9s} of the sessions that came, went 0.1/0.2/0.3/0.4 IDR deeper: in the first bar "
                             + "/".join(f"{100 * x:.0f}" for x in fb) + "%, by the session end " + "/".join(f"{100 * x:.0f}" for x in lt) + "%")
            im = img[key]
            md = im["modes"]
            st = [m for m in md if m["stable2"]]
            lines.append(f"{key} picture states {im['n']}; visit-field columns (15 min, from 60 min on) with >= 2 stable price modes: "
                         f"{len(st)} of {len(md)} ({100 * len(st) / max(1, len(md)):.0f}%)")
            if st:
                pos = np.concatenate([m["pos"] for m in st])
                h, e = np.histogram(pos, bins=np.arange(-2.0, 3.01, 0.25))
                lines.append(f"{'':9s} where those modes sit (u, 0.25 bins from -2): " + " ".join(f"{e[j]:+.2f}:{h[j]}" for j in range(len(h)) if h[j]))
            for nm in ("OC", "FV", "ST"):
                save[f"{key}-{nm}"] = im[nm]
            save[f"{key}-n"] = np.array(im["n"])
            print(key, f"{time.time() - t0:.0f}s", flush=True)
    np.savez_compressed(HERE / "fields.npz", rows=ROWS, **save)
    print("\n".join(lines))
