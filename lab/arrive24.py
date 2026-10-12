"""DR Lab design 24 — «Отсюда до места» (PROFILE:ARRIVE-24): the verified Q1 mechanism on the working screen.

The question (Q1-PILOT-0.2; KADR-1.1 ed. 2 §5, Q:K-ARRIVE), asked on every closed M5 of today's confirmation family:
«after this cut, until the block end, of the family's sessions that at the same clock time stood where today stands and
had not yet been at the place L, how many reached L?», next to the status of the same place today.

- places L in {0, -1/2, -7/10} of today's scale u = d (p - e) / w (the IDR edge on the confirmation side, the middle of
  the IDR, the start of retirement): the three places of the A/D measurements, nothing else;
- the parent is the family of the screen as the operator has it: the weekday family by default, all weekdays on his
  explicit switch (D1 of the pilot is not chosen here: the screen's own switch picks the parent, «все подтверждённые
  сессии» stays on the stand on 8771);
- the computation is the pilot's verified engine (lab/q1/engine.py: Table.target_state, select, reasons) run on the
  family's own members — the same cases, paths and rules the A/D reconciliation proved (tests/arrive24.py checks the
  identity with engine.attempt on history days); nothing is re-implemented here;
- today is read only through its prefix (lab/now24.py::today_path cuts every candle after the cut); a place reached
  today, a hole in today's prefix, today's DR break and the block's end are facts of the prefix, never a share;
- n_match < 20: no number («мало сессий: n=…»), the set is never widened.

DR-LAB-SC-1.1: the response leaves through the contract gate (lab/contract.py::attach_arrive), which re-derives today's
state, every member's eligibility, position and label by the reference definitions and withholds a place that fails.
Only the ODR and RDR blocks are in the verified scope of Q1; ADR says so.
"""
from __future__ import annotations

import datetime as _dt

import numpy as np

import contract
import now24
import scene24
from q1 import engine as Q

VERSION = "DR-LAB-ARRIVE-24"
LEVELS = Q.LEVELS                       # {"0": (0, 1), "-1/2": (-1, 2), "-7/10": (-7, 10)}
ORDER = ("0", "-1/2", "-7/10")
BLOCKS = Q.BLOCKS                       # ("ODR", "RDR"): the verified scope
SUPPORT = Q.SUPPORT                     # 20
SCOPE_EST = {"weekday": "NODEPOS_WD", "all": "NODEPOS_ALL"}   # the pilot's names of the same parents
_TBL = {}


class _Keys:
    """The engine's Table asks its provider only for a case key; the family's member id is that key here."""
    kind = "family"

    @staticmethod
    def key(case):
        return case["id"]


def _weekday(date):
    return _dt.date.fromisoformat(date).weekday()


def _weekday_n(fam):
    wd = _weekday(fam["today"]["date"])
    return fam["N"] if fam["key"].get("scope", "weekday") == "weekday" else sum(1 for m in fam["members"] if _weekday(m["date"]) == wd)


