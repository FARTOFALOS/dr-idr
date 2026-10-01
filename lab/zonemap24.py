"""DR Lab design 24 — the zone map of R and X, `zone-map-3`: DR-LAB-ZONE-MAP-2.0 with the corrections of its audit
(meaning/lens/2026-10-01-zone-map-2/otvet-auditora.md), adopted by the operator on 01.10.2026. Meaning: meaning/12.

One rule makes the zones; it replaces V2's watershed, merge and floor:
  D(cell) = the number of the family's known events of one kind (R or X) in the 3 x 3 cells around a cell of the grid
  0.1 width x 15 minutes, at every cell, empty ones included. A zone is a connected region of cells (8-neighbourhood)
  whose D is at least half of the region's own maximum and which holds no cell above that maximum: the half-height
  region of its own apex.
Consequences, each a property of superlevel sets rather than a convention:
  - a region is continuous: a cell where history had no event but its neighbours did belongs to it when its D does;
  - two concentrations are separate zones when the valley between them falls below half of each of them; a valley
    above half of the higher one makes them one ridge; a bump whose valley lies between the two halves is a shoulder
    of the higher one and stays outside its half-height region;
  - regions never overlap, and no step needs a tie-break: a component of a superlevel set is a set.
A region is a zone only with at least max(4, ceil(0.05 N)) sessions; every other known event is the residual. The share
of a zone is its sessions / N; unknown and no-event stay in N and never receive a place.

Diagnostics are properties of a zone, never a permission to exist: the same zone on three shifted grids and on
resampled sessions (Jaccard of member sets), and a path-null measured on sessions that did not shape the zone (the
older half finds the region, the newer half is compared with sign-flipped copies of its own paths).
Today's status of a zone (HOLDS / POSSIBLE / IMPOSSIBLE) follows the reachable set of the final event (§23-24 of V2).
"""
from __future__ import annotations

import hashlib
import math

import numpy as np
from scipy import ndimage

VERSION = "zone-map-3"
NULL_MODEL = "sign-flip-1"           # each M5 after the session's own activation reflected about the previous close
RATIO = 0.5                          # the half height
MIN_ABS, MIN_FRAC = 4, 0.05          # the minimum support
SHIFTS = ((1, 0), (0, 5), (0, 10))   # half price cell, minutes (V2 §30)
BOOT, NULL_REPS, YEAR_BOOT = 50, 200, 200
EIGHT = np.ones((3, 3), dtype=int)
# Research figures (studies/zone_map_3_2026_10_01, targets 2018-2025, weekday maps; exploratory, the corpus was seen):
# how often a zone of each status was realised, 30 / 60 / 120 minutes after the confirmation. Shown only in the research
# details of a zone (meaning/12 §4), never as today's chance.
STUDY = {"ADR R": ((29.1, 42.7, 63.5), (4.1, 4.2, 4.8)), "ADR X": ((34.5, 48.8, 66.7), (3.3, 3.5, 3.9)),
         "ODR R": ((27.9, 40.5, 60.8), (5.4, 5.7, 6.0)), "ODR X": ((32.9, 47.8, 65.9), (4.0, 4.1, 4.4)),
         "RDR R": ((31.7, 46.1, 62.9), (5.4, 5.5, 5.6)), "RDR X": ((26.6, 40.7, 56.5), (5.9, 6.5, 7.2))}


def study_refs(session, e):
    h, p = STUDY.get(f"{session} {e}", (None, None))
    if h is None: return None
    f = lambda v: " / ".join(f"{x:g}".replace(".", ",") for x in v)
    return dict(study_id="zone_map_3_2026_10_01", period="2018-2025",
                text=f"исследование 2018–2025 (разведка, не шанс на сегодня; карты по дню недели): «держится» сбывалась в {f(h)} %, "
                     f"«возможна» — в {f(p)} %, «невозможна» — ни разу (через 30 / 60 / 120 минут после подтверждения)")


