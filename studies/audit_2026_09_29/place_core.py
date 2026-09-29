"""E8: the number printed inside a constellation vs. the area it is printed on.

design/sozvezdiya-21/src/app.js: a place's share (drawMarks prints k.pct at the core's peak) counts every similar
session whose extreme (after the first minutes) fell in the place's price band; the drawn core is the connected region
>= 38 % of the place's own density peak that holds most of its sessions (kde: 2.5 min x 0.025 IDR grid, bilinear
splat, Gaussian 6 min x 0.06 IDR with the page's kernel); the panel's «самое плотное место» (hotOf) is the densest
0.1 IDR step inside the place and its densest 5-minute window widened to neighbours >= 60 %.
Here, on sampled confirmed states of 2016-2025 with walk-forward cohorts: band share vs core share vs hot-spot share.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import convolve1d, label

sys.path.insert(0, str(Path(__file__).parent))
from common import INST, dense  # noqa: E402
from models_vec import model_arrays, model_at  # noqa: E402
from replay_core import TEST_YEARS, prep  # noqa: E402
from screen_replay import cohort  # noqa: E402

rng = np.random.default_rng(5)


def kern(s):
    r = math.ceil(s * 3); a = np.exp(-np.arange(-r, r + 1) ** 2 / (2 * s * s)); return a / a.sum()


KX, KY = kern(6 / 2.5), kern(0.06 / 0.025)


def core_of(t, u, obs, near, end):
    if len(t) < 3: return None
    dt, du = 2.5, 0.025
    u0 = u.min() - 0.3; t0 = obs + near - 10
    nU = math.ceil((u.max() + 0.3 - u0) / du) + 1; nT = math.ceil((end + 10 - t0) / dt) + 1
    Hm = np.zeros((nU, nT))
    fx = (t - t0) / dt; fy = (u - u0) / du; ix = np.floor(fx).astype(int); iy = np.floor(fy).astype(int); ax = fx - ix; ay = fy - iy
    for dy, dx, wgt in ((0, 0, (1 - ax) * (1 - ay)), (0, 1, ax * (1 - ay)), (1, 0, (1 - ax) * ay), (1, 1, ax * ay)):
        yy, xx = iy + dy, ix + dx; ok = (yy >= 0) & (yy < nU) & (xx >= 0) & (xx < nT)
        np.add.at(Hm, (yy[ok], xx[ok]), wgt[ok])
    Hm = convolve1d(convolve1d(Hm, KX, axis=1, mode="constant"), KY, axis=0, mode="constant")
    thr = Hm.max() * 0.38
    lab, nlab = label(Hm >= thr, structure=np.ones((3, 3)))
    cx = np.floor((t - t0) / dt + 0.5).astype(int); cy = np.floor((u - u0) / du + 0.5).astype(int)
    ok = (cx >= 0) & (cx < nT) & (cy >= 0) & (cy < nU)
    comp = np.zeros(len(t), int); comp[ok] = lab[cy[ok], cx[ok]]
    if nlab == 0: return 0
    counts = np.bincount(comp, minlength=nlab + 1)[1:]
    return int(counts.max()) if counts.size else 0


def hot_of(t, u, all_t, all_u, N):
    """hotOf: densest 0.1 IDR step of the place, then its densest 5-min window widened to neighbours >= 60 %."""
    if not len(u): return None
    b = np.floor(u / 0.1 + 1e-9).astype(int)
    vals, cnt = np.unique(b, return_counts=True)
    best = vals[np.argmax(cnt)]
    inb = (np.floor(all_u / 0.1 + 1e-9).astype(int) == best)
    tt = all_t[inb]
    if not len(tt): return None
    bins = (tt - 1) // 5 * 5
    bv, bc = np.unique(bins, return_counts=True); m = dict(zip(bv.tolist(), bc.tolist()))
    pk = bv[np.argmax(bc)]; peak = m[pk]; a0, a1 = pk, pk + 5
    while m.get(a0 - 5, 0) >= 0.6 * peak: a0 -= 5
    while m.get(a1, 0) >= 0.6 * peak: a1 += 5
    return float(((tt > a0) & (tt <= a1)).sum() / N)


if __name__ == "__main__":
    for inst in INST:
        for sess in ("RDR", "ODR"):
            d = dense(inst, sess); grid, P, conf_by, fail_by = prep(d); M = model_arrays(inst, d)
            end = d["end"]
            cand = np.flatnonzero((d["year"] >= 2016) & d["complete"])
            out = {"pull": [], "cont": []}
            n_states = 0
            while n_states < 300:
                i = int(rng.choice(cand)); t = int(rng.choice(grid))
                if not P[t]["avail"][i] or not conf_by(t)[i] or fail_by(t)[i]: continue
                Y = d["year"][i]
                pool, sel, band, u0 = cohort(d, P, t, i, "conf", conf_by, fail_by, d["year"] < Y, model_at(M, t, d["start"]))
                if len(sel) < 20: continue
                n_states += 1
                near = 5 if end - t < 45 else 15
                Q = P[t]["conf"]; N = len(sel)
                s1 = math.ceil((u0 + 0.25) / 0.5) * 0.5
                for role, uu, tt, bands in (("pull", Q["mn"][sel], Q["tmn"][sel], ((-0.25, np.inf), (-0.75, -0.25), (-np.inf, -0.75))),
                                             ("cont", Q["mx"][sel], Q["tmx"][sel], ((s1 + 0.5, np.inf), (s1, s1 + 0.5), (-np.inf, s1)))):
                    far = tt > t + near
                    fu, ft = uu[far], tt[far]
                    for rank, (lo, hi) in enumerate(bands):
                        inz = (fu >= lo) & (fu < hi)
                        if inz.sum() < 3: continue
                        band_pct = inz.sum() / N
                        core = core_of(ft[inz].astype(float), fu[inz], t, near, end)
                        hot = hot_of(ft[inz], fu[inz], ft, fu, N)
                        out[role].append((band_pct, (core or 0) / N, hot if hot is not None else 0.0))
            for role, rows in out.items():
                A = np.array(rows)
                ratio = A[:, 1] / A[:, 0]
                big = A[:, 0] >= 0.2
                print(f"{inst} {sess} {role}: places {len(A)} | band share median {100 * np.median(A[:, 0]):.1f}% | core/band median {np.median(ratio):.2f} "
                      f"(p25 {np.percentile(ratio, 25):.2f}, p75 {np.percentile(ratio, 75):.2f}) | core < half the band in {100 * (ratio < 0.5).mean():.0f}% | "
                      f"for places >= 20%: core/band {np.median(ratio[big]):.2f}, hot spot/band {np.median(A[big, 2] / A[big, 0]):.2f}", flush=True)
