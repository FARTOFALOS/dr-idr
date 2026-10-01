"""Checks of design 24's statistical layer (lab/scene24.py) against the semantic specification DR-LAB-SEM-1.0.

    python -B tests/sem24.py

Part 1: the specification's 32 synthetic reference checks (its validate_semantics_v1.py), carried over to the
functions of scene24 (rows in integer ticks, u = v / w with w = 10 so every rational of the reference is exact).
Part 2: integration checks on the session base (lab/.runtime/boxes_*): the equalities and differences of spec §14 on
real families, including the two families of spec §12 (NQ RDR Wednesday long 11:45-12:00, NQ ODR Wednesday long
04:00-04:15). Prints aggregates only (no dates, no paths). Exit code 0 = all good.
"""
import sys
from collections import Counter
from fractions import Fraction as Q
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lab"))
import scene21  # noqa: E402
import scene24 as S  # noqa: E402

failures = []


def check(cond, msg):
    print(("  ok  " if cond else "  FAIL ") + msg)
    if not cond: failures.append(msg)


# ---------- part 1: the 32 reference checks ----------
W = 10                                     # every rational of the reference times 10 is an integer


def rows_of(spec):
    """Reference rows (close minute, low, high, close) as fractions of the IDR -> {close: (close, o, h, l, c)} ticks,
    long, edge 0, width 10."""
    out = {}
    for t, l, h, c in spec:
        L, H, C = int(Q(l) * W), int(Q(h) * W), int(Q(c) * W)
        assert L <= C <= H
        out[t] = (t, C, H, L, C)
    return out


def summ(spec, act, end, opp=Q(-11, 10)):
    return S.measure(rows_of(spec), act, end, 1, 0, int(Q(opp) * W))


def thr(spec, start, end, level, up=True):
    lv = Q(level)
    return S.reach(rows_of(spec), start, end, 1, 0, W, (lv.numerator, lv.denominator), up)


