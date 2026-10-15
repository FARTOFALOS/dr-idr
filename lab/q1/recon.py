"""Q1 pilot — reconciliation with the original A/D procedure (studies/kadr_2026_10_12/kadr_checks.py).

    python -B lab/q1/recon.py              adapter + engine, row by row (~3-6 min)
    python -B lab/q1/recon.py --golden     also re-run the ORIGINAL study_a / study_de unchanged (~5 min more)

Writes only to lab/.q1-pilot/recon/ (git-ignored): case-level mismatches stay local, the summary holds counts only.

1. The published reference studies/kadr_2026_10_12/kadr_checks.json is read, never written; its SHA-256 is recorded
   before and after the run.
2. --golden: the original module's functions run unchanged on this corpus; their A, D and E sections are compared with
   the published ones value by value.
3. Adapter: the row loop of A (NODEPOS_wd) and D (GEO, NODEPOS_all) — the original's own lines and helpers — keeping
   per row the target, the cut, the place and each estimator's member set and intermediate statuses. Its aggregates
   must equal the published D and A numbers exactly; that is what makes it the original procedure.
4. The pilot engine answers every one of those rows through the same calls the review page makes (the target state from
   the target's prefix, the estimator's parent, the selection), and is compared case by case: parent composition,
   eligible / not yet / near / member sets, n, yes, unknown, known.
5. Domain accounting: the pilot's 5-minute schedule and the targets outside A/D's evaluated domain, counted apart.
6. A seeded sample of rows is re-derived over the WHOLE parent by the scalar second implementation (raw rows).
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parent
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(ROOT / "studies" / "kadr_2026_10_12"))
from q1 import engine as E  # noqa: E402

E.bind_corpus()
import kadr_checks as K  # noqa: E402  the original module, imported, never run as a script (its main() writes)
import now24 as N  # noqa: E402
import now24_validate as V  # noqa: E402

GOLDEN = ROOT / "studies" / "kadr_2026_10_12" / "kadr_checks.json"
OUT = LAB / ".q1-pilot" / "recon"
LEVEL_NAMES = ("0", "-1/2", "-7/10")
EST_MAP = (("GEO", "GEO"), ("NODEPOS_all", "NODEPOS_ALL"), ("NODEPOS_wd", "NODEPOS_WD"))
SCALAR_ROWS, SEED = 120, 20261012


def file_sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jnorm(x):
    return json.loads(json.dumps(x, ensure_ascii=False))


def diff(a, b, path=""):
    """Every place where two JSON values differ (exact)."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            out += diff(a.get(k, "<missing>"), b.get(k, "<missing>"), f"{path}.{k}")
        return out
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        out = []
        for k, (x, y) in enumerate(zip(a, b)):
            out += diff(x, y, f"{path}[{k}]")
        return out
    return [] if a == b else [f"{path}: published {b!r} vs rerun {a!r}"]


def golden_rerun(gold):
    t0 = time.time()
    RA, UA = K.study_a()
    A = jnorm(K.analyse_a(RA, UA))
    DE = jnorm(K.study_de())
    res = dict(seconds=round(time.time() - t0),
               A=diff(A, gold["A"], "A"), D=diff(DE["D"], gold["D"], "D"), E=diff(DE["E"], gold["E"], "E"))
    res["identical"] = not (res["A"] or res["D"] or res["E"])
    return res


