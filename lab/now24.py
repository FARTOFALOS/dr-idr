"""DR Lab design 24 — the layer «Сейчас» (NOW): DR-LAB-NOW-1.0.

Specification: meaning/lens/2026-10-06-now-1.0/DR-LAB-NOW-1.0.md (closed by the operator on 06.10.2026); the decisions
taken while implementing it: meaning/15-sloj-seichas.md.

The base map of screen 24 (lab/scene24.py: the family F frozen at the activation, one N, every share count / N) is not
touched. NOW answers another question on every closed M5: after the path today has already lived, how much movement
usually remained ahead for the family's sessions that were in a comparable observable state at the same clock time?

Primary objects (spec §6), for R and mirrored for X, in the directed scale of the snapshot (u = v / w, integer ticks):
  new  = after the cut some M5 makes the extreme strictly further than the one already seen (a tie is not new);
  d    = the final extreme minus the one already seen (>= 0), in units of the IDR width;
  tau  = M5 after the cut until the first strictly further extreme (only where new = 1).
State at the cut (spec §5): the session's own post-activation M5 up to the common clock cut (the activating M5
excluded), complete (no wholly missing M5) and alive (a confirmation-family session that has already closed beyond its
own opposite DR is in another phase). Membership never uses anything after the cut (spec §22.7).
Models: B0 = every eligible session of the family at that clock time; M1 = |r - r_today| <= 0.25 (for R; x for X);
M2 = both; M3 = M2 and the last up to 6 closes after the activation within MAE 0.20 / max 0.35 (at least 3). All
distances exact in integers: |a/w - b/v| <= n/d  <=>  d |a v - b w| <= n w v.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

VERSION = "DR-LAB-NOW-1.0"
RULES = {"tol": [1, 4], "tol_sens": [[1, 5], [3, 10]], "m3_mae": [1, 5], "m3_max": [7, 20], "m3_min": 3, "m3_len": 6,
         "support": 20, "warmup": 40, "deltas": [[1, 10], [1, 5], [2, 5]], "coverage": 0.5, "boot": 2000, "unit": "iso-week",
         "cut": "common session clock", "activation_m5": "excluded", "tie": "not new"}
RULES_ID = hashlib.sha1(json.dumps([VERSION, RULES], sort_keys=True).encode()).hexdigest()[:12]
MODELS = ("B0", "M1", "M2", "M3")
RUNTIME = Path(__file__).resolve().parent / ".runtime"
VALIDATION = RUNTIME / "now24_validation.json"
_SER = {}
_VAL = {"mtime": None, "data": None}


# ---------- one session on the common clock ----------
def series(P, a, oppv=None):
    """Everything NOW needs of one session at every cut of its block's common clock.

    P: (L, 3) directed (low, high, close) ticks per common clock M5 (nan where the M5 is wholly absent); a: the grid
    index of the activating M5 (its own confirmation or break; excluded from the prefix); oppv: the directed opposite DR
    of a confirmation-family session (an M5 closing strictly below it ends the original phase), None for the break family.
    Returns int arrays of length L, valid only where valid[c] (a non-empty, complete, alive prefix (a, c])."""
    L = len(P)
    idx = np.arange(L)
    lo, hi, cl = P[:, 0], P[:, 1], P[:, 2]
    nan = np.isnan(lo)
    post = idx > a
    bad = np.logical_or.accumulate(post & nan)
    lo_i = np.where(nan, np.inf, lo)
    hi_i = np.where(nan, -np.inf, hi)
    r = np.minimum.accumulate(np.where(post, lo_i, np.inf))
    x = np.maximum.accumulate(np.where(post, hi_i, -np.inf))
    alive = np.ones(L, bool)
    if oppv is not None:
        alive = ~np.logical_or.accumulate(post & ~nan & (np.where(nan, 0, cl) < oppv))
    valid = post & ~bad & alive
    # the future of every cut c: the M5 k > c of the block
    fmin = np.append(np.minimum.accumulate(lo_i[::-1])[::-1][1:], np.inf)
    fmax = np.append(np.maximum.accumulate(hi_i[::-1])[::-1][1:], -np.inf)
    fnan = np.append(np.logical_or.accumulate(nan[::-1])[::-1][1:], False)
    newR = np.where(fmin < r, 1, np.where(fnan, -1, 0)).astype(np.int8)
    newX = np.where(fmax > x, 1, np.where(fnan, -1, 0)).astype(np.int8)
    # the final extremes of the whole horizon after the activation: known only when no M5 is missing there
    hor_known = not bad[-1] and post.any()
    rr = np.where(valid, r, 0).astype(np.int64)
    xx = np.where(valid, x, 0).astype(np.int64)
    dR = np.where(valid & hor_known, rr - (int(r[-1]) if hor_known else 0), -1).astype(np.int64)
    dX = np.where(valid & hor_known, (int(x[-1]) if hor_known else 0) - xx, -1).astype(np.int64)
    # the first M5 of the new extreme: known when no M5 is missing between the cut and it
    cn = np.cumsum(nan)

    def first(cmp):
        has = cmp.any(1)
        k = cmp.argmax(1)
        miss_between = (cn[np.maximum(k - 1, 0)] - cn) > 0
        return np.where(has & ~(miss_between & (k - 1 > idx)), k - idx, -1).astype(np.int16)
    later = idx[None, :] > idx[:, None]
    tauR = first((lo_i[None, :] < r[:, None]) & later)
    tauX = first((hi_i[None, :] > x[:, None]) & later)
    return dict(valid=valid, r=rr, x=xx, cl=np.where(valid, np.where(nan, 0, cl), 0).astype(np.int64),
                clr=np.where(nan, 0, cl).astype(np.int64), cnan=nan,
                newR=np.where(valid, newR, -2).astype(np.int8), newX=np.where(valid, newX, -2).astype(np.int8),
                dR=dR, dX=dX, tauR=np.where(valid, tauR, -1), tauX=np.where(valid, tauX, -1))


def stack(sers):
    keys = sers[0].keys() if sers else ()
    return {k: np.stack([s[k] for s in sers]) for k in keys}


# ---------- membership at the cuts (exact) ----------
def _near(a, wa, b, wb, tol):
    """|a / wa - b / wb| <= n / d, elementwise, in integers."""
    n, d = tol
    return d * np.abs(a * wb - b * wa) <= n * wa * wb


def masks(S, w, a_mem, T, w_t, a_t, cuts, tol=(1, 4)):
    """The member masks (J x C) of every model at the cuts. S: stacked series of the members, w: their widths, a_mem:
    their activation indices; T: today's series (or a target's), w_t, a_t; cuts: grid indices where today is valid."""
    cuts = np.asarray(cuts, dtype=int)
    V = S["valid"][:, cuts]
    W = w[:, None].astype(np.int64)
    rj, xj = S["r"][:, cuts], S["x"][:, cuts]
    ri, xi = T["r"][cuts][None, :], T["x"][cuts][None, :]
    m1R = V & _near(rj, W, ri, w_t, tol)
    m1X = V & _near(xj, W, xi, w_t, tol)
    m2 = m1R & m1X
    shape = np.zeros_like(V)
    n_max, n_min = RULES["m3_len"], RULES["m3_min"]
    (mn, md), (xn, xd) = RULES["m3_mae"], RULES["m3_max"]
    lim = W * w_t
    for ci, c in enumerate(cuts):
        n = min(n_max, c - a_t)
        if n < n_min: continue
        p0 = c - n + 1
        ok = a_mem < p0                                        # every compared close is after the member's activation
        dif = np.abs(S["clr"][:, p0:c + 1] * w_t - T["clr"][p0:c + 1][None, :] * W)
        shape[:, ci] = ok & (md * dif.sum(1) <= mn * n * lim[:, 0]) & (xd * dif.max(1) <= xn * lim[:, 0])
    return {"B0": V, "M1R": m1R, "M1X": m1X, "M2": m2, "M3": m2 & shape, "shape": shape}


def model_mask(Mk, model, ev):
    return Mk["B0"] if model == "B0" else Mk["M1" + ev] if model == "M1" else Mk[model]


# ---------- the forecast of one set at one cut ----------
def _q(a, qs=(0.25, 0.5, 0.75)):
    return [round(float(np.quantile(a, q)), 4) for q in qs] if len(a) else [None] * len(qs)


def forecast(S, w, mask_col, cut, ev):
    """The NOW numbers of one member set (a bool vector over the members) at one cut, for event ev."""
    new, d, tau = S["new" + ev][:, cut], S["d" + ev][:, cut], S["tau" + ev][:, cut]
    m = mask_col
    total, yes, unk = int(m.sum()), int((m & (new == 1)).sum()), int((m & (new == -1)).sum())
    known = total - unk
    dk = m & (d >= 0)
    dn = d[dk] / w[dk]
    dn_new = dn[dn > 0]
    tk = m & (new == 1) & (tau > 0)
    tt = tau[tk].astype(float)
    # SC-1.1 V2 / V2.2: the existence of a new extreme, its final magnitude and its first time have their own supports
    out = dict(support=dict(N_match_total=total, N_match_known=known, N_match_unknown=unk, N_delta_known=int(dk.sum()),
                            N_new_yes=yes, N_new_no=known - yes, N_delta_unknown=total - int(dk.sum())),
               p_new_extreme=round(yes / known, 4) if known else None,
               p_new_bounds=[round(yes / total, 4), round((yes + unk) / total, 4)] if total else [None, None])
    out["p_no_new_extreme"] = None if out["p_new_extreme"] is None else round(1 - out["p_new_extreme"], 4)
    q = _q(dn)
    qn = _q(dn_new)
    out["delta"] = dict(q25=q[0], q50=q[1], q75=q[2],
                        **{f"p_ge_0_{n * 100 // dd:02d}": (round(float(np.mean(10 * d[dk] * dd >= n * 10 * w[dk])), 4) if dk.any() else None)
                           for n, dd in RULES["deltas"]})
    out["delta_if_new"] = dict(q25=qn[0], q50=qn[1], q75=qn[2], n=int(len(dn_new)), n_unknown=int((m & (new == 1) & (d < 0)).sum()))
    qt = _q(tt)
    out["time_to_new"] = dict(q25_m5=qt[0], q50_m5=qt[1], q75_m5=qt[2],
                              q25_min=None if qt[0] is None else round(5 * qt[0], 1), q50_min=None if qt[1] is None else round(5 * qt[1], 1),
                              q75_min=None if qt[2] is None else round(5 * qt[2], 1), n=int(len(tt)),
                              n_unknown=int((m & (new == 1) & ~(tau > 0)).sum()), n_no_event=int((m & (new == 0)).sum()))
    return out


# ---------- the validation passport (written by lab/now24_validate.py) ----------
def validation():
    if not VALIDATION.exists(): return None
    mt = VALIDATION.stat().st_mtime
    if _VAL["mtime"] != mt:
        _VAL["data"] = json.loads(VALIDATION.read_text(encoding="utf-8"))
        _VAL["mtime"] = mt
    return _VAL["data"]


def decision(view, ev, inst, session, scope):
    """The product mode of one event (spec §12, §14.4, T10): the matcher the walk-forward promoted, or TIME_BASELINE."""
    V = validation()
    base = dict(status="NOT_VALIDATED", matcher=None, magnitude="B0", time="B0", tested_through=None, rules_id=RULES_ID)
    if scope != "weekday": return dict(base, status="NOT_VALIDATED_SCOPE", note="все дни недели: правила проверены только на семье дня недели")
    if V is None: return dict(base, note="проверка на истории ещё не прогнана")
    if V.get("rules_id") != RULES_ID: return dict(base, status="STALE", note="паспорт проверки от других правил")
    d = (V.get("decisions") or {}).get(f"{view}:{ev}")
    if not d: return dict(base, note="нет решения для этого события")
    out = dict(base, status=d["status"], matcher=d.get("matcher"), magnitude=d.get("magnitude", "B0"), time=d.get("time", "B0"),
               tested_through=V.get("tested_through"), brier_skill=d.get("brier_skill"), magnitude_skill=d.get("magnitude_skill"),
               time_skill=d.get("time_skill"))
    if f"{inst}:{session}" in (d.get("cells_fallback") or []):
        out.update(status="CELL_FALLBACK", note="в этой связке инструмент × сессия путь хуже базы: показана база по времени")
    return out


# ---------- the live payload ----------
def _member_series(snap):
    sid = snap["snapshot_id"]
    if sid in _SER: return _SER[sid]
    grid = snap["grid"]
    formed = snap["schedule"]["formed"]
    sers, w, a = [], [], []
    for m in snap["members"]:
        P = np.array([q if q is not None else [np.nan] * 3 for q in m["path"]], dtype=float)
        ai = (m["act"] - formed - 5) // 5
        sers.append(series(P, ai, m.get("oppv") if snap["view"] == "conf" else None))
        w.append(m["w"]); a.append(ai)
    out = (stack(sers) if sers else None, np.array(w, dtype=np.int64), np.array(a, dtype=np.int64))
    if len(_SER) > 32: _SER.clear()
    _SER[sid] = out
    return out


def today_path(bars, grid, tick, d, e_px, cut):
    """Today's directed (low, high, close) ticks on the snapshot's grid up to the cut only — a replayed history day
    has its later candles in the data, and they must never enter (spec §3.3, §22.7)."""
    tk = lambda p: int(round(p / tick))
    e = tk(e_px)
    have = {int(b[0]) + 5: b for b in bars}
    P = np.full((len(grid), 3), np.nan)
    for j, T in enumerate(grid):
        if T > cut: break
        b = have.get(T)
        if b is None: continue
        h, l, c = tk(b[2]), tk(b[3]), tk(b[4])
        P[j] = (l - e, h - e, c - e) if d == 1 else (e - h, e - l, e - c)
    return P


def payload(fam, bars, tick, debug=False):
    """NOW of a family response of lab/scene24.py (the snapshot and today's state) at its slice."""
    today, view = fam["today"], fam["view"]
    grid, formed, end = fam["grid"], fam["schedule"]["formed"], fam["schedule"]["end"]
    key = fam["key"]
    side = today["side"]
    d = side if view == "conf" else -side
    act = today["c0"] if view == "conf" else today["brk"]
    w_px = today["idrH"] - today["idrL"]
    e_px = today["idrH"] if d == 1 else today["idrL"]
    cut, status = today["slice"], "OK"
    # spec §18: the original family's NOW freezes at the last cut before the break; the break family has its own
    if view == "conf" and today.get("brk") is not None and cut >= today["brk"]:
        cut, status = today["brk"] - 5, "FROZEN_AT_BREAK"
    head = dict(now_version=VERSION, rules_id=RULES_ID, status=status, view=view,
                cut=dict(cut_clock_et=_clk(cut), cut=cut, family_id=fam["family_id"], snapshot_id=fam["snapshot_id"]),
                base=dict(N_base=fam["N"]))
    if cut > end:
        cut, head["status"] = end, "HORIZON_OVER"
    c = (cut - formed - 5) // 5
    a_t = (act - formed - 5) // 5
    if c <= a_t:
        return dict(head, status="NO_PREFIX", note="после " + ("подтверждения" if view == "conf" else "слома") + " ещё не закрылась ни одна M5")
    if c >= len(grid) - 1:
        return dict(head, status="HORIZON_OVER", note="блок закончен: впереди нет M5")
    w_t = int(round(w_px / tick))
    P = today_path(bars, grid, tick, d, e_px, cut)
    T = series(P, a_t, None)
    if not T["valid"][c]:
        return dict(head, status="UNKNOWN_PREFIX", note="в сегодняшнем пути после активации нет целой M5: состояние не определено")
    S, w, a_mem = _member_series(fam)
    head["cut"].update(today_elapsed_m5=int(c - a_t))
    if S is None:
        return dict(head, status="EMPTY_FAMILY")
    Mk = masks(S, w, a_mem, T, w_t, a_t, [c], tuple(RULES["tol"]))
    out = dict(head)
    for ev in ("R", "X"):
        dec = decision(view, ev, key["instrument"], key["session"], key.get("scope", "weekday"))
        b0 = forecast(S, w, Mk["B0"][:, 0], c, ev)
        res = {m: forecast(S, w, model_mask(Mk, m, ev)[:, 0], c, ev) for m in ("M1", "M2", "M3")}
        state = dict(r_seen=round(int(T["r"][c]) / w_t, 6), x_seen=round(int(T["x"][c]) / w_t, 6), last_close=round(int(T["cl"][c]) / w_t, 6))
        # implementation decision 12 (meaning/15): the time baseline too publishes no number on fewer than 20 eligible
        # sessions (a break family may hold one) — the spirit of §11, no false precision; the counts stay in research
        if b0["support"]["N_match_total"] < RULES["support"]:
            out[ev] = dict(mode="INSUFFICIENT_SUPPORT", matcher=None, state=state, continuation=None, baseline=b0, validation=dec,
                           note="мало сессий семьи для «Сейчас»: n=" + str(b0["support"]["N_match_total"]), research=res)
            continue
        m = dec.get("matcher")
        path_ok = dec["status"] == "VALIDATED" and m in res
        sup = res[m]["support"]["N_match_total"] if path_ok else 0
        if path_ok and sup >= RULES["support"]:
            main, mode, note = dict(res[m]), "PATH_CONDITIONED", None
            # spec §14.2-14.3: the remaining movement and the time from the path only if they passed their own gates
            if dec.get("magnitude") != "PATH":
                main["delta"], main["delta_if_new"], main["delta_source"] = b0["delta"], b0["delta_if_new"], "B0"
            if dec.get("time") != "PATH":
                main["time_to_new"], main["time_source"] = b0["time_to_new"], "B0"
        else:
            main, mode = dict(b0), "TIME_BASELINE"
            note = ("похожих слишком мало: n=" + str(sup) + "; показана база по времени") if path_ok else None
        main["support"] = dict(main["support"], N_eligible=b0["support"]["N_match_total"])
        out[ev] = dict(mode=mode, matcher=m if mode == "PATH_CONDITIONED" else None, note=note, state=state,
                       continuation=main, baseline=b0, validation=dec,
                       research=res if (debug or mode != "PATH_CONDITIONED") else None)
    return out


def _clk(t):
    t = int(t) % 1440
    return f"{t // 60:02d}:{t % 60:02d}"


def live(inst, session, at=None, date=None, view="auto", debug=False):
    """The request of the page: the family of lab/scene24.py and its NOW at the slice. The payload leaves through the
    contract gate (lab/contract.py::attach_now): its numbers are re-derived at the cut by the reference definitions,
    an event block that fails is withheld, and every published number carries its C1 claim."""
    import contract
    import scene24
    params = dict(instrument=inst, session=session, at=at, date=date, view=view)
    fam = scene24.family(inst, session, at, date, view)
    if fam.get("status") != "ok" or "today" not in fam or not fam.get("N"):
        out = dict(now_version=VERSION, status="NO_FAMILY", message=fam.get("message") or ("в семье нет сессий" if fam.get("status") == "ok" else None))
        return contract.attach_now(out, fam, [], 0.25, params)
    day = scene24.day_view(inst, date)
    tick = float(day.get("tick") or 0.25)
    return contract.attach_now(payload(fam, day["bars"], tick, debug), fam, day["bars"], tick, params)
