"""Check of the working screen's place percentages after the operator's decision of 2026-09-29: a place's share = how
often price of similar sessions CAME into the place (a place ahead of the price), not the final extreme.

1) Calibration: for every test session of 2016-2025 every 15 minutes (walk-forward cohorts, years before the test year,
   the screen's own similar-session rules from screen_replay.cohort), for each place ahead of the price on each side:
   forecast = share of the cohort that reached the place's near edge after the minute; outcome = did today's session.
   Brier skill against a constant equal to the realised frequency of the same states (as in the audit), by the price
   match (● ±0,25 IDR, ◐ ±0,5, ○ none — ○ is not shown on the screen), session-clustered bootstrap intervals.
2) Order (confirmed states): for continuation places, did price come there BEFORE a wick beyond its own opposite DR
   (a stop right behind DR)? Forecast = share of the cohort that did, outcome = today.

Places as the screen defines them (design/sozvezdiya-22/src/app.js zoneDefs). Coordinates as the screen measures the
similar sessions: each in its own scale (0 = its confirmation-side IDR edge, 1 IDR = 1). Per-state records stay local.
python -B studies/audit_2026_09_29/place_arrivals.py
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
from screen_replay import cohort  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "lab" / ".runtime" / "audit_place_arrivals.json"


def edges(mode, u0, uH=None, uL=None):
    """(role, name, edge, direction) of the places ahead of the price, as zoneDefs draws them."""
    out = []
    if mode == "wait":
        for nm, e in (("DR high", uH), ("+1,0", 2.0)):
            if e > u0: out.append(("up", nm, e, 1))
        for nm, e in (("DR low", uL), ("-1,0", -1.0)):
            if e < u0: out.append(("dn", nm, e, -1))
        return out
    s1 = math.ceil((u0 + 0.25) / 0.5) * 0.5
    out += [("cont", "next half-step", s1, 1), ("cont", "second half-step", s1 + 0.5, 1)]
    for nm, e in (("-0,25", -0.25), ("-0,75", -0.75)):
        if e < u0: out.append(("pull", nm, e, -1))
    return out


def run(inst, sess):
    d = dense(inst, sess)
    grid, P, conf_by, fail_by = prep(d)
    M = model_arrays(inst, d)
    start = d["start"]
    side, w = d["side"], d["idrh"] - d["idrl"]
    e_conf = np.where(side == 1, d["idrh"], d["idrl"])
    opp = np.where(side == 1, d["drl"], d["drh"])
    rec = []
    for Y in TEST_YEARS:
        test = np.flatnonzero((d["year"] == Y) & d["complete"])
        cal = d["year"] < Y
        for t in grid:
            mod = model_at(M, t, start)
            s_t = (t - start) // 5 - 1
            for i in test:
                if not P[t]["avail"][i]: continue
                mode = ("brk" if fail_by(t)[i] else "conf") if conf_by(t)[i] else "wait"
                if mode == "brk" and side[i] == 0: continue
                _, sel, band, u0 = cohort(d, P, t, i, mode, conf_by, fail_by, cal.copy(), mod)
                if len(sel) == 0: continue
                Q = P[t][mode]
                match = "p25" if band == 0.25 else "p50" if band == 0.5 else "none"
                sid = f"{inst}-{sess}-{d['date'][i]}"
                uH = (d["drh"][i] - d["idrl"][i]) / w[i]; uL = (d["drl"][i] - d["idrl"][i]) / w[i]
                ed = edges(mode, u0, uH, uL)
                if mode == "conf":
                    S = np.r_[sel, i]
                    H, L = d["H"][S, s_t + 1:], d["L"][S, s_t + 1:]
                    up = side[S, None] * (np.where(side[S, None] == 1, H, L) - e_conf[S, None]) / w[S, None]
                    dn = side[S, None] * (np.where(side[S, None] == 1, L, H) - e_conf[S, None]) / w[S, None]
                    ou = (side[S] * (opp[S] - e_conf[S]) / w[S])[:, None]
                    first = lambda hit: np.where(hit.any(1), hit.argmax(1), 10 ** 6)
                    t_stop = first(np.nan_to_num(dn, nan=np.inf) < ou)
                for k, (role, nm, e, dirn) in enumerate(ed):
                    v = Q["mx"] if dirn == 1 else Q["mn"]
                    hit = (v >= e) if dirn == 1 else (v <= e)
                    r = dict(sid=sid, t=int(t), mode=mode, match=match, role=role, rank=k, p=float(hit[sel].mean()), y=bool(hit[i]), n=int(len(sel)))
                    if mode == "conf" and role == "cont":
                        t_hit = first(np.nan_to_num(up, nan=-np.inf) >= e)
                        before = t_hit < t_stop
                        r["p_first"] = float(before[:-1].mean()); r["y_first"] = bool(before[-1])
                    rec.append(r)
    return rec


def bss(p, y, sid, B=300, rng=np.random.default_rng(7)):
    p, y = np.asarray(p, float), np.asarray(y, float)
    base = lambda pp, yy: 1 - np.mean((pp - yy) ** 2) / max(1e-12, np.mean((yy.mean() - yy) ** 2))
    val = base(p, y)
    ids, inv = np.unique(sid, return_inverse=True)
    groups = [np.flatnonzero(inv == g) for g in range(len(ids))]
    bs = []
    for _ in range(B):
        idx = np.concatenate([groups[g] for g in rng.integers(0, len(groups), len(groups))])
        bs.append(base(p[idx], y[idx]))
    return val, np.percentile(bs, [2.5, 97.5])


def report(out):
    lines = []
    for key, rec in out.items():
        for mode in ("conf", "wait", "brk"):
            for match in ("p25", "p50", "none"):
                R = [r for r in rec if r["mode"] == mode and r["match"] == match]
                if len(R) < 200: continue
                p = [r["p"] for r in R]; y = [r["y"] for r in R]; s = [r["sid"] for r in R]
                v, ci = bss(p, y, s)
                bins = np.clip((np.array(p) * 5).astype(int), 0, 4)
                rel = " ".join(f"{int(b * 20)}-{int(b * 20 + 20)}%:{100 * np.mean(np.array(p)[bins == b]):.0f}->{100 * np.mean(np.array(y)[bins == b]):.0f}" for b in range(5) if (bins == b).sum() >= 50)
                line = f"{key} {mode:4s} {match:4s} states {len(R):6d}  BSS {100 * v:5.1f}% [{100 * ci[0]:.1f}; {100 * ci[1]:.1f}]  forecast->real {rel}"
                F = [r for r in R if "p_first" in r]
                if len(F) >= 200:
                    v2, ci2 = bss([r["p_first"] for r in F], [r["y_first"] for r in F], [r["sid"] for r in F])
                    line += f"\n{'':9s} order: continuation place before a wick beyond DR  BSS {100 * v2:5.1f}% [{100 * ci2[0]:.1f}; {100 * ci2[1]:.1f}]  mean forecast {100 * np.mean([r['p_first'] for r in F]):.0f}% real {100 * np.mean([r['y_first'] for r in F]):.0f}%"
                lines.append(line)
    return "\n".join(lines)


if __name__ == "__main__":
    out, t0 = {}, time.time()
    for inst in INST:
        for sess in ("RDR", "ODR"):
            out[f"{inst}-{sess}"] = run(inst, sess)
            print(inst, sess, len(out[f"{inst}-{sess}"]), f"{time.time() - t0:.0f}s", flush=True)
    OUT.write_text(json.dumps(out), encoding="utf-8")
    print(report(out))
