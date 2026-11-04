"""Validate this proposal's mapping, not RPX calculations or runtime admission.

Uses the current compiled SC types and the frozen FOM JSON Schema. It never builds
or changes either registry. Run with .venv-linkml/Scripts/python.exe -B -X utf8.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path

from jsonschema import validators

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def digest(data):
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def index_registry(doc, spec):
    values, kinds = {}, {}
    for collection, rows in doc["registry"].items():
        if not isinstance(rows, list):
            continue
        kind = spec["classes"]["Registry"]["slots"].get(collection, {}).get("range")
        for row in rows:
            if isinstance(row, dict) and "id" in row:
                if row["id"] in values:
                    raise ValueError("duplicate registry id: " + row["id"])
                values[row["id"]], kinds[row["id"]] = row, kind
    return values, kinds


def check(data, sources=True):
    errors, counts = [], {}

    def require(ok, code, detail):
        counts[code] = counts.get(code, 0) + 1
        if not ok:
            errors.append({"check": code, "detail": detail})

    sc = read("contract/build/runtime_spec.json")
    candidate = read("integration/candidates/build/runtime_spec.json")
    fom = read("integration/reference/trace/build/trace_runtime_spec.json")
    specs = {"accepted": sc, "candidate": candidate, "reference": fom}
    registries = {
        "accepted": index_registry(read("contract/build/registry.json"), sc),
        "candidate": index_registry(read("integration/candidates/build/registry.json"), candidate),
    }
    accepted, _ = registries["accepted"]

    if sources:
        require(bool(data["source_hashes"]), "SOURCE-PINS", "missing file pins")
        for name, expected in data["source_hashes"].items():
            p = ROOT / name
            require(p.is_file() and digest(p.read_bytes()) == expected, "SOURCE-PINS", name)
        for source in data["git_sources"]:
            result = subprocess.run(
                ["git", "show", source["revision"] + ":" + source["path"]],
                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            require(result.returncode == 0 and digest(result.stdout) == source["sha256_lf"],
                    "SOURCE-PINS", source["revision"] + ":" + source["path"])

    require(data["status"] == "PROPOSAL" and data["runtime_enabled"] is False
            and not data["admitted_predictive_claims"], "NO-PROMOTION", "proposal standing")
    require(data["artifact_kind"] == "IMPLEMENTATION_MAPPING_NOT_REGISTRY", "NO-PROMOTION", "mapping is not a registry product")
    require(data["validation_boundary"]["mapping_only"] is True, "NO-PROMOTION", "mapping boundary")
    require(data["baseline"]["reference_status"] == read("integration/reference/source.json")["standing"],
            "REFERENCE-STANDING", "frozen reference is not a current catalogue")

    for binding in data["existing_bindings"]:
        values, kinds = registries[binding["registry"]]
        require(binding["id"] in values and kinds.get(binding["id"]) == binding["class"],
                "TYPED-REFERENCE", binding["id"])
        slots = specs[binding["registry"]]["classes"].get(binding["class"], {}).get("slots", {})
        for slot in binding["slots"]:
            require(slot in slots, "EXISTING-SLOT", binding["class"] + "." + slot)

    for binding in data["class_bindings"]:
        classes = specs[binding["source"]]["classes"]
        require(binding["class"] in classes, "EXISTING-CLASS", binding["class"])
        for slot in binding["slots"]:
            require(slot in classes.get(binding["class"], {}).get("slots", {}),
                    "EXISTING-SLOT", binding["class"] + "." + slot)

    proposed = [data["proposed_profile"], *data["proposed_questions"],
                *data["proposed_outcomes"], *data["proposed_estimands"]]
    ids = [x["id"] for x in proposed]
    require(len(ids) == len(set(ids)), "PROPOSED-IDENTITY", "duplicate proposed id")
    for obj in proposed:
        require(obj["id"] not in accepted and obj["class"] in sc["classes"],
                "PROPOSED-IDENTITY", obj["id"])

    delta = data["schema_delta"]
    for name, additions in delta["enums"].items():
        require(name in sc["enums"], "SCHEMA-DELTA", name)
        for value in additions:
            require(value not in sc["enums"].get(name, []) and value not in candidate["enums"].get(name, []),
                    "SCHEMA-DELTA", name + ":" + value + " must be declared as new")
    for field in delta["fields"]:
        require(field["class"] in sc["classes"] and field["field"] not in sc["classes"][field["class"]]["slots"],
                "SCHEMA-DELTA", field["class"] + "." + field["field"])
        require(field["range"] == "string" or field["range"] in sc["classes"] or field["range"] in sc["enums"],
                "SCHEMA-DELTA", "range " + field["range"])
    for name in delta["conceptual_not_machine_classes"] + [r["class"] for r in delta["new_classes"]]:
        require(name not in sc["classes"] and name not in fom["classes"], "NO-INVENTED-CLASS", name)
    for p in delta["pattern_extensions"]:
        pattern = fom["classes"][p["class"]]["slots"][p["field"]]["pattern"]
        require(re.fullmatch(pattern, p["new_value"]) is None, "SCHEMA-DELTA", "standing pattern requires extension")

    outcomes = {o["id"]: o for o in data["proposed_outcomes"]}
    require(set(outcomes) == {"OUT:RPX-GUARDED-1", "OUT:RPX-BAR-MIN-1"}, "RPX-SEPARATION", "two distinct outcomes")
    for outcome in outcomes.values():
        require(outcome["horizon_end"] == "BEFORE_FIRST_FINAL_X_M5"
                and outcome["endpoint_evidence_horizon"] == "BLOCK_END_CLOSE_INCLUSIVE"
                and outcome["endpoint_outcome"] == "OUT:FINAL-X-1"
                and outcome["uses_case_future_as_label"] is True, "WINDOW-VS-EVIDENCE", outcome["id"])
        for field, enum in [("projection", "ProjectionKind"), ("event", "EventKind"), ("horizon_end", "HorizonEnd")]:
            require(outcome[field] in delta["enums"][enum], "SCHEMA-DELTA", outcome["id"] + "." + field)
    if "OUT:RPX-BAR-MIN-1" in outcomes:
        require(outcomes["OUT:RPX-BAR-MIN-1"]["empirical_status"] == "NOT_MEASURED", "EVIDENCE-SCOPE", "raw evidence")
    common = data["estimand_common"]
    require(common["q4_case_set"] == ["CS:F-CONF-1", "CS:F-CONF-ALL-1"]
            and common["q4_denominator"] == "N_BASE_UNIQUE_MEMBERS", "SET-DENOMINATOR", "fixed confirmation family")
    require(common["claim_class"] == "DescriptiveClaim" and not common["surface_bindings"], "NO-PROMOTION", "no predictive or inherited UI binding")
    for est in data["proposed_estimands"]:
        require(est["q5_outcome"] in outcomes and est["question"] in ids
                and est["q7_measure"] in sc["enums"]["SummaryMeasure"], "ESTIMAND-LINK", est["id"])
    for edge in data["definition_edges"]:
        require(edge["from"] in outcomes and edge["to"] == "OUT:FINAL-X-1"
                and edge["field"] == "endpoint_outcome" and edge["scope"] == "SAME_CASE_FRAME_FULL_HORIZON",
                "ENDPOINT-DEPENDENCY", str(edge))
    require({e["from"] for e in data["definition_edges"]} == set(outcomes), "ENDPOINT-DEPENDENCY", "both RPX depend on X")

    patch = data["fom_catalog_patch"]
    frozen_terms = read("integration/reference/trace/catalog/55-terms.yaml")["terms"]
    terms = {t["id"]: t for t in frozen_terms + patch["terms"]}
    refs = set(accepted) | set(ids)
    for term in patch["terms"]:
        for target in term["denotes"]:
            require(target in refs, "TERM-REFERENCE", term["id"] + " -> " + target)
    swpc = (ROOT / "spec/DR-LAB-SWPC-1.1.md").read_text(encoding="utf-8-sig")
    for relation in patch["term_relations"]:
        require(relation["left"] in terms and relation["right"] in terms, "TERM-REFERENCE", relation["id"])
        for guard in relation["guards"]:
            require(re.search(r"\b" + re.escape(guard) + r"\b", swpc) is not None, "TERM-GUARD", guard)
    pragmatic = data["preserved_pragmatic_binding"]
    require(pragmatic["mathematical_identity"] is False and pragmatic["change_to_existing_answer"] is False
            and pragmatic["mandatory_sequence_B_then_L"] is False, "PRAGMATIC-NOT-IDENTITY", "preserve accepted answer")

    facets = {f["id"]: f for f in read("integration/reference/trace/catalog/60-facets.yaml")["facet_definitions"] + patch["facet_definitions"]}
    for assignment in data["facet_assignments"]:
        definition = facets.get(assignment["facet"])
        require(definition is not None, "FACET-SCOPE", assignment["facet"])
        if definition:
            expected = {"ESTIMANDS": "EstimandSpecification", "CASE_SETS": "CaseSetSpecification"}.get(definition["scope_ru"])
            require(expected is None or assignment["target_class"] == expected, "FACET-SCOPE", assignment["facet"])
    require(facets["FACET:OUTCOME"]["projection"] == "outcome_id", "FACET-DERIVATION", "direct outcome identity")
    for finding in patch["research_findings"]:
        require(finding["accepted_basis"] is False and finding["lifecycle"] == "NOT_PROMOTED"
                and "OUT:RPX-BAR-MIN-1" not in finding["validates"], "EVIDENCE-SCOPE", finding["id"])
        for target in finding["validates"]:
            require(target in refs, "EVIDENCE-SCOPE", target)
    for collection in patch.values():
        if isinstance(collection, list):
            for record in collection:
                for evidence in record.get("evidence", []):
                    require((ROOT / evidence.split("#", 1)[0]).is_file(), "EVIDENCE-FILE", evidence)

    schema = read("integration/reference/trace/build/dr_lab_trace.schema.json")
    scoped = {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": "#/$defs/FomCatalog"}
    validator = validators.validator_for(scoped)(scoped)
    schema_errors = list(validator.iter_errors(patch))
    require(not schema_errors, "FOM-STRUCTURE", "; ".join(e.message for e in schema_errors))
    return errors, counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    data = json.loads((HERE / "ontology-map.json").read_text(encoding="utf-8"))
    errors, counts = check(data)
    mutations = [
        ("wrong existing type", "TYPED-REFERENCE", lambda d: d["existing_bindings"][0].update({"class": "EstimandSpecification"})),
        ("C2 promotion", "NO-PROMOTION", lambda d: d["estimand_common"].update({"claim_class": "PredictiveClaim"})),
        ("raw inherits research", "EVIDENCE-SCOPE", lambda d: d["proposed_outcomes"][1].update({"empirical_status": "VALIDATED"})),
        ("measurement becomes full block", "WINDOW-VS-EVIDENCE", lambda d: d["proposed_outcomes"][1].update({"horizon_end": "BLOCK_END_CLOSE_INCLUSIVE"})),
        ("set role attached to outcome", "FACET-SCOPE", lambda d: d["facet_assignments"][5].update({"target_class": "OutcomeSpecification"})),
        ("pragmatic answer becomes identity", "PRAGMATIC-NOT-IDENTITY", lambda d: d["preserved_pragmatic_binding"].update({"mathematical_identity": True})),
        ("guarded loses dependency on X", "ENDPOINT-DEPENDENCY", lambda d: d["definition_edges"].pop(0)),
    ]
    counterexamples = []
    for name, expected, mutate in mutations:
        changed = copy.deepcopy(data)
        mutate(changed)
        detected, _ = check(changed, sources=False)
        passed = any(e["check"] == expected for e in detected)
        counterexamples.append({"case": name, "expected_check": expected, "detected": passed})
        if not passed:
            errors.append({"check": "COUNTEREXAMPLE", "detail": name})
    report = {
        "artifact": data["id"], "outcome": "PASS" if not errors else "FAIL",
        "scope": "proposal mapping, references, FOM record structure and source preservation only",
        "checks": counts, "violations": errors, "counterexamples": counterexamples,
        "boundaries": data["validation_boundary"],
        "manifest_sha256": digest((HERE / "ontology-map.json").read_bytes()),
    }
    if args.report:
        (HERE / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
