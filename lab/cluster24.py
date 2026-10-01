"""DR Lab design 24 — the automatic main cluster of one event (R or X) of a family snapshot.

The operator's question (2026-10-01): under what conditions does a subset of the points of one distribution, R or X,
earn the right to be called the automatic main cluster of the family? The specification says what a cluster is (§7: a
reproducible local concentration of one event in price and time, with an explicit boundary and confirmed stability) and
what would prove one (§7.2). This module is the declared answer (meaning/11-glavnyj-klaster.md).

The subset is the set of known events of the family inside one block of the specification's grid (§6): 5 price cells x
4 time cells, 0.5 IDR width x 60 minutes. The candidate is the block holding the most known events, among the blocks
inside the family's own time (from its confirmation window to the block end); ties go to the earlier block, then to the
one nearer the edge 0, then to the lower one. The candidate earns the name «главный кластер» when all five hold:

У1 a concentration in price and in time: without any one of its sessions it still holds at least twice the mean of the
   neighbouring blocks of its window (the bands above and below) and at least twice the mean of the neighbouring blocks
   of its band (the hour before and after, where the family had time; with no such time it fails);
У2 first without one session and without the unknown: it leads every other place (a block more than one cell away) by
   at least 2 sessions, even when each session whose event is unknown is put wherever its observed part allows;
У3 not the grid: the grid shifted by half a price cell and by 5 or 10 minutes finds the same place on all six grids;
У4 not the set of sessions: 200 resamples of the family's sessions with replacement find the same place at least 80 %
   of the time;
У5 the independent history: the newer half of the family (by date) has at least 30 sessions; the older half finds the
   same place on its own, and in the newer half that older block is still at least 1.5 times as dense as its
   neighbours, with a one-sided binomial p <= 0.05.

«The same place» = block centres within one cell (0.1 width and 15 minutes). The number of the cluster is the share of
the family in its block, yes / N with the unknown kept apart: the same number a manual selection of the same block gives.
Nothing here changes N or any other share.
"""
from __future__ import annotations

import math

import numpy as np

RULE = "main-cluster-1"
KB, TB = 5, 4                       # the block: price cells x time cells (0.5 IDR width x 60 minutes)
WINDOW = 15
DENSE, LEAD = 2.0, 2                # У1, У2
SHIFTS = ((0, 0), (0, 5), (0, 10), (1, 0), (1, 5), (1, 10))   # У3: half price cells, minutes
BOOT, BOOT_MIN, SEED = 200, 0.8, 20261001                     # У4
DENSE_NEW, P_NEW, MIN_NEW = 1.5, 0.05, 30     # У5


def compact(members, ev, grid):
    """Per member, what the rule needs of event ev: ('k', v, w, t) known; ('u', v, w, t, gaps) unknown, where v, t are
    the observed extreme so far and its first open (None without an observed M5) and gaps the opens of the wholly
    missing M5 on its horizon; ('n',) no period."""
    out, j = [], 0 if ev == "R" else 1
    pick = min if ev == "R" else max
    for m in members:
        e = m[ev]
        if e["s"] == "known":
            out.append(("k", e["v"], m["w"], e["t"]))
        elif e["s"] == "unknown":
            obs = [(T, q[j]) for T, q in zip(grid, m["path"]) if T > m["act"] and q is not None]
            gaps = [T - 5 for T, q in zip(grid, m["path"]) if T > m["act"] and q is None]
            v = pick(x for _, x in obs) if obs else None
            t = next(T - 5 for T, x in obs if x == v) if obs else None
            out.append(("u", v, m["w"], t, gaps))
        else:
            out.append(("n",))
    return out


