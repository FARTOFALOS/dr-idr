"""Lens 15 (2026-10-01): an automatic «main cluster» of R / X. Three candidate definitions are put through the
stability conditions of DR-LAB-SEM-1.0 §7.2, on the real tape and on memoryless paths made of each session's own
candles.

    python -B studies/lens15_2026_10_01/selector.py               # NQ: the real tape and one memoryless replica
    python -B studies/lens15_2026_10_01/selector.py --synthetic   # the same pipeline on random walks (debugging)

Declared before counting on the tape. The pipeline was debugged on --synthetic only. The plain-words version is in
meaning/lens/2026-10-01-otvet-15.md.

Atom, space, family: unchanged from DR-LAB-SEM-1.0 and lab/scene24.py. One known R (or X) per member of a
confirmation family F = instrument x session x weekday x direction x 15-minute window of the confirming M5. R and X
are measured by scene24.measure from the member's own confirmation to the block end; time = the open of the first M5
reaching the price. Cells are 0.1 SD x 15 minutes from the box end. R and X are never mixed. N = all members; an
unknown event stays in N and has no position. Families: NQ ADR / ODR / RDR, every key with N >= 20, sessions
2006-2025.

Candidate regions: rectangles of whole cells inside the family's possible hours (from its confirmation window to the
block end). M: exactly 3 x 3 cells (0.3 SD x 45 min). J and G: 1..10 price cells (<= 1.0 SD) x 1..8 time cells
(<= 2 h).

Concentration, one per definition:
  M «where most»: the number of the family's events in the window;
  J «beyond the two histograms» (the lens): Kulldorff's space-time permutation scan statistic. Expected count in a
    rectangle = (events in its price band) x (events in its time window) / n; Poisson log-likelihood ratio when the
    count exceeds it;
  G «beyond geometry»: the same ratio against the expected count of memoryless paths of the same members: each
    member's own post-confirmation M5 candles at their own clock places, the direction of every candle a fair coin
    (a candle is mirrored as a whole), K_BASE replicas per member; a rectangle's expectation is at least MU_FLOOR.
The main region = the highest value; ties -> smaller area, then earlier time, then price centre nearer to 0.

A main region is CONFIRMED when all hold:
  1. first decade: A = the main region of the 2006-2015 members;
  2. second decade: on the 2016-2025 members region A, fixed, is still a concentration, one-sided p < 0.05:
     M: its count against its same-size neighbours inside the possible hours (binomial, equal-density null);
     J: its count against 999 permutations of the time labels among those members;
     G: its count against 999 draws from the members' memoryless baseline;
  3. the same place: the main region C of all members overlaps A (IoU >= 0.25), and the main region on each of three
     shifted grids (+0.05 SD; +5 min; +10 min) overlaps C (IoU >= 0.25);
  4. not resampling noise and not one session: C is the main region (IoU >= 0.25) in >= 50 % of 200 bootstrap
     samples of whole members, and after removing any one of the sessions inside C;
  5. J and G only: C beats chance as the maximum over all candidate regions, p < 0.05 (199 permutations of the time
     labels / 199 memoryless families).
The same pipeline also runs on data «null»: one memoryless replica of every member in place of its real path. What
it confirms there is the geometry of the candles, not a property of the market.

Outputs: aggregates only (family keys, counts, shares, region bounds; no dates, no paths): results_<inst>.json and the
printed log.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "lab"))

SPLIT = "2016-01-01"
NMIN = 20
HMAX, WMAX = 10, 8
IOU = 0.25
NBOOT, NPERM, NCHECK = 200, 199, 999
K_BASE, K_SIG = 100, 199
SHIFTS = ((1, 0), (0, 5), (0, 10))       # (price phase in 1/20 SD, time phase in minutes)
ALPHA = 0.05
BOOT_SHARE = 0.5
SEED = 20261001
MU_FLOOR = 0.5 / K_BASE
SELECTORS = ("M", "J", "G")
EVENTS = ("R", "X")
DAYS = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")


def clk(t):
    t = int(round(t)) % 1440
    return f"{t // 60:02d}:{t % 60:02d}"


# ---------- members: their events and the candles of their horizon ----------
def sessions_real(inst, session):
    import scene21
    import scene24 as S
    B = scene21._boxes(inst)
    _, f, E = S.SESS[session]
    shift = S.SHIFT[session]
    miss = S._missing(inst, B, session)
    out = []
    for i, m in enumerate(B["boxes"]):
        if m["session"] != session or m["conf"] is None or m["date"] >= "2026-01-01": continue
        conf = int(m["conf"]) - shift
        if any(T < conf for T in miss.get(i, [])): continue          # first confirmation not established (scene24)
        d = m["side"]
        e = m["idr_high"] if d == 1 else m["idr_low"]
        w = int(m["idr_high"] - m["idr_low"])
        rows = S._rows(B, i, shift)
        ev = S.measure(rows, conf, E, d, e)
        rec = dict(key=(m["weekday"], d, S.window_of(conf, f)), first=m["date"] < SPLIT, w=w, known=ev["R"]["s"] == "known")
        if rec["known"]:
            T = range(conf + 5, E + 1, 5)
            lo, hi, cl = (np.array(x, dtype=np.int64) for x in zip(*(S.directed(rows[t], d, e) for t in T)))
            rec.update(R=(ev["R"]["v"], ev["R"]["t"]), X=(ev["X"]["v"], ev["X"]["t"]),
                       c0=int(S.directed(rows[conf], d, e)[2]), lo=lo, hi=hi, cl=cl,
                       opens=np.array(T, dtype=np.int64) - 5)
        out.append(rec)
    return out, f, E


def sessions_synthetic(rng):
    """Random walks on an RDR-like block (box end 10:30, block end 16:00), no market data. Families 0-2: pure walks;
    families 3-4: 40 % of the sessions dip to about -0.7 SD around 12:00-12:30 and then rally (a planted cluster)."""
    f, E, w = 630, 960, 100
    out = []
    for fam, (N, planted) in enumerate(((25, False), (60, False), (150, False), (60, True), (150, True))):
        w0 = 1
        for _ in range(N):
            conf = f + 15 * w0 + 5 * int(rng.integers(0, 3)) + 5
            T = np.arange(conf + 5, E + 1, 5)
            n = len(T)
            inc = rng.normal(0, 18, n)
            if planted and rng.random() < 0.4:
                tgt = 735 + 5 * int(rng.integers(0, 6))             # 12:15-12:40 close of the dip
                j = int(np.searchsorted(T, tgt))
                inc[:j] += (-70 - 30) / max(j, 1) - inc[:j].mean() * 0.8
                inc[j:] += 220 / max(n - j, 1)
            cl = np.round(30 + np.cumsum(inc)).astype(np.int64)
            prev = np.concatenate(([30], cl[:-1]))
            hi = np.maximum(cl, prev) + np.round(np.abs(rng.normal(0, 6, n))).astype(np.int64)
            lo = np.minimum(cl, prev) - np.round(np.abs(rng.normal(0, 6, n))).astype(np.int64)
            opens = T - 5
            jr, jx = int(lo.argmin()), int(hi.argmax())
            out.append(dict(key=(fam, 1, w0), first=bool(rng.random() < 0.5), w=w, known=True,
                            R=(int(lo[jr]), int(opens[jr])), X=(int(hi[jx]), int(opens[jx])),
                            c0=30, lo=lo, hi=hi, cl=cl, opens=opens))
    return out, f, E


def memoryless(rec, K, rng, mirror=None):
    """K replicas of the member's horizon: its own candles at their own clock places, each candle mirrored as a whole
    (open gap, high, low, close against the previous close) with probability 1/2. Returns R value, R time, X value, X
    time (directed ticks, open minutes), the first time on ties."""
    c0, lo, hi, cl, opens = rec["c0"], rec["lo"], rec["hi"], rec["cl"], rec["opens"]
    prev = np.concatenate(([c0], cl[:-1]))
    a, b, d = hi - prev, lo - prev, cl - prev
    s = rng.random((K, len(cl))) < 0.5 if mirror is None else mirror
    A, Bv, D = np.where(s, -b, a), np.where(s, -a, b), np.where(s, -d, d)
    C = np.cumsum(D, axis=1) + c0
    P = np.empty_like(C)
    P[:, 0] = c0
    P[:, 1:] = C[:, :-1]
    HI, LO = P + A, P + Bv
    jr, jx, ar = LO.argmin(1), HI.argmax(1), np.arange(K)
    return LO[ar, jr], opens[jr], HI[ar, jx], opens[jx]


# ---------- grid ----------
def cells(v, t, w, f, pph=0, pt=0):
    """Price cell [k/10 + pph/20, (k+1)/10 + pph/20) of v / w (exact integer floor) and time cell from the box end
    shifted by pt minutes."""
    return (20 * v - pph * w) // (2 * w), (t - f - pt) // 15


def domain(w0, f, E, pt=0):
    """The family's possible hours as time cells: from the first M5 after a confirmation in window w0 to the block end."""
    return (15 * w0 + 5 - pt) // 15, (E - 5 - f - pt) // 15


