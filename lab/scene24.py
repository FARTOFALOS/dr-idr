"""DR Lab design 24 — the statistical layer of the semantic specification DR-LAB-SEM-1.0.

The specification (meaning/lens/2026-10-01-specifikaciya-v1.md) is the source of meaning; this module implements its
measurements on the session base of the working screen (lab/.runtime/boxes_*, lab/build_boxes.py: every session
instance with its clock M5 candles from the box start to the session end, 2006-2025). Design 22 reads the same base
through lab/scene21.py and is not changed by this module.

The atom (operator, 2026-10-01): an M5 candle that exists in the base is an observation, day and night alike (ADR,
ODR and RDR are treated the same way). Only a wholly absent M5 on an event's horizon is a hole, and only where the
event cannot be determined without it.

Coordinates (spec §3.1): for a session of direction d (+1 long, -1 short) and IDR width w (ticks), u = d (p - e) / w,
e = the IDR edge on the side of play. Everything stays in integer ticks: a directed value v = d (p - e) goes out with
w, the price cell is floor(10 v / w) and a level u = a / b is tested as v b >= a w. No rounded price enters a test.

Families (spec §3.2, §9.3):
- confirmation family F = instrument x session x weekday of the trading date x direction x the 15-minute window of the
  confirming M5 (its TradingView label = open minute, counted from the box end), sessions of 2006-2025 strictly before
  the viewed trading date;
- break family F_break = instrument x session x weekday x the original direction x the 15-minute window of the M5 that
  broke the DR; orientation flipped (0 = the opposite IDR edge), events measured from each session's own break.
A session whose first confirmation (or first break) cannot be established because a whole M5 is missing before it
joins no family; it is counted in the journal of undetermined keys.

Events of a member (spec §5), from its own activation (the activating candle excluded) to the end E of its block (the
M5 closing at E included):
- R = the lowest directed low and the open minute of the first M5 reaching it (every tied open kept); X = the highest
  directed high, the same way; status known / unknown (an M5 missing on the horizon) / none (no M5 on the horizon);
- DR outcome (confirmation family): broken = an M5 closed strictly beyond its own opposite DR (a wick is not a close,
  equality is not a break, a later return does not undo it); held = fully observed without that; unknown; none;
- order of the first times: R_before_X / X_before_R / same_M5 / unknown, with the repeats kept.
The path: every common clock M5 of the block after the box, as directed low, high, close (None where absent).
"""
from __future__ import annotations

import bisect
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

import cluster24  # noqa: F401  (main-cluster-1, kept for its archived studies; the screen shows the zone map)
import scene21
import zonemap24

SEM_VERSION = "DR-LAB-SEM-1.0"
SESS = scene21.SESS            # day minutes: (box start, box end = start of the trading window f, block end E)
SHIFT = scene21.SHIFT          # history minute = day minute + shift (ADR after midnight +1440)
ORDER = scene21.ORDER
WINDOW = 15
DAYS = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")
RUNTIME = Path(__file__).resolve().parent / ".runtime"
_MISSING = {}
_SNAP = {}
SCOPES = ("weekday", "all")    # zone-map-3 §2: the weekday family by default, all weekdays only on request


def clk(t):
    t = int(t) % 1440
    return f"{t // 60:02d}:{t % 60:02d}"


def window_of(close, formed):
    """Spec §3.2: the window of an event by the open minute of its M5 (close - 5), half-open, from the box end."""
    return (close - 5 - formed) // WINDOW


def cell(v, w):
    """The 0.1-SD price cell [k/10, (k+1)/10) of a directed value v on width w (both ticks): exact floor."""
    return (10 * v) // w


def directed(row, d, e):
    """(low, high, close) of an M5 row (close minute, o, h, l, c; ticks) in directed ticks from the edge e. For a
    short the directed low comes from the physical high and the directed high from the physical low."""
    _, _, h, l, c = row
    return (l - e, h - e, c - e) if d == 1 else (e - h, e - l, e - c)