def run(golden=False):
    OUT.mkdir(parents=True, exist_ok=True)
    gsha0 = file_sha(GOLDEN)
    gold = json.loads(GOLDEN.read_text(encoding="utf-8"))
    t0 = time.time()
    summary = dict(reference=dict(file=str(GOLDEN.relative_to(ROOT)), sha256_before=gsha0), engine=dict(model=E.MODEL, engine=E.ENGINE),
                   corpus=str(E.CORPUS["path"]), universes=[])
    if golden:
        print("golden re-run of the original functions ...", flush=True)
        summary["golden_rerun"] = golden_rerun(gold)
        print("  identical" if summary["golden_rerun"]["identical"] else f"  DIFFERS: {summary['golden_rerun']}", flush=True)

    rows = {k: [] for k in ("week", "y")}
    for nm, _ in EST_MAP:
        rows["n_" + nm], rows[f"p_{nm}_y"] = [], []
    cmp = {nm: dict(rows=0, parent_mismatch=0, eligible_mismatch=0, notyet_mismatch=0, near_mismatch=0, member_mismatch=0,
                    count_mismatch=0, member_cells=0) for nm, _ in EST_MAP}
    state_mismatch, mismatches, row_index = 0, [], []
    domain = dict(targets_all=0, targets_ad=0, rows_5min=0, rows_15min=0, rows_ad=0, rows_15min_target_unknown=0,
                  rows_15min_small_family=0, rows_5min_only=0)

    for inst in K.INSTS:
        for session in K.SESSIONS:
            tu = time.time()
            U, grid = V.universe(inst, session, "conf")
            T = E.table(inst, session)
            if T.ids != [u["id"] for u in U]:
                raise AssertionError("the engine table is not the A/D universe")
            Lg = len(grid)
            ser = [N.series(u["P"], u["a"], u["oppv"]) for u in U]
            fl = [K.future_low(u["P"]) for u in U]
            order = sorted(range(len(U)), key=lambda j: U[j]["date"])
            order_np = np.array(order)
            dates_o = np.array([U[j]["date"] for j in order])
            S_o = N.stack([ser[j] for j in order])
            w_o = np.array([U[j]["w"] for j in order], dtype=np.int64)
            FMIN_o = np.stack([fl[j][0] for j in order])
            FNAN_o = np.stack([fl[j][1] for j in order])
            groups = {}
            for j in range(len(U)):
                groups.setdefault((U[j]["side"], U[j]["win"]), []).append(j)
            n_targets = 0
            for gk, idxs in groups.items():
                idxs.sort(key=lambda j: U[j]["date"])
                idxs_np = np.array(idxs)
                dates_g = np.array([U[j]["date"] for j in idxs])
                wdays = np.array([U[j]["weekday"] for j in idxs])
                Sg = N.stack([ser[j] for j in idxs])
                wg = np.array([U[j]["w"] for j in idxs], dtype=np.int64)
                FMIN = np.stack([fl[j][0] for j in idxs])
                FNAN = np.stack([fl[j][1] for j in idxs])
                for t, i in enumerate(idxs):
                    nb = int(np.searchsorted(dates_g, dates_g[t], side="left"))
                    fam_all = np.arange(nb)
                    fam_wd = fam_all[wdays[:nb] == U[i]["weekday"]]
                    Tt, w_t, a_t = ser[i], U[i]["w"], U[i]["a"]
                    fmin_t, fnan_t = fl[i]
                    # ---- domain accounting (counts only; the causal prefix arrays of the target)
                    domain["targets_all"] += 1
                    all_cuts = np.array([c for c in range(a_t + 1, Lg - 1) if Tt["valid"][c]], dtype=int)
                    for _, a, b in K.LEVELS:
                        if not len(all_cuts):
                            break
                        op = (Tt["cl"][all_cuts] * b > a * w_t) & (Tt["r"][all_cuts] * b > a * w_t)
                        on15 = (all_cuts + 1) % K.STEP == 0
                        yk = np.where(fmin_t[all_cuts] * b <= a * w_t, 1, np.where(fnan_t[all_cuts], -1, 0)) >= 0
                        big = len(fam_wd) >= K.MIN_FAM
                        domain["rows_5min"] += int(op.sum())
                        domain["rows_15min"] += int((op & on15).sum())
                        domain["rows_5min_only"] += int((op & ~on15).sum())
                        domain["rows_ad"] += int((op & on15 & yk).sum()) if big else 0
                        domain["rows_15min_target_unknown"] += int((op & on15 & ~yk).sum()) if big else 0
                        domain["rows_15min_small_family"] += 0 if big else int((op & on15).sum())
                    if len(fam_wd) < K.MIN_FAM:
                        continue
                    cuts = np.array([c for c in range(a_t + 1, Lg - 1) if Tt["valid"][c] and (c + 1) % K.STEP == 0], dtype=int)
                    if not len(cuts):
                        continue
                    n_targets += 1
                    domain["targets_ad"] += 1
                    nbo = int(np.searchsorted(dates_o, dates_g[t], side="left"))
                    week = K.iso_week(U[i]["date"])
                    for li, (_, a, b) in enumerate(K.LEVELS):
                        ok = (Tt["cl"][cuts] * b > a * w_t) & (Tt["r"][cuts] * b > a * w_t)
                        y = np.where(fmin_t[cuts] * b <= a * w_t, 1, np.where(fnan_t[cuts], -1, 0))
                        ok &= y >= 0
                        if not ok.any():
                            continue
                        cs = cuts[ok]
                        rows["week"].append(np.full(len(cs), week, np.int32))
                        rows["y"].append(y[ok].astype(np.int8))
                        row_index.extend((U[i]["id"], int(c), li) for c in cs)
                        # ---- the engine: the target's state from its own prefix, cut by cut
                        lvl = E.LEVELS[LEVEL_NAMES[li]]
                        cl_e = []
                        for c in cs:
                            st = T.target_state(i, int(c), lvl)
                            if st["status"] != "OPEN" or st["close_v"] != int(Tt["cl"][c]) or st["r_v"] != int(Tt["r"][c]):
                                state_mismatch += 1
                            cl_e.append(st.get("close_v", 0))
                        for nm, est in EST_MAP:
                            # ---- the adapter: the original lines
                            if nm == "GEO":
                                S, w, FM, FN, idx, glob = S_o, w_o, FMIN_o, FNAN_o, np.arange(nbo), order_np[:nbo]
                            else:
                                fam = fam_all if nm == "NODEPOS_all" else fam_wd
                                S, w, FM, FN, idx, glob = Sg, wg, FMIN, FNAN, fam, idxs_np[fam]
                            W = w[idx][:, None]
                            reach = FM[idx][:, cs] * b <= a * W
                            unk = (~reach) & FN[idx][:, cs]
                            Vm = S["valid"][idx][:, cs]
                            node = Vm & (S["r"][idx][:, cs] * b > a * W)
                            pos = Vm & N._near(S["cl"][idx][:, cs], W, Tt["cl"][cs][None, :], w_t, (1, 4))
                            M = node & pos
                            n = M.sum(0)
                            yes = (M & reach).sum(0)
                            kn = n - (M & unk).sum(0)
                            with np.errstate(invalid="ignore", divide="ignore"):
                                p = np.where(kn > 0, yes / np.maximum(kn, 1), np.nan)
                            rows["n_" + nm].append(n.astype(np.int32))
                            rows[f"p_{nm}_y"].append(p.astype(np.float32))
                            # ---- the engine's parent and selection, compared case by case
                            par = T.parent(i, est)
                            c_ = cmp[nm]
                            c_["rows"] += len(cs)
                            if not np.array_equal(np.sort(par), np.sort(glob)):
                                c_["parent_mismatch"] += len(cs)
                                mismatches.append(dict(estimator=nm, target=U[i]["id"], level=LEVEL_NAMES[li], kind="parent",
                                                       engine_only=sorted(set(T.ids[q] for q in par) - set(U[q]["id"] for q in glob))[:10],
                                                       adapter_only=sorted(set(U[q]["id"] for q in glob) - set(T.ids[q] for q in par))[:10]))
                                continue
                            o1, o2 = np.argsort(par), np.argsort(glob)
                            m = T.select(par[o1], cs, lvl, cl_e, w_t)
                            Vm2, node2, pos2, M2 = Vm[o2], node[o2], pos[o2], M[o2]
                            eq = dict(eligible=np.array_equal(m["valid"], Vm2), notyet=np.array_equal(m["notyet"], node2),
                                      near=np.array_equal(m["valid"] & m["near"], pos2), member=np.array_equal(m["match"], M2))
                            for k2, v2 in eq.items():
                                if not v2:
                                    c_[f"{k2}_mismatch"] += 1
                            c_["member_cells"] += int(M2.size)
                            ne = m["match"].sum(0)
                            ye = (m["match"] & m["reach"]).sum(0)
                            ke = ne - (m["match"] & m["unk"]).sum(0)
                            bad = (ne != n) | (ye != yes) | (ke != kn)
                            c_["count_mismatch"] += int(bad.sum())
                            if not all(eq.values()) or bad.any():
                                q = int(np.flatnonzero(bad)[0]) if bad.any() else 0
                                e_ids = set(T.ids[par[o1][r]] for r in np.flatnonzero(m["match"][:, q]))
                                a_ids = set(U[glob[o2][r]]["id"] for r in np.flatnonzero(M2[:, q]))
                                mismatches.append(dict(estimator=nm, target=U[i]["id"], cut=int(cs[q]), level=LEVEL_NAMES[li], kind="members/counts",
                                                       equal=eq, adapter=[int(n[q]), int(yes[q]), int(kn[q])], engine=[int(ne[q]), int(ye[q]), int(ke[q])],
                                                       engine_only=sorted(e_ids - a_ids)[:10], adapter_only=sorted(a_ids - e_ids)[:10]))
            summary["universes"].append(dict(inst=inst, session=session, sessions=len(U), ad_targets=n_targets, seconds=round(time.time() - tu)))
            print(f"{inst} {session}: {len(U)} sessions, {n_targets} A/D targets, {time.time() - tu:.0f}s", flush=True)

    R = {k: np.concatenate(v) for k, v in rows.items()}
    # ---- the adapter IS the original procedure when its aggregates equal the published ones
    D_ad = dict(rows=int(len(R["y"])),
                coverage={k: round(float((R["n_" + k] >= K.SUP).mean()), 4) for k in ("GEO", "NODEPOS_all")},
                median_n={k: float(np.median(R["n_" + k])) for k in ("GEO", "NODEPOS_all")},
                GEO_vs_NODEPOS_all=K.pair_scores(R, "y", "NODEPOS_all", "GEO", 41))
    A_cov = {k: dict(share_n_ge_20=round(float((R["n_" + k] >= K.SUP).mean()), 4), median_n=float(np.median(R["n_" + k])))
             for k in ("NODEPOS_wd", "NODEPOS_all")}
    adapter = dict(D=diff(jnorm(D_ad), {k: gold["D"][k] for k in D_ad}, "D"),
                   A_rows=diff(int(len(R["y"])), gold["A"]["rows"], "A.rows"),
                   A_coverage=diff(jnorm(A_cov), {k: gold["A"]["coverage"][k] for k in A_cov}, "A.coverage"))
    adapter["identical"] = not (adapter["D"] or adapter["A_rows"] or adapter["A_coverage"])
    summary["adapter_vs_published"] = adapter
    summary["engine_vs_adapter"] = dict(rows=int(len(R["y"])), target_state_mismatch=state_mismatch, by_estimator=cmp,
                                        mismatch_records=len(mismatches))
    summary["domain"] = domain

    # ---- the scalar second implementation over the whole parent, on a seeded sample of rows
    rng = np.random.default_rng(SEED)
    pick = sorted(rng.choice(len(row_index), size=min(SCALAR_ROWS, len(row_index)), replace=False).tolist())
    sc = dict(rows=len(pick), parent_members_checked=0, disagreements=0, examples=[])
    for q in pick:
        sid, c, li = row_index[q]
        inst, _, session = sid.split("-")
        T = E.table(inst, session)
        i = T.pos[sid]
        for _, est in EST_MAP:
            att = T.attempt(i, c, LEVEL_NAMES[li], est)
            lab = np.where(att["mask"]["reach"], "YES", np.where(att["mask"]["unk"], "UNKNOWN", "NO"))
            for r_, j in enumerate(att["par"]):
                rs, lb = T.scalar_classify(int(j), c, E.LEVELS[LEVEL_NAMES[li]], att["state"]["close_v"], att["state"]["w"])
                want = (str(att["reason"][r_]), str(lab[r_]) if att["reason"][r_] == "MATCH" else None)
                sc["parent_members_checked"] += 1
                if (rs, lb) != want:
                    sc["disagreements"] += 1
                    if len(sc["examples"]) < 10:
                        sc["examples"].append(dict(row=[sid, c, LEVEL_NAMES[li]], estimator=est, case=T.ids[j], vector=list(want), scalar=[rs, lb]))
    summary["scalar_sample"] = {k: v for k, v in sc.items() if k != "examples"}
    summary["reference"]["sha256_after"] = file_sha(GOLDEN)
    summary["reference"]["unchanged"] = summary["reference"]["sha256_after"] == gsha0
    summary["seconds"] = round(time.time() - t0)
    (OUT / "recon_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "recon_mismatches.json").write_text(json.dumps(dict(mismatches=mismatches, scalar_examples=sc["examples"]),
                                                          ensure_ascii=False, indent=1), encoding="utf-8")
    return summary


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    s = run(golden="--golden" in sys.argv)
    print(json.dumps({k: v for k, v in s.items() if k != "universes"}, ensure_ascii=False, indent=1))
