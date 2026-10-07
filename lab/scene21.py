"""DR Lab — the data of the working screen «Созвездия» (design 21, lab/dist/index.html).

Two requests, both read-only and local:

- day_view(inst): the current trading day's M5 bars from TradingView Desktop (saved by live.fetch) on day minutes
  (ET minutes from the trading day's midnight; the evening before is negative: 18:00 = -360, ADR 19:30 = -270), the
  moment of the fetch on the same scale, and the box of the previous trading day's RDR. The screen computes the
  sessions (DR, IDR, confirmation, DR break) itself with the rules of live.py.
- cohort(inst, session, at): for a session at a minute (live, or a replay minute: prefix honesty, only bars closed by
  then are used), the similar sessions of 2006-2025 (lab/.runtime/boxes_*, build_boxes.py) and what each did after that
  minute, in its own IDR units: its extremes up and down with their times, its closes and bar ranges every 5 minutes,
  whether its DR held, and (before a confirmation) its first later confirmation. The screen draws the stars, the
  places, the fan and the percentages from these; definitions in docs/SEMANTICS.md («Экран Созвездия»).

Similar sessions (same instrument and session, complete, weekday):
- confirmed: same direction, confirmation within 15 minutes of today's and not after the minute, DR not broken by then;
- after a DR break: the same, DR broken by then; measured on the new side (the opposite IDR edge, direction flipped);
- before a confirmation: no confirmation by the minute, the same box colour and the same state of the day's models
  (upside / downside alive); the models are dropped when fewer than 40 sessions remain;
- in all three: price at the minute within 0.25 IDR of today's on that scale (0.5, then no limit, when fewer than 40).
The base is M5: a history session is measured from its last M5 close at or before the minute.
"""
from __future__ import annotations

import bisect
import json
from pathlib import Path

import numpy as np
import pandas as pd

import live

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".runtime"
SESS = {"ADR": (-270, -210, 120), "ODR": (180, 240, 510), "RDR": (570, 630, 960)}   # day minutes
SHIFT = {"ADR": 1440, "ODR": 0, "RDR": 0}                                          # history minute = day minute + shift
ORDER = ("ADR", "ODR", "RDR")
_B = {}
_CACHE = {}


def _boxes(inst):
    if inst in _B: return _B[inst]
    p = RUNTIME / f"boxes_{inst.lower()}_meta.json"
    if not p.exists(): return None
    meta = json.loads(p.read_text(encoding="utf-8"))
    z = np.load(RUNTIME / f"boxes_{inst.lower()}.npz")
    boxes = meta["boxes"]
    B = dict(info=meta["info"], boxes=boxes, bars=z["bars"], off=z["offsets"], tick=meta["info"]["tick"],
             idx={(b["date"], b["session"]): i for i, b in enumerate(boxes)},
             rdr=sorted(b["date"] for b in boxes if b["session"] == "RDR"))
    _B[inst] = B
    return B


# ---------- the trading day from TradingView ----------
def _day_raw(inst):
    raw = live._load(inst)
    if raw is None: return None, None
    b = np.asarray(raw["bars"], float)
    et = pd.to_datetime(b[:, 0].astype(np.int64), unit="s", utc=True).tz_convert("America/New_York")
    fetched = pd.Timestamp(raw["fetched_at"]).tz_convert("America/New_York")

    def minutes(D):
        return ((et - D) / pd.Timedelta(minutes=1)).to_numpy()

    D = (fetched + pd.Timedelta(hours=6)).normalize()        # a trading day starts at 18:00 ET the evening before
    m = minutes(D)
    if not ((m >= -360) & (m < 1020)).any():                 # weekend or holiday: the last day that has bars
        D = (et[-1] + pd.Timedelta(hours=6)).normalize(); m = minutes(D)
    return raw, dict(b=b, et=et, D=D, m=m, fetched=fetched)


def _box(bars, start, formed):
    """Seven box levels from [t_open, o, h, l, c] rows of one session (None if the formation hour is incomplete)."""
    w = [x for x in bars if start <= x[0] < formed]
    if len(w) != (formed - start) // 5: return None
    o = np.array([x[1] for x in w]); h = np.array([x[2] for x in w]); l = np.array([x[3] for x in w]); c = np.array([x[4] for x in w])
    idr_h, idr_l = float(np.maximum(o, c).max()), float(np.minimum(o, c).min())
    if idr_h <= idr_l: return None
    return dict(drH=float(h.max()), drL=float(l.min()), idrH=idr_h, idrL=idr_l, open=float(o[0]), close=float(c[-1]))