def measure(rows, start, end, d, e, opp=None):
    """Spec §5.1-5.2 on one session.

    rows: {close minute: (close, o, h, l, c)} in ticks; start: the close minute of the activating M5 (excluded);
    end: E (the M5 closing at E included, one opening at E not); d, e: orientation and edge; opp: the directed
    opposite DR (ticks) for the DR outcome, None when the outcome is not measured (break family)."""
    expected = range(start + 5, end + 1, 5)
    obs, missing = [], []
    for T in expected:
        r = rows.get(T)
        if r is None: missing.append(T)
        else: obs.append((T, directed(r, d, e)))
    status = "none" if not len(expected) else "unknown" if missing else "known"
    out = dict(s=status, missing=len(missing), expected=len(expected))
    if opp is not None:
        brk = next((T for T, (_, _, c) in obs if c < opp), None)
        out["outcome"] = "broken" if brk is not None else "none" if not len(expected) else "unknown" if missing else "held"
        out["break"] = brk
        out["break_time_known"] = brk is not None and not any(T < brk for T in missing)
    for name, j, pick in (("R", 0, min), ("X", 1, max)):
        if status == "known":
            v = pick(x[j] for _, x in obs)
            ties = [T - 5 for T, x in obs if x[j] == v]
            out[name] = dict(s="known", v=int(v), t=ties[0], ties=ties)
        else:
            ev = dict(s=status)
            if obs: ev["bound"] = int(pick(x[j] for _, x in obs))     # observed so far: a bound, never a final point
            out[name] = ev
    if status == "known":
        rt, xt = out["R"]["ties"], out["X"]["ties"]
        out["order"] = "R_before_X" if rt[0] < xt[0] else "X_before_R" if xt[0] < rt[0] else "same_M5"
        out["order_detail"] = dict(all_x_before_all_r=max(xt) < min(rt), all_r_before_all_x=max(rt) < min(xt),
                                   x_again_after_r=any(t > rt[0] for t in xt), r_again_after_x=any(t > xt[0] for t in rt))
    else:
        out["order"] = "unknown"
    return out


def reach(rows, start, end, d, e, w, level, up=True):
    """Spec §5.4 «на уровне или дальше» for one session over the M5 closing in (start, end]: 'yes' when an observed
    M5 reaches the level (evidence stands even if another M5 is missing), 'unknown' when not reached and an M5 is
    missing, 'no' otherwise (an empty horizon is 'no'). level = (a, b): u = a / b, b > 0."""
    a, b = level
    expected = range(start + 5, end + 1, 5)
    hit, gap = False, False
    for T in expected:
        r = rows.get(T)
        if r is None: gap = True; continue
        lo, hi, _ = directed(r, d, e)
        if (hi * b >= a * w) if up else (lo * b <= a * w): hit = True; break
    return "yes" if hit else "unknown" if gap else "no"


def visits(lo, hi, a, b):
    """Spec §5.4: an M5 range [lo, hi] visits the band [a, b): lo < b and hi >= a."""
    return lo < b and hi >= a


def crosses(lo, hi, L):
    """Spec §5.4: literal crossing of a level by a candle: lo <= L <= hi."""
    return lo <= L <= hi


# ---------- the session base ----------
def _base(inst):
    return scene21._boxes(inst)


def _rows(B, i, shift):
    """{close day-minute: (close, o, h, l, c)} ticks of instance i."""
    a = B["bars"][B["off"][i]:B["off"][i + 1]]
    return {int(r[0]) - shift: (int(r[0]) - shift, int(r[1]), int(r[2]), int(r[3]), int(r[4])) for r in a}


def _missing(inst, B, session):
    """Per instance of the session: the sorted close minutes of the M5 wholly absent after the box (day scale)."""
    key = (inst, session, id(B))
    if key in _MISSING: return _MISSING[key]
    start, formed, end = SESS[session]
    shift = SHIFT[session]
    exp = np.arange(formed + 5, end + 1, 5)
    out = {}
    for i, m in enumerate(B["boxes"]):
        if m["session"] != session: continue
        a = B["bars"][B["off"][i]:B["off"][i + 1]]
        out[i] = exp[~np.isin(exp, a[:, 0].astype(np.int64) - shift)].tolist()
    _MISSING[key] = out
    return out


def source_version(inst, B):
    p = RUNTIME / f"boxes_{inst.lower()}_meta.json"
    return dict(base=B["info"].get("version"), boxes=len(B["boxes"]), built=int(p.stat().st_mtime) if p.exists() else None,
                history=f"2006-01-01..{max(b['date'] for b in B['boxes'])}")


def _sid(inst, m):
    return f"{inst}-{m['date'].replace('-', '')}-{m['session']}"


# ---------- the viewed trading day: live from TradingView, or a date of the history ----------
def day_view(inst, date=None):
    if inst not in scene21.live.SYMBOLS: raise ValueError("Unknown instrument")
    if not date:
        v = scene21.day_view(inst)
        v["source"] = "live"
        return v
    return day_hist(inst, date)


