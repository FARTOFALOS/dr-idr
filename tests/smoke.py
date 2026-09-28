"""Smoke checks for agents: run after every change, before telling the operator it works.

    python -B tests/smoke.py

Offline: needs lab/.runtime (built history) but neither TradingView nor a browser. Checks the invariants that must
never break (no 2026 in history, API shapes, finite JSON, live state incl. replay) and the syntax of the front end.
Exit code 0 = all good.
"""
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "lab"
sys.path.insert(0, str(LAB))
failures = []


def check(cond, msg):
    print(("  ok  " if cond else "  FAIL ") + msg)
    if not cond: failures.append(msg)


def finite_json(obj, where):
    try:
        json.dumps(obj, allow_nan=False)
        return True
    except ValueError:
        print("       non-finite number in", where)
        return False


import engine_market as H  # noqa: E402
H.initialize()
by_inst = {i: [e for e in H._E if e["instrument"] == i] for i in H.INSTRUMENTS}
check(all(len(v) > 10000 for v in by_inst.values()), "history loaded: " + ", ".join(f"{k} {len(v)}" for k, v in by_inst.items()))
check(max(e["date"] for e in H._E) <= "2025-12-31", "2026 stays hidden (latest episode " + max(e["date"] for e in H._E) + ")")
check(all(e["width"] > 0 for e in H._E), "every episode has a positive IDR width")

for inst in H.INSTRUMENTS:
    d = H.query(dict(instrument=inst, session="RDR", direction="long", **{"from": "630", "to": "660"}))
    keys = {"data_kind", "n", "true", "target", "charts", "heat", "curve", "scenes"}
    check(keys <= set(d) and d["n"] > 500 and finite_json(d, f"query {inst}"), f"history query {inst} RDR long 10:30-11:00: n={d['n']}, DR true {d['true']['pct']:.1f}%")
p = H.query(dict(instrument="NQ", session="RDR", direction="long", mode="prefix", observed="720", **{"from": "630", "to": "660"}))
check(p["n"] > 0 and finite_json(p, "prefix query"), f"prefix (at-the-moment) query: n={p['n']}")
s = H.scene(by_inst["NQ"][-1]["id"])
check(s is not None and len(s["bars"]) > 0, "scene endpoint returns bars")

import live  # noqa: E402
raw = (LAB / ".runtime" / "live" / "nq.json")
if raw.exists():
    for session in ("ADR", "ODR", "RDR"):
        st = live.state("NQ", session)
        check(st.get("status") in {"forming", "waiting", "confirmed", "no_session"} and finite_json(st, f"live {session}"), f"live state NQ {session}: {st.get('status')}")
    st = live.state("NQ", "RDR")
    if st.get("status") == "confirmed":
        o = st.get("overlay") or {}
        check(o.get("n", 0) >= 0 and "charts" in o or o.get("n") == 0, f"live overlay NQ RDR: n={o.get('n')}")
        at = st["confirmation"] + 30
        if at < st["end"]:
            r = live.state("NQ", "RDR", at)
            check(r.get("replay") == at and r.get("observed") == at and finite_json(r, "replay"), f"replay at {H.clock(at)}: status {r.get('status')}")
else:
    print("  --  no live candles saved yet (lab/.runtime/live/nq.json): live checks skipped")

import scene21  # noqa: E402
B = scene21._boxes("NQ")
if B is None:
    check(False, "session base built (python -B lab/build_boxes.py)")
else:
    check(max(b["date"] for b in B["boxes"]) <= "2025-12-31", "2026 stays hidden in the session base (latest " + max(b["date"] for b in B["boxes"]) + ")")
    confirmed = {(e["date"], e["session"]): (e["confirmation"], 1 if e["direction"] == "long" else -1) for e in by_inst["NQ"]}
    bad = sum(1 for b in B["boxes"] if b["conf"] and (b["date"], b["session"]) in confirmed and confirmed[(b["date"], b["session"])] != (b["conf"], b["side"]))
    check(bad == 0, f"session base agrees with the episodes on every confirmation (mismatches {bad})")
    if raw.exists():
        v = scene21.day_view("NQ")
        check(v.get("status") == "ok" and len(v["bars"]) > 0 and finite_json(v, "day view"), f"day view NQ {v.get('date')}: {len(v.get('bars', []))} bars")
        for session, at in (("RDR", 700), ("RDR", 635), ("ODR", 300)):
            c = scene21.cohort("NQ", session, at)
            ok = c.get("status") in ("ok", "before", "forming", "done", "noconf") and finite_json(c, f"cohort {session} {at}")
            if c.get("status") == "ok": ok = ok and c["n"] > 0 and len(c["sims"]["mx"]) == c["n"] and all(len(x) == len(c["grid"]) for x in c["sims"]["cl"])
            check(ok, f"cohort NQ {session} at {H.clock(at)}: {c.get('status')} {c.get('mode', '')} n={c.get('n')}")

node = shutil.which("node")
if node:
    for js in ("dist/app.js", "dist/live.js", "dist/sozvezdiya.js", "tv_fetch.mjs"):
        r = subprocess.run([node, "--check", str(LAB / js)], capture_output=True, text=True)
        check(r.returncode == 0, f"syntax {js}")
else:
    print("  --  node not found: front-end syntax not checked")

print()
print("ALL GOOD" if not failures else f"{len(failures)} FAILED")
sys.exit(1 if failures else 0)
