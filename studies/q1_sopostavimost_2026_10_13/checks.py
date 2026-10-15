"""Q1 comparability of «stood there» (13.10.2026): does the selection add information beyond the distance to the place
and the time left to the block end?

Declared before the first count in README.md of this folder (commit 4af2cce, «заявка»); this docstring restates it
briefly, the README is the reference. Exploration on the seen history 2006-2025 (2026 closed). Aggregates only: no
dates, prices or session ids leave the run.

Rows: exactly the rows of study A (studies/kadr_2026_10_12, 296 738): a confirmed session of NQ/ES/YM x ODR/RDR
replayed as today with a weekday family >= 40, cuts every 15 minutes after its activation while eligible, a place
L in {0, -1/2, -7/10} still open today, today's outcome known. Candidates for every estimator: the same instrument x
block, strictly earlier dates, eligible at the cut, not yet at L (lab/q1/engine.Table.select). Estimators differ only
by the selection inside that set:
  NODEPOS_WD, NODEPOS_ALL, GEO  the window |u - u_today| <= 1/4 on the engine's parents (the screen and D1 candidates);
  BASE_D                        the same 0.05 IDR bin of the distance to the place at the same cut (reference);
  CLOCK                         any position (context);
  BASE_DW / BASE_DP / BASE_DV   BASE_D and the same IDR width class / pullback bucket / count of nearer places reached.
An estimate is the share of YES among members with a known outcome; it exists when n >= 20.

    python -B studies/q1_sopostavimost_2026_10_13/checks.py          main count, null and positive controls -> checks.json
    python -B studies/q1_sopostavimost_2026_10_13/checks.py --dry    a code check on part of NQ ODR: shapes and time only
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "lab"))
sys.path.insert(0, str(ROOT / "studies" / "kadr_2026_10_12"))
from q1 import engine as E  # noqa: E402

E.bind_corpus()
import kadr_checks as K  # noqa: E402  helpers only (iso_week, boot_mean, adjusted, MIN_FAM, STEP); never run as a script
import now24 as N  # noqa: E402

DECLARED = "4af2cce"
LEVELS = (("0", 0, 1), ("-1/2", -1, 2), ("-7/10", -7, 10))
NEARER = {"0": (), "-1/2": ((0, 1),), "-7/10": ((0, 1), (-1, 2))}
SUP, REPS, SUB_REPS = 20, 2000, 20
EPOCHS = (("2009-12", 2009, 2012), ("2013-19", 2013, 2019), ("2020-25", 2020, 2025))
DIST_INNER = np.array([0.05, 0.10, 0.25, 0.50])
DIST_NAMES = ("0-0.05", "0.05-0.10", "0.10-0.25", "0.25-0.50", ">=0.50")
TIME_NAMES = ("<=60", "61-120", ">120")
WIDTH_NAMES = ("narrow", "usual", "wide")
PULL_NAMES = ("0-1/4", "1/4-1/2", "1/2-1", ">=1")
WINDOW_EST = ("NODEPOS_WD", "NODEPOS_ALL", "GEO")
ALL_EST = WINDOW_EST + ("BASE_D", "CLOCK", "BASE_DW", "BASE_DP", "BASE_DV")
HIST_BINS = 50                       # member shift u_m - u_today in [-1/4, 1/4], step 0.01
CAL_MIN_EPOCH_ROWS = 300
PUBLISHED = dict(rows=296738, coverage=dict(NODEPOS_WD=0.2288, NODEPOS_ALL=0.7878, GEO=0.9607),
                 median_n=dict(NODEPOS_WD=10.0, NODEPOS_ALL=49.0, GEO=354.0), geo_vs_all_diff=0.001262)
SEED_NULL, SEED_POS, SEED_SUB = 20261013, 20261014, 20261015
POS_SHARE = 0.30


# ---------------------------------------------------------------- features known at the cut
def width_classes(T):
    """0 narrow / 1 usual / 2 wide: the session's IDR width against the median width of the 20 previous confirmed sessions
    of the same instrument x block (known before the session); -1 with fewer than 20 previous sessions."""
    w = T.w.astype(np.int64)
    out = np.full(len(w), -1, np.int8)
    for j in range(20, len(w)):
        prev = np.sort(w[j - 20:j])
        m2 = int(prev[9] + prev[10])                     # twice the median of 20
        out[j] = 0 if 8 * w[j] < 3 * m2 else 2 if 3 * w[j] > 2 * m2 else 1   # < 0.75 m; > 4/3 m
    return out


def pull_bucket(xv, cl, w):
    """The pullback already made from the session's extreme, (x_seen - close) / w: [0, 1/4), [1/4, 1/2), [1/2, 1), >= 1."""
    p = xv - cl
    return np.where(4 * p < w, 0, np.where(2 * p < w, 1, np.where(p < w, 2, 3))).astype(np.int8)


