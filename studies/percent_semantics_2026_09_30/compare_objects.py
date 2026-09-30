"""Which region does each candidate object call «main»? One family, one time x SD space (lens 14, 2026-09-30).

The curator's audit (meaning/lens/2026-09-30-linza-14.md) asks for one computation before any UI change: on today's
family, compare the current first-touch constellations, the M5-close state density and the high-low touch field. The
executor adds the author's own objects (lens 6: per session one maximum retracement and one maximum extension, with
their times), because the operator asked not to replace the author's principles.

Families (today's, 2026-09-30, from lab/.runtime and the day's live bars; read-only):
  NQ · RDR · Wednesday · long · confirmation 11:45-12:00 (t0 = 11:50), and
  NQ · ODR · Wednesday · long · confirmation 04:00-04:15 (t0 = 04:05).
The film is the family's clock M5 bars from t0 to the session end, each session in its own IDR units (0 = its
confirmation-side IDR edge, -1 = the opposite IDR edge, +0.5 / +1.0 = STD steps).

Output: aggregates only (shares, counts, ranges in SD and clock time) and one figure per family. No prices, no dates, no
per-session rows.
usage: python -B studies/percent_semantics_2026_09_30/compare_objects.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "lab"))
import scene21 as S  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

DU = 0.1           # price cell, SD (IDR widths)
NEAR = 15          # the screen's «first minutes» (kde grid starts at t0 + NEAR - 10)


def clk(t):
    t = int(round(t))
    return f"{(t // 60) % 24:02d}:{t % 60:02d}"


def film(session, t0):
    f = S.family("NQ", session, t0)
    assert f["status"] == "ok" and f["mode"] == "conf", f.get("status")
    G = np.array(f["grid"], float)
    arr = lambda k: np.array([[np.nan if v is None else v for v in m[k]] for m in f["members"]], float)
    held = np.array([m["held"] for m in f["members"]], bool)
    v = S.day_view("NQ")
    s = S._state(v["bars"], session, t0, v["now"], False)
    edge = s["idrH"] if s["side"] == 1 else s["idrL"]
    u0 = s["side"] * (s["price"] - edge) / s["width"]
    return dict(f=f, G=G, lo=arr("lo"), hi=arr("hi"), cl=arr("cl"), held=held, u0=u0, N=len(f["members"]))


# ---------- 1. the current screen: first touches of places, their KDE and contours (design 22, conf mode) ----------
def places(u0):
    s1 = math.ceil((u0 + 0.25) / 0.5) * 0.5
    s2 = s1 + 0.5
    cont = [("за +%.1f" % s2, s2, np.inf), ("+%.1f…+%.1f" % (s1, s2), s1, s2), ("до +%.1f" % s1, -np.inf, s1)]
    pull = [("граница", -0.25, np.inf), ("центр", -0.75, -0.25), ("retirement", -np.inf, -0.75)]
    return [("cont", z) for z in cont if z[1] > u0] + [("pull", z) for z in pull if z[2] <= u0]


def first_touch_stars(F):
    G, lo, hi = F["G"], F["lo"], F["hi"]
    out = []
    for side, (name, a, b) in places(F["u0"]):
        for i in range(F["N"]):
            for j in range(len(G)):
                if np.isnan(lo[i, j]) or np.isnan(hi[i, j]): continue
                if lo[i, j] < b and hi[i, j] >= a:
                    u = max(lo[i, j], a + 1e-9) if side == "pull" else min(hi[i, j], b - 1e-9)
                    out.append(dict(side=side, place=name, band=(a, b), i=i, t=G[j] - 5, u=u))
                    break
    return out


def kde_place(stars, t0, end):
    """design 22's kde(): 2.5 min x 0.025 SD, blur 6 min x 0.06 SD, grid from t0 + NEAR - 10."""
    if len(stars) < 3: return None
    dt, du = 2.5, 0.025
    us = [q["u"] for q in stars]
    ua, tb = min(us) - 0.3, t0 + NEAR - 10
    nU, nT = int(math.ceil((max(us) + 0.3 - ua) / du)) + 1, int(math.ceil((end + 10 - tb) / dt)) + 1
    H = np.zeros((nU, nT))
    for q in stars:
        fx, fy = (q["t"] - tb) / dt, (q["u"] - ua) / du
        ix, iy = int(math.floor(fx)), int(math.floor(fy)); ax, ay = fx - ix, fy - iy
        for yy, xx, w in ((iy, ix, (1 - ax) * (1 - ay)), (iy, ix + 1, ax * (1 - ay)), (iy + 1, ix, (1 - ax) * ay), (iy + 1, ix + 1, ax * ay)):
            if 0 <= yy < nU and 0 <= xx < nT: H[yy, xx] += w
    H = ndimage.gaussian_filter(H, (0.06 / du, 6 / dt), mode="constant", truncate=3)
    return dict(H=H, t=tb + np.arange(nT) * dt, u=ua + np.arange(nU) * du)


