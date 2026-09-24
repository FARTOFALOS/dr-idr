"""DR Lab — build DR/IDR episodes from the real NQ minute tape (read-only).

Definitions are frozen in docs/SEMANTICS.md. Tape: <market root>/<NQ|ES|YM> (the G3 canonical corpus spine, read-only);
market root = env DR_IDR_MARKET, default ../../g3-market-research/data/market next to this repository.
2026 stays hidden: the build stops at 2025-12-31 ET. Volume is not read. Prices are stored as integer ticks
(NQ, ES 0.25; YM 1). Minute coordinates are ET minutes of the session's calendar day; ADR minutes after midnight
are +1440. Every M1 bar carries its CLOSE minute.

Run from the repository root: python -B lab/build_market.py [NQ ES YM]   (about 30 s per instrument)
Output: lab/.runtime/market_<inst>.npz and market_<inst>_meta.json (git-ignored, rebuildable).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
MARKET = Path(os.environ.get("DR_IDR_MARKET") or (HERE.parents[1] / "g3-market-research" / "data" / "market"))
VERSION = "dr-lab-market-2"
TICKS = {"NQ": 0.25, "ES": 0.25, "YM": 1.0}
START, STOP = "2006-01-01", "2026-01-01"          # ET; 2026 hidden
SESSIONS = {"RDR": (570, 630, 960), "ODR": (180, 240, 510), "ADR": (1170, 1230, 1560)}
CLOSED_GAP_NS = 3 * 3600 * 10**9                 # a gap this long after the last bar = market closed early
OUT = HERE / ".runtime"


def load_minutes(inst):
    d = MARKET / inst
    if not d.exists(): raise SystemExit(f"market tape not found: {d} (set DR_IDR_MARKET)")
    ts = np.load(d / "close_ts_utc_ns.npy", mmap_mode="r")
    lo = np.searchsorted(ts, pd.Timestamp(START, tz="America/New_York").value)
    hi = np.searchsorted(ts, pd.Timestamp(STOP, tz="America/New_York").value)
    ts = np.asarray(ts[lo:hi], dtype="int64")
    et = pd.to_datetime(ts - 60_000_000_000, utc=True).tz_convert("America/New_York")   # bar open, ET
    df = pd.DataFrame({k: np.asarray(np.load(d / f"{n}.npy", mmap_mode="r")[lo:hi], dtype="float64")
                       for k, n in (("o", "open"), ("h", "high"), ("l", "low"), ("c", "close"))})
    df["date"] = (et.year * 10000 + et.month * 100 + et.day).to_numpy()
    df["mod"] = (et.hour * 60 + et.minute).to_numpy()
    df["ts"] = ts
    return df


def instances(df):
    """Assign each minute to a session instance: (session, calendar day of the window, minute coordinate)."""
    mod = df["mod"].to_numpy()
    day = pd.to_datetime(df["date"].astype(str)).to_numpy().astype("datetime64[D]").astype(np.int64)
    out = []
    for name, (start, formed, end) in SESSIONS.items():
        if name == "ADR":
            eve = mod >= start
            morn = mod < end - 1440
            idx = np.flatnonzero(eve | morn)
            iday = np.where(eve[idx], day[idx], day[idx] - 1)
            t = np.where(eve[idx], mod[idx], mod[idx] + 1440)
        else:
            idx = np.flatnonzero((mod >= start) & (mod < end))
            iday, t = day[idx], mod[idx]
        out.append((name, idx, iday, t))
    return out


def m5(t, o, h, l, c):
    """Clock-aligned M5 buckets by bar open minute: start, open, high, low, close, index of last M1."""
    b = t // 5 * 5
    first = np.r_[0, np.flatnonzero(b[1:] != b[:-1]) + 1]
    last = np.r_[first[1:], len(b)] - 1
    return (b[first], o[first], np.maximum.reduceat(h, first), np.minimum.reduceat(l, first), c[last], last)


def build(inst):
    TICK = TICKS[inst]
    df = load_minutes(inst)
    ts = df["ts"].to_numpy()
    px = {k: np.rint(df[k].to_numpy() / TICK).astype(np.int64) for k in ("o", "h", "l", "c")}
    meta, chunks, offsets = [], [], [0]
    census = {s: dict(instances=0, incomplete_window=0, flat_idr=0, no_confirmation=0, weekend=0, episodes=0) for s in SESSIONS}
    for name, idx, iday, tt in instances(df):
        start, formed, end = SESSIONS[name]
        cut = np.r_[0, np.flatnonzero(iday[1:] != iday[:-1]) + 1, len(idx)]
        for a, z in zip(cut[:-1], cut[1:]):
            census[name]["instances"] += 1
            rows = idx[a:z]; t = tt[a:z]
            o, h, l, c = (px[k][rows] for k in ("o", "h", "l", "c"))
            win = t < formed
            if win.sum() == 0:
                census[name]["incomplete_window"] += 1; continue
            wb, wo, wh, wl, wc, _ = m5(t[win], o[win], h[win], l[win], c[win])
            if len(wb) != (formed - start) // 5 or wb[0] != start:
                census[name]["incomplete_window"] += 1; continue
            dr_hi, dr_lo = int(wh.max()), int(wl.min())
            idr_hi, idr_lo = int(np.maximum(wo, wc).max()), int(np.minimum(wo, wc).min())
            if idr_hi <= idr_lo:
                census[name]["flat_idr"] += 1; continue
            obs = ~win
            if obs.sum() == 0:
                census[name]["no_confirmation"] += 1; continue
            ot, oo, oh, ol, oc = t[obs], o[obs], h[obs], l[obs], c[obs]
            ob, _, _, _, obc, olast = m5(ot, oo, oh, ol, oc)
            up = np.flatnonzero(obc > dr_hi); dn = np.flatnonzero(obc < dr_lo)
            k_up = up[0] if len(up) else None; k_dn = dn[0] if len(dn) else None
            if k_up is None and k_dn is None:
                census[name]["no_confirmation"] += 1; continue
            k = k_up if (k_dn is None or (k_up is not None and k_up < k_dn)) else k_dn
            side = 1 if k is k_up else -1
            tau = int(ob[k] + 5)
            e_up = np.flatnonzero(obc > idr_hi); e_dn = np.flatnonzero(obc < idr_lo)
            cands = ([(int(e_up[0]), 1)] if len(e_up) else []) + ([(int(e_dn[0]), -1)] if len(e_dn) else [])
            idr_first = (int(ob[min(cands)[0]] + 5), min(cands)[1]) if cands else None
            after = ot + 1 > tau
            if after.sum() == 0:
                census[name]["no_confirmation"] += 1; continue
            bt = ot[after] + 1
            bars = np.stack([bt, oo[after], oh[after], ol[after], oc[after]], axis=1)
            last_row = rows[obs][after][-1]
            closed_early = last_row + 1 >= len(ts) or ts[last_row + 1] - ts[last_row] >= CLOSED_GAP_NS
            complete = bool(bt[-1] == end or closed_early)
            edge = idr_hi if side == 1 else idr_lo
            width = idr_hi - idr_lo
            opposite = dr_lo if side == 1 else dr_hi
            later = np.arange(len(ob)) > k
            fail = np.flatnonzero(later & ((obc < dr_lo) if side == 1 else (obc > dr_hi)))
            dr_true = False if len(fail) else (True if complete else None)
            lowc = side * ((bars[:, 3] if side == 1 else bars[:, 2]) - edge) / width
            highc = side * ((bars[:, 2] if side == 1 else bars[:, 3]) - edge) / width
            ir, ie = int(np.argmin(lowc)), int(np.argmax(highc))
            day0 = np.datetime64(int(iday[a]), "D")
            trade_day = day0 + (1 if name == "ADR" else 0)
            wd = int(pd.Timestamp(trade_day).weekday())
            if wd > 4:
                census[name]["weekend"] += 1; continue
            ep = dict(id=f"{inst}-{pd.Timestamp(trade_day):%Y%m%d}-{name}", instrument=inst, tick=TICK, date=f"{pd.Timestamp(trade_day):%Y-%m-%d}", weekday=wd,
                      session=name, direction="long" if side == 1 else "short", confirmation=tau, formed=formed, end=end,
                      edge=edge, width=width, dr_high=dr_hi, dr_low=dr_lo, idr_high=idr_hi, idr_low=idr_lo,
                      open=int(wo[0]), window_close=int(wc[-1]), box="up" if wc[-1] > wo[0] else ("down" if wc[-1] < wo[0] else "flat"),
                      idr_first_time=idr_first[0] if idr_first else None, idr_first_side=idr_first[1] if idr_first else None,
                      complete=complete, closed_early=bool(closed_early and bt[-1] != end),
                      dr_true=dr_true, dr_fail_time=int(ob[fail[0]] + 5) if len(fail) else None,
                      retracement=round(float(lowc[ir]), 6), retracement_time=int(bt[ir]),
                      extension=round(float(highc[ie]), 6), extension_time=int(bt[ie]))
            meta.append(ep); chunks.append(bars.astype(np.int32)); offsets.append(offsets[-1] + len(bars))
            census[name]["episodes"] += 1
    OUT.mkdir(exist_ok=True)
    np.savez_compressed(OUT / f"market_{inst.lower()}.npz", bars=np.concatenate(chunks), offsets=np.asarray(offsets, np.int64))
    info = dict(version=VERSION, instrument=inst, tape=f"g3-market-research/data/market/{inst} (canonical corpus spine)", start=START, stop_exclusive=STOP,
                hidden="2026", tick=TICK, sessions=SESSIONS, census=census, episodes=len(meta))
    (OUT / f"market_{inst.lower()}_meta.json").write_text(json.dumps(dict(info=info, episodes=meta), ensure_ascii=False), encoding="utf-8")
    print(inst, json.dumps(census, ensure_ascii=False), "episodes", len(meta), flush=True)


if __name__ == "__main__":
    for inst in (sys.argv[1:] or ["NQ", "ES", "YM"]):
        build(inst.upper())
