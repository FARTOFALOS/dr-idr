"""DR Lab 23.5 — the semantic core DR-LAB-TP-1.1 (operator 03.11.2026, in chat; the document «DR-LAB-TP-1.1 · Смысловое
ядро созвездий» in the project «dr», file claude/dr-lab-tp-1-0-smyslovoe-yadro.md).

What it measures, in the author's order (time → price → continuation):
- T: the confirmation family's sessions whose DR held (the author's «only true scenarios», operator 03.11: «нам нужно
  отбирать сессии, которые действительно удержали»); the whole family stays only for the DR outcome;
- the clock of T's pullbacks R (R before the session's extreme, ':rpre'): known R per 15-minute cell of the block, its
  bunches (every one shown, operator 03.11: «важно видеть и такой кластер, а не один всего лишь выбирать»), its median
  and its 70 % mark (the open minute by which half / 70 % of T's known R had happened);
- the windows the marks cut: W1 from the start of the first bunch to the median (the author's entry window, «first mode
  from the left … up until the median»), W2 from the median to the 70 % mark (the author's second window), LATE after
  it, BEFORE ahead of W1;
- the price bands of one window's sessions (the author's «the data automatically adjusts»): a window family T_W is the
  sessions of T whose R lies in the window, and its bands are the places of the screen;
- the places of the same sessions' top X (operator 04.11: X shown like R; core 1.4, 04.11 evening): the price bands of
  all the window's tops, as the author's «cluster of extension… next big cluster» targets, over 0.2-SD cells (X spreads
  over ~3 SD: at 0.1 the rule split it into fragile bands of 4-6 sessions; at 0.2 the bands are found in more families
  and hold better on a held-out session and on later years, the check of 04.11). The time of the tops is their own
  clock (bunches, median, 70 %), not a place: bunch × band places were tried on 04.11 and held no better than chance. A
  top in the last 15 minutes of the block is a move that had not ended before the close: it is counted apart («ход не
  кончился до закрытия») and never forms a place (the old pile of X at 16:00); it still counts in N and in the ladder.

The bunch and band rule (executor's provisional choice, [И]; the numbers are the operator's next stage, core §12): over
raw counts of one axis (15-minute cells, or 0.1-SD cells; 0.2-SD cells for X), an apex is a cell at least as high as its neighbours; an
apex is a bunch / band when its prominence (its height above the higher of the two lowest points separating it from a
higher apex, or from the edge) is at least half its height; neighbouring accepted apexes split the axis at the lowest
cell between them; the region of an apex is the run around it, inside its part, where the count is at least half the
apex; it needs max(4, ceil(0.05 N)) sessions (the support of zone-map-3). Equal heights: the earlier cell is the higher.
Every quantity here is a count of real sessions; nothing is smoothed.
"""
from __future__ import annotations

STEP = 15                          # minutes of a time cell (the operator's grid)
VERSION = "tp-2.0"              # 2.0 (10.11): the mass threshold from the size N of the whole family F
BANDS_RULE, NONE_RULE = "TP_BANDS", "TP_NONE"     # key.zone_rule of a window family and of T itself
BANDS_VERSION = "tp-bands-4"      # 4 (10.11, DR-LAB-TP-2.0): the support from N of the whole family F; 2 (04.11): X places as bunch × band; 3 (04.11 evening): X places as price bands, 0.2 SD
X_CELL = 2                         # an X band counts 0.2-SD cells: two cells of the 0.1 grid (core 1.4 [И])
WINDOWS = ("BEFORE", "W1", "W2", "LATE")
Q_MEDIAN, Q_70 = (1, 2), (7, 10)