def coords(r, f, pph=0, pt=0):
    k1, k2, b1, b2 = r
    return (k1 / 10 + pph / 20, (k2 + 1) / 10 + pph / 20, f + 15 * b1 + pt, f + 15 * (b2 + 1) + pt)


def iou(a, b):
    if a is None or b is None: return 0.0
    p = max(0.0, min(a[1], b[1]) - max(a[0], b[0]))
    t = max(0.0, min(a[3], b[3]) - max(a[2], b[2]))
    inter = p * t
    union = (a[1] - a[0]) * (a[3] - a[2]) + (b[1] - b[0]) * (b[3] - b[2]) - inter
    return inter / union if union > 0 else 0.0


# ---------- scans ----------
_PAIRS = {}


def pairs(n, m):
    """Prefix-index pairs (i1, i2) of every run of 1..m consecutive cells among n."""
    if (n, m) not in _PAIRS:
        a = [(i, i + h) for h in range(1, min(m, n) + 1) for i in range(n - h + 1)]
        _PAIRS[(n, m)] = (np.array([x for x, _ in a], dtype=np.int64), np.array([y for _, y in a], dtype=np.int64))
    return _PAIRS[(n, m)]


def prefix(T):
    P = np.zeros((T.shape[0] + 1, T.shape[1] + 1))
    P[1:, 1:] = T.cumsum(0).cumsum(1)
    return P


