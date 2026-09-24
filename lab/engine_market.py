"""DR Lab engine over real NQ / ES / YM episodes (built by build_market.py). Same API contract as engine.py (demo).

Read-only. Nothing here reads the tape: episodes and their post-confirmation M1 bars come from .runtime.
Differences from the demo engine, all deliberate:
- M5 closes are taken from the last M1 bar of each clock bucket, not from `minute % 5`;
- target reach counts a hit even on an incomplete session, and reports unknowns with bounds;
- chart filters accept a range (`retr_hi`, `ext_hi`, `rtime_hi`, `etime_hi`), which the UI already sends.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".runtime"
SESSIONS = {"RDR": (570, 630, 960), "ODR": (180, 240, 510), "ADR": (1170, 1230, 1560)}
INSTRUMENTS = ("NQ", "ES", "YM")
_E = None; _INFO = {}; _BARS = {}; _OFF = {}; _BY_ID = None
VERSION = "dr-lab-market-2"


def initialize():
    global _E, _BY_ID
    _E = []
    for inst in INSTRUMENTS:
        meta = json.loads((RUNTIME / f"market_{inst.lower()}_meta.json").read_text(encoding="utf-8"))
        z = np.load(RUNTIME / f"market_{inst.lower()}.npz")
        _INFO[inst], _BARS[inst], _OFF[inst] = meta["info"], z["bars"], z["offsets"]
        for i, e in enumerate(meta["episodes"]): e["_i"] = i
        _E.extend(meta["episodes"])
    _BY_ID = {e["id"]: e for e in _E}


def bars(e):
    inst = e["instrument"]
    return _BARS[inst][_OFF[inst][e["_i"]]:_OFF[inst][e["_i"] + 1]]


def clock(minute):
    if minute is None: return None
    m = int(minute)
    return f"{m // 60 % 24:02d}:{m % 60:02d}" + (" +1" if m >= 1440 else "")


def percentile(values, q):
    a = sorted(values)
    if not a: return None
    p = (len(a) - 1) * q; lo, hi = math.floor(p), math.ceil(p)
    return a[lo] + (a[hi] - a[lo]) * (p - lo)


def interval(k, n):
    if not n: return None
    z = 1.959963984540054; p = k / n
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    radius = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(100 * (center - radius), 1), round(100 * (center + radius), 1)]


def side_of(e):
    return 1 if e["direction"] == "long" else -1


def m5_closes(b):
    """(bucket end minute, close) of each clock M5 bucket; b[:,0] are M1 close minutes."""
    end = (b[:, 0] + 4) // 5 * 5
    last = np.r_[np.flatnonzero(end[1:] != end[:-1]), len(end) - 1]
    return end[last], b[last, 4]


def metrics(b, e, side):
    edge, width = e["edge"], e["width"]
    lows = side * ((b[:, 3] if side == 1 else b[:, 2]) - edge) / width
    highs = side * ((b[:, 2] if side == 1 else b[:, 3]) - edge) / width
    ir, ie = int(np.argmin(lows)), int(np.argmax(highs))
    return dict(retracement=round(float(lows[ir]), 6), retracement_time=int(b[ir, 0]),
                extension=round(float(highs[ie]), 6), extension_time=int(b[ie, 0]))


def get_base(p):
    session = p.get("session", "RDR"); inst = p.get("instrument", "NQ")
    if session not in SESSIONS: raise ValueError("Unknown session")
    if inst not in INSTRUMENTS: raise ValueError("Unknown instrument")
    start = float(p.get("from", SESSIONS[session][1])); stop = float(p.get("to", SESSIONS[session][1] + 90))
    if start >= stop: raise ValueError("Начало окна должно быть раньше конца")
    d = p.get("direction", "long")
    if d not in ("long", "short", "all"): raise ValueError("Unknown direction")
    wd = p.get("weekday", "all")
    rows = [e for e in _E if e["instrument"] == inst and e["session"] == session and start <= e["confirmation"] < stop
            and (d == "all" or e["direction"] == d) and (wd == "all" or e["weekday"] == int(wd))]
    return rows


def hist(rows, field, lo, hi, step):
    bins = [{"lo": round(lo + i * step, 6), "hi": round(lo + (i + 1) * step, 6), "n": 0} for i in range(round((hi - lo) / step))]
    under = over = 0
    for e in rows:
        v = e[field] - (1 if field.endswith("_time") else 0)   # a time bucket holds the minute's trading, so 16:00 close -> 15:45
        idx = math.floor((v - lo + 1e-9) / step)
        if idx < 0: under += 1
        elif idx >= len(bins): over += 1
        else: bins[idx]["n"] += 1
    return {"bins": bins, "n": len(rows), "underflow": under, "overflow": over}


def scene(scene_id):
    e = _BY_ID.get(scene_id)
    if e is None: return None
    out = {k: v for k, v in e.items() if k != "_i"}
    out["bars"] = bars(e).tolist()
    return out


def query(p):
    if _E is None: initialize()
    base = get_base(p); rows = base
    mode = p.get("mode", "history")
    if mode not in ("history", "prefix"): raise ValueError("Unknown observation mode")
    future = [x for x in ("retr", "rtime", "ext", "etime") if p.get(x) not in (None, "")]
    if mode == "prefix" and (future or p.get("status", "all") != "all"):
        raise ValueError("Фильтры итогового исхода доступны только в исследовании полной истории")
    formed, end = SESSIONS[p.get("session", "RDR")][1:]
    observed = int(float(p.get("observed", formed + 60)))
    if not formed < observed < end: raise ValueError("Срез должен быть после формирования DR и до конца сессии")
    target = float(p.get("target", .8))
    if not .1 <= target <= 4: raise ValueError("Цель должна быть от 0.1 до 4 IDR")
    prefix_excluded = 0
    measured_src = []                       # (episode, bars to measure)
    if mode == "prefix":
        alive = []
        for e in rows:
            side = side_of(e); b = bars(e)
            past = b[b[:, 0] <= observed]
            if e["confirmation"] >= observed or not len(past) or past[-1, 0] != observed:
                continue
            ends, closes = m5_closes(past)
            done = ends <= observed
            later = ends > e["confirmation"]
            opp = e["dr_low"] if side == 1 else e["dr_high"]
            failed = bool((done & later & (side * (closes - opp) < 0)).any())
            reached = float((side * ((past[:, 2] if side == 1 else past[:, 3]) - e["edge"]) / e["width"]).max()) >= target
            if not failed and not reached:
                alive.append(e)
        prefix_excluded = len(rows) - len(alive); rows = alive
        for e in rows:
            b = bars(e); after = b[b[:, 0] > observed]
            if len(after): measured_src.append((e, after))
    else:
        if p.get("status", "all") != "all":
            wanted = p["status"] == "true"
            rows = [e for e in rows if e["dr_true"] is wanted]
        for field, param, step in (("retracement", "retr", .1), ("extension", "ext", .1),
                                   ("retracement_time", "rtime", 15), ("extension_time", "etime", 15)):
            if p.get(param) not in (None, ""):
                lo = float(p[param]); hi = float(p.get(param + "_hi", lo))
                lo, hi = min(lo, hi), max(lo, hi)
                shift = 1 if field.endswith("_time") else 0
                rows = [e for e in rows if e["complete"] and lo - 1e-9 <= e[field] - shift < hi + step - 1e-9]
        measured_src = [(e, None) for e in rows]
    # final-extremum charts: fully observed sessions only
    measured, hits, unknown = [], 0, 0
    for e, b in measured_src:
        m = e if b is None else {**e, **metrics(b, e, side_of(e))}
        if m["extension"] >= target: hits += 1
        elif not e["complete"]: unknown += 1
        if e["complete"]: measured.append(m)
    known = [e for e in rows if e["complete"]]
    base_known = [e for e in base if e["complete"]]
    true_k = sum(e["dr_true"] is True for e in rows); true_n = sum(e["dr_true"] is not None for e in rows)
    time_lo = formed if mode == "history" else (observed // 15) * 15
    defs = {"retr": ("retracement", -2.6, .5, .1), "ext": ("extension", 0, 3.6, .1),
            "rtime": ("retracement_time", time_lo, end, 15), "etime": ("extension_time", time_lo, end, 15)}
    charts = {name: hist(measured, *d) for name, d in defs.items()}
    for name, d in defs.items(): charts[name]["reference"] = hist(base_known, *d)["bins"]
    counts = {}
    for e in measured:
        key = (math.floor((e["retracement"] + 1e-9) / .1), int((e["retracement_time"] - 1) // 15) * 15)
        counts[key] = counts.get(key, 0) + 1
    cells = [{"r": r / 10, "t": t, "n": n} for (r, t), n in sorted(counts.items())]
    curve = []
    grid = np.arange(formed + 5, end + 1, 5)
    cols = []
    for e in known:
        b = bars(e); side = side_of(e)
        pos = np.searchsorted(b[:, 0], grid); pos_c = np.minimum(pos, len(b) - 1)
        ok = (pos < len(b)) & (b[pos_c, 0] == grid)
        cols.append(np.where(ok, side * (b[pos_c, 4] - e["edge"]) / e["width"], np.nan))
    if cols:
        A = np.vstack(cols)
        for j, t in enumerate(grid):
            v = A[:, j]; v = v[np.isfinite(v)]
            if len(v):
                curve.append({"t": int(t), "n": int(len(v)), "low": float(np.percentile(v, 20)),
                              "mid": float(np.percentile(v, 50)), "high": float(np.percentile(v, 80))})
    tn = hits + sum(1 for m in measured if m["extension"] < target)
    total_scope = hits + unknown + sum(1 for m in measured if m["extension"] < target)
    inst = p.get("instrument", "NQ")
    return {"data_kind": "MARKET", "instrument": inst, "version": VERSION, "seed": None,
            "total": sum(e["instrument"] == inst for e in _E), "tick": _INFO[inst]["tick"],
            "provenance": f"{inst} {_INFO[inst]['start']} … 2025-12-31 · 2026 скрыт · без Volume",
            "query": p, "base_n": len(base), "n": len(rows), "complete_n": len(known),
            "unknown_n": len(rows) - len(known), "prefix_excluded": prefix_excluded,
            "true": {"k": true_k, "n": true_n, "pct": 100 * true_k / true_n if true_n else None, "interval": interval(true_k, true_n)},
            "target": {"k": hits, "n": tn, "pct": 100 * hits / tn if tn else None, "interval": interval(hits, tn), "unknown": unknown,
                       "bounds": [100 * hits / total_scope, 100 * (hits + unknown) / total_scope] if total_scope else None},
            "median_retr": percentile([e["retracement"] for e in measured], .5),
            "median_ext": percentile([e["extension"] for e in measured], .5),
            "median_rtime": clock(percentile([e["retracement_time"] for e in measured], .5)),
            "charts": charts, "heat": cells, "curve": curve, "end": end, "formed": formed,
            "scenes": [{k: e[k] for k in ("id", "date", "direction", "confirmation", "complete", "dr_true", "retracement",
                                          "retracement_time", "extension")} for e in rows[:80]]}
