"""PROFILE:ARRIVE-24 — «Отсюда до места» on screen 24 (SC-1.1 §12.6; the verified Q1 mechanism of the pilot).

What is checked (offline, on the built session base):
- identity with the pilot: on random history scenes (NQ / ES / YM x ODR / RDR, several cuts, both family scopes) the
  answer of the screen (lab/arrive24.py, the family on screen as the parent) equals the pilot engine's attempt
  (lab/q1/engine.py::Table.attempt with NODEPOS_WD / NODEPOS_ALL) member by member — the pilot's reconciliation with
  A/D therefore carries over to the screen;
- the boundary: today's candles after the cut never change the answer (rewritten to reach every place, the payload is
  byte-identical);
- the gate: strict on every sampled state (no violation), and a tampered answer is withheld in its place only;
- the statuses: n < 20 publishes no number, a place reached today is a fact with its time, ADR is out of scope.

Run: python -B tests/arrive24.py   (ALL GOOD at the end)
"""
from __future__ import annotations

import copy
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lab"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import contract          # noqa: E402
import arrive24 as AR     # noqa: E402
import scene24            # noqa: E402
from q1 import engine as Q  # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print(("  ok   " if ok else "  FAIL ") + name + ("" if ok else f" — {detail}"))
    if not ok: FAILS.append(name)


def production(inst, block, at, date, scope):
    out, fam, bars, tick = AR._arrive(inst, block, at, date, scope)
    return out, fam, bars, tick


def scenes(n_dates=6, seed=20261012):
    rnd = random.Random(seed)
    for inst in Q.INSTRUMENTS:
        for block in Q.BLOCKS:
            tbl = Q.table(inst, block)
            rows = [i for i in range(len(tbl.ids)) if str(tbl.dates[i]) >= "2012-01-01"]
            for i in rnd.sample(rows, n_dates):
                cuts = tbl.open_cuts(i)
                if not cuts: continue
                for c in sorted(rnd.sample(cuts, min(3, len(cuts)))):
                    yield inst, block, tbl, i, c


def test_identity():
    print("identity with the pilot engine (member by member)")
    n_att = n_open = 0
    bad = []
    for inst, block, tbl, i, c in scenes():
        date, at = str(tbl.dates[i]), int(tbl.grid[c])
        for scope, est in (("weekday", "NODEPOS_WD"), ("all", "NODEPOS_ALL")):
            out, fam, _, _ = production(inst, block, at, date, scope)
            for lv in AR.ORDER:
                att = tbl.attempt(i, c, lv, est)
                n_att += 1
                st = att["state"]["status"]
                if out["status"] != "OK":
                    if out["status"] != st: bad.append((inst, block, date, c, scope, lv, "block status", out["status"], st))
                    continue
                P = next(p for p in out["places"] if p["level"] == lv)
                if P["state"]["status"] != st or P["state"].get("time") != att["state"].get("time"):
                    bad.append((inst, block, date, c, scope, lv, "state", P["state"], att["state"].get("status"))); continue
                if st != "OPEN": continue
                n_open += 1
                k, K = P["counts"], att["counts"]
                if {f: k[f] for f in K} != K: bad.append((inst, block, date, c, scope, lv, "counts", k, K)); continue
                if P["members"] != [[m["id"], m["label"]] for m in att["members"]]: bad.append((inst, block, date, c, scope, lv, "members")); continue
                if P["publication"] != att["estimate"]["publication"]: bad.append((inst, block, date, c, scope, lv, "publication"))
    check(f"screen = pilot on {n_att} attempts ({n_open} open places)", not bad and n_open > 50, bad[:3])


def _rewrite_future(day, cut, side, place_price):
    """Today's candles after the cut rewritten to run through every place (a wholly different future)."""
    d = copy.deepcopy(day)
    bars = []
    for b in d["bars"]:
        b = list(b)
        if int(b[0]) + 5 > cut:
            hi, lo = (place_price + 50, b[3]) if side == -1 else (b[2], place_price - 50)
            b[2], b[3] = max(b[2], hi), min(b[3], lo)
        bars.append(b)
    d["bars"] = bars
    return d


