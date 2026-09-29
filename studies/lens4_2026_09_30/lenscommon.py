"""Shared helpers for the checks asked by semantic lens 4 (meaning/lens/2026-09-30-linza-4.md).

Read-only over lab/.runtime (boxes base) and the G3 minute tape; only aggregates leave this folder.
Coordinates of a confirmed session as the screen measures its similar sessions: its own scale, 0 = its confirmation-side
IDR edge, +1 = one IDR width further in the confirmation direction (conf mode of lab/scene21.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

AUD = Path(__file__).resolve().parents[1] / "audit_2026_09_29"
sys.path.insert(0, str(AUD))
from common import INST, SESS, dense, load  # noqa: E402,F401
from replay_core import TEST_YEARS, cohort as rc_cohort, prep  # noqa: E402,F401

RT = Path(__file__).resolve().parents[2] / "lab" / ".runtime"


def conf_paths(d):
    """up / dn: the bar's extreme in / against the confirmation direction; X: the close; all in conf coordinates."""
    side = d["side"].astype(float)
    w = d["idrh"] - d["idrl"]
    w = np.where(w > 0, w, np.nan)
    e = np.where(side == 1, d["idrh"], d["idrl"])
    s = side[:, None]
    H, L, C = d["H"], d["L"], d["C"]
    up = s * (np.where(s == 1, H, L) - e[:, None]) / w[:, None]
    dn = s * (np.where(s == 1, L, H) - e[:, None]) / w[:, None]
    X = s * (C - e[:, None]) / w[:, None]
    return up, dn, X


def suffix_max(A):
    """out[:, s] = max of A[:, s+1:] (NaN ignored, -inf when nothing is left)."""
    B = np.where(np.isnan(A), -np.inf, A)
    R = np.maximum.accumulate(B[:, ::-1], axis=1)[:, ::-1]
    out = np.full_like(B, -np.inf)
    out[:, :-1] = R[:, 1:]
    return out


def suffix_min(A):
    return -suffix_max(-A)


def slot(d, t):
    """Index of the M5 slot that closes at minute t."""
    return (t - d["start"]) // 5 - 1


class Screen:
    """The screen's confirmed-state cohort (lab/scene21.py, conf mode) at any M5 close, vectorised."""

    def __init__(self, d):
        self.d = d
        self.up, self.dn, self.X = conf_paths(d)
        self.SU, self.SD = suffix_max(self.up), suffix_min(self.dn)
        C = d["C"]
        self.fut_ok = np.flip(np.logical_or.accumulate(np.flip(~np.isnan(C), 1), 1), 1)   # a bar at or after slot s

    def pos(self, s):
        x = self.X[:, s]
        return np.where(np.isnan(x), self.X[:, s - 1], x)

    def avail(self, s):
        ok = np.zeros(len(self.X), bool)
        if s + 1 < self.X.shape[1]:
            ok = ~np.isnan(self.pos(s)) & self.fut_ok[:, s + 1]
        return ok

    def cohort(self, i, t, years_ok, band_on=True):
        d = self.d
        s = slot(d, t)
        base = d["complete"] & years_ok & self.avail(s)
        base[i] = False
        conf, fail = d["conf"], d["fail"]
        m = base & (d["side"] == d["side"][i]) & (conf >= 0) & (conf <= t) & (np.abs(conf - conf[i]) <= 15)
        m &= ~((fail >= 0) & (fail <= t))
        pool = np.flatnonzero(m)
        pos = self.pos(s)
        u0 = pos[i]
        band, sel = None, pool
        if band_on:
            for bw in (0.25, 0.5):
                c = pool[np.abs(pos[pool] - u0) <= bw]
                if len(c) >= 40:
                    band, sel = bw, c
                    break
        return sel, band, u0


def edges_conf(u0):
    """The places ahead of the price after a confirmation, as the screen draws them (app.js zoneDefs):
    (role, lower, upper) bands; continuation up to the next half-step s1 not closer than 0.25 and the one after it;
    pullback -0.25 / -0.75 when they are below the price."""
    s1 = np.ceil((u0 + 0.25) / 0.5) * 0.5
    out = [("cont", s1, s1 + 0.5), ("cont", s1 + 0.5, np.inf)]
    if u0 > -0.25: out.append(("pull", -0.75, -0.25))
    if u0 > -0.75: out.append(("pull", -np.inf, -0.75))
    return out


def near_edge(role, lo, hi):
    return lo if role == "cont" else hi


def bss(p, y, sid, B=400, seed=7):
    """Brier skill against a constant equal to the realised frequency; session-clustered bootstrap 95 % interval."""
    p, y = np.asarray(p, float), np.asarray(y, float)
    f = lambda pp, yy: 1 - np.mean((pp - yy) ** 2) / max(1e-12, np.mean((yy.mean() - yy) ** 2))
    groups = _groups(sid)
    rng = np.random.default_rng(seed)
    bs = [f(p[ix], y[ix]) for ix in (_resample(groups, rng) for _ in range(B))]
    return f(p, y), np.percentile(bs, [2.5, 97.5])


def paired_brier(pa, pb, y, sid, B=400, seed=11):
    """Brier(a) - Brier(b) (positive = b better) with a session-clustered bootstrap 95 % interval."""
    pa, pb, y = (np.asarray(v, float) for v in (pa, pb, y))
    diff = (pa - y) ** 2 - (pb - y) ** 2
    groups = _groups(sid)
    rng = np.random.default_rng(seed)
    bs = [diff[ix].mean() for ix in (_resample(groups, rng) for _ in range(B))]
    return diff.mean(), np.percentile(bs, [2.5, 97.5])


def _groups(sid):
    _, inv = np.unique(np.asarray(sid), return_inverse=True)
    order = np.argsort(inv, kind="stable")
    cuts = np.flatnonzero(np.diff(inv[order])) + 1
    return np.split(order, cuts)


def _resample(groups, rng):
    return np.concatenate([groups[g] for g in rng.integers(0, len(groups), len(groups))])


def reliability(p, y, k=5):
    p, y = np.asarray(p, float), np.asarray(y, float)
    b = np.clip((p * k).astype(int), 0, k - 1)
    return " ".join(f"{int(100 * j / k)}-{int(100 * (j + 1) / k)}%:{100 * p[b == j].mean():.0f}->{100 * y[b == j].mean():.0f}"
                    for j in range(k) if (b == j).sum() >= 50)
