"""DR Lab — the live session: current M5 bars from TradingView Desktop + the historical probability overlay.

Bars come from the local TradingView Desktop through the tradingview-mcp command line (Chrome DevTools, read-only
chart data). The chart's symbol and timeframe are switched to fetch, then restored. Live bars are only displayed and
matched against the 2006-2025 episodes; they are never written into the historical base or its statistics.

Overlay = prefix-matched cohort from history: same instrument, session and confirmation direction, confirmation within
15 minutes of today's, the same DR state at the observed minute (not broken / broken), and a similar position on the
IDR scale at that minute (within 0.25 IDR; widened to 0.5, then dropped, when fewer than 40 sessions remain). Everything
is measured strictly after the observed minute.
"""
from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path

import numpy as np
import pandas as pd

import engine_market as H

ROOT = Path(__file__).resolve().parent
LIVE = ROOT / ".runtime" / "live"
SYMBOLS = {"NQ": "CME_MINI:NQ1!", "ES": "CME_MINI:ES1!", "YM": "CBOT_MINI:YM1!"}
TICK = {"NQ": 0.25, "ES": 0.25, "YM": 1.0}
SESSIONS = H.SESSIONS
LEVELS = [round(x, 2) for x in np.arange(-1.5, 3.001, 0.25)]
_lock = threading.Lock()


