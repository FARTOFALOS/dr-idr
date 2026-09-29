"""Replay of the working screen on history (walk-forward cohorts, test years 2016-2025), validated against
lab/scene21.cohort by replay_equivalence.py / replay_equivalence_values.py (identical cohorts and values on 360 + 72 sampled states).

Adds to replay_core.py: the model filter before a confirmation (as scene21), session ids (for session-clustered
intervals), the first STD target exactly as the panel's «Цели» picks it (the next half-step beyond the side's running
extreme since the confirmation), the fan's path coverage, and for the time pile-up: the arcsine prediction of a
driftless path on the tape's own M5 variance clock and on a flat clock, with and without the first-minutes exclusion.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from common import INST, dense  # noqa: E402
from models_vec import model_arrays, model_at  # noqa: E402
from replay_core import TEST_YEARS, prep  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "lab" / ".runtime" / "audit_screen_replay.json"


def var_clock(d):
    C = d["C"]
    r = np.diff(np.log(C), axis=1)
    v = np.nanmean(r ** 2, axis=0)
    return np.r_[np.nan, v]                     # v[s] = variance of the move into slot s (closing at start+5(s+1))


def arcsine_late(v, start, t, near_until, end):
    s0 = (t - start) // 5 - 1
    def V(tt): return float(np.nansum(v[s0 + 1:(tt - start) // 5])) if tt > t else 0.0
    VT = V(end)
    A = lambda tt: (2 / math.pi) * math.asin(math.sqrt(min(1.0, V(tt) / VT)))
    late_far = (1 - A(end - 30)) / max(1e-12, 1 - A(near_until))
    late_all = 1 - A(end - 30)
    Tt = end - t
    Au = lambda tt: (2 / math.pi) * math.asin(math.sqrt((tt - t) / Tt))
    return late_far, late_all, (1 - Au(end - 30)) / max(1e-12, 1 - Au(near_until))


def cohort(d, P, t, i, mode, conf_by, fail_by, years_ok, mod):
    base = d["complete"] & years_ok & P[t]["avail"]
    base[i] = False
    if mode in ("conf", "brk"):
        m = base & (d["side"] == d["side"][i]) & conf_by(t) & (np.abs(d["conf"] - d["conf"][i]) <= 15)
        m &= fail_by(t) if mode == "brk" else ~fail_by(t)
    else:
        m = base & ~conf_by(t) & (d["box"] == d["box"][i])
    pool = np.flatnonzero(m)
    if mode == "wait" and mod[i] >= 0:
        s = pool[mod[pool] == mod[i]]
        if len(s) >= 40: pool = s
    pos = P[t][mode]["pos"]; u0 = pos[i]
    band, sel = None, pool
    for bw in (0.25, 0.5):
        c = pool[np.abs(pos[pool] - u0) <= bw]
        if len(c) >= 40: band, sel = bw, c; break
    return pool, sel, band, u0


def pull_class(mn, tmn, near_until):
    return np.where(tmn <= near_until, 0, np.where(mn >= -0.25, 1, np.where(mn >= -0.75, 2, 3)))


def run(inst, sess):
    d = dense(inst, sess)
    grid, P, conf_by, fail_by = prep(d)
    M = model_arrays(inst, d)
    v = var_clock(d)
    start, end = d["start"], d["end"]
    w = d["idrh"] - d["idrl"]
    side = d["side"]
    e_conf = np.where(side == 1, d["idrh"], d["idrl"])
    rec = []
    for Y in TEST_YEARS:
        test = np.flatnonzero((d["year"] == Y) & d["complete"])
        cal_years = d["year"] < Y
        loyo_years = d["year"] != Y
        for t in grid:
            mod = model_at(M, t, start)
            s_t = (t - start) // 5 - 1
            for i in test:
                if not P[t]["avail"][i]: continue
                mode = ("brk" if fail_by(t)[i] else "conf") if conf_by(t)[i] else "wait"
                if mode == "brk" and side[i] == 0: continue
                near_until = t + (5 if end - t < 45 else 15)
                pool, sel, band, u0 = cohort(d, P, t, i, mode, conf_by, fail_by, cal_years.copy(), mod)
                r = dict(sid=f"{inst}-{sess}-{d['date'][i]}", t=int(t), mode=mode, n=int(len(sel)), band=band)
                # the size of the same cohort from every other year: what a 20-year base gives the live screen
                _, selL, bandL, _ = cohort(d, P, t, i, mode, conf_by, fail_by, loyo_years.copy(), mod)
                r["nL"], r["bandL"] = int(len(selL)), bandL
                if mode != "wait": r["since_conf"] = int(t - d["conf"][i])
                if len(sel) == 0: rec.append(r); continue
                Q = P[t][mode]
                if mode == "conf":
                    r["p_held"] = float(P[t]["held"][sel].mean()); r["y_held"] = bool(P[t]["held"][i])
                    # first STD target as targets21: next half-step beyond the running extreme since the confirmation
                    cs = (d["conf"][i] - start) // 5 - 1
                    hs = d["H"][i, cs + 1:s_t + 1] if side[i] == 1 else d["L"][i, cs + 1:s_t + 1]
                    far = np.nanmax(side[i] * (hs - e_conf[i]) / w[i]) if len(hs) and not np.isnan(hs).all() else u0
                    far = max(far, u0)
                    tgt = max(0.5, (math.floor(far / 0.5 + 1e-9) + 1) * 0.5)
                    r["tgt_gap"] = round(tgt - u0, 3)
                    r["p_tgt"] = float((Q["mx"][sel] >= tgt).mean()); r["y_tgt"] = bool(Q["mx"][i] >= tgt)
                    pc = pull_class(Q["mn"][sel], Q["tmn"][sel], near_until)
                    r["p_pull"] = [float((pc == c).mean()) for c in range(4)]
                    r["y_pull"] = int(pull_class(Q["mn"][i:i + 1], Q["tmn"][i:i + 1], near_until)[0])
                    # fan coverage: share of similar sessions whose whole path stays inside the 20-80 fan
                    X = side[sel, None] * (d["C"][sel, s_t + 1:] - e_conf[sel, None]) / w[sel, None] - Q["pos"][sel, None] + u0
                    ok = ~np.isnan(X)
                    cnt = ok.sum(0)
                    Xs = np.sort(np.where(ok, X, np.inf), axis=0)
                    cols = cnt >= 10
                    if cols.any():
                        idx20 = np.clip(np.round(0.2 * (cnt - 1)).astype(int), 0, None); idx80 = np.clip(np.round(0.8 * (cnt - 1)).astype(int), 0, None)
                        q20 = Xs[idx20, np.arange(Xs.shape[1])]; q80 = Xs[idx80, np.arange(Xs.shape[1])]
                        inside = np.where(ok[:, cols], (X[:, cols] >= q20[cols]) & (X[:, cols] <= q80[cols]), True).all(1)
                        r["fan_cov"] = float(inside.mean())
                        xi = side[i] * (d["C"][i, s_t + 1:] - e_conf[i]) / w[i]
                        oki = ~np.isnan(xi) & cols
                        r["fan_y"] = bool(((xi[oki] >= q20[oki]) & (xi[oki] <= q80[oki])).all()) if oki.any() else None
                    # time pile-up
                    if end - t >= (210 if sess == "RDR" else 180):
                        lf, la, lu = arcsine_late(v, start, t, near_until, end)
                        r["arc_far"], r["arc_all"], r["arc_flat"] = lf, la, lu
                        r["unif"] = 30.0 / (end - near_until)
                        for role, tt in (("pull", Q["tmn"]), ("cont", Q["tmx"])):
                            allt = tt[sel]; far_t = allt[allt > near_until]
                            r[f"late_all_{role}"] = float((allt > end - 30).mean())
                            if len(far_t) >= 10: r[f"late_{role}"] = float((far_t > end - 30).mean())
                            r[f"y_late_{role}"] = bool(tt[i] > end - 30) if tt[i] > near_until else None
                elif mode == "wait":
                    cross = np.where(d["conf"][sel] > t, side[sel], 0)
                    r["p_up"] = float((cross == 1).mean()); r["y_up"] = bool(d["conf"][i] > t and side[i] == 1)
                    uH_today = (d["drh"][i] - d["idrl"][i]) / w[i]; uH_own = (d["drh"][sel] - d["idrl"][sel]) / w[sel]
                    r["p_drh_mapped"] = float((Q["mx"][sel] >= uH_today).mean()); r["p_drh_own"] = float((Q["mx"][sel] >= uH_own).mean())
                    r["y_drh"] = bool(Q["mx"][i] >= uH_today)
                rec.append(r)
    return rec


if __name__ == "__main__":
    out = {}
    t0 = time.time()
    for inst in INST:
        for sess in ("RDR", "ODR"):
            out[f"{inst}-{sess}"] = run(inst, sess)
            print(inst, sess, len(out[f"{inst}-{sess}"]), f"{time.time() - t0:.0f}s", flush=True)
    OUT.write_text(json.dumps(out), encoding="utf-8")   # per-session records stay local (lab/.runtime is git-ignored)
    print("done")
