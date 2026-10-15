"""Real M5 witness + UNKNOWN incidence; protocol is the sibling README.md."""
from __future__ import annotations

import collections
import copy
import gzip
import hashlib
import json
import importlib.util
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RT = ROOT / "lab/.runtime/scene-continuity-2026-10-15"
sys.path.insert(0, str(ROOT / "lab"))
import continuity24 as E
import continuity_audit as A
import integration24 as I
import integration_audit as IA
import now24_validate as V
import scene24 as S


def stamp():
    paths = [HERE / "README.md", HERE / "run.py", ROOT / "lab/continuity24.py",
             ROOT / "lab/continuity_audit.py", ROOT / "tests/continuity24.py",
             ROOT / "studies/dynamic_field_2026_10_15/checks.py",
             ROOT / "lab/scene24.py", ROOT / "lab/now24_validate.py",
             ROOT / "integration/reference/trace/schema/dr_lab_trace.yaml",
             ROOT / "integration/reference/trace/fom.py"]
    return [dict(artifact=str(p.relative_to(ROOT)).replace("\\", "/"),
                 version=hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()) for p in paths]


def original_research_recount(cases, grid, first_packet, date):
    spec = importlib.util.spec_from_file_location("_continuity_original_study", ROOT / "studies/dynamic_field_2026_10_15/checks.py")
    R = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(R)
    d = R.pack(cases, grid)
    i = next(i for i, c in enumerate(d["cases"]) if c["date"] == date)
    j = list(grid).index(first_packet["context"]["cut"])
    k = int(10 * d["cl"][i, j]) // int(d["w"][i])
    labels, specs = R.labels(d, j, k)
    col = np.flatnonzero((specs == [1, 0, 4]).all(1)).item()
    ids = R.selections(d, i, j)[R.METHODS.index("POS_GEO")]
    reference = {d["cases"][int(v)]["id"]: ("YES" if labels[v, col] == 1 else "NO" if labels[v, col] == 0 else "UNKNOWN") for v in ids}
    if reference != first_packet["labels"]:
        raise AssertionError("candidate differs from original research at the shared declared point")
    return dict(status="PASS", n=len(ids), support=E.support(reference))


def unknown_incidence():
    totals = collections.Counter()
    widths, cells = [], []
    for inst in ("NQ", "ES", "YM"):
        for block in ("ODR", "RDR"):
            with np.load(ROOT / f"lab/.runtime/dynamic-field-2026-10-15/{inst}_{block}.npz", allow_pickle=False) as a:
                meta = json.loads(str(a["meta"]))
                mi = meta["methods"].index("POS_GEO")
                n, k = a["n"][mi], a["known"][mi]
                take = (a["kind"] == 0) & (n >= 20) & (k >= 20)
                n, k = n[take].astype(np.int64), k[take].astype(np.int64)
                w = (n - k) / n
                row = dict(instrument=inst, block=block, rows=len(n), rows_with_unknown=int((w > 0).sum()),
                           member_labels=int(n.sum()), unknown_member_labels=int((n - k).sum()),
                           maximum_bound_width=float(w.max()))
                cells.append(row)
                widths.append(w)
                totals.update({x: row[x] for x in ("rows", "rows_with_unknown", "member_labels", "unknown_member_labels")})
    width = np.concatenate(widths)
    return dict(**totals, rows_with_unknown_fraction=totals["rows_with_unknown"] / totals["rows"],
                unknown_member_fraction=totals["unknown_member_labels"] / totals["member_labels"],
                bound_width_quantiles={str(q): float(np.quantile(width, q)) for q in (.5, .9, .95, .99, 1.)},
                rows_at_least_width={str(q): int((width >= q).sum()) for q in (.05, .1, .2)}, cells=cells,
                scope="existing POS_GEO WINDOW_VISIT support-qualified rows; dependent questions, not independent days")


def empirical_grid(packet, today, grid):
    t = packet["target"]
    cut = packet["context"]["cut"]
    j = list(grid).index(cut)
    current = E.Q(int(today["P"][j, 2]), today["w"])
    base_k = (10 * current) // 1
    lo, hi = E.Q(*t["low"]), E.Q(*t["high"])
    center_k = (lo + hi) * 5
    geometry = hi - lo == E.Q(1, 5) and center_k - base_k in (-10, -5, -2, 2, 5, 10)
    time = (t["first_close"] - cut, t["last_close"] - cut) in ((5, 15), (20, 30), (50, 60))
    return bool(geometry and time and not packet["question"]["conditions"])