def day_view(inst):
    if inst not in live.SYMBOLS: raise ValueError("Unknown instrument")
    raw, d = _day_raw(inst)
    if raw is None: return dict(status="no_data", message="Живых свечей ещё нет: нажмите «Обновить».")
    D, m, b = d["D"], d["m"], d["b"]
    keep = (m >= -360) & (m < 1020)
    bars = [[int(round(t)), float(o), float(h), float(l), float(c)] for t, (o, h, l, c) in zip(m[keep], b[keep, 1:5])]
    prev = None                                               # the previous trading day's RDR, from the same fetch
    for back in range(1, 6):
        P = D - pd.Timedelta(days=back)
        if P.weekday() > 4: continue
        mp = ((d["et"] - P) / pd.Timedelta(minutes=1)).to_numpy()
        rows = [[int(round(t)), float(o), float(h), float(l), float(c)] for t, (o, h, l, c) in zip(mp, b[:, 1:5]) if 570 <= t < 630]
        # operator 2026-10-06: the screen scrolls back to the previous trading day's RDR and no further, so its candles
        # from 09:30 to 18:00 come along, placed one day before today's minute 0 (after a weekend Friday sits right
        # before Sunday's evening: the clock on the axis stays right, the closed days are not drawn as empty space)
        early = [[int(round(t)) - 1440, float(o), float(h), float(l), float(c)] for t, (o, h, l, c) in zip(mp, b[:, 1:5]) if 570 <= t < 1080]
        bars = [r for r in early if r[0] < -360] + bars
        bx = _box(rows, 570, 630)
        if bx: prev = dict(bx, name="RDR " + P.strftime("%d.%m"), date=str(P.date())); break
        if rows: break
    now = float((d["fetched"] - D) / pd.Timedelta(minutes=1))
    return dict(status="ok", instrument=inst, tick=live.TICK[inst], date=str(D.date()), weekday=int(D.weekday()),
                now=now, fetched_at=raw["fetched_at"], feed=raw.get("feed"), switched=bool(raw.get("switched")),
                source_interval=raw.get("source_interval", 5), bars=bars, prev=prev,
                base=_boxes(inst) is not None)


# ---------- one session at a minute (the rules of live.py) ----------
def _state(bars, k, obs, now, is_live):
    start, formed, end = SESS[k]
    closed_by = now if is_live else obs
    closed = [x for x in bars if x[0] + 5 <= closed_by]
    known = bars if is_live else closed
    win = [x for x in known if start <= x[0] < formed]
    s = dict(k=k, start=start, formed=formed, end=end, obs=obs)
    if not win or obs < start: s["status"] = "before"; return s
    bx = _box(win, start, formed)
    s["complete"] = bx is not None and sum(1 for x in closed if start <= x[0] < formed) == (formed - start) // 5
    if not s["complete"]: s["status"] = "forming"; return s
    s.update(bx); s["width"] = bx["idrH"] - bx["idrL"]; s["box"] = "up" if bx["close"] > bx["open"] else ("down" if bx["close"] < bx["open"] else "flat")
    lim = min(obs, end)
    ins = [x for x in known if formed <= x[0] < lim]
    last = ins[-1] if ins else win[-1]
    s["price"] = last[4]
    conf = None
    for x in closed:
        if x[0] < formed or x[0] + 5 > lim: continue
        if x[4] > bx["drH"]: conf = (x[0] + 5, 1); break
        if x[4] < bx["drL"]: conf = (x[0] + 5, -1); break
    if not conf:
        s["status"] = "noconf" if obs >= end else "waiting"; return s
    s["conf"], s["side"] = conf
    opp = bx["drL"] if conf[1] == 1 else bx["drH"]
    s["failed"] = next((x[0] + 5 for x in closed if x[0] + 5 > conf[0] and x[0] + 5 <= lim and conf[1] * (x[4] - opp) < 0), None)
    s["status"] = "done" if obs >= end else ("broken" if s["failed"] else "confirmed")
    return s


