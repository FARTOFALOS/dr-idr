"""Independent recount and cross-release relations using the retained FOM/Trace evidence form.

These are bounded new checks; the frozen catalog is not silently rebound. They
validate computations/relations, not presentation, calibration or human acceptance.
"""
from __future__ import annotations

from fractions import Fraction
import importlib.util
from pathlib import Path
import numpy as np

from revisions24 import digest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("_continuity_reference_fom", ROOT / "integration/reference/trace/fom.py")
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)


def _label(case, grid, target, first, last):
    """Scalar reference. It does not call the candidate's visit/selection helpers."""
    low = Fraction(*target["low"])
    high = Fraction(*target["high"])
    missing, hit = False, False
    for t, bar in zip(grid, case["P"]):
        if not first <= t <= last:
            continue
        if not all(np.isfinite(v) for v in bar):
            missing = True
        else:
            hit |= Fraction(int(bar[0]), int(case["w"])) < high and Fraction(int(bar[1]), int(case["w"])) >= low
    return "YES" if hit else "UNKNOWN" if missing else "NO"


def check_frame(packet, cases, today, grid):
    errors = []
    cut, t = packet["context"]["cut"], packet["target"]
    expected_physical = [Fraction(t["frame"]["edge"]) + t["frame"]["direction"] *
                         Fraction(t["frame"]["width"]) * Fraction(*band) for band in (t["low"], t["high"])]
    if [Fraction(*p) for p in t["physical_edges"]] != expected_physical:
        errors.append(("frame", "physical pin differs from its fixed SD transform"))
    identity = {k: t[k] for k in ("frame", "low", "high", "first_close", "last_close", "parent", "creation_kind")}
    if digest(identity) != t["id"] or t["id"] != packet["context"]["target_id"]:
        errors.append(("target", "target identifier differs from the declared event/frame"))
    actual, eligible = [], []
    target_cl = None
    for c in [today] + cases:
        post = [bar for j, bar in enumerate(c["P"]) if j > c["a"] and grid[j] <= cut]
        okay = (bool(post) and all(all(np.isfinite(v) for v in b) for b in post) and
                (c.get("oppv") is None or all(b[2] >= c["oppv"] for b in post)))
        if c is today:
            target_cl = Fraction(int(post[-1][2]), int(c["w"])) if okay else None
        elif c["date"] < today["date"] and okay:
            eligible.append(c["id"])
            if target_cl is not None and abs(Fraction(int(post[-1][2]), int(c["w"])) - target_cl) <= Fraction(1, 4):
                actual.append(c["id"])
    sel = packet["selection"]
    if set(actual) != set(sel["M"]) or set(eligible) != set(sel["eligible"]):
        errors.append(("M", "reference prefix/position membership differs"))
    if set(sel["G"]) != {c["id"] for c in cases if c["date"] < today["date"]}:
        errors.append(("G", "parent is not exactly the earlier-date corpus"))
    if not set(packet["risk_set"]["ids"]) <= set(sel["M"]) <= set(sel["eligible"]) <= set(sel["G"]):
        errors.append(("sets", "required child/parent relation fails"))
    if sel["full_path_compared"] or sel["compared"] != "POSITION_AT_COMMON_CLOCK":
        errors.append(("comparison", "position has been presented as whole-path compatibility"))
    q = packet["question"]
    by_id = {c["id"]: c for c in cases}
    expected_risk = []
    # This independent reference covers the ordinary and NO_VISIT residual question.
    sequence = any(c["kind"] == "A_THEN_B" for c in q["conditions"])
    if not sequence:
        for cid in actual:
            c = by_id[cid]
            keep = True
            for cond in q["conditions"]:
                if cond["kind"] == "WINDOW_NO_VISIT":
                    keep &= (c["a"] < 0 or grid[c["a"]] < t["first_close"])
                    keep &= _label(c, grid, t, t["first_close"], cut) == "NO"
            if keep:
                expected_risk.append(cid)
        if set(expected_risk) != set(packet["risk_set"]["ids"]):
            errors.append(("risk", "no-visit prefix condition was dropped or misapplied"))
    labels = {cid: _label(by_id[cid], grid, t, max(t["first_close"], cut + 5), t["last_close"])
              for cid in packet["risk_set"]["ids"]} if q["active"] and cut < t["last_close"] else {}
    if labels != packet["labels"]:
        errors.append(("labels", "reference future-range labels differ"))
    e = packet["estimate"]
    s = packet["support"]
    if e is not None and e != s:
        errors.append(("estimate", "issued value differs from recounted support"))
    if s:
        yes, no, unknown = (sum(x == k for x in labels.values()) for k in ("YES", "NO", "UNKNOWN"))
        if (s["n_total"], s["n_known"], s["yes"], s["no"], s["unknown"]) != (len(labels), yes + no, yes, no, unknown):
            errors.append(("support", "outcome-specific known count or denominator differs"))
        expected = [yes / len(labels), (yes + unknown) / len(labels)] if labels else None
        if s["bounds"] != expected or (unknown and s["point_is_comparison_score"]):
            errors.append(("uncertainty", "unknown outcomes have become a ranking point"))
    if e is None and packet["status"] == "RESEARCH_ONLY":
        errors.append(("estimate", "open supported phase lost its research result"))
    actual_today = _label(today, grid, t, t["first_close"], min(cut, t["last_close"]))
    state = packet["observed"]
    if state["value"] != actual_today:
        errors.append(("fact", "target knowledge differs from observed closed prefix"))
    if state["status"] == "FACT_YES":
        witnessed = [T for T in grid if t["first_close"] <= T <= min(cut, t["last_close"]) and
                     _label(today, grid, t, T, T) == "YES"]
        if state["available_at"] != witnessed[0] or e is not None:
            errors.append(("fact", "visit time is premature or retains a future percentage"))
    return F.result("CONTINUITY-FRAME-RECOUNT", len(cases), errors,
                    dict(sequence_reference="NOT_COVERED" if sequence else "NOT_APPLICABLE"))


