"""DR Lab semantic trace (DR-LAB-SEMANTIC-ARCHITECTURE 0.1 with its addendum 0.2) — the acceptance of the executable
contour on the real system.

What is checked:
- the products: trace/build equals what its sources give (trace/tools/build.py --check in the LinkML environment) and
  is not stale; a changed source makes the catalog stale, and then no traced claim is reliable (fail closed);
- the model: every static link check of lab/semtrace.py passes (references and their types, code, checks, estimand
  chains, claim profiles, profile standing, the edition's amendment additive, coverage of 0.1, the SWPC §9 bindings),
  and the registry's status conflation is found and registered (BND-02);
- the declared scenes (BASE-24 zone share, NOW-1.0 «R позже углублялся», ARRIVE-24 / Q1 «отсюда до −0,5», the same
  place with «мало сессий»): forward trace with every mandatory link VERIFIED in this run, the three operations recorded
  apart, the assessments on their own axes (decision from the standing, human acceptance PENDING), the replaced futures
  of the target and of the analogues changing nothing selected, the reports valid against TraceReport (stdlib and
  LinkML in a temporary folder);
- backward: lineage from the claim's binding reaches its definitions, sources and code; impact of its question, outcome
  and case-set rule reaches the claim and its presentation (IMPACT); a code change reaches the stored Q1 issues;
- the accepted line: BASE-24 and NOW-1.0 recomputed by the code of the accepted commit give the same bundles;
- the Q1 stores: identities, outcome links, revisions, the store's own verify(), bytes unchanged; the stored issue of
  the ARRIVE scene answers the same and reproduces IDENTICAL;
- the counterexamples: changed label, broken reference, mismatched denominator, forbidden future (target, analogues),
  wrong claim profile, missing evidence — each detected at its place, the claim not reliable;
- the screen: the saved states of studies/trace_2026_10_13/screens re-checked against the bundles computed now (stale if
  the page or the registry changed: re-collect); `--screens` collects them anew (headless Chrome, a server of this
  checkout on a free port, never 8767).

Run: python -B tests/trace_arch.py [--screens]     (ALL GOOD at the end; a few minutes; the session base is needed)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lab"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import contract as C   # noqa: E402
import semtrace as T   # noqa: E402

VENV = ROOT / ".venv-linkml" / "Scripts" / "python.exe"
EVIDENCE = ROOT / "studies" / "trace_2026_10_13"
failures = []


def check(cond, msg):
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        failures.append(msg)


def future_ohlc_unit():
    """No G3 data required: a future perturbation must change every OHLC, never the M5 prefix."""
    import numpy as np

    original = np.asarray([[665, 101, 105, 99, 103],
                           [670, 103, 107, 102, 106],
                           [675, 106, 108, 104, 107],
                           [680, 107, 109, 103, 105]], dtype=np.int32)
    mutated = original.copy()
    n = T.mutate_future_ohlc(mutated, 0, len(mutated), shift=0, after=670, width_ticks=5)
    check(n == 2, "future OHLC unit: exactly the two M5 after the close-minute cut are mutated")
    check(np.array_equal(mutated[:2], original[:2]), "future OHLC unit: the entire allowed prefix is unchanged")
    check(np.array_equal(mutated[:, 0], original[:, 0]), "future OHLC unit: the observation clock remains unchanged")
    check(bool(np.all(mutated[2:, 1:5] != original[2:, 1:5])),
          "future OHLC unit: every future open, high, low and close changes (no wicks-only blind spot)")
    check(bool(np.all(mutated[2:, 3] <= mutated[2:, 1]) and
               np.all(mutated[2:, 1] <= mutated[2:, 2]) and
               np.all(mutated[2:, 3] <= mutated[2:, 4]) and
               np.all(mutated[2:, 4] <= mutated[2:, 2])),
          "future OHLC unit: every mutated M5 is a valid OHLC candle")
    check(bool(np.any(mutated[2:, 4] != original[2:, 4])),
          "future OHLC unit: a selector reading future CLOSE sees a changed input")


def products():
    print("the products")
    if VENV.exists():
        r = subprocess.run([str(VENV), "-B", str(ROOT / "trace" / "tools" / "build.py"), "--check"], capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONUTF8="1"), timeout=900)
        check(r.returncode == 0 and "IN SYNC" in r.stdout, "trace/build equals what its sources give (trace/tools/build.py --check)" + ("" if r.returncode == 0 else ": " + (r.stdout + r.stderr)[-600:]))
    else:
        print("  ..  .venv-linkml absent: the LinkML rebuild check not run")
    st = T.load()
    check(not T.stale_reasons(st), "the compiled catalog represents its sources (no stale reason)")
    cat = json.loads(T.CATALOG_FILE.read_text(encoding="utf-8"))
    first = next(iter(cat["stamps"]["sources"]))
    cat["stamps"]["sources"][first] = "0" * 64
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp) / "catalog.json"
        t.write_text(json.dumps(cat, ensure_ascii=False), encoding="utf-8")
        st2 = T.load(t)
        reasons = T.stale_reasons(st2)
        check(bool(reasons), f"a source changed since the build makes the catalog stale ({reasons[:1]})")
        sc = T.scenes(st2)["SCENE:NOW-NEW"]
        res, g, _ = T.static_checks(st2)
        rep, _ = T.trace_scene(st2, g, sc, mutations=False, static={c["check"]: c for c in res})
        check(not rep["assessment"]["reliable"] and any(v["code"] == "TRACE_STALE" for v in rep["violations"]), "a stale catalog declares no claim reliable (fail closed)")
    return st


def model(st):
    print("the model: static link checks")
    res, g, code = T.static_checks(st)
    for c in res:
        check(c["outcome"] == "PASS", f"{c['check']}: {T.TRACE_CHECKS[c['check']]} ({c['checked']})" + ("" if c["outcome"] == "PASS" else ": " + "; ".join(f"{v['where']}: {v['message']}" for v in c["violations"][:4])))
    by = {c["check"]: c for c in res}
    conf = by["STANDING"]["details"]["conflicts"]
    check({x["profile"] for x in conf} == {"PROFILE:ARRIVE-24", "PROFILE:PRE-24"} and all(x["boundary"] == "BND-02" for x in conf),
          "the registry's ACTIVE status of the proposed profiles ARRIVE-24 and PRE-24 is found and registered as BND-02")
    ed = by["EDITION-ADDITIVE"]["details"]
    check(ed.get("accepted_sha256", "").startswith("bdba7276") and ed.get("accepted_lines_removed_or_rewritten") == 0,
          f"the accepted SC-1.1 text is kept line by line in the text this line pins ({ed.get('state')}; {ed.get('accepted_lines_extended')} lines extended, {ed.get('lines_added')} added)")
    check(by["CATALOG-COVERAGE"]["details"]["arch_ids"] == 130, "0.1 holds 130 entry ids (ENT 32, R 16, INV 12, PROC 20, T 19, A 20, GAP 11), every one in the catalog")
    return {c["check"]: c for c in res}, g, code


def scenes(st, static, g, reps, shots):
    print("the declared scenes: forward trace on the real base")
    reports = []
    for sid, sc in T.scenes(st).items():
        rep, ex = T.trace_scene(st, g, sc, screen=shots.get(sc["page_fragment"]), reps=reps, mutations=True, static=static)
        reports.append(rep)
        a = rep["assessment"]
        mand = [l for s in rep["stages"] for l in s["links"] if l["mandatory"]]
        check(a["reliable"] and all(l["status"] in ("VERIFIED", "NOT_APPLICABLE") for l in mand),
              f"{sid}: {rep['claim']} — every mandatory link verified in this run ({len(mand)} links)" + ("" if a["reliable"] else ": " + "; ".join(v["code"] + " " + v["where"] for v in rep["violations"][:4])))
        by = {c["check"]: c for c in ex["checks"]}
        check(by["FUTURE-TARGET"]["outcome"] == "PASS" and by["FUTURE-TARGET"]["details"]["replaced_m5"] > 0,
              f"{sid}: the target day's candles after the cut replaced in memory ({by['FUTURE-TARGET']['details']['replaced_m5']} M5) change nothing, before or after the gate")
        check(by["FUTURE-MEMBERS"]["outcome"] == "PASS" and by["FUTURE-MEMBERS"]["details"]["labels_changed"] and by["FUTURE-MEMBERS"]["details"].get("mutated_fields") == "OHLC",
              f"{sid}: the analogues' futures replaced ({by['FUTURE-MEMBERS']['details']['sessions']} sessions) change their labels but no membership")
        want = "ACCEPTED" if sc["profile_key"] in ("BASE-24", "NOW-1.0") else "PROPOSED_FOR_ACCEPTANCE"
        check(a["decision"] == want and a["presentation_human"] == "PENDING" and a["model_definiteness"] == "DEFINED" and a["implementation"] == "VERIFIED_IN_RUN",
              f"{sid}: decision {a['decision']}, model {a['model_definiteness']}, implementation {a['implementation']}, presentation (machine) {a['presentation_machine']}, (human) {a['presentation_human']} — separate axes")
        ops = {o["operation"]: o for o in rep["operations"]}
        check(set(ops) == {"COMPUTE", "PRESENT", "ISSUE"} and ops["COMPUTE"]["performed"] and all(o["not_implied_ru"] for o in ops.values()),
              f"{sid}: the three operations recorded apart (compute {ops['COMPUTE']['performed']}, present {ops['PRESENT']['performed']}, issue {ops['ISSUE']['performed']})")
        errs = T.validate(rep, "TraceReport", st["spec"])
        check(not errs, f"{sid}: the report is a valid TraceReport (stdlib){': ' + str(errs[:2]) if errs else ''}")
        if sc["profile_key"] == "ARRIVE-24":
            q = by.get("Q1-ISSUE-MATCH", {})
            check(q.get("outcome") == "PASS" and q["details"].get("reproduce") == "IDENTICAL",
                  f"{sid}: the stored issue {q.get('details', {}).get('issue_id', '?')[:16]} (same target, cut, set, model) answers the same and reproduces IDENTICAL; issuing stays a separate operation")
        if shots.get(sc["page_fragment"]):
            check(by.get("SCREEN", {}).get("outcome") == "PASS", f"{sid}: the rendered element is the published claim in its value form and registered words ({by.get('SCREEN', {}).get('details')})")
    if VENV.exists():
        with tempfile.TemporaryDirectory() as tmp:
            files = []
            for i, r in enumerate(reports):
                f = Path(tmp) / f"rep{i}.json"
                f.write_text(json.dumps(r, ensure_ascii=False), encoding="utf-8")
                files.append(str(f))
            code = ("import json,sys\nfrom linkml.validator import Validator\nfrom linkml.validator.plugins import JsonschemaValidationPlugin\n"
                    f"v=Validator({str(ROOT / 'trace' / 'schema' / 'dr_lab_trace.yaml')!r}, validation_plugins=[JsonschemaValidationPlugin(closed=True)])\n"
                    "n=0\nfor f in sys.argv[1:]:\n    r=v.validate(json.load(open(f,encoding='utf-8')),'TraceReport'); n+=len(r.results)\n    [print(f, x.message[:200]) for x in r.results[:3]]\nprint('ERRORS', n)\n")
            r = subprocess.run([str(VENV), "-c", code] + files, capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONUTF8="1"))
            check(r.returncode == 0 and "ERRORS 0" in r.stdout, f"LinkML validates the {len(files)} reports against TraceReport (closed world, temporary folder)" + ("" if "ERRORS 0" in r.stdout else ": " + (r.stdout + r.stderr)[-500:]))
    return reports


def backward(st, g, reports):
    print("backward: lineage and impact")
    for rep in reports:
        b = T.claim_binding(st, rep)
        lin = {m for gr in T.lineage(g, b)["groups"] for m in gr["members"]}
        est = C.get(rep["claim"].split()[0])
        need = {est["id"], est["question"], est["q5_outcome"], est["profile"]} | set(est["q4_case_set"])
        check(need <= lin and any(m.startswith("SRC:") for m in lin) and any(m.startswith("code:") for m in lin),
              f"{rep['scene']}: from {b} back to the estimand, its question, outcome, case sets, profile, sources and code ({len(lin)} nodes){': missing ' + str(sorted(need - lin)) if not need <= lin else ''}")
    imp = T.check_impact(g, reports)
    check(imp["outcome"] == "PASS", f"IMPACT: {T.TRACE_CHECKS['IMPACT']} ({imp['checked']})" + ("" if imp["outcome"] == "PASS" else ": " + str(imp["violations"][:2])))
    near = {m for gr in T.impact(g, "code:lab/now24.py::_near")["groups"] for m in gr["members"]}
    check({"q1:STORED-ISSUES", "EST:K-ARRIVE"} <= near, "a change of lab/now24.py::_near reaches the stored Q1 issues (their MODEL hashes it) and «Отсюда»")
    path = T.why(g, "CMP:K-POS-1", "PB:B18/EST:K-ARRIVE")
    check(bool(path), "why: the chain from a changed comparison to the screen binding is explained link by link (" + " ".join(f"{p} {r}" for p, r, _ in (path or [])) + ")")
    narrow = {m for gr in T.impact(g, "CMP:K-POS-1")["groups"] for m in gr["members"] if m.startswith("EST:")}
    check(narrow == {"EST:K-ARRIVE"}, f"impact is not everything: changing CMP:K-POS-1 reaches exactly one estimand ({sorted(narrow)})")


def accepted(st):
    print("the accepted line")
    sc = [s for s in T.scenes(st).values() if s["profile_key"] in ("BASE-24", "NOW-1.0")]
    r = T.check_accepted_identity(st, sc)
    d = r["details"]
    check(r["outcome"] == "PASS", f"BASE-24 and NOW-1.0 recomputed by the code of the accepted commit {d.get('accepted_commit', '?')[:10]} give the same bundles "
          + str([(x["scene"], x["bundles"], x["numbers_identical"], x["words_identical"]) for x in d.get("scenes", [])]) + ("" if r["outcome"] == "PASS" else ": " + str(r["violations"][:2])))
    check(not d.get("modules_differ"), f"the modules computing BASE-24 / NOW-1.0 are those of the accepted commit; lab/contract.py differs in {d.get('contract_functions_changed')} (+{d.get('contract_functions_added')} new functions)")


def stores(st):
    print("the Q1 stores (read only)")
    res, reps = T.check_q1_stores(st["spec"])
    d = res["details"]
    check(res["outcome"] == "PASS", f"Q1-STORE: {len(d['stores'])} stores, {res['checked']} records — identities, links, revisions and verify() agree" + ("" if res["outcome"] == "PASS" else ": " + str(res["violations"][:3])))
    check(d["bytes_unchanged"], f"the {d['files']} files of the stores are byte-identical before and after the run")
    return reps


def counterexamples(st, g, code, static, reps, shots):
    print("the counterexamples")
    cx = T.counterexamples(st, g, code, static, base_reports=dict(screens=shots), reps=reps)
    kinds = {x["kind"] for x in cx}
    check({"CX-4a", "CX-4b", "CX-4c"} <= {x["id"] for x in cx},
          "negative controls include target future, analogue future event, AND analogue future close")
    for x in cx:
        check(x["detected"] and (x["reliable_after"] in (None, False)), f"{x['id']} {x['kind']}: {x['tamper']} → {x['check']} {x['codes']} at {x['where'][:1]}")
    for k in ("изменённая метка исхода", "нарушенная ссылка", "несовпадающий знаменатель", "запрещённое будущее", "неправильный профиль утверждения", "отсутствие исходных свидетельств"):
        check(k in kinds, f"the kind «{k}» is exercised")


def saved_screens(st):
    out = {}
    for f in sorted((EVIDENCE / "screens").glob("*.json")) if (EVIDENCE / "screens").is_dir() else []:
        s = json.loads(f.read_text(encoding="utf-8"))
        page = T.sha256_lf(ROOT / "lab" / "dist" / "24" / "d24.js")
        fresh = s["page_build_sha256"] == page and s["registry_hash"] == C.registry_hash()
        check(fresh, f"the saved screen state {f.name} belongs to this page build and registry" + ("" if fresh else " — re-collect: python -B lab/semtrace.py run --out studies/trace_2026_10_13 --screens"))
        if fresh:
            out[s["fragment"]] = s
    return out


def main():
    collect = "--screens" in sys.argv[1:]
    future_ohlc_unit()
    st = products()
    static, g, code = model(st)
    reps = stores(st)
    if collect:
        with tempfile.TemporaryDirectory() as tmp:
            raw = T.collect_screens(sorted({s["page_fragment"] for s in T.scenes(st).values()}), tmp)
        shots = {f: T.ingest_screen(r, [s["id"] for s in T.scenes(st).values() if s["page_fragment"] == f]) for f, r in raw.items()}
        print(f"  ..  screen states collected anew: {sorted(shots)}")
    else:
        shots = saved_screens(st)
    reports = scenes(st, static, g, reps, shots)
    backward(st, g, reports)
    accepted(st)
    counterexamples(st, g, code, static, reps, shots)
    print()
    print("ALL GOOD" if not failures else f"{len(failures)} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
