"""E0 + E1: the author's descriptive claims on the real tape vs. null paths that keep the real box.

Question: do the DR/IDR descriptive regularities (DR true ~80%, box colour -> direction ~70%, return into DR ~90%,
+0.5 reached ~80%) need anything beyond the geometry of the day's own volatility and drift?

Real: each complete session of a type (all M5 slots present), statistics by the lab's rules (close-based confirmation
and DR true, IDR by bodies, coordinates from the confirmation-side IDR edge in IDR widths).
Nulls keep the real formation hour (so DR, IDR, box colour are the real ones) and replace what follows the box:
  P60  post-box M5 bars permuted within 60-minute blocks (keeps drift and vol profile at 60-min scale)
  PALL post-box M5 bars permuted over the whole post-box period (keeps the day's post-box drift and bar shapes)
  P0   as PALL with the day's post-box drift removed (pure volatility geometry)
  NBR  post-box bars of another day of the same session type within +-10 rows (similar volatility regime),
       spliced after the real box (the aftermath does not "know" this box)
Each bar is moved as a whole (its open gap, high, low, close relative to the previous close), so bar shapes stay real.
Decision (declared before counting): a claim is "geometry" for an instrument/session when the PALL and NBR rates lie
within 5 pp of the real rate; "beyond geometry" when the real rate exceeds both nulls by >= 5 pp with the real 95%
interval above both null means.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from common import INST, SESS, dense, wilson  # noqa: E402

K = 10
rng = np.random.default_rng(20260929)


def stats(O, H, L, C, nb):
    drh = H[:, :nb].max(1); drl = L[:, :nb].min(1)
    idrh = np.maximum(O[:, :nb], C[:, :nb]).max(1); idrl = np.minimum(O[:, :nb], C[:, :nb]).min(1)
    w = idrh - idrl
    box = np.sign(C[:, nb - 1] - O[:, 0])
    Cp, Hp, Lp = C[:, nb:], H[:, nb:], L[:, nb:]
    Sp = Cp.shape[1]
    up = Cp > drh[:, None]; dn = Cp < drl[:, None]
    BIG = 10 ** 6
    ku = np.where(up.any(1), up.argmax(1), BIG); kd = np.where(dn.any(1), dn.argmax(1), BIG)
    side = np.where(ku < kd, 1, np.where(kd < ku, -1, 0))
    k = np.minimum(ku, kd)
    j = np.arange(Sp)[None, :]
    later = j > k[:, None]
    lg = side == 1
    fail_c = np.where(lg, (later & (Cp < drl[:, None])).any(1), (later & (Cp > drh[:, None])).any(1))
    fail_w = np.where(lg, (later & (Lp < drl[:, None])).any(1), (later & (Hp > drh[:, None])).any(1))
    lit = np.where(lg, ~(Lp < drl[:, None]).any(1), ~(Hp > drh[:, None]).any(1))
    has_later = later.any(1)
    minL = np.where(later, Lp, np.inf).min(1); maxH = np.where(later, Hp, -np.inf).max(1)
    edge = np.where(lg, idrh, idrl)
    retr = np.where(lg, (minL - idrh) / w, -(maxH - idrl) / w)
    ext = np.where(lg, (maxH - idrh) / w, -(minL - idrl) / w)
    into_dr = np.where(lg, minL <= drh, maxH >= drl)
    into_idr = np.where(lg, minL <= idrh, maxH >= idrl)
    delay = (k + 1) * 5
    ok = (side != 0) & has_later & (w > 0)
    return dict(side=side, ok=ok, true_c=~fail_c, true_w=~fail_w, lit=lit, retr=retr, ext=ext, into_dr=into_dr,
                into_idr=into_idr, box=box, delay=delay, n=len(side))


def summary(s):
    ok = s["ok"]; n_ok = int(ok.sum())
    r = lambda m: 100.0 * float(m[ok].mean()) if n_ok else np.nan
    agree_mask = ok & (s["box"] != 0)
    deep = ok & (s["retr"] <= -0.75)
    b = lambda lo, hi: ok & (s["delay"] > lo) & (s["delay"] <= hi)
    return dict(n=s["n"], conf=100.0 * float((s["side"] != 0).mean()), n_conf=n_ok,
                true_c=r(s["true_c"]), true_w=r(s["true_w"]), lit=r(s["lit"]),
                agree=100.0 * float((s["side"][agree_mask] == s["box"][agree_mask]).mean()),
                into_dr=r(s["into_dr"]), into_idr=r(s["into_idr"]),
                ext05=r(s["ext"] >= 0.5), ext10=r(s["ext"] >= 1.0),
                retr_med=float(np.median(s["retr"][ok])), ext_med=float(np.median(s["ext"][ok])),
                held_after_075=100.0 * float(s["true_c"][deep].mean()) if deep.any() else np.nan,
                share_touch_075=100.0 * float(deep.sum() / max(1, n_ok)),
                true_c_0_30=100.0 * float(s["true_c"][b(0, 30)].mean()), true_c_30_60=100.0 * float(s["true_c"][b(30, 60)].mean()),
                true_c_60p=100.0 * float(s["true_c"][b(60, 10 ** 6)].mean()))


def increments(O, H, L, C):
    prevC = np.concatenate([O[:, :1], C[:, :-1]], axis=1)
    return O - prevC, H - prevC, L - prevC, C - prevC


def rebuild(O, H, L, C, nb, dO, dH, dL, dC):
    """Real box (slots < nb) + given post-box increments."""
    c0 = C[:, nb - 1:nb]
    Cp = c0 + np.cumsum(dC, axis=1)
    prev = np.concatenate([c0, Cp[:, :-1]], axis=1)
    return (np.concatenate([O[:, :nb], prev + dO], 1), np.concatenate([H[:, :nb], prev + dH], 1),
            np.concatenate([L[:, :nb], prev + dL], 1), np.concatenate([C[:, :nb], Cp], 1))


def permuted(inc, nb, block):
    dO, dH, dL, dC = (x[:, nb:] for x in inc)
    n, Sp = dC.shape
    keys = rng.random((n, Sp)) + (np.arange(Sp)[None, :] // block if block else 0) * 10.0
    order = np.argsort(keys, axis=1)
    g = lambda a: np.take_along_axis(a, order, axis=1)
    return g(dO), g(dH), g(dL), g(dC)


def neighbour(inc, nb, rows_ok):
    dO, dH, dL, dC = (x[:, nb:] for x in inc)
    n = dC.shape[0]
    off = rng.integers(1, 11, n) * rng.choice([-1, 1], n)
    src = np.clip(np.arange(n) + off, 0, n - 1)
    src = np.where(src == np.arange(n), np.clip(np.arange(n) - off, 0, n - 1), src)
    return dO[src], dH[src], dL[src], dC[src]


def run(inst, sess):
    d = dense(inst, sess)
    nb = d["nbox"]
    full = ~(np.isnan(d["O"]).any(1) | np.isnan(d["H"]).any(1) | np.isnan(d["L"]).any(1) | np.isnan(d["C"]).any(1))
    O, H, L, C = (d[k][full] for k in "OHLC")
    res = {"REAL": summary(stats(O, H, L, C, nb))}
    inc = increments(O, H, L, C)
    for name in ("P60", "PALL", "P0", "NBR"):
        draws = []
        for _ in range(K):
            if name == "P60": dd = permuted(inc, nb, 12)
            elif name in ("PALL", "P0"): dd = permuted(inc, nb, 0)
            else: dd = neighbour(inc, nb, full)
            if name == "P0":
                mu = dd[3].mean(1, keepdims=True)
                dd = tuple(x - mu for x in dd)
            draws.append(summary(stats(*rebuild(O, H, L, C, nb, *dd), nb)))
        keys = draws[0].keys()
        res[name] = {k: float(np.nanmean([x[k] for x in draws])) for k in keys}
        res[name + "_sd"] = {k: float(np.nanstd([x[k] for x in draws])) for k in keys}
    R = res["REAL"]
    ci = {}
    for k in ("true_c", "true_w", "lit", "agree", "into_dr", "into_idr", "ext05", "ext10"):
        ci[k] = wilson(round(R[k] * R["n_conf"] / 100), R["n_conf"])
    res["REAL_ci"] = ci
    return res


if __name__ == "__main__":
    out = {}
    t0 = time.time()
    for inst in INST:
        for sess in ("RDR", "ODR", "ADR"):
            out[f"{inst}-{sess}"] = run(inst, sess)
            R, P, N, Z = (out[f"{inst}-{sess}"][k] for k in ("REAL", "PALL", "NBR", "P0"))
            print(f"{inst} {sess} n={R['n']} conf {R['conf']:.1f}/{P['conf']:.1f}/{N['conf']:.1f} | "
                  f"DRtrue close {R['true_c']:.1f} vs PALL {P['true_c']:.1f} P0 {Z['true_c']:.1f} NBR {N['true_c']:.1f} | "
                  f"wick {R['true_w']:.1f}/{P['true_w']:.1f}/{N['true_w']:.1f} | lit {R['lit']:.1f}/{P['lit']:.1f}/{N['lit']:.1f} | "
                  f"agree {R['agree']:.1f}/{P['agree']:.1f}/{N['agree']:.1f} | intoDR {R['into_dr']:.1f}/{P['into_dr']:.1f}/{N['into_dr']:.1f} | "
                  f"ext05 {R['ext05']:.1f}/{P['ext05']:.1f}/{N['ext05']:.1f} | held|-0.75 {R['held_after_075']:.1f}/{P['held_after_075']:.1f}/{N['held_after_075']:.1f}"
                  f"  [{time.time() - t0:.0f}s]", flush=True)
    Path(__file__).with_suffix(".json").write_text(json.dumps(out, indent=1), encoding="utf-8")