def reached_nearer(r, w, nearer):
    """How many of the places nearer than L (above it) the session's post-activation low has already reached."""
    v = np.zeros(np.shape(r), np.int8)
    for pa, pb in nearer:
        v = v + (r * pb <= pa * w).astype(np.int8)
    return v


def counts(M, reach, unk):
    return M.sum(0).astype(np.int32), (M & reach).sum(0).astype(np.int32), (M & unk).sum(0).astype(np.int32)


# ---------------------------------------------------------------- rows of one instrument x block
def collect(T, uni, rows, hist, dom, limit=None):
    X = N.stack([N.series(c["P"], c["a"], c["oppv"]) for c in T.cases])["x"]
    wcls = width_classes(T)
    Lg = len(T.grid)
    tau_all = int(T.grid[-1]) - np.asarray(T.grid, dtype=np.int64)
    checked = 0
    for i in range(len(T.ids)):
        if limit is not None and dom["targets"] >= limit:
            break
        fam_wd = T.parent(i, "NODEPOS_WD")
        if len(fam_wd) < K.MIN_FAM:
            continue
        a_t, w_t = int(T.a[i]), int(T.w[i])
        cuts = np.array([c for c in range(a_t + 1, Lg - 1) if T.VALID[i, c] and (c + 1) % K.STEP == 0], dtype=int)
        if not len(cuts):
            continue
        dom["targets"] += 1
        pars = dict(NODEPOS_WD=fam_wd, NODEPOS_ALL=T.parent(i, "NODEPOS_ALL"), GEO=T.parent(i, "GEO"))
        date = str(T.dates[i])
        year, week = int(date[:4]), K.iso_week(date)
        for li, (name, la, lb) in enumerate(LEVELS):
            lvl = (la, lb)
            op = (T.CL[i, cuts] * lb > la * w_t) & (T.R[i, cuts] * lb > la * w_t)
            if not op.any():
                continue
            cs = cuts[op]
            tm = T.select(np.array([i]), cs, lvl, T.CL[i, cs], w_t)          # today's own outcome, the engine's rule
            yv = np.where(tm["reach"][0], 1, np.where(tm["unk"][0], -1, 0))
            dom["rows_open"] += len(cs)
            dom["rows_target_unknown"] += int((yv < 0).sum())
            keep = yv >= 0
            if not keep.any():
                continue
            cs, yv = cs[keep], yv[keep]
            if checked < 3 and dom["rows_open"] % 97 < 3:                    # the engine's state equals the arrays
                st = T.target_state(i, int(cs[0]), lvl)
                if st["status"] != "OPEN" or st["close_v"] != int(T.CL[i, cs[0]]) or st["r_v"] != int(T.R[i, cs[0]]):
                    raise AssertionError(f"target state differs from the table at {uni}/{i}/{cs[0]}")
                checked += 1
            clt, rt, xt = T.CL[i, cs], T.R[i, cs], X[i, cs]
            out, ms = {}, {}
            for e in WINDOW_EST:
                ms[e] = T.select(pars[e], cs, lvl, clt, w_t)
                out[e] = counts(ms[e]["match"], ms[e]["reach"], ms[e]["unk"])
            g, par = ms["GEO"], pars["GEO"]
            ny, reach, unk = g["notyet"], g["reach"], g["unk"]
            CLp = T.CL[par][:, cs]
            Wp = T.w[par][:, None].astype(np.int64)
            kb = (20 * (CLp * lb - la * Wp)) // (lb * Wp)
            kt = (20 * (clt * lb - la * w_t)) // (lb * w_t)
            mD = ny & (kb == kt[None, :])
            out["BASE_D"] = counts(mD, reach, unk)
            out["CLOCK"] = counts(ny, reach, unk)
            wc_t = int(wcls[i])
            mW = mD & (wcls[par][:, None] == wc_t) if wc_t >= 0 else np.zeros_like(mD)
            out["BASE_DW"] = counts(mW, reach, unk)
            pb = pull_bucket(X[par][:, cs], CLp, Wp)
            pt = pull_bucket(xt, clt, w_t)
            out["BASE_DP"] = counts(mD & (pb == pt[None, :]), reach, unk)
            if NEARER[name]:
                vt = reached_nearer(rt, w_t, NEARER[name])
                vb = reached_nearer(T.R[par][:, cs], Wp, NEARER[name])
                out["BASE_DV"] = counts(mD & (vb == vt[None, :]), reach, unk)
            else:
                vt = np.full(len(cs), -1, np.int8)
                z = np.zeros(len(cs), np.int32)
                out["BASE_DV"] = (z, z, z)
            dt = (clt * lb - la * w_t) / (lb * w_t)
            dcls = np.searchsorted(DIST_INNER, dt, side="right")
            ut = clt / w_t
            k = len(cs)
            for key, val in (("uni", np.full(k, uni, np.int8)), ("li", np.full(k, li, np.int8)), ("cut", cs.astype(np.int16)),
                             ("year", np.full(k, year, np.int16)), ("week", np.full(k, week, np.int32)), ("y", yv.astype(np.int8)),
                             ("d", dt.astype(np.float64)), ("kt", kt.astype(np.int32)), ("tau", tau_all[cs].astype(np.int16)),
                             ("wc", np.full(k, wc_t, np.int8)), ("pt", pt), ("vt", vt.astype(np.int8))):
                rows[key].append(val)
            for e in ALL_EST:
                n_, yes_, un_ = out[e]
                rows["n_" + e].append(n_)
                rows["yes_" + e].append(yes_)
                rows["unk_" + e].append(un_)
            for e in WINDOW_EST:                                              # where the members stood against today
                M, pe = ms[e]["match"], pars[e]
                n_e = out[e][0]
                sh = T.CL[pe][:, cs] / T.w[pe][:, None] - ut[None, :]
                with np.errstate(invalid="ignore", divide="ignore"):
                    rows["sh_" + e].append(np.where(n_e > 0, (sh * M).sum(0) / np.maximum(n_e, 1), np.nan))
                ans = n_e >= SUP
                if ans.any():
                    rr_, cc_ = np.nonzero(M[:, ans])
                    b = np.clip(np.floor((sh[:, ans][rr_, cc_] + 0.25) / 0.01).astype(np.int64), 0, HIST_BINS - 1)
                    hist[e] += np.bincount(dcls[ans][cc_] * HIST_BINS + b, minlength=len(DIST_NAMES) * HIST_BINS
                                           ).reshape(len(DIST_NAMES), HIST_BINS)


