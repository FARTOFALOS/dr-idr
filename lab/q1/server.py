"""The isolated review scene of the Q1 pilot: a local server on 127.0.0.1:8771 (standard library only).

    python -B lab/q1/server.py [--port 8771]      (the shortcut «DR Lab Q1» runs start-q1-pilot.cmd)

Separate from the working DR Lab server (127.0.0.1:8767): its own process, port, routes and store; the working routes,
their contract registry and screen 24 are untouched. Every API response is marked X-DR-Lab-Contract with the pilot's
own passport (lab/q1/passport.py), never as a profile of the accepted SC-1.1 gate.

Routes (GET unless noted):
  /                     the page (lab/q1/web)
  /api/q1/meta          the passport, the estimators, the levels, the corpus, the store
  /api/q1/dates         the target sessions of an instrument x block (dates with an established confirmation)
  /api/q1/scene         one target at one cut: candles up to the cut only, levels, today's state, the answer of an estimator
  /api/q1/population    the whole parent of an estimator at the cut, one reason per session (on demand)
  /api/q1/case          one analogue's path in its own frame (on demand)
  /api/q1/issues        stored issues (optionally of one target)
  /api/q1/issue         one stored issue as written, its integrity and its outcomes
  POST /api/q1/issue    compute an attempt from the target's prefix and write it once
  POST /api/q1/reproduce  recompute a stored issue on its original inputs and compare the bytes
  POST /api/q1/outcome  attach the observed outcome to a stored issue (a separate record)
  /api/q1/outcome       an issue's outcome records and the target's candles after the cut (only once attached)
  /api/q1/verify        every record's hash, identity and link
  /api/q1/recon         the summary of the last A/D reconciliation run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB))
from q1 import engine as E  # noqa: E402
from q1 import passport  # noqa: E402
from q1.store import Collision, Store, sha  # noqa: E402

WEB = Path(__file__).resolve().parent / "web"
RUNTIME = LAB / ".q1-pilot"
STORE = Store(Path(os.environ.get("Q1_STORE", RUNTIME / "store")))
_LOCK = threading.Lock()


def tbl(inst, block):
    with _LOCK:                                   # build a table once, even if two requests arrive together
        return E.table(inst, block)


def u_price(T, i, a, b):
    """The physical price of a place u = a / b on the target's own frame (for drawing only, rounded to the tick)."""
    fr = T.provider.frame(T.keys[i], int(T.side[i]))
    v = fr["e"] + int(T.side[i]) * fr["w"] * a / b
    return round(round(v) * fr["tick"], 6), v * fr["tick"]


def target_info(T, i):
    k = T.keys[i]
    b = T.provider.box(k)
    tick = T.provider.tick
    return dict(id=T.ids[i], date=str(T.dates[i]), weekday=int(T.weekday[i]), side=int(T.side[i]), block=T.block,
                instrument=T.inst, activation_close=E.clk(T.grid[T.a[i]]), window=int(T.win[i]), tick=tick,
                box=dict(drH=b["dr_high"] * tick, drL=b["dr_low"] * tick, idrH=b["idr_high"] * tick, idrL=b["idr_low"] * tick),
                start=E.scene24.SESS[T.block][0], formed=T.formed, end=T.end, w=int(T.w[i]))


def answer_view(att):
    """What the page shows of one attempt: the state, and if open the counts, the estimate and the members."""
    out = dict(estimator=att["estimator"], state=att["state"])
    if att["state"]["status"] == "OPEN":
        out.update(counts=att["counts"], estimate=att["estimate"], members=att["members"])
    return out


