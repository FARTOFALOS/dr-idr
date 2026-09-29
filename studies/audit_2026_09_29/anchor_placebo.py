"""E2: the honest line of docs/RESEARCH.md backlog #1 — the DR rule on one-hour windows at every start time of the day.

For each start time s (every 5 minutes, ET) and each calendar day: box = 12 clock M5 bars [s, s+60), DR by wicks,
IDR by bodies, confirmation = first M5 close beyond DR after the box, DR true = no later M5 close beyond the opposite
DR within a FIXED horizon of 240 minutes after the box (the same for every start, so the anchors get no time advantage).
Only windows with all 12 + 48 M5 bars present are counted (weekends, the 17:00-18:00 halt and holidays drop out).
Question: are 03:00, 09:30 and 19:30 special against their neighbours, or does DR true follow the ratio of the box's
range to the next hours' volatility at every hour of the day?
Read-only over the G3 tape via lab/build_market.load_minutes; aggregates only.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lab"))
from build_market import TICKS, load_minutes  # noqa: E402

HOR = 48  # 240 minutes of M5 after the box


def dense_day(inst):
    df = load_minutes(inst)
    tick = TICKS[inst]
    d = pd_days(df["date"].to_numpy())
    slot = df["mod"].to_numpy() // 5
    key = d * 288 + slot
    first = np.r_[0, np.flatnonzero(key[1:] != key[:-1]) + 1]
    last = np.r_[first[1:], len(key)] - 1
    o = np.rint(df["o"].to_numpy() / tick); h = np.rint(df["h"].to_numpy() / tick)
    l = np.rint(df["l"].to_numpy() / tick); c = np.rint(df["c"].to_numpy() / tick)
    k = key[first]
    O = o[first]; C = c[last]
    Hh = np.maximum.reduceat(h, first); Ll = np.minimum.reduceat(l, first)
    d0 = k.min() // 288
    nd = k.max() // 288 - d0 + 2
    A = {x: np.full(nd * 288, np.nan) for x in "OHLC"}
    pos = k - d0 * 288
    A["O"][pos] = O; A["H"][pos] = Hh; A["L"][pos] = Ll; A["C"][pos] = C
    return {x: v.reshape(nd, 288) for x, v in A.items()}, d0


def pd_days(date_int):
    import pandas as pd
    return pd.to_datetime(pd.Series(date_int).astype(str)).to_numpy().astype("datetime64[D]").astype(np.int64)


def run(inst):
    A, d0 = dense_day(inst)
    E = {x: np.concatenate([v[:-1], v[1:]], axis=1) for x, v in A.items()}   # (days, 576): the day and the next
    out = {}
    for j in range(288):
        sl = slice(j, j + 12 + HOR)
        O, H, L, C = (E[x][:, sl] for x in "OHLC")
        ok = ~(np.isnan(O).any(1) | np.isnan(H).any(1) | np.isnan(L).any(1) | np.isnan(C).any(1))
        O, H, L, C = O[ok], H[ok], L[ok], C[ok]
        drh = H[:, :12].max(1); drl = L[:, :12].min(1)
        idrh = np.maximum(O[:, :12], C[:, :12]).max(1); idrl = np.minimum(O[:, :12], C[:, :12]).min(1)
        box = np.sign(C[:, 11] - O[:, 0])
        Cp, Hp, Lp = C[:, 12:], H[:, 12:], L[:, 12:]
        up = Cp > drh[:, None]; dn = Cp < drl[:, None]
        BIG = 10 ** 6
        ku = np.where(up.any(1), up.argmax(1), BIG); kd = np.where(dn.any(1), dn.argmax(1), BIG)
        side = np.where(ku < kd, 1, np.where(kd < ku, -1, 0)); k = np.minimum(ku, kd)
        later = np.arange(HOR)[None, :] > k[:, None]
        fail = np.where(side == 1, (later & (Cp < drl[:, None])).any(1), (later & (Cp > drh[:, None])).any(1))
        conf = (side != 0) & later.any(1) & (idrh > idrl)
        dr_w = drh - drl
        post_rng = Hp.max(1) - Lp.min(1)
        agree = conf & (box != 0)
        out[j] = dict(t=f"{j * 5 // 60:02d}:{j * 5 % 60:02d}", n=int(ok.sum()), n_conf=int(conf.sum()),
                      conf=100.0 * float(conf.mean()) if ok.any() else None,
                      true=100.0 * float((~fail[conf]).mean()) if conf.any() else None,
                      agree=100.0 * float((side[agree] == box[agree]).mean()) if agree.any() else None,
                      ratio=float(np.median(dr_w / np.maximum(post_rng, 1))) if ok.any() else None,
                      true_first30=100.0 * float((~fail[conf & (k < 6)]).mean()) if (conf & (k < 6)).any() else None,
                      share_first30=100.0 * float((conf & (k < 6)).sum() / max(1, conf.sum())))
    return out


if __name__ == "__main__":
    res = {}
    for inst in ("NQ", "ES", "YM"):
        t0 = time.time()
        res[inst] = run(inst)
        r = res[inst]
        for a in ("02:00", "02:30", "02:45", "03:00", "03:15", "03:30", "04:00", "08:30", "09:00", "09:15", "09:20", "09:25", "09:30",
                  "09:35", "09:40", "09:45", "10:00", "10:30", "11:00", "12:00", "13:00", "19:00", "19:15", "19:30", "19:45", "20:00", "21:00"):
            j = int(a[:2]) * 12 + int(a[3:]) // 5
            x = r[j]
            if x["true"] is None: print(inst, a, "no data"); continue
            print(f"{inst} {a} n={x['n']:5d} conf {x['conf']:.1f} DRtrue {x['true']:.1f} (first30 {x['true_first30']:.1f}, share {x['share_first30']:.0f}%) "
                  f"agree {x['agree']:.1f} DRwidth/post-range {x['ratio']:.2f}", flush=True)
        print(inst, f"{time.time() - t0:.0f}s", flush=True)
    Path(__file__).with_suffix(".json").write_text(json.dumps(res, indent=0), encoding="utf-8")