def seed(*parts):
    """§23: every random procedure is seeded from the version, the family, the snapshot, the event and the test."""
    return int(hashlib.sha256("|".join(map(str, (VERSION,) + parts)).encode()).hexdigest()[:15], 16)


def cell_of(v, w, t, formed, dk=0, dt=0):
    """The price and time cell of an event (directed ticks v on width w, open minute t) on a grid shifted by dk half
    price cells and dt minutes."""
    return (20 * v - dk * w) // (2 * w), (t - formed - dt) // 15


def regions(pts, b_lo, b_hi):
    """The zone regions of a set of event cells (with multiplicity) on the time cells b_lo..b_hi. Returns a list of
    (cells, apex D, apex cells); no minimum support yet."""
    if not pts: return []
    ks = [p[0] for p in pts]
    k_lo, k_hi = min(ks) - 1, max(ks) + 1
    A = np.zeros((k_hi - k_lo + 1, b_hi - b_lo + 1), dtype=np.int64)
    for k, b in pts:
        if b_lo <= b <= b_hi: A[k - k_lo, b - b_lo] += 1
    D = ndimage.correlate(A, EIGHT, mode="constant", cval=0)
    peak = (D == ndimage.maximum_filter(D, size=3, mode="constant", cval=0)) & (D > 0)
    out, seen = [], set()
    for lam in sorted({D[i, j] / 2 for i, j in zip(*np.nonzero(peak))}, reverse=True):
        lab, _ = ndimage.label(D >= lam, structure=EIGHT)
        for i, j in zip(*np.nonzero(peak & (D == 2 * lam))):
            L = lab[i, j]
            if (lam, L) in seen: continue
            seen.add((lam, L))
            mask = lab == L
            if D[mask].max() != D[i, j]: continue                      # a higher cell inside: not its own apex
            cells = [(int(a) + k_lo, int(b) + b_lo) for a, b in zip(*np.nonzero(mask))]
            apex = [(int(a) + k_lo, int(b) + b_lo) for a, b in zip(*np.nonzero(mask & (D == D[i, j])))]
            out.append((cells, int(D[i, j]), apex))
    return out


def zone_map(points, N, b_lo, b_hi):
    """points: [(k, b, session_id)] the known events (one per session); N: the whole family. Zones ordered by start
    time, then share, then nearness to u = 0 (V2 §21); the residual is every known session outside them."""
    need = max(MIN_ABS, math.ceil(MIN_FRAC * N))
    where = {}
    for k, b, sid in points: where.setdefault((k, b), []).append(sid)
    zones, used = [], set()
    for cells, top, apex in regions([(k, b) for k, b, _ in points], b_lo, b_hi):
        members = sorted({s for c in cells for s in where.get(c, ())})
        if len(members) < need: continue
        cs = set(cells)
        anchor = min(apex, key=lambda c: (c[1], abs(2 * c[0] + 1), c[0]))      # V2 §11: the canonical peak anchor
        k0, k1 = min(c[0] for c in cells), max(c[0] for c in cells) + 1
        zones.append(dict(cells=sorted(cs), members=members, n=len(members), apex_D=top, anchor=anchor,
                          price=[k0, k1], time=[min(c[1] for c in cells), max(c[1] for c in cells) + 1]))
        used.update(members)
    near0 = lambda z: 0 if z["price"][0] <= 0 < z["price"][1] else z["price"][0] if z["price"][0] > 0 else -z["price"][1]
    zones.sort(key=lambda z: (z["time"][0], -z["n"], near0(z)))
    return dict(zones=zones, residual=sorted({s for _, _, s in points} - used), need=need)


def _jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 0.0


def _match(zone, other):
    """The zone of another map that shares most members (Jaccard of member sets); ties: the earlier, then nearer 0."""
    best = 0.0
    for z in other["zones"]:
        best = max(best, _jaccard(zone["members"], z["members"]))
    return best


