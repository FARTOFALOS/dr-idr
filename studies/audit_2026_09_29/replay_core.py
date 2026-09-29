"""Shared core of the screen replay: lab/scene21.py's similar-session rules, vectorised over lab/.runtime/boxes_*.

prep(d)     per observation minute (15-minute grid after the box): each session's position, extremes after the minute
            (in the coordinates of the three modes), their times, and whether its DR held after the minute
cohort(...) the similar sessions of scene21.cohort for a session at a minute (same side / confirmation window / DR
            state, or before a confirmation the box colour and the day's models), then the price band ±0.25 / ±0.5 IDR
            when it keeps >= 40 sessions. replay_equivalence.py checks it against the production code path.
Read-only; nothing here writes.
"""
from __future__ import annotations

import numpy as np

TEST_YEARS = range(2016, 2026)


def prep(d):
    start, formed, end, S = d["start"], d["formed"], d["end"], d["S"]
    grid = list(range(formed + 15, end - 14, 15))
    n = len(d["side"])
    w = d["idrh"] - d["idrl"]
    side = d["side"]
    e_conf = np.where(side == 1, d["idrh"], d["idrl"])
    e_brk = np.where(side == 1, d["idrl"], d["idrh"])
    P = {}
    H, L, C = d["H"], d["L"], d["C"]
    close_min = start + 5 * (np.arange(S) + 1)
    for t in grid:
        s = (t - start) // 5 - 1
        ct = np.where(np.isnan(C[:, s]), C[:, s - 1], C[:, s])
        fut_ok = ~np.isnan(C[:, s + 1:]).all(1)
        avail = ~np.isnan(ct) & fut_ok
        Hf = np.where(np.isnan(H[:, s + 1:]), -np.inf, H[:, s + 1:]); Lf = np.where(np.isnan(L[:, s + 1:]), np.inf, L[:, s + 1:])
        Cf = C[:, s + 1:]
        ih = Hf.argmax(1); il = Lf.argmin(1)
        maxH = Hf.max(1); minL = Lf.min(1)
        th = close_min[s + 1 + ih]; tl = close_min[s + 1 + il]
        out = {}
        for mode, e, dd in (("conf", e_conf, side), ("brk", e_brk, -side), ("wait", d["idrl"], np.ones(n, int))):
            pos = dd * (ct - e) / w
            mx = np.where(dd == 1, (maxH - e) / w, (e - minL) / w)
            mn = np.where(dd == 1, (minL - e) / w, (e - maxH) / w)
            tmx = np.where(dd == 1, th, tl); tmn = np.where(dd == 1, tl, th)
            out[mode] = dict(pos=pos, mx=mx, mn=mn, tmx=tmx, tmn=tmn)
        opp = np.where(side == 1, d["drl"], d["drh"])
        with np.errstate(invalid="ignore"):
            broke_later = np.where(side == 1, (Cf < opp[:, None]).any(1), (Cf > opp[:, None]).any(1))
        P[t] = dict(avail=avail, held=~broke_later, **out)
    conf_by = lambda t: (d["conf"] >= 0) & (d["conf"] <= t)
    fail_by = lambda t: (d["fail"] >= 0) & (d["fail"] <= t)
    return grid, P, conf_by, fail_by


def cohort(d, P, t, i, mode, conf_by, fail_by, years_ok, mod=None, include_self=False):
    """Similar sessions of session i at minute t; mod = the day-model codes at t (models_vec.model_at) or None."""
    base = d["complete"] & years_ok & P[t]["avail"]
    if not include_self: base[i] = False
    if mode in ("conf", "brk"):
        m = base & (d["side"] == d["side"][i]) & conf_by(t) & (np.abs(d["conf"] - d["conf"][i]) <= 15)
        m &= fail_by(t) if mode == "brk" else ~fail_by(t)
    else:
        m = base & ~conf_by(t) & (d["box"] == d["box"][i])
    pool = np.flatnonzero(m)
    if mode == "wait" and mod is not None:
        sel_m = pool[mod[pool] == mod[i]] if mod[i] >= 0 else pool[:0]
        if len(sel_m) >= 40: pool = sel_m
    pos = P[t][mode]["pos"]; u0 = pos[i]
    band, sel = None, pool
    for bw in (0.25, 0.5):
        c = pool[np.abs(pos[pool] - u0) <= bw]
        if len(c) >= 40: band, sel = bw, c; break
    return pool, sel, band, u0


def pull_class(mn, tmn, near_until):
    """0 = extreme in the first minutes, 1 = from the confirmation-side edge (>= -0.25), 2 = centre, 3 = beyond -0.75."""
    return np.where(tmn <= near_until, 0, np.where(mn >= -0.25, 1, np.where(mn >= -0.75, 2, 3)))