def main():
    RT.mkdir(parents=True, exist_ok=True)
    inst, block, date, scope = "NQ", "RDR", "2025-12-17", "all"
    initial = I.scene(inst, block, 640, date, "conf", scope)
    family = initial["family"]
    t = family["today"]
    frame = E.Frame(inst, date, block, t["side"], str(t["idrL"] if t["side"] == -1 else t["idrH"]),
                    str(t["idrH"] - t["idrL"]), t["c0"], family["schedule"]["end"])
    target = E.pin(frame, "1.7", "1.9", 690, 700, 670)
    cases, grid = V.universe(inst, block, "conf")
    for c in cases:
        c.update(instrument=inst, block=block)
    today = copy.deepcopy(next(c for c in cases if c["date"] == date))
    today.update(tick=str(initial["day"]["tick"]), edge=frame.edge)
    versions = stamp()
    packets, checks, transitions, summary = [], [], [], []
    initial_revision = E.digest(E.original_record(family))
    for cut in range(670, 701, 5):
        current_family, _, _ = S._family(inst, block, cut, date, "conf:all")
        p = E.release(cases, today, grid, target, cut, current_family)
        result = A.check_frame(p, cases, today, grid)
        if result["outcome"] != "PASS":
            raise AssertionError(result)
        checks.append(result)
        if packets:
            tr = A.transition(packets[-1], p)
            if tr["outcome"] != "PASS":
                raise AssertionError(tr)
            transitions.append(tr)
        packets.append(p)
        fi = set(family["ids"])
        summary.append(dict(cut=S.clk(cut), status=p["status"], observed=p["observed"],
                            target_id=target.id, question_id=p["question"]["id"], context_id=p["context"]["id"],
                            G=len(p["selection"]["G"]), M_position=len(p["selection"]["M"]),
                            M_in_F=len(set(p["selection"]["M"]) & fi),
                            M_outside_F=len(set(p["selection"]["M"]) - fi),
                            risk_n=len(p["risk_set"]["ids"]), support=p["support"] if p["estimate"] is not None else None,
                            conditions=p["question"]["conditions"],
                            on_original_empirical_grid=empirical_grid(p, today, grid),
                            original_unchanged=p["context"]["original_revision"] == initial_revision))
        print(S.clk(cut), p["status"], "M", len(p["selection"]["M"]), "risk", len(p["risk_set"]["ids"]),
              "support", p["estimate"], flush=True)
    return_question = None
    for cut in range(700, frame.end - 15 + 1, 5):
        try:
            return_question = E.revisit(target, cut, cut + 5, cut + 15, today, grid)
        except ValueError:
            continue
        break  # first departure established by this prefix, not by its future return
    if return_question is None:
        raise AssertionError("fixture has no established departure")
    rec = return_question["target"]
    child = E.pin(frame, E.Q(*target.low), E.Q(*target.high), rec["first_close"], rec["last_close"],
                  rec["created_at"], target.id, "REVISIT_AFTER_OBSERVED_EXIT")
    return_outcome = E.observed(today, grid, child, child.last_close)
    # Return to the accepted BASE after the new return question has run its window.
    restored = I.scene(inst, block, child.last_close, date, "conf", scope)
    restored_same = E.original_record(restored["family"]) == E.original_record(family)
    if not restored_same or not all(r["original_unchanged"] for r in summary):
        raise AssertionError("original BASE changed")
    audits = [IA.audit(p, dict(instrument=inst, session=block, date=date, view="conf", scope=scope))
              for p in (initial, restored)]
    if any(a["status"] != "PASS_SCOPED" for a in audits):
        raise AssertionError(audits)
    evidence = [A.evidence(c, versions, "studies/scene_continuity_2026_10_15/run.py") for c in checks + transitions]
    private = dict(initial_base_revision=initial_revision, packets=packets, checks=checks,
                   transitions=transitions, trace_evidence=evidence, return_question=return_question,
                   return_observation=return_outcome, accepted_audits=audits)
    with gzip.open(RT / "witness.json.gz", "wt", encoding="utf-8") as f:
        json.dump(private, f, ensure_ascii=False)
    result = dict(version=E.VERSION, status="PASS", source_hashes=versions, fixture=dict(
        instrument=inst, block=block, date=date, scope=scope, activation=S.clk(frame.activation),
        pin_cut="11:10", sd_band=[1.7, 1.9], window_bar_closes=["11:30", "11:35", "11:40"], F_N=family["N"]),
        releases=summary, transitions=[c["details"] for c in transitions],
        frame_recounts=len(checks), transition_checks=len(transitions),
        original_research_recount=original_research_recount(cases, grid, packets[0], date),
        original_restored_identically=restored_same, restore_cut=S.clk(child.last_close),
        accepted_trace_audits=[a["status"] for a in audits],
        return_question=dict(new_target=return_question["target"]["id"], parent=target.id,
                             established_departure=return_question["departure_fact"],
                             new_question=return_question["question"]["id"], later_observation=return_outcome,
                             estimator_status=return_question["estimator_status"]),
        unknown_incidence=unknown_incidence(),
        limits=["illustrative known scene, not forecast validation", "fixed-window/residual extensions not calibrated",
                "new UI not implemented or perceptually accepted", "full frozen FOM/Trace catalog not rebound",
                "no automatic C2/C3, no return percentage", "2026 closed; individual records local only"])
    (HERE / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS original BASE restored; existing Trace audits", result["accepted_trace_audits"], flush=True)
    print("UNKNOWN", json.dumps(result["unknown_incidence"], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