def rect_sums(P, I1, I2, J1, J2):
    return P[np.ix_(I2, J2)] - P[np.ix_(I1, J2)] - P[np.ix_(I2, J1)] + P[np.ix_(I1, J1)]


def llr(c, mu, n):
    out = np.zeros(c.shape)
    m = (c > mu) & (c > 0)
    if not m.any(): return out
    cc, mm = c[m], np.maximum(mu[m], MU_FLOOR)
    rest, restmu = n - cc, n - mm
    t2 = np.zeros_like(cc)
    ok = rest > 0
    t2[ok] = rest[ok] * np.log(rest[ok] / restmu[ok])
    out[m] = cc * np.log(cc / mm) + t2
    return out


def table(k, b, K0, nk, b_lo, nb, wt=None):
    idx = (k - K0) * nb + (b - b_lo)
    return np.bincount(idx, weights=wt, minlength=nk * nb).reshape(nk, nb).astype(float)


def scan_lr(sel, k, b, dom, base=None, only_top=False):
    """Main region of J or G over events (k, b) on time cells dom. base = (kb, bb, weight) of the memoryless replicas
    for G. Returns (rect, count, expected, score) or None when no rectangle exceeds its expectation."""
    n = len(k)
    if n == 0: return 0.0 if only_top else None
    K0, K1 = int(k.min()), int(k.max())
    b_lo, b_hi = dom
    nk, nb = K1 - K0 + 1, b_hi - b_lo + 1
    T = table(k, b, K0, nk, b_lo, nb)
    I1, I2 = pairs(nk, HMAX)
    J1, J2 = pairs(nb, WMAX)
    c = np.rint(rect_sums(prefix(T), I1, I2, J1, J2))
    if sel == "J":
        rp = np.concatenate(([0.0], T.sum(1).cumsum()))
        cp = np.concatenate(([0.0], T.sum(0).cumsum()))
        mu = np.outer(rp[I2] - rp[I1], cp[J2] - cp[J1]) / n
    else:
        kb, bb, wt = base
        s = (kb >= K0) & (kb <= K1)
        mu = rect_sums(prefix(table(kb[s], bb[s], K0, nk, b_lo, nb, wt[s])), I1, I2, J1, J2)
    mu = np.maximum(mu, 0.0)
    sc = llr(c, mu, n)
    top = float(sc.max())
    if only_top: return top
    if top <= 0: return None
    ii, jj = np.nonzero(sc >= top - 1e-9)
    area = (I2[ii] - I1[ii]) * (J2[jj] - J1[jj])
    cen = np.abs(K0 + (I1[ii] + I2[ii]) / 2)
    o = np.lexsort((cen, J1[jj], area))
    i, j = ii[o[0]], jj[o[0]]
    return (K0 + int(I1[i]), K0 + int(I2[i]) - 1, b_lo + int(J1[j]), b_lo + int(J2[j]) - 1), int(c[i, j]), float(mu[i, j]), top