def run_rows(tables, limit=None):
    rows = {k: [] for k in ("uni", "li", "cut", "year", "week", "y", "d", "kt", "tau", "wc", "pt", "vt")}
    for e in ALL_EST:
        rows["n_" + e], rows["yes_" + e], rows["unk_" + e] = [], [], []
    for e in WINDOW_EST:
        rows["sh_" + e] = []
    hist = {e: np.zeros((len(DIST_NAMES), HIST_BINS), np.int64) for e in WINDOW_EST}
    doms = []
    for uni, (label, T) in enumerate(tables):
        t0 = time.time()
        dom = dict(universe=label, sessions=len(T.ids), targets=0, rows_open=0, rows_target_unknown=0)
        collect(T, uni, rows, hist, dom, limit)
        dom["seconds"] = round(time.time() - t0)
        doms.append(dom)
        print(f"  {label}: {dom['targets']} targets, {dom['rows_open'] - dom['rows_target_unknown']} rows, {dom['seconds']}s", flush=True)
    R = {k: np.concatenate(v) if v else np.zeros(0) for k, v in rows.items()}
    R["p"], R["a"] = {}, {}
    for e in ALL_EST:
        n, yes, un = R["n_" + e], R["yes_" + e], R["unk_" + e]
        kn = n - un
        a = (n >= SUP) & (kn > 0)
        p = np.full(len(n), np.nan)
        p[a] = yes[a] / kn[a]
        R["p"][e], R["a"][e] = p, a
    return R, hist, doms