def need(n):
    """The minimum support of a bunch or a band: max(4, ceil(0.05 n)) [И, the support of zone-map-3]."""
    return max(4, -(-n // 20))


def regions(c):
    """The bunch / band rule on a list of counts (module note). Returns [(lo, hi, apex)] as indices, ordered."""
    n = len(c)
    if not n: return []
    higher = lambda j, i: c[j] > c[i] or (c[j] == c[i] and j < i)
    apex = [i for i in range(n) if c[i] > 0 and (i == 0 or c[i] >= c[i - 1]) and (i == n - 1 or c[i] >= c[i + 1])
            and not (i > 0 and c[i - 1] == c[i])]                       # a plateau is one apex, at its first cell
    keep = []
    for i in apex:
        base = []
        for step in (-1, 1):
            j, low = i + step, c[i]
            while 0 <= j < n and not higher(j, i):
                low = min(low, c[j]); j += step
            base.append(low if 0 <= j < n else 0)                       # past the edge the count is 0
        if 2 * (c[i] - max(base)) >= c[i]: keep.append(i)
    out = []
    for a, i in enumerate(keep):
        left = 0 if a == 0 else min(range(keep[a - 1], i + 1), key=lambda j: (c[j], j)) + 1
        right = n - 1 if a == len(keep) - 1 else min(range(i, keep[a + 1] + 1), key=lambda j: (c[j], j)) - 1
        lo = hi = i
        while lo - 1 >= left and 2 * c[lo - 1] >= c[i]: lo -= 1
        while hi + 1 <= right and 2 * c[hi + 1] >= c[i]: hi += 1
        out.append((lo, hi, i))
    return out


def quantile_time(ts, q):
    """The open minute by which ceil(q K) of the K known events had happened (ts sorted); None without events."""
    K = len(ts)
    if not K: return None
    k = -(-q[0] * K // q[1])
    return dict(t=int(ts[k - 1]), k=int(k), K=int(K))


def clock(members, ev, formed):
    """The known event times of members (scene24 records) and their 15-minute cells."""
    ts = sorted(int(m[ev]["t"]) for m in members if m[ev]["s"] == "known")
    cells = {}
    for t in ts:
        b = (t - formed) // STEP
        cells[b] = cells.get(b, 0) + 1
    unknown = sum(1 for m in members if m[ev]["s"] == "unknown")
    none = sum(1 for m in members if m[ev]["s"] == "none")
    return ts, cells, unknown, none


def windows(members, formed, win, end, n_base=None):
    """The clock of T's R, its bunches, marks and windows. members: T (the family's DR-held sessions); n_base: the size N
    of the whole family F, the base of the mass threshold (DR-LAB-TP-2.0 §3: a bunch needs max(4, ceil(0.05 N)) sessions
    of the family, operator 10.11)."""
    N = len(members)
    nb = N if n_base is None else int(n_base)
    ts, cells, unknown, none = clock(members, "R", formed)
    b_lo, b_hi = win, (end - 5 - formed) // STEP
    c = [cells.get(b, 0) for b in range(b_lo, b_hi + 1)]
    bunches = []
    for lo, hi, top in regions(c):
        n = sum(c[lo:hi + 1])
        if n >= need(nb): bunches.append(dict(b0=b_lo + lo, b1=b_lo + hi + 1, n=int(n), peak=b_lo + top))
    med, p70 = quantile_time(ts, Q_MEDIAN), quantile_time(ts, Q_70)
    W = dict.fromkeys(WINDOWS)
    if med:
        bm, bp = (med["t"] - formed) // STEP, (p70["t"] - formed) // STEP
        first = next((u for u in bunches if u["b0"] <= bm), None)
        s = first["b0"] if first else b_lo          # [И] no bunch before the median: W1 starts at the confirmation
        W["W1"] = [s, bm + 1]
        if s > b_lo: W["BEFORE"] = [b_lo, s]
        if bp > bm: W["W2"] = [bm + 1, bp + 1]
        if bp < b_hi: W["LATE"] = [bp + 1, b_hi + 1]
    return dict(version=VERSION, N=N, known=len(ts), unknown=unknown, none=none, cells=[[b, n] for b, n in sorted(cells.items())],
                bunches=bunches, median=med, p70=p70, windows=W, need=need(nb), n_base=nb, step=STEP, range=[b_lo, b_hi + 1])


def in_window(m, W, formed):
    """A member of T belongs to the window [b0, b1) when its R is known and its 15-minute cell lies in it."""
    x = m["R"]
    return W is not None and x["s"] == "known" and W[0] <= (x["t"] - formed) // STEP < W[1]


def x_marks(members, formed):
    """The median and 70 % marks of the sessions' own X (the continuation's time lines, core §4.6)."""
    ts, cells, unknown, none = clock(members, "X", formed)
    return dict(median=quantile_time(ts, Q_MEDIAN), p70=quantile_time(ts, Q_70), known=len(ts), unknown=unknown, none=none,
                cells=[[b, n] for b, n in sorted(cells.items())])


def bands(points, n_family, b_lo, b_hi):
    """The places of one window family: price bands of its events by the bunch rule over 0.1-SD cells (the counts over
    the window's cells), each with the cells its sessions really occupy. points: [(k, b, session_id)]. The record has the
    shape of lab/zonemap24.py::zone_map (zones, residual, need)."""
    pts = [p for p in points if b_lo <= p[1] <= b_hi]
    req = need(n_family)
    if not pts: return dict(zones=[], residual=[], need=req)
    ks = [k for k, _, _ in pts]
    k_lo, k_hi = min(ks), max(ks)
    c = [0] * (k_hi - k_lo + 1)
    for k, _, _ in pts: c[k - k_lo] += 1
    zones = []
    for lo, hi, _ in regions(c):
        sel = [p for p in pts if k_lo + lo <= p[0] <= k_lo + hi]
        members = sorted({s for _, _, s in sel})
        if len(members) < req: continue
        occ = {}
        for k, b, s in sel: occ.setdefault((k, b), []).append(s)
        top = max(len(v) for v in occ.values())
        anchor = min((q for q, v in occ.items() if len(v) == top), key=lambda q: (q[1], abs(2 * q[0] + 1), q[0]))
        cs = sorted(occ)
        zones.append(dict(cells=cs, members=members, n=len(members), apex_D=top, anchor=anchor,
                          price=[k_lo + lo, k_lo + hi + 1], time=[min(q[1] for q in cs), max(q[1] for q in cs) + 1]))
    near0 = lambda z: 0 if z["price"][0] <= 0 < z["price"][1] else z["price"][0] if z["price"][0] > 0 else -z["price"][1]
    zones.sort(key=lambda z: (z["time"][0], -z["n"], near0(z)))
    used = {s for z in zones for s in z["members"]}
    return dict(zones=zones, residual=sorted({s for _, _, s in pts} - used), need=req)


def xbands(points, n_family, b_lo, b_hi):
    """The places of the top X of one window family (module note, core 1.4): the price bands of every known top of the
    window's sessions by the band rule over 0.2-SD cells (X_CELL cells of the 0.1 grid), without the tops of the block's
    last 15-minute cell (a move cut by the close); each place with the 0.1 cells its sessions really occupy, its price
    bounds on the 0.1 grid. points: [(k, b, session_id)] on the 0.1 grid. The record has the shape of bands /
    lab/zonemap24.py::zone_map; the residual holds every known top outside a place, those of the last cell included."""
    pts = [p for p in points if b_lo <= p[1] <= b_hi]
    req = need(n_family)
    body = [p for p in pts if p[1] < b_hi]
    at = {s: (k, b) for k, b, s in body}                                 # one top per session
    zones = []
    for z in bands([(k // X_CELL, b, s) for k, b, s in body], n_family, b_lo, b_hi - 1)["zones"]:
        occ = {}
        for s in z["members"]: occ.setdefault(at[s], []).append(s)
        top = max(len(v) for v in occ.values())
        anchor = min((q for q, v in occ.items() if len(v) == top), key=lambda q: (q[1], abs(2 * q[0] + 1), q[0]))
        cs = sorted(occ)
        zones.append(dict(cells=cs, members=z["members"], n=z["n"], apex_D=top, anchor=anchor,
                          price=[X_CELL * z["price"][0], X_CELL * z["price"][1]], time=[min(q[1] for q in cs), max(q[1] for q in cs) + 1]))
    near0 = lambda z: 0 if z["price"][0] <= 0 < z["price"][1] else z["price"][0] if z["price"][0] > 0 else -z["price"][1]
    zones.sort(key=lambda z: (z["time"][0], -z["n"], near0(z)))
    used = {s for z in zones for s in z["members"]}
    return dict(zones=zones, residual=sorted({s for _, _, s in pts} - used), need=req)