def fetch(inst):
    """Pull bars of the instrument from TradingView Desktop in one node process (tv_fetch.mjs). A pane of the user's
    layout that already shows the future on 5 or 1 minute is read without switching anything; otherwise the active
    chart is switched to 5 minutes for 2-4 s and restored."""
    if inst not in SYMBOLS: raise ValueError("Unknown instrument")
    with _lock:
        r = subprocess.run(["node", str(ROOT / "tv_fetch.mjs"), SYMBOLS[inst], "1500"], capture_output=True, text=True,
                           timeout=90, encoding="utf-8")
    try:
        d = json.loads(r.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        raise RuntimeError("TradingView не ответил: " + (r.stderr or r.stdout).strip()[:200])
    if not d.get("success"):
        raise RuntimeError("TradingView Desktop не отдал свечи (он должен быть запущен с CDP): " + str(d.get("error"))[:200])
    bars = [[int(b[0]), float(b[1]), float(b[2]), float(b[3]), float(b[4])] for b in d["bars"]]
    interval = int(d.get("interval") or 5)
    if interval == 1:                                   # aggregate to clock M5; keep older M5 from the previous file
        m5 = {}
        for t, o, h, l, c in bars:
            k = t - t % 300
            if k not in m5: m5[k] = [k, o, h, l, c]
            else: m5[k][2] = max(m5[k][2], h); m5[k][3] = min(m5[k][3], l); m5[k][4] = c
        old = _load(inst)
        if old:
            for b in old["bars"]:
                if b[0] < min(m5): m5[b[0]] = b
        bars = [m5[k] for k in sorted(m5)]
    out = dict(instrument=inst, symbol=SYMBOLS[inst], feed=d.get("feed"), switched=bool(d.get("switched")), source_interval=interval,
               fetched_at=pd.Timestamp.now(tz="UTC").isoformat(), bars=bars)
    LIVE.mkdir(parents=True, exist_ok=True)
    (LIVE / f"{inst.lower()}.json").write_text(json.dumps(out), encoding="utf-8")
    return out


def _load(inst):
    p = LIVE / f"{inst.lower()}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _session_bars(raw, session):
    """M5 bars of the latest instance of `session` as minute coordinates of its calendar day, plus the fetch moment on
    the same coordinates."""
    start, formed, end = SESSIONS[session]
    b = np.asarray(raw["bars"], float)
    et = pd.to_datetime(b[:, 0].astype(np.int64), unit="s", utc=True).tz_convert("America/New_York")
    day = et.normalize().tz_localize(None).to_numpy().astype("datetime64[D]")
    mod = (et.hour * 60 + et.minute).to_numpy()
    if session == "ADR":
        eve = mod >= start; morn = mod < end - 1440
        iday = np.where(eve, day, day - np.timedelta64(1, "D")); t = np.where(eve, mod, mod + 1440); keep = eve | morn
    else:
        keep = (mod >= start) & (mod < end); iday, t = day, mod
    if not keep.any(): return None
    last_day = iday[keep].max()
    m = keep & (iday == last_day)
    fetched = pd.Timestamp(raw["fetched_at"]).tz_convert("America/New_York").tz_localize(None)
    now = (fetched - pd.Timestamp(str(last_day))).total_seconds() / 60.0          # minutes since that calendar midnight
    trade_day = last_day + (np.timedelta64(1, "D") if session == "ADR" else np.timedelta64(0, "D"))
    return dict(day=str(trade_day), t=t[m].astype(int), o=b[m, 1], h=b[m, 2], l=b[m, 3], c=b[m, 4], now=now)


def _coord(px, edge, width, side):
    return side * (px - edge) / width


def state(inst, session, at=None):
    """`at` (minute coordinate of a candle close) replays the screen as it was at that minute: only bars closed by
    then are known; later candles are still returned for display."""
    raw = _load(inst)
    if raw is None: return dict(status="no_data", message="Живых свечей ещё нет: нажмите «Обновить».")
    tick = TICK[inst]
    start, formed, end = SESSIONS[session]
    sb = _session_bars(raw, session)
    if sb is None: return dict(status="no_session", message=f"В загруженных свечах нет сессии {session}.", fetched_at=raw["fetched_at"])
    t, o, h, l, c = sb["t"], sb["o"] / tick, sb["h"] / tick, sb["l"] / tick, sb["c"] / tick
    live_now = sb["now"]
    replay = at is not None
    now = float(at) if replay else live_now
    closed = t + 5 <= now + 1e-9                          # an M5 bar counts only after its close
    known = closed if replay else np.ones(len(t), bool)   # bars whose highs and lows are known at the observed minute
    running = (not replay) and bool(start <= now < end and (t[-1] + 5) >= now - 10)
    if replay:
        observed = int(at)
        kk = np.flatnonzero(closed)
        price_now = float(c[kk[-1]]) if len(kk) else None
    elif running:
        observed = int(np.floor(now))                    # the live minute; price = last trade inside the forming bar
        price_now = float(c[-1])
    else:
        observed = int(t[closed][-1] + 5) if closed.any() else None
        price_now = float(c[closed][-1]) if closed.any() else None
    out = dict(status="forming", instrument=inst, session=session, day=sb["day"], feed=raw.get("feed"), switched=raw.get("switched"),
               source_interval=raw.get("source_interval", 5), fetched_at=raw["fetched_at"], running=running,
               tick=tick, start=start, formed=formed, end=end, observed=observed, replay=int(at) if replay else None,
               bars=[[int(a), float(b_ * tick), float(cc * tick), float(d * tick), float(e * tick), bool(f)] for a, b_, cc, d, e, f in zip(t, o, h, l, c, t + 5 <= live_now + 1e-9)])
    win = t < formed
    if win.sum() == 0: return out
    wo, wc = o[win], c[win]
    out["open"] = float(o[win][0] * tick)
    out["window_complete"] = bool(win.sum() == (formed - start) // 5 and closed[win].all())
    dr_hi, dr_lo = float(h[win].max()), float(l[win].min())
    idr_hi, idr_lo = float(np.maximum(wo, wc).max()), float(np.minimum(wo, wc).min())
    out.update(dr_high=dr_hi * tick, dr_low=dr_lo * tick, idr_high=idr_hi * tick, idr_low=idr_lo * tick)
    if not out["window_complete"] or observed is None or observed <= formed or price_now is None:
        return out
    width = idr_hi - idr_lo
    conf = None
    for k in np.flatnonzero((t >= formed) & closed):
        if c[k] > dr_hi: conf = (int(t[k] + 5), 1); break
        if c[k] < dr_lo: conf = (int(t[k] + 5), -1); break
    if conf is None or width <= 0:
        out["status"] = "waiting"
        out["pending"] = _pending(inst, session, observed)
        return out
    tau, side = conf
    edge = idr_hi if side == 1 else idr_lo
    opp = dr_lo if side == 1 else dr_hi
    fail_k = [k for k in np.flatnonzero(closed & (t + 5 > tau)) if side * (c[k] - opp) < 0]
    failed_at = int(t[fail_k[0]] + 5) if fail_k else None
    since = (t + 5 > tau) & known
    now_coord = float(_coord(price_now, edge, width, side))
    out.update(status="confirmed", direction="long" if side == 1 else "short", confirmation=tau, edge=edge * tick, width=width * tick,
               failed_at=failed_at, now_coord=now_coord, price_now=price_now * tick,
               retr_so_far=float(_coord((l if side == 1 else h)[since], edge, width, side).min()) if since.any() else None,
               ext_so_far=float(_coord((h if side == 1 else l)[since], edge, width, side).max()) if since.any() else None)
    out["overlay"] = _overlay(inst, session, "long" if side == 1 else "short", tau, observed, now_coord, failed_at is not None)
    return out


def _pending(inst, session, observed):
    """DR formed, no confirmation yet: how later confirmations split historically."""
    later = [e for e in H._E if e["instrument"] == inst and e["session"] == session and e["confirmation"] > observed]
    census = H._INFO[inst]["census"][session]
    never = census["no_confirmation"]
    n = len(later) + never
    lo = [e for e in later if e["direction"] == "long"]; sh = [e for e in later if e["direction"] == "short"]
    med = lambda xs: H.clock(float(np.median([e["confirmation"] for e in xs]))) if xs else None
    return dict(n=n, long_pct=100 * len(lo) / n if n else None, short_pct=100 * len(sh) / n if n else None,
                none_pct=100 * never / n if n else None, long_median=med(lo), short_median=med(sh))


def _overlay(inst, session, direction, tau, observed, now_coord, failed):
    """Similar sessions of history at the observed minute, and everything the screen draws from them."""
    formed, end = SESSIONS[session][1:]
    grid = np.arange(observed + 5, end + 1, 5)
    pool = []
    for e in H._E:
        if e["instrument"] != inst or e["session"] != session or e["direction"] != direction or not e["complete"]:
            continue
        if abs(e["confirmation"] - tau) > 15 or e["confirmation"] > observed: continue
        b = H.bars(e); side = H.side_of(e)
        past = b[b[:, 0] <= observed]; fut = b[b[:, 0] > observed]
        if not len(past) or not len(fut): continue
        ends, closes = H.m5_closes(past)
        opp = e["dr_low"] if side == 1 else e["dr_high"]
        was_failed = bool(((ends <= observed) & (ends > e["confirmation"]) & (side * (closes - opp) < 0)).any())
        if was_failed != failed: continue
        pos = float(side * (past[-1, 4] - e["edge"]) / e["width"])
        lows = side * ((fut[:, 3] if side == 1 else fut[:, 2]) - e["edge"]) / e["width"]
        highs = side * ((fut[:, 2] if side == 1 else fut[:, 3]) - e["edge"]) / e["width"]
        k = np.searchsorted(fut[:, 0], grid); kk = np.minimum(k, len(fut) - 1)
        path = np.where((k < len(fut)) & (fut[kk, 0] == grid), side * (fut[kk, 4] - e["edge"]) / e["width"] - pos, np.nan)
        pool.append(dict(pos=pos, retracement=float(lows.min()), retracement_time=int(fut[int(np.argmin(lows)), 0]),
                         extension=float(highs.max()), extension_time=int(fut[int(np.argmax(highs)), 0]),
                         dr_true=bool(e["dr_true"]), path=path))
    band, cohort = None, pool
    for w in (0.25, 0.5):
        sel = [x for x in pool if abs(x["pos"] - now_coord) <= w]
        if len(sel) >= 40: band, cohort = w, sel; break
    n = len(cohort)
    if n == 0: return dict(n=0, pool=len(pool))
    fmin = np.array([x["retracement"] for x in cohort]); fmax = np.array([x["extension"] for x in cohort])
    tmin = np.array([x["retracement_time"] for x in cohort]); tmax = np.array([x["extension_time"] for x in cohort])
    touch = {L: 0 for L in LEVELS}
    for lo_, hi_ in zip(fmin, fmax):
        for L in LEVELS:
            if (L >= now_coord and hi_ >= L) or (L < now_coord and lo_ <= L): touch[L] += 1
    A = np.vstack([x["path"] for x in cohort])
    fan = []
    for j, g in enumerate(grid):
        v = A[:, j]; v = v[np.isfinite(v)]
        if len(v) >= 10:
            fan.append(dict(t=int(g), n=int(len(v)), low=float(now_coord + np.percentile(v, 20)),
                            mid=float(now_coord + np.percentile(v, 50)), high=float(now_coord + np.percentile(v, 80))))

    def cells_of(vals, times):
        c = {}
        for a_, b_ in zip(np.round(np.floor(vals / .1 + 1e-9) * .1, 1), (times - 1) // 15 * 15):
            c[(float(a_), int(b_))] = c.get((float(a_), int(b_)), 0) + 1
        return c

    def zones_of(vals, times):
        z = {}
        for a_, b_ in zip(np.round(np.floor(vals / .2 + 1e-9) * .2, 1), (times - 1) // 30 * 30):
            z[(float(a_), int(b_))] = z.get((float(a_), int(b_)), 0) + 1
        return [dict(lo=k[0], hi=round(k[0] + .2, 1), t=k[1], t_hi=k[1] + 30, n=v, pct=round(100 * v / n, 1))
                for k, v in sorted(z.items(), key=lambda kv: -kv[1])[:3]]

    cmin, cmax = cells_of(fmin, tmin), cells_of(fmax, tmax)
    t0 = observed // 15 * 15
    r_hi = max(.5, round(float(np.ceil((now_coord + .15) * 10) / 10), 1)); e_lo = min(-1.0, round(float(np.floor((now_coord - .15) * 10) / 10), 1))
    defs = {"retr": ("retracement", round(r_hi - 3.1, 1), r_hi, .1), "ext": ("extension", e_lo, round(e_lo + 4.6, 1), .1),
            "rtime": ("retracement_time", t0, end, 15), "etime": ("extension_time", t0, end, 15)}
    charts = {k: H.hist(cohort, *d) for k, d in defs.items()}
    for k, d in defs.items(): charts[k]["reference"] = H.hist(pool, *d)["bins"]
    decile = {}                                         # where the retracement ends, by 0.1 IDR band (for the lines inside DR/IDR)
    for a_ in np.round(np.floor(fmin / .1 + 1e-9) * .1, 1): decile[float(a_)] = decile.get(float(a_), 0) + 1
    return dict(n=n, pool=len(pool), band=band, touch={str(L): round(100 * k / n, 1) for L, k in touch.items()},
                dr_true_pct=round(100 * float(np.mean([x["dr_true"] for x in cohort])), 1),
                future_min_median=float(np.median(fmin)), future_max_median=float(np.median(fmax)),
                fan=fan, cluster_min=[dict(lo=k[0], t=k[1], n=v) for k, v in cmin.items()],
                cluster_max=[dict(lo=k[0], t=k[1], n=v) for k, v in cmax.items()],
                zones_min=zones_of(fmin, tmin), zones_max=zones_of(fmax, tmax),
                retr_end={str(k): round(100 * v / n, 1) for k, v in sorted(decile.items())},
                # the same cohort in the format of the history charts
                charts=charts, heat=[dict(r=k[0], t=k[1], n=v) for k, v in cmin.items()],
                curve=fan, formed=int(t0), end=end, complete_n=n,
                median_retr=float(np.median(fmin)), median_ext=float(np.median(fmax)),
                median_rtime=H.clock(float(np.median(tmin))))
