"""Independent reference of the 23.5 local layer «Съёмы лоу» (SW-0.1, operator 2026-10-26).

The page computes the layer from the family it shows (design/sozvezdiya-23-5/src/sweeps235.js); this module recomputes
it from the same published family, without the page's code, for tests/sweeps235.py and tests/sweeps235_page.mjs.
Definition: docs/DR-LAB-23-5-SWEEPS.md. Stdlib only; reads a family as /api/integration/scene publishes it.

  held low   : an M5 that makes a new low of the session after its activation (directed frame: against the side), when
               the next M5 does not go below it;
  sweep      : a later M5 goes below the latest held low by at least one tick (a wick counts);
  bottom     : the deepest point from the sweep until the first new high of the session (a continuation);
  unknown    : a missing M5 after the activation, or an M5 that is both a new low and a new high (order unknown, no M1).
"""
from __future__ import annotations
import json
import math
import sys
import urllib.parse
import urllib.request

CATS = ("CONT", "NOCONT", "NONE", "UNKNOWN")


def session(grid, m):
    """One historical session -> (status, events). An event: swing (v, t), bottom (v, t), continuation open or None."""
    bars = []
    for T, q in zip(grid, m["path"]):
        if T <= m["act"]:
            continue
        if q is None:
            return "UNKNOWN", []
        bars.append((T, q[0], q[1]))
    if not bars:
        return "NONE", []
    # first pass: every held low, keyed by the index of the M5 from which it is known (the confirming M5)
    lows, low_so_far = {}, math.inf
    for i, (T, lo, _) in enumerate(bars):
        if lo < low_so_far:
            if i + 1 < len(bars) and bars[i + 1][1] >= lo:
                lows[i + 1] = (lo, T - 5)
            low_so_far = lo
    # second pass: sweeps and continuations
    events, episode, held, high, low, unclear = [], None, None, -math.inf, math.inf, False
    for i, (T, lo, hi) in enumerate(bars):
        held = lows.get(i, held)
        new_high, new_low = hi > high, lo < low
        took = new_low and held is not None and lo < held[0]
        if episode is not None and new_high:
            if new_low:
                unclear = True
            else:
                episode["cont"] = T - 5
                events.append(episode)
                episode = None
        if took and new_high and episode is None and high > -math.inf:
            unclear = True
        if took:
            if episode is None:
                episode = dict(swing=held, bottom=(lo, T - 5), cont=None)
            else:
                episode["swing"], episode["bottom"] = held, (lo, T - 5)
        elif new_low and episode is not None:
            episode["bottom"] = (lo, T - 5)
        low, high = min(low, lo), max(high, hi)
    if episode is not None:
        events.append(episode)
    if unclear:                     # an M5 whose order decides the result: the session is unknown, as a missing M5
        return "UNKNOWN", []
    return "KNOWN", events


def regions(cells_by_case, b_lo, b_hi):
    """Half-height regions of their own peak over D = sessions with a cell in the 3 x 3 neighbourhood (one vote each)."""
    ks = [k for cs in cells_by_case.values() for k, _ in cs]
    if not ks or b_hi < b_lo:
        return []
    k_lo, k_hi = min(ks) - 1, max(ks) + 1
    D = {}
    for cs in cells_by_case.values():
        cover = set()
        for k, b in cs:
            if b_lo <= b <= b_hi:
                cover |= {(k + dk, b + db) for dk in (-1, 0, 1) for db in (-1, 0, 1)
                          if k_lo <= k + dk <= k_hi and b_lo <= b + db <= b_hi}
        for c in cover:
            D[c] = D.get(c, 0) + 1
    near = lambda c: [(c[0] + dk, c[1] + db) for dk in (-1, 0, 1) for db in (-1, 0, 1) if (dk, db) != (0, 0)]
    peaks = [c for c, v in D.items() if all(D.get(n, 0) <= v for n in near(c))]
    out, seen = [], set()
    for lam in sorted({D[c] / 2 for c in peaks}, reverse=True):
        label, n = {}, 0
        for c in sorted(D):
            if c in label or D[c] < lam:
                continue
            stack, label[c] = [c], n
            while stack:
                x = stack.pop()
                for y in near(x):
                    if y not in label and D.get(y, 0) >= lam:
                        label[y] = n
                        stack.append(y)
            n += 1
        for c in sorted(peaks):
            if D[c] != 2 * lam or (lam, label[c]) in seen:
                continue
            seen.add((lam, label[c]))
            cells = [x for x, L in label.items() if L == label[c]]
            if max(D[x] for x in cells) != D[c]:
                continue
            out.append(cells)
    return out


def model(fam):
    grid, N, formed = fam["grid"], fam["N"], fam["schedule"]["formed"]
    end, w0 = fam["schedule"]["end"], fam["key"]["window"][0]
    cats = dict.fromkeys(CATS, 0)
    stars, by_case = [], {}
    for m in fam["members"]:
        status, events = session(grid, m)
        if status != "KNOWN":
            cats[status] += 1
            continue
        cont = [e for e in events if e["cont"] is not None]
        cats["CONT" if cont else "NOCONT" if events else "NONE"] += 1
        for e in cont:
            v, t = e["bottom"]
            k, b = (10 * v) // m["w"], (t - formed) // 15
            stars.append(dict(case=m["id"], k=k, b=b, v=v, t=t, swing=list(e["swing"]), cont=e["cont"], w=m["w"]))
            by_case.setdefault(m["id"], set()).add((k, b))
    need = max(4, math.ceil(N / 20))
    zones = []
    for cells in regions(by_case, (w0 - formed) // 15, (end - 5 - formed) // 15):
        cs = set(cells)
        members = sorted(c for c, s in by_case.items() if s & cs)
        if len(members) < need:
            continue
        inside = [s for s in stars if (s["k"], s["b"]) in cs and s["case"] in members]
        depth = sorted(s["swing"][0] / s["w"] - s["v"] / s["w"] for s in inside)
        kk, bb = [c[0] for c in cells], [c[1] for c in cells]
        zones.append(dict(n=len(members), members=members, k0=min(kk), k1=max(kk) + 1, t0=formed + 15 * min(bb),
                          t1=formed + 15 * (max(bb) + 1), stars=len(inside), depth=depth[(len(depth) - 1) // 2]))
    zones.sort(key=lambda z: (z["t0"], -z["n"]))
    for i, z in enumerate(zones):
        z["label"] = "С" + str(i + 1)
    assert sum(cats.values()) == N, "the categories must split the family"
    return dict(N=N, need=need, cats=cats, stars=len(stars), zones=zones)


def fetch(base, **params):
    url = base.rstrip("/") + "/api/integration/scene?" + urllib.parse.urlencode(dict(view="conf", scope="weekday", trials="", **params))
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.load(r)["family"]


if __name__ == "__main__":
    # python -B lab/sweeps235_ref.py http://127.0.0.1:8735 NQ RDR 670 [YYYY-MM-DD]
    base, inst, sess, at = sys.argv[1:5]
    args = dict(instrument=inst, session=sess, at=at)
    if len(sys.argv) > 5:
        args["date"] = sys.argv[5]
    out = model(fetch(base, **args))
    for z in out["zones"]:
        z.pop("members")
    print(json.dumps(out, ensure_ascii=False))