def scan_m(k, b, dom):
    """Main 3 x 3 window of M: the most events; ties -> earlier time, price centre nearer to 0."""
    b_lo, b_hi = dom
    if len(k) == 0 or b_hi - b_lo + 1 < 3: return None
    K0 = int(k.min()) - 2
    nk, nb = int(k.max()) - K0 + 3, b_hi - b_lo + 1
    P = prefix(table(k, b, K0, nk, b_lo, nb))
    c = np.rint(P[3:, 3:] - P[:-3, 3:] - P[3:, :-3] + P[:-3, :-3])
    top = c.max()
    ii, jj = np.nonzero(c >= top)
    o = np.lexsort((np.abs(K0 + ii + 1.5), jj))
    i, j = int(ii[o[0]]), int(jj[o[0]])
    return (K0 + i, K0 + i + 2, b_lo + j, b_lo + j + 2), int(top), None, float(top)


def inside(r, k, b):
    k1, k2, b1, b2 = r
    return (k >= k1) & (k <= k2) & (b >= b1) & (b <= b2)


def binom_tail(n, k, p):
    """P(X >= k) for X ~ Binomial(n, p)."""
    return float(sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(k, n + 1)))


# ---------- one family ----------
class Family:
    def __init__(self, key, recs, f, E, ver_obs, rng):
        self.key, self.f, self.E = key, f, E
        self.w0 = key[2]
        self.N = len(recs)
        kn = [r for r in recs if r["known"]]
        self.n = len(kn)
        self.w = np.array([r["w"] for r in kn], dtype=np.int64)
        self.first = np.array([r["first"] for r in kn], dtype=bool)
        self.nA_all = sum(1 for r in recs if r["first"])
        self.obs = {"real": {e: (np.array([r[e][0] for r in kn], dtype=np.int64), np.array([r[e][1] for r in kn], dtype=np.int64))
                             for e in EVENTS}}
        base = [memoryless(r, K_BASE, rng) for r in kn]
        sig = [memoryless(r, K_SIG, rng) for r in kn]
        null = [memoryless(r, 1, rng) for r in kn]
        self.base = {"R": (np.array([x[0] for x in base]), np.array([x[1] for x in base])),
                     "X": (np.array([x[2] for x in base]), np.array([x[3] for x in base]))}
        self.sig = {"R": (np.array([x[0] for x in sig]), np.array([x[1] for x in sig])),
                    "X": (np.array([x[2] for x in sig]), np.array([x[3] for x in sig]))}
        self.obs["null"] = {"R": (np.array([x[0][0] for x in null]), np.array([x[1][0] for x in null])),
                            "X": (np.array([x[2][0] for x in null]), np.array([x[3][0] for x in null]))}

    def grid(self, sel, ver, ev, idx, pph=0, pt=0):
        v, t = self.obs[ver][ev]
        k, b = cells(v[idx], t[idx], self.w[idx], self.f, pph, pt)
        base = None
        if sel == "G":
            bv, bt = self.base[ev]
            kb, bb = cells(bv[idx], bt[idx], self.w[idx][:, None], self.f, pph, pt)
            base = (kb.ravel(), bb.ravel(), np.full(kb.size, 1.0 / K_BASE))
        return k, b, base

    def main(self, sel, ver, ev, idx, pph=0, pt=0):
        k, b, base = self.grid(sel, ver, ev, idx, pph, pt)
        dom = domain(self.w0, self.f, self.E, pt)
        return scan_m(k, b, dom) if sel == "M" else scan_lr(sel, k, b, dom, base)

    def evaluate(self, sel, ver, ev, rng):
        f, n = self.f, self.n
        allx = np.arange(n)
        dom = domain(self.w0, f, self.E)
        C = self.main(sel, ver, ev, allx)
        out = dict(main=None, confirmed=False)
        if C is None: return out
        rC = coords(C[0], f)
        k, b, base = self.grid(sel, ver, ev, allx)
        out["main"] = dict(price=[round(rC[0], 2), round(rC[1], 2)], time=[clk(rC[2]), clk(rC[3])], cells=list(C[0]),
                           count=C[1], share=round(100 * C[1] / self.N, 1),
                           ratio=None if C[2] is None else round(C[1] / max(C[2], MU_FLOOR), 2),
                           where="start" if C[0][2] <= dom[0] + 1 else "end" if C[0][3] >= dom[1] - 1 else "middle")
        # 1-2: found on the first decade, still a concentration on the second
        iA, iB = np.nonzero(self.first)[0], np.nonzero(~self.first)[0]
        A = self.main(sel, ver, ev, iA) if len(iA) else None
        p_check, cA = 1.0, 0
        if A is not None and len(iB):
            kB, bB, _ = self.grid(sel, ver, ev, iB)
            inA = inside(A[0], kB, bB)
            cA = int(inA.sum())
            if cA:
                if sel == "M":
                    k1, k2, b1, b2 = A[0]
                    nbr, m = 0, 0
                    for dk in (-3, 0, 3):
                        for db in (-3, 0, 3):
                            if (dk, db) == (0, 0) or b1 + db < dom[0] or b2 + db > dom[1]: continue
                            m += 1
                            nbr += int(inside((k1 + dk, k2 + dk, b1 + db, b2 + db), kB, bB).sum())
                    p_check = binom_tail(cA + nbr, cA, 1.0 / (1 + m)) if m else 1.0
                elif sel == "J":
                    k1, k2, b1, b2 = A[0]
                    inb = (kB >= k1) & (kB <= k2)
                    perms = rng.permuted(np.tile(bB, (NCHECK, 1)), axis=1)
                    cnt = (inb[None, :] & (perms >= b1) & (perms <= b2)).sum(1)
                    p_check = (1 + int((cnt >= cA).sum())) / (1 + NCHECK)
                else:
                    bv, bt = self.base[ev]
                    kb, bb = cells(bv[iB], bt[iB], self.w[iB][:, None], f)
                    probs = inside(A[0], kb, bb).mean(1)
                    sims = (rng.random((NCHECK, len(iB))) < probs[None, :]).sum(1)
                    p_check = (1 + int((sims >= cA).sum())) / (1 + NCHECK)
        out["first_decade"] = None if A is None else dict(cells=list(A[0]), iou_with_main=round(iou(coords(A[0], f), rC), 2))
        out["second_decade"] = dict(count=cA, n=int(len(iB)), p=round(p_check, 4))
        c1 = A is not None and iou(coords(A[0], f), rC) >= IOU
        c2 = p_check < ALPHA
        # 3: grid shifts
        sh = []
        for pph, pt in SHIFTS:
            S_ = self.main(sel, ver, ev, allx, pph, pt)
            sh.append(round(iou(None if S_ is None else coords(S_[0], f, pph, pt), rC), 2))
        c3 = all(x >= IOU for x in sh)
        # 4: bootstrap of whole members (unknown ones drawn too, then without a position) and leave one out
        hits = 0
        for _ in range(NBOOT):
            d = rng.integers(0, self.N, self.N)
            d = d[d < n]
            Bt = self.main(sel, ver, ev, d) if len(d) else None
            hits += iou(None if Bt is None else coords(Bt[0], f), rC) >= IOU
        boot = hits / NBOOT
        loo = []
        for i in np.nonzero(inside(C[0], k, b))[0]:
            L = self.main(sel, ver, ev, np.delete(allx, i))
            loo.append(iou(None if L is None else coords(L[0], f), rC))
        c4 = boot >= BOOT_SHARE and all(x >= IOU for x in loo)
        # 5: the maximum against chance
        p_max = None
        if sel != "M":
            top = C[3]
            if sel == "J":
                tops = [scan_lr("J", k, rng.permutation(b), dom, only_top=True) for _ in range(NPERM)]
            else:
                sv, st = self.sig[ev]
                tops = []
                for j in range(NPERM):
                    kj, bj = cells(sv[:, j], st[:, j], self.w, f)
                    tops.append(scan_lr("G", kj, bj, dom, base, only_top=True))
            p_max = (1 + sum(t >= top - 1e-9 for t in tops)) / (1 + NPERM)
        c5 = sel == "M" or p_max < ALPHA
        out.update(shifts_iou=sh, bootstrap=round(boot, 3), loo_min_iou=round(min(loo), 2) if loo else None,
                   p_max=None if p_max is None else round(p_max, 4),
                   conditions=dict(first_decade_same_place=c1, second_decade_holds=c2, grid_shifts=c3,
                                   resampling_and_one_session=c4, beats_chance=c5),
                   confirmed=bool(c1 and c2 and c3 and c4 and c5))
        return out


