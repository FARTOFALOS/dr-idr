"""Intermarket study: does the state of the other two indices at a DR confirmation change how it plays out?

Written before counting (2026-09-24). Episodes: lab/.runtime/market_{nq,es,ym}_meta.json (NQ/ES/YM,
2006-2025, 2026 hidden), one session (default RDR). Unit: trading day; each focal instrument is reported separately
(the three are dependent on the same day and are never pooled).

1. Co-movement (description): direction agreement of the three confirmations on the same day, confirmation-time
   differences, same-day correlation of extension and of DR true.
2. Prefix state (the question): at focal instrument X's confirmation minute tau_X (close of the confirming M5), each
   other instrument Y is SAME (confirmed the same direction at or before tau_X), OPP (confirmed the opposite way at or
   before tau_X) or NOT_YET. Groups: ALL_AGREE (both SAME), HALF (one SAME, one NOT_YET), LEAD (both NOT_YET),
   DIVERGE (any OPP). Everything used is known at tau_X.
   Outcomes of X from tau_X to the session end: DR true, touch of +1.0 IDR, median max retracement (IDR).
3. Decision rule (fixed now): a relationship exists if DR true of ALL_AGREE vs LEAD, or of DIVERGE vs the rest,
   differs with two-proportion |z| >= 3 for every focal instrument, with the same sign in all three epochs.
   Otherwise: co-movement only, no usable conditional difference at this resolution.
4. Control added after the first read (it can only remove a claim, never rescue one): DR true depends on how much
   session is left after confirmation, and the groups confirm at different times. Differences are re-measured
   inside 30-minute confirmation-time strata (Mantel-Haenszel weights n1*n2/(n1+n2)); median confirmation time per
   group is reported. A difference that vanishes inside strata is a timing effect, not an intermarket one.

Run from the repository root: python -B studies/intermarket.py [RDR|ODR|ADR]
"""
import json, math, sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RUNTIME = HERE.parent / "lab" / ".runtime"
INST = ("NQ", "ES", "YM")
EPOCHS = (("2006-12", "2006", "2012"), ("2013-19", "2013", "2019"), ("2020-25", "2020", "2025"))
TARGET = 1.0


def load(session):
    frames = []
    for i in INST:
        E = json.loads((RUNTIME / f"market_{i.lower()}_meta.json").read_text(encoding="utf-8"))["episodes"]
        d = pd.DataFrame([e for e in E if e["session"] == session])
        d["inst"] = i
        frames.append(d[["inst", "date", "direction", "confirmation", "dr_true", "extension", "retracement", "complete"]])
    return pd.concat(frames, ignore_index=True)


def wilson(k, n):
    if not n: return (np.nan, np.nan)
    z = 1.96; p = k / n; den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (round(100 * (c - h), 1), round(100 * (c + h), 1))


def ztest(k1, n1, k2, n2):
    if not n1 or not n2: return None
    p = (k1 + k2) / (n1 + n2); se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return round((k1 / n1 - k2 / n2) / se, 2) if se > 0 else None


def outcome(g):
    t = g[g.dr_true.notna()]
    k, n = int((t.dr_true == True).sum()), len(t)  # noqa: E712
    c = g[g.complete]
    hit = int(((g.extension >= TARGET)).sum()); hn = int(((g.extension >= TARGET) | g.complete).sum())
    return dict(n=len(g), dr_true_pct=round(100 * k / n, 1) if n else None, dr_true_k=k, dr_true_n=n, dr_true_ci=wilson(k, n),
                touch_1idr_pct=round(100 * hit / hn, 1) if hn else None,
                median_retr=round(float(c.retracement.median()), 2) if len(c) else None)