# ---------- 2. the curator's M5-close state density; 3. the high-low touch field ----------
def state_density(F, umin, umax):
    edges = np.arange(umin, umax + DU / 2, DU)
    nK, T = len(edges) - 1, len(F["G"])
    C = np.zeros((nK, T))
    present = np.zeros(T)
    for j in range(T):
        col = F["cl"][:, j]
        col = col[~np.isnan(col)]
        present[j] = len(col)
        k = np.clip(np.floor((col - umin) / DU).astype(int), 0, nK - 1)
        np.add.at(C[:, j], k, 1)
    return C, edges, present


def touch_field(F, umin, umax):
    edges = np.arange(umin, umax + DU / 2, DU)
    nK, T = len(edges) - 1, len(F["G"])
    V = np.zeros((nK, T))
    for j in range(T):
        for a, b in zip(F["lo"][:, j], F["hi"][:, j]):
            if np.isnan(a) or np.isnan(b): continue
            ka, kb = int(np.clip(np.floor((a - umin) / DU), 0, nK - 1)), int(np.clip(np.floor((b - umin) / DU), 0, nK - 1))
            V[ka:kb + 1, j] += 1
    return V / F["N"], edges


def hdr(M, share):
    """The highest-density region of a non-negative map: the densest cells that together hold `share` of its mass."""
    flat = np.sort(M.ravel())[::-1]
    cum = np.cumsum(flat) / flat.sum()
    thr = flat[min(len(flat) - 1, int(np.searchsorted(cum, share)))]
    return M >= thr


# ---------- 4. the author's objects: one maximum retracement and one maximum extension per session ----------
def author_events(F):
    G, lo, hi = F["G"], F["lo"], F["hi"]
    mn = np.nanmin(lo, axis=1); mx = np.nanmax(hi, axis=1)
    tmn = G[np.nanargmin(lo, axis=1)] - 5; tmx = G[np.nanargmax(hi, axis=1)] - 5
    return mn, tmn, mx, tmx


def hist(values, width, lo_edge=None):
    b = np.floor(np.asarray(values) / width + 1e-9).astype(int)
    u, c = np.unique(b, return_counts=True)
    return {int(k): int(n) for k, n in zip(u, c)}


def top_cells(h, N, k=3, width=0.1, is_time=False):
    items = sorted(h.items(), key=lambda kv: -kv[1])[:k]
    if is_time: return ", ".join(f"{clk(b * width)}–{clk(b * width + width)} {100 * n / N:.0f} %" for b, n in items)
    return ", ".join(f"{b * width:+.1f}…{(b + 1) * width:+.1f} {100 * n / N:.0f} %" for b, n in items)


def pctl(v, q):
    return float(np.percentile(v, q))


