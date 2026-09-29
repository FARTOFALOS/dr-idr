"""Shared loader for the audit experiments (read-only over lab/.runtime; aggregates only leave this folder).

Dense per-session M5 arrays from boxes_<inst>.npz (build_boxes.py): one row per session instance of a type,
slots = clock M5 bars from the formation start to the session end, NaN where a bar is missing.
Prices stay in ticks.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

RT = Path(__file__).resolve().parents[2] / "lab" / ".runtime"
SESS = {"RDR": (570, 630, 960), "ODR": (180, 240, 510), "ADR": (1170, 1230, 1560)}
INST = ("NQ", "ES", "YM")


def load(inst):
    meta = json.loads((RT / f"boxes_{inst.lower()}_meta.json").read_text(encoding="utf-8"))
    z = np.load(RT / f"boxes_{inst.lower()}.npz")
    return meta["info"], meta["boxes"], z["bars"], z["offsets"]


def dense(inst, sess):
    """Return dict with meta arrays and dense O,H,L,C (n, S) for one session type."""
    info, boxes, bars, off = load(inst)
    start, formed, end = SESS[sess]
    S = (end - start) // 5
    idx = [i for i, b in enumerate(boxes) if b["session"] == sess]
    n = len(idx)
    O = np.full((n, S), np.nan); H = O.copy(); L = O.copy(); C = O.copy()
    for r, i in enumerate(idx):
        a = bars[off[i]:off[i + 1]]
        k = (a[:, 0] - start) // 5 - 1
        ok = (k >= 0) & (k < S)
        O[r, k[ok]] = a[ok, 1]; H[r, k[ok]] = a[ok, 2]; L[r, k[ok]] = a[ok, 3]; C[r, k[ok]] = a[ok, 4]
    g = lambda key: np.array([boxes[i][key] for i in idx])
    conf = np.array([boxes[i]["conf"] if boxes[i]["conf"] is not None else -1 for i in idx])
    fail = np.array([boxes[i]["fail"] if boxes[i]["fail"] is not None else -1 for i in idx])
    box = np.array([{"up": 1, "down": -1, "flat": 0}[boxes[i]["box"]] for i in idx])
    date = g("date")
    return dict(inst=inst, sess=sess, start=start, formed=formed, end=end, S=S, nbox=(formed - start) // 5,
                O=O, H=H, L=L, C=C, drh=g("dr_high").astype(float), drl=g("dr_low").astype(float),
                idrh=g("idr_high").astype(float), idrl=g("idr_low").astype(float), open=g("open").astype(float),
                close=g("close").astype(float), box=box, conf=conf, side=g("side").astype(int), fail=fail,
                complete=g("complete").astype(bool), date=date, year=np.array([int(d[:4]) for d in date]),
                weekday=g("weekday").astype(int), tick=info["tick"])


def wilson(k, n):
    if not n: return (np.nan, np.nan)
    z = 1.96; p = k / n; den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (100 * (c - h), 100 * (c + h))
