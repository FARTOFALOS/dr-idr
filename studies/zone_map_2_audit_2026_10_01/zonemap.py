"""DR-LAB-ZONE-MAP-2.0 (`zone-map-2`): an independent implementation written from the specification for its audit.
Not the product: design 24 does not use it.

Where the specification leaves a choice, the choice taken here is named (A1-A4) and discussed in the audit:
A1 watershed ties (§13): among equal best neighbours the earlier clock bin, then the price nearer u = 0, then the lower
   cell; «clock distance to the peak plateau» is not defined before the endpoint is known;
A2 non-peak plateaus (§11, §13): a plateau of equal D with a higher neighbour somewhere climbs as one unit to its best
   higher neighbour; the specification's per-cell rule stops such cells on a plateau that is not a peak;
A3 the zone mask after the basin floor (§14) is kept as computed even when it falls apart into pieces (the merge test
   uses the lower peak, the floor the merged maximum); how often this happens is measured;
A4 the slice t of today's status (§22-24) is the open of the last closed M5, so a new extreme has an open s > t.
"""
import math
from collections import Counter, defaultdict
from itertools import groupby

SADDLE, FLOOR, MIN_ABS, MIN_FRAC = 0.50, 0.50, 4, 0.05


class _UF:
    def __init__(self, xs): self.p = {x: x for x in xs}
    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]; x = self.p[x]
        return x
    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b: self.p[b] = a


def zone_map(pts, N):
    """pts: [(k, b, sid)] the known events of one distribution (one per session); N: the whole family.
    Returns zones (mask, members, envelope, anchor, pieces) ordered as in §21, and the residual sessions."""
    A = Counter((k, b) for k, b, _ in pts)
    occ = sorted(A)
    S = set(occ)
    nb = {c: [(c[0] + dk, c[1] + db) for dk in (-1, 0, 1) for db in (-1, 0, 1) if (dk or db) and (c[0] + dk, c[1] + db) in S] for c in occ}
    D = {c: A[c] + sum(A[n] for n in nb[c]) for c in occ}                      # §9: 3 x 3 sum of raw occupancy
    # plateaus: 8-connected occupied cells of equal D (§11)
    pl, cells = {}, defaultdict(list)
    for c in occ:
        if c in pl: continue
        q = [c]; pl[c] = c
        while q:
            x = q.pop(); cells[c].append(x)
            for n in nb[x]:
                if n not in pl and D[n] == D[c]: pl[n] = c; q.append(n)
    lev = {p: D[p] for p in cells}
    up = {p: [n for x in cells[p] for n in nb[x] if D[n] > lev[p]] for p in cells}
    peaks = [p for p in cells if not up[p]]
    pk = set(peaks)
    # maximin saddles on the occupied graph by a merge tree in decreasing D; pairs merge when S >= 0.5 x the lower peak (§12)
    muf, comp, cp = _UF(peaks), _UF(list(cells)), {}
    done = set()
    for L, grp in groupby(sorted(cells, key=lambda p: -lev[p]), key=lambda p: lev[p]):
        grp = list(grp)
        for p in grp: cp[p] = [p] if p in pk else []; done.add(p)
        for p in grp:
            for q in {pl[n] for x in cells[p] for n in nb[x]} & done:
                a, b = comp.find(p), comp.find(q)
                if a == b: continue
                for x in cp[a]:
                    for y in cp[b]:
                        if L >= SADDLE * min(lev[x], lev[y]): muf.union(x, y)
                comp.p[b] = a; cp[a] = cp[a] + cp.pop(b)
    # watershed endpoints by steepest ascent (§13, A1, A2)
    tie = lambda c: (c[1], abs(2 * c[0] + 1), c[0])
    end = {}
    for p in cells:
        x, path = p, []
        while up[x] and x not in end:
            path.append(x)
            m = max(D[n] for n in up[x])
            x = pl[min((n for n in up[x] if D[n] == m), key=tie)]
        e = end.get(x, x)
        for y in path + [x]: end[y] = e
    # basins of merged peaks, the floor, the minimum support (§14, §15)
    groups = defaultdict(list)
    for p in cells: groups[muf.find(end[p])].append(p)
    by_cell = defaultdict(list)
    for k, b, sid in pts: by_cell[(k, b)].append(sid)
    need = max(MIN_ABS, math.ceil(MIN_FRAC * N))
    zones, used = [], set()
    for g, plats in groups.items():
        top = max(lev[p] for p in peaks if muf.find(p) == g)
        mask = {x for p in plats for x in cells[p] if D[x] >= FLOOR * top}
        members = {s for x in mask for s in by_cell[x]}
        if len(members) < need: continue
        apex = min((p for p in peaks if muf.find(p) == g and lev[p] == top), key=lambda p: min(tie(x) for x in cells[p]))
        anchor = min(cells[apex], key=tie)
        zones.append(dict(mask=mask, members=members, n=len(members), k0=min(x[0] for x in mask), k1=max(x[0] for x in mask) + 1,
                          b0=min(x[1] for x in mask), b1=max(x[1] for x in mask) + 1, anchor=anchor, pieces=_pieces(mask)))
        used |= members
    near0 = lambda z: 0 if z["k0"] <= 0 < z["k1"] else z["k0"] if z["k0"] > 0 else -z["k1"]   # envelope to u = 0, cells
    zones.sort(key=lambda z: (z["b0"], -z["n"], near0(z)))
    residual = {sid for _, _, sid in pts} - used
    return dict(zones=zones, residual=residual, need=need)


def _pieces(mask):
    seen, n = set(), 0
    for c in mask:
        if c in seen: continue
        n += 1; q = [c]; seen.add(c)
        while q:
            x = q.pop()
            for dk in (-1, 0, 1):
                for db in (-1, 0, 1):
                    y = (x[0] + dk, x[1] + db)
                    if y in mask and y not in seen: seen.add(y); q.append(y)
    return n


def status(mask, q, extreme_u10, w, t_next, formed, last_open, ev):
    """Today's status of one zone (§22-24) at a slice: q = the provisional pair's cell, extreme_u10 = 10 x its directed
    value (ticks), w = today's IDR width (ticks), t_next = the earliest open of a new extreme (A4). HOLDS / POSSIBLE /
    IMPOSSIBLE by the reachable set: a farther price, a later open, within the horizon."""
    if q in mask: return "HOLDS"
    if t_next > last_open: return "IMPOSSIBLE"                                # no time left in the horizon
    for k, b in mask:
        price_ok = k * w < extreme_u10 if ev == "R" else (k + 1) * w > extreme_u10
        if not price_ok: continue
        lo_open, hi_open = formed + 15 * b, formed + 15 * b + 10              # the M5 opens of the cell
        if hi_open >= t_next and lo_open <= last_open: return "POSSIBLE"
    return "IMPOSSIBLE"
