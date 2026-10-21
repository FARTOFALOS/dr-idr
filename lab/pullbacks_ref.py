"""Independent reference of the candidate DR-LAB-PB-0.1 (lab/pullbacks24.py), written again from its definition
(meaning/lens/2026-10-21-otkaty-do-obnovleniya/03-opredelenie-PB-0.1.md) in another way:

- every session's bars are re-read from the session base (not through scene24), and its trading-window lows, highs and
  closes must equal the path of the same member in the accepted family snapshot;
- the bottom of an episode is found on explicit price paths: the vertex M5 and the update M5 are each walked in both
  orders their OHLC allow (high first / low first); the bottom is established only when all four combinations give the
  same price and the same M5 (two orders of two M5 are the extreme cases of every compatible path);
- the cells a not established bottom could take are enumerated tick by tick;
- the constellations are found without scipy: D(cell) counts the sessions with a point in its 3 x 3 neighbourhood
  directly, the half-height regions are grown by breadth-first search;
- today's episodes and relations are recomputed from the day's own candles.
check(proof, fam, B, day) -> {"outcome": "PASS" | "FAIL", "errors": [...], "checked": n}.
"""
from __future__ import annotations

import hashlib
import math

SESS = {"ADR": (-270, -210, 120), "ODR": (180, 240, 510), "RDR": (570, 630, 960)}
SHIFT = {"ADR": 1440, "ODR": 0, "RDR": 0}


def _dir(o, h, l, c, d, e):
    if d == 1: return [o - e, h - e, l - e, c - e]
    return [e - o, e - l, e - h, e - c]


def base_bars(B, date, session, d, e):
    start, _, end = SESS[session]
    i = B["idx"][(date, session)]
    by = {}
    for r in B["bars"][B["off"][i]:B["off"][i + 1]].tolist():
        by[int(r[0]) - SHIFT[session]] = _dir(int(r[1]), int(r[2]), int(r[3]), int(r[4]), d, e)
    return [by.get(T) for T in range(start + 5, end + 1, 5)]


def scale_states(bars, a, b, h, kmax):
    """'T' / 'N' / 'F' at every scale 1..kmax, by explicit neighbour lists."""
    out = []
    for k in range(1, kmax + 1):
        idx = list(range(a - k, a)) + list(range(b + 1, b + 1 + k))
        if any(i < 0 or i >= len(bars) for i in idx): out.append("F"); continue
        qs = [bars[i] for i in idx]
        if any(q is not None and q[1] >= h for q in qs): out.append("F")
        elif any(q is None for q in qs): out.append("N")
        else: out.append("T")
    return out


def plateaus(bars, first):
    res, i = [], 0
    while i < len(bars):
        q = bars[i]
        if q is None or (i > 0 and bars[i - 1] is not None and bars[i - 1][1] == q[1]): i += 1; continue
        j = i
        while j + 1 < len(bars) and bars[j + 1] is not None and bars[j + 1][1] == q[1]: j += 1
        if i >= first: res.append((i, j, q[1]))
        i = j + 1
    return res


def _walk(bar, order):
    o, h, l, c = bar
    return [o, h, l, c] if order == "HF" else [o, l, h, c]


def bottom(bars, a, h, jb):
    """Four explicit paths: (price, M5) of the first deepest point on each."""
    res = []
    for oa in ("HF", "LF"):
        pa = _walk(bars[a], oa)
        after = pa[pa.index(h) + 1:]
        for ob in ("HF", "LF"):
            pts = [(x, a) for x in after]
            for j in range(a + 1, jb):
                pts += [(x, j) for x in bars[j]]
            pb = _walk(bars[jb], ob)
            for x in pb:
                if x > h: break
                pts.append((x, jb))
            m = min(x for x, _ in pts)
            res.append((m, next(j for x, j in pts if x == m)))
    return res


def possible_values(bars, a, h, jb):
    """Every (M5, price) at which the first deepest point could lie, tick by tick: a part can hold it at x when every
    earlier part can stay strictly above x and every later part at or above x."""
    parts = []
    o, hh, l, c = bars[a]
    parts.append((a, l, l if (o == h or c == l) else c))
    for j in range(a + 1, jb): parts.append((j, bars[j][2], bars[j][2]))
    o, hh, l, c = bars[jb]
    if o <= h: parts.append((jb, l, l if o == l else o))
    out = []
    for i, (j, lo, hi) in enumerate(parts):
        for x in range(lo, hi + 1):
            if all(x < p[2] for p in parts[:i]) and all(x <= p[2] for p in parts[i + 1:]): out.append((j, x))
    return out