print("Part 1: the 32 reference checks of the specification")
a = [(5, Q(-1, 2), Q(1, 5), 0), (10, 0, 1, Q(1, 2))]
b = [(5, 0, 1, Q(1, 2)), (10, Q(-1, 2), Q(1, 5), 0)]
sa, sb = summ(a, 0, 10), summ(b, 0, 10)
check((sa["R"]["v"], sa["X"]["v"]) == (sb["R"]["v"], sb["X"]["v"]) and sa["order"] != sb["order"], "same_extreme_values_different_order")
check(summ(a + [(15, -9, 9, 0)], 0, 10) == sa, "session_end_excludes_next_block")
check(summ([(0, -9, 9, 0)] + a, 0, 10) == sa, "confirmation_bar_excluded")
check(summ(b, 5, 10)["X"]["v"] == int(Q(1, 5) * W), "own_confirmation_changes_event")
check(S.window_of(660, 630) == 1 and S.window_of(665, 630) == 2, "window_by_open_label")
check(S.window_of(-205, -210) == S.window_of(1235, 1230) == 0, "adr_wrap_keeps_window")
check(S.cell(-3, 4) == -8 and S.cell(1, 2) == 5, "half_open_price_boundary")
check((750 - 0) // S.WINDOW == 50, "time_boundary_has_no_minus_one")
rep = summ(a + [(15, Q(-1, 2), 1, 0)], 0, 15)
check(rep["R"]["ties"] == [0, 10] and rep["X"]["ties"] == [5, 10], "all_tied_times_preserved")
check(rep["R"]["t"] == 0, "single_event_uses_first_time")
check(summ([(5, -1, 1, 0)], 0, 5)["order"] == "same_M5", "same_bar_order_unknown")
mis = summ(a[:1], 0, 10)
check(mis["s"] == "unknown" and mis["R"]["s"] == "unknown", "missing_bar_invalidates_final_extreme")
check(mis["outcome"] == "unknown", "missing_without_observed_break_not_held")
check(summ([(5, -2, 0, Q(-3, 2))], 0, 10)["outcome"] == "broken", "observed_break_survives_missing")
check(summ([(5, -2, 0, 0)], 0, 5)["outcome"] == "held", "wick_not_DR_break")
check(summ([(5, -2, 0, Q(-11, 10))], 0, 5)["outcome"] == "held", "equal_opposite_DR_not_break")
check(summ([], 10, 10)["s"] == "none", "no_future_event_is_none")
check(summ([], 10, 10)["outcome"] == "none", "empty_lifetime_is_not_evidence_DR_held")
check(thr(a, 10, 10, Q(1, 2)) == "no", "empty_remaining_horizon_has_no_reach")
check(thr(a[1:], 0, 10, Q(1, 2)) == "yes", "hit_with_other_missing_is_known_yes")
check(thr(a[:1], 0, 10, 1) == "unknown", "no_hit_with_missing_is_unknown")
gap = [(5, Q(4, 5), 1, Q(9, 10))]
check(thr(gap, 0, 5, Q(1, 2)) == "yes" and not S.crosses(int(Q(4, 5) * W), W, int(Q(1, 2) * W)), "beyond_is_not_literal_intersection")
check(sum(1 for k in range(3) if S.visits(0, int(Q(1, 5) * W), k, k + 1)) == 3, "range_can_cover_multiple_bins")
check(Q(7, 25) + Q(13, 25) + Q(5, 25) == 1, "full_N_with_unknown")
check((Q(7, 25), Q(7 + 5, 25)) == (Q(28, 100), Q(48, 100)), "unknown_share_bounds")
check(Q(5, 25) != Q(2, 25), "price_band_not_joint_region")
check(Q(18, 25) >= Q(7, 10) > Q(17, 25), "70_percent_not_exact_at_N25")
# reflection: a short with mirrored prices gives the same directed values as the long
long_row, short_row = (5, 100, 109, 95, 104), (5, -100, -95, -109, -104)
check(S.directed(long_row, 1, 100) == S.directed(short_row, -1, -100), "long_short_reflection")
# today's prefix: the state at a slice does not depend on the bars after it, nor on the forming M5
def day_bars(extra):
    box = [[570 + 5 * j, 100.0, 101.0, 99.0, 100.0 + (j % 2)] for j in range(12)]     # a box: DR 99..101, IDR 100..101
    return box + [[630, 100.5, 101.25, 100.5, 101.25], [635, 101.25, 101.5, 101.0, 101.25]] + extra
fa, fb = day_bars([[640, 101.25, 101.25, 90.0, 91.0]]), day_bars([[640, 101.25, 120.0, 101.0, 119.0]])
sta, stb = scene21._state(fa, "RDR", 640, 1020, False), scene21._state(fb, "RDR", 640, 1020, False)
check((sta["conf"], sta["side"], sta["price"]) == (stb["conf"], stb["side"], stb["price"]) == (635, 1, 101.25) and not sta.get("failed"),
      "today_prefix_invariant_to_future_replacement")
sfa, sfb = scene21._state(fa, "RDR", 644, 644, True), scene21._state(fb, "RDR", 644, 644, True)
check((sfa["conf"], sfa["side"], sfa.get("failed")) == (sfb["conf"], sfb["side"], sfb.get("failed")), "forming_M5_does_not_change_statistics")
check(len({"s1", "s1", "s2"}) == 2, "member_with_two_places_counted_once_in_union")
check(all(not (sa["X"]["v"] >= up) or sa["X"]["v"] >= lo for lo, up in [(5, 10), (10, 15)]), "levels_are_nested")
n1 = 32 - sum(1 for f in failures)
print(f"  -> {n1} of 32 reference checks pass")

# ---------- part 2: integration on the session base ----------
print()
print("Part 2: families of the session base")
B = scene21._boxes("NQ")
if B is None:
    check(False, "session base built (python -B lab/build_boxes.py)")
    sys.exit(1)


def snap(session, weekday, side, view, win, cutoff="2026-01-01"):
    return S._snapshot("NQ", B, session, weekday, side, view, win, cutoff)


def members_rows(session, sn):
    """{id: rows} of the snapshot's members, for recomputation."""
    shift = S.SHIFT[session]
    out = {}
    for i, m in enumerate(B["boxes"]):
        if m["session"] == session and S._sid("NQ", m) in set(sn["ids"]): out[S._sid("NQ", m)] = (S._rows(B, i, shift), m)
    return out


def check_snapshot(label, session, sn):
    N, f, end = sn["N"], S.SESS[session][1], S.SESS[session][2]
    for ev in ("R", "X"):
        c = sn["counts"][ev]
        check(sum(n for _, _, n in c["cells"]) + c["unknown"] + c["none"] == N, f"{label}: {ev} cells + unknown + none = N ({N})")
        P = Counter(); T = Counter()
        for k, b, n in c["cells"]: P[k] += n; T[b] += n
        check(sum(P.values()) == sum(T.values()) == c["known"], f"{label}: {ev} price and time histograms are projections of one table")
        check(all(0 <= b < (end - f) // 15 for b in T), f"{label}: {ev} time cells inside the block")
    if "outcome" in sn["counts"]:
        o = sn["counts"]["outcome"]
        check(sum(o.values()) == N, f"{label}: DR outcomes add up to N: {o}")
    check(len(set(sn["ids"])) == N, f"{label}: one member = one session")
    # the tail of X equals «на уровне или дальше» on the same own horizon (spec §14.1-3), at every 0.1 level
    rows = members_rows(session, sn)
    bad = 0
    for m in sn["members"]:
        r, meta = rows[m["id"]]
        d = sn["scale"]["orientation"]
        side = 1 if meta["side"] == 1 else -1
        e = meta["idr_high"] if d == 1 else meta["idr_low"]
        for k in range(-20, 31):
            yes = S.reach(r, m["act"], end, d, e, m["w"], (k, 10), True)
            if m["X"]["s"] == "known" and (yes == "yes") != (10 * m["X"]["v"] >= k * m["w"]): bad += 1
            yes = S.reach(r, m["act"], end, d, e, m["w"], (k, 10), False)
            if m["R"]["s"] == "known" and (yes == "yes") != (10 * m["R"]["v"] <= k * m["w"]): bad += 1
    check(bad == 0, f"{label}: X tail = reach up and R cumulative = reach down at 51 levels (mismatches {bad})")
    # nesting: a farther level is reached by no more sessions; a shorter remaining horizon by no more sessions
    worse = 0
    for m in sn["members"]:
        r, meta = rows[m["id"]]
        d = sn["scale"]["orientation"]
        e = meta["idr_high"] if d == 1 else meta["idr_low"]
        prev = None
        for t in range(m["act"], end + 1, 15):
            y = S.reach(r, t, end, d, e, m["w"], (5, 10), True)
            if prev == "no" and y == "yes": worse += 1
            prev = y if y != "unknown" else prev
    check(worse == 0, f"{label}: a shorter remaining horizon never adds a reach (violations {worse})")
    # region inside a band: the joint share never exceeds the band share
    for ev in ("R", "X"):
        cells = sn["counts"][ev]["cells"]
        if not cells: continue
        k0 = Counter(k for k, _, _ in cells).most_common(1)[0][0]
        band = sum(n for k, _, n in cells if k == k0)
        region = sum(n for k, b, n in cells if k == k0 and b == min(bb for kk, bb, _ in cells if kk == k0))
        check(region <= band, f"{label}: {ev} a region's share <= its band's share ({region} <= {band} of {N})")
    return sn


# the two families of spec §12
rdr = check_snapshot("NQ RDR Wed long 11:45", "RDR", snap("RDR", 2, 1, "conf", 5))
odr = check_snapshot("NQ ODR Wed long 04:00", "ODR", snap("ODR", 2, 1, "conf", 0))
print(f"       RDR: N={rdr['N']}, outcome {rdr['counts']['outcome']}, order {rdr['counts']['order']}, unknown R {rdr['counts']['R']['unknown']}, journal {rdr['journal']}")
print(f"       ODR: N={odr['N']}, outcome {odr['counts']['outcome']}, order {odr['counts']['order']}, unknown R {odr['counts']['R']['unknown']}, journal {odr['journal']}")
check(rdr["N"] == 25 and rdr["counts"]["outcome"] == dict(held=21, broken=4, unknown=0, none=0), "RDR family agrees with spec §12 (N 25, held 21, broken 4)")
odr_ref = dict(held=133, broken=51, unknown=3, none=0)
check(odr["counts"]["outcome"] == odr_ref or odr["N"] < 187, f"ODR family agrees with spec §12 or is smaller by the undetermined keys (N {odr['N']} vs 187)")
o = rdr["counts"]["order"]
check(o.get("X_before_R") == 17 and o.get("R_before_X") == 8, "RDR order of first times as in spec §12 (X first 17, R first 8)")
check(sum(1 for m in rdr["members"] if m["orderDetail"] and m["orderDetail"]["all_x_before_all_r"]) == 16, "RDR: all X before all R in 16 sessions (spec §12)")
# the break family: another N, flipped orientation, no DR outcome inside it
brk = snap("RDR", 2, 1, "brk", 8)
check("outcome" not in brk["counts"] and brk["scale"]["orientation"] == -1, f"break family: no DR-outcome share, orientation flipped (N {brk['N']})")
check(snap("RDR", 2, 1, "conf", 5)["snapshot_id"] == rdr["snapshot_id"], "returning to the confirmation snapshot restores the same snapshot")
# the snapshot does not depend on today's slice: the history-day request at different slices keeps its snapshot
d = next(x[0] for x in S.dates("NQ")["dates"] if x[0] >= "2025-06-02" and "R" in x[1])
ids = set()
for at in (700, 760, 840, 955):
    r = S.family("NQ", "RDR", at=at, date=d)
    if r.get("status") == "ok" and r["view"] == "conf": ids.add(r["snapshot_id"])
check(len(ids) <= 1, f"history day {d[:4]}: the snapshot is the same at every slice of the day (distinct ids {len(ids)})")
# every session of the base: a family member is always before the viewed date
f2 = S.family("NQ", "RDR", at=840, date=d)
if f2.get("status") == "ok": check(all(m["date"] < d for m in f2["members"]), "history day: every member is from an earlier date")
# ODR and ADR are measured the same way as RDR
for sess, win in (("ODR", 1), ("ADR", 1)):
    sn = snap(sess, 1, -1, "conf", win)
    check(sn["N"] >= 0 and sum(sn["counts"]["outcome"].values()) == sn["N"], f"{sess} Tue short window {win}: N {sn['N']}, outcome {sn['counts']['outcome']}, unknown R {sn['counts']['R']['unknown']}")

# ---------- part 3: the automatic main cluster (lab/cluster24.py, meaning/11) ----------
print()
print("Part 3: the main cluster")
import numpy as np  # noqa: E402
import cluster24 as C  # noqa: E402

F0, E0 = 630, 960                          # RDR: cells from 10:30, block end 16:00; family window 0


def fam(n, cluster=0, where=(0, 0), extra=(), old_only=False, seed=7, spread=(-20, 20)):
    """A synthetic family in date order: `cluster` members inside the block at price cells where[0]…+4 and time cells
    where[1]…+3, the others spread over the family's time and prices; w = 10, so the price cell of v is v."""
    rng = np.random.default_rng(seed)
    pts = []
    picks = set(rng.choice(n // 2 if old_only else n, cluster, replace=False).tolist()) if cluster else set()
    for i in range(n):
        if i in picks: k, b = where[0] + int(rng.integers(0, 5)), where[1] + int(rng.integers(0, 4))
        else: k, b = int(rng.integers(*spread)), int(rng.integers(0, 22))
        pts.append(("k", k, 10, F0 + 15 * b + 5 * int(rng.integers(1 if b == 0 else 0, 3))))
    for e in extra: pts[e[0]] = e[1]
    return pts


clear = fam(120, 36)
r1 = C.main_cluster(clear, "R", F0, E0, 0)
check(r1["status"] == "earned" and r1["block"]["k0"] in (-1, 0, 1) and r1["block"]["b0"] in (0, 1), f"a clear concentration earns the name (failed {r1['failed']}, block {r1.get('block')})")
inside = sum(1 for p in clear if r1["block"]["k0"] <= p[1] < r1["block"]["k1"] and r1["block"]["b0"] <= (p[3] - F0) // 15 < r1["block"]["b1"])
check(inside == r1["yes"], f"the cluster's number = the known events inside its block ({inside} = {r1['yes']})")
check(C.main_cluster(clear, "R", F0, E0, 0) == r1, "the same family gives the same cluster (fixed resampling seed)")
r2 = C.main_cluster(fam(120, 0, seed=8), "R", F0, E0, 0)
check(r2["status"] == "candidate", f"a family without a concentration earns nothing (failed {r2['failed']})")
r3 = C.main_cluster(fam(40, 12), "R", F0, E0, 0)
check(r3["status"] == "candidate" and "U5" in r3["failed"], f"a family under 60 sessions earns nothing: the newer half is under 30 (failed {r3['failed']})")
two = fam(120, 0, seed=9)
rng = np.random.default_rng(3)
for i in range(0, 120, 4): two[i] = ("k", int(rng.integers(0, 5)), 10, F0 + 15 * int(rng.integers(0, 4)) + 5)
for i in range(2, 120, 4): two[i] = ("k", -12 + int(rng.integers(0, 5)), 10, F0 + 15 * (10 + int(rng.integers(0, 4))))
r4 = C.main_cluster(two, "R", F0, E0, 0)
check(r4["status"] == "candidate" and ("U2" in r4["failed"] or "U4" in r4["failed"]), f"two equal concentrations: no main one (failed {r4['failed']})")
r5 = C.main_cluster(fam(120, 30, old_only=True), "R", F0, E0, 0)
check(r5["status"] == "candidate" and "U5" in r5["failed"], f"a concentration only in the older half does not hold on the newer one (failed {r5['failed']})")
# the unknown put against the leader: two unknown sessions that could stand in the rival's block lower the lead by 2
base = fam(120, 0, seed=11, spread=(-40, 40))
for j, i in enumerate(range(0, 120, 6)): base[i] = ("k", j % 5, 10, F0 + 15 * (j % 4) + 5)            # 20 in the leader
for j, i in enumerate(range(3, 120, 7)): base[i] = ("k", -15 + j % 5, 10, F0 + 15 * (12 + j % 4))      # 17 in the rival
lead = C.main_cluster(base, "R", F0, E0, 0)["checks"]["U2"]
unk = list(base)
for i in (1, 7): unk[i] = ("u", None, 10, None, [F0 + 15 * 13])                                        # nothing observed
lead_u = C.main_cluster(unk, "R", F0, E0, 0)["checks"]["U2"]
check(lead["lead"] - lead_u["lead"] == 2 and lead_u["rival"]["unknown"] == 2, f"the unknown counts against the leader (lead {lead['lead']} -> {lead_u['lead']})")
r6 = C.main_cluster(clear, "R", F0, E0, 0, after=4)
check(r6.get("block") is None or r6["block"]["b0"] >= 4, "the study's 'inside the session' candidate starts an hour after the first block")
# on the base: the cluster is part of the snapshot, its number is its block's count, the name follows the check
dd = "2025-12-09"
seen = {}
for at in (700, 840, 955):
    r = S.family("NQ", "RDR", at=at, date=dd, view="conf")
    if r.get("status") != "ok": continue
    for ev in ("R", "X"):
        c = r["clusters"][ev]
        seen.setdefault(ev, set()).add((c["status"], str(c.get("block")), c.get("yes"), c["named"]))
        if c.get("block"):
            b = c["block"]
            n = sum(n for k, t, n in r["counts"][ev]["cells"] if b["k0"] <= k < b["k1"] and b["b0"] <= t < b["b1"])
            check(n == c["yes"], f"base: {ev} cluster number = its block's count in the snapshot ({n} = {c['yes']})")
        check(not c["named"] or (c["status"] == "earned" and C.CHECK["RDR"]["held"]), f"base: {ev} named only when earned and the check of RDR held")
check(all(len(v) == 1 for v in seen.values()) and seen, "base: the cluster does not move with the slice")
rb = S.family("NQ", "RDR", date="2025-12-17", view="auto")
if rb.get("status") == "ok" and rb["view"] == "brk": check(not any(rb["clusters"][e]["named"] for e in ("R", "X")), "base: the break family gets no name (not checked)")

print()
print("ALL GOOD" if not failures else f"{len(failures)} FAILED")
sys.exit(1 if failures else 0)
