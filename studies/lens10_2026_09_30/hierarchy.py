"""Lens 10, patch 2.1: the time hierarchy of the maps on a toy synthetic history (reference code, pasport-polya.md
section 0). Baseline at the activation M5 t0 (the first M5 after the box that closed beyond the DR), a Dynamic map at
every later closed M5; each map is built from today's prefix up to its slice only, so a later map cannot rewrite it.

Sessions are in their own units (long confirmation: an M5 close above the DR high DRH; the opposite DR is OU); bars are
(close minute, open, top, bottom, close). The toy matcher follows the working screen (lab/scene21.py, conf mode):
confirmed within 15 minutes of today's t0 and not after its slice, DR intact at its slice, close at its slice within
0.25 of today's close at the slice. align = 'clock' puts every similar session at today's clock minute (the screen now);
align = 'event' puts it at its own t0 plus the time since today's activation (patch 2.1: «на их собственном t0»).
"""
from __future__ import annotations

import copy
from collections import Counter

from field import session_cells

DRH, OU, FORMED = 0.15, -1.2, 630


def activation(s):
    """t0: the close minute of the first M5 after the box whose close is beyond the DR (None: no activation yet)."""
    return next((b[0] for b in s["bars"] if b[0] > FORMED and b[4] > DRH), None)


def prefix(s, t):
    return dict(s, bars=[b for b in s["bars"] if b[0] <= t])


def close_at(s, t):
    return next((b[4] for b in s["bars"] if b[0] == t), None)


def broken_by(s, t):
    a0 = activation(s)
    return a0 is not None and any(a0 < b[0] <= t and b[4] < OU for b in s["bars"])


def cohort(today, history, tn, align):
    """Similar sessions for today's slice tn, from today's prefix up to tn only: [(session, its own slice)]."""
    T0, x = activation(today), close_at(today, tn)
    out = []
    for h in history:
        a0 = activation(h)
        if a0 is None or abs(a0 - T0) > 15: continue
        ts = tn if align == "clock" else a0 + (tn - T0)
        if a0 > ts or broken_by(h, ts): continue
        c = close_at(h, ts)
        if c is None or abs(c - x) > 0.25: continue
        out.append((h, ts))
    return out


def map_at(today_full, history, tn, H=780, align="clock"):
    """The map a trader would see at today's closed M5 tn: None before the activation, the Baseline at t0, a Dynamic
    map after it. Cells are put on today's clock: a similar session's column j becomes tn + (j - its own slice)."""
    today = prefix(today_full, tn)
    T0 = activation(today)
    if T0 is None or tn < T0: return dict(kind=None, t=tn)
    C = cohort(today, history, tn, align)
    votes = Counter()
    for h, ts in C:
        cells, _ = session_cells(h, ts, H)
        votes.update({(k, tn + (j - ts)) for k, j in cells if tn + (j - ts) <= H})
    N = len(C)
    return dict(kind="baseline" if tn == T0 else "dynamic", t=tn, t0=T0, N=N, members=sorted(h["name"] for h, _ in C),
                V={key: n / N for key, n in votes.items()} if N else {})


class Day:
    """What the screen keeps during one session: the Baseline once, a Dynamic map per later closed M5."""

    def __init__(self):
        self.baseline, self.dynamic, self._frozen = None, {}, None

    def on_close(self, today_full, history, tn, align="clock"):
        m = map_at(today_full, history, tn, align=align)
        if m["kind"] == "baseline" and self.baseline is None:
            self.baseline, self._frozen = m, copy.deepcopy(m)
        elif m["kind"] == "dynamic":
            self.dynamic[tn] = m
        return m

    def baseline_intact(self):
        return self.baseline == self._frozen