def day_hist(inst, date):
    """A trading date of 2006-2025 from the session base, shown as if it were today: the M5 candles of its three blocks
    (ADR, ODR, RDR; nothing between them), the previous trading day's RDR box, and the whole day already closed (the
    screen moves through it by replay). Its families use only sessions of earlier dates."""
    B = _base(inst)
    if B is None: return dict(status="no_base", message="Нет базы сессий: python -B lab/build_boxes.py")
    tick = float(B["tick"])
    bars, wd = [], None
    for k in ORDER:
        i = B["idx"].get((date, k))
        if i is None: continue
        wd = B["boxes"][i]["weekday"]
        a = B["bars"][B["off"][i]:B["off"][i + 1]]
        bars += [[int(r[0]) - 5 - SHIFT[k], r[1] * tick, r[2] * tick, r[3] * tick, r[4] * tick] for r in a.tolist()]
    if not bars: return dict(status="no_data", message="В истории нет этого дня", date=date, source="history")
    bars.sort(key=lambda r: r[0])
    prev = None
    j = bisect.bisect_left(B["rdr"], date) - 1
    if j >= 0:
        pi = B["idx"].get((B["rdr"][j], "RDR"))
        if pi is not None:
            q = B["boxes"][pi]
            # operator 2026-10-06: the previous trading date's RDR candles one day before minute 0 (see scene21.day_view)
            a = B["bars"][B["off"][pi]:B["off"][pi + 1]]
            bars = [[int(r[0]) - 5 - SHIFT["RDR"] - 1440, r[1] * tick, r[2] * tick, r[3] * tick, r[4] * tick] for r in a.tolist()] + bars
            prev = dict(drH=q["dr_high"] * tick, drL=q["dr_low"] * tick, idrH=q["idr_high"] * tick, idrL=q["idr_low"] * tick,
                        open=q["open"] * tick, close=q["close"] * tick, name="RDR " + q["date"][8:10] + "." + q["date"][5:7], date=q["date"])
    return dict(status="ok", source="history", instrument=inst, tick=tick, date=date, weekday=wd, now=1020.0, fetched_at=None,
                feed="история " + date[8:10] + "." + date[5:7] + "." + date[:4], switched=False, source_interval=5,
                bars=bars, prev=prev, base=True)


def dates(inst):
    """Every trading date of the base with the sessions whose first confirmation is established that day (letters A, O,
    R): the history picker walks the days on which the chosen session has a family to show."""
    if inst not in scene21.live.SYMBOLS: raise ValueError("Unknown instrument")
    B = _base(inst)
    if B is None: return dict(status="no_base")
    flags = {}
    for session in ORDER:
        miss, shift = _missing(inst, B, session), SHIFT[session]
        for i, m in enumerate(B["boxes"]):
            if m["session"] != session: continue
            f = flags.setdefault(m["date"], [])
            conf = None if m["conf"] is None else int(m["conf"]) - shift
            if conf is not None and not any(T < conf for T in miss.get(i, [])): f.append(session[0])
    return dict(status="ok", instrument=inst, dates=[[d, "".join(flags[d])] for d in sorted(flags)])