def scene(q):
    T = tbl(q["inst"], q["block"])
    i = T.row(q["date"])
    cuts = T.open_cuts(i)
    c = int(q.get("cut") or min(cuts[-1], int(T.a[i]) + 6)) if cuts else None
    level = q.get("level") or "-1/2"
    info = target_info(T, i)
    out = dict(target=info, cuts=[dict(index=k, close=E.clk(T.grid[k])) for k in cuts], cut=c, level=level,
               levels={nm: dict(a=a, b=b, price=u_price(T, i, a, b)[0], exact=u_price(T, i, a, b)[1]) for nm, (a, b) in E.LEVELS.items()},
               candles=T.provider.physical(T.keys[i], upto=T.grid[c] if c is not None else T.formed))
    if c is None:
        return dict(out, state=dict(status="NO_PREFIX"))
    st = T.target_state(i, c, E.LEVELS[level])
    out["state"] = st
    tgt = T.target_record(i, level)
    out["target_id"] = E.target_id(tgt)
    out["saved"] = [issue_summary(r) for r in STORE.issues(out["target_id"])]
    if st["status"] == "OPEN":
        out["answers"] = {est: answer_view(T.attempt(i, c, level, est)) for est in E.ESTIMATORS}
    return out


def issue_summary(r):
    pl, m = r["payload"], r["meta"]
    return dict(issue_id=pl["issue_id"], target_id=pl["target_id"], date=pl["target"]["date"], instrument=pl["target"]["instrument"],
                block=pl["target"]["block"], level=pl["target"]["level"]["name"], cut=pl["cut"], estimator=pl["estimator"]["id"],
                publication=pl["estimate"]["publication"], counts=pl["counts"], estimate=pl["estimate"], created_utc=m.get("created_utc"),
                payload_sha256=m.get("payload_sha256"), outcomes=len(STORE.outcomes(issue_id_=pl["issue_id"])))


def population(q):
    T = tbl(q["inst"], q["block"])
    i = T.row(q["date"])
    att = T.attempt(i, int(q["cut"]), q["level"], q["est"])
    if att["state"]["status"] != "OPEN":
        return dict(state=att["state"])
    c, w_t = att["cut"], att["state"]["w"]
    rows = []
    for r_, j in enumerate(att["par"]):
        rs = str(att["reason"][r_])
        eligible = bool(att["mask"]["valid"][r_])
        rows.append(dict(id=T.ids[j], date=str(T.dates[j]), side=int(T.side[j]), window=int(T.win[j]), weekday=int(T.weekday[j]),
                         activation_close=E.clk(T.grid[T.a[j]]), reason=rs,
                         close_u=round(int(T.CL[j, c]) / int(T.w[j]), 4) if eligible else None,
                         r_u=round(int(T.R[j, c]) / int(T.w[j]), 4) if eligible else None))
    return dict(state=att["state"], counts=att["counts"], rows=rows, today_close_u=round(att["state"]["close_v"] / w_t, 4))


def case_path(q):
    T = tbl(q["inst"], q["block"])
    j = T.pos[q["id"]]
    c = int(q["cut"])
    la, lb = E.LEVELS[q["level"]]
    w = int(T.w[j])
    P = T.P[j]
    pts = [None if P[k][0] != P[k][0] else [round(P[k][0] / w, 4), round(P[k][1] / w, 4), round(P[k][2] / w, 4)] for k in range(len(P))]
    fr = T.first_reach(j, c, (la, lb))
    return dict(id=T.ids[j], date=str(T.dates[j]), side=int(T.side[j]), activation=int(T.a[j]), activation_close=E.clk(T.grid[T.a[j]]),
                grid=[E.clk(t) for t in T.grid], path=pts, cut=c, level=la / lb,
                first_reach=None if fr is None else dict(index=fr[0], close=E.clk(T.grid[fr[0]]), time_known=fr[1]))


def make_issue(body):
    T = tbl(body["inst"], body["block"])
    i = T.row(body["date"])
    status, att, rec = E.issue(STORE, T, i, int(body["cut"]), body["level"], body["est"])
    if status is None:
        return dict(status="NOT_OPEN", state=att["state"])
    return dict(status=status, summary=issue_summary(rec), file=str(STORE.root / "issues" / f"{rec['payload']['issue_id']}.json"))


def get_issue(q):
    rec = STORE.get_issue(q["id"])
    if rec is None:
        return dict(status="NOT_FOUND")
    ok = sha(rec["payload"]) == rec["meta"]["payload_sha256"]
    outs = sorted(STORE.outcomes(issue_id_=q["id"]), key=lambda r: r["payload"]["revision"])
    return dict(status="OK", integrity=ok, record=rec, outcomes=outs, file=str(STORE.root / "issues" / f"{q['id']}.json"))