def _case(m, side, win, formed):
    P = np.array([q if q is not None else [np.nan] * 3 for q in m["path"]], dtype=float)
    return dict(id=m["id"], date=m["date"], weekday=_weekday(m["date"]), side=side, win=win,
                a=(m["act"] - formed - 5) // 5, w=int(m["w"]), oppv=int(m["oppv"]), P=P)


def family_table(fam):
    """The engine's Table over the members of one confirmation family snapshot (cached by snapshot)."""
    sid = fam["snapshot_id"]
    t = _TBL.get(sid)
    if t is None:
        side = 1 if fam["key"]["direction"] == "long" else -1
        formed = fam["schedule"]["formed"]
        win = (fam["key"]["window"][0] - formed) // scene24.WINDOW
        cases = [_case(m, side, win, formed) for m in fam["members"]]
        t = Q.Table(fam["key"]["instrument"], fam["key"]["session"], cases, fam["grid"], _Keys)
        if len(_TBL) > 32: _TBL.clear()
        _TBL[sid] = t
    return t


def today_case(fam, bars, tick):
    """Today as one case of the same frame, read only through its prefix up to the slice."""
    today, grid, formed = fam["today"], fam["grid"], fam["schedule"]["formed"]
    d = today["side"]
    tk = lambda p: int(round(p / tick))
    e_px = today["idrH"] if d == 1 else today["idrL"]
    e = tk(e_px)
    oppv = d * (tk(today["drL"] if d == 1 else today["drH"]) - e)
    P = now24.today_path(bars, grid, tick, d, e_px, today["slice"])
    return dict(id="today", date=today["date"], weekday=_weekday(today["date"]), side=d,
                win=(today["window"] if today.get("window") is not None else 0), a=(today["c0"] - formed - 5) // 5,
                w=tk(today["idrH"]) - tk(today["idrL"]), oppv=int(oppv), P=P)


def arrive(inst, session, at=None, date=None, scope="weekday"):
    """The request of the block «Отсюда до места» (/api/d24/arrive)."""
    params = dict(instrument=inst, session=session, at=at, date=date, scope=scope)
    out, fam, bars, tick = _arrive(inst, session, at, date, scope)
    return contract.attach_arrive(out, fam, bars, tick, params)


def _arrive(inst, session, at=None, date=None, scope="weekday"):
    if scope not in scene24.SCOPES: raise ValueError("scope: weekday | all")
    head = dict(profile=VERSION, question="Q:K-ARRIVE", engine=Q.ENGINE, model=Q.MODEL[:12], scope=scope,
                estimator=SCOPE_EST[scope], levels=[dict(level=k, a=LEVELS[k][0], b=LEVELS[k][1]) for k in ORDER])
    if session not in BLOCKS:
        return dict(head, status="OUT_OF_SCOPE", message="ответ «отсюда» проверен на истории только для ODR и RDR"), None, [], 0.25
    fam = scene24.family(inst, session, at, date, "conf" + (":all" if scope == "all" else ""))
    # a family the gate withheld (its members could not be re-derived) comes back with another status: no answer either;
    # a withheld zone map leaves the members, and so this answer, intact
    if fam.get("status") != "ok" or "today" not in fam:
        return dict(head, status="NO_FAMILY", family_status=fam.get("status"), message=fam.get("message")), fam, [], 0.25
    day = scene24.day_view(inst, date)
    bars, tick = day["bars"], float(day.get("tick") or 0.25)
    today, grid, formed, end = fam["today"], fam["grid"], fam["schedule"]["formed"], fam["schedule"]["end"]
    cut = int(today["slice"])
    c = (cut - formed - 5) // 5
    head.update(family_id=fam["family_id"], snapshot_id=fam["snapshot_id"], N_parent=int(fam["N"]),
                cut=dict(cut=cut, cut_clock_et=Q.clk(cut), c=int(c), horizon_end=Q.clk(end),
                         on_ad_15min_grid=bool(c >= 0 and (c + 1) % Q.AD_STEP == 0)),
                # the A/D reconciliation covered every parent on targets whose weekday family has >= 40 sessions, at the
                # 15-minute cuts; the weekday family is the all-weekdays family's members of today's weekday
                evidence=dict(ad_target_domain=bool(_weekday_n(fam) >= Q.AD_MIN_FAMILY)))
    # today's state comes from the engine on today's prefix (block over, no M5 yet, a hole, the DR break — in this order)
    T1 = Q.Table(inst, session, [today_case(fam, bars, tick)], grid, _Keys)
    F = family_table(fam)
    par = np.arange(len(F.ids))
    places, block = [], None
    for name in ORDER:
        lv = LEVELS[name]
        st = T1.target_state(0, c, lv)
        rec = dict(level=name, a=lv[0], b=lv[1], state=dict(status=st["status"]) | ({"time": st["time"]} if "time" in st else {}))
        if st["status"] in ("NO_PREFIX", "PREFIX_UNKNOWN", "DR_BROKEN", "BLOCK_OVER"):
            block = block or dict(status=st["status"], time=st.get("time"))
            continue
        if st["status"] == "OPEN":
            rec["state"].update(close_v=st["close_v"], r_v=st["r_v"], w=st["w"])
            if not len(par):
                rec.update(counts=dict(N_parent=0, N_eligible=0, N_not_yet=0, n_match=0, yes=0, no=0, unknown=0, n_known=0),
                           publication="WITHHELD_FEW_SESSIONS", point=None, bounds=None, members=[])
            else:
                m = {k: v[:, 0] for k, v in F.select(par, np.array([c]), lv, [st["close_v"]], st["w"]).items()}
                match, reach, unk = m["match"], m["reach"], m["unk"]
                n, yes, unknown = int(match.sum()), int((match & reach).sum()), int((match & unk).sum())
                no = n - yes - unknown
                reason = F.reasons(m)
                rec.update(counts=dict(N_parent=int(len(par)), N_eligible=int(m["valid"].sum()), N_not_yet=int(m["notyet"].sum()),
                                       n_match=n, yes=yes, no=no, unknown=unknown, n_known=yes + no,
                                       excluded={r: int((reason == r).sum()) for r in Q.REASONS if r != "MATCH"}),
                           publication="WITHHELD_FEW_SESSIONS" if n < SUPPORT else "NO_KNOWN_OUTCOME" if yes + no == 0 else "PUBLISHED",
                           point=dict(num=yes, den=yes + no) if yes + no else None,
                           bounds=[dict(num=yes, den=n), dict(num=yes + unknown, den=n)] if n else None,
                           members=[[F.ids[j], "YES" if r_ else "UNKNOWN" if u_ else "NO"]
                                    for j, r_, u_ in zip(par[match], reach[match], unk[match])])
        places.append(rec)
    if block is not None and not places:
        return dict(head, **{k: v for k, v in block.items() if v is not None}), fam, bars, tick
    return dict(head, status="OK", today=dict(a_t=int(T1.a[0]), w=int(T1.w[0])), places=places), fam, bars, tick
