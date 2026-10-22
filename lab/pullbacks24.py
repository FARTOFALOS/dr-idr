"""DR Lab screen 24 · the candidate «Откаты перед обновлением экстремума» (DR-LAB-PB-0.1).

Meaning: meaning/lens/2026-10-21-otkaty-do-obnovleniya/ — the construction (01), its review (02), the definition this
module implements (03) and the executor's answer (04). A separate candidate next to BASE-24 / NOW-1.0: it reads the
accepted family snapshot of lab/scene24.py (the same F, N, frame and activation, verified by lab/contract.py), never
changes it, and publishes its own envelope from the candidate registry (integration/candidates, DR-LAB-CANDIDATES-1).

The episode of one historical session, in the directed scale of the family on screen (u = d (p - e) / w; for a short
every price is mirrored, so «high» below is the directed high):
  vertex H  a run of consecutive M5 with one equal high h whose k neighbours on each side are all strictly lower
            (k = the scale of locality: 1 by the construction; 2, 3 and 6 to compare). It starts in the trading window;
            the box's candles serve as left context. It is recognisable at the close of its k-th right neighbour.
            A missing neighbour leaves the vertex undetermined at that scale.
  update B  the first M5 after the run whose high exceeds h (one tick is enough, a wick and a gap count; equality is a
            repeat of the vertex and does not complete). B is established at the close of its M5.
  bottom L  the deepest price between the first achievement of h and the first exceedance, and the first M5 that
            reached it. Inside the vertex M5 only its part after the high counts (its low may come before the high),
            inside the B M5 only its part before the exceedance. L is established only when every path compatible with
            the OHLC of those M5 gives the same price and the same M5 (else UNKNOWN_INTRABAR, no point is drawn).
            The bottom must lie after the close of the session's own activating M5; a deepest point at or before it
            excludes the episode (PRE_ACTIVATION): the path is never trimmed. A missing M5 between H and B leaves the
            episode unknown (UNKNOWN_GAP); a missing M5 after B changes nothing.
  no update the vertex was not exceeded until the block end (NO_UPDATE): not an episode of the map.
Nested episodes are kept; episodes with the same bottom (the same M5 and price) are one point with several links.
The DR break is a fact of the path: its order against L and B is kept (confirmation frame), never a filter.

The constellations (zone-map-3 geometry over these points, one vote per session): cells 0.1 IDR x 15 minutes by the
open of L's M5; D(cell) = the number of sessions with at least one point in the 3 x 3 neighbourhood (deduplicated over
the neighbourhood); a zone = the connected half-height region of its own apex holding at least max(4, ceil(0.05 N))
sessions. Its share = sessions with an established point inside / N of the family; sessions whose unknown episodes or
missing M5 could place a point inside give the upper bound; episodes and points are counted apart. Zones may share
sessions: the shares do not add up to 100 %.

Today: the same rule on today's closed M5 only (prefix honesty). For every zone: its window by the clock (ahead /
current / past), whether today's price visited it, whether a today's episode with its bottom in it is completed (the
update of its own vertex), or today's pullback stands in it with its vertex not yet updated. No R / X status applies.
"""
from __future__ import annotations

from collections import OrderedDict
import copy
import hashlib
import json
import math
from pathlib import Path
import threading

import numpy as np
from scipy import ndimage

import contract as C
import integration24 as I
import scene24 as S

VERSION = "DR-LAB-PB-0.1"
ROUTE = "/api/integration/pullbacks"
PROFILE = "PROFILE:PB-24"
SCALES = (1, 2, 3, 6)                 # neighbours on each side; 1 = the construction's choice (default)
KMAX = max(SCALES)
MIN_ABS, MIN_FRAC = 4, 0.05           # zone-map-3 support: max(4, ceil(0.05 N)) sessions
CATEGORIES = ("IN_ZONES", "OUTSIDE", "UNKNOWN", "NONE")   # the family's sessions at one scale, one 100 % of N
EIGHT = np.ones((3, 3), dtype=bool)
CODE_REVISION = hashlib.sha256(b"".join((Path(__file__).parent / p).read_bytes().replace(b"\r\n", b"\n")
                                        for p in ("pullbacks24.py", "pullbacks_ref.py"))).hexdigest()
