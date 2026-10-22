"""DR-LAB-PB-0.1 «Откаты перед обновлением экстремума»: the meaning checks of the construction (its §5 table), the three
refinements of its review, real families re-derived by the independent reference, and deliberate faults.

    python -B tests/pullbacks24.py

Synthetic paths are written as directed M5 bars (open, high, low, close) in ticks; index 0 is the box's last candle
(the left context), the trading window starts at index 1 unless said otherwise. No market data is written.
"""
from pathlib import Path
import copy
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lab"))
import contract as C            # noqa: E402
import integration24 as I       # noqa: E402
import pullbacks24 as P         # noqa: E402
import pullbacks_ref as R       # noqa: E402

DONE = []


def check(ok, name):
    if not ok: raise AssertionError(name)
    DONE.append(name)
    print("PASS " + name, flush=True)


def run(bars, first=1, act=0, oppv=None, kmax=6):
    """The implementation and the reference on one path; they must agree before anything is read."""
    eps, pts = P.analyse(bars, first, act, oppv, kmax)
    ref = R.episodes_of([list(b) if b else None for b in bars], first, act, oppv, kmax)
    keys = ("a", "b", "h", "kt", "kn", "status")
    assert [tuple(e[k] for k in keys) for e in eps] == [tuple(r[k] for k in keys) for r in ref], (eps, ref)
    for e, r in zip(eps, ref):
        if e["status"] == "KNOWN": assert (e["jl"], e["L"], e["jb"], e.get("dr")) == (r["jl"], r["L"], r["jb"], r.get("dr")), (e, r)
    return eps, pts


def known(eps):
    return [(e["a"], e["h"], e["jl"], e["L"], e["jb"]) for e in eps if e["status"] == "KNOWN"]


BOX = (100, 105, 99, 104)