def _link(prev, bars_after, upto=None):
    """Does the session (its bars) break the upside / downside model against the previous box? M5 closes only; an
    open beyond the level excludes the model at once (docs/STRATEGY.md §2.1-2.2)."""
    if prev is None or not len(bars_after): return (False, False)
    rows = [x for x in bars_after if upto is None or x[0] + 5 <= upto]
    if not rows: return (False, False)
    up = rows[0][1] < prev["drL"] or any(x[4] < prev["drL"] for x in rows)
    dn = rows[0][1] > prev["drH"] or any(x[4] > prev["drH"] for x in rows)
    return (up, dn)


def _models_today(bars, k, obs, prev_rdr):
    """(upside alive, downside alive) of the day at the minute: the previous session against the one before it (whole),
    this session against the previous one (bars closed by the minute)."""
    i = ORDER.index(k)
    boxes = {kk: _box([x for x in bars if SESS[kk][0] <= x[0] < SESS[kk][1]], SESS[kk][0], SESS[kk][1]) for kk in ORDER}
    prev_of = {"ADR": prev_rdr, "ODR": boxes["ADR"], "RDR": boxes["ODR"]}
    sess_bars = {kk: [x for x in bars if SESS[kk][0] <= x[0] < SESS[kk][2]] for kk in ORDER}
    links = [_link(prev_of[k], sess_bars[k], obs)]
    if i > 0:
        pk = ORDER[i - 1]
        links.append(_link(prev_of[pk], sess_bars[pk]))
    return (not any(l[0] for l in links), not any(l[1] for l in links))


# ---------- history ----------
def _hist_bars(B, i):
    return B["bars"][B["off"][i]:B["off"][i + 1]]


def _hist_box(B, date, k):
    i = B["idx"].get((date, k))
    return None if i is None else (i, B["boxes"][i])


def _hist_prev_rdr(B, date):
    j = bisect.bisect_left(B["rdr"], date) - 1
    return _hist_box(B, B["rdr"][j], "RDR") if j >= 0 else None


def _link_np(prev, a, upto=None):
    """_link on history arrays: prev box in ticks, a = [close minute, o, h, l, c] ticks, upto = history close minute."""
    if prev is None: return (False, False)
    if upto is not None: a = a[a[:, 0] <= upto]
    if not len(a): return (False, False)
    lo, hi = prev["dr_low"], prev["dr_high"]
    return (bool(a[0, 1] < lo or (a[:, 4] < lo).any()), bool(a[0, 1] > hi or (a[:, 4] > hi).any()))


def _models_hist(B, i, k, obs_h, cache):
    """The same model state for a history session at the same minute."""
    date = B["boxes"][i]["date"]
    key = (date, k)
    if key not in cache:
        idx = ORDER.index(k)
        pk = ORDER[idx - 1] if idx > 0 else None
        prev = _hist_box(B, date, pk) if pk else _hist_prev_rdr(B, date)
        prev_prev = _hist_box(B, date, "ADR") if pk == "ODR" else (_hist_prev_rdr(B, date) if pk == "ADR" else None)
        whole = _link_np(prev_prev[1], _hist_bars(B, prev[0])) if prev and prev_prev else (False, False)
        cache[key] = (prev, whole)
    prev, whole = cache[key]
    if prev is None: return None
    cur = _link_np(prev[1], _hist_bars(B, i), obs_h)
    return (not (whole[0] or cur[0]), not (whole[1] or cur[1]))


WINDOW = 15            # the activation window of the family, minutes (the operator, 2026-09-30)
BREAK_WEEKDAY = True   # the family after a DR break keeps the weekday (operator 2026-09-30: few sessions are fine, dashes where none)


def window_of(close, formed):
    """The 15-minute window of an event (a confirmation or a DR break) by the author's rule (operator 2026-09-30, after
    the forensic check of the author's videos, studies/forensic_window_2026_09_30/): by the TradingView label of the M5,
    i.e. its OPEN minute, counted from the start of the session's trading window (the box end), half-open
    [formed + 15 b, formed + 15 (b + 1)); `close` is the M5's close minute. RDR: candles 10:30, 10:35, 10:40 (closes
    10:35-10:45) -> 10:30-10:45; 10:45, 10:50, 10:55 (closes 10:50-11:00) -> 10:45-11:00. One window per event: the
    candle that closes exactly at a boundary belongs to the window that ends there (the author: the 10:55 candle is «in
    the first 30 minutes»; the 4:30 candle is «a different time bucket»). No double membership."""
    return (close - 5 - formed) // WINDOW


