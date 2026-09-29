"""Equivalence of the vectorised replay (replay_core.py + models_vec.py) with the production code path
lab/scene21.cohort(), on history days.

For a sampled history session and minute, the day's M5 bars (previous trading day's RDR, ADR, ODR, RDR from
lab/.runtime/boxes_*) are handed to scene21 as if TradingView had delivered them (live._load is replaced inside this
process only; nothing is written). scene21.cohort(inst, session, at=minute) then runs unchanged, over the full base,
which contains that day too. The vectorised cohort is computed with the same pool (all years, the day included) and
the model filter before a confirmation. Compared: mode, n, band and the set of selected session dates.
"""
from __future__ import annotations

import bisect
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lab"))
import scene21  # noqa: E402
from common import dense, load  # noqa: E402
from models_vec import model_arrays, model_at  # noqa: E402
from replay_core import prep  # noqa: E402

SHIFT = {"ADR": 1440, "ODR": 0, "RDR": 0}
rng = np.random.default_rng(7)
CUR = {}
scene21.live._load = lambda inst: CUR.get(inst)


def fake_raw(inst, date, boxes, bars, off, by, rdr, tick):
    rows = []
    D = pd.Timestamp(date)

    def add(bdate, sess, cal):
        i = by.get((bdate, sess))
        if i is None: return
        for cm, o, h, l, c in bars[off[i]:off[i + 1]]:
            ts = (pd.Timestamp(cal) + pd.Timedelta(minutes=int(cm) - 5)).tz_localize("America/New_York", nonexistent="shift_forward", ambiguous=True)
            rows.append([int(ts.timestamp()), o * tick, h * tick, l * tick, c * tick])
    j = bisect.bisect_left(rdr, date) - 1
    if j >= 0: add(rdr[j], "RDR", rdr[j])
    add(date, "ADR", D - pd.Timedelta(days=1))
    add(date, "ODR", D)
    add(date, "RDR", D)
    rows.sort()
    fetched = (D + pd.Timedelta(hours=16, minutes=5)).tz_localize("America/New_York").tz_convert("UTC").isoformat()
    return dict(bars=rows, fetched_at=fetched, feed="history-replay", switched=False, source_interval=5)


def vec_cohort(d, P, t, i, mode, conf_by, fail_by, M):
    base = d["complete"] & P[t]["avail"]
    if mode in ("conf", "brk"):
        m = base & (d["side"] == d["side"][i]) & conf_by(t) & (np.abs(d["conf"] - d["conf"][i]) <= 15)
        m &= fail_by(t) if mode == "brk" else ~fail_by(t)
    else:
        m = base & ~conf_by(t) & (d["box"] == d["box"][i])
    pool = np.flatnonzero(m)
    used = False
    if mode == "wait":
        mod = model_at(M, t, d["start"])
        sel_m = pool[mod[pool] == mod[i]] if mod[i] >= 0 else pool[:0]
        if len(sel_m) >= 40: pool, used = sel_m, True
    pos = P[t][mode]["pos"]; u0 = pos[i]
    band, sel = None, pool
    for bw in (0.25, 0.5):
        c = pool[np.abs(pos[pool] - u0) <= bw]
        if len(c) >= 40: band, sel = bw, c; break
    return sel, band, used


if __name__ == "__main__":
    tot = agree_all = 0
    for inst in ("NQ", "ES", "YM"):
        info, boxes, bars, off = load(inst)
        by = {(b["date"], b["session"]): k for k, b in enumerate(boxes)}
        rdr = sorted(b["date"] for b in boxes if b["session"] == "RDR")
        tick = info["tick"]
        for sess in ("RDR", "ODR"):
            d = dense(inst, sess)
            grid, P, conf_by, fail_by = prep(d)
            M = model_arrays(inst, d)
            want = {"conf": 25, "brk": 15, "wait": 20}
            got = {k: 0 for k in want}; res = {k: [0, 0, 0, 0] for k in want}   # states, n equal, band equal, dates equal
            cand = np.flatnonzero((d["year"] >= 2016) & d["complete"])
            tries = 0
            while any(got[k] < want[k] for k in want) and tries < 5000:
                tries += 1
                i = int(rng.choice(cand)); t = int(rng.choice(grid))
                if not P[t]["avail"][i]: continue
                mode = ("brk" if fail_by(t)[i] else "conf") if conf_by(t)[i] else "wait"
                if got[mode] >= want[mode]: continue
                CUR[inst] = fake_raw(inst, str(d["date"][i]), boxes, bars, off, by, rdr, tick)
                prod = scene21.cohort(inst, sess, at=t - SHIFT[sess])
                if prod.get("status") != "ok" or prod.get("mode") != mode:
                    print("   state mismatch", inst, sess, d["date"][i], t, mode, prod.get("status"), prod.get("mode")); got[mode] += 1; res[mode][0] += 1; continue
                sel, band, used = vec_cohort(d, P, t, i, mode, conf_by, fail_by, M)
                same_dates = sorted(prod["sims"]["date"]) == sorted(d["date"][sel].tolist())
                r = res[mode]; r[0] += 1; r[1] += prod["n"] == len(sel); r[2] += prod["band"] == band; r[3] += same_dates
                got[mode] += 1
                if not same_dates:
                    print(f"   diff {inst} {sess} {d['date'][i]} t={t} {mode}: prod n={prod['n']} band={prod['band']} models={prod.get('models')} | vec n={len(sel)} band={band} models_used={used}")
            for k, (s_, a, b, c) in res.items():
                print(f"{inst} {sess} {k}: states {s_}, same n {a}, same band {b}, same selected dates {c}", flush=True)
                tot += s_; agree_all += c
    print(f"TOTAL states {tot}, identical cohorts {agree_all}")
