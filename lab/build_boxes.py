"""DR Lab — every session box of the tape with its M5 bars, for the screen «Созвездия» (read-only).

build_market.py keeps only confirmed sessions and their bars after the confirmation. The screen also needs sessions
before (or without) a confirmation, the box colour and the day's models, so this builds every session instance whose
formation hour is complete: its seven box levels, its confirmation and DR break (if any), and its clock M5 bars from the
start of the formation hour to the end of the session. Same tape, same definitions (docs/SEMANTICS.md), 2026 hidden,
no Volume. Minute coordinates are those of build_market.py (ADR after midnight +1440); a bar carries its CLOSE minute.

Run from the repository root: python -B lab/build_boxes.py [NQ ES YM]   (about 30-60 s per instrument)
Output: lab/.runtime/boxes_<inst>.npz and boxes_<inst>_meta.json (git-ignored, rebuildable).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_market import CLOSED_GAP_NS, SESSIONS, TICKS, instances, load_minutes, m5  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / ".runtime"
VERSION = "dr-lab-boxes-1"


def build(inst):
    tick = TICKS[inst]
    df = load_minutes(inst)
    ts = df["ts"].to_numpy()
    px = {k: np.rint(df[k].to_numpy() / tick).astype(np.int64) for k in ("o", "h", "l", "c")}
    meta, chunks, offsets = [], [], [0]
    for name, idx, iday, tt in instances(df):
        start, formed, end = SESSIONS[name]
        cut = np.r_[0, np.flatnonzero(iday[1:] != iday[:-1]) + 1, len(idx)]
        for a, z in zip(cut[:-1], cut[1:]):
            rows = idx[a:z]; t = tt[a:z]
            o, h, l, c = (px[k][rows] for k in ("o", "h", "l", "c"))
            win = t < formed
            if win.sum() == 0: continue
            wb, wo, wh, wl, wc, _ = m5(t[win], o[win], h[win], l[win], c[win])
            if len(wb) != (formed - start) // 5 or wb[0] != start: continue
            dr_hi, dr_lo = int(wh.max()), int(wl.min())
            idr_hi, idr_lo = int(np.maximum(wo, wc).max()), int(np.minimum(wo, wc).min())
            if idr_hi <= idr_lo: continue
            day0 = np.datetime64(int(iday[a]), "D")
            trade_day = day0 + (1 if name == "ADR" else 0)
            wd = int(pd.Timestamp(trade_day).weekday())
            if wd > 4: continue
            bs, bo, bh, bl, bc, blast = m5(t, o, h, l, c)            # whole session, clock M5 by open minute
            be = bs + 5                                             # close minute of each M5
            after = bs >= formed
            conf = None
            for k in np.flatnonzero(after):
                if bc[k] > dr_hi: conf = (int(be[k]), 1); break
                if bc[k] < dr_lo: conf = (int(be[k]), -1); break
            fail = None
            if conf:
                opp = dr_lo if conf[1] == 1 else dr_hi
                for k in np.flatnonzero(after & (be > conf[0])):
                    if conf[1] * (bc[k] - opp) < 0: fail = int(be[k]); break
            last_row = rows[-1]
            closed_early = last_row + 1 >= len(ts) or ts[last_row + 1] - ts[last_row] >= CLOSED_GAP_NS
            complete = bool(be[-1] >= end or closed_early)
            meta.append(dict(date=f"{pd.Timestamp(trade_day):%Y-%m-%d}", weekday=wd, session=name,
                             dr_high=dr_hi, dr_low=dr_lo, idr_high=idr_hi, idr_low=idr_lo, open=int(wo[0]), close=int(wc[-1]),
                             box="up" if wc[-1] > wo[0] else ("down" if wc[-1] < wo[0] else "flat"),
                             conf=conf[0] if conf else None, side=conf[1] if conf else 0, fail=fail, complete=complete))
            chunks.append(np.stack([be, bo, bh, bl, bc], axis=1).astype(np.int32))
            offsets.append(offsets[-1] + len(be))
    OUT.mkdir(exist_ok=True)
    np.savez_compressed(OUT / f"boxes_{inst.lower()}.npz", bars=np.concatenate(chunks), offsets=np.asarray(offsets, np.int64))
    info = dict(version=VERSION, instrument=inst, tick=tick, sessions=SESSIONS, stop_exclusive="2026-01-01", hidden="2026", boxes=len(meta))
    (OUT / f"boxes_{inst.lower()}_meta.json").write_text(json.dumps(dict(info=info, boxes=meta), ensure_ascii=False), encoding="utf-8")
    by = {s: sum(1 for m in meta if m["session"] == s) for s in SESSIONS}
    print(inst, "boxes", len(meta), by, "latest", max(m["date"] for m in meta), flush=True)


if __name__ == "__main__":
    for inst in (sys.argv[1:] or ["NQ", "ES", "YM"]):
        build(inst.upper())
