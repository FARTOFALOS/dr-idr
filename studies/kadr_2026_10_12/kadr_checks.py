"""KADR-1.0 checks (12.10.2026): two discriminating measurements on the already-seen history 2006-2025, declared in
this docstring before the first count. Curator: Claude (Opus 5.5). Aggregates only: no dates, no prices.

    python -B studies/kadr_2026_10_12/kadr_checks.py        (the operator's Python with numpy)

A. «Где ждать откат от сейчас»: the accepted ladder against the position-matched frame.
   Question (operator 08.10: the decision DR Lab changes most often is «где ждать откат»): at a closed M5 cut t after
   today's confirmation (DR intact, complete prefix), for each of the operator's three pullback places
   L in {0, -1/2, -7/10} (IDR edge, mid, start of retirement) that lies below today's last close and that today has NOT
   yet reached (today's post-activation low > L): does today's price reach L (directed low <= L) on an M5 after t, until
   the block end?
   Targets: every confirmation-family session of NQ/ES/YM x ODR/RDR replayed as today, with the families of
   lab/scene24 (same instrument, session, weekday, side, 15-minute window, strictly earlier dates) when the weekday
   family has >= 40 sessions; cuts every 15 minutes of the common clock (grid index c with (c+1) % 3 == 0) after the
   activation, while today is eligible.
   Estimators (share of 'yes' among members with a known outcome):
     LADDER  - all N members, reach after t (what screen 24 shows as EST:B-LEVEL-REST; sign rule u <= 0 -> low <= L);
     CLOCK   - members eligible at t (NOW-1.0 B0: own activation before t, complete prefix, DR intact);
     NODE    - CLOCK and the member has not yet reached L after its own activation (KADR §9.2 «ЕЩЁ НЕ ПРИШЛИ»);
     POS     - CLOCK and |c_m(t) - c_today(t)| <= 1/4 IDR (KADR ПОЛОЖЕНИЕ(1/4));
     NODEPOS - NODE and POS (KADR's recommended default).
   Each for the weekday family (the screen's default) and the all-weekdays family (О25), strictly earlier dates both.
   Scores: support coverage (share of rows with n >= 20); Brier on the rows where both compared estimators have
   n >= 20, the difference's 95 % interval by resampling whole ISO weeks (pooled over instruments and sessions); BSS
   against the constant equal to those rows' own base rate (favourable to the constant); reliability in 10 bins.
   Declared primary comparisons: NODEPOS_wd vs LADDER_wd; CLOCK_wd vs LADDER_wd; NODEPOS_all vs NODEPOS_wd.
   Declared reading: a difference counts only if its interval excludes zero. Exploration on seen history: it informs
   the operator's choices (KADR §17 frame default, О25); it admits no number to the product.

B. Path memory (KADR Г1, lens 5 test 1) on the operator's two stories «середина -> +0,5» and «+0,5 -> середина».
   Population: every confirmation-family session of NQ/ES/YM x ODR/RDR 2006-2025 (no family: a property of paths).
   At cuts every 15 minutes with a complete prefix and DR intact, where both mid (-1/2) and +1/2 have been reached
   after the activation, in different M5 (the same M5 = unknown order, excluded), and +1 not yet reached:
   group A = mid reached first, group B = +1/2 reached first.
   Moment strata: universe (instrument x session) x 30-minute clock bucket x last close bucket (1/4) x made pullback
   bucket (1/4, capped at -5/4) x made extension bucket (1/4).
   Outcomes after t: reach +1; a new pullback extreme (low strictly below the made low); DR break (a close strictly
   beyond the own opposite DR).
   Statistic: the stratum-adjusted difference A - B (weights nA nB / (nA + nB), strata holding both groups), its 95 %
   interval by resampling ISO weeks; the raw difference alongside.
   Declared reading: the order of lived events carries information beyond the moment if the adjusted interval excludes
   zero AND |difference| >= 3 pp; otherwise the moment hypothesis survives for this feature (interval width reported).

Added after the first reading of A and B (same day, marked as such; nothing above was changed):
B2. Robustness of B to the width of the strata: the same records with close / pullback / extension buckets of 1/10 and
   15-minute clock buckets. Question: is B's only residual (reach +1, -4.4 pp) left over from coarse strata?
C. Support only (no outcome is read): the frame of the place question «после прихода: что раньше». Place L = -1/2,
   target U = +1, stop D = -7/10. At the cuts of A where today is in the node «пришли, ни цели, ни стопа после касания»,
   how many family members (weekday / all weekdays) are in the same node at the same clock, and with |close| within
   1/4. Without the M5 open in the base path a touch M5 that also reached U and closed below U is «unknown» (conservative).

Added after the curator lens of 12.10 evening (declared here before the count; A, B, B2, C unchanged):
D. Geometry against the family key for Q:K-ARRIVE (the rows of A). GEO = every confirmation session of the same
   instrument x session, any side, any 15-minute window, any weekday, strictly earlier dates, eligible at t (own
   activation before t, complete, DR intact), not yet at L after its activation, close within 1/4 IDR of today's
   (directed scale, own IDR width as the scale known at the cut). Compared with NODEPOS_all on the rows where both have
   n >= 20. Reading: if GEO is not worse (interval of the Brier difference includes 0 or favours GEO), the side and the
   activation window add nothing beyond clock + position in the IDR ruler; if NODEPOS_all is better, they do.
E. Quality of «после прихода: что раньше» read from the common clock. Rows: the targets of A at the 15-minute cuts
   where today is in the node «пришли к -1/2, после касания ни +1, ни -7/10» (the rows of C). Outcome after t: which
   of U = +1 / D = -7/10 is reached first until the block end (both in one M5 or a missing M5 before the first event =
   unknown, excluded; neither = NONE). Scored as two binary events (U first; D first). Estimators (share among known):
     FRAME_ALL     - all-weekdays parent, eligible at t, in the same node at t, outcome after t;
     FRAME_ALL_POS - and close within 1/4;
     TOUCH_WD      - the map family (weekday): among members that ever arrived, the outcome after their OWN touch
                     (§6.4 without open), whole session, no clock alignment — the «история касаний» object;
     TOUCH_ALL     - the same on the all-weekdays parent;
     CLOCK_ALL     - all-weekdays parent eligible at t, any node, outcome after t.
   Declared comparisons: FRAME_ALL vs TOUCH_WD; FRAME_ALL_POS vs FRAME_ALL; FRAME_ALL vs CLOCK_ALL. A difference counts
   only if its interval excludes zero; BSS against the rows' own base rate; reliability bins with >= 50 rows.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "lab"))
import now24 as N  # noqa: E402
import now24_validate as V  # noqa: E402

OUT = Path(__file__).resolve().parent
INSTS = ("NQ", "ES", "YM")
SESSIONS = ("ODR", "RDR")
LEVELS = (("0", 0, 1), ("-1/2", -1, 2), ("-7/10", -7, 10))
EST = ("LADDER", "CLOCK", "NODE", "POS", "NODEPOS")
FAMS = ("wd", "all")
MIN_FAM, SUP, STEP, REPS = 40, 20, 3, 2000
COLS = [f"{e}_{f}" for f in FAMS for e in EST]


def iso_week(date):
    y, w, _ = dt.date.fromisoformat(date).isocalendar()
    return y * 100 + w


def future_low(P):
    """For every grid index c: the minimum directed low over the M5 after c (inf if none) and whether one is missing."""
    lo = P[:, 0]
    nan = np.isnan(lo)
    lo_i = np.where(nan, np.inf, lo)
    fmin = np.append(np.minimum.accumulate(lo_i[::-1])[::-1][1:], np.inf)
    fnan = np.append(np.logical_or.accumulate(nan[::-1])[::-1][1:], False)
    return fmin, fnan


def future_high(P):
    hi = P[:, 1]
    nan = np.isnan(hi)
    hi_i = np.where(nan, -np.inf, hi)
    fmax = np.append(np.maximum.accumulate(hi_i[::-1])[::-1][1:], -np.inf)
    fnan = np.append(np.logical_or.accumulate(nan[::-1])[::-1][1:], False)
    return fmax, fnan


def future_break(P, oppv):
    """1 if some M5 after c closes strictly beyond the opposite DR, 0 if fully observed without it, -1 unknown."""
    cl = P[:, 2]
    nan = np.isnan(cl)
    brk = (~nan) & (np.where(nan, 0, cl) < oppv)
    fb = np.append(np.logical_or.accumulate(brk[::-1])[::-1][1:], False)
    fnan = np.append(np.logical_or.accumulate(nan[::-1])[::-1][1:], False)
    return np.where(fb, 1, np.where(fnan, -1, 0)).astype(np.int8)


def boot_mean(diff, week, reps=REPS, seed=0):
    uw, inv = np.unique(week, return_inverse=True)
    s = np.bincount(inv, weights=diff)
    n = np.bincount(inv).astype(float)
    rng = np.random.default_rng(seed)
    out = np.empty(reps)
    for b0 in range(0, reps, 200):
        k = rng.integers(0, len(uw), size=(min(200, reps - b0), len(uw)))
        out[b0:b0 + len(k)] = s[k].sum(1) / n[k].sum(1)
    return float(diff.mean()), float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


# ------------------------------------------------------------------ A
def study_a():
    rows = {k: [] for k in ("uid", "week", "lvl", "y", "elapsed")}
    for c in COLS: rows["n_" + c], rows["p_" + c] = [], []
    universes = []
    for inst in INSTS:
        for session in SESSIONS:
            uid = len(universes)
            U, grid = V.universe(inst, session, "conf")
            Lg = len(grid)
            ser = [N.series(u["P"], u["a"], u["oppv"]) for u in U]
            fl = [future_low(u["P"]) for u in U]
            groups = {}
            for j, u in enumerate(U): groups.setdefault((u["side"], u["win"]), []).append(j)
            n_targets = 0
            for gk, idxs in groups.items():
                idxs.sort(key=lambda j: U[j]["date"])
                dates = [U[j]["date"] for j in idxs]
                dates_np = np.array(dates)
                wdays = np.array([U[j]["weekday"] for j in idxs])
                Sg = N.stack([ser[j] for j in idxs])
                wg = np.array([U[j]["w"] for j in idxs], dtype=np.int64)
                FMIN = np.stack([fl[j][0] for j in idxs])
                FNAN = np.stack([fl[j][1] for j in idxs])
                for t, i in enumerate(idxs):
                    nb = int(np.searchsorted(dates_np, dates[t], side="left"))   # strictly earlier dates
                    fam_all = np.arange(nb)
                    fam_wd = fam_all[wdays[:nb] == U[i]["weekday"]]
                    if len(fam_wd) < MIN_FAM: continue
                    T, w_t, a_t = ser[i], U[i]["w"], U[i]["a"]
                    cuts = np.array([c for c in range(a_t + 1, Lg - 1) if T["valid"][c] and (c + 1) % STEP == 0], dtype=int)
                    if not len(cuts): continue
                    fmin_t, fnan_t = fl[i]
                    n_targets += 1
                    for li, (_, a, b) in enumerate(LEVELS):
                        cl_t, r_t = T["cl"][cuts], T["r"][cuts]
                        ok = (cl_t * b > a * w_t) & (r_t * b > a * w_t)
                        yes_t = fmin_t[cuts] * b <= a * w_t
                        y = np.where(yes_t, 1, np.where(fnan_t[cuts], -1, 0))
                        ok &= y >= 0
                        if not ok.any(): continue
                        cs = cuts[ok]
                        rows["uid"].append(np.full(len(cs), uid, np.int8))
                        rows["week"].append(np.full(len(cs), iso_week(U[i]["date"]), np.int32))
                        rows["lvl"].append(np.full(len(cs), li, np.int8))
                        rows["y"].append(y[ok].astype(np.int8))
                        rows["elapsed"].append((cs - a_t).astype(np.int16))
                        for fname, fam in (("wd", fam_wd), ("all", fam_all)):
                            w = wg[fam][:, None]
                            reach = FMIN[fam][:, cs] * b <= a * w
                            unk = (~reach) & FNAN[fam][:, cs]
                            Vm = Sg["valid"][fam][:, cs]
                            node = Vm & (Sg["r"][fam][:, cs] * b > a * w)
                            pos = Vm & N._near(Sg["cl"][fam][:, cs], w, T["cl"][cs][None, :], w_t, (1, 4))
                            masks = {"LADDER": np.ones_like(Vm), "CLOCK": Vm, "NODE": node, "POS": pos, "NODEPOS": node & pos}
                            for e, M in masks.items():
                                n = M.sum(0)
                                yes = (M & reach).sum(0)
                                kn = n - (M & unk).sum(0)
                                with np.errstate(invalid="ignore", divide="ignore"):
                                    p = np.where(kn > 0, yes / np.maximum(kn, 1), np.nan)
                                rows[f"n_{e}_{fname}"].append(n.astype(np.int32))
                                rows[f"p_{e}_{fname}"].append(p.astype(np.float32))
            universes.append(dict(inst=inst, session=session, sessions=len(U), targets=n_targets))
            print(f"A {inst} {session}: {len(U)} sessions, {n_targets} targets", flush=True)
    R = {k: np.concatenate(v) for k, v in rows.items()}
    return R, universes


def brier_pair(R, sel, ref, est, seed):
    y = R["y"].astype(float)
    ok = sel & (R["n_" + ref] >= SUP) & (R["n_" + est] >= SUP) & np.isfinite(R["p_" + ref]) & np.isfinite(R["p_" + est])
    if ok.sum() < 100: return dict(rows=int(ok.sum()))
    a = (R["p_" + ref][ok] - y[ok]) ** 2
    b = (R["p_" + est][ok] - y[ok]) ** 2
    base = y[ok].mean()
    c0 = ((base - y[ok]) ** 2).mean()
    m, lo, hi = boot_mean(a - b, R["week"][ok], seed=seed)
    return dict(rows=int(ok.sum()), weeks=int(len(np.unique(R["week"][ok]))), base_rate=round(float(base), 4),
                brier_ref=round(float(a.mean()), 5), brier_est=round(float(b.mean()), 5),
                bss_ref_vs_const=round(1 - float(a.mean()) / c0, 4), bss_est_vs_const=round(1 - float(b.mean()) / c0, 4),
                skill_est_vs_ref=round(1 - float(b.mean()) / float(a.mean()), 4),
                diff=round(m, 6), lo=round(lo, 6), hi=round(hi, 6), counts=bool(lo > 0 or hi < 0))


def reliability(R, sel, est):
    ok = sel & (R["n_" + est] >= SUP) & np.isfinite(R["p_" + est])
    p, y = R["p_" + est][ok], R["y"][ok]
    out = []
    for k in range(10):
        m = (p >= k / 10) & (p < (k + 1) / 10 if k < 9 else p <= 1)
        if m.sum() >= 50: out.append([f"{k / 10:.1f}-{(k + 1) / 10:.1f}", int(m.sum()), round(float(p[m].mean()), 3), round(float(y[m].mean()), 3)])
    return out


def analyse_a(R, universes):
    res = dict(universes=universes, rows=int(len(R["y"])), coverage={}, primary={}, secondary={}, by_level={}, by_session={},
               reliability={})
    allrows = np.ones(len(R["y"]), bool)
    for c in COLS:
        res["coverage"][c] = dict(share_n_ge_20=round(float((R["n_" + c] >= SUP).mean()), 4),
                                  median_n=float(np.median(R["n_" + c])))
    res["primary"]["NODEPOS_wd vs LADDER_wd"] = brier_pair(R, allrows, "LADDER_wd", "NODEPOS_wd", 1)
    res["primary"]["CLOCK_wd vs LADDER_wd"] = brier_pair(R, allrows, "LADDER_wd", "CLOCK_wd", 2)
    res["primary"]["NODEPOS_all vs NODEPOS_wd"] = brier_pair(R, allrows, "NODEPOS_wd", "NODEPOS_all", 3)
    res["secondary"]["NODEPOS_all vs LADDER_wd"] = brier_pair(R, allrows, "LADDER_wd", "NODEPOS_all", 4)
    res["secondary"]["POS_wd vs CLOCK_wd"] = brier_pair(R, allrows, "CLOCK_wd", "POS_wd", 5)
    res["secondary"]["NODE_wd vs CLOCK_wd"] = brier_pair(R, allrows, "CLOCK_wd", "NODE_wd", 6)
    res["secondary"]["NODEPOS_wd vs POS_wd"] = brier_pair(R, allrows, "POS_wd", "NODEPOS_wd", 7)
    res["secondary"]["CLOCK_all vs CLOCK_wd"] = brier_pair(R, allrows, "CLOCK_wd", "CLOCK_all", 8)
    for li, (name, _, _) in enumerate(LEVELS):
        s = R["lvl"] == li
        res["by_level"][name] = dict(rows=int(s.sum()),
                                     cov_NODEPOS_wd=round(float((R["n_NODEPOS_wd"][s] >= SUP).mean()), 4),
                                     cov_NODEPOS_all=round(float((R["n_NODEPOS_all"][s] >= SUP).mean()), 4),
                                     NODEPOS_wd_vs_LADDER_wd=brier_pair(R, s, "LADDER_wd", "NODEPOS_wd", 10 + li),
                                     NODEPOS_all_vs_LADDER_wd=brier_pair(R, s, "LADDER_wd", "NODEPOS_all", 20 + li))
    for sess in SESSIONS:
        s = np.isin(R["uid"], [k for k, u in enumerate(universes) if u["session"] == sess])
        res["by_session"][sess] = dict(rows=int(s.sum()),
                                       NODEPOS_wd_vs_LADDER_wd=brier_pair(R, s, "LADDER_wd", "NODEPOS_wd", 30),
                                       NODEPOS_all_vs_LADDER_wd=brier_pair(R, s, "LADDER_wd", "NODEPOS_all", 31))
    for e in ("LADDER_wd", "CLOCK_wd", "NODEPOS_wd", "NODEPOS_all"):
        res["reliability"][e] = reliability(R, allrows, e)
    return res


# ------------------------------------------------------------------ B
def study_b(q=4, clock_div=6):
    rec = {k: [] for k in ("uid", "week", "grp", "stratum", "y_p1", "y_newR", "y_brk")}
    universes = []
    for inst in INSTS:
        for session in SESSIONS:
            uid = len(universes)
            U, grid = V.universe(inst, session, "conf")
            Lg = len(grid)
            idx = np.arange(Lg)
            n_rec = 0
            for u in U:
                P, a, w, oppv = u["P"], u["a"], u["w"], u["oppv"]
                s = N.series(P, a, oppv)
                lo, hi = P[:, 0], P[:, 1]
                post = idx > a
                mid = post & ~np.isnan(lo) & (np.where(np.isnan(lo), 0, lo) * 2 <= -w)
                p5 = post & ~np.isnan(hi) & (np.where(np.isnan(hi), 0, hi) * 2 >= w)
                if not mid.any() or not p5.any(): continue
                fm, fp = int(np.argmax(mid)), int(np.argmax(p5))
                if fm == fp: continue
                grp = 0 if fm < fp else 1
                fmax, fnan_h = future_high(P)
                fmin, fnan_l = future_low(P)
                brk = future_break(P, oppv)
                cs = [c for c in range(max(fm, fp), Lg - 1)
                      if s["valid"][c] and (c + 1) % STEP == 0 and s["x"][c] < w]
                if not cs: continue
                cs = np.array(cs, dtype=int)
                r, x, cl = s["r"][cs], s["x"][cs], s["cl"][cs]
                yp1 = np.where(fmax[cs] >= w, 1, np.where(fnan_h[cs], -1, 0))
                ynr = np.where(fmin[cs] < r, 1, np.where(fnan_l[cs], -1, 0))
                rb = np.maximum(np.floor_divide(q * r, w), -(5 * q) // 4)
                strat = [(uid, int(c // clock_div), int(np.floor_divide(q * cv, w)), int(rv), int(np.floor_divide(q * xv, w)))
                         for c, cv, rv, xv in zip(cs, cl, rb, x)]
                rec["uid"].append(np.full(len(cs), uid, np.int8))
                rec["week"].append(np.full(len(cs), iso_week(u["date"]), np.int32))
                rec["grp"].append(np.full(len(cs), grp, np.int8))
                rec["stratum"].extend(strat)
                rec["y_p1"].append(yp1.astype(np.int8)); rec["y_newR"].append(ynr.astype(np.int8)); rec["y_brk"].append(brk[cs])
                n_rec += len(cs)
            universes.append(dict(inst=inst, session=session, records=n_rec))
            print(f"B(q={q}) {inst} {session}: {n_rec} records", flush=True)
    keys = {k: i for i, k in enumerate(sorted(set(rec["stratum"])))}
    R = {k: np.concatenate(v) for k, v in rec.items() if k != "stratum"}
    R["sid"] = np.array([keys[k] for k in rec["stratum"]], dtype=np.int32)
    return R, universes


def adjusted(y, grp, sid, wt):
    """Stratum-adjusted A - B with record weights wt (bootstrap multiplicities)."""
    K = int(sid.max()) + 1
    nA = np.bincount(sid, weights=wt * (grp == 0), minlength=K)
    nB = np.bincount(sid, weights=wt * (grp == 1), minlength=K)
    sA = np.bincount(sid, weights=wt * (grp == 0) * y, minlength=K)
    sB = np.bincount(sid, weights=wt * (grp == 1) * y, minlength=K)
    both = (nA > 0) & (nB > 0)
    if not both.any(): return np.nan
    wk = nA[both] * nB[both] / (nA[both] + nB[both])
    d = sA[both] / nA[both] - sB[both] / nB[both]
    return float((wk * d).sum() / wk.sum())


def analyse_b(R, universes):
    res = dict(universes=universes, outcomes={})
    for name in ("y_p1", "y_newR", "y_brk"):
        ok = R[name] >= 0
        y, g, sid, wk = R[name][ok].astype(float), R["grp"][ok], R["sid"][ok], R["week"][ok]
        raw = float(y[g == 0].mean() - y[g == 1].mean())
        adj = adjusted(y, g, sid, np.ones(len(y)))
        uw, inv = np.unique(wk, return_inverse=True)
        rng = np.random.default_rng(7)
        bs = np.empty(REPS)
        for b in range(REPS):
            m = np.bincount(rng.integers(0, len(uw), len(uw)), minlength=len(uw)).astype(float)
            bs[b] = adjusted(y, g, sid, m[inv])
        lo, hi = float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))
        K = int(sid.max()) + 1
        nA = np.bincount(sid, weights=(g == 0).astype(float), minlength=K)
        nB = np.bincount(sid, weights=(g == 1).astype(float), minlength=K)
        both = (nA > 0) & (nB > 0)
        inboth = both[sid]
        res["outcomes"][name] = dict(records=int(len(y)), A=int((g == 0).sum()), B=int((g == 1).sum()),
                                     rate_A=round(float(y[g == 0].mean()), 4), rate_B=round(float(y[g == 1].mean()), 4),
                                     raw_diff=round(raw, 4), adjusted_diff=round(adj, 4), lo=round(lo, 4), hi=round(hi, 4),
                                     records_in_shared_strata=int(inboth.sum()), shared_strata=int(both.sum()),
                                     memory=bool((lo > 0 or hi < 0) and abs(adj) >= 0.03))
    return res


# ------------------------------------------------------------------ C (support only)
NOT_YET, U_BEFORE, ARRIVED, TARGET_FIRST, STOP_FIRST, UNKNOWN = range(6)


def node_series(P, a, w, L=(-1, 2), U=(1, 1), D=(-7, 10)):
    """The node of the place question (approach from above) on the prefix (a, c] for every grid index c; -1 where the
    prefix has a missing M5. The activating close is beyond DR, so the approach to L <= 0 is armed at the activation."""
    (la, lb), (ua, ub), (da, db) = L, U, D
    out = np.full(len(P), -1, np.int8)
    node = NOT_YET
    for k in range(a + 1, len(P)):
        lo, hi, cl = P[k]
        if np.isnan(lo): break
        tL, tU, tD = lo * lb <= la * w, hi * ub >= ua * w, lo * db <= da * w
        if node == NOT_YET:
            if tL and tU: node = UNKNOWN                      # touch and target in one M5: their order is unknown
            elif tU: node = U_BEFORE
            elif tL:
                node = STOP_FIRST if tD else ARRIVED            # the stop below the place cannot precede the touch
        elif node == ARRIVED:
            if tU and tD: node = UNKNOWN
            elif tU: node = TARGET_FIRST
            elif tD: node = STOP_FIRST
        out[k] = node
    return out


def study_c():
    res = {}
    cov = {k: [] for k in ("n_wd", "n_wd_pos", "n_all", "n_all_pos")}
    for inst in INSTS:
        for session in SESSIONS:
            U, grid = V.universe(inst, session, "conf")
            Lg = len(grid)
            ser = [N.series(u["P"], u["a"], u["oppv"]) for u in U]
            nodes = [node_series(u["P"], u["a"], u["w"]) for u in U]
            groups = {}
            for j, u in enumerate(U): groups.setdefault((u["side"], u["win"]), []).append(j)
            for gk, idxs in groups.items():
                idxs.sort(key=lambda j: U[j]["date"])
                dates_np = np.array([U[j]["date"] for j in idxs])
                wdays = np.array([U[j]["weekday"] for j in idxs])
                Sg = N.stack([ser[j] for j in idxs])
                NDg = np.stack([nodes[j] for j in idxs])
                wg = np.array([U[j]["w"] for j in idxs], dtype=np.int64)
                for t, i in enumerate(idxs):
                    nb = int(np.searchsorted(dates_np, dates_np[t], side="left"))
                    fam_all = np.arange(nb)
                    fam_wd = fam_all[wdays[:nb] == U[i]["weekday"]]
                    if len(fam_wd) < MIN_FAM: continue
                    T, w_t, a_t = ser[i], U[i]["w"], U[i]["a"]
                    cs = np.array([c for c in range(a_t + 1, Lg - 1) if T["valid"][c] and (c + 1) % STEP == 0
                                   and nodes[i][c] == ARRIVED], dtype=int)
                    if not len(cs): continue
                    for fname, fam in (("wd", fam_wd), ("all", fam_all)):
                        Vm = Sg["valid"][fam][:, cs] & (NDg[fam][:, cs] == ARRIVED)
                        pos = Vm & N._near(Sg["cl"][fam][:, cs], wg[fam][:, None], T["cl"][cs][None, :], w_t, (1, 4))
                        cov[f"n_{fname}"].append(Vm.sum(0)); cov[f"n_{fname}_pos"].append(pos.sum(0))
            print(f"C {inst} {session} done", flush=True)
    for k, v in cov.items():
        a = np.concatenate(v)
        res[k] = dict(rows=int(len(a)), share_n_ge_20=round(float((a >= SUP).mean()), 4), median_n=float(np.median(a)))
    return res


# ------------------------------------------------------------------ D and E (after the curator lens)
def next_index(mask):
    """For every c: the smallest j > c with mask[j], len(mask) if none."""
    L = len(mask)
    out = np.full(L, L, dtype=np.int32)
    nxt = L
    for j in range(L - 1, -1, -1):
        out[j] = nxt
        if mask[j]: nxt = j
    return out


def after_outcome(P, w, U=(1, 1), D=(-7, 10)):
    """For every cut c: the first of U / D over the M5 after c: 1 = U, 2 = D, 0 = neither to the block end,
    -1 = unknown (both in one M5, or a missing M5 before the first event / before the end)."""
    (ua, ub), (da, db) = U, D
    lo, hi = P[:, 0], P[:, 1]
    nan = np.isnan(lo)
    hU = ~nan & (np.where(nan, 0, hi) * ub >= ua * w)
    hD = ~nan & (np.where(nan, 0, lo) * db <= da * w)
    fu, fd, fn = next_index(hU), next_index(hD), next_index(nan)
    L = len(P)
    e = np.minimum(fu, fd)
    out = np.where(fn < e, -1, np.where(e == L, 0, np.where(fu == fd, -1, np.where(fu < fd, 1, 2))))
    return out.astype(np.int8)


def touch_outcome(P, a, w, L=(-1, 2), U=(1, 1), D=(-7, 10)):
    """The history of touches (own anchor «от касания», §6.4 without the open): 'U', 'D', 'NONE', 'unknown',
    'not_arrived' (no touch to the end, or U before the touch)."""
    (la, lb), (ua, ub), (da, db) = L, U, D
    state = NOT_YET
    for k in range(a + 1, len(P)):
        lo, hi, cl = P[k]
        if np.isnan(lo): return "unknown"
        tL, tU, tD = lo * lb <= la * w, hi * ub >= ua * w, lo * db <= da * w
        if state == NOT_YET:
            if tL:
                if tD and not tU: return "D"
                if tD and tU: return "unknown"
                if tU: return "U" if cl * ub >= ua * w else "unknown"
                state = ARRIVED
            elif tU: return "not_arrived"
        else:
            if tU and tD: return "unknown"
            if tU: return "U"
            if tD: return "D"
    return "NONE" if state == ARRIVED else "not_arrived"


def pair_scores(rows, y_key, ref, est, seed):
    y = rows[y_key].astype(float)
    pr, pe = rows["p_" + ref + "_" + y_key], rows["p_" + est + "_" + y_key]
    ok = (rows["n_" + ref] >= SUP) & (rows["n_" + est] >= SUP) & np.isfinite(pr) & np.isfinite(pe)
    if ok.sum() < 100: return dict(rows=int(ok.sum()))
    a, b = (pr[ok] - y[ok]) ** 2, (pe[ok] - y[ok]) ** 2
    base = y[ok].mean()
    c0 = ((base - y[ok]) ** 2).mean()
    m, lo, hi = boot_mean(a - b, rows["week"][ok], seed=seed)
    return dict(rows=int(ok.sum()), base_rate=round(float(base), 4), bss_ref_vs_const=round(1 - float(a.mean()) / c0, 4),
                bss_est_vs_const=round(1 - float(b.mean()) / c0, 4), skill_est_vs_ref=round(1 - float(b.mean()) / float(a.mean()), 4),
                diff=round(m, 6), lo=round(lo, 6), hi=round(hi, 6), counts=bool(lo > 0 or hi < 0))


def study_de():
    D = {k: [] for k in ("week", "y", "n_GEO", "p_GEO_y", "n_NODEPOS_all", "p_NODEPOS_all_y")}
    EST_E = ("FRAME_ALL", "FRAME_ALL_POS", "FRAME_WD", "TOUCH_WD", "TOUCH_ALL", "CLOCK_ALL")
    E = {k: [] for k in ("week", "yU", "yD")}
    for e in EST_E: E["n_" + e], E[f"p_{e}_yU"], E[f"p_{e}_yD"] = [], [], []
    for inst in INSTS:
        for session in SESSIONS:
            U, grid = V.universe(inst, session, "conf")
            Lg = len(grid)
            ser = [N.series(u["P"], u["a"], u["oppv"]) for u in U]
            fl = [future_low(u["P"]) for u in U]
            nodes = [node_series(u["P"], u["a"], u["w"]) for u in U]
            aft = [after_outcome(u["P"], u["w"]) for u in U]
            tch = np.array([{"U": 1, "D": 2, "NONE": 0, "unknown": -1, "not_arrived": -2}[touch_outcome(u["P"], u["a"], u["w"])] for u in U])
            order = sorted(range(len(U)), key=lambda j: U[j]["date"])
            dates_o = np.array([U[j]["date"] for j in order])
            S_o = N.stack([ser[j] for j in order])
            w_o = np.array([U[j]["w"] for j in order], dtype=np.int64)
            FMIN_o = np.stack([fl[j][0] for j in order])
            FNAN_o = np.stack([fl[j][1] for j in order])
            groups = {}
            for j in range(len(U)): groups.setdefault((U[j]["side"], U[j]["win"]), []).append(j)
            for gk, idxs in groups.items():
                idxs.sort(key=lambda j: U[j]["date"])
                dates_g = np.array([U[j]["date"] for j in idxs])
                wdays = np.array([U[j]["weekday"] for j in idxs])
                Sg = N.stack([ser[j] for j in idxs])
                wg = np.array([U[j]["w"] for j in idxs], dtype=np.int64)
                FMIN = np.stack([fl[j][0] for j in idxs]); FNAN = np.stack([fl[j][1] for j in idxs])
                NDg = np.stack([nodes[j] for j in idxs]); AFg = np.stack([aft[j] for j in idxs]); TCg = tch[idxs]
                for t, i in enumerate(idxs):
                    nb = int(np.searchsorted(dates_g, dates_g[t], side="left"))
                    fam_all = np.arange(nb)
                    fam_wd = fam_all[wdays[:nb] == U[i]["weekday"]]
                    if len(fam_wd) < MIN_FAM: continue
                    T, w_t, a_t = ser[i], U[i]["w"], U[i]["a"]
                    cuts = np.array([c for c in range(a_t + 1, Lg - 1) if T["valid"][c] and (c + 1) % STEP == 0], dtype=int)
                    if not len(cuts): continue
                    week = iso_week(U[i]["date"])
                    nbo = int(np.searchsorted(dates_o, dates_g[t], side="left"))
                    # D: the rows of A
                    fmin_t, fnan_t = fl[i]
                    for _, a, b in LEVELS:
                        ok = (T["cl"][cuts] * b > a * w_t) & (T["r"][cuts] * b > a * w_t)
                        y = np.where(fmin_t[cuts] * b <= a * w_t, 1, np.where(fnan_t[cuts], -1, 0))
                        ok &= y >= 0
                        if not ok.any(): continue
                        cs = cuts[ok]
                        for name, S, w, FM, FN, idx in (("GEO", S_o, w_o, FMIN_o, FNAN_o, np.arange(nbo)),
                                                        ("NODEPOS_all", Sg, wg, FMIN, FNAN, fam_all)):
                            W = w[idx][:, None]
                            reach = FM[idx][:, cs] * b <= a * W
                            unk = (~reach) & FN[idx][:, cs]
                            M = S["valid"][idx][:, cs] & (S["r"][idx][:, cs] * b > a * W) & N._near(S["cl"][idx][:, cs], W, T["cl"][cs][None, :], w_t, (1, 4))
                            n = M.sum(0); yes = (M & reach).sum(0); kn = n - (M & unk).sum(0)
                            with np.errstate(invalid="ignore", divide="ignore"):
                                p = np.where(kn > 0, yes / np.maximum(kn, 1), np.nan)
                            D["n_" + name].append(n.astype(np.int32)); D[f"p_{name}_y"].append(p.astype(np.float32))
                        D["week"].append(np.full(len(cs), week, np.int32)); D["y"].append(y[ok].astype(np.int8))
                    # E: today in the node «пришли, не решено» at the cut
                    ce = cuts[nodes[i][cuts] == ARRIVED]
                    if not len(ce): continue
                    yo = aft[i][ce]
                    ce, yo = ce[yo >= 0], yo[yo >= 0]
                    if not len(ce): continue
                    E["week"].append(np.full(len(ce), week, np.int32))
                    E["yU"].append((yo == 1).astype(np.int8)); E["yD"].append((yo == 2).astype(np.int8))

                    def put(name, M, OUT):
                        n = M.sum(0)
                        kn = (M & (OUT >= 0)).sum(0)
                        with np.errstate(invalid="ignore", divide="ignore"):
                            pU = np.where(kn > 0, (M & (OUT == 1)).sum(0) / np.maximum(kn, 1), np.nan)
                            pD = np.where(kn > 0, (M & (OUT == 2)).sum(0) / np.maximum(kn, 1), np.nan)
                        E["n_" + name].append(n.astype(np.int32))
                        E[f"p_{name}_yU"].append(pU.astype(np.float32)); E[f"p_{name}_yD"].append(pD.astype(np.float32))

                    for name, fam in (("ALL", fam_all), ("WD", fam_wd)):
                        Vm = Sg["valid"][fam][:, ce]
                        node = Vm & (NDg[fam][:, ce] == ARRIVED)
                        OUT = AFg[fam][:, ce]
                        if name == "ALL":
                            put("FRAME_ALL", node, OUT)
                            put("FRAME_ALL_POS", node & N._near(Sg["cl"][fam][:, ce], wg[fam][:, None], T["cl"][ce][None, :], w_t, (1, 4)), OUT)
                            put("CLOCK_ALL", Vm, OUT)
                        else:
                            put("FRAME_WD", node, OUT)
                        # history of touches: own anchor, whole session, the same for every cut of this target
                        arrived = TCg[fam] >= -1
                        Mt = np.repeat(arrived[:, None], len(ce), 1)
                        put("TOUCH_" + name, Mt, np.repeat(TCg[fam][:, None], len(ce), 1))
            print(f"D/E {inst} {session} done", flush=True)
    RD = {k: np.concatenate(v) for k, v in D.items()}
    RE = {k: np.concatenate(v) for k, v in E.items()}
    out = dict(D=dict(rows=int(len(RD["y"])),
                      coverage={k: round(float((RD["n_" + k] >= SUP).mean()), 4) for k in ("GEO", "NODEPOS_all")},
                      median_n={k: float(np.median(RD["n_" + k])) for k in ("GEO", "NODEPOS_all")},
                      GEO_vs_NODEPOS_all=pair_scores(RD, "y", "NODEPOS_all", "GEO", 41)),
               E=dict(rows=int(len(RE["yU"])),
                      coverage={e: round(float((RE["n_" + e] >= SUP).mean()), 4) for e in EST_E},
                      median_n={e: float(np.median(RE["n_" + e])) for e in EST_E}))
    for ev in ("yU", "yD"):
        out["E"][ev] = {"FRAME_ALL vs TOUCH_WD": pair_scores(RE, ev, "TOUCH_WD", "FRAME_ALL", 51),
                        "FRAME_ALL_POS vs FRAME_ALL": pair_scores(RE, ev, "FRAME_ALL", "FRAME_ALL_POS", 52),
                        "FRAME_ALL vs CLOCK_ALL": pair_scores(RE, ev, "CLOCK_ALL", "FRAME_ALL", 53),
                        "TOUCH_ALL vs TOUCH_WD": pair_scores(RE, ev, "TOUCH_WD", "TOUCH_ALL", 54)}
    rel = {}
    for e in ("FRAME_ALL", "TOUCH_WD"):
        ok = (RE["n_" + e] >= SUP) & np.isfinite(RE[f"p_{e}_yU"])
        p, y = RE[f"p_{e}_yU"][ok], RE["yU"][ok]
        rel[e] = [[f"{k / 10:.1f}-{(k + 1) / 10:.1f}", int(m.sum()), round(float(p[m].mean()), 3), round(float(y[m].mean()), 3)]
                  for k in range(10) for m in [(p >= k / 10) & ((p < (k + 1) / 10) if k < 9 else (p <= 1))] if m.sum() >= 50]
    out["E"]["reliability_yU"] = rel
    return out


def main():
    t0 = time.time()
    if "--add2" in sys.argv:                      # D and E only, merged into the saved result
        out = json.loads((OUT / "kadr_checks.json").read_text(encoding="utf-8"))
        out.update(study_de())
        out["seconds_add2"] = round(time.time() - t0)
        (OUT / "kadr_checks.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps(dict(D=out["D"], E=out["E"]), ensure_ascii=False, indent=1))
        return
    if "--add" in sys.argv:                       # B2 and C only, merged into the saved result of A and B
        out = json.loads((OUT / "kadr_checks.json").read_text(encoding="utf-8"))
        RB2, UB2 = study_b(q=10, clock_div=3)
        out["B2"] = analyse_b(RB2, UB2)
        out["C"] = study_c()
        out["seconds_add"] = round(time.time() - t0)
        (OUT / "kadr_checks.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps(dict(B2=out["B2"]["outcomes"], C=out["C"]), ensure_ascii=False, indent=1))
        return
    RA, UA = study_a()
    A = analyse_a(RA, UA)
    print(f"A done {time.time() - t0:.0f}s", flush=True)
    RB, UB = study_b()
    B = analyse_b(RB, UB)
    print(f"B done {time.time() - t0:.0f}s", flush=True)
    out = dict(study="KADR-1.0 checks", date="2026-10-12", history="2006-2025 (2026 closed)", A=A, B=B,
               seconds=round(time.time() - t0))
    (OUT / "kadr_checks.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