def possible_cells(bars, a, h, jb, act, w, formed, grid):
    return {((10 * x) // w, (grid[j] - 5 - formed) // 15) for j, x in possible_values(bars, a, h, jb) if j > act}


def episodes_of(bars, first, act, oppv, kmax):
    out = []
    for a, b, h in plateaus(bars, first):
        st = scale_states(bars, a, b, h, kmax)
        kt = next((k for k, s in enumerate(st) if s != "T"), kmax)
        kn = next((k for k, s in enumerate(st) if s == "F"), kmax)
        if kn == 0: continue
        e = dict(a=a, b=b, h=h, kt=kt, kn=kn)
        jb, gap = None, None
        for j in range(b + 1, len(bars)):
            if bars[j] is None: gap = j; break
            if bars[j][1] > h: jb = j; break
        if gap is not None: e["status"] = "UNKNOWN_GAP"; e["gap"] = gap; out.append(e); continue
        if jb is None: e["status"] = "NO_UPDATE"; out.append(e); continue
        e["jb"] = jb
        res = bottom(bars, a, h, jb)
        if len(set(res)) == 1:
            m, j = res[0]
            e.update(status="KNOWN" if j > act else "PRE_ACTIVATION", jl=j, L=m)
            if e["status"] == "KNOWN" and oppv is not None:
                cats = set()
                for x in range(act + 1, len(bars)):
                    if bars[x] is None or bars[x][3] < oppv:
                        cats.add("BEFORE_L" if x < j else "BETWEEN_L_B" if x < jb else "INTACT_AT_B")
                        if bars[x] is not None: break
                else: cats.add("INTACT_AT_B")
                e["dr"] = cats.pop() if len(cats) == 1 else "UNKNOWN"
            elif e["status"] == "KNOWN": e["dr"] = "NA"
        else:
            e["status"] = "PRE_ACTIVATION" if all(j <= act for j, _ in possible_values(bars, a, h, jb)) else "UNKNOWN_INTRABAR"
        out.append(e)
    return out


def unique_density_zones(by_case, b_lo, b_hi, n_family):
    need = max(4, -(-n_family // 20))
    allc = {c for cs in by_case.values() for c in cs}
    if not allc: return [], need
    ks = [k for k, _ in allc]
    cells = [(k, b) for k in range(min(ks) - 1, max(ks) + 2) for b in range(b_lo, b_hi + 1)]
    near = {}
    for cid, cs in by_case.items():                     # every session counted once in every neighbourhood it touches
        for c in {(k + dk, b + db) for k, b in cs for dk in (-1, 0, 1) for db in (-1, 0, 1)}:
            near[c] = near.get(c, 0) + 1
    D = {c: near.get(c, 0) for c in cells}
    nbs = {c: [(c[0] + dk, c[1] + db) for dk in (-1, 0, 1) for db in (-1, 0, 1) if (dk or db) and (c[0] + dk, c[1] + db) in D] for c in cells}
    peaks = [c for c in cells if D[c] > 0 and all(D[c] >= D[n] for n in nbs[c])]
    zones = []
    for top in sorted({D[c] for c in peaks}, reverse=True):
        comp_of = {}                                       # the components of {2 D >= top}, grown breadth-first
        for c0 in cells:
            if c0 in comp_of or 2 * D[c0] < top: continue
            comp, queue = {c0}, [c0]
            while queue:
                c = queue.pop()
                for n in nbs[c]:
                    if n not in comp and 2 * D[n] >= top: comp.add(n); queue.append(n)
            for c in comp: comp_of[c] = comp
        done = set()
        for p in sorted(c for c in peaks if D[c] == top):
            comp = comp_of[p]
            if id(comp) in done: continue
            done.add(id(comp))
            if max(D[c] for c in comp) != top: continue
            members = sorted(cid for cid, cs in by_case.items() if cs & comp)
            if len(members) < need: continue
            apex = [c for c in comp if D[c] == top]
            zones.append(dict(cells=comp, members=members, top=top, anchor=min(apex, key=lambda c: (c[1], abs(2 * c[0] + 1), c[0]))))
    return zones, need


def check(proof, fam, B, day):
    h = check_history(proof, fam, B)
    t = check_today(proof, fam, day)
    errs = h["errors"] + t
    return dict(outcome="FAIL" if errs else "PASS", errors=errs, checked=h["checked"])


def check_history(proof, fam, B):
    errs, n = [], 0
    ctx, grid = proof["context"], proof["grid"]
    session = ctx["session"]
    start, formed, end = SESS[session]
    if grid != list(range(start + 5, end + 1, 5)): errs.append("grid")
    first = (formed - start) // 5
    kmax = max(proof["definition"]["scales"])
    members = {m["id"]: m for m in fam["members"]}
    if [s["id"] for s in proof["sessions"]] != [m["id"] for m in fam["members"]]: errs.append("sessions are not the family's members")
    fgrid = fam["grid"]
    ref_eps, ref_pts, unc_src = {}, {}, {}
    for s in proof["sessions"]:
        n += 1
        m = members.get(s["id"])
        if m is None: continue
        bars = base_bars(B, s["date"], session, s["direction"], s["edge_ticks"])
        if bars != s["bars"]: errs.append(f"{s['id']}: witness bars differ from the base"); continue
        path = [None if q is None else [q[2], q[1], q[3]] for q in bars[first:]]
        if [None if q is None else list(q) for q in m["path"]] != path or fgrid != grid[first:]: errs.append(f"{s['id']}: witness differs from the family path")
        act = grid.index(m["act"])
        if s["act"] != m["act"] or s["w"] != m["w"]: errs.append(f"{s['id']}: frame")
        eps = episodes_of(bars, first, act, s["oppv"], kmax)
        ref_eps[s["id"]] = eps
        for e in eps:
            if e["status"] == "KNOWN":
                key = (s["id"], e["jl"], e["L"])
                p = ref_pts.setdefault(key, dict(kt=0, kn=0, n=0, kts=[]))
                p["kt"] = max(p["kt"], e["kt"]); p["kn"] = max(p["kn"], e["kn"]); p["n"] += 1; p["kts"].append(e["kt"])
        unc_src[s["id"]] = (bars, act, s["w"])
    # episodes
    pub = {}
    for e in proof["episodes"]: pub.setdefault(e["case"], []).append(e)
    for cid, eps in ref_eps.items():
        got = pub.get(cid, [])
        if len(got) != len(eps): errs.append(f"{cid}: {len(got)} episodes published, {len(eps)} by the reference"); continue
        for g, r in zip(got, eps):
            for k in ("a", "b", "h", "kt", "kn", "status"):
                if g[k] != r[k]: errs.append(f"{cid} episode at {r['a']}: {k} {g[k]} != {r[k]}")
            for k in (("jl", "L", "jb", "dr") if r["status"] == "KNOWN" else ("jb",) if r["status"] != "UNKNOWN_GAP" else ()):
                if g.get(k) != r.get(k): errs.append(f"{cid} episode at {r['a']}: {k} {g.get(k)} != {r.get(k)}")
            if r["status"] == "UNKNOWN_INTRABAR":
                bars, act, w = unc_src[cid]
                cells = possible_cells(bars, r["a"], r["h"], r["jb"], act, w, formed, grid)
                pc = {((10 * x) // w, (grid[j] - 5 - formed) // 15) for j, lo, hi in g["cand"] for x in range(lo, hi + 1)}
                if cells != pc: errs.append(f"{cid} episode at {r['a']}: possible cells differ")
    # points
    pp = {(p["case"], p["i"], p["v"]): p for p in proof["points"]}
    if set(pp) != set(ref_pts): errs.append(f"points: {len(pp)} published, {len(ref_pts)} by the reference")
    for key, r in ref_pts.items():
        p = pp.get(key)
        if p is None: continue
        w = members[key[0]]["w"]
        if (p["k"], p["b"]) != ((10 * key[2]) // w, (grid[key[1]] - 5 - formed) // 15) or p["kt"] != r["kt"] or len(p["episodes"]) != r["n"]: errs.append(f"point {key}")
    # constellations at every scale
    N = fam["N"]
    win = (fam["key"]["window"][0] - formed) // 15
    for s in proof["definition"]["scales"]:
        zm = proof["maps"][str(s)]
        by_case = {}
        for (cid, i, v), r in ref_pts.items():
            if r["kt"] >= s: by_case.setdefault(cid, set()).add(((10 * v) // members[cid]["w"], (grid[i] - 5 - formed) // 15))
        zones, need = unique_density_zones(by_case, win, (end - 5 - formed) // 15, N)
        zones.sort(key=lambda z: (min(b for _, b in z["cells"]), -len(z["members"]), _near0(z["cells"])))
        if zm["need"] != need: errs.append(f"scale {s}: support")
        if len(zones) != len(zm["zones"]): errs.append(f"scale {s}: {len(zm['zones'])} zones published, {len(zones)} by the reference"); continue
        poss = possible_by_case(ref_eps, unc_src, ref_pts, members, s, grid, formed)
        for i, (z, r) in enumerate(zip(zm["zones"], zones)):
            if {tuple(c) for c in z["cell_mask"]} != r["cells"]: errs.append(f"scale {s} {z['label']}: cells")
            if z["members"] != r["members"] or z["n_known"] != len(r["members"]): errs.append(f"scale {s} {z['label']}: members")
            if z["label"] != f"L{i + 1}" or z["apex_D"] != r["top"] or list(z["anchor"]) != list(r["anchor"]): errs.append(f"scale {s} {z['label']}: order or apex")
            if z["zone_id"] != hashlib.sha1(f"{fam['snapshot_id']}|DR-LAB-PB-0.1|{s}|{list(r['anchor'])}".encode()).hexdigest()[:12]: errs.append(f"scale {s} {z['label']}: zone id")
            pos = sorted(c for c, cs in poss.items() if c not in r["members"] and cs & r["cells"])
            if z["possible"] != pos or z["n_possible"] != len(pos): errs.append(f"scale {s} {z['label']}: possible members")
            inside = [rp for (cid, i_, v), rp in ref_pts.items() if rp["kt"] >= s and ((10 * v) // members[cid]["w"], (grid[i_] - 5 - formed) // 15) in r["cells"]]
            if z["n_points"] != len(inside) or z["n_episodes"] != sum(1 for rp in inside for k in rp["kts"] if k >= s): errs.append(f"scale {s} {z['label']}: episode or point counts")
        inz = {c for z in zones for c in z["members"]}
        out_ = len([c for c in by_case if c not in inz]); unk = sum(1 for c, cs in poss.items() if c not in by_case and cs)
        if zm["sessions"] != dict(IN_ZONES=len(inz), OUTSIDE=out_, UNKNOWN=unk, NONE=N - len(inz) - out_ - unk): errs.append(f"scale {s}: session categories")
    return dict(outcome="FAIL" if errs else "PASS", errors=errs, checked=n)


def _near0(cells):
    k0, k1 = min(k for k, _ in cells), max(k for k, _ in cells) + 1
    return 0 if k0 <= 0 < k1 else k0 if k0 > 0 else -k1


def possible_by_case(ref_eps, unc_src, ref_pts, members, s, grid, formed):
    """Cells where a bottom could lie at scale s without being established: unknown episodes (tick by tick), known
    episodes whose vertex is undetermined at s, and every cell after a missing M5 of the trading window."""
    out = {}
    start = grid[0] - 5
    first = (formed - start) // 5
    for cid, eps in ref_eps.items():
        bars, act, w = unc_src[cid]
        cs = out.setdefault(cid, set())
        known = {((10 * v) // w, (grid[i] - 5 - formed) // 15) for (c, i, v), r in ref_pts.items() if c == cid and r["kt"] >= s}
        for e in eps:
            if e["kn"] < s: continue
            if e["status"] == "UNKNOWN_INTRABAR": cs |= possible_cells(bars, e["a"], e["h"], e["jb"], act, w, formed, grid)
            elif e["status"] == "KNOWN" and e["kt"] < s:
                c = ((10 * e["L"]) // w, (grid[e["jl"]] - 5 - formed) // 15)
                if c not in known: cs.add(c)
            elif e["status"] == "UNKNOWN_GAP":
                j0 = max(e["a"], act + 1)
                cap = min([bars[e["a"]][2] if (bars[e["a"]][0] == e["h"] or bars[e["a"]][3] == bars[e["a"]][2]) else bars[e["a"]][3]] + [bars[x][2] for x in range(e["a"] + 1, e["gap"])])
                last = next((x for x in range(e["gap"] + 1, len(bars)) if bars[x] is not None and bars[x][1] > e["h"]), len(bars) - 1)
                cs |= {("≤", (10 * cap) // w, b) for b in range((grid[j0] - 5 - formed) // 15, (grid[last] - 5 - formed) // 15 + 1)}
        g = next((j for j in range(first, len(bars)) if bars[j] is None), None)
        if g is not None:
            j0 = max(g, act + 1)
            if j0 < len(bars): cs |= {("*", None, b) for b in range((grid[j0] - 5 - formed) // 15, (grid[-1] - 5 - formed) // 15 + 1)}
    return {c: _Cells(cs) for c, cs in out.items() if cs}


class _Cells:
    """A set of exact cells plus half-planes ('≤', k, b: any cell of time b at or below k) and columns ('*', None, b)."""
    def __init__(self, items):
        self.items = items

    def __and__(self, cells):
        hit = set()
        for c in cells:
            if c in self.items: hit.add(c)
            elif ("*", None, c[1]) in self.items: hit.add(c)
            elif any(t[0] == "≤" and t[2] == c[1] and c[0] <= t[1] for t in self.items if isinstance(t[0], str)): hit.add(c)
        return hit

    def __bool__(self):
        return bool(self.items)


def check_today(proof, fam, day):
    errs = []
    T = proof["today"]
    ctx, grid = proof["context"], proof["grid"]
    session = ctx["session"]
    start, formed, end = SESS[session]
    first = (formed - start) // 5
    t = fam["today"]
    tick = float(day.get("tick") or 0.25)
    tk = lambda p: int(round(p / tick))
    side = t["side"]; d = side if fam["view"] == "conf" else -side
    e = tk(t["idrH"] if d == 1 else t["idrL"]); w = tk(t["idrH"] - t["idrL"])
    act_min = t["c0"] if fam["view"] == "conf" else t["brk"]
    oppv = d * (tk(t["drL"] if side == 1 else t["drH"]) - e) if fam["view"] == "conf" else None
    by = {int(b[0]) + 5: b for b in day["bars"]}
    bars = []
    for Tm in grid:
        if Tm > ctx["cut"]: break
        b = by.get(Tm)
        bars.append(None if b is None else _dir(tk(b[1]), tk(b[2]), tk(b[3]), tk(b[4]), d, e))
    if bars != T["bars"] or T["act"] != act_min or T["w"] != w or T["edge_ticks"] != e or T["oppv"] != oppv: return ["today: bars or frame differ from the day's candles"]
    act = grid.index(act_min)
    eps = episodes_of(bars, first, act, oppv, max(proof["definition"]["scales"]))
    if len(eps) != len(T["episodes"]): return [f"today: {len(T['episodes'])} episodes published, {len(eps)} by the reference"]
    for g, r in zip(T["episodes"], eps):
        st = "NOT_YET" if r["status"] == "NO_UPDATE" else r["status"]
        if (g["a"], g["h"], g["kt"], g["status"]) != (r["a"], r["h"], r["kt"], st): errs.append(f"today: episode at {r['a']}")
        if st == "KNOWN" and (g["jl"], g["L"], g["jb"], g.get("dr")) != (r["jl"], r["L"], r["jb"], r.get("dr")): errs.append(f"today: bottom of episode at {r['a']}")
    for s in proof["definition"]["scales"]:
        zs, rel = proof["maps"][str(s)]["zones"], T["zones"][str(s)]
        if len(zs) != len(rel): errs.append(f"today: relations at scale {s}"); continue
        for z, x in zip(zs, rel):
            cs = {tuple(c) for c in z["cell_mask"]}
            clock = "AHEAD" if ctx["cut"] <= z["time_start"] else "PAST" if ctx["cut"] >= z["time_end"] else "CURRENT"
            vis = None; gap = False
            for j in range(act + 1, len(bars)):
                b = (grid[j] - 5 - formed) // 15
                inb = [k for k, bb in cs if bb == b]
                if not inb: continue
                if bars[j] is None: gap = True; continue
                lo, hi = bars[j][2], bars[j][1]
                if any(10 * lo < (k + 1) * w and 10 * hi >= k * w for k in inb): vis = grid[j]; break
            want_v = dict(state="VISITED", close=vis) if vis else dict(state="UNKNOWN" if gap else "NOT_YET")
            done = [r for r in eps if r["status"] == "KNOWN" and r["kt"] >= s and ((10 * r["L"]) // w, (grid[r["jl"]] - 5 - formed) // 15) in cs]
            if (x["clock"], x["visit"]) != (clock, want_v): errs.append(f"today: clock or visit of {z['label']} at scale {s}")
            if done and (x["completion"]["state"] != "COMPLETED" or x["completion"]["b_close"] != min(grid[r["jb"]] for r in done)): errs.append(f"today: completion of {z['label']} at scale {s}")
            if not done and x["completion"]["state"] == "COMPLETED": errs.append(f"today: completion of {z['label']} at scale {s} without a completed episode")
    return errs