def main():
    session = (sys.argv[1] if len(sys.argv) > 1 else "RDR").upper()
    D = load(session)
    W = D.pivot(index="date", columns="inst")
    days = W.index[W["direction"].notna().all(axis=1)]
    res = dict(session=session, days_all_three=int(len(days)))
    # 1. co-movement
    dirs = W.loc[days, "direction"]
    agree = (dirs.nunique(axis=1) == 1)
    res["same_direction_all_three_pct"] = round(100 * agree.mean(), 1)
    shuffled = []
    rng = np.random.default_rng(20260924)
    for _ in range(200):
        p = pd.DataFrame({i: rng.permutation(dirs[i].to_numpy()) for i in INST})
        shuffled.append((p.nunique(axis=1) == 1).mean())
    res["same_direction_if_days_unrelated_pct"] = round(100 * float(np.mean(shuffled)), 1)
    tc = W.loc[days, "confirmation"]
    res["confirmation_spread_min_median"] = float((tc.max(axis=1) - tc.min(axis=1)).median())
    res["same_confirmation_minute_all_three_pct"] = round(100 * float((tc.nunique(axis=1) == 1).mean()), 1)
    ext = W.loc[days[agree.to_numpy()], "extension"].astype(float)
    res["extension_corr_same_day_agreeing"] = {f"{a}-{b}": round(float(ext[a].corr(ext[b])), 3) for a, b in (("NQ", "ES"), ("NQ", "YM"), ("ES", "YM"))}
    first = tc.idxmin(axis=1)[(tc.nunique(axis=1) > 1) | True]
    res["first_to_confirm_share"] = {i: round(100 * float(((tc[i] == tc.min(axis=1)) & (tc.eq(tc.min(axis=1), axis=0).sum(axis=1) == 1)).mean()), 1) for i in INST}
    # 2. prefix state at each focal confirmation
    rows = []
    for x in INST:
        others = [y for y in INST if y != x]
        for d in W.index[W[("direction", x)].notna()]:
            tx, sx = W.at[d, ("confirmation", x)], W.at[d, ("direction", x)]
            st = []
            for y in others:
                ty, sy = W.at[d, ("confirmation", y)], W.at[d, ("direction", y)]
                if pd.isna(sy) or ty > tx: st.append("NOT_YET")
                else: st.append("SAME" if sy == sx else "OPP")
            grp = "DIVERGE" if "OPP" in st else ("ALL_AGREE" if st == ["SAME", "SAME"] else ("HALF" if "SAME" in st else "LEAD"))
            rows.append(dict(inst=x, date=d, group=grp, tau=int(tx), dr_true=W.at[d, ("dr_true", x)], extension=W.at[d, ("extension", x)],
                             retracement=W.at[d, ("retracement", x)], complete=bool(W.at[d, ("complete", x)])))
    R = pd.DataFrame(rows)
    R["dr_true"] = R.dr_true.map(lambda v: None if v is None or (isinstance(v, float) and np.isnan(v)) else bool(v))
    R["year"] = R.date.str[:4]
    res["groups"] = {}; verdict = {}
    for x in INST:
        res["groups"][x] = {}
        for ep, lo, hi in (("all", "0000", "9999"),) + EPOCHS:
            g = R[(R.inst == x) & (R.year >= lo) & (R.year <= hi)]
            res["groups"][x][ep] = {k: outcome(v) for k, v in g.groupby("group")}
            o = res["groups"][x][ep]
            a, l = o.get("ALL_AGREE"), o.get("LEAD")
            dv = o.get("DIVERGE"); rest = g[g.group != "DIVERGE"]
            rest_o = outcome(rest)
            res["groups"][x][ep]["_z_all_agree_vs_lead"] = ztest(a["dr_true_k"], a["dr_true_n"], l["dr_true_k"], l["dr_true_n"]) if a and l else None
            res["groups"][x][ep]["_z_diverge_vs_rest"] = ztest(dv["dr_true_k"], dv["dr_true_n"], rest_o["dr_true_k"], rest_o["dr_true_n"]) if dv else None
        verdict[x] = {}
        for key in ("_z_all_agree_vs_lead", "_z_diverge_vs_rest"):
            zs = [res["groups"][x][ep][key] for ep, _, _ in EPOCHS]
            verdict[x][key] = bool(abs(res["groups"][x]["all"][key] or 0) >= 3 and all(z is not None for z in zs)
                                   and len({np.sign(z) for z in zs}) == 1)
    # 4. timing control
    R["stratum"] = (R.tau - 1) // 30
    def mh(g, a_mask, b_mask):
        num = den = var = 0.0
        for _, s_ in g[g.dr_true.notna()].groupby("stratum"):
            A = s_[a_mask(s_)].dr_true.astype(float); B = s_[b_mask(s_)].dr_true.astype(float)
            if len(A) < 5 or len(B) < 5: continue
            w = len(A) * len(B) / (len(A) + len(B)); pa, pb = A.mean(), B.mean()
            num += w * (pa - pb); den += w; var += w * w * (pa * (1 - pa) / len(A) + pb * (1 - pb) / len(B))
        return (round(float(100 * num / den), 1), round(float(num / math.sqrt(var)), 2) if var > 0 else None) if den else (None, None)
    res["timing_control"] = {}
    for x in INST:
        res["timing_control"][x] = {}
        for ep, lo, hi in (("all", "0000", "9999"),) + EPOCHS:
            g = R[(R.inst == x) & (R.year >= lo) & (R.year <= hi)]
            res["timing_control"][x][ep] = dict(
                median_conf_time={k: int(v.tau.median()) for k, v in g.groupby("group")},
                diverge_minus_rest_pp_z=mh(g, lambda s_: s_.group == "DIVERGE", lambda s_: s_.group != "DIVERGE"),
                agree_minus_lead_pp_z=mh(g, lambda s_: s_.group == "ALL_AGREE", lambda s_: s_.group == "LEAD"))
    res["verdict_per_instrument"] = verdict
    res["relationship"] = {key: all(verdict[x][key] for x in INST) for key in ("_z_all_agree_vs_lead", "_z_diverge_vs_rest")}
    out = HERE / f"intermarket_{session.lower()}.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "groups"}, ensure_ascii=False, indent=1, default=str))
    for x in INST:
        print("==", x)
        for ep in ("all",) + tuple(e for e, _, _ in EPOCHS):
            o = res["groups"][x][ep]
            line = " | ".join(f"{g}: n {o[g]['n']}, DRtrue {o[g]['dr_true_pct']}% {o[g]['dr_true_ci']}, +1IDR {o[g]['touch_1idr_pct']}%, retr {o[g]['median_retr']}"
                              for g in ("ALL_AGREE", "HALF", "LEAD", "DIVERGE") if g in o)
            print(f"  {ep:7s} {line} || z agree-lead {o['_z_all_agree_vs_lead']}, z diverge-rest {o['_z_diverge_vs_rest']}")
        for ep in ("all",) + tuple(e for e, _, _ in EPOCHS):
            t = res["timing_control"][x][ep]
            print(f"  timing {ep:7s} median conf {t['median_conf_time']} | inside strata: diverge-rest {t['diverge_minus_rest_pp_z']} pp,z | agree-lead {t['agree_minus_lead_pp_z']} pp,z")


if __name__ == "__main__":
    main()
