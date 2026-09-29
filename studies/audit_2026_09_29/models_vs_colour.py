"""E7b: is the day-model effect on the RDR confirmation direction (C7a) more than box geometry?
Real RDR box + (a) the real aftermath, (b) a neighbouring day's aftermath (NBR null of geometry_nulls.py, K draws).
Models at 10:30 as lab/scene21.py computes them. Also: the model split inside each box colour.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from common import INST, dense, load  # noqa: E402
from geometry_nulls import increments, neighbour, rebuild, stats  # noqa: E402

K = 20


def models(inst, dates):
    info, boxes, bars, off = load(inst)
    by = {(b["date"], b["session"]): i for i, b in enumerate(boxes)}
    up = np.full(len(dates), -1); dn = np.full(len(dates), -1)
    for r, date in enumerate(dates):
        a_i, o_i, r_i = by.get((date, "ADR")), by.get((date, "ODR")), by.get((date, "RDR"))
        if a_i is None or o_i is None or r_i is None: continue
        A, O = boxes[a_i], boxes[o_i]
        ob = bars[off[o_i]:off[o_i + 1]]; rb = bars[off[r_i]:off[r_i + 1]]
        rbox = rb[rb[:, 0] <= 630]
        if len(rbox) < 12 or len(ob) < 12: continue
        up_b = rbox[0, 1] < O["dr_low"] or (rbox[:, 4] < O["dr_low"]).any() or ob[0, 1] < A["dr_low"] or (ob[:, 4] < A["dr_low"]).any()
        dn_b = rbox[0, 1] > O["dr_high"] or (rbox[:, 4] > O["dr_high"]).any() or ob[0, 1] > A["dr_high"] or (ob[:, 4] > A["dr_high"]).any()
        up[r], dn[r] = int(not up_b), int(not dn_b)
    return up, dn


def split(side, up, dn, mask=None):
    m = np.ones(len(side), bool) if mask is None else mask
    ou = m & (up == 1) & (dn == 0) & (side != 0); od = m & (dn == 1) & (up == 0) & (side != 0)
    if ou.sum() < 30 or od.sum() < 30: return None
    return 100 * (side[ou] == 1).mean() - 100 * (side[od] == 1).mean()


if __name__ == "__main__":
    for inst in INST:
        d = dense(inst, "RDR")
        full = ~(np.isnan(d["O"]).any(1) | np.isnan(d["H"]).any(1) | np.isnan(d["L"]).any(1) | np.isnan(d["C"]).any(1))
        O, H, L, C = (d[k][full] for k in "OHLC")
        dates = d["date"][full]
        up, dn = models(inst, dates)
        ok = up >= 0
        real = stats(O, H, L, C, 12)
        box = real["box"]
        res_real = split(real["side"][ok], up[ok], dn[ok])
        by_box_real = {b: split(real["side"][ok], up[ok], dn[ok], box[ok] == b) for b in (1, -1)}
        inc = increments(O, H, L, C)
        nulls, nb_box = [], {1: [], -1: []}
        for _ in range(K):
            s = stats(*rebuild(O, H, L, C, 12, *neighbour(inc, 12, full)), 12)
            nulls.append(split(s["side"][ok], up[ok], dn[ok]))
            for b in (1, -1): nb_box[b].append(split(s["side"][ok], up[ok], dn[ok], box[ok] == b))
        print(f"{inst}: long-share split only-up minus only-down: real {res_real:+.1f} pp, NBR null {np.mean(nulls):+.1f} pp (sd {np.std(nulls):.1f})")
        for b in (1, -1):
            print(f"   inside {'green' if b == 1 else 'red'} boxes: real {by_box_real[b]:+.1f} pp, NBR {np.mean(nb_box[b]):+.1f} pp")