# ---------------------------------------------------------------- reading
def r6(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), 6)


def epoch_masks(year):
    return [(nm, (year >= a) & (year <= b)) for nm, a, b in EPOCHS]


def compare(R, y, X, ref, seed, mask=None):
    """Paired Brier X - ref on the rows where both answer; negative favours X."""
    c = R["a"][X] & R["a"][ref]
    if mask is not None:
        c &= mask
    if not c.any():
        return dict(rows=0, verdict="NO_COMMON_ROWS")
    yy = y[c].astype(float)
    bX, br = (R["p"][X][c] - yy) ** 2, (R["p"][ref][c] - yy) ** 2
    diff = bX - br
    mean, lo, hi = K.boot_mean(diff, R["week"][c], REPS, seed)
    ep = {nm: dict(rows=int(m.sum()), diff=r6(diff[m].mean()) if m.any() else None) for nm, m in epoch_masks(R["year"][c])}
    skill = 1 - float(bX.mean()) / float(br.mean())
    same = all(v["rows"] > 0 and v["diff"] < 0 for v in ep.values())
    verdict = ("ESTABLISHED" if hi < 0 and same and skill >= 0.01 else "REFUTED_AS_IMPROVEMENT" if lo > 0 else "NOT_ESTABLISHED")
    return dict(rows=int(c.sum()), share_of_rows=r6(c.mean()), base_rate=r6(yy.mean()), brier_X=r6(bX.mean()),
                brier_ref=r6(br.mean()), diff=r6(mean), lo=r6(lo), hi=r6(hi), rel_skill=r6(skill),
                median_n_X=r6(np.median(R["n_" + X][c])), median_n_ref=r6(np.median(R["n_" + ref][c])), epochs=ep, verdict=verdict)


def subsample_p(n, yes, unk, m, rng):
    """The share of YES among known after keeping m of n members (without replacement); unchanged where n == m."""
    ys, kn = yes.astype(np.int64).copy(), (n - unk).astype(np.int64).copy()
    big = n > m
    if big.any():
        nb, yb, ub, mb = n[big].astype(np.int64), yes[big].astype(np.int64), unk[big].astype(np.int64), m[big].astype(np.int64)
        y_s = rng.hypergeometric(yb, nb - yb, mb)
        rest = mb - y_s
        ok = rest > 0
        no_b = nb - yb - ub
        n_s = np.where(ok, rng.hypergeometric(np.where(ok, no_b, 1), np.where(ok, ub, 0), np.where(ok, rest, 1)), 0)
        ys[big], kn[big] = y_s, y_s + n_s
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(kn > 0, ys / np.maximum(kn, 1), np.nan)