def stories():
    # 1. after 110 -> 103 -> 112 the price falls to 99: the completed pullback stays 103
    eps, pts = run([BOX, (104, 110, 104, 109), (109, 109, 103, 104), (104, 112, 104, 111), (111, 111, 99, 100)])
    check(known(eps) == [(1, 110, 2, 103, 3)] and [(p["i"], p["v"]) for p in pts] == [(2, 103)],
          "1: 110 -> 103 -> 112, then a fall to 99: the point stays 103 (a later fall does not move a completed episode)")
    # 2. 110 -> 103 -> 108, then the block ends: no completed episode before the update of 110
    eps, pts = run([BOX, (104, 110, 104, 109), (109, 109, 103, 104), (104, 108, 104, 107), (107, 107, 105, 106)])
    check(not known(eps) and [e["status"] for e in eps] == ["NO_UPDATE"], "2: 110 -> 103 -> 108, block end: «обновления до конца блока не было», no point")
    # 3. two completed pullbacks 103 and 108: both kept
    eps, pts = run([BOX, (104, 110, 104, 109), (109, 109, 103, 104), (104, 111, 104, 111), (111, 112, 110, 111), (111, 111, 108, 109),
                    (109, 115, 109, 114), (114, 114, 110, 111)])
    check(sorted((p["i"], p["v"]) for p in pts) == [(2, 103), (5, 108)], "3: 110 -> 103 -> 112 -> 108 -> 115: both points 103 and 108 are kept")
    # 4. the day's high 120 earlier, later locally 110 -> 104 -> 112: the pullback 104 counts
    eps, pts = run([BOX, (104, 120, 104, 119), (119, 119, 105, 106), (106, 107, 102, 103), (106, 110, 106, 109), (109, 109, 104, 105),
                    (105, 112, 105, 111), (111, 111, 107, 108)])
    check((4, 110, 5, 104, 6) in known(eps) and [e["status"] for e in eps if e["h"] == 120] == ["NO_UPDATE"],
          "4: a local cycle under the day's higher high 120 is counted (110 -> 104 -> 112)")
    # 5. one bottom precedes the updates of several vertices: one point, several links
    eps, pts = run([BOX, (110, 115, 110, 114), (114, 114, 108, 109), (109, 109, 107, 108), (108, 111, 108, 110), (110, 110, 103, 104),
                    (104, 116, 104, 115), (115, 115, 112, 113)])
    check(known(eps) == [(1, 115, 5, 103, 6), (4, 111, 5, 103, 6)] and len(pts) == 1 and len(pts[0]["links"]) == 2,
          "5: 115 -> 107 -> 111 -> 103 -> 116: one point 103 with two links (not two stars)")
    eps, pts = run([BOX, (110, 115, 110, 114), (114, 114, 108, 109), (109, 109, 107, 108),
                    (108, 111, 108, 110), (110, 110, 94, 96), (96, 112, 96, 111),
                    (111, 111, 94, 94), (96, 116, 96, 115), (115, 115, 112, 113)], oppv=95)
    links = [eps[i] for p in pts if (p["i"], p["v"]) == (5, 94) for i in p["links"]]
    check({(e["h"], e["jb"], e["dr"]) for e in links} == {(111, 6, "INTACT_AT_B"), (115, 8, "BETWEEN_L_B")},
          "5b: one bottom, two updates with a DR break between them: the order belongs to each episode, not the merged star")
    # 7. the order inside the vertex M5 decides whether its low comes after its high: no point is invented
    eps, pts = run([BOX, (104, 110, 100, 108), (108, 109, 103, 104), (104, 112, 104, 111)])
    check([e["status"] for e in eps][:1] == ["UNKNOWN_INTRABAR"] and not pts, "7a: the vertex M5 may hold the deepest point after its high: unknown, no point")
    eps, pts = run([BOX, (110, 110, 104, 109), (109, 109, 103, 104), (106, 112, 101, 111)])
    check(eps[0]["status"] == "UNKNOWN_INTRABAR" and not pts, "7b: the update M5 may dip below before or after it exceeds: unknown, no point")
    eps, pts = run([BOX, (110, 110, 100, 108), (108, 109, 103, 104), (104, 112, 104, 111)])
    check(known(eps) == [(1, 110, 1, 100, 3)], "7c: a vertex M5 that opens at its high: its low is after the high, the bottom is established in it")
    # 9. a missing M5 after a completed episode keeps it; a missing M5 between H and B leaves it unknown
    eps, pts = run([BOX, (104, 110, 104, 109), (109, 109, 103, 104), (104, 112, 104, 111), None, (111, 111, 99, 100)])
    check(known(eps) == [(1, 110, 2, 103, 3)], "9a: a missing M5 after B does not cancel the established episode")
    eps, pts = run([BOX, (104, 110, 104, 109), (109, 109, 103, 104), None, (104, 112, 104, 111)])
    check(eps[0]["status"] == "UNKNOWN_GAP" and not pts, "9b: a missing M5 between H and B: the episode is unknown, not absent")
    # review of PR #19 (Codex, 21.10): a gap after the observed bottom opens before it only that bottom, not every
    # earlier cell at or below it; from the gap on the session's missing-M5 columns hold the rest
    bars = [BOX, (104, 110, 104, 109), (109, 109, 103, 104), (104, 108, 105, 107), None, (107, 112, 106, 111)]
    eps, pts = run(bars)
    w, grid = 40, list(range(5, 5 * len(bars) + 1, 5))
    check(eps[0]["status"] == "UNKNOWN_GAP" and eps[0]["cand"] == [[2, 103, 103]]
          and R.seen_cells([list(b) if b else None for b in bars], 1, 110, 4, 0, w, 0, grid) == {((10 * 103) // w, 0)},
          "9c: before a missing M5 only the observed first deepest point is possible (implementation = reference)")
    # the bottom must lie after the own activation; a deeper point at or before it is never trimmed away
    bars = [BOX, (104, 110, 104, 109), (109, 109, 100, 101), (101, 106, 102, 105), (105, 112, 105, 111)]
    eps, _ = run(bars, act=2)
    check(eps[0]["status"] == "PRE_ACTIVATION", "the deepest point before the activation excludes the episode (no trimming to a later, shallower low)")
    eps, _ = run(bars, act=1)
    check(eps[0]["status"] == "KNOWN" and eps[0]["jl"] == 2, "the vertex may precede the activation when the bottom lies after it")
    # equality does not update; a gap above does
    eps, _ = run([BOX, (104, 110, 104, 109), (109, 109, 103, 104), (104, 110, 104, 109), (109, 109, 105, 106), (115, 116, 115, 116)])
    check(known(eps) == [(1, 110, 2, 103, 5)], "a repeat of the vertex price does not complete; the first strict exceedance does, a gap above included")
    # a plateau of equal highs is one vertex; a repeated equal vertex after a separate dip starts its own nested episode
    eps, _ = run([BOX, (104, 110, 104, 109), (109, 110, 105, 106), (106, 107, 103, 104), (104, 110, 104, 109), (109, 109, 101, 102),
                  (102, 112, 102, 111)])
    check([(e["a"], e["b"]) for e in eps if e["h"] == 110] == [(1, 2), (4, 4)] and known(eps) == [(1, 110, 5, 101, 6), (4, 110, 5, 101, 6)],
          "a plateau is one vertex; an equal vertex after a separate dip is its own nested episode")


def density():
    # 6. one session with many points in one neighbourhood: one vote in the density and in the share
    by_case = {"A": {(0, 0), (0, 1), (1, 0), (1, 1)}, "B": {(0, 0)}, "C": {(0, 1)}, "D": {(1, 1)}, "E": {(5, 5)}}
    regs, (D, k_lo, b_lo) = P.regions(by_case, 0, 6)
    check(D[0 - k_lo, 0 - b_lo] == 4 and D.max() == 4, "6a: D counts sessions, not points: four points of one session add one vote")
    zones, need = R.unique_density_zones(by_case, 0, 6, 10)
    z = [x for x in zones if (0, 0) in x["cells"]][0]
    check(z["members"] == ["A", "B", "C", "D"] and need == 4, "6b: the share of the region counts each session once")
    # A 0.1-IDR region can lie between every reachable tick of a narrow-range session.
    # A missing candle allows unknown ticks, never fractional ticks that cannot occur.
    H=dict(grid=P.block_grid("RDR"),episodes=[],
           sessions=[dict(id=c,w=100,gap=None,act_i=12) for c in "ABCD"]+[dict(id="U",w=1,gap=20,act_i=12)],
           points=[dict(case=c,kt=1,k=5,b=3,episodes=[]) for c in "ABCD"])
    fam=dict(N=5,snapshot_id="synthetic-tick-grid",key=dict(session="RDR",window=[630,645]))
    z=P.zone_map(H,fam,1)["zones"][0]
    check(z["n_known"]==4 and z["n_possible"]==0,
          "6c: a missing M5 cannot put a one-tick-IDR session in a zone between its reachable ticks")
    hit=R._Cells({("*",None,3)},width=1)&{(-10,3),(-1,3),(0,3),(1,3),(10,3)}
    check(hit=={(-10,3),(0,3),(10,3)},"6d: independent unknown-cell membership respects positive and negative integer ticks")


def review():
    # R1. a micro-swing 110 -> 109,75 -> 110,25 (ticks 440 -> 439 -> 441) is an episode at scale 1, its vertex is not local at 2
    eps, pts = run([(420, 430, 419, 429), (429, 431, 428, 430), (440, 440, 440, 440), (439, 439, 439, 439), (439, 441, 439, 441), (441, 441, 436, 437)], first=2, act=1)
    e = [x for x in eps if x["h"] == 440][0]
    check(e["status"] == "KNOWN" and e["L"] == 439 and e["kt"] == 1 and pts[0]["kt"] == 1,
          "R1a: a one-tick micro-swing is a pullback at scale 1 (one neighbour M5): the scale is named, never universal")
    big = [(420, 430, 419, 429), (429, 431, 428, 430), (430, 432, 429, 431), (450, 450, 446, 449), (449, 449, 445, 446), (446, 447, 440, 441),
           (441, 444, 438, 443), (443, 452, 443, 451), (451, 451, 447, 448), (448, 448, 444, 445)]
    eps, pts = run(big, first=2, act=1)
    v = [x for x in eps if x["h"] == 450][0]
    check(v["kt"] >= 2 and v["status"] == "KNOWN" and v["L"] == 438, "R1b: a larger swing keeps its vertex at scale 2 and more")
    ids1 = [x["a"] for x in eps]
    eps2, _ = run(big, first=2, act=1, kmax=2)
    check([x["a"] for x in eps2] == ids1 and [(x["status"], x.get("L")) for x in eps2] == [(x["status"], x.get("L")) for x in eps],
          "R1c: the scale changes whether a vertex counts, never the episode (same H, L, B at every scale)")
    # R3. the order of L, the DR break and B is kept (confirmation frame), never a filter
    base = [BOX, (104, 110, 104, 109), (109, 109, 103, 104), (104, 106, 103, 105), (105, 112, 105, 111), (111, 111, 108, 109)]
    for closes, want in (((104, 105, 111, 109), "INTACT_AT_B"), ((90, 105, 111, 109), "BETWEEN_L_B"), ((104, 90, 111, 109), "BETWEEN_L_B"),
                         ((104, 105, 111, 90), "INTACT_AT_B")):
        bars = [base[0], base[1]] + [(b[0], b[1], min(b[2], c), c) for b, c in zip(base[2:], closes)]
        eps, _ = run(bars, oppv=95)
        e = [x for x in eps if x["h"] == 110][0]
        check(e["status"] == "KNOWN" and e["dr"] == want, f"R3: closes {closes} against the opposite DR 95: {want}")
    bars = [BOX, (90, 90, 80, 85), (110, 110, 105, 109), (109, 109, 103, 104), (104, 112, 104, 111), (111, 111, 108, 109)]
    eps, _ = run(bars, act=0, oppv=95, first=1)
    e = [x for x in eps if x["h"] == 110][0]
    check(e["dr"] == "BEFORE_L", "R3: a break before the bottom is named as such; the episode stays on the map")
    bars = [BOX, None, (104, 110, 104, 109), (109, 109, 103, 104), (104, 112, 104, 111), (111, 111, 108, 109)]
    eps, _ = run(bars, act=0, oppv=95, first=2)
    e = [x for x in eps if x["h"] == 110][0]
    check(e["dr"] == "UNKNOWN", "R3: a missing M5 that could hold an earlier break leaves the order unknown")


def today():
    """8 and R2: today's facts come from closed M5 only; a visit of the region is not a completed episode."""
    fam = dict(key=dict(session="RDR", window=[630, 645]), view="conf",
               today=dict(side=1, idrH=125.0, idrL=100.0, drH=126.0, drL=99.0, c0=640, brk=None))
    H = dict(grid=P.block_grid("RDR"), first=12)
    zone = dict(zone_id="z", cell_mask=[[k, b] for k in range(0, 3) for b in range(0, 3)], time_start=630, time_end=675)
    maps = {1: dict(zones=[zone])}
    tick = 0.25
    bar = lambda t, o, h, l, c: [t, o, h, l, c]
    box = [bar(570 + 5 * i, 110, 112, 108, 111) for i in range(12)]
    # after the activation (10:40): a vertex at 10:45, the bottom inside the region at 10:55, the update at 11:05
    after = [bar(630, 120, 126.5, 118, 126.25), bar(635, 126.25, 127, 125, 126.75), bar(640, 126.75, 130, 126.75, 129.5), bar(645, 129.5, 129.75, 126, 126.5),
             bar(650, 126.5, 127, 125.5, 126.0), bar(655, 126.0, 129.0, 126.0, 128.75), bar(660, 128.75, 131.0, 128.75, 130.5)]
    day = dict(bars=box + after, tick=tick)
    t1 = P.today_part(fam, day, H, maps, 660)
    rel = t1["zones"]["1"][0]
    check(rel["visit"]["state"] == "VISITED" and rel["completion"]["state"] != "COMPLETED",
          "8 / R2: before the update's M5 closes, today's pullback in the region is a visit, never «completed»")
    t2 = P.today_part(fam, day, H, maps, 665)
    rel = t2["zones"]["1"][0]
    check(rel["completion"]["state"] == "COMPLETED" and rel["completion"]["b_close"] == 665,
          "8 / R2: completed only at the close of the M5 that updates today's own vertex")
    check(t1["zones"]["1"][0]["clock"] == "CURRENT" and P.today_part(fam, day, H, maps, 680)["zones"]["1"][0]["clock"] == "PAST",
          "today: the region's window by the clock (current, then past) is a separate fact")


def real():
    started = time.perf_counter()
    st, fam, B, day, a = P.build("NQ", "RDR", 670, "2025-12-17", "auto", "weekday")
    check(st == "OK" and a["context"]["N"] == fam["N"] == len(a["sessions"]), "real: NQ RDR 17.12.2025 — every member of the accepted family has its witness")
    chk = R.check(a, fam, B, day)
    check(chk["outcome"] == "PASS", f"real: the independent reference re-derives every episode, point, constellation and today's relation ({chk['errors'][:3]})")
    st, _, _, _, b = P.build("NQ", "RDR", 700, "2025-12-17", "auto", "weekday")
    same = all(a[k] == b[k] for k in ("sessions", "episodes", "points", "maps"))
    check(same and a["today"] != b["today"], "R2: a new slice changes today's facts only; the historical map, its points and its times stay")
    eps = [e for e in a["episodes"] if e["status"] == "KNOWN"]
    act = {m["id"]: m["act"] for m in fam["members"]}
    check(eps and all(e["h_open"] <= e["l_open"] < e["b_close"] and e["l_open"] + 5 > act[e["case"]] for e in eps),
          "R2: every episode keeps three times apart: its vertex, its bottom after the own activation, the close that established the update")
    for args in (("NQ", "RDR", 670, "2025-12-17", "auto", "all"), ("ES", "ODR", 300, "2025-11-12", "auto", "weekday"),
                 ("YM", "ADR", -100, "2025-10-08", "auto", "weekday"), ("NQ", "RDR", 870, "2025-12-10", "auto", "weekday"),
                 ("NQ", "RDR", 870, "2025-12-10", "conf", "weekday")):
        st, f2, B2, d2, p2 = P.build(*args)
        if st != "OK": check(False, f"real: {args} built ({st})")
        chk = R.check(p2, f2, B2, d2)
        check(chk["outcome"] == "PASS", f"real: {args[0]} {args[1]} {args[3]} {args[4]}:{args[5]} — reference agrees ({chk['errors'][:2]})")
        if args[4] == "auto" and f2["view"] == "brk":
            k = [e for e in p2["episodes"] if e["status"] == "KNOWN"]
            check(p2["context"]["view"] == "brk" and all(s["direction"] == f2["scale"]["orientation"] for s in p2["sessions"]) and all(e["dr"] == "NA" for e in k),
                  "R3: after today's break the map is built in the break family's own frame, never mixed with the confirmation frame")
        if args[4] == "conf" and args[3] == "2025-12-10":
            check(p2["context"]["view"] == "conf" and any(e.get("dr") in ("BETWEEN_L_B", "BEFORE_L") for e in p2["episodes"]),
                  "R3: the original confirmation family keeps its frame; episodes across a break carry their order")
    print("real families", round(time.perf_counter() - started, 1), "s", flush=True)


def faults():
    st, fam, B, day, proof = P.build("NQ", "RDR", 670, "2025-12-17", "auto", "weekday")
    good = P.publish(proof, fam, R.check(proof, fam, B, day))
    check(good["status"] == "OK" and good["contract"]["status"] == "CONFORMANT" and good["release_id"] == P.revision(good["proof"]),
          "publication: CONFORMANT, one release hash binds the whole proof")
    gate = I.review_gate()
    check(not gate.undeclared_numbers(P.ROUTE, good), "publication: every number of the answer is declared by the candidate registry")
    kinds = {b["estimand"] for b in good["contract"]["bundles"]}
    check(kinds == {"EST:PB-ZONE", "EST:PB-SESSIONS", "EST:PB-REGION"} and all(b["claim"]["claim_class"] == "DescriptiveClaim" for b in good["contract"]["bundles"]),
          "publication: only C0 descriptive claims of the three registered estimands")
    for fault in ("bar", "point", "member", "status", "marginal", "clock", "missing-marginals"):

        bad = copy.deepcopy(proof)
        if fault == "bar":
            s = next(s for s in bad["sessions"] if any(p["case"] == s["id"] for p in bad["points"]))
            j = next(j for j in range(len(s["bars"])) if s["bars"][j]); s["bars"][j][2] -= 1
        elif fault == "point": bad["points"][0]["v"] -= 1
        elif fault == "member": bad["maps"]["1"]["zones"][0]["members"].pop()
        elif fault == "status": next(e for e in bad["episodes"] if e["status"] == "KNOWN")["status"] = "UNKNOWN_INTRABAR"
        elif fault == "marginal": bad["marginals"]["1"][0]["n_known"] += 1
        elif fault == "clock": bad["marginals"]["1"][0]["later"] += 1
        else: bad.pop("marginals")
        out = P.publish(bad, fam, R.check(bad, fam, B, day))
        check(out["status"] == "REFERENCE_MISMATCH" and "proof" not in out and not out["contract"].get("bundles"),
              f"fault «{fault}»: the reference refuses, the number and the drawing are withdrawn together")
    check(P.response(dict(instrument="NQ", session="RDR", at=670, date="2026-01-02"))["status"] == "OUT_OF_SCOPE", "the closed 2026 tape cannot be opened through the candidate")
    check(len(C.registry()["estimands"]) == 53 and len(gate.registry()["estimands"]) == 63,
          "the accepted 53 estimands are untouched; the candidate edition holds 60 + 3 (zones, sessions, regional membership)")
    for region in ("[true,2,0,3]", "[2,1,0,3]"):
        try:
            P.response(dict(instrument="NQ",session="RDR",at=670,date="2025-12-17",region=region))
        except ValueError:
            rejected = True
        else:
            rejected = False
        check(rejected, "a malformed region is rejected before publication: " + region)


if __name__ == "__main__":
    t0 = time.perf_counter()
    stories(); density(); review(); today(); real(); faults()
    print("ALL GOOD", len(DONE), "checks;", round(time.perf_counter() - t0, 1), "s", flush=True)
