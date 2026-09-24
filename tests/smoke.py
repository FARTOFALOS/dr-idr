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

node = shutil.which("node")
if node:
    for js in ("dist/app.js", "dist/live.js", "tv_fetch.mjs"):
        r = subprocess.run([node, "--check", str(LAB / js)], capture_output=True, text=True)
        check(r.returncode == 0, f"syntax {js}")
else:
    print("  --  node not found: front-end syntax not checked")

print()
print("ALL GOOD" if not failures else f"{len(failures)} FAILED")
sys.exit(1 if failures else 0)