def support_control(R, y, X, ref, seed):
    """The same comparison with the larger member set cut to the smaller n, row by row (a diagnostic of size)."""
    c = R["a"][X] & R["a"][ref]
    if not c.any():
        return dict(rows=0)
    yy = y[c].astype(float)
    nX, yX, uX = R["n_" + X][c], R["yes_" + X][c], R["unk_" + X][c]
    nr, yr, ur = R["n_" + ref][c], R["yes_" + ref][c], R["unk_" + ref][c]
    m = np.minimum(nX, nr)
    rng = np.random.default_rng(seed)
    acc, cnt = np.zeros(len(yy)), np.zeros(len(yy))
    for _ in range(SUB_REPS):
        pX, pr = subsample_p(nX, yX, uX, m, rng), subsample_p(nr, yr, ur, m, rng)
        ok = ~np.isnan(pX) & ~np.isnan(pr)
        acc[ok] += (pX[ok] - yy[ok]) ** 2 - (pr[ok] - yy[ok]) ** 2
        cnt[ok] += 1
    k = cnt > 0
    diff = acc[k] / cnt[k]
    mean, lo, hi = K.boot_mean(diff, R["week"][c][k], REPS, seed)
    ep = {nm: r6(diff[mm].mean()) if mm.any() else None for nm, mm in epoch_masks(R["year"][c][k])}
    return dict(rows=int(k.sum()), equal_n_median=r6(np.median(m[k])), diff=r6(mean), lo=r6(lo), hi=r6(hi), epochs=ep)


def calibration(R, y, e, mask, seed):
    c = R["a"][e] & mask
    out = dict(rows_in_class=int(mask.sum()), rows=int(c.sum()), coverage=r6(c.sum() / max(mask.sum(), 1)),
               median_n=r6(np.median(R["n_" + e][mask])) if mask.any() else None)
    if not c.any():
        return out
    diff = R["p"][e][c] - y[c]
    mean, lo, hi = K.boot_mean(diff, R["week"][c], REPS, seed)
    ep = {nm: dict(rows=int(m.sum()), gap=r6(diff[m].mean()) if m.any() else None) for nm, m in epoch_masks(R["year"][c])}
    ev = [v["gap"] for v in ep.values() if v["rows"] >= CAL_MIN_EPOCH_ROWS]
    same = len(ev) >= 2 and (all(g > 0 for g in ev) or all(g < 0 for g in ev)) and np.sign(ev[0]) == np.sign(mean)
    out.update(mean_estimate=r6(R["p"][e][c].mean()), observed=r6(y[c].mean()), gap=r6(mean), lo=r6(lo), hi=r6(hi), epochs=ep,
               material=bool(abs(mean) >= 0.05 and (lo > 0 or hi < 0) and same))
    return out


def strata(R, sel):
    key = np.stack([R["uni"][sel], R["li"][sel], R["cut"][sel], R["kt"][sel]], 1)
    return np.unique(key, axis=0, return_inverse=True)[1].ravel()


def info_pair(R, y, var, a_val, b_val, mask, seed):
    """Stratum-adjusted difference of today's reach rate, group a minus group b, at the same instrument x block, place,
    cut and 0.05 IDR distance bin (kadr_checks.adjusted; ISO weeks resampled)."""
    sel = mask & ((var == a_val) | (var == b_val))
    if not sel.any():
        return dict(rows=0, verdict="NO_ROWS")
    yy, g, sid, wk, yr = y[sel].astype(float), np.where(var[sel] == a_val, 0, 1), strata(R, sel), R["week"][sel], R["year"][sel]
    delta = K.adjusted(yy, g, sid, np.ones(len(yy)))
    uw, inv = np.unique(wk, return_inverse=True)
    rng = np.random.default_rng(seed)
    bs = np.empty(REPS)
    for b in range(REPS):
        mlt = np.bincount(rng.integers(0, len(uw), len(uw)), minlength=len(uw)).astype(float)
        bs[b] = K.adjusted(yy, g, sid, mlt[inv])
    lo, hi = float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))
    ep = {}
    for nm, m in epoch_masks(yr):
        ep[nm] = r6(K.adjusted(yy[m], g[m], np.unique(sid[m], return_inverse=True)[1], np.ones(int(m.sum())))) if m.any() and (g[m] == 0).any() and (g[m] == 1).any() else None
    Kn = int(sid.max()) + 1
    nA, nB = np.bincount(sid, weights=(g == 0).astype(float), minlength=Kn), np.bincount(sid, weights=(g == 1).astype(float), minlength=Kn)
    both = (nA > 0) & (nB > 0)
    same = all(v is not None and np.sign(v) == np.sign(delta) and v != 0 for v in ep.values())
    est = bool(delta == delta and abs(delta) >= 0.05 and (lo > 0 or hi < 0) and same)
    return dict(rows_A=int((g == 0).sum()), rows_B=int((g == 1).sum()), rows_in_shared_strata=int(both[sid].sum()),
                rate_A=r6(yy[g == 0].mean()) if (g == 0).any() else None, rate_B=r6(yy[g == 1].mean()) if (g == 1).any() else None,
                adjusted_diff=r6(delta), lo=r6(lo), hi=r6(hi), epochs=ep, verdict="ESTABLISHED" if est else "NOT_ESTABLISHED")


