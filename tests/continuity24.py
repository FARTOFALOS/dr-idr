"""Semantic counterexamples for the fixed-target executable candidate (no UI writes)."""
import copy
import json
from pathlib import Path
import sys
import subprocess

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lab"))
import continuity24 as E
import continuity_audit as A


def check(ok, name):
    if not ok:
        raise AssertionError(name)
    print("PASS " + name, flush=True)


def fixture():
    grid = list(range(605, 666, 5))
    frame = E.Frame("NQ", "2025-12-17", "RDR", 1, "100", "10", 605, 665)
    p = np.tile([-5., 5., 0.], (len(grid), 1))
    today = dict(id="today", date=frame.date, instrument="NQ", block="RDR", side=1,
                 tick="0.1", edge="100", a=0, w=100, oppv=-200, P=p.copy())
    cases = []
    for i in range(25):
        c = copy.deepcopy(today)
        c.update(id=str(i), date="2020-12-17")
        # A before B in the known prefix, regardless of future labels.
        c["P"][1] = [-40, -30, -35]
        c["P"][2] = [-5, 5, 0]
        c["P"][6] = [40, 60, 50]
        cases.append(c)
    today["P"][1] = [-40, -30, -35]
    today["P"][2] = [-5, 5, 0]
    today["P"][6] = [40, 60, 50]
    target = E.pin(frame, ".4", ".6", 625, 640, 610)
    original = dict(family_id="F", snapshot_id="FS", N=1, ids=["0"], members=[dict(id="0")])
    return cases, today, grid, target, original