# ---------- the snapshot of a family ----------
def _snapshot(inst, B, session, weekday, side, view, win, cutoff, scope="weekday"):
    """The family of the key and its measurements; independent of today's slice (spec §9.2, §13.1). scope 'all' drops
    the weekday from the key: another family, another N and snapshot (zone-map-3 §2.2), never a fallback."""
    key = (inst, session, weekday, side, view, win, cutoff, scope, source_version(inst, B)["built"])
    if key in _SNAP: return _SNAP[key]
    start, formed, end = SESS[session]
    shift = SHIFT[session]
    miss = _missing(inst, B, session)
    grid = list(range(formed + 5, end + 1, 5))          # the block's common clock M5 (close minutes) after the box
    members, journal = [], Counter()
    w_start, w_end = formed + WINDOW * win, formed + WINDOW * (win + 1)
    for i, m in enumerate(B["boxes"]):
        if m["session"] != session or (scope == "weekday" and m["weekday"] != weekday) or m["date"] >= cutoff: continue
        gaps = miss.get(i, [])
        conf = None if m["conf"] is None else int(m["conf"]) - shift
        # the first confirmation is established when no whole M5 is missing before it (spec §3.2)
        if conf is None:
            if gaps:
                journal["confirmation_undetermined"] += 1
                if gaps[0] <= w_end: journal["confirmation_undetermined_could_be_this_window"] += 1
            continue
        if any(T < conf for T in gaps):
            journal["confirmation_undetermined"] += 1
            if gaps[0] <= w_end and conf > w_start: journal["confirmation_undetermined_could_be_this_window"] += 1
            continue
        if m["side"] != side: continue
        fail = None if m["fail"] is None else int(m["fail"]) - shift
        if view == "conf":
            if window_of(conf, formed) != win: continue
            act, d = conf, side
        else:
            if fail is None:
                if any(T > conf for T in gaps):
                    journal["break_undetermined"] += 1
                    if any(conf < T <= w_end for T in gaps): journal["break_undetermined_could_be_this_window"] += 1
                continue
            if any(conf < T < fail for T in gaps):
                journal["break_undetermined"] += 1
                continue
            if window_of(fail, formed) != win: continue
            act, d = fail, -side
        rows = _rows(B, i, shift)
        e = (m["idr_high"] if d == 1 else m["idr_low"])
        w = m["idr_high"] - m["idr_low"]
        opp = None
        if view == "conf":
            opp = d * ((m["dr_low"] if side == 1 else m["dr_high"]) - e)
        ev = measure(rows, act, end, d, e, opp)
        path = [list(directed(rows[T], d, e)) if T in rows else None for T in grid]
        rec = dict(id=_sid(inst, m), date=m["date"], w=int(w), act=act, conf=conf, fail=fail, confWin=window_of(conf, formed),
                   R=ev["R"], X=ev["X"], order=ev["order"], orderDetail=ev.get("order_detail"), missing=ev["missing"], path=path)
        if view == "conf":
            rec.update(oppv=int(opp), outcome=ev["outcome"], brk=ev["break"], brkKnown=ev["break_time_known"],
                       drv=int(d * ((m["dr_high"] if side == 1 else m["dr_low"]) - e)))   # its own DR on the side of play
        members.append(rec)
    members.sort(key=lambda r: r["date"])
    N = len(members)

    def dist(name):
        cells, unknown, none = Counter(), 0, 0
        for r in members:
            x = r[name]
            if x["s"] == "known": cells[(cell(x["v"], r["w"]), (x["t"] - formed) // WINDOW)] += 1
            elif x["s"] == "unknown": unknown += 1
            else: none += 1
        return dict(cells=[[k, b, n] for (k, b), n in sorted(cells.items())], unknown=unknown, none=none, known=N - unknown - none)

    counts = dict(R=dist("R"), X=dist("X"), order=dict(Counter(r["order"] for r in members)))
    if view == "conf": counts["outcome"] = {k: sum(1 for r in members if r["outcome"] == k) for k in ("held", "broken", "unknown", "none")}
    ids = [r["id"] for r in members]
    src = source_version(inst, B)
    family_id = hashlib.sha1(json.dumps([SEM_VERSION, inst, session, weekday if scope == "weekday" else "all", side, view, win, cutoff, ids]).encode()).hexdigest()[:16]
    measured = [[r["id"], r["R"], r["X"], r.get("outcome"), r["order"]] for r in members]
    snapshot_id = hashlib.sha1(json.dumps([family_id, src, measured], sort_keys=True).encode()).hexdigest()[:16]
    what = "подтверждение" if view == "conf" else "слом DR"
    snap = dict(
        status="ok", semantics=SEM_VERSION, source=src, view=view, family_id=family_id, snapshot_id=snapshot_id,
        key=dict(instrument=inst, session=session, weekday=weekday, direction="long" if side == 1 else "short",
                 event="confirmation" if view == "conf" else "break", window=[w_start, w_end], cutoff=cutoff, scope=scope),
        cond=f"{session} · {DAYS[weekday] if scope == 'weekday' else 'все дни'} · {'лонг' if side == 1 else 'шорт'} · {what} {clk(w_start)}–{clk(w_end)}",
        N=N, ids=ids,
        scale=dict(orientation=side if view == "conf" else -side, edge="IDR на стороне подтверждения" if view == "conf" else "противоположный край IDR",
                   unit="ширина IDR", price_cell="1/10", time_cell=WINDOW, f=formed),
        schedule=dict(start=start, formed=formed, end=end),
        rules=dict(start="собственное " + ("подтверждение" if view == "conf" else "закрытие за DR") + " каждой сессии; эта M5 не входит",
                   end="конец блока " + clk(end) + "; M5, закрывшаяся в " + clk(end) + ", входит",
                   time="открытие первой M5, достигшей цены", atom="существующая M5-свеча базы; дырка = целиком отсутствующая M5"),
        grid=grid, members=members, counts=counts, journal=dict(journal))
    if len(_SNAP) > 64: _SNAP.clear()
    _SNAP[key] = snap
    return snap


def _today_zones(snap, bars, tick, d, e_px, w_px, act, slice_, formed, end):
    """Today's provisional R and X after the activation, from closed M5 only, and the status of every zone at the slice
    (zone-map-3 §24): HOLDS / POSSIBLE / IMPOSSIBLE by the reachable set; 'unknown' when a whole M5 is missing."""
    tk = lambda p: int(round(p / tick))
    e_t, w_t = tk(e_px), tk(w_px)
    have = {int(b[0]) + 5: b for b in bars}
    rows, gap = [], False
    for T in range(act + 5, slice_ + 1, 5):
        b = have.get(T)
        if b is None: gap = True; continue
        lo, hi = (b[3], b[2]) if d == 1 else (b[2], b[3])
        rows.append((T, d * (tk(lo) - e_t), d * (tk(hi) - e_t)))
    out = {}
    for ev, zm in snap.get("zones", {}).items():
        if gap:
            out[ev] = dict(state="unknown", status=["STATUS_UNKNOWN"] * len(zm["zones"]))
            continue
        if rows:
            j = min(range(len(rows)), key=lambda i: (rows[i][1], i)) if ev == "R" else min(range(len(rows)), key=lambda i: (-rows[i][2], i))
            v = rows[j][1] if ev == "R" else rows[j][2]
            q = zonemap24.cell_of(v, w_t, rows[j][0] - 5, formed)
            out[ev] = dict(state="ok", q=list(q), v10=10 * v, w=w_t,
                           status=[zonemap24.status(z["cell_mask"], ev, tuple(q), 10 * v, w_t, slice_, formed, end - 5) for z in zm["zones"]])
        else:
            out[ev] = dict(state="none", status=[zonemap24.status(z["cell_mask"], ev, None, None, w_t, slice_, formed, end - 5) for z in zm["zones"]])
    return out


def family(inst, session, at=None, date=None, view="auto"):
    """The request of design 24: today's state at the slice (closed M5 only, the rules of live.py) and the snapshot of
    its family. view: 'auto' = the break family after today's DR break, else the confirmation family; 'conf' = the
    original confirmation snapshot (kept after a break, spec §9.3); a suffix ':all' asks for the all-weekdays family
    (zone-map-3 §2.2, an explicit choice of the operator, never a fallback)."""
    view, _, sc = (view or "auto").partition(":")
    scope = "all" if sc == "all" else "weekday"
    if inst not in scene21.live.SYMBOLS: raise ValueError("Unknown instrument")
    if session not in SESS: raise ValueError("Unknown session")
    B = _base(inst)
    if B is None: return dict(status="no_base", message="Нет базы сессий: python -B lab/build_boxes.py")
    day = day_view(inst, date)
    if day.get("status") != "ok": return dict(status=day.get("status", "no_data"), message=day.get("message"))
    bars, now = day["bars"], day["now"]
    is_live = not date and at is None
    obs = int(np.floor(now)) if at is None else int(at)
    s = scene21._state(bars, session, obs, now, is_live)
    start, formed, end = SESS[session]
    today = dict(date=day["date"], source=day["source"], status=s["status"], obs=obs, slice=obs // 5 * 5)
    if not s.get("conf"):
        return dict(status=s["status"], session=session, today=today)
    side, c0, brk = s["side"], s["conf"], s.get("failed")
    today.update(c0=c0, side=side, window=window_of(c0, formed), brk=brk, brkWindow=None if brk is None else window_of(brk, formed),
                 idrH=s["idrH"], idrL=s["idrL"], drH=s["drH"], drL=s["drL"])
    v = "brk" if (view in ("auto", "brk") and brk) else "conf"
    win = today["brkWindow"] if v == "brk" else today["window"]
    cutoff = day["date"]
    snap = _snapshot(inst, B, session, day["weekday"], side, v, win, cutoff, scope)
    # the zone maps of R and X (zone-map-3, meaning/12): once per snapshot (kept in it), so the slice never moves them
    if "zones" not in snap: snap["zones"] = {e: zonemap24.evaluate(snap, e) for e in ("R", "X")}
    out = dict(snap)
    d = side if v == "conf" else -side
    e_px = (s["idrH"] if d == 1 else s["idrL"])
    act = c0 if v == "conf" else brk
    today["zones"] = _today_zones(snap, bars, float(day.get("tick") or 0.25), d, e_px, s["idrH"] - s["idrL"], act, today["slice"], formed, end)
    out.update(today=today, available=dict(conf=True, brk=bool(brk), scopes=list(SCOPES)), weekday=day["weekday"])
    return out