def _flip(path, act_i, rng, reps, e):
    """Sign-flip copies of one session (the null of the synthesis §11): every M5 after the activation reflected with
    p = 1/2 about the previous synthetic close. Returns (values, indices) of the R (min low) or X (max high) per copy."""
    seg = path[act_i + 1:]
    c0 = path[act_i, 2]
    prev = np.concatenate([[c0], seg[:-1, 2]])
    dL, dH, dC = seg[:, 0] - prev, seg[:, 1] - prev, seg[:, 2] - prev
    eps = rng.choice((-1.0, 1.0), size=(reps, len(seg)))
    cl = c0 + np.cumsum(eps * dC, axis=1)
    pv = np.concatenate([np.full((reps, 1), c0), cl[:, :-1]], axis=1)
    lo = pv + np.where(eps > 0, dL, -dH)
    hi = pv + np.where(eps > 0, dH, -dL)
    return (lo.min(1), lo.argmin(1)) if e == "R" else (hi.max(1), hi.argmax(1))


def map_of(members, e, formed, end, win, ids, dk=0, dt=0, weights=None):
    """The zone map of event e for snapshot members (scene24 records), optionally on a shifted grid or with resampling
    weights (a session counted w times)."""
    pts = []
    for i, m in enumerate(members):
        x = m[e]
        if x["s"] != "known": continue
        k, b = cell_of(x["v"], m["w"], x["t"], formed, dk, dt)
        for _ in range(1 if weights is None else int(weights[i])): pts.append((k, b, ids[i]))
    t_first, t_last = formed + 15 * win + 5, end - 5
    return zone_map(pts, len(members) if weights is None else int(sum(weights)), (t_first - formed - dt) // 15, (t_last - formed - dt) // 15)


def evaluate(snap, e):
    """The zone map of one event of a snapshot of lab/scene24.py, with every zone's passport and diagnostics."""
    mem, sch = snap["members"], snap["schedule"]
    formed, end = sch["formed"], sch["end"]
    win = (snap["key"]["window"][0] - formed) // 15
    ids = [m["id"] for m in mem]
    N = len(mem)
    zm = map_of(mem, e, formed, end, win, ids)
    unknown = sum(1 for m in mem if m[e]["s"] == "unknown")
    none = sum(1 for m in mem if m[e]["s"] == "none")
    base = dict(algorithm_version=VERSION, family_scope=snap["key"].get("scope", "weekday"), family_id=snap["family_id"],
                snapshot_id=snap["snapshot_id"], event_id=e, N_family=N, n_residual_total=len(zm["residual"]),
                unknown_count=unknown, no_event_count=none, min_support=zm["need"], study_refs=study_refs(snap["key"]["session"], e))
    # diagnostics on the whole map (once per event)
    shifted = [map_of(mem, e, formed, end, win, ids, dk, dt) for dk, dt in SHIFTS]
    rng = np.random.default_rng(seed(snap["family_id"], snap["snapshot_id"], e, "bootstrap"))
    boots = [map_of(mem, e, formed, end, win, ids, weights=rng.multinomial(N, np.full(N, 1 / N))) for _ in range(BOOT)] if N else []
    older = mem[:N // 2]
    disc = map_of(older, e, formed, end, win, ids[:N // 2]) if len(older) else dict(zones=[])
    newer = [m for m in mem[N // 2:] if m[e]["s"] == "known"]
    grid = np.array(snap["grid"])
    zones = []
    for z_i, z in enumerate(zm["zones"]):
        label = f"{e}{z_i + 1}"
        zid = hashlib.sha1("|".join(map(str, (snap["snapshot_id"], e, z["anchor"], VERSION))).encode()).hexdigest()[:12]
        jac = [round(_match(z, s), 3) for s in shifted]
        rec = [_match(z, b) for b in boots]
        out = dict(base, zone_id=zid, label=label, peak_anchor=list(z["anchor"]), cell_mask=[list(c) for c in z["cells"]],
                   price_low=z["price"][0], price_high=z["price"][1], time_start=formed + 15 * z["time"][0], time_end=formed + 15 * z["time"][1],
                   member_session_ids=z["members"], n_zone=z["n"], p_snapshot=z["n"] / N if N else None,
                   grid_member_jaccard=dict(price_half=jac[0], time_5=jac[1], time_10=jac[2], min=min(jac)),
                   bootstrap_recovery=dict(mean=round(float(np.mean(rec)), 3) if rec else None,
                                           share_ge_half=round(float(np.mean([r >= 0.5 for r in rec])), 3) if rec else None, of=len(rec)))
        out.update(_null(z, disc, newer, grid, formed, e, snap, z_i))
        zones.append(out)
    return dict(base, zones=zones, residual_ids=zm["residual"],
                residual_share=len(zm["residual"]) / N if N else None)


def _null(z, disc, newer, grid, formed, e, snap, z_i):
    """§33.1 on held-out sessions: the older half's zone overlapping this one most (cells) is frozen; the newer half's
    known events are compared with sign-flipped copies of their own paths in that frozen region."""
    out = dict(null_model_id=NULL_MODEL)
    cs = set(map(tuple, z["cells"]))
    best, frozen = 0.0, None
    for d in disc["zones"]:
        j = _jaccard(cs, set(map(tuple, d["cells"])))
        if j > best: best, frozen = j, set(map(tuple, d["cells"]))
    if frozen is None:
        return dict(out, null_status="not_applicable: the older half has no zone at this place")
    if len(newer) < 10:
        return dict(out, null_status="not_applicable: fewer than 10 known events in the newer half")
    rng = np.random.default_rng(seed(snap["family_id"], snap["snapshot_id"], e, z_i, "null"))
    real, H = [], []
    for m in newer:
        x = m[e]
        real.append(cell_of(x["v"], m["w"], x["t"], formed) in frozen)
        P = np.array([q if q is not None else [np.nan] * 3 for q in m["path"]], dtype=float)
        ai = int(np.searchsorted(grid, m["act"]))
        vals, idx = _flip(P, ai, rng, NULL_REPS, e)
        t = grid[ai + 1 + idx] - 5
        k = np.floor_divide(10 * vals.astype(np.int64), m["w"])
        b = (t - formed) // 15
        H.append(np.array([(int(kk), int(bb)) in frozen for kk, bb in zip(k, b)]))
    real = np.array(real, dtype=float); H = np.array(H, dtype=float)
    q_null = H.mean(0)
    p_real, p_null = float(real.mean()), float(np.median(q_null))
    yrs = np.array([int(m["date"][:4]) for m in newer]); uy = np.unique(yrs)
    yr = np.random.default_rng(seed(snap["family_id"], snap["snapshot_id"], e, z_i, "null-years"))
    ex = []
    for _ in range(YEAR_BOOT):
        wts = np.zeros(len(newer))
        for y in yr.choice(uy, len(uy)): wts += yrs == y
        ex.append((wts @ real) / wts.sum() - np.median((wts @ H) / wts.sum()))
    return dict(out, null_status="measured", null_frozen_overlap=round(best, 3), null_validation_n=len(newer),
                p_real_mask=round(p_real, 4), p_null_mask=round(p_null, 4), null_excess=round(p_real - p_null, 4),
                null_interval=[round(float(x), 4) for x in np.percentile(ex, [5, 95])],
                minimum_detectable_excess=round(float(np.percentile(q_null, 95) - p_null), 4))


def status(cells, e, q, v10, w, t_next, formed, last_open):
    """Today's status of one zone (V2 §23-24, the slice convention of zone-map-3: t_next = the close of the last closed
    M5, the earliest open of a new extreme). q = the cell of today's provisional pair, v10 = 10 x its directed value;
    q = None before the first M5 after the activation has closed."""
    cs = set(map(tuple, cells))
    if q is not None and q in cs: return "HOLDS"
    if t_next > last_open: return "IMPOSSIBLE"
    for k, b in cs:
        if q is not None and not (k * w < v10 if e == "R" else (k + 1) * w > v10): continue      # no extreme yet: any price
        if formed + 15 * b + 10 >= t_next and formed + 15 * b <= last_open: return "POSSIBLE"
    return "IMPOSSIBLE"