def family(inst, session, at=None):
    """The main object of the working screen since 2026-09-30 (meaning/08-semantika-klasterov.md): today's family and its
    whole clock-aligned M5 film.

    After today's DR break (operator 2026-09-30) the screen plays the break: the family becomes the sessions whose DR
    also broke — the same instrument, session, weekday (BREAK_WEEKDAY) and direction, the break in the same 15-minute
    window (window_of) — and its film runs from today's break in the scale of the break's direction (0 = the opposite
    IDR edge, positive = the break's way), as design 22's «По слому» mode. Such families are small (NQ RDR: a median of
    4 sessions); the operator accepts that, and an empty one shows no numbers.

    Family F = the same instrument, session, weekday and direction, confirmation in the same 15-minute window (window_of),
    complete sessions of 2006-2025. It is fixed by today's confirmation t0 (known from closed M5 only) and does not change
    during the day; one denominator N = |F| for every number. No re-matching by price or state, nothing renormalised to
    DR true. The film: for every clock M5 after t0 up to the end of the session, each member's bar in its own scale
    (d * (price - e) / w, e = its confirmation-side IDR edge, w = its IDR width): lo, hi, cl; None where it has no bar
    (after its last bar the market was closed; before it, a missing bar). Today's slice only chooses which columns are
    ahead; the film itself is the same all day, so the map at t0 (the Baseline) is never rewritten."""
    if inst not in live.SYMBOLS: raise ValueError("Unknown instrument")
    if session not in SESS: raise ValueError("Unknown session")
    raw, d = _day_raw(inst)
    if raw is None: return dict(status="no_data")
    B = _boxes(inst)
    if B is None: return dict(status="no_base", message="Нет базы сессий: python -B lab/build_boxes.py")
    view = day_view(inst)
    bars, now = view["bars"], view["now"]
    is_live = at is None
    obs = int(np.floor(now)) if is_live else int(at)
    s = _state(bars, session, obs, now, is_live)
    if s["status"] not in ("confirmed", "broken", "done") or not s.get("conf"):
        return dict(status=s["status"], session=session, obs=obs)
    start, formed, end = SESS[session]
    shift = SHIFT[session]
    brk = bool(s.get("failed"))
    side, wd = s["side"], view["weekday"]
    t0 = s["failed"] if brk else s["conf"]
    d_ = -side if brk else side                               # the direction of play: after a break, the break's
    b = window_of(t0, formed)
    key = ("family", inst, session, view["date"], t0, side, brk)
    if key in _CACHE:
        out = dict(_CACHE[key]); out.update(obs=obs, o5=obs // 5 * 5, status_today=s["status"]); return out
    grid = list(range(t0 + 5, end + 1, 5))
    mem = []
    for i, m in enumerate(B["boxes"]):
        if m["session"] != session or not m["complete"] or m["conf"] is None or m["side"] != side: continue
        if brk:
            if m["fail"] is None or window_of(m["fail"] - shift, formed) != b: continue
            if BREAK_WEEKDAY and m["weekday"] != wd: continue
        elif m["weekday"] != wd or window_of(m["conf"] - shift, formed) != b: continue
        a = _hist_bars(B, i)
        w = m["idr_high"] - m["idr_low"]
        e = m["idr_high"] if d_ == 1 else m["idr_low"]       # the IDR edge on the side of play
        opp = m["dr_low"] if side == 1 else m["dr_high"]
        at_close = {int(r[0]) - shift: r for r in a}
        cu = lambda v: round(float(d_ * (v - e) / w), 3)
        lo, hi, cl = [], [], []
        for T in grid:
            r = at_close.get(T)
            if r is None: lo.append(None); hi.append(None); cl.append(None); continue
            top, bot = (r[2], r[3]) if d_ == 1 else (r[3], r[2])
            hi.append(cu(top)); lo.append(cu(bot)); cl.append(cu(r[4]))
        mem.append(dict(date=m["date"], conf=int(m["conf"]) - shift, fail=None if m["fail"] is None else int(m["fail"]) - shift,
                        held=None if brk else m["fail"] is None, uOpp=None if brk else cu(opp),
                        last=int(a[-1, 0]) - shift, lo=lo, hi=hi, cl=cl))
    clk = lambda t: f"{(t // 60) % 24:02d}:{t % 60:02d}"
    days = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")
    w0 = formed + WINDOW * b
    what = "слом DR" if brk else "подтверждение"
    day = f" · {days[wd]}" if not brk or BREAK_WEEKDAY else ""
    out = dict(status="ok", mode="brk" if brk else "conf", session=session, t0=t0, side=side, weekday=wd, window=[w0, w0 + WINDOW],
               grid=grid, n=len(mem), cond=f"{session}{day} · {'лонг' if side == 1 else 'шорт'} · {what} {clk(w0)}–{clk(w0 + WINDOW)}",
               members=mem)
    if len(_CACHE) > 200: _CACHE.clear()
    _CACHE[key] = out
    res = dict(out); res.update(obs=obs, o5=obs // 5 * 5, status_today=s["status"])
    return res



# ---------- DR-LAB-SEM-1.0 experimental session map ----------
def family_sem_v1(inst, session, at=None):
    """Experimental SEM-1.0 snapshot for design 23.

    Additive endpoint: design 22 and family() are unchanged.
    Confirmation family: one fixed F, one R and one X event per historical member, measured after
    that member's OWN confirmation through the end of its ADR/ODR/RDR horizon.
    Break family: the same measurement starts after that member's own DR break and uses break direction.

    R = deepest directed low; X = farthest directed high. Event time is the OPEN minute of the first
    M5 attaining the final extreme. If any expected post-start M5 is missing, R/X are unknown.
    A common-clock close film is returned separately.
    """
    if inst not in live.SYMBOLS:
        raise ValueError("Unknown instrument")
    if session not in SESS:
        raise ValueError("Unknown session")
    raw, d = _day_raw(inst)
    if raw is None:
        return dict(status="no_data")
    B = _boxes(inst)
    if B is None:
        return dict(status="no_base", message="Нет базы сессий: python -B lab/build_boxes.py")

    view = day_view(inst)
    bars, now = view["bars"], view["now"]
    is_live = at is None
    obs = int(np.floor(now)) if is_live else int(at)
    s = _state(bars, session, obs, now, is_live)
    if s["status"] not in ("confirmed", "broken", "done") or not s.get("conf"):
        return dict(status=s["status"], session=session, obs=obs, semantics="DR-LAB-SEM-1.0")

    start, formed, end = SESS[session]
    shift = SHIFT[session]
    brk = bool(s.get("failed"))
    side, wd = s["side"], view["weekday"]
    t0 = s["failed"] if brk else s["conf"]
    dplay = -side if brk else side
    win = window_of(t0, formed)
    cache_key = ("family_sem_v1", inst, session, view["date"], t0, side, brk)

    if cache_key in _CACHE:
        out = dict(_CACHE[cache_key])
        out.update(obs=obs, o5=obs // 5 * 5, status_today=s["status"])
        return out

    path_grid = list(range(formed, end, 5))
    mem = []
    outcome = dict(held=0, broken=0, unknown=0, no_period=0)
    for i, m in enumerate(B["boxes"]):
        if m["session"] != session or not m["complete"] or m["conf"] is None or m["side"] != side:
            continue
        if brk:
            if m["fail"] is None or window_of(m["fail"] - shift, formed) != win:
                continue
            if BREAK_WEEKDAY and m["weekday"] != wd:
                continue
            event_start = int(m["fail"])
        else:
            if m["weekday"] != wd or window_of(m["conf"] - shift, formed) != win:
                continue
            event_start = int(m["conf"])

        a = _hist_bars(B, i)
        width = m["idr_high"] - m["idr_low"]
        if width <= 0:
            continue
        edge = m["idr_high"] if dplay == 1 else m["idr_low"]
        cu = lambda v: float(dplay * (v - edge) / width)
        by_close = {int(r[0]): r for r in a}

        path_cl = []
        for T in path_grid:
            r = by_close.get(T + 5 + shift)
            path_cl.append(None if r is None else round(cu(r[4]), 6))

        hist_end = end + shift
        expected = list(range(event_start + 5, hist_end + 1, 5))
        if not expected:
            ev_status = "no_period"
            rows = np.empty((0, 5), dtype=float)
        else:
            missing = any(T not in by_close for T in expected)
            ev_status = "unknown" if missing else "known"
            rows = np.array([by_close[T] for T in expected if T in by_close], dtype=float)

        r_u = x_u = tr = tx = None
        if ev_status == "known" and len(rows):
            phys_hi = rows[:, 2] if dplay == 1 else rows[:, 3]
            phys_lo = rows[:, 3] if dplay == 1 else rows[:, 2]
            hi_u = dplay * (phys_hi - edge) / width
            lo_u = dplay * (phys_lo - edge) / width
            ix = int(np.argmax(hi_u))
            ir = int(np.argmin(lo_u))
            x_u = round(float(hi_u[ix]), 6)
            r_u = round(float(lo_u[ir]), 6)
            tx = int(rows[ix, 0]) - 5 - shift
            tr = int(rows[ir, 0]) - 5 - shift

        outc = None
        if not brk:
            if m["fail"] is not None and int(m["fail"]) <= hist_end:
                outc = "broken"
            elif ev_status == "known":
                outc = "held"
            elif ev_status == "no_period":
                outc = "no_period"
            else:
                outc = "unknown"
            outcome[outc] += 1

        mem.append(dict(
            date=m["date"], conf=int(m["conf"]) - shift,
            fail=None if m["fail"] is None else int(m["fail"]) - shift,
            event_start=event_start - shift, event_status=ev_status,
            r=r_u, tr=tr, x=x_u, tx=tx, outcome=outc, path_cl=path_cl
        ))

    clk = lambda t: f"{(t // 60) % 24:02d}:{t % 60:02d}"
    days = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")
    w0 = formed + WINDOW * win
    what = "слом DR" if brk else "подтверждение"
    cond = f"{session} · {days[wd]} · {'лонг' if side == 1 else 'шорт'} · {what} {clk(w0)}–{clk(w0 + WINDOW)}"
    width_today = s["width"]
    edge_today = s["idrH"] if dplay == 1 else s["idrL"]
    today = dict(start=start, formed=formed, end=end, conf=s["conf"], fail=s.get("failed"),
                 side=side, direction=dplay, drH=s["drH"], drL=s["drL"],
                 idrH=s["idrH"], idrL=s["idrL"], width=width_today, edge=edge_today)

    out = dict(status="ok", semantics="DR-LAB-SEM-1.0", prototype=True,
               mode="brk" if brk else "conf", session=session, t0=t0, side=side, weekday=wd,
               window=[w0, w0 + WINDOW], path_grid=path_grid, n=len(mem), cond=cond,
               today=today, outcome=None if brk else outcome, members=mem)
    if len(_CACHE) > 200:
        _CACHE.clear()
    _CACHE[cache_key] = out
    res = dict(out)
    res.update(obs=obs, o5=obs // 5 * 5, status_today=s["status"])
    return res

def cohort(inst, session, at=None):
    if inst not in live.SYMBOLS: raise ValueError("Unknown instrument")
    if session not in SESS: raise ValueError("Unknown session")
    raw, d = _day_raw(inst)
    if raw is None: return dict(status="no_data")
    B = _boxes(inst)
    if B is None: return dict(status="no_base", message="Нет базы сессий: python -B lab/build_boxes.py")
    view = day_view(inst)
    bars, now = view["bars"], view["now"]
    is_live = at is None
    obs = int(np.floor(now)) if is_live else int(at)
    key = (inst, session, obs, is_live, raw["fetched_at"])
    if key in _CACHE: return _CACHE[key]
    s = _state(bars, session, obs, now, is_live)
    mode = {"confirmed": "conf", "broken": "brk", "waiting": "wait"}.get(s["status"])
    if mode is None: return dict(status=s["status"], session=session, obs=obs)
    start, formed, end = SESS[session]
    shift, tick = SHIFT[session], B["tick"]
    o5 = obs // 5 * 5                                         # history: from the last M5 close at or before the minute
    oh = o5 + shift
    grid = list(range(o5 + 5, end + 1, 5))
    w = s["width"]
    if mode == "conf":
        side = s["side"]; edge = s["idrH"] if side == 1 else s["idrL"]; u0 = side * (s["price"] - edge) / w; d_ = side
    elif mode == "brk":
        side = s["side"]; d_ = -side; edge = s["idrL"] if side == 1 else s["idrH"]; u0 = d_ * (s["price"] - edge) / w
    else:
        side = 0; d_ = 1; u0 = (s["price"] - s["idrL"]) / w
    models_today = _models_today(bars, session, obs, view["prev"]) if mode == "wait" else None
    pool = []
    mcache = {}
    for i, m in enumerate(B["boxes"]):
        if m["session"] != session or not m["complete"]: continue
        if mode in ("conf", "brk"):
            if m["side"] != side or m["conf"] is None or abs(m["conf"] - (s["conf"] + shift)) > 15 or m["conf"] > oh: continue
            if (m["fail"] is not None and m["fail"] <= oh) != (mode == "brk"): continue
        else:
            if m["conf"] is not None and m["conf"] <= oh: continue
            if m["box"] != s["box"]: continue
        a = _hist_bars(B, i)
        k0 = int(np.searchsorted(a[:, 0], oh, side="right"))
        if k0 == 0 or k0 >= len(a) or a[k0 - 1, 0] < oh - 5: continue
        wi = m["idr_high"] - m["idr_low"]
        if mode == "conf": e_ = m["idr_high"] if side == 1 else m["idr_low"]
        elif mode == "brk": e_ = m["idr_low"] if side == 1 else m["idr_high"]
        else: e_ = m["idr_low"]
        rec = dict(i=i, e=e_, w=wi, k0=k0, pos=float(d_ * (a[k0 - 1, 4] - e_) / wi))
        if mode == "wait": rec["model"] = _models_hist(B, i, session, oh, mcache)
        pool.append(rec)
    used_models = False
    if mode == "wait" and models_today is not None:
        sel = [x for x in pool if x["model"] == models_today]
        if len(sel) >= 40: pool, used_models = sel, True
    band, sel = None, pool
    for bw in (0.25, 0.5):
        cand = [x for x in pool if abs(x["pos"] - u0) <= bw]
        if len(cand) >= 40: band, sel = bw, cand; break
    for rec in sel:
        m = B["boxes"][rec["i"]]; a = _hist_bars(B, rec["i"]); fut = a[rec["k0"]:]
        cu = lambda v: d_ * (v - rec["e"]) / rec["w"]
        hi = cu(fut[:, 2] if d_ == 1 else fut[:, 3]); lo = cu(fut[:, 3] if d_ == 1 else fut[:, 2]); cl = cu(fut[:, 4])
        ix, iy = int(np.argmax(hi)), int(np.argmin(lo))
        gi = {int(t) - shift: j for j, t in enumerate(fut[:, 0])}
        r3 = lambda arr: [round(float(arr[gi[T]]), 3) if T in gi else None for T in grid]
        rec.update(date=m["date"], mx=round(float(hi[ix]), 4), tmx=int(fut[ix, 0]) - shift, mn=round(float(lo[iy]), 4), tmn=int(fut[iy, 0]) - shift,
                   cl=r3(cl), hi=r3(hi), lo=r3(lo), pos=round(rec["pos"], 4))
        if mode == "conf":
            opp = m["dr_low"] if side == 1 else m["dr_high"]
            rec["held"] = not bool((side * (fut[:, 4] - opp) < 0).any())
            rec["wick"] = bool((side * ((fut[:, 3] if side == 1 else fut[:, 2]) - opp) < 0).any())  # design 22: a wick beyond its own DR
        if mode == "wait":
            rec["cross"] = m["side"] if m["conf"] is not None else 0
            rec["uH"] = round(float((m["dr_high"] - rec["e"]) / rec["w"]), 4); rec["uL"] = round(float((m["dr_low"] - rec["e"]) / rec["w"]), 4)  # own DR
    clk = lambda t: f"{(t // 60) % 24:02d}:{t % 60:02d}"
    if mode == "wait":
        cond = "подтверждения нет к " + clk(obs) + ", коробка " + {"up": "зелёная", "down": "красная", "flat": "серая"}[s["box"]] +                (", модели дня те же" if used_models else "")
    else:
        cond = ("лонг" if side == 1 else "шорт") + ", подтверждение " + clk(s["conf"] - 15) + "–" + clk(s["conf"] + 15) +                (", DR сломан" if mode == "brk" else ", DR цел")
    cond += (", цена ±" + str(band).replace(".", ",") + " IDR") if band else ", цена без ограничения"
    keys = ("date", "pos", "mx", "tmx", "mn", "tmn", "cl", "hi", "lo") + (("held", "wick") if mode == "conf" else ()) + (("cross", "uH", "uL") if mode == "wait" else ())
    out = dict(status="ok", mode=mode, session=session, obs=obs, o5=o5, n=len(sel), band=band, cond=cond, grid=grid, u0=u0,
               models=dict(up=models_today[0], down=models_today[1], used=used_models) if models_today else None,
               sims={k: [x[k] for x in sel] for k in keys})
    if len(_CACHE) > 200: _CACHE.clear()
    _CACHE[key] = out
    return out
