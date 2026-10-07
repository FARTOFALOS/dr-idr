"""DR-LAB-NOW-1.0 — the walk-forward validator and the promotion of the layer «Сейчас» (spec §12-14, §24 stages 2-3).

    python -B lab/now24_validate.py            # every instrument, session and family view; writes the passport

Every historical session is replayed as if it were today (spec §13.1): its family is the sessions of the same key
(instrument x session x weekday x direction x 15-minute window of its activation) of STRICTLY EARLIER dates, chosen
exactly as lab/scene24.py chooses them; it is a target only when that family has at least 40 sessions (§13.2). At every
closed M5 after its activation while its scene is alive (complete prefix; the original phase until its own break), the
forecasts of B0 and of M1-M3 are computed from the family only, then the target's own outcome is attached (§13.4).

Scores (§14): Brier of P(new extreme) against B0 on the cuts where a matcher has support >= 20; the 95 % interval of the
difference by resampling whole calendar weeks (pooled over instruments: one week is one unit); CRPS of the remaining
movement d and of the time tau (the empirical ensemble of the matched sessions). Promotion is code, by the declared
gates, per family view (confirmation / break) and event (R / X), pooled over instruments and sessions:
  B0 -> M1 -> M2 -> M3, each must beat B0 (BSS > 0, interval above 0, support on >= 50 % of eligible cuts) and the
  current winner (interval of their difference above 0); the winner's tolerance 0.25 is then checked at 0.20 and 0.30
  (a negative skill = UNSTABLE: the product shows B0). An instrument x session cell where the promoted matcher is
  clearly worse than B0 (the whole interval below 0) falls back to B0 there.
Outputs: lab/.runtime/now24_validation.json (the passport the live API reads), lab/.runtime/now24_records.npz (every
forecast record), meaning/lens/2026-10-06-now-1.0/proverka.md (aggregates only, no dates or prices).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import now24 as N  # noqa: E402
import scene24  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "meaning" / "lens" / "2026-10-06-now-1.0" / "DR-LAB-NOW-1.0.md"
REPORT = ROOT / "meaning" / "lens" / "2026-10-06-now-1.0" / "proverka.md"
INSTS = ("NQ", "ES", "YM")
SESSIONS = ("ADR", "ODR", "RDR")
VIEWS = ("conf", "brk")
TOLS = {"t25": (1, 4), "t20": (1, 5), "t30": (3, 10)}
KEYS = ["B0"] + [f"{m}@{t}" for t in TOLS for m in ("M1", "M2", "M3")]
# EXPLORATION, never a product candidate (spec §8: no matcher may be added after the mass test started): E1 compares the
# distance of the last close from the extreme already made (c - r for R, x - c for X) within 0.10 — the state a random
# walk's chance of a new extreme depends on; added after NOW-1.0's result to motivate a version 1.1 (meaning/15)
KEYS_X = ["E1"]
KEYS = KEYS + KEYS_X


def universe(inst, session, view):
    """Every session of the base that joins a family of this view, chosen by the rules of scene24._snapshot."""
    B = scene24._base(inst)
    start, formed, end = scene24.SESS[session]
    shift = scene24.SHIFT[session]
    miss = scene24._missing(inst, B, session)
    grid = list(range(formed + 5, end + 1, 5))
    out = []
    for i, m in enumerate(B["boxes"]):
        if m["session"] != session: continue
        gaps = miss.get(i, [])
        conf = None if m["conf"] is None else int(m["conf"]) - shift
        if conf is None or any(T < conf for T in gaps): continue
        side = m["side"]
        fail = None if m["fail"] is None else int(m["fail"]) - shift
        if view == "conf":
            act, d, win = conf, side, scene24.window_of(conf, formed)
        else:
            if fail is None or any(conf < T < fail for T in gaps): continue
            act, d, win = fail, -side, scene24.window_of(fail, formed)
        rows = scene24._rows(B, i, shift)
        e = m["idr_high"] if d == 1 else m["idr_low"]
        w = m["idr_high"] - m["idr_low"]
        if w <= 0: continue
        P = np.full((len(grid), 3), np.nan)
        for j, T in enumerate(grid):
            r = rows.get(T)
            if r is not None: P[j] = scene24.directed(r, d, e)
        oppv = d * ((m["dr_low"] if side == 1 else m["dr_high"]) - e) if view == "conf" else None
        out.append(dict(id=scene24._sid(inst, m), date=m["date"], weekday=m["weekday"], side=side, win=win,
                        a=(act - formed - 5) // 5, w=int(w), P=P, oppv=oppv))
    return out, grid


def crps(X, M, y):
    """CRPS of the empirical ensemble X[:, c] restricted to M[:, c] against y[c] (nan where undefined)."""
    n = M.sum(0).astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        t1 = np.where(M, np.abs(X - y[None, :]), 0).sum(0) / n
        Xs = np.sort(np.where(M, X, np.inf), 0)
        i = np.arange(1, X.shape[0] + 1)[:, None]
        wts = np.where(i <= n[None, :], 2 * i - n[None, :] - 1, 0)
        t2 = 2 * (wts * np.where(np.isfinite(Xs), Xs, 0)).sum(0) / n ** 2
        out = t1 - 0.5 * t2
    out[(n == 0) | np.isnan(y)] = np.nan
    return out


def iso_week(date):
    y, w, _ = dt.date.fromisoformat(date).isocalendar()
    return y * 100 + w


def run_universe(inst, session, view, rec, uid):
    U, grid = universe(inst, session, view)
    L = len(grid)
    sers = [N.series(u["P"], u["a"], u["oppv"]) for u in U]
    groups = {}
    for j, u in enumerate(U): groups.setdefault((u["weekday"], u["side"], u["win"]), []).append(j)
    n_t = 0
    for gk, idxs in groups.items():
        idxs.sort(key=lambda j: U[j]["date"])
        if len(idxs) <= RW: continue
        Sg = N.stack([sers[j] for j in idxs])
        wg = np.array([U[j]["w"] for j in idxs], dtype=np.int64)
        ag = np.array([U[j]["a"] for j in idxs], dtype=np.int64)
        dates = [U[j]["date"] for j in idxs]
        for t in range(len(idxs)):
            nb = sum(1 for dd in dates[:t] if dd < dates[t])            # strictly earlier dates only (spec §2.1, §13.1)
            if nb < RW: continue
            i = idxs[t]
            T, w_t, a_t = sers[i], U[i]["w"], U[i]["a"]
            cuts = [c for c in range(a_t + 1, L - 1) if T["valid"][c]]
            if not cuts: continue
            S = {k: v[:nb] for k, v in Sg.items()}
            w, am = wg[:nb], ag[:nb]
            Mk = N.masks(S, w, am, T, w_t, a_t, cuts, TOLS["t25"])
            shape = Mk["shape"]                                           # the path condition alone (M3 = M2 & shape)
            sets = {"B0": Mk["B0"]}
            for tn, tol in TOLS.items():
                W = w[:, None]
                V = Mk["B0"]
                m1R = V & N._near(S["r"][:, cuts], W, T["r"][cuts][None, :], w_t, tol)
                m1X = V & N._near(S["x"][:, cuts], W, T["x"][cuts][None, :], w_t, tol)
                m2 = m1R & m1X
                sets[f"M1R@{tn}"], sets[f"M1X@{tn}"], sets[f"M2@{tn}"], sets[f"M3@{tn}"] = m1R, m1X, m2, m2 & shape
            W = w[:, None]
            V = Mk["B0"]
            sets["E1R"] = V & N._near(S["cl"][:, cuts] - S["r"][:, cuts], W, (T["cl"][cuts] - T["r"][cuts])[None, :], w_t, (1, 10))
            sets["E1X"] = V & N._near(S["x"][:, cuts] - S["cl"][:, cuts], W, (T["x"][cuts] - T["cl"][cuts])[None, :], w_t, (1, 10))
            C = len(cuts)
            rec["u"].append(np.full(C, uid, np.int16)); rec["tgt"].append(np.full(C, i, np.int32))
            rec["week"].append(np.full(C, iso_week(U[i]["date"]), np.int32)); rec["cut"].append(np.array(cuts, np.int16))
            rec["nbase"].append(np.full(C, nb, np.int16)); rec["year"].append(np.full(C, int(U[i]["date"][:4]), np.int16))
            for ev in ("R", "X"):
                ynew = T["new" + ev][cuts].astype(np.int8)
                yd = np.where(T["d" + ev][cuts] >= 0, T["d" + ev][cuts] / w_t, np.nan)
                yt = np.where((ynew == 1) & (T["tau" + ev][cuts] > 0), T["tau" + ev][cuts].astype(float), np.nan)
                rec[f"ynew_{ev}"].append(ynew); rec[f"yd_{ev}"].append(yd.astype(np.float32)); rec[f"yt_{ev}"].append(yt.astype(np.float32))
                new = S["new" + ev][:, cuts]
                dv = S["d" + ev][:, cuts]
                dn = dv / w[:, None]
                tau = S["tau" + ev][:, cuts].astype(float)
                for key in KEYS:
                    M = sets["B0"] if key == "B0" else sets["E1" + ev] if key == "E1" else sets[key.replace("M1@", "M1" + ev + "@")]
                    tot = M.sum(0)
                    yes = (M & (new == 1)).sum(0)
                    unk = (M & (new == -1)).sum(0)
                    kn = tot - unk
                    with np.errstate(invalid="ignore", divide="ignore"):
                        p = np.where(kn > 0, yes / np.maximum(kn, 1), np.nan)
                    rec[f"n_{key}_{ev}"].append(tot.astype(np.int16))
                    rec[f"p_{key}_{ev}"].append(p.astype(np.float32))
                    rec[f"cd_{key}_{ev}"].append(crps(dn, M & (dv >= 0), yd).astype(np.float32))
                    rec[f"ct_{key}_{ev}"].append(crps(tau, M & (new == 1) & (tau > 0), yt).astype(np.float32))
            n_t += 1
    return n_t, len(U)


RW = N.RULES["warmup"]


def boot(diff, week, reps, seed):
    """Mean of diff and its 95 % interval by resampling whole weeks."""
    uw, inv = np.unique(week, return_inverse=True)
    s = np.bincount(inv, weights=diff)
    n = np.bincount(inv).astype(float)
    rng = np.random.default_rng(seed)
    out = np.empty(reps)
    for b0 in range(0, reps, 200):
        k = rng.integers(0, len(uw), size=(min(200, reps - b0), len(uw)))
        out[b0:b0 + len(k)] = s[k].sum(1) / n[k].sum(1)
    return float(diff.mean()), float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def score(R, sel, ev, key, kind="brier", ref="B0", seed=0):
    """Skill of `key` against `ref` on the records sel (bool). kind: brier (P new) / magnitude (CRPS d) / time (CRPS tau)."""
    if kind == "brier":
        y = R[f"ynew_{ev}"].astype(float)
        a = (R[f"p_{ref}_{ev}"] - y) ** 2
        b = (R[f"p_{key}_{ev}"] - y) ** 2
    else:
        f = "cd" if kind == "magnitude" else "ct"
        a, b = R[f"{f}_{ref}_{ev}"].astype(float), R[f"{f}_{key}_{ev}"].astype(float)
    ok = sel & np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 30: return dict(n=int(ok.sum()), skill=None, diff=None, lo=None, hi=None, weeks=0)
    m, lo, hi = boot(a[ok] - b[ok], R["week"][ok], N.RULES["boot"], seed)
    return dict(n=int(ok.sum()), weeks=int(len(np.unique(R["week"][ok]))), skill=round(1 - float(b[ok].mean()) / float(a[ok].mean()), 5),
                diff=round(m, 6), lo=round(lo, 6), hi=round(hi, 6))


def promote(R, ev, sel_view, seed):
    """The ladder of spec §12 on the records of one view, pooled over instruments and sessions."""
    y_ok = R[f"ynew_{ev}"] >= 0
    elig = sel_view & y_ok & np.isfinite(R[f"p_B0_{ev}"])
    if not elig.any():
        # no target ever had a family of >= 40 sessions of this view: the path cannot be tested; the product shows B0
        return dict(matcher=None, status="NOT_TESTABLE", table={}, eligible_records=0, eligible_targets=0)
    sup = lambda key: R[f"n_{key}_{ev}"] >= N.RULES["support"]
    table, winner, wkey = {}, "B0", "B0"
    for m in ("M1", "M2", "M3"):
        key = f"{m}@t25"
        cov = float(sup(key)[elig].mean()) if elig.any() else 0.0
        vs_b0 = score(R, elig & sup(key), ev, key, "brier", "B0", seed + 1)
        passes = vs_b0["skill"] is not None and vs_b0["skill"] > 0 and vs_b0["lo"] > 0 and cov >= N.RULES["coverage"]
        vs_w = None
        if passes and winner != "B0":
            vs_w = score(R, elig & sup(key) & sup(wkey), ev, key, "brier", wkey, seed + 2)
            passes = vs_w["skill"] is not None and vs_w["lo"] > 0
        table[m] = dict(coverage=round(cov, 4), vs_B0=vs_b0, vs_winner=vs_w, promoted=passes)
        if passes: winner, wkey = m, key
    out = dict(matcher=None, status="TIME_BASELINE", table=table, eligible_records=int(elig.sum()),
               eligible_targets=int(len(np.unique(R["tgt"][elig].astype(np.int64) + 100000 * R["u"][elig].astype(np.int64)))) if elig.any() else 0)
    if winner == "B0": return out
    # spec §14.4: the tolerance's neighbours only check fragility, they are never candidates
    sens = {}
    for tn in ("t20", "t30"):
        k = f"{winner}@{tn}"
        sens[tn] = score(R, elig & sup(k), ev, k, "brier", "B0", seed + 3)
    unstable = any(v["skill"] is None or v["skill"] < 0 for v in sens.values())
    mag = score(R, elig & sup(wkey), ev, wkey, "magnitude", "B0", seed + 4)
    tim = score(R, elig & sup(wkey), ev, wkey, "time", "B0", seed + 5)
    out.update(matcher=winner, status="UNSTABLE" if unstable else "VALIDATED", sensitivity=sens,
               brier_skill=table[winner]["vs_B0"]["skill"], magnitude=mag, time=tim,
               magnitude_skill=mag["skill"], time_skill=tim["skill"])
    out["magnitude_mode"] = "PATH" if (mag["skill"] or 0) > 0 and (mag["lo"] or 0) > 0 else "B0"
    out["time_mode"] = "PATH" if (tim["skill"] or 0) > 0 and (tim["lo"] or 0) > 0 else "B0"
    return out


def main():
    t0 = time.time()
    if "--rescore" in sys.argv:                                   # the decisions and the report again from the saved records
        Z = np.load(N.RUNTIME / "now24_records.npz")
        U = json.loads(str(Z["universes"]))
        R = {k: Z[k] for k in Z.files if k != "universes"}
        return decide(R, U, t0)
    rec = {k: [] for k in ("u", "tgt", "week", "cut", "nbase", "year")}
    for ev in ("R", "X"):
        for k in ("ynew", "yd", "yt"): rec[f"{k}_{ev}"] = []
        for key in KEYS:
            for f in ("n", "p", "cd", "ct"): rec[f"{f}_{key}_{ev}"] = []
    U = []
    for inst in INSTS:
        for session in SESSIONS:
            for view in VIEWS:
                uid = len(U)
                n_t, n_u = run_universe(inst, session, view, rec, uid)
                U.append(dict(inst=inst, session=session, view=view, targets=n_t, sessions=n_u))
                print(f"  {inst} {session} {view}: {n_u} sessions, {n_t} targets  ({time.time() - t0:.0f} s)", flush=True)
    R = {k: (np.concatenate(v) if v else np.array([])) for k, v in rec.items()}
    np.savez_compressed(N.RUNTIME / "now24_records.npz", **R, universes=json.dumps(U))
    decide(R, U, t0)


def decide(R, U, t0):
    spec_hash = hashlib.sha1(SPEC.read_bytes()).hexdigest()[:12] if SPEC.exists() else None
    dec, report = {}, {}
    uview = np.array([U[u]["view"] for u in R["u"]]) if len(R["u"]) else np.array([])
    ucell = np.array([U[u]["inst"] + ":" + U[u]["session"] for u in R["u"]]) if len(R["u"]) else np.array([])
    for vi, view in enumerate(VIEWS):
        for ei, ev in enumerate(("R", "X")):
            sel = uview == view
            P = promote(R, ev, sel, 1000 * vi + 100 * ei)
            if P["status"] == "NOT_TESTABLE":
                dec[f"{view}:{ev}"] = dict(status="NOT_TESTABLE", matcher=None, research_matcher=None, magnitude="B0", time="B0", cells_fallback=[])
                report[f"{view}:{ev}"] = dict(P, cells={}, cells_fallback=[])
                print(f"  {view}:{ev} -> NOT_TESTABLE", flush=True)
                continue
            # per instrument x session: the promoted matcher (or M1 when none) against B0 in each cell
            cells, fallback = {}, []
            show = P["matcher"] or "M1"
            for cell in sorted(set(ucell[sel])):
                cs = sel & (ucell == cell) & (R[f"ynew_{ev}"] >= 0) & np.isfinite(R[f"p_B0_{ev}"])
                k = f"{show}@t25"
                sc = score(R, cs & (R[f"n_{k}_{ev}"] >= N.RULES["support"]), ev, k, "brier", "B0", 7)
                b0 = R[f"p_B0_{ev}"][cs]
                yy = R[f"ynew_{ev}"][cs].astype(float)
                cells[cell] = dict(matcher=show, records=int(cs.sum()), base_rate=round(float(yy.mean()), 4) if cs.any() else None,
                                   brier_B0=round(float(((b0 - yy) ** 2).mean()), 5) if cs.any() else None,
                                   coverage=round(float((R[f"n_{k}_{ev}"][cs] >= N.RULES["support"]).mean()), 4) if cs.any() else None, vs_B0=sc)
                if P["matcher"] and sc["hi"] is not None and sc["hi"] < 0: fallback.append(cell)
            P["cells"] = cells
            P["cells_fallback"] = fallback
            dec[f"{view}:{ev}"] = dict(status=P["status"], matcher=P["matcher"] if P["status"] == "VALIDATED" else None,
                                       research_matcher=P["matcher"], magnitude=P.get("magnitude_mode", "B0"), time=P.get("time_mode", "B0"),
                                       brier_skill=P.get("brier_skill"), magnitude_skill=P.get("magnitude_skill"), time_skill=P.get("time_skill"),
                                       cells_fallback=fallback)
            report[f"{view}:{ev}"] = P
            print(f"  {view}:{ev} -> {P['status']} {P['matcher'] or ''}", flush=True)
    explo = {}
    if f"p_E1_R" in R:
        for view in VIEWS:
            for ev in ("R", "X"):
                elig = (uview == view) & (R[f"ynew_{ev}"] >= 0) & np.isfinite(R[f"p_B0_{ev}"])
                if not elig.any(): continue
                sup = R[f"n_E1_{ev}"] >= N.RULES["support"]
                v = score(R, elig & sup, ev, "E1", "brier", "B0", 9)
                v["coverage"] = round(float(sup[elig].mean()), 4)
                explo[f"{view}:{ev}"] = v
    years = [int(y) for y in R["year"]] if len(R["year"]) else []
    out = dict(now_version=N.VERSION, rules_id=N.RULES_ID, rules=N.RULES, spec_sha1=spec_hash,
               generated=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
               tested_through=str(max(years)) if years else None, tested_from=str(min(years)) if years else None,
               universes=U, records=int(len(R["u"])), decisions=dec, report=report, exploration=explo)
    N.VALIDATION.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    write_report(out)
    print(f"done in {time.time() - t0:.0f} s: {out['records']} records", flush=True)


def _f(x, nd=3):
    return "—" if x is None else f"{x:.{nd}f}".replace(".", ",")


def write_report(out):
    """meaning/lens/2026-10-06-now-1.0/proverka.md: the aggregates of the run (no dates, no prices)."""
    L = [f"# Проверка слоя «Сейчас» на истории · {out['now_version']}", "",
         f"Правила `{out['rules_id']}`, спецификация sha1 `{out['spec_sha1']}`, прогон {out['generated']}. Цели — исторические сессии "
         f"{out['tested_from']}–{out['tested_through']}, у каждой семья только из более ранних дат и не меньше {N.RULES['warmup']} сессий. "
         f"Записей (цель × закрытая M5): {out['records']}. Единица пересэмплирования — календарная неделя.", "",
         "Skill — `1 − оценка модели / оценка B0` (больше нуля — лучше базы по времени). Интервал — 95 % разницы оценок по неделям.", "",
         "| Семья · событие | Решение | Matcher | Brier skill | интервал | покрытие ≥20 | Величина (CRPS) skill | Время skill |", "|---|---|---|---:|---|---:|---:|---:|"]
    for k, P in out["report"].items():
        view, ev = k.split(":")
        t = P["table"]
        if not t:
            L.append(f"| {'исходная' if view == 'conf' else 'слома'} · {ev} | {P['status']} | — | — | нет целей: семьи этого вида не набирают {N.RULES['warmup']} сессий | — | — | — |")
            continue
        best = P["matcher"] or "—"
        sk = t[P["matcher"]]["vs_B0"] if P["matcher"] else None
        L.append(f"| {'исходная' if view == 'conf' else 'слома'} · {ev} | {P['status']} | {best} | {_f(sk and sk['skill'], 4)} | "
                 f"{'—' if not sk else '[' + _f(sk['lo'], 5) + '; ' + _f(sk['hi'], 5) + ']'} | {_f(t[P['matcher']]['coverage'] if P['matcher'] else None, 2)} | "
                 f"{_f(P.get('magnitude_skill'), 4)} | {_f(P.get('time_skill'), 4)} |")
    L += ["", "## Каждый matcher против B0 (тот же срез записей)", "",
          "| Семья · событие | Matcher | записей | недель | покрытие | Brier skill | интервал разницы | против победителя |", "|---|---|---:|---:|---:|---:|---|---|"]
    for k, P in out["report"].items():
        view, ev = k.split(":")
        for m, r in P["table"].items():
            v = r["vs_B0"]
            w = r["vs_winner"]
            L.append(f"| {'исходная' if view == 'conf' else 'слома'} · {ev} | {m} | {v['n']} | {v['weeks']} | {_f(r['coverage'], 2)} | {_f(v['skill'], 4)} | "
                     f"{'—' if v['lo'] is None else '[' + _f(v['lo'], 5) + '; ' + _f(v['hi'], 5) + ']'} | "
                     f"{'—' if not w else _f(w['skill'], 4) + ' [' + _f(w['lo'], 5) + '; ' + _f(w['hi'], 5) + ']'} |")
    L += ["", "## По инструменту и сессии (промотированный matcher, иначе M1, против B0)", "",
          "| Семья · событие | Связка | записей | частота нового экстремума | Brier B0 | покрытие | skill | интервал |", "|---|---|---:|---:|---:|---:|---:|---|"]
    for k, P in out["report"].items():
        view, ev = k.split(":")
        for cell, c in P["cells"].items():
            v = c["vs_B0"]
            L.append(f"| {'исходная' if view == 'conf' else 'слома'} · {ev} | {cell} ({c['matcher']}) | {c['records']} | {_f(c['base_rate'], 3)} | {_f(c['brier_B0'], 4)} | "
                     f"{_f(c['coverage'], 2)} | {_f(v['skill'], 4)} | {'—' if v['lo'] is None else '[' + _f(v['lo'], 5) + '; ' + _f(v['hi'], 5) + ']'} |")
    if "exploration" in out:
        L += ["", "## Разведка вне спецификации (не кандидат в продукт)", "",
              "E1 — расстояние последнего закрытия от уже сделанного экстремума (c − r для R, x − c для X) в пределах 0,10. Добавлен "
              "после результата NOW-1.0, поэтому это гипотеза для версии 1.1, а не проверенный matcher (спецификация §8).", "",
              "| Семья · событие | записей | недель | покрытие ≥20 | Brier skill | интервал разницы |", "|---|---:|---:|---:|---:|---|"]
        for k, v in out["exploration"].items():
            view, ev = k.split(":")
            L.append(f"| {'исходная' if view == 'conf' else 'слома'} · {ev} | {v['n']} | {v['weeks']} | {_f(v.get('coverage'), 2)} | {_f(v['skill'], 4)} | "
                     f"{'—' if v['lo'] is None else '[' + _f(v['lo'], 5) + '; ' + _f(v['hi'], 5) + ']'} |")
    L += ["", "Числа — описание истории на walk-forward, не торговое преимущество (спецификация §22, §26.9).", ""]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
