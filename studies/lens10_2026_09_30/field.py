"""Lens 10: the time-first field, reference implementation of pasport-polya.md (written to be read, not to be fast).

A similar session after the slice t is a path: its M5 bars (close minute, open, top, bottom, close) in its own units
(as in studies/lens8_2026_09_30/contract.py: top = the extreme in the confirmation direction), plus 'complete' (the data
reach the session end or the market closed early by the base's rule). The atom of the field: the bar's observed range
[bottom, top] in future column j intersects the half-open price bin k = [0.1 k, 0.1 (k+1)).
"""
from __future__ import annotations

import math
from collections import Counter

STEP = 0.1


def bin_of(u):
    """Index k of the half-open bin [0.1 k, 0.1 (k+1)) that holds u (rounded against float noise)."""
    return math.floor(round(u / STEP, 9))


def bins_of_range(lo, hi):
    """Every bin the closed range [lo, hi] intersects: top >= 0.1 k and bottom < 0.1 (k+1)."""
    return range(bin_of(lo), bin_of(hi) + 1)


def columns(t, H):
    """The future M5 columns after t, named by their close minute: t+5 ... H."""
    return list(range(t + 5, H + 5, 5))


def session_columns(path, t, H):
    """Per future column: the bar, or 'unknown' (missing bar while the session still ran, or data cut before H), or
    'closed' (after an early end of the session: the market was closed, a known 'did not reach')."""
    have = {b[0]: b for b in path["bars"] if t < b[0] <= H}
    last = max(have) if have else t
    out = {}
    for j in columns(t, H):
        if j in have: out[j] = have[j]
        elif j <= last: out[j] = "unknown"
        else: out[j] = "closed" if path.get("complete", True) else "unknown"
    return out


def session_cells(path, t, H):
    """(cells, unknown columns): cells = {(k, j)} the session votes in; one vote per cell at most."""
    cells, unknown = set(), set()
    for j, b in session_columns(path, t, H).items():
        if b == "unknown": unknown.add(j)
        elif b != "closed":
            for k in bins_of_range(b[3], b[2]): cells.add((k, j))
    return cells, unknown


def field(paths, t, H):
    """V(k, j) = sessions whose bar in column j intersects bin k / N, the same N for every cell; and the number of
    sessions with an unknown column j (their cells there are unknown: the value is the known mass, the full share lies
    in [n/N; (n+u)/N])."""
    N = len(paths)
    votes, unk = Counter(), Counter()
    for p in paths:
        c, u = session_cells(p, t, H)
        votes.update(c)
        unk.update(u)
    return {key: n / N for key, n in votes.items()}, unk, N


def reaches(bar, K):
    """The bar's range intersects the area K = (a, b), bounds exact (not rounded to bins), both belong to K."""
    return bar[2] >= K[0] and bar[3] <= K[1]


def V_area(paths, t, H, K, window=None):
    """V(K, j) for one column (window = [j]) or V(K, J) for a window of columns: sessions whose bar in at least one column
    of the window intersects K, each session once / N."""
    N = len(paths)
    n = 0
    for p in paths:
        cols = session_columns(p, t, H)
        J = window or list(cols)
        n += any(isinstance(cols[j], tuple) and reaches(cols[j], K) for j in J)
    return n / N


def first_reach(path, t, H, K):
    """Derived statistic: the first future column in which the session's bar intersects K (None if never)."""
    for j, b in session_columns(path, t, H).items():
        if isinstance(b, tuple) and reaches(b, K): return j
    return None


def session_mass(paths, t, H, contour):
    """M(C): sessions with at least one voted cell inside the contour (a set of (k, j)) / N; not the sum of cells."""
    return sum(1 for p in paths if session_cells(p, t, H)[0] & contour) / len(paths)


def gap_cross(path, t, H):
    """Bins jumped over between the previous observed price (the previous bar's close; for the first column the close at
    t) and a bar whose whole range lies on the other side: {(k, j)}. Not a range visit, no vote."""
    closes = {b[0]: b[4] for b in path["bars"]}
    prev = closes.get(t)
    out = set()
    for j, b in session_columns(path, t, H).items():
        if not isinstance(b, tuple):
            prev = None
            continue
        if prev is not None:
            if b[3] > prev:                                   # the bar is wholly above the previous price
                out |= {(k, j) for k in range(bin_of(prev) + 1, bin_of(b[3]))}
            elif b[2] < prev:                                 # wholly below
                out |= {(k, j) for k in range(bin_of(b[2]) + 1, bin_of(prev))}
        prev = b[4]
    return out