def feature_tests(R, y, seeds):
    """P4-P6: information (stratum-adjusted) and prediction (BASE_D + feature against BASE_D)."""
    lv = R["li"]
    out = dict(P4=dict(information={}, prediction=None), P5=dict(information={}, prediction=None),
               P6=dict(information={}, prediction=None))
    allr = np.ones(len(y), bool)
    out["P4"]["information"]["narrow-usual"] = info_pair(R, y, R["wc"], 0, 1, allr, seeds[0])
    out["P4"]["information"]["wide-usual"] = info_pair(R, y, R["wc"], 2, 1, allr, seeds[1])
    out["P4"]["prediction"] = compare(R, y, "BASE_DW", "BASE_D", seeds[2])
    for k, nm in enumerate(PULL_NAMES[1:], start=1):
        out["P5"]["information"][f"{nm} - {PULL_NAMES[0]}"] = info_pair(R, y, R["pt"], k, 0, allr, seeds[3] + k)
    out["P5"]["prediction"] = compare(R, y, "BASE_DP", "BASE_D", seeds[4])
    out["P6"]["information"]["-1/2: v1-v0"] = info_pair(R, y, R["vt"], 1, 0, lv == 1, seeds[5])
    out["P6"]["information"]["-7/10: v1-v0"] = info_pair(R, y, R["vt"], 1, 0, lv == 2, seeds[6])
    out["P6"]["information"]["-7/10: v2-v0"] = info_pair(R, y, R["vt"], 2, 0, lv == 2, seeds[7])
    out["P6"]["prediction"] = compare(R, y, "BASE_DV", "BASE_D", seeds[8], mask=lv >= 1)
    for p in ("P4", "P5", "P6"):
        out[p]["information_verdict"] = ("ESTABLISHED" if any(v.get("verdict") == "ESTABLISHED" for v in out[p]["information"].values())
                                         else "NOT_ESTABLISHED")
    return out


def quantiles_from_hist(h):
    tot = h.sum()
    if tot == 0:
        return None
    cdf = np.cumsum(h) / tot
    centers = -0.25 + 0.01 * (np.arange(HIST_BINS) + 0.5)
    return {f"q{int(q * 100)}": r6(centers[int(np.searchsorted(cdf, q))]) for q in (0.10, 0.25, 0.50, 0.75, 0.90)}