def transition(before, after):
    """An unchanged target does not imply an unchanged residual question."""
    errors = []
    a, b = before["context"], after["context"]
    if not a["cut"] < b["cut"]:
        errors.append(("cut", "transition must advance the closed M5 cut"))
    for k in ("instrument", "date", "block", "target_id", "original_revision", "method"):
        if a[k] != b[k]:
            errors.append((k, "fixed-target continuity invariant changed"))
    if before["target"] != after["target"]:
        errors.append(("target", "physical area, absolute window or source frame drifted"))
    for p in (before, after):
        if digest({k: v for k, v in p["question"].items() if k != "id"}) != p["question"]["id"]:
            errors.append(("question", "question identifier differs from its content"))
    same_question = before["question"]["id"] == after["question"]["id"]
    same_definition = {k: v for k, v in before["question"].items() if k != "id"} == {
        k: v for k, v in after["question"].items() if k != "id"}
    if same_question != same_definition:
        errors.append(("question", "question identity hides a changed remainder or condition"))
    common = set(before["risk_set"]["ids"]) & set(after["risk_set"]["ids"])
    if same_question and a["history_revision"] == b["history_revision"] and any(
            before["labels"].get(k) != after["labels"].get(k) for k in common):
        errors.append(("historical outcome", "same event on the same witness changed without a revision"))
    if after["observed"]["status"] != "OPEN" and after["estimate"] is not None:
        errors.append(("applicability", "resolved/gapped target still bears a fresh percentage"))
    if before["observed"]["status"] == "FACT_YES" and after["observed"]["status"] != "FACT_YES":
        errors.append(("fact", "an established visit disappeared"))
    reasons = []
    if a["prefix_revision"] != b["prefix_revision"]:
        reasons.append("NEW_OBSERVATION")
    if a["history_revision"] != b["history_revision"]:
        reasons.append("HISTORY_REVISION")
    if before["selection"]["M"] != after["selection"]["M"]:
        reasons.append("POSITION_MEMBERSHIP_CHANGED")
    if not same_question:
        reasons.append("QUESTION_REMAINDER_OR_APPLICABILITY_CHANGED")
    if before["question"]["conditions"] != after["question"]["conditions"]:
        reasons.append("PREFIX_CONDITION_CHANGED")
    if after["observed"]["status"].startswith("FACT"):
        reasons.append("OBSERVED_FACT")
    return F.result("CONTINUITY-TRANSITION", 8, errors, dict(
        before=a["id"], after=b["id"], same_target=True, same_question=same_question,
        same_original=a["original_revision"] == b["original_revision"], reasons=reasons,
        entered=len(set(after["selection"]["M"]) - set(before["selection"]["M"])),
        left=len(set(before["selection"]["M"]) - set(after["selection"]["M"]))))


def evidence(result, versions, source):
    return dict(check=result["check"], obligation="FIXED-WINDOW-CANDIDATE:" + result["check"],
                origin="MACHINE_RUN_HERE", outcome=result["outcome"], artifact_versions=versions,
                checked=result["checked"], source=source,
                detail="Bounded executable FOM/Trace relation check; no UI or human acceptance. " +
                       digest(result))
