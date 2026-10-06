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
        for session, at in (("RDR", 700), ("RDR", 800), ("ODR", 300), ("ODR", 400)):
            f = scene21.family("NQ", session, at)
            ok = f.get("status") in ("ok", "before", "forming", "waiting", "noconf", "done") and finite_json(f, f"family {session} {at}")
            if f.get("status") == "ok":
                ok = ok and f["mode"] in ("conf", "brk") and f["n"] == len(f["members"]) and f["window"][1] - f["window"][0] == 15
                ok = ok and all(len(m[k]) == len(f["grid"]) for m in f["members"] for k in ("lo", "hi", "cl"))
            check(ok, f"family NQ {session} at {H.clock(at)}: {f.get('status')} {f.get('mode', '')} n={f.get('n')}")
    # the family window: the TradingView label of the M5 (its open), one window per event (the author's rule, 2026-09-30)
    wo = scene21.window_of
    check([wo(c, 630) for c in (635, 645, 650, 660, 665)] == [0, 0, 1, 1, 2] and wo(245, 240) == 0 and wo(275, 240) == 2,
          "family window by the candle label: 10:40 -> 10:30-10:45, 10:55 (closed 11:00) -> 10:45-11:00, 04:30 -> 04:30-04:45")

    # design 24 (lab/scene24.py, DR-LAB-SEM-1.0): a history day opened as today, its families, one snapshot per day;
    # the full semantic checks are tests/sem24.py
    import scene24  # noqa: E402
    d24 = scene24.day_view("NQ", "2025-12-17")
    check(d24.get("status") == "ok" and len(d24["bars"]) > 100 and finite_json(d24, "d24 day"), f"design 24 history day: {len(d24.get('bars', []))} bars")
    for session, at in (("RDR", 700), ("ODR", 300), ("ADR", -150)):
        f = scene24.family("NQ", session, at, "2025-12-17")
        ok = f.get("status") in ("ok", "before", "forming", "waiting", "noconf") and finite_json(f, f"d24 family {session}")
        if f.get("status") == "ok":
            ok = ok and f["N"] == len(f["members"]) and all(m["date"] < "2025-12-17" for m in f["members"])
            for ev in ("R", "X"):
                cnt = f["counts"][ev]
                ok = ok and sum(n for _, _, n in cnt["cells"]) + cnt["unknown"] + cnt["none"] == f["N"]
        check(ok, f"design 24 family NQ {session} 2025-12-17 at {H.clock(at)}: {f.get('status')} {f.get('view', '')} N={f.get('N')}")
    # the layer «Сейчас» (lab/now24.py, DR-LAB-NOW-1.0): finite, its base N equals the family's, R and X both answered;
    # the full acceptance tests are tests/now24.py
    import now24  # noqa: E402
    nw = now24.live("NQ", "RDR", 720, "2025-12-17")
    fam = scene24.family("NQ", "RDR", 720, "2025-12-17")
    ok = finite_json(nw, "d24 now") and nw.get("status") in ("OK", "FROZEN_AT_BREAK", "NO_PREFIX", "UNKNOWN_PREFIX", "HORIZON_OVER", "NO_FAMILY")
    if nw.get("status") == "OK":
        ok = ok and nw["base"]["N_base"] == fam["N"] and all(nw[ev]["continuation"]["support"]["N_eligible"] <= fam["N"] for ev in ("R", "X"))
    check(ok, f"design 24 «Сейчас» NQ RDR 2025-12-17 12:00: {nw.get('status')} {nw.get('R', {}).get('mode', '')}")

node = shutil.which("node")
if node:
    for js in ("dist/app.js", "dist/live.js", "dist/sozvezdiya.js", "dist/24/d24.js", "tv_fetch.mjs"):
        r = subprocess.run([node, "--check", str(LAB / js)], capture_output=True, text=True)
        check(r.returncode == 0, f"syntax {js}")
else:
    print("  --  node not found: front-end syntax not checked")

print()
print("ALL GOOD" if not failures else f"{len(failures)} FAILED")
sys.exit(1 if failures else 0)