def analyse(R, hist):
    y = R["y"].astype(float)
    dcls = np.searchsorted(DIST_INNER, R["d"], side="right")
    tcls = np.where(R["tau"] <= 60, 0, np.where(R["tau"] <= 120, 1, 2))
    res = dict(rows=int(len(y)), base_rate=r6(y.mean()),
               rows_by_epoch={nm: int(m.sum()) for nm, m in epoch_masks(R["year"])},
               coverage={e: dict(share_n_ge_20=r6((R["n_" + e] >= SUP).mean()), median_n=r6(np.median(R["n_" + e])),
                                 answered=r6(R["a"][e].mean())) for e in ALL_EST})
    s1 = dict(P1=compare(R, y, "NODEPOS_WD", "BASE_D", 101), P2=compare(R, y, "NODEPOS_ALL", "BASE_D", 102),
              P3=compare(R, y, "GEO", "BASE_D", 103), context_CLOCK=compare(R, y, "CLOCK", "BASE_D", 104))
    s1["support_control"] = {p: support_control(R, y, X, "BASE_D", SEED_SUB + k)
                             for k, (p, X) in enumerate((("P1", "NODEPOS_WD"), ("P2", "NODEPOS_ALL"), ("P3", "GEO")))}
    s1["calibration"] = {}
    for e in ("NODEPOS_WD", "NODEPOS_ALL", "GEO", "BASE_D"):
        s1["calibration"][e] = dict(
            by_distance={nm: calibration(R, y, e, dcls == k, 200 + 10 * k) for k, nm in enumerate(DIST_NAMES)},
            by_time_left={nm: calibration(R, y, e, tcls == k, 300 + 10 * k) for k, nm in enumerate(TIME_NAMES)})
    s1["situations"] = {nm: dict(rows=int((dcls == k).sum()), share=r6((dcls == k).mean())) for k, nm in enumerate(DIST_NAMES)}
    s1["distances"] = {}
    for e in WINDOW_EST:
        sh, a = R["sh_" + e], R["a"][e]
        s1["distances"][e] = {}
        for k, nm in enumerate(DIST_NAMES):
            m = a & (dcls == k)
            s1["distances"][e][nm] = dict(
                rows=int(m.sum()),
                row_mean_shift=dict(mean=r6(sh[m].mean()) if m.any() else None,
                                    **({f"q{q}": r6(np.percentile(sh[m], q)) for q in (10, 25, 50, 75, 90)} if m.any() else {})),
                members=quantiles_from_hist(hist[e][k]))
    s2 = dict(width_classes={nm: dict(rows=int((R["wc"] == k).sum())) for k, nm in enumerate(WIDTH_NAMES)},
              calibration_BASE_D_by_width={nm: calibration(R, y, "BASE_D", R["wc"] == k, 400 + 10 * k) for k, nm in enumerate(WIDTH_NAMES)})
    f = feature_tests(R, y, (501, 502, 503, 510, 520, 531, 532, 533, 540))
    s2["P4"] = f["P4"]
    s3 = dict(P5=f["P5"], P6=f["P6"],
              pull_buckets={nm: int((R["pt"] == k).sum()) for k, nm in enumerate(PULL_NAMES)},
              nearer_reached={f"{LEVELS[li][0]}: v{v}": int(((R["li"] == li) & (R["vt"] == v)).sum()) for li in (1, 2) for v in range(li + 1)})
    return res, s1, s2, s3


def null_control(R, seed):
    """Today's outcomes permuted inside (instrument x block, place, cut, 0.05 bin): nothing may come out established."""
    sid = strata(R, np.ones(len(R["y"]), bool))
    rng = np.random.default_rng(seed)
    o = np.argsort(sid, kind="stable")
    o2 = np.lexsort((rng.random(len(sid)), sid))
    yp = np.empty_like(R["y"])
    yp[o] = R["y"][o2]
    y = yp.astype(float)
    f = feature_tests(R, y, (601, 602, 603, 610, 620, 631, 632, 633, 640))
    out = dict(P1=compare(R, y, "NODEPOS_WD", "BASE_D", 701)["verdict"], P2=compare(R, y, "NODEPOS_ALL", "BASE_D", 702)["verdict"],
               P3=compare(R, y, "GEO", "BASE_D", 703)["verdict"])
    for p in ("P4", "P5", "P6"):
        out[p] = dict(information=f[p]["information_verdict"], prediction=f[p]["prediction"]["verdict"],
                      pairs={k: dict(diff=v.get("adjusted_diff"), lo=v.get("lo"), hi=v.get("hi")) for k, v in f[p]["information"].items()})
    out["passed"] = not any(v == "ESTABLISHED" for v in (out["P1"], out["P2"], out["P3"])) and not any(
        out[p]["information"] == "ESTABLISHED" or out[p]["prediction"] == "ESTABLISHED" for p in ("P4", "P5", "P6"))
    return out