# ---------- run ----------
def check_null_builder(recs):
    """With no candle mirrored, the memoryless builder must give back the real R and X exactly."""
    bad = 0
    for r in recs:
        if not r["known"]: continue
        vr, tr, vx, tx = memoryless(r, 1, None, mirror=np.zeros((1, len(r["cl"])), dtype=bool))
        bad += (int(vr[0]), int(tr[0])) != tuple(r["R"]) or (int(vx[0]), int(tx[0])) != tuple(r["X"])
    return bad


def run(inst, sessions, synthetic, quick):
    global NBOOT, NPERM, NCHECK
    if quick: NBOOT, NPERM, NCHECK = 40, 39, 199
    rng = np.random.default_rng(SEED)
    fams, totals = [], {}
    t0 = time.time()
    groups = [("SYN", sessions_synthetic(rng))] if synthetic else [(s, sessions_real(inst, s)) for s in sessions]
    for session, (recs, f, E) in groups:
        bad = check_null_builder(recs)
        print(f"{session}: {len(recs)} confirmed sessions with an established first confirmation; null builder mismatches {bad}")
        if bad: raise SystemExit("the memoryless builder does not reproduce the real events")
        totals[session] = len(recs)
        by = {}
        for r in recs: by.setdefault(r["key"], []).append(r)
        for key in sorted(by, key=lambda q: (q[2], q[0], -q[1])):
            mem = by[key]
            if len(mem) < NMIN: continue
            F = Family(key, mem, f, E, None, rng)
            rec = dict(session=session, weekday=key[0] if synthetic else DAYS[key[0]], direction="long" if key[1] == 1 else "short",
                       window=[clk(f + 15 * key[2]), clk(f + 15 * key[2] + 15)], N=F.N, known=F.n,
                       first_decade=int(F.first.sum()), second_decade=int((~F.first).sum()), res={})
            t1 = time.time()
            lo_b, hi_b = domain(F.w0, f, E)
            rec["piles"] = {}
            for ver in ("real", "null"):
                for ev in EVENTS:
                    _, b = cells(*F.obs[ver][ev], F.w, f)
                    rec["piles"][f"{ver}/{ev}"] = dict(first30=round(100 * float((b <= lo_b + 1).sum()) / F.N, 1),
                                                       last30=round(100 * float((b >= hi_b - 1).sum()) / F.N, 1))
            for ver in ("real", "null"):
                for ev in EVENTS:
                    for sel in SELECTORS:
                        rec["res"][f"{ver}/{ev}/{sel}"] = F.evaluate(sel, ver, ev, rng)
            fams.append(rec)
            conf = " ".join(f"{q}:{'+' if rec['res'][q]['confirmed'] else '.'}" for q in rec["res"])
            print(f"  {session} {rec['weekday']} {rec['direction']:5s} {rec['window'][0]} N {F.N:3d}  {conf}  ({time.time() - t1:.0f} s)", flush=True)
    print(f"done in {time.time() - t0:.0f} s")
    return fams, totals