def test_boundary():
    print("the boundary: today's candles after the cut never enter")
    checked = 0
    for inst, block, tbl, i, c in list(scenes(n_dates=3, seed=7)):
        date, at = str(tbl.dates[i]), int(tbl.grid[c])
        out, fam, _, _ = production(inst, block, at, date, "all")
        if out["status"] != "OK": continue
        today = fam["today"]
        side = today["side"]
        e = today["idrH"] if side == 1 else today["idrL"]
        w = today["idrH"] - today["idrL"]
        far = e + side * (-0.7) * w
        real = scene24.day_view
        try:
            fake = _rewrite_future(real(inst, date), at, side, far)
            scene24.day_view = lambda inst_, date_=None, _f=fake: _f
            scene24._SNAP.clear(); AR._TBL.clear()
            out2, _, _, _ = production(inst, block, at, date, "all")
        finally:
            scene24.day_view = real
            scene24._SNAP.clear(); AR._TBL.clear()
        same = json.dumps(out, sort_keys=True) == json.dumps(out2, sort_keys=True)
        checked += 1
        if not same:
            check(f"{inst} {block} {date} cut {c}: the answer did not change with a rewritten future", False, "payload differs")
            return
    check(f"a rewritten future leaves the answer byte-identical ({checked} scenes)", checked >= 5)


def test_gate():
    print("the gate (lab/contract.py::attach_arrive)")
    contract.STRICT["on"] = True
    n = 0
    try:
        for inst, block, tbl, i, c in scenes(n_dates=4, seed=11):
            for scope in ("weekday", "all"):
                body = contract.finalize("/api/d24/arrive", AR.arrive(inst, block, int(tbl.grid[c]), str(tbl.dates[i]), scope))
                n += 1
                assert body["contract"]["status"] == "CONFORMANT", body["contract"]
                pub = [p for p in body.get("places", []) if p.get("publication") in ("PUBLISHED", "NO_KNOWN_OUTCOME")]
                assert len(body["contract"].get("bundles", [])) == len(pub), "one bundle per published place"
        check(f"strict gate on {n} states: conformant, one bundle per published place", n > 30)
    except Exception as exc:
        check("strict gate", False, repr(exc)[:300])
    finally:
        contract.STRICT["on"] = False
    out, fam, bars, tick = production("NQ", "RDR", 670, "2025-12-17", "all")
    t = copy.deepcopy(out)
    P = next(p for p in t["places"] if p["level"] == "-1/2")
    P["members"][0][1] = "NO" if P["members"][0][1] == "YES" else "YES"
    body = contract.attach_arrive(t, fam, bars, tick, {})
    held = {p["level"]: bool(p.get("withheld")) for p in body["places"]}
    check("a tampered label withholds that place only", held == {"0": False, "-1/2": True, "-7/10": False}
          and body["contract"]["status"] == "VIOLATION" and all(b["claim"]["claim_class"] == "ConditionalDescriptiveClaim" for b in body["contract"]["bundles"]), held)
    t = copy.deepcopy(out)
    t["N_parent"] += 1
    body = contract.attach_arrive(t, fam, bars, tick, {})
    check("another parent than the family on screen withholds the answer", body["status"] == "CONTRACT_VIOLATION" and not body["contract"].get("bundles"))


def test_statuses():
    print("statuses")
    out, _, _, _ = production("NQ", "RDR", 670, "2025-12-17", "weekday")
    few = [p for p in out["places"] if p["publication"] == "WITHHELD_FEW_SESSIONS"]
    body = contract.attach_arrive(*production("NQ", "RDR", 670, "2025-12-17", "weekday"), {})
    check("n < 20: no number (no bundle), the counts kept", len(few) == 3 and not body["contract"]["bundles"] and all(p["counts"]["n_match"] < 20 for p in few))
    out, _, _, _ = production("NQ", "ADR", 0, "2025-12-17", "weekday")
    check("ADR is outside the verified scope", out["status"] == "OUT_OF_SCOPE")
    # a place reached today: find one on the sampled scenes
    found = None
    for inst, block, tbl, i, c in scenes(n_dates=6, seed=3):
        o, _, _, _ = production(inst, block, int(tbl.grid[c]), str(tbl.dates[i]), "all")
        r = [p for p in o.get("places", []) if p["state"]["status"] == "RESOLVED"]
        if r: found = r[0]; break
    check("a place reached today is a fact with its time, no share", found is not None and "time" in found["state"] and "counts" not in found, found)


if __name__ == "__main__":
    Q.bind_corpus(ROOT / "lab" / ".runtime")
    test_identity()
    test_boundary()
    test_gate()
    test_statuses()
    print("ALL GOOD" if not FAILS else f"FAILED: {FAILS}")
    sys.exit(1 if FAILS else 0)
