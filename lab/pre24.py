"""DR Lab design 24 — PRE-24: the second screen before the confirmation (operator 2026-10-08, meaning/17 §7).

Before today's session confirms, three questions of the operator are answered from history: in which direction
similar sessions then confirmed, in which 15 minutes, and what happened after the confirmation on each side. Similar
sessions are selected by the operator's choice of 2026-10-08 — box colour, model of the day, price position in the box —
at the common clock cut t (the close of today's last closed M5; the same clock time ET of each session):

- the same instrument and block, the weekday of the trading date (all weekdays only on the operator's explicit switch,
  never a fallback), trading dates strictly before the viewed day (the session base ends 2025-12-31);
- alive at t: no confirmation closed by t, and every M5 after the box up to t present (a wholly missing M5 there leaves
  it undetermined: the journal, never a member);
- the same box colour (the close of the formation hour against its open: up / down / flat);
- the same state of the day's models at t (upside alive, downside alive; docs/STRATEGY.md §2.1-2.2, the rule of design
  22: scene21._models_today / _models_hist); a model that cannot be established (a box it needs is missing) is never
  read as alive: today — no answer, history — the journal;
- the price at t within 1/4 IDR of today's on the box scale u = (close - IDR low) / IDR width (design 22's band),
  exact in integers: 4 |a w_t - a_t w| <= w w_t. Nothing is widened (operator 2026-10-08 «ничего не расширять»): fewer
  than FEW sessions are shown as they are, with «мало сессий: n=…».

The outcome of a member after t (its whole session is history): the first M5 after t closing strictly beyond its own
DR — LONG / SHORT with its close minute and its 15-minute window (scene24.window_of, by the M5's open label); NONE (the
remainder up to the block end fully observed without one); UNKNOWN (a wholly missing M5 after t before the first
observed one). After a known confirmation: its own R, X and DR outcome by scene24.measure — the definitions of the
confirmation family, from its own confirmation (that M5 excluded) to the block end.

DR-LAB-SC-1.1: the response leaves through the contract gate (lab/contract.py::attach_pre), which re-derives the set
and every outcome from the session base by the reference definitions and withholds what fails.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter

import numpy as np

import contract
import scene21
import scene24

VERSION = "DR-LAB-PRE-24"
SESS, SHIFT, ORDER = scene21.SESS, scene21.SHIFT, scene21.ORDER
BAND = (1, 4)            # the price at t within 1/4 IDR of today's (design 22's first band), never widened
FEW = 20                 # fewer similar sessions: «мало сессий: n=…» (operator 2026-10-08)
SIDES = ("LONG", "SHORT")
FIRSTS = ("LONG", "SHORT", "NONE", "UNKNOWN")
DR_CATS = ("held", "broken", "unknown", "none")
_SNAP = {}


def _q(vals):
    """q25 / q50 / q75 among known values (numpy's linear quantile), four decimals; None without a value."""
    return [round(float(np.quantile(vals, q)), 4) for q in (0.25, 0.5, 0.75)] if vals else None


def models_today(bars, k, cut, prev_rdr):
    """scene21._models_today at the cut, with every box it needs established; (None, reason) otherwise. ADR needs the
    previous trading day's RDR; ODR the ADR box and the previous RDR; RDR the ODR and ADR boxes."""
    box = lambda kk: scene21._box([x for x in bars if SESS[kk][0] <= x[0] < SESS[kk][1]], SESS[kk][0], SESS[kk][1])
    need = {"ADR": [("предыдущего RDR", prev_rdr)], "ODR": [("ADR", box("ADR")), ("предыдущего RDR", prev_rdr)],
            "RDR": [("ODR", box("ODR")), ("ADR", box("ADR"))]}[k]
    for name, b in need:
        if b is None: return None, "модель дня не определена: нет коробки " + name
    return scene21._models_today(bars, k, cut, prev_rdr), None


def models_hist(B, i, k, cut_h, cache):
    """scene21._models_hist with both boxes it needs present in the base (the previous session's box and, for ODR and
    RDR, the box before it: scene21 reads a missing one as «not broken»); None otherwise."""
    date = B["boxes"][i]["date"]
    if k == "ODR" and (scene21._hist_box(B, date, "ADR") is None or scene21._hist_prev_rdr(B, date) is None): return None
    if k == "RDR" and (scene21._hist_box(B, date, "ODR") is None or scene21._hist_box(B, date, "ADR") is None): return None
    return scene21._models_hist(B, i, k, cut_h, cache)


def pre(inst, session, at=None, date=None, scope="weekday"):
    """The request of the block «До подтверждения» (/api/d24/pre)."""
    out, B, day = _pre(inst, session, at, date, scope)
    return contract.attach_pre(out, inst, B, day, dict(instrument=inst, session=session, at=at, date=date, scope=scope))


def _pre(inst, session, at=None, date=None, scope="weekday"):
    if inst not in scene21.live.SYMBOLS: raise ValueError("Unknown instrument")
    if session not in SESS: raise ValueError("Unknown session")
    if scope not in scene24.SCOPES: raise ValueError("scope: weekday | all")
    B = scene24._base(inst)
    if B is None: return dict(status="no_base", message="Нет базы сессий: python -B lab/build_boxes.py"), None, None
    day = scene24.day_view(inst, date)
    if day.get("status") != "ok": return dict(status=day.get("status", "no_data"), message=day.get("message")), B, day
    bars, now = day["bars"], day["now"]
    is_live = not date and at is None
    obs = int(np.floor(now)) if at is None else int(at)
    s = scene21._state(bars, session, obs, now, is_live)
    start, formed, end = SESS[session]
    cut = obs // 5 * 5
    today = dict(date=day["date"], source=day["source"], status=s["status"], obs=obs, slice=cut)
    if s["status"] != "waiting":
        return dict(status=s["status"], session=session, today=today), B, day
    tick = float(day.get("tick") or B["tick"])
    tk = lambda p: int(round(p / tick))
    closed = {int(b[0]) + 5: b for b in bars if int(b[0]) + 5 <= cut}
    today.update(box=s["box"], idrH=s["idrH"], idrL=s["idrL"], drH=s["drH"], drL=s["drL"])
    if any(T not in closed for T in range(formed + 5, cut + 1, 5)):
        return dict(status="prefix_unknown", session=session, today=today, message="нет свечи M5 после коробки до среза: состояние сегодня не установлено"), B, day
    models_t, why = models_today(bars, session, cut, day.get("prev"))
    if models_t is None:
        return dict(status="model_unknown", session=session, today=today, message=why), B, day
    L_t, w_t = tk(s["idrL"]), tk(s["idrH"]) - tk(s["idrL"])
    a_t = tk(closed[cut][4]) - L_t
    today.update(models=dict(up=bool(models_t[0]), down=bool(models_t[1])), pos=dict(a=a_t, w=w_t))
    src = scene24.source_version(inst, B)
    key = dict(instrument=inst, session=session, weekday=day["weekday"], scope=scope, cutoff=day["date"], cut=cut, box=s["box"],
               models=[bool(models_t[0]), bool(models_t[1])], pos=[a_t, w_t], band=list(BAND))
    ck = json.dumps([key, src["built"]], sort_keys=True)
    snap = _SNAP.get(ck)
    if snap is None:
        snap = _snapshot(inst, B, key, models_t, src)
        if len(_SNAP) > 64: _SNAP.clear()
        _SNAP[ck] = snap
    out = dict(snap)
    out.update(session=session, today=today, weekday=day["weekday"], available=dict(scopes=list(scene24.SCOPES)))
    return out, B, day


def _snapshot(inst, B, key, models_t, src):
    """The set of similar sessions at the cut and the outcome of every member after it (independent of the page)."""
    session, cut, scope, wd = key["session"], key["cut"], key["scope"], key["weekday"]
    start, formed, end = SESS[session]
    shift = SHIFT[session]
    a_t, w_t = key["pos"]
    miss = scene24._missing(inst, B, session)
    members, journal, mcache = [], Counter(), {}
    for i, m in enumerate(B["boxes"]):
        if m["session"] != session or (scope == "weekday" and m["weekday"] != wd) or m["date"] >= key["cutoff"]: continue
        gaps = miss.get(i, [])
        conf = None if m["conf"] is None else int(m["conf"]) - shift
        if conf is not None and conf <= cut: continue          # confirmed by t (there or earlier at a hole): not alive
        if any(T <= cut for T in gaps):                         # a hole up to t could have been a confirmation
            journal["alive_undetermined"] += 1
            continue
        if m["box"] != key["box"]: continue
        rows = scene24._rows(B, i, shift)
        L, w = m["idr_low"], m["idr_high"] - m["idr_low"]
        a = rows[cut][4] - L
        if BAND[1] * abs(a * w_t - a_t * w) > BAND[0] * w * w_t: continue
        mod = models_hist(B, i, session, cut + shift, mcache)
        if mod is None:                                         # a box the model needs is missing in the base
            journal["model_undetermined"] += 1
            continue
        if (bool(mod[0]), bool(mod[1])) != (bool(models_t[0]), bool(models_t[1])): continue
        if conf is None: first = "UNKNOWN" if any(T > cut for T in gaps) else "NONE"
        else: first = "UNKNOWN" if any(cut < T < conf for T in gaps) else ("LONG" if m["side"] == 1 else "SHORT")
        rec = dict(id=scene24._sid(inst, m), date=m["date"], w=int(w), a=int(a), first=first,
                   conf=conf if first in SIDES else None, win=scene24.window_of(conf, formed) if first in SIDES else None)
        if first in SIDES:
            d = 1 if first == "LONG" else -1
            e = m["idr_high"] if d == 1 else m["idr_low"]
            ev = scene24.measure(rows, conf, end, d, e, d * ((m["dr_low"] if d == 1 else m["dr_high"]) - e))
            rec.update(R=ev["R"], X=ev["X"], outcome=ev["outcome"])
        members.append(rec)
    members.sort(key=lambda r: r["date"])
    N = len(members)
    side = {}
    for sd in SIDES:
        M = [r for r in members if r["first"] == sd]
        rx = {}
        for ev in ("R", "X"):
            vals = [r[ev]["v"] / r["w"] for r in M if r[ev]["s"] == "known"]
            rx[ev] = dict(known=len(vals), unknown=sum(1 for r in M if r[ev]["s"] == "unknown"), none=sum(1 for r in M if r[ev]["s"] == "none"), q=_q(vals))
        side[sd] = dict(n=len(M), win=[[int(b), int(c)] for b, c in sorted(Counter(r["win"] for r in M).items())],
                        dr={k: sum(1 for r in M if r["outcome"] == k) for k in DR_CATS}, R=rx["R"], X=rx["X"])
    counts = dict(first={k: sum(1 for r in members if r["first"] == k) for k in FIRSTS}, side=side)
    ids = [r["id"] for r in members]
    family_id = hashlib.sha1(json.dumps([VERSION, key, ids], sort_keys=True).encode()).hexdigest()[:16]
    measured = [[r["id"], r["first"], r["conf"], r.get("R"), r.get("X"), r.get("outcome")] for r in members]
    snapshot_id = hashlib.sha1(json.dumps([family_id, src, measured], sort_keys=True).encode()).hexdigest()[:16]
    return dict(status="ok", profile=VERSION, source=src, key=key, family_id=family_id, snapshot_id=snapshot_id,
                schedule=dict(start=start, formed=formed, end=end), N=N, few=N < FEW, ids=ids, members=members,
                counts=counts, journal=dict(journal))