def summary(fams, totals):
    out = {}
    allN = sum(totals.values())
    tested = sum(r["N"] for r in fams) or 1
    for q in ("real/R", "real/X", "null/R", "null/X"):
        out["piles/" + q] = {p: round(sum(r["N"] * r["piles"][q][p] for r in fams) / tested, 1) for p in ("first30", "last30")}
    for ver in ("real", "null"):
        for ev in EVENTS:
            for sel in SELECTORS:
                q = f"{ver}/{ev}/{sel}"
                rows = [(r, r["res"][q]) for r in fams]
                conf = [(r, x) for r, x in rows if x["confirmed"]]
                where = {}
                for _, x in rows:
                    if x["main"]: where[x["main"]["where"]] = where.get(x["main"]["where"], 0) + 1
                cwhere = {}
                for _, x in conf: cwhere[x["main"]["where"]] = cwhere.get(x["main"]["where"], 0) + 1
                bins = {}
                for lo, hi in ((20, 49), (50, 99), (100, 10 ** 6)):
                    sub = [(r, x) for r, x in rows if lo <= r["N"] <= hi]
                    bins[f"{lo}-{hi if hi < 10 ** 6 else ''}"] = [sum(x["confirmed"] for _, x in sub), len(sub)]
                conds = {}
                for _, x in rows:
                    for c, v in (x.get("conditions") or {}).items(): conds[c] = conds.get(c, 0) + bool(v)
                out[q] = dict(families=len(rows), confirmed=len(conf), by_N=bins,
                              sessions_with_confirmed_pct=round(100 * sum(r["N"] for r, _ in conf) / allN, 1),
                              main_where=where, confirmed_where=cwhere, conditions_met=conds,
                              confirmed_share_median=None if not conf else float(np.median([x["main"]["share"] for _, x in conf])))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inst", default="NQ")
    ap.add_argument("--sessions", default="ADR,ODR,RDR")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--merge", action="store_true", help="join results_<inst>_<session>.json into results_<inst>.json")
    a = ap.parse_args()
    if a.merge:
        fams, totals, doc = [], {}, None
        for s in a.sessions.split(","):
            doc = json.loads((HERE / f"results_{a.inst.lower()}_{s.lower()}.json").read_text(encoding="utf-8"))
            fams += doc["families"]
            totals.update(doc["sessions_total"])
        doc.update(sessions_total=totals, summary=summary(fams, totals), families=fams)
        (HERE / f"results_{a.inst.lower()}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        for q, x in doc["summary"].items(): print(q, json.dumps(x, ensure_ascii=False))
        return
    fams, totals = run(a.inst, a.sessions.split(","), a.synthetic, a.quick)
    S = summary(fams, totals)
    for q, x in S.items():
        if q.startswith("piles/"):
            print(f"{q:14s} share of N in the first / last 30 minutes of the possible hours: {x['first30']} % / {x['last30']} %")
            continue
        print(f"{q:12s} families {x['families']:3d} confirmed {x['confirmed']:3d} by N {x['by_N']} sessions {x['sessions_with_confirmed_pct']:5.1f}% "
              f"main {x['main_where']} confirmed {x['confirmed_where']} share median {x['confirmed_share_median']}")
    name = "synthetic" if a.synthetic else a.inst.lower() + "_" + a.sessions.lower().replace(",", "-")
    if a.quick: name += "_quick"
    doc = dict(study="lens 15: automatic main cluster of R / X, three definitions through spec §7.2", declared=__doc__,
               parameters=dict(SPLIT=SPLIT, NMIN=NMIN, HMAX=HMAX, WMAX=WMAX, IOU=IOU, NBOOT=NBOOT, NPERM=NPERM, NCHECK=NCHECK,
                               K_BASE=K_BASE, K_SIG=K_SIG, SHIFTS=SHIFTS, ALPHA=ALPHA, BOOT_SHARE=BOOT_SHARE, SEED=SEED,
                               MU_FLOOR=MU_FLOOR),
               instrument=None if a.synthetic else a.inst, sessions_total=totals, summary=S, families=fams)
    (HERE / f"results_{name}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