def outcome_view(rid, attach):
    rec = STORE.get_issue(rid)
    if rec is None:
        return dict(status="NOT_FOUND")
    pl = rec["payload"]
    T = tbl(pl["target"]["instrument"], pl["target"]["block"])
    out = dict(status="NONE")
    if attach:
        st, r2 = E.attach_outcome(STORE, T, rid)
        out = dict(status=st, check=r2["check"] if st == "REFUSED" else r2["payload"]["check"])
    outs = sorted(STORE.outcomes(issue_id_=rid), key=lambda r: r["payload"]["revision"])
    out["outcomes"] = outs
    if outs:                                     # the target's later candles exist for the page only once an outcome is on record
        i = T.row(pl["target"]["date"])
        cut_min = T.grid[pl["cut"]["index"]]
        out["after"] = [r for r in T.provider.physical(T.keys[i]) if r[0] + 5 > cut_min]
    return out


def recon():
    p = RUNTIME / "recon" / "recon_summary.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else dict(status="NOT_RUN")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(WEB), **kw)

    def end_headers(self):
        if not self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, fmt, *args):
        if len(args) > 1 and str(args[1]) not in ("200", "304"):
            super().log_message(fmt, *args)

    def json(self, value, status=200):
        data = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-DR-Lab-Contract", passport.HEADER)
        self.end_headers()
        self.wfile.write(data)

    def _q(self):
        return {k: v[-1] for k, v in parse_qs(urlparse(self.path).query).items()}

    def do_GET(self):
        path = urlparse(self.path).path
        q = self._q()
        try:
            if path == "/api/q1/meta":
                return self.json(dict(passport.catalog(), model=E.MODEL, engine=E.ENGINE, question=E.QUESTION, corpus=str(E.CORPUS["path"]),
                                      store=str(STORE.root), instruments=E.INSTRUMENTS, blocks=E.BLOCKS, order=E.ESTIMATORS,
                                      code=E.code_version()))
            if path == "/api/q1/dates":
                T = tbl(q["inst"], q["block"])
                return self.json(dict(dates=[[str(T.dates[j]), E.clk(T.grid[T.a[j]]), int(T.side[j])] for j in range(len(T.ids))]))
            if path == "/api/q1/scene":
                return self.json(scene(q))
            if path == "/api/q1/population":
                return self.json(population(q))
            if path == "/api/q1/case":
                return self.json(case_path(q))
            if path == "/api/q1/issues":
                return self.json(dict(issues=[issue_summary(r) for r in STORE.issues(q.get("target_id"))]))
            if path == "/api/q1/issue":
                return self.json(get_issue(q))
            if path == "/api/q1/outcome":
                return self.json(outcome_view(q["id"], attach=False))
            if path == "/api/q1/verify":
                return self.json(STORE.verify())
            if path == "/api/q1/recon":
                return self.json(recon())
            if path.startswith("/api/"):
                return self.json(dict(error="unknown route"), 404)
            return super().do_GET()
        except Exception as exc:                  # a scene that cannot be computed says why; the server keeps running
            return self.json(dict(status="ERROR", error=f"{type(exc).__name__}: {exc}"), 500)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
            if path == "/api/q1/issue":
                return self.json(make_issue(body))
            if path == "/api/q1/reproduce":
                rec = STORE.get_issue(body["id"])
                if rec is None:
                    return self.json(dict(status="NOT_FOUND"))
                pl = rec["payload"]
                return self.json(E.reproduce(STORE, tbl(pl["target"]["instrument"], pl["target"]["block"]), body["id"]))
            if path == "/api/q1/outcome":
                return self.json(outcome_view(body["id"], attach=True))
            return self.json(dict(error="unknown route"), 404)
        except Collision as exc:
            return self.json(dict(status="COLLISION", error=str(exc)), 409)
        except Exception as exc:
            return self.json(dict(status="ERROR", error=f"{type(exc).__name__}: {exc}"), 500)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("Q1_PORT", 8771)))
    args = ap.parse_args()
    E.bind_corpus()
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Q1 pilot: http://127.0.0.1:{args.port}/  corpus {E.CORPUS['path']}  store {STORE.root}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