_lock = threading.RLock()
_HIST = OrderedDict()                 # the historical part per family snapshot (never moved by the slice)
_OUT = OrderedDict()
_REF = OrderedDict()                  # the reference's verdict on the historical part, per snapshot


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def revision(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------------------------------------------------
# one session: bars, vertices, episodes
# ---------------------------------------------------------------------------------------------------------------------
def directed(r, d, e):
    """(o, h, l, c) of an M5 row (close minute, o, h, l, c; ticks) in directed ticks from the edge e; for a short the
    directed high is the physical low."""
    _, o, h, l, c = r
    return (o - e, h - e, l - e, c - e) if d == 1 else (e - o, e - l, e - h, e - c)


def block_grid(session):
    """The close minutes of every M5 of the block, the box first (day minutes)."""
    start, formed, end = S.SESS[session]
    return list(range(start + 5, end + 1, 5))


def _state(bars, idxs, h):
    """'T' all present and strictly lower, 'N' one missing (none higher or equal), 'F' one higher or equal / outside."""
    st = "T"
    for i in idxs:
        if i < 0 or i >= len(bars): return "F"
        q = bars[i]
        if q is None: st = "N"; continue
        if q[1] >= h: return "F"
    return st


def vertices(bars, first, kmax=KMAX):
    """Every run of equal highs that is (or may be) a vertex at scale 1. kt = the largest scale at which it is
    established, kn >= kt = the largest at which it may be (a missing neighbour): T* N* F* in the scale."""
    out, n, i = [], len(bars), 0
    while i < n:
        if bars[i] is None: i += 1; continue
        h, j = bars[i][1], i
        while j + 1 < n and bars[j + 1] is not None and bars[j + 1][1] == h: j += 1
        if i >= first:
            kt = kn = 0
            for k in range(1, kmax + 1):
                l, r = _state(bars, range(i - k, i), h), _state(bars, range(j + 1, j + 1 + k), h)
                s = "F" if "F" in (l, r) else "N" if "N" in (l, r) else "T"
                if s == "T" and kn == kt: kt = kn = k
                elif s != "F": kn = k
                else: break
            if kn: out.append(dict(a=i, b=j, h=int(h), kt=kt, kn=kn))
        i = j + 1
    return out


def _after_high(bar, h):
    """The possible minimum of the vertex M5 after its first high: exact when it opened at the high or closed at its
    low, else anywhere in [low, close]."""
    o, _, l, c = bar
    return (l, l) if (o == h or c == l) else (l, c)


def _before_exceed(bar, h):
    """The possible minimum of the update M5 before the exceedance: none when it opened beyond h (a gap), exact when it
    opened at its low, else anywhere in [low, open]."""
    o, _, l, _ = bar
    if o > h: return None
    return (l, l) if o == l else (l, o)


def first_bottom(segs):
    """segs: (M5 index, lowest possible minimum, highest possible minimum) of the parts of the path between the first
    achievement of h and the update, in time order. A part may hold the first deepest point only if its lowest value
    can be strictly below every earlier part and not above any later one. Returns (Lmin, Lmax, possible parts with the
    range of values they can hold as that first deepest point)."""
    n = len(segs)
    pre, suf = [None] * n, [None] * n
    m = None
    for i in range(n):
        pre[i] = m; m = segs[i][2] if m is None else min(m, segs[i][2])
    m = None
    for i in range(n - 1, -1, -1):
        suf[i] = m; m = segs[i][2] if m is None else min(m, segs[i][2])
    out = []
    for (j, lo, hi), p_, s_ in zip(segs, pre, suf):
        if (p_ is None or lo < p_) and (s_ is None or lo <= s_):
            top = min(x for x in (hi, s_, None if p_ is None else p_ - 1) if x is not None)
            out.append((j, lo, top))
    return min(s[1] for s in segs), min(s[2] for s in segs), out


def episode(bars, v, act):
    """The episode of one vertex: H -> L -> B, or why it is not established."""
    a, b, h, n = v["a"], v["b"], v["h"], len(bars)
    jb = None
    for j in range(b + 1, n):
        q = bars[j]
        if q is None:
            # a whole M5 missing before any observed exceedance: the update and the bottom may lie in it
            # before the gap the M5 are observed: there the bottom can only be the first deepest point of the observed
            # part (cand, after the own activation); at or after the gap it is anywhere, which the session's own
            # missing-M5 columns already cover (uncertainty)
            cap = min([_after_high(bars[a], h)[1]] + [bars[x][2] for x in range(a + 1, j)])
            last = next((x for x in range(j + 1, n) if bars[x] is not None and bars[x][1] > h), n - 1)
            _, _, seen = first_bottom([(a,) + _after_high(bars[a], h)] + [(x, bars[x][2], bars[x][2]) for x in range(a + 1, j)])
            return dict(status="UNKNOWN_GAP", gap=j, cap=int(cap), span=[a, last],
                        cand=[[s[0], int(s[1]), int(s[2])] for s in seen if s[0] > act])
        if q[1] > h: jb = j; break
    if jb is None: return dict(status="NO_UPDATE")
    segs = [(a,) + _after_high(bars[a], h)] + [(j, bars[j][2], bars[j][2]) for j in range(a + 1, jb)]
    tail = _before_exceed(bars[jb], h)
    if tail is not None: segs.append((jb,) + tail)
    lo, hi, cand = first_bottom(segs)
    if lo == hi and len(cand) == 1:
        jl = cand[0][0]
        return dict(status="KNOWN" if jl > act else "PRE_ACTIVATION", jl=jl, L=int(lo), jb=jb)
    if all(s[0] <= act for s in cand): return dict(status="PRE_ACTIVATION", jb=jb, ambiguous=True)
    return dict(status="UNKNOWN_INTRABAR", jb=jb, lo=int(lo), hi=int(hi), mixed=any(s[0] <= act for s in cand),
                cand=[[s[0], int(s[1]), int(s[2])] for s in cand if s[0] > act])


def break_order(bars, act, oppv, jl, jb):
    """Where the session's first DR break (an M5 closed strictly beyond its own opposite DR, after its activation) lies
    against L and B: BEFORE_L, BETWEEN_L_B (L, then the break, then the update), INTACT_AT_B (no break up to B: the
    break comes later or never) or UNKNOWN (a missing M5 could hold an earlier break). The break of L's own M5 is at
    its close, after L; the break of B's own M5 is at its close, after the exceedance."""
    cats = set()
    for j in range(act + 1, len(bars)):
        q = bars[j]
        if q is None:
            cats.add("BEFORE_L" if j < jl else "BETWEEN_L_B" if j < jb else "INTACT_AT_B")
            continue
        if q[3] < oppv:
            cats.add("BEFORE_L" if j < jl else "BETWEEN_L_B" if j < jb else "INTACT_AT_B")
            break
    else:
        cats.add("INTACT_AT_B")
    return cats.pop() if len(cats) == 1 else "UNKNOWN"


def first_break(bars, act, oppv):
    """(close index of the first observed break, known) after the activation; known = no M5 missing before it."""
    gap = False
    for j in range(act + 1, len(bars)):
        q = bars[j]
        if q is None: gap = True; continue
        if q[3] < oppv: return j, not gap
    return None, not gap


def analyse(bars, first, act, oppv=None, kmax=KMAX):
    """Every vertex of one session with its episode; the merged points of the established episodes."""
    eps, pts = [], OrderedDict()
    for v in vertices(bars, first, kmax):
        e = dict(v, **episode(bars, v, act))
        if e["status"] == "KNOWN":
            e["dr"] = "NA" if oppv is None else break_order(bars, act, oppv, e["jl"], e["jb"])
            p = pts.setdefault((e["jl"], e["L"]), dict(i=e["jl"], v=e["L"], links=[], kt=0, kn=0))
            p["links"].append(len(eps)); p["kt"] = max(p["kt"], e["kt"]); p["kn"] = max(p["kn"], e["kn"])
        eps.append(e)
    return eps, list(pts.values())


def gaps_from(bars, first):
    """The first missing M5 of the trading window, or None."""
    return next((j for j in range(first, len(bars)) if bars[j] is None), None)


# ---------------------------------------------------------------------------------------------------------------------
# the family: every member's episodes and points (the historical part; fixed at the family's snapshot)
# ---------------------------------------------------------------------------------------------------------------------
def cell(v, w):
    return (10 * v) // w


def tcell(open_minute, formed):
    return (open_minute - formed) // 15


def member_record(B, snap, m, session):
    """One member as a witness: its own bars over the whole block (box first), its frame and activation."""
    start, formed, end = S.SESS[session]
    i = B["idx"][(m["date"], session)]
    box = B["boxes"][i]
    d = snap["scale"]["orientation"]
    e = box["idr_high"] if d == 1 else box["idr_low"]
    rows = S._rows(B, i, S.SHIFT[session])
    bars = [list(directed(rows[T], d, e)) if T in rows else None for T in block_grid(session)]
    w = dict(id=m["id"], date=m["date"], w=int(m["w"]), direction=int(d), edge_ticks=int(e), act=int(m["act"]),
             oppv=int(m["oppv"]) if snap["view"] == "conf" else None, bars=bars)
    w["revision"] = revision(w)
    return w


def history(fam, B):
    """The historical part of the candidate for one verified family snapshot: witnesses, episodes, points."""
    key = (fam["snapshot_id"], fam["view"], fam["key"].get("scope"), CODE_REVISION)
    with _lock:
        if key in _HIST: return _HIST[key]
    session = fam["key"]["session"]
    start, formed, end = S.SESS[session]
    grid = block_grid(session)
    first = (formed - start) // 5
    sessions, episodes, points = [], [], []
    for m in fam["members"]:
        w = member_record(B, fam, m, session)
        act = grid.index(w["act"])
        eps, pts = analyse([tuple(q) if q else None for q in w["bars"]], first, act, w["oppv"])
        ids = []
        for e in eps:
            rec = dict(id=hashlib.sha1(f"{VERSION}|{fam['view']}|{w['id']}|{e['a']}|{e['h']}".encode()).hexdigest()[:16],
                       case=w["id"], a=e["a"], b=e["b"], h=e["h"], kt=e["kt"], kn=e["kn"], status=e["status"],
                       h_open=grid[e["a"]] - 5)
            if e.get("jb") is not None: rec.update(jb=e["jb"], b_close=grid[e["jb"]])
            if e["status"] == "KNOWN":
                rec.update(jl=e["jl"], L=e["L"], l_open=grid[e["jl"]] - 5, dr=e["dr"])
            elif e["status"] == "UNKNOWN_INTRABAR":
                rec.update(lo=e["lo"], hi=e["hi"], mixed=e["mixed"], cand=e["cand"])
            elif e["status"] == "UNKNOWN_GAP":
                rec.update(gap=e["gap"], cap=e["cap"], span=e["span"], cand=e["cand"])
            elif e.get("ambiguous"): rec["ambiguous"] = True
            ids.append(rec["id"]); episodes.append(rec)
        for p in pts:
            t = grid[p["i"]] - 5
            points.append(dict(id=f"{w['id']}|{p['i']}|{p['v']}", case=w["id"], i=p["i"], v=p["v"], open=t,
                               k=cell(p["v"], w["w"]), b=tcell(t, formed), kt=p["kt"], kn=p["kn"],
                               episodes=[ids[j] for j in p["links"]]))
        w["act_i"], w["first_i"] = act, first
        j, known = first_break([tuple(q) if q else None for q in w["bars"]], act, w["oppv"]) if w["oppv"] is not None else (None, True)
        w["brk"] = grid[j] if j is not None else None
        w["brk_known"] = bool(known)
        w["gap"] = gaps_from(w["bars"], first)
        sessions.append(w)
    out = dict(grid=grid, first=first, sessions=sessions, episodes=episodes, points=points)
    with _lock:
        _HIST[key] = out
        while len(_HIST) > 12: _HIST.popitem(last=False)
    return out


def uncertainty(H, fam, scale):
    """Per session: rectangles (b0, b1, k0, k1) of cells where an unestablished episode or a missing M5 could place
    a bottom at this scale (k0 / k1 None = unbounded price)."""
    session = fam["key"]["session"]
    start, formed, end = S.SESS[session]
    grid, out = H["grid"], {}
    known = {(p["case"], p["k"], p["b"]) for p in H["points"] if p["kt"] >= scale}
    w_of = {s["id"]: s for s in H["sessions"]}
    def add_candidates(R, cand, w):
        for j, lo, hi in cand:
            b = tcell(grid[j] - 5, formed)
            if lo is None or hi is None or w >= 10:
                R.append((b, b, cell(lo, w), cell(hi, w)))
            else:
                # A 0.1-IDR cell can be narrower than one tick (notably YM). The intervening cells then have no price.
                for k in sorted({cell(t, w) for t in range(lo, hi + 1)}): R.append((b, b, k, k))
    for e in H["episodes"]:
        if e["kn"] < scale: continue
        w = w_of[e["case"]]["w"]
        R = out.setdefault(e["case"], [])
        if e["status"] == "UNKNOWN_INTRABAR":
            add_candidates(R, e["cand"], w)
        elif e["status"] == "UNKNOWN_GAP":
            # the observed part before the gap: only its possible first deepest points; from the gap on, the session's
            # missing-M5 columns below (a later gap cannot move a bottom into earlier, observed time)
            add_candidates(R, e["cand"], w)
        elif e["status"] == "KNOWN" and e["kt"] < scale:
            k, b = cell(e["L"], w), tcell(e["l_open"], formed)
            if (e["case"], k, b) not in known: R.append((b, b, k, k))
    for s in H["sessions"]:
        if s["gap"] is not None:
            j0 = max(s["gap"], s["act_i"] + 1)
            if j0 < len(grid): out.setdefault(s["id"], []).append((tcell(grid[j0] - 5, formed), tcell(grid[-1] - 5, formed), None, None))
    return {k: v for k, v in out.items() if v}


def _hits(rects, cells):
    for b0, b1, k0, k1 in rects:
        for k, b in cells:
            if b0 <= b <= b1 and (k0 is None or k >= k0) and (k1 is None or k <= k1): return True
    return False


# ---------------------------------------------------------------------------------------------------------------------
# the constellations: zone-map-3 geometry, one vote per session in every neighbourhood
# ---------------------------------------------------------------------------------------------------------------------
def regions(cells_by_case, b_lo, b_hi):
    """The half-height regions of their own apex over D(cell) = the number of sessions with at least one point in the
    3 x 3 neighbourhood of the cell (each session dilated once, then summed: deduplicated over the neighbourhood)."""
    ks = [k for cs in cells_by_case.values() for k, _ in cs]
    if not ks: return [], None
    k_lo, k_hi = min(ks) - 1, max(ks) + 1
    D = np.zeros((k_hi - k_lo + 1, b_hi - b_lo + 1), dtype=np.int64)
    for cs in cells_by_case.values():
        A = np.zeros(D.shape, dtype=bool)
        for k, b in cs:
            if b_lo <= b <= b_hi: A[k - k_lo, b - b_lo] = True
        D += ndimage.binary_dilation(A, structure=EIGHT)
    peak = (D == ndimage.maximum_filter(D, size=3, mode="constant", cval=0)) & (D > 0)
    out, seen = [], set()
    for lam in sorted({D[i, j] / 2 for i, j in zip(*np.nonzero(peak))}, reverse=True):
        lab, _ = ndimage.label(D >= lam, structure=EIGHT)
        for i, j in zip(*np.nonzero(peak & (D == 2 * lam))):
            L = lab[i, j]
            if (lam, L) in seen: continue
            seen.add((lam, L))
            mask = lab == L
            if D[mask].max() != D[i, j]: continue
            cells = [(int(a) + k_lo, int(b) + b_lo) for a, b in zip(*np.nonzero(mask))]
            apex = [(int(a) + k_lo, int(b) + b_lo) for a, b in zip(*np.nonzero(mask & (D == D[i, j])))]
            out.append((cells, int(D[i, j]), apex))
    return out, (D, k_lo, b_lo)


def zone_map(H, fam, scale):
    """The zones of one scale: exact cell masks, established members (one vote per session), possible members, episode
    and point counts; the sessions' categories of N."""
    session = fam["key"]["session"]
    start, formed, end = S.SESS[session]
    N = fam["N"]
    need = max(MIN_ABS, math.ceil(MIN_FRAC * N))
    win = (fam["key"]["window"][0] - formed) // 15
    b_lo, b_hi = win, (end - 5 - formed) // 15
    pts = [p for p in H["points"] if p["kt"] >= scale]
    by_case = OrderedDict()
    for p in pts: by_case.setdefault(p["case"], set()).add((p["k"], p["b"]))
    unc = uncertainty(H, fam, scale)
    widths = {s["id"]: s["w"] for s in H["sessions"]}
    eps_known = {e["id"] for e in H["episodes"] if e["status"] == "KNOWN" and e["kt"] >= scale}
    regs, _ = regions(by_case, b_lo, b_hi)
    zones = []
    for cells, top, apex in regs:
        cs = set(cells)
        members = sorted(c for c, s in by_case.items() if s & cs)
        if len(members) < need: continue
        possible = sorted(c for c, R in unc.items() if c not in set(members) and _hits(R, {
            (k,b) for k,b in cs if math.ceil(k*widths[c]/10) < math.ceil((k+1)*widths[c]/10)
        }))
        inside = [p for p in pts if (p["k"], p["b"]) in cs]
        anchor = min(apex, key=lambda c: (c[1], abs(2 * c[0] + 1), c[0]))
        kk, bb = [c[0] for c in cells], [c[1] for c in cells]
        zones.append(dict(cell_mask=[list(c) for c in sorted(cs)], apex_D=top, anchor=list(anchor), members=members, possible=possible,
                          n_known=len(members), n_possible=len(possible), n_points=len(inside),
                          n_episodes=sum(1 for p in inside for e in p["episodes"] if e in eps_known),
                          price_low=min(kk), price_high=max(kk) + 1, time_start=formed + 15 * min(bb), time_end=formed + 15 * (max(bb) + 1)))
    near0 = lambda z: 0 if z["price_low"] <= 0 < z["price_high"] else z["price_low"] if z["price_low"] > 0 else -z["price_high"]
    zones.sort(key=lambda z: (z["time_start"], -z["n_known"], near0(z)))
    for i, z in enumerate(zones):
        z["label"] = f"L{i + 1}"
        z["zone_id"] = hashlib.sha1(f"{fam['snapshot_id']}|{VERSION}|{scale}|{z['anchor']}".encode()).hexdigest()[:12]
    used = {c for z in zones for c in z["members"]}
    cats = dict(IN_ZONES=len(used), OUTSIDE=len([c for c in by_case if c not in used]), UNKNOWN=sum(1 for c in unc if c not in by_case))
    cats["NONE"] = N - cats["IN_ZONES"] - cats["OUTSIDE"] - cats["UNKNOWN"]
    return dict(scale=scale, need=need, zones=zones, sessions=cats, points=len(pts), episodes=len(eps_known))


# ---------------------------------------------------------------------------------------------------------------------
# today: the same rule on the closed M5 up to the slice; three relations to every zone
# ---------------------------------------------------------------------------------------------------------------------
def pending(bars, v, act):
    """A recognised vertex not updated by the slice: the deepest price after its first high so far (provisional, never
    called completed), when the OHLC determine it; None otherwise."""
    a, h = v["a"], v["h"]
    segs = [(a,) + _after_high(bars[a], h)]
    for j in range(a + 1, len(bars)):
        if bars[j] is None: return None
        segs.append((j, bars[j][2], bars[j][2]))
    lo, hi, cand = first_bottom(segs)
    if lo != hi or len(cand) != 1 or cand[0][0] <= act: return None
    return dict(jl=cand[0][0], L=int(lo))


def today_frame(fam, day):
    """Today's directed frame of the family on screen (ticks): direction, edge, width, activation, opposite DR."""
    t = fam["today"]; tick = float(day.get("tick") or 0.25)
    tk = lambda p: int(round(p / tick))
    side, view = t["side"], fam["view"]
    d = side if view == "conf" else -side
    e_px = t["idrH"] if d == 1 else t["idrL"]
    opp = None
    if view == "conf": opp = d * (tk(t["drL"] if side == 1 else t["drH"]) - tk(e_px))
    return dict(d=d, e=tk(e_px), w=tk(t["idrH"] - t["idrL"]), act=t["c0"] if view == "conf" else t["brk"], oppv=opp, tick=tick)


def today_bars(day, session, cut, fr):
    """Today's closed M5 of the block up to the slice, directed; a slot without its M5 is None."""
    have = {int(b[0]) + 5: b for b in day["bars"]}
    tk = lambda p: int(round(p / fr["tick"]))
    out = []
    for T in block_grid(session):
        if T > cut: break
        b = have.get(T)
        out.append(None if b is None else list(directed((T, tk(b[1]), tk(b[2]), tk(b[3]), tk(b[4])), fr["d"], fr["e"])))
    return out


def today_part(fam, day, H, maps, cut):
    session = fam["key"]["session"]
    start, formed, end = S.SESS[session]
    fr = today_frame(fam, day)
    grid = H["grid"]
    bars = today_bars(day, session, cut, fr)
    act = grid.index(fr["act"])
    first = H["first"]
    tb = [tuple(q) if q else None for q in bars]
    eps, pend = [], []
    for v in vertices(tb, first):
        e = dict(v, **episode(tb, v, act))
        rec = dict(a=e["a"], b=e["b"], h=e["h"], kt=e["kt"], kn=e["kn"], status="NOT_YET" if e["status"] == "NO_UPDATE" else e["status"],
                   h_open=grid[e["a"]] - 5)
        if e.get("jb") is not None: rec.update(jb=e["jb"], b_close=grid[e["jb"]])
        if e["status"] == "KNOWN":
            rec.update(jl=e["jl"], L=e["L"], l_open=grid[e["jl"]] - 5, k=cell(e["L"], fr["w"]), cb=tcell(grid[e["jl"]] - 5, formed),
                       dr="NA" if fr["oppv"] is None else break_order(tb, act, fr["oppv"], e["jl"], e["jb"]))
        if e["status"] == "NO_UPDATE":
            p = pending(tb, v, act)
            if p: rec.update(jl=p["jl"], L=p["L"], l_open=grid[p["jl"]] - 5, k=cell(p["L"], fr["w"]), cb=tcell(grid[p["jl"]] - 5, formed))
        eps.append(rec)
    rel = {}
    for s, zm in maps.items():
        out = []
        for z in zm["zones"]:
            cs = {tuple(c) for c in z["cell_mask"]}
            bset = {b for _, b in cs}
            clock = "AHEAD" if cut <= z["time_start"] else "PAST" if cut >= z["time_end"] else "CURRENT"
            visit, gap = None, False
            for j in range(act + 1, len(tb)):
                b = tcell(grid[j] - 5, formed)
                if b not in bset: continue
                q = tb[j]
                if q is None: gap = True; continue
                if any(k2 == b and 10 * q[2] < (k + 1) * fr["w"] and 10 * q[1] >= k * fr["w"] for k, k2 in cs):
                    visit = grid[j]; break
            done = [e for e in eps if e["status"] == "KNOWN" and e["kt"] >= s and (e["k"], e["cb"]) in cs]
            wait = [e for e in eps if e["status"] == "NOT_YET" and e["kt"] >= s and e.get("L") is not None and (e["k"], e["cb"]) in cs]
            comp = dict(state="COMPLETED", b_close=min(e["b_close"] for e in done), h_open=min(done, key=lambda e: e["b_close"])["h_open"]) if done else \
                dict(state="IN_ZONE_NOT_UPDATED", h_open=max(e["h_open"] for e in wait)) if wait else dict(state="NONE")
            out.append(dict(zone_id=z["zone_id"], clock=clock, visit=dict(state="VISITED", close=visit) if visit else dict(state="UNKNOWN" if gap else "NOT_YET"),
                            completion=comp))
        rel[str(s)] = out
    return dict(cut=cut, act=fr["act"], direction=fr["d"], w=fr["w"], edge_ticks=fr["e"], oppv=fr["oppv"], bars=bars, episodes=eps, zones=rel)


# ---------------------------------------------------------------------------------------------------------------------
# the publication: one proof (definition, context, witnesses, episodes, points, maps, today), its independent check,
# its envelope from the candidate registry
# ---------------------------------------------------------------------------------------------------------------------
def marginal_regions(H, fam, scale, cut, extra=None):
    """Membership of sessions, not episode counts. Bins can share the same session.
    Earlier = all its established bottoms in the region closed by cut; later = at least one did not.
    Unknown membership remains a separate upper bound and never becomes an absence."""
    pts = [p for p in H["points"] if p["kt"] >= scale]
    unc = uncertainty(H, fam, scale)
    ks = sorted({p["k"] for p in pts})
    nb = (S.SESS[fam["key"]["session"]][2] - S.SESS[fam["key"]["session"]][1]) // 15
    regions_ = [(k, k + 1, None, None) for k in ks]
    regions_ += [(None, k + 1, None, None) for k in ks] + [(k, None, None, None) for k in ks]
    regions_ += [(None, None, b, b + 1) for b in range(nb)]
    formed = S.SESS[fam["key"]["session"]][1]
    regions_ += [(None, None, (z["time_start"] - formed) // 15, (z["time_end"] - formed) // 15) for z in H["maps"][scale]["zones"] + fam.get("zones", {}).get("X", {}).get("zones", [])]
    if extra:
        regions_ += [tuple(extra), (extra[0], extra[1], None, None), (None, None, extra[2], extra[3])]
    out, seen = [], set()
    for k0, k1, b0, b1 in regions_:
        key = (k0, k1, b0, b1)
        if key in seen: continue
        seen.add(key)
        inside = lambda p: (k0 is None or p["k"] >= k0) and (k1 is None or p["k"] < k1) and (b0 is None or p["b"] >= b0) and (b1 is None or p["b"] < b1)
        use = [p for p in pts if inside(p)]
        members = sorted({p["case"] for p in use})
        later = {p["case"] for p in use if p["open"] + 5 > cut}
        def overlaps(R, w):
            if k0 is not None and k1 is not None and math.ceil(k0*w/10) >= math.ceil(k1*w/10): return False
            return any((b0 is None or rb1 >= b0) and (b1 is None or rb0 < b1) and
                       (k0 is None or rk1 is None or rk1 >= k0) and (k1 is None or rk0 is None or rk0 < k1)
                       for rb0, rb1, rk0, rk1 in R)
        weights = {w["id"]: w["w"] for w in H["sessions"]}
        possible = sorted(c for c, R in unc.items() if c not in members and overlaps(R, weights[c]))
        out.append(dict(k0=k0, k1=k1, b0=b0, b1=b1, members=members, possible=possible,
                        n_known=len(members), n_possible=len(possible), earlier=len(members) - len(later), later=len(later)))
    return out


def build(inst, session, cut, date=None, view="auto", scope="weekday", region=None):
    """The proof of one scene, before its gate. Returns (status, fam, B, day, proof)."""
    view_arg = view + (":all" if scope == "all" else "")
    raw, B, day = S._family(inst, session, cut, date, view_arg)
    if raw.get("status") != "ok" or "today" not in raw or not raw["today"].get("c0"):
        return raw.get("status") or "NO_FAMILY", None, B, day, None
    fam = C.attach_family(raw, inst, B, day, dict(instrument=inst, session=session, at=cut, date=date, view=view_arg))
    if fam.get("status") != "ok" or fam["contract"]["status"] != "CONFORMANT": return "FAMILY_NOT_PUBLISHED", fam, B, day, None
    if not fam["N"]: return "EMPTY_FAMILY", fam, B, day, None
    H = history(fam, B)
    maps = H.setdefault("maps", {})
    for s in SCALES:
        if s not in maps: maps[s] = zone_map(H, fam, s)
    today = today_part(fam, day, H, maps, cut)
    tick = float(day.get("tick") or 0.25)
    from revisions24 import prefix_revision
    start, formed, end = S.SESS[session]
    context = dict(instrument=inst, date=day["date"], session=session, cut=cut, view=fam["view"], scope=scope,
                   family_id=fam["family_id"], snapshot_id=fam["snapshot_id"], N=fam["N"], cond=fam["cond"],
                   case_set=C.case_set_spec_of(fam), formed=formed, end=end, prefix_revision=prefix_revision(day["bars"], cut, tick),
                   code_revision=CODE_REVISION, registry_hash=I.review_gate().registry_hash(), base_registry_hash=C.registry_hash())
    definition = dict(version=VERSION, scales=list(SCALES), default_scale=SCALES[0], min_abs=MIN_ABS, min_frac_num=1, min_frac_den=20,
                      grid="GRID:K10-J15-1", density="ONE_VOTE_PER_SESSION_IN_3X3", exceed="STRICT_ONE_TICK_WICK_AND_GAP",
                      bottom="ALL_OHLC_COMPATIBLE_PATHS_SAME_PRICE_AND_M5", activation="BOTTOM_AFTER_OWN_ACTIVATION_CLOSE_NO_TRIM")
    proof = dict(definition=definition, context=context, grid=H["grid"], first_i=H["first"], sessions=H["sessions"],
                 episodes=H["episodes"], points=H["points"], maps={str(s): maps[s] for s in SCALES}, today=today,
                 marginals={str(s): marginal_regions(H, fam, s, cut, region) for s in SCALES})
    return "OK", fam, B, day, proof


def publish(proof, fam, check):
    gate = I.review_gate()
    ctx = proof["context"]
    env = gate.Envelope(ROUTE, PROFILE, dict(instrument=ctx["instrument"], session=ctx["session"], cut=ctx["cut"], date=ctx["date"], view=ctx["view"], scope=ctx["scope"]))
    env.check("independent re-derivation of every episode, point, zone and today's relations (lab/pullbacks_ref.py)", check["outcome"] == "PASS", check.get("checked"))
    if check["outcome"] != "PASS":
        env.violate("PULLBACK_REFERENCE_MISMATCH", ["E1", "P1", "V2"], "; ".join(check["errors"][:5]), withheld=["EST:PB-ZONE", "EST:PB-SESSIONS", "EST:PB-REGION"])
        return dict(status="REFERENCE_MISMATCH", contract=env.finish(), message="Эпизоды или созвездия не подтвердились независимым пересчётом: слой снят")
    release_id = revision(proof)
    N, cs_id, sid = ctx["N"], ctx["case_set"], ctx["snapshot_id"]
    inputs = gate._inputs(fam, [dict(input_kind="CODE", ref=VERSION, version=CODE_REVISION), dict(input_kind="PARAMETERS", ref="release", version=release_id)])
    for s in SCALES:
        zm = proof["maps"][str(s)]
        for v in proof["marginals"][str(s)]:
            yes, unknown = v["n_known"], v["n_possible"]
            est = [dict(estimator="ESTR:PB-REGION", value_kind="POINT", value=yes / N, numerator=yes, denominator=N, unit="share of N_base")]
            if unknown: est.append(dict(estimator="ESTR:PB-REGION", value_kind="BOUNDS", lower=yes / N, upper=(yes + unknown) / N, denominator=N, unit="share of N_base"))
            env.bundle("EST:PB-REGION", cs_id, sid, "lab/pullbacks24.py::marginal_regions", inputs, est,
                       [dict(case_set=sid, n_base=N, components=[dict(component="MEMBERSHIP", of=N, yes=yes, unknown=unknown, no=N-yes-unknown)])],
                       dict(yes=yes, unknown=unknown, N=N, scale=s),
                       parameters=dict(scale=s, **{k:v[k] for k in ("k0", "k1", "b0", "b1")}, release=release_id))
        for z in zm["zones"]:
            est = [dict(estimator="ESTR:PB-ZONE", value_kind="POINT", value=z["n_known"] / N, numerator=z["n_known"], denominator=N, unit="share of N_base")]
            if z["n_possible"]: est.append(dict(estimator="ESTR:PB-ZONE", value_kind="BOUNDS", lower=z["n_known"] / N, upper=(z["n_known"] + z["n_possible"]) / N, denominator=N, unit="share of N_base"))
            env.bundle("EST:PB-ZONE", cs_id, sid, "lab/pullbacks24.py::zone_map", inputs, est,
                       [dict(case_set=sid, n_base=N, components=[dict(component="MEMBERSHIP", of=N, yes=z["n_known"], unknown=z["n_possible"], no=N - z["n_known"] - z["n_possible"])])],
                       dict(yes=z["n_known"], N=N, label=z["label"], unknown=z["n_possible"], episodes=z["n_episodes"], scale=s),
                       parameters=dict(zone_id=z["zone_id"], label=z["label"], scale=s, episodes=z["n_episodes"], points=z["n_points"], release=release_id))
        c = zm["sessions"]
        env.bundle("EST:PB-SESSIONS", cs_id, sid, "lab/pullbacks24.py::zone_map", inputs,
                   [dict(estimator="ESTR:PB-SESSIONS", value_kind="CATEGORY_SHARES", unit="categories of N_base", denominator=N,
                         categories=[dict(category=k, count=int(c[k])) for k in CATEGORIES])],
                   [dict(case_set=sid, n_base=N, components=[dict(component="CATEGORY", of=N, known=N - c["UNKNOWN"], unknown=c["UNKNOWN"])])],
                   dict(N=N, in_zones=c["IN_ZONES"], outside=c["OUTSIDE"], unknown=c["UNKNOWN"], none=c["NONE"], scale=s, episodes=zm["episodes"]),
                   parameters=dict(scale=s, episodes=zm["episodes"], points=zm["points"], release=release_id))
    out = dict(status="OK", release_id=release_id, proof=proof, contract=env.finish(),
               review=dict(decision="CANDIDATE", human_acceptance="PENDING", edition=I.REVIEW_EDITION))
    if out["contract"]["status"] != "CONFORMANT":
        return dict(status="CONTRACT_VIOLATION", contract=out["contract"], message="Ответ не прошёл проверку контракта")
    return gate.finalize(ROUTE, out)


def response(params):
    inst, session = params.get("instrument", "NQ"), params.get("session", "RDR")
    date = params.get("date") or None
    view, scope = params.get("view", "auto"), params.get("scope", "weekday")
    if inst not in ("NQ", "ES", "YM") or session not in S.SESS: return dict(status="OUT_OF_SCOPE", message="Инструмент или блок вне кандидата")
    if view not in ("auto", "conf") or scope not in S.SCOPES: raise ValueError("view: auto | conf; scope: weekday | all")
    if date and date > "2025-12-31": return dict(status="OUT_OF_SCOPE", message="История после 2025 закрыта")
    cut = int(params["at"])
    region = json.loads(params["region"]) if params.get("region") else None
    if region is not None and (not isinstance(region, list) or len(region) != 4 or any(x is not None and (type(x) is not int or abs(x) > 100000) for x in region)):
        raise ValueError("region: four integer or null bounds")
    if region is not None and any(region[i] is not None and region[i+1] is not None and region[i] >= region[i+1] for i in (0,2)):
        raise ValueError("region: lower bound must precede upper bound")
    if cut % 5: raise ValueError("только закрытые M5")
    gate = I.review_gate()
    if C.stale() or gate.stale(): return dict(status="CONTRACT_STALE", message="Реестр изменился: слой снят")
    with _lock:
        status, fam, B, day, proof = build(inst, session, cut, date, view, scope, region)
        if status != "OK": return dict(status=status, message={"NO_FAMILY": "Нужно подтверждение и семья", "FAMILY_NOT_PUBLISHED": "Семья не опубликована шлюзом SC-1.1",
                                                               "EMPTY_FAMILY": "В семье нет сессий"}.get(status, "Семьи нет: " + str(status)))
        key = revision([proof["context"], proof["today"]["bars"], region])
        if key in _OUT: return _OUT[key]
        import pullbacks_ref as R
        # the historical part is re-derived once per snapshot (it never moves with the slice); today's part every time
        hkey = (proof["context"]["snapshot_id"], proof["context"]["view"], proof["context"]["scope"], CODE_REVISION)
        if hkey not in _REF:
            _REF[hkey] = R.check_history(proof, fam, B)
            while len(_REF) > 12: _REF.popitem(last=False)
        h, t = _REF[hkey], R.check_today(proof, fam, day)
        m = R.check_marginals(proof, fam)
        check = dict(outcome="FAIL" if h["errors"] or t or m else "PASS", errors=h["errors"] + t + m, checked=h["checked"])
        out = publish(proof, fam, check)
        _OUT[key] = out
        while len(_OUT) > 6: _OUT.popitem(last=False)
        return out