# ---------- the report ----------
def report(session, t0, fig_path):
    F = film(session, t0)
    G, N = F["G"], F["N"]
    T, end = len(G), G[-1]
    print(f"\n=== NQ · {session} · {F['f']['cond']} · N = {N}, t0 = {clk(t0)}, columns {T} (to {clk(end)}), today u0 = {F['u0']:+.2f}")
    mn, tmn, mx, tmx = author_events(F)
    umin = math.floor(min(np.nanmin(F["lo"]), -1.5) * 2) / 2
    umax = math.ceil(max(np.nanmax(F["hi"]), 1.5) * 2) / 2
    umin, umax = max(umin, -4.0), min(umax, 5.0)

    # (0) outcome
    print(f"DR held to the session end: {100 * F['held'].mean():.0f} % · broke {100 * (1 - F['held'].mean()):.0f} %")

    # (1) current screen
    stars = first_touch_stars(F)
    print("1. CURRENT SCREEN (first touch of places ahead; share = sessions that touched the band after t0, of N):")
    for side, (name, a, b) in places(F["u0"]):
        st = [q for q in stars if q["place"] == name]
        print(f"   {side:4s} {name:14s} {100 * len(st) / N:4.0f} %  first-touch times median {clk(np.median([q['t'] for q in st])) if st else '—'}")
    kd = {}
    for side, (name, a, b) in places(F["u0"]):
        st = [q for q in stars if q["place"] == name]
        k = kde_place(st, t0, end)
        if k is None: continue
        kd[name] = (side, k)
        m = k["H"] >= 0.38 * k["H"].max()
        ys, xs = np.nonzero(m)
        print(f"   contour of «{name}» (38 % of its peak): {k['u'][ys.min()]:+.2f}…{k['u'][ys.max()]:+.2f} SD, {clk(k['t'][xs.min()])}–{clk(k['t'][xs.max()])}")

    # (2) state density
    C, edges, present = state_density(F, umin, umax)
    tot = C.sum()
    P = C / np.maximum(present, 1)
    Q = C.sum(axis=1) / tot
    kq = np.argsort(-Q)[:4]
    print("2. CURATOR'S M5-CLOSE STATE DENSITY (each column = 100 % of the sessions present; mass = share of all session x M5 states):")
    print(f"   states {int(tot)} of {N * T} (missing {100 * (1 - tot / (N * T)):.1f} %)")
    print("   price projection Q, top cells: " + ", ".join(f"{edges[k]:+.1f}…{edges[k + 1]:+.1f} {100 * Q[k]:.1f} %" for k in kq))
    early = C[:, G <= t0 + 30].sum() / tot
    print(f"   the first 30 minutes hold {100 * early:.0f} % of all states; max column share {100 * P.max():.0f} % at {clk(G[np.unravel_index(P.argmax(), P.shape)[1]] - 5)}")
    for share in (0.3, 0.5):
        R = hdr(C, share)
        lab, n = ndimage.label(R)
        sizes = ndimage.sum(C, lab, range(1, n + 1)) / tot
        big = int(np.argmax(sizes)) + 1
        ys, xs = np.nonzero(lab == big)
        print(f"   densest region holding {int(share * 100)} % of states: {n} pieces; the largest {100 * sizes.max():.0f} % of all states, "
              f"{edges[ys.min()]:+.1f}…{edges[ys.max() + 1]:+.1f} SD, {clk(G[xs.min()] - 5)}–{clk(G[xs.max()])}")
    # where the median close is at a few times
    for tt in (t0 + 30, t0 + 120, end):
        j = int(np.argmin(np.abs(G - tt)))
        col = F["cl"][:, j]; col = col[~np.isnan(col)]
        print(f"   closes at {clk(G[j])}: median {np.median(col):+.2f}, 20-80 % {pctl(col, 20):+.2f}…{pctl(col, 80):+.2f}")

    # (3) touch field
    V, _ = touch_field(F, umin, umax)
    colsum = V.sum(axis=0)
    print("3. HIGH-LOW TOUCH FIELD (share of N whose bar touched the cell in that M5):")
    print(f"   a column sums to {colsum.min():.2f}…{colsum.max():.2f} (x N) — one bar votes in several cells, so not 100 %")
    jmax = np.unravel_index(V.argmax(), V.shape)
    print(f"   max cell {100 * V.max():.0f} % at {edges[jmax[0]]:+.1f} SD, {clk(G[jmax[1]] - 5)}")

    # (4) author's objects
    hmn, hmx = hist(mn, 0.1), hist(mx, 0.1)
    htm, htx = hist(tmn, 15), hist(tmx, 15)
    print("4. AUTHOR'S OBJECTS (per session ONE value; each histogram sums to 100 % of N; whole family, not only DR true):")
    print(f"   max retracement (lowest point after t0 to the end): median {np.median(mn):+.2f}, «70 %» line {pctl(mn, 30):+.2f} (deeper went 30 %)")
    print(f"     top cells: {top_cells(hmn, N)}")
    print(f"     beyond the opposite IDR edge (< -1.0): {100 * np.mean(mn < -1):.0f} %; broke the DR: {100 * (1 - F['held'].mean()):.0f} %")
    print(f"     time (15 min): {top_cells(htm, N, 3, 15, True)}; median {clk(np.median(tmn))}")
    print(f"   max extension (highest point after t0 to the end): median {np.median(mx):+.2f}, «70 %» line {pctl(mx, 30):+.2f} (reached by 70 %)")
    print(f"     top cells: {top_cells(hmx, N)}")
    print(f"     time (15 min): {top_cells(htx, N, 3, 15, True)}; median {clk(np.median(tmx))}; in the last 30 minutes {100 * np.mean(tmx >= end - 30):.0f} %")
    # the author's T&P-like zone: the modal retracement cell and adjacent cells with at least half its count
    kmode = max(hmn, key=hmn.get)
    zone = [kmode]
    for step in (-1, 1):
        k = kmode + step
        while hmn.get(k, 0) >= 0.5 * hmn[kmode]: zone.append(k); k += step
    zlo, zhi = min(zone) * 0.1, (max(zone) + 1) * 0.1
    inz = (mn >= zlo) & (mn < zhi)
    print(f"   a T&P-like zone (modal retracement cell + neighbours >= half of it): {zlo:+.1f}…{zhi:+.1f} holds {100 * inz.mean():.0f} % of sessions; "
          f"their retracement times: {top_cells(hist(tmn[inz], 15), max(1, inz.sum()), 2, 15, True)} (of the zone)")
    reach = {lv: 100 * np.mean(mx >= lv) for lv in (0.5, 1.0, 1.5)}
    print("   reach ladder = the tail of the max-extension distribution: " + ", ".join(f"≥{lv:+.1f}: {r:.0f} %" for lv, r in reach.items()))

    # ---------- figure ----------
    fig, ax = plt.subplots(2, 2, figsize=(16, 10), sharex=True, sharey=True)
    ext = [t0, end, umin, umax]
    X = lambda t: t
    ticks = np.arange(math.ceil(t0 / 30) * 30, end + 1, 30)

    a = ax[0, 0]
    for name, (side, k) in kd.items():
        a.contour(k["t"], k["u"], k["H"] / k["H"].max(), levels=[0.38], colors=["#2a9d8f" if side == "cont" else "#e76f51"], linewidths=1.4)
    for q in stars:
        a.plot(q["t"], q["u"], ".", color="#2a9d8f" if q["side"] == "cont" else "#e76f51", ms=5, alpha=0.8)
    for side, (name, lo_, hi_) in places(F["u0"]):
        a.text(end - 2, (max(lo_, umin) + min(hi_, umax)) / 2, f"{name} {100 * len([q for q in stars if q['place'] == name]) / N:.0f} %",
               ha="right", va="center", fontsize=9, color="#2a9d8f" if side == "cont" else "#e76f51")
    a.set_title("1. Экран сейчас: первые касания мест и созвездия\n% места = коснулись полосы после t0", fontsize=10)

    a = ax[0, 1]
    im = a.imshow(np.ma.masked_equal(P, 0), origin="lower", aspect="auto", cmap="viridis", extent=[G[0] - 5, G[-1], edges[0], edges[-1]], vmin=0, vmax=max(0.3, P.max()))
    fig.colorbar(im, ax=a, fraction=0.03, label="доля семьи в этой пятиминутке")
    R = hdr(C, 0.3)
    a.contour(G - 2.5, (edges[:-1] + edges[1:]) / 2, R.astype(float), levels=[0.5], colors=["white"], linewidths=1.2)
    a.set_title("2. Куратор: плотность закрытий M5 (колонка = 100 %)\nбелый контур — самые плотные клетки, 30 % всех состояний", fontsize=10)

    a = ax[1, 0]
    im = a.imshow(np.ma.masked_equal(V, 0), origin="lower", aspect="auto", cmap="magma", extent=[G[0] - 5, G[-1], edges[0], edges[-1]], vmin=0)
    fig.colorbar(im, ax=a, fraction=0.03, label="доля семьи, чья свеча задела ячейку")
    a.set_title("3. Поле касаний high–low\n(одна свеча голосует в нескольких клетках, колонка > 100 %)", fontsize=10)

    a = ax[1, 1]
    H2, xe, ye = np.histogram2d(tmn, mn, bins=[np.arange(t0 - (t0 % 15), end + 15, 15), np.arange(umin, umax + 0.1, 0.1)])
    im = a.imshow(np.ma.masked_equal(H2.T / N, 0), origin="lower", aspect="auto", cmap="Oranges", extent=[xe[0], xe[-1], ye[0], ye[-1]], vmin=0)
    fig.colorbar(im, ax=a, fraction=0.03, label="доля сессий: макс. откат в этой клетке (цена × 15 мин)")
    a.plot(tmn[F["held"]], mn[F["held"]], "v", color="#6c3a1f", ms=5, label="макс. откат (DR удержался)")
    a.plot(tmn[~F["held"]], mn[~F["held"]], "x", color="black", ms=6, label="макс. откат (DR сломан)")
    a.plot(tmx, mx, "^", color="#1d6fa5", ms=5, label="макс. расширение")
    a.axhspan(zlo, zhi, color="#f4a261", alpha=0.15)
    a.legend(loc="upper left", fontsize=8)
    a.set_title("4. Автор: одно событие на сессию\nмакс. откат и макс. расширение до конца сессии и их время", fontsize=10)

    for a in ax.ravel():
        for lv, st_ in ((0, "-"), (-1, "--"), (0.5, ":"), (1.0, ":"), (-0.5, ":")):
            a.axhline(lv, color="grey", lw=0.7, ls=st_)
        a.set_xlim(t0 - 5, end); a.set_ylim(umin, umax)
        a.set_xticks(ticks); a.set_xticklabels([clk(t) for t in ticks])
    ax[1, 0].set_ylabel("SD (ширины IDR), 0 = край IDR подтверждения, −1 = противоположный край")
    ax[0, 0].set_ylabel("SD")
    fig.suptitle(f"NQ · {F['f']['cond']} · N = {N} · от {clk(t0)} до {clk(end)} · одна семья, четыре кандидата на «главный кластер»")
    fig.tight_layout()
    fig.savefig(fig_path, dpi=110)
    plt.close(fig)
    print(f"   figure: {fig_path.name}")


if __name__ == "__main__":
    report("RDR", 710, HERE / "rdr_n25.png")
    report("ODR", 245, HERE / "odr_n187.png")