def _cells(pts, dk, dt, formed):
    """Price and time cells of the known events on a grid shifted by dk half price cells and dt minutes."""
    k = np.array([(20 * p[1] - dk * p[2]) // (2 * p[2]) for p in pts], dtype=np.int64)
    b = np.array([(p[3] - formed - dt) // WINDOW for p in pts], dtype=np.int64)
    return k, b


def _span(formed, end, win, dt):
    """The block starts b0 lying inside the family's own time on a grid shifted by dt minutes."""
    t_first, t_last = formed + WINDOW * win + 5, end - 5        # the first and last possible event opens
    return (t_first - formed - dt) // WINDOW, (t_last - formed - dt) // WINDOW - (TB - 1)


class _Field:
    """Block sums of known events over block starts (k0, b0); room around for the neighbours."""

    def __init__(self, k, b, b_min, b_max, weights=None, after=0):
        self.k_lo = int(k.min()) - KB - 2 if len(k) else -KB - 2
        k_hi = int(k.max()) + KB + 2 if len(k) else KB + 2
        self.b_lo = b_min - TB
        b_hi = b_max + 2 * TB - 1
        self.b_min, self.b_max = b_min, b_max
        shape = (k_hi - self.k_lo + 1, b_hi - self.b_lo + 1)
        if weights is None:
            H = np.zeros(shape, dtype=np.int64)
            np.add.at(H, (k - self.k_lo, b - self.b_lo), 1)
            self.S = self._sum(H[None])[0]
        else:                                                    # resamples x events
            H = np.zeros((weights.shape[0],) + shape, dtype=np.int64)
            flat = (k - self.k_lo) * shape[1] + (b - self.b_lo)
            Hf = H.reshape(weights.shape[0], -1)
            for i, c in enumerate(flat): Hf[:, c] += weights[:, i]
            self.S = self._sum(H)
        J = np.arange(self.S.shape[-1]) + self.b_lo
        I = np.arange(self.S.shape[-2]) + self.k_lo
        self.k0, self.b0 = np.meshgrid(I, J, indexing="ij")
        self.valid = (self.b0 >= b_min) & (self.b0 <= b_max)
        self.cand = self.valid & (self.b0 >= b_min + after)     # where a candidate may stand (the study: after > 0)

    @staticmethod
    def _sum(H):
        C = np.zeros((H.shape[0], H.shape[1] + 1, H.shape[2] + 1), dtype=np.int64)
        C[:, 1:, 1:] = H.cumsum(1).cumsum(2)
        return C[:, KB:, TB:] - C[:, :-KB, TB:] - C[:, KB:, :-TB] + C[:, :-KB, :-TB]

    def at(self, k0, b0, S=None):
        S = self.S if S is None else S
        i, j = k0 - self.k_lo, b0 - self.b_lo
        if 0 <= i < S.shape[-2] and 0 <= j < S.shape[-1]: return int(S[..., i, j])
        return 0

    def order(self, dk=0):
        """Tie-break rank of the candidate starts: earlier block, then centre nearer the edge, then lower."""
        k0, b0 = self.k0[self.cand], self.b0[self.cand]
        rank = np.empty(len(k0), dtype=np.int64)
        rank[np.lexsort((k0, np.abs(2 * k0 + KB + dk), b0))] = np.arange(len(k0))
        return k0, b0, rank

    def pick(self, dk=0):
        if not self.cand.any(): return None
        k0, b0, rank = self.order(dk)
        n = self.S[self.cand]
        best = np.flatnonzero(n == n.max())
        i = best[np.argmin(rank[best])]
        return int(k0[i]), int(b0[i]), int(n[i])

    def neighbours(self, k0, b0, S=None):
        """Counts of the neighbouring blocks: of its window (the bands above and below), of its band (the blocks before
        and after it in time, only where the family had time)."""
        price = [self.at(k0 - KB, b0, S), self.at(k0 + KB, b0, S)]
        time = [self.at(k0, b0 + s, S) for s in (-TB, TB) if self.b_min <= b0 + s <= self.b_max]
        return price, time


def _same(a, b):
    return abs(a[0] - b[0]) <= 1 and abs(a[1] - b[1]) <= 1


def _tail(c, n, p):
    """One-sided binomial P(X >= c), X ~ Bin(n, p)."""
    return float(sum(math.comb(n, x) * p ** x * (1 - p) ** (n - x) for x in range(c, n + 1)))


def _possible(u, F, ev, formed):
    """Starts (k0, b0) whose block an unknown event could fall into: its observed extreme at its first open, or at a
    wholly missing M5 any price at or beyond that extreme (any price without an observed M5)."""
    _, v, w, t, gaps = u
    mask = np.zeros(F.S.shape, dtype=bool)
    if v is not None:
        k, b = (10 * v) // w, (t - formed) // WINDOW
        mask |= (F.k0 >= k - KB + 1) & (F.k0 <= k) & (F.b0 >= b - TB + 1) & (F.b0 <= b)
    ray = np.ones(F.S.shape, dtype=bool) if v is None else (F.k0 <= (10 * v) // w) if ev == "R" else (F.k0 + KB - 1 >= (10 * v) // w)
    for g in {(t - formed) // WINDOW for t in gaps}:
        mask |= ray & (F.b0 >= g - TB + 1) & (F.b0 <= g)
    return mask


def main_cluster(pts, ev, formed, end, win, full=True, after=0):
    """The candidate of one event of a family and conditions У1-У5. pts: compact() of the family's members in date
    order. full=False stops at the first failed condition (the study's speed); the screen asks for all of them. after:
    the candidate may only start that many 15-minute cells after the family's first block (the study's question about
    the inside of the session; the screen uses 0)."""
    N = len(pts)
    kn = [p for p in pts if p[0] == "k"]
    unk = [p for p in pts if p[0] == "u"]
    out = dict(rule=RULE, event=ev, N=N, known=len(kn), unknown=len(unk), none=N - len(kn) - len(unk))
    b_min, b_max = _span(formed, end, win, 0)
    if not kn or b_max < b_min + after:
        out.update(status="none", failed=[], checks={})
        return out
    k, b = _cells(kn, 0, 0, formed)
    F = _Field(k, b, b_min, b_max, after=after)
    k0, b0, yes = F.pick()
    out.update(block=dict(k0=k0, k1=k0 + KB, b0=b0, b1=b0 + TB), time=[formed + WINDOW * b0, formed + WINDOW * (b0 + TB)],
               yes=yes)
    checks, failed = {}, []

    def done(name, ok, **info):
        checks[name] = dict(ok=bool(ok), **info)
        if not ok: failed.append(name)
        return not ok and not full

    # У1: a concentration in price and in time, without any one of its sessions
    price, time = F.neighbours(k0, b0)
    c1 = yes - 1
    ok = bool(time) and c1 >= DENSE * np.mean(price) and c1 >= DENSE * np.mean(time)
    if done("U1", ok, price=price, time=time): return _end(out, checks, failed)

    # У2: the lead over every other place, with the unknown put where it hurts most
    U = np.zeros(F.S.shape, dtype=np.int64)
    for u in unk: U += _possible(u, F, ev, formed)
    other = F.cand & ((np.abs(F.k0 - k0) > 1) | (np.abs(F.b0 - b0) > 1))
    if other.any():
        worst = F.S + U
        i = np.flatnonzero(other.ravel())[np.argmax(worst[other])]
        rival = dict(k0=int(F.k0.ravel()[i]), b0=int(F.b0.ravel()[i]), yes=int(F.S.ravel()[i]), unknown=int(U.ravel()[i]))
        lead = yes - rival["yes"] - rival["unknown"]
    else:
        rival, lead = None, yes
    if done("U2", lead >= LEAD, lead=int(lead), rival=rival): return _end(out, checks, failed)

    # У5: the older half finds the place; the newer half still has it denser than around
    h = N // 2
    old_k = [p for p in pts[:h] if p[0] == "k"]
    new_k = [p for p in pts[h:] if p[0] == "k"]
    hist = dict(older=dict(n=h, known=len(old_k)), newer=dict(n=N - h, known=len(new_k)))
    ok = False
    if N - h >= MIN_NEW and old_k and new_k:
        ko, bo = _cells(old_k, 0, 0, formed)
        Fo = _Field(ko, bo, b_min, b_max, after=after)
        po = Fo.pick()
        hist["older"].update(k0=po[0], b0=po[1], yes=po[2], same=_same(po, (k0, b0)))
        kq, bq = _cells(new_k, 0, 0, formed)
        Fn = _Field(kq, bq, b_min, b_max)
        cn = Fn.at(po[0], po[1])
        pn, tn = Fn.neighbours(po[0], po[1])
        nb = pn + tn
        n = cn + sum(nb)
        p = _tail(cn, n, 1 / (1 + len(nb))) if n else 1.0
        hist["newer"].update(yes=cn, neighbours=nb, p=round(p, 6))
        ok = hist["older"]["same"] and cn >= DENSE_NEW * np.mean(nb) and p <= P_NEW
    if done("U5", ok, **hist): return _end(out, checks, failed)

    # У3: the same place on six grids
    places = []
    for dk, dt in SHIFTS:
        bs = _span(formed, end, win, dt)
        ks, bb = _cells(kn, dk, dt, formed)
        q = _Field(ks, bb, *bs, after=after).pick(dk)
        places.append(None if q is None else [q[0] + KB / 2 + dk / 2, formed + dt + WINDOW * (q[1] + TB / 2)])
    centre = [k0 + KB / 2, formed + WINDOW * (b0 + TB / 2)]
    same = sum(1 for q in places if q and abs(q[0] - centre[0]) <= 1 and abs(q[1] - centre[1]) <= WINDOW)
    if done("U3", same == len(SHIFTS), same=same, of=len(SHIFTS)): return _end(out, checks, failed)

    # У4: resampled sessions
    rng = np.random.default_rng(SEED)
    W = rng.multinomial(N, np.full(N, 1 / N), size=BOOT)
    W = W[:, [i for i, p in enumerate(pts) if p[0] == "k"]]
    Fb = _Field(k, b, b_min, b_max, weights=W, after=after)
    vk, vb, rank = F.order()
    score = Fb.S[:, F.cand] - rank / (len(rank) + 1)
    best = np.argmax(score, axis=1)
    hit = (np.abs(vk[best] - k0) <= 1) & (np.abs(vb[best] - b0) <= 1)
    done("U4", hit.mean() >= BOOT_MIN, same=round(float(hit.mean()), 3), of=BOOT)
    return _end(out, checks, failed)


def _end(out, checks, failed):
    out.update(checks=checks, failed=failed, status="earned" if not failed and len(checks) == 5 else "candidate")
    return out


# The check on sessions 2018-2025 (meaning/11 §6, studies/main_cluster_2026_10_01/check_2018_2025.json), per session of
# confirmation families: M1 held or not, and what landed on the next sessions against the family's number (M2). The
# screen gives the name «главный кластер» only where M1 held; the break family was not checked.
CHECK = {
    "ADR": dict(held=True, verdict="выдержано",
                n=346, families=21, family_share=0.1904, landed=0.1705, ratio=0.895, ratio_5_95=[0.774, 1.013],
                neighbour=0.0539, contrast=3.161, contrast_5_95=[2.643, 4.0],
                events=dict(
                    R=dict(n=230, families=13, family_share=0.1931, landed=0.1739, ratio=0.901, ratio_5_95=[0.789, 1.048],
                           neighbour=0.0594, contrast=2.927, contrast_5_95=[2.239, 4.65]),
                    X=dict(n=116, families=8, family_share=0.1852, landed=0.1638, ratio=0.884, ratio_5_95=[0.664, 1.073],
                           neighbour=0.0431, contrast=3.8, contrast_5_95=[2.455, 6.0]))),
    "ODR": dict(held=True, verdict="выдержано",
                n=1156, families=46, family_share=0.1921, landed=0.1583, ratio=0.824, ratio_5_95=[0.735, 0.908],
                neighbour=0.0548, contrast=2.889, contrast_5_95=[2.538, 3.289],
                events=dict(
                    R=dict(n=625, families=24, family_share=0.1896, landed=0.1696, ratio=0.894, ratio_5_95=[0.759, 1.022],
                           neighbour=0.0571, contrast=2.972, contrast_5_95=[2.571, 3.424]),
                    X=dict(n=531, families=22, family_share=0.195, landed=0.145, ratio=0.744, ratio_5_95=[0.673, 0.846],
                           neighbour=0.0521, contrast=2.783, contrast_5_95=[2.36, 3.296]))),
    "RDR": dict(held=True, verdict="выдержано",
                n=1724, families=65, family_share=0.2103, landed=0.1879, ratio=0.894, ratio_5_95=[0.771, 1.013],
                neighbour=0.0418, contrast=4.5, contrast_5_95=[3.665, 5.374],
                events=dict(
                    R=dict(n=836, families=32, family_share=0.2211, landed=0.2201, ratio=0.995, ratio_5_95=[0.872, 1.128],
                           neighbour=0.0435, contrast=5.064, contrast_5_95=[4.301, 5.916]),
                    X=dict(n=888, families=33, family_share=0.2001, landed=0.1577, ratio=0.788, ratio_5_95=[0.667, 0.922],
                           neighbour=0.0402, contrast=3.925, contrast_5_95=[2.972, 5.106]))),
}


def of_snapshot(snap, ev):
    """The main cluster of event ev of a snapshot of lab/scene24.py (its members are in date order), with the check of
    its session and whether the screen may call it «главный кластер»."""
    sch = snap["schedule"]
    win = (snap["key"]["window"][0] - sch["formed"]) // WINDOW
    out = main_cluster(compact(snap["members"], ev, snap["grid"]), ev, sch["formed"], sch["end"], win)
    chk = CHECK.get(snap["key"]["session"]) if snap["view"] == "conf" else None
    out["method"] = None if chk is None else dict(chk, event=chk["events"].get(ev))
    out["named"] = out["status"] == "earned" and bool(chk and chk["held"])
    return out
