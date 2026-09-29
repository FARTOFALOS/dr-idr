"""Day-model state as lab/scene21.py computes it for history (_models_hist), vectorised per session type.

For session type k and every session j: prev = the session before it in ADR->ODR->RDR (ADR: the previous RDR date),
prev_prev = the one before that (ODR: previous RDR; RDR: ADR of the same date; ADR: none).
whole link = prev's bars (all) vs prev_prev's DR; current link at minute t = j's bars closed by t vs prev's DR.
A link breaks the upside model if the first open is below the DR low or any M5 close is below it (mirror: downside).
model(j, t) = (upside alive, downside alive); -1 where prev is missing (scene21 returns None -> never equal).
"""
from __future__ import annotations

import bisect

import numpy as np

from common import load

ORDER = ("ADR", "ODR", "RDR")


def model_arrays(inst, d):
    info, boxes, bars, off = load(inst)
    by = {(b["date"], b["session"]): i for i, b in enumerate(boxes)}
    rdr = sorted(b["date"] for b in boxes if b["session"] == "RDR")
    k = d["sess"]; S = d["S"]; start = d["start"]
    n = len(d["date"])
    pk = ORDER[ORDER.index(k) - 1] if k != "ADR" else None

    def prev_rdr(date):
        j = bisect.bisect_left(rdr, date) - 1
        return by.get((rdr[j], "RDR")) if j >= 0 else None

    def link(pbox, a):
        if pbox is None or not len(a): return (False, False)
        lo, hi = pbox["dr_low"], pbox["dr_high"]
        return (bool(a[0, 1] < lo or (a[:, 4] < lo).any()), bool(a[0, 1] > hi or (a[:, 4] > hi).any()))

    has_prev = np.zeros(n, bool)
    whole_up = np.zeros(n, bool); whole_dn = np.zeros(n, bool)
    cur_up = np.zeros((n, S), bool); cur_dn = np.zeros((n, S), bool)   # broken by the bar closing at slot s (cumulative)
    for r, date in enumerate(d["date"]):
        p_i = by.get((date, pk)) if pk else prev_rdr(date)
        if p_i is None: continue
        has_prev[r] = True
        pbox = boxes[p_i]
        pp_i = by.get((date, "ADR")) if pk == "ODR" else (prev_rdr(date) if pk == "ADR" else None)
        if pk == "ODR": pp_i = by.get((date, "ADR"))
        if pk == "ADR": pp_i = prev_rdr(date)
        if pk is None: pp_i = None
        if pp_i is not None:
            wu, wd = link(boxes[pp_i], bars[off[p_i]:off[p_i + 1]])
            whole_up[r], whole_dn[r] = wu, wd
        i = by[(date, k)]
        a = bars[off[i]:off[i + 1]]
        if not len(a): continue
        lo, hi = pbox["dr_low"], pbox["dr_high"]
        first_up, first_dn = a[0, 1] < lo, a[0, 1] > hi
        slot = (a[:, 0] - start) // 5 - 1
        bu = np.zeros(S, bool); bd = np.zeros(S, bool)
        ok = (slot >= 0) & (slot < S)
        bu[slot[ok]] = a[ok, 4] < lo; bd[slot[ok]] = a[ok, 4] > hi
        cu = np.logical_or.accumulate(bu) | first_up
        cd = np.logical_or.accumulate(bd) | first_dn
        # before the session's first bar closes nothing of it is known: scene21 then returns (False, False)
        first_slot = slot[ok].min() if ok.any() else 0
        cu[:first_slot] = False; cd[:first_slot] = False
        cur_up[r], cur_dn[r] = cu, cd
    return dict(has_prev=has_prev, whole_up=whole_up, whole_dn=whole_dn, cur_up=cur_up, cur_dn=cur_dn)


def model_at(M, t, start):
    """(up alive, down alive) coded as 2*up + dn, or -1 where the previous session is missing."""
    s = (t - start) // 5 - 1
    up = ~(M["whole_up"] | M["cur_up"][:, s]); dn = ~(M["whole_dn"] | M["cur_dn"][:, s])
    return np.where(M["has_prev"], 2 * up.astype(int) + dn.astype(int), -1)