def positive_control(seed):
    """NQ only, in memory: 30 % of the narrow-box sessions reach every place at every cut (as today and as members)."""
    tables = []
    rng = np.random.default_rng(seed)
    for blk in ("ODR", "RDR"):
        T = E.table("NQ", blk)
        T2 = copy.copy(T)
        wc = width_classes(T)
        pick = (wc == 0) & (rng.random(len(wc)) < POS_SHARE)
        fm = T.FMIN.copy()
        fm[pick, :] = -np.inf
        T2.FMIN = fm
        tables.append((f"NQ {blk} (injected)", T2))
    R, _, doms = run_rows(tables)
    y = R["y"].astype(float)
    inf = info_pair(R, y, R["wc"], 0, 1, np.ones(len(y), bool), 801)
    pred = compare(R, y, "BASE_DW", "BASE_D", 802)
    return dict(universes=doms, rows=int(len(y)), information_narrow_usual=inf, prediction_BASE_DW_vs_BASE_D=pred,
                passed=bool(inf["verdict"] == "ESTABLISHED" and pred["verdict"] == "ESTABLISHED"))


def git_head():
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    except Exception:
        return None


def main():
    dry = "--dry" in sys.argv
    t0 = time.time()
    if dry:
        R, hist, doms = run_rows([("NQ ODR", E.table("NQ", "ODR"))], limit=300)
        print("dry run:", len(R["y"]), "rows;", {k: v.shape for k, v in list(R.items())[:6] if hasattr(v, "shape")},
              f"{time.time() - t0:.0f}s")
        return
    print("main count", flush=True)
    tables = [(f"{inst} {blk}", E.table(inst, blk)) for inst in K.INSTS for blk in K.SESSIONS]
    R, hist, doms = run_rows(tables)
    y = R["y"].astype(float)
    anchors = dict(rows=int(len(y)), coverage={e: r6(round(float((R["n_" + e] >= SUP).mean()), 4)) for e in WINDOW_EST},
                   median_n={e: float(np.median(R["n_" + e])) for e in WINDOW_EST})
    gva = compare(R, y, "GEO", "NODEPOS_ALL", 1)
    anchors["geo_vs_nodepos_all_diff"] = r6(-gva["diff"]) if gva.get("diff") is not None else None
    ok = (anchors["rows"] == PUBLISHED["rows"] and anchors["coverage"] == PUBLISHED["coverage"]
          and anchors["median_n"] == PUBLISHED["median_n"]
          and anchors["geo_vs_nodepos_all_diff"] is not None and round(anchors["geo_vs_nodepos_all_diff"], 6) == PUBLISHED["geo_vs_all_diff"])
    anchors["identical_to_published_A_D"] = bool(ok)
    print("anchors:", anchors, flush=True)
    if not ok:
        raise SystemExit("the rows or members differ from the published A/D: the count stops here (README §2)")
    print("reading", flush=True)
    res, s1, s2, s3 = analyse(R, hist)
    print("null control", flush=True)
    nc = null_control(R, SEED_NULL)
    print("positive control", flush=True)
    pc = positive_control(SEED_POS)
    out = dict(study="Q1 comparability of «stood there» (13.10.2026)", declared_in=DECLARED, code_commit=git_head(),
               engine_model=E.MODEL, corpus=dict((lbl, T.provider.version) for lbl, T in tables), history="2006-2025 (2026 closed)",
               domain=doms, anchors=anchors, rows=res, step1=s1, step2=s2, step3=s3,
               controls=dict(null=nc, positive=pc), seconds=round(time.time() - t0))
    (HERE / "checks.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"done in {time.time() - t0:.0f}s -> checks.json", flush=True)


if __name__ == "__main__":
    main()
