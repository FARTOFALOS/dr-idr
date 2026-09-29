"""E2c: robustness of the ex-ante anchor difference (anchor_exante.py) to residual confounding inside wide strata.
Around each anchor (starts within +-45 min): (a) 20 quantile strata of the anchor's ex-ante ratio instead of 5;
(b) logistic regression DR true ~ 1 + log r + (log r)^2 + anchored, windows of the neighbourhood pooled, the anchored
coefficient reported as the average marginal difference in pp. Day-block bootstrap (days resampled) for (b).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from anchor_placebo import dense_day  # noqa: E402
from anchor_exante import ANCH, per_start  # noqa: E402

rng = np.random.default_rng(21)


def logit_fit(X, y, it=30):
    b = np.zeros(X.shape[1])
    for _ in range(it):
        p = 1 / (1 + np.exp(-(X @ b))); W = p * (1 - p) + 1e-9
        b = b + np.linalg.solve(X.T @ (X * W[:, None]) + 1e-6 * np.eye(X.shape[1]), X.T @ (y - p))
    return b


def ame(X, b, col):
    X1 = X.copy(); X1[:, col] = 1; X0 = X.copy(); X0[:, col] = 0
    return 100 * float(np.mean(1 / (1 + np.exp(-(X1 @ b))) - 1 / (1 + np.exp(-(X0 @ b)))))


for inst in ("NQ", "ES", "YM"):
    A, d0 = dense_day(inst)
    E = {x: np.concatenate([v[:-1], v[1:]], axis=1) for x, v in A.items()}
    for a, ja in ANCH.items():
        starts = list(range(ja - 9, ja + 10))
        Q = {j: per_start(E, j) for j in starts}
        qa = Q[ja]; ma = qa["conf"] & np.isfinite(qa["ratio"]) & (qa["ratio"] > 0)
        # (a) 20 strata
        edges = np.quantile(qa["ratio"][ma], np.linspace(0, 1, 21)[1:-1])
        bins = list(zip(np.r_[-np.inf, edges], np.r_[edges, np.inf]))
        tot = wsum = 0.0
        with np.errstate(invalid="ignore"):
            for lo, hi in bins:
                sa = ma & (qa["ratio"] > lo) & (qa["ratio"] <= hi)
                if sa.sum() < 20: continue
                tn = [Q[j]["true"][Q[j]["conf"] & np.isfinite(Q[j]["ratio"]) & (Q[j]["ratio"] > lo) & (Q[j]["ratio"] <= hi)].mean()
                      for j in starts if j != ja and (Q[j]["conf"] & (Q[j]["ratio"] > lo) & (Q[j]["ratio"] <= hi)).any()]
                tot += sa.sum() * (qa["true"][sa].mean() - np.mean(tn)); wsum += sa.sum()
        strat20 = 100 * tot / wsum
        # (b) logistic regression over the neighbourhood
        rows = []
        for j in starts:
            q = Q[j]; m = q["conf"] & np.isfinite(q["ratio"]) & (q["ratio"] > 0)
            idx = np.flatnonzero(m)
            lr = np.log(q["ratio"][idx])
            rows.append(np.c_[idx, np.ones(len(idx)), lr, lr ** 2, np.full(len(idx), 1.0 if j == ja else 0.0), q["true"][idx].astype(float)])
        D = np.vstack(rows)
        X, y, day = D[:, 1:5], D[:, 5], D[:, 0].astype(int)
        b = logit_fit(X, y); est = ame(X, b, 3)
        uniq = np.unique(day); pos = {d: k for k, d in enumerate(uniq)}
        by_day = [[] for _ in uniq]
        for r_, d_ in enumerate(day): by_day[pos[d_]].append(r_)
        boots = []
        for _ in range(60):
            pick = rng.integers(0, len(uniq), len(uniq))
            ix = np.concatenate([by_day[k] for k in pick])
            bb = logit_fit(X[ix], y[ix]); boots.append(ame(X[ix], bb, 3))
        print(f"{inst} {a}: 20 strata {strat20:+.2f} pp | logistic AME {est:+.2f} pp [{np.percentile(boots, 2.5):+.2f}; {np.percentile(boots, 97.5):+.2f}]", flush=True)