def main():
    cases, today, grid, target, original = fixture()
    def run(cut, **changes):
        return E.release(changes.get("cases", cases), changes.get("today", today), grid, target, cut, original,
                         changes.get("sequence"))
    a, b = run(615), run(620)
    check(a["question"]["id"] == b["question"]["id"] and a["context"]["id"] != b["context"]["id"],
          "same future target/question, different dated releases")
    early_hit = copy.deepcopy(today)
    early_hit["P"][3] = [40, 60, 50]  # 10:20, before the first target-window close at 10:25
    early_answer = run(620, today=early_hit)
    check(early_answer["observed"]["status"] == "OPEN" and early_answer["observed"]["value"] == "NO",
          "a price visit before the pinned time window does not resolve its future-window event")
    c = run(625)
    check(c["target"] == a["target"] and c["question"]["id"] != b["question"]["id"] and
          c["question"]["conditions"][0]["kind"] == "WINDOW_NO_VISIT", "same target, explicit residual question")
    fact = run(635)
    check(fact["observed"]["status"] == "FACT_YES" and fact["observed"]["available_at"] == 635 and
          fact["estimate"] is None, "visit becomes fact exactly at known M5 close")
    check(all(A.check_frame(p, cases, today, grid)["outcome"] == "PASS" for p in (a, b, c, fact)),
          "independent membership and label recount")
    check(all(A.transition(x, y)["outcome"] == "PASS" for x, y in ((a, b), (b, c), (c, fact))),
          "FOM transition distinguishes target, question, support and fact")
    check(not fact["labels"] and A.transition(fact, run(640))["outcome"] == "PASS",
          "resolved target carries no leftover future labels on subsequent M5")
    broken = copy.deepcopy(c)
    broken["target"]["physical_edges"][0][0] += 1
    check(A.transition(b, broken)["outcome"] == "FAIL", "physical pin drift is detected")
    broken = copy.deepcopy(c)
    broken["question"]["id"] = b["question"]["id"]
    check(A.transition(b, broken)["outcome"] == "FAIL", "changed question cannot reuse old question identity")
    broken = copy.deepcopy(b)
    broken["selection"]["full_path_compared"] = True
    check(A.check_frame(broken, cases, today, grid)["outcome"] == "FAIL", "position cannot masquerade as path matching")
    broken = json.loads(json.dumps(b))
    broken["estimate"]["yes"] += 1
    check(A.check_frame(broken, cases, today, grid)["outcome"] == "FAIL", "issued percentage cannot detach from its support")
    broken = copy.deepcopy(b)
    broken["observed"]["status"] = "FACT_NO"
    check(A.check_frame(broken, cases, today, grid)["outcome"] == "FAIL", "no visit so far is not a completed NO fact")
    broken = copy.deepcopy(c)
    broken["question"]["first_close"] += 5
    check(A.check_frame(broken, cases, today, grid)["outcome"] == "FAIL", "a correct count cannot label a different remaining window")
    future = copy.deepcopy(today)
    future["P"][4:] = [400, 500, 450]
    new = run(620, today=future)
    check(new == b, "today's unobserved future changes neither selector, answer nor context")
    hist = copy.deepcopy(cases)
    hist[0]["P"][6:] = [-5, 5, 0]
    changed = run(620, cases=hist)
    check(changed["selection"] == b["selection"] and changed["labels"] != b["labels"] and
          changed["context"]["history_revision"] != b["context"]["history_revision"],
          "historical future changes labels/revision, never position membership")
    scaled = copy.deepcopy(cases)
    for member in scaled:
        member["P"] *= 2
        member["w"] *= 2
        member["oppv"] *= 2
    scale_answer = run(620, cases=scaled)
    check(scale_answer["selection"]["M"] == b["selection"]["M"] and scale_answer["labels"] == b["labels"],
          "historical own-width scaling preserves position matching and transferred target events")
    bad_frame = copy.deepcopy(today)
    bad_frame["edge"] = "101"
    try:
        run(620, today=bad_frame)
        check(False, "changed box silently moved the pin")
    except ValueError:
        check(True, "changed source frame requires an explicit new target")
    seen = copy.deepcopy(cases)
    seen[0]["P"][4] = [0, 60, 0]
    conditioned = run(625, cases=seen)
    check(conditioned["selection"]["M"] == c["selection"]["M"] and
          len(conditioned["risk_set"]["ids"]) == 24, "shared POS pool differs from explicit residual risk set")
    check(conditioned['risk_set']['exclusions'] == {'0': 'WINDOW_ALREADY_VISITED'} and
          A.check_frame(conditioned, seen, today, grid)['outcome'] == 'PASS',
          'elapsed visit is an independently checked exclusion cause')
    forged = copy.deepcopy(conditioned)
    forged['risk_set']['exclusions']['0'] = 'NOT_ACTIVE_AT_WINDOW_START'
    check(A.check_frame(forged, seen, today, grid)['outcome'] == 'FAIL',
          'a plausible but false exclusion cause fails even when membership and numbers are correct')
    hole = copy.deepcopy(today)
    hole["P"][4] = np.nan
    gap = run(625, today=hole)
    check(gap["status"] == "OBSERVATION_GAP" and gap["estimate"] is None,
          "unknown prefix is not no-visit-so-far")
    gap_hit = run(635, today=hole)
    check(gap_hit["observed"]["value"] == "YES" and not gap_hit["observed"]["first_time_known"],
          "known visit survives earlier gap without inventing first arrival time")
    labels = {str(i): "YES" if i < 16 else "NO" if i < 20 else "UNKNOWN" for i in range(100)}
    s = E.support(labels)
    check(s["point_known"] == .8 and s["bounds"] == [.16, .96] and s["primary"] == "BOUNDS" and
          not s["point_is_comparison_score"], "16/20 among 100 is primarily 16-96%, not a ranking score of 80%")
    holes = copy.deepcopy(cases)
    for h in holes:
        h["P"][4] = np.nan
    y1 = {h["id"]: E.visit(h, grid, target) for h in holes}
    t2 = E.pin(target.frame, "1.4", "1.6", 625, 640, 620)
    y2 = {h["id"]: E.visit(h, grid, t2) for h in holes}
    check(E.support(y1)["n_known"] == 25 and E.support(y2)["n_known"] == 0,
          "same participants/window, different known counts by region (YES dominates gaps)")
    seq = dict(kind="A_THEN_B", A=[[-2, 5], [-3, 10]], B=[[-1, 20], [1, 20]], first_close=610, last_close=615)
    seq_answer = run(620, sequence=seq)
    check(seq_answer["risk_set"]["ids"] == b["risk_set"]["ids"] and
          seq_answer["question"]["id"] != b["question"]["id"],
          "A -> B is a distinct selection condition even when participants coincide")
    one = copy.deepcopy(today)
    one["P"][1] = [-40, 5, 0]
    one["P"][2] = [20, 25, 22]
    check(E.sequence_value(one, grid, seq, 620) == "UNKNOWN", "same-M5 A/B does not invent intrabar order")
    still = copy.deepcopy(today)
    still["P"][7:] = [40, 60, 50]
    try:
        E.revisit(target, 645, 650, 660, still, grid)
        check(False, "continued occupancy wrongly called a return")
    except ValueError:
        check(True, "continued occupancy does not establish a return")
    child = E.revisit(target, 645, 650, 660, today, grid)
    check(child["target"]["id"] != target.id and child["target"]["parent"] == target.id,
          "return after observed departure has a new target and causal link")
    for d in (-1, 1):
        fr = E.Frame("NQ", "2025-12-17", "RDR", d, "100", "10", 605, 665)
        pin = E.pin(fr, ".4", ".6", 625, 640, 620)
        check(pin.physical == [[104, 1], [106, 1]] if d == 1 else pin.physical == [[96, 1], [94, 1]],
              "directed SD to fixed physical band, direction " + str(d))
    schema = json.loads((ROOT / "integration/reference/trace/build/dr_lab_trace.schema.json").read_text(encoding="utf-8"))
    schema["$ref"] = "#/$defs/ArchitectureCheckEvidence"
    for key in ("required", "properties", "additionalProperties", "type"):
        schema.pop(key, None)
    ev = A.evidence(A.transition(a, b), [dict(artifact="test", version=E.VERSION)], "tests/continuity24.py")
    validator = next(p / ".venv-linkml/Scripts/python.exe" for p in [ROOT, *ROOT.parents]
                     if (p / ".venv-linkml/Scripts/python.exe").is_file())
    subprocess.run([str(validator), "-B", "-c", "import json,sys,jsonschema; x=json.load(sys.stdin); jsonschema.Draft202012Validator(x['schema']).validate(x['evidence'])"],
                   input=json.dumps(dict(schema=schema, evidence=ev)), text=True, check=True, capture_output=True)
    check(True, "evidence validates against existing Trace ArchitectureCheckEvidence (no new ontology class)")
    print("ALL GOOD", flush=True)


if __name__ == "__main__":
    main()
