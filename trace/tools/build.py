"""Builds the trace catalog of DR Lab from its sources (run with the LinkML environment).

    .venv-linkml\\Scripts\\python.exe trace/tools/build.py           # lint, validate, generate, check, write
    .venv-linkml\\Scripts\\python.exe trace/tools/build.py --check   # regenerate in memory, compare with the files

Sources (the only places the trace is written by hand):
    trace/schema/dr_lab_trace.yaml   the LinkML module (imports contract/schema/dr_lab_sc.yaml unchanged)
    trace/catalog/*.yaml             the catalog: standing, architecture entries, boundaries, scenes, absence bindings
Read, never written:
    contract/build/registry.json     the compiled SC-1.1 registry the catalog points into
    spec/DR-LAB-SWPC-1.1.md, tests/swpc11.py   the bindings B01-B18 and §9 (estimand -> bindings), parsed by swpc11
Products (committed, never edited by hand; lab/semtrace.py reads them without LinkML):
    trace/build/catalog.json                the merged catalog with the generated presentation bindings and the stamps
    trace/build/trace_runtime_spec.json     the structural rules of every class (SC-1.1's and the trace's)
    trace/build/dr_lab_trace.schema.json    the JSON Schema LinkML generates (closed world), used by tests/trace_arch.py

Steps: linkml-lint (trace/schema/linkml-lint.yaml) -> every catalog file and the compiled whole validated against
TraceCatalog (closed world) -> the presentation bindings generated from SWPC-1.1 §9 -> the static checks of
lab/semtrace.py run on the fresh products (references and their types, code, checks, estimand chains, claim profiles,
standing, edition, coverage) -> the products, deterministic, stamped with the SHA-256 of every source.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

import yaml
from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml.validator import Validator
from linkml.validator.plugins import JsonschemaValidationPlugin
from linkml_runtime.utils.schemaview import SchemaView

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "trace" / "schema" / "dr_lab_trace.yaml"
LINT = ROOT / "trace" / "schema" / "linkml-lint.yaml"
CAT_DIR = ROOT / "trace" / "catalog"
OUT = ROOT / "trace" / "build"
SC_SCHEMA = ROOT / "contract" / "schema" / "dr_lab_sc.yaml"
SC_REGISTRY = ROOT / "contract" / "build" / "registry.json"
SWPC_DOC = ROOT / "spec" / "DR-LAB-SWPC-1.1.md"
SWPC_RECORD = ROOT / "tests" / "swpc11.py"
ARCH = [ROOT / "meaning" / "lens" / "2026-10-13-semantic-architecture" / "01-DR-LAB-SEMANTIC-ARCHITECTURE-0.1.md",
        ROOT / "meaning" / "lens" / "2026-10-13-semantic-architecture" / "02-DR-LAB-SEMANTIC-ARCHITECTURE-0.2-dopolnenie.md"]
PAGE = {name: ROOT / "design" / "sozvezdiya-24" / "src" / name for name in ("app.js", "panel.js", "graph.js")}


def sha256_lf(p):
    return hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def rel(p):
    return str(Path(p).resolve().relative_to(ROOT)).replace("\\", "/")


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=1) + "\n"


def fail(msgs):
    for m in msgs:
        print("  FAIL", m)
    sys.exit(1)


def runtime_spec(sv):
    """The structural rules lab/semtrace.py applies (from LinkML's induced view), with the identifier of every class."""
    classes, enums = {}, {}
    for name in sorted(sv.all_enums()):
        enums[name] = sorted(sv.get_enum(name).permissible_values)
    for name in sorted(sv.all_classes()):
        c = sv.get_class(name)
        slots, designator = {}, None
        for s in sv.class_induced_slots(name):
            rng = s.range or sv.schema.default_range or "string"
            inlined = bool(s.inlined or s.inlined_as_list)
            if rng in sv.all_classes() and not sv.get_identifier_slot(rng):
                inlined = True
            d = dict(range=rng, required=bool(s.required or s.identifier), multivalued=bool(s.multivalued), inlined=inlined, identifier=bool(s.identifier))
            for k, a in (("min", "minimum_value"), ("max", "maximum_value"), ("min_card", "minimum_cardinality"), ("max_card", "maximum_cardinality")):
                if getattr(s, a, None) is not None:
                    d[k] = getattr(s, a)
            if s.pattern:
                d["pattern"] = s.pattern
            if s.designates_type:
                designator = s.name
            slots[s.name] = d
        rules = []
        for r in c.rules or []:
            pre = {k: v.equals_string for k, v in (r.preconditions.slot_conditions or {}).items()} if r.preconditions else {}
            post = {}
            for k, v in ((r.postconditions.slot_conditions or {}).items() if r.postconditions else []):
                cond = {}
                if v.required:
                    cond["required"] = True
                if v.equals_string is not None:
                    cond["equals"] = v.equals_string
                if str(v.value_presence or "") == "ABSENT":
                    cond["absent"] = True
                post[k] = cond
            rules.append(dict(pre=pre, post=post, description=r.description))
        classes[name] = dict(abstract=bool(c.abstract), slots=slots, rules=rules, designator=designator,
                             descendants=sorted(sv.class_descendants(name, reflexive=False)))
    return dict(schema=sv.schema.name, version=sv.schema.version, classes=classes, enums=enums)


def load_catalog():
    files = sorted(CAT_DIR.glob("*.yaml"))
    parts, merged = {}, {"catalog_part": "merged"}
    for f in files:
        d = yaml.safe_load(f.read_text(encoding="utf-8"))
        parts[f] = d
        for k, v in d.items():
            if isinstance(v, list):
                merged.setdefault(k, []).extend(v)
    return files, parts, merged


def swpc_record():
    """tests/swpc11.py parses SWPC-1.1 (its only source) into B (bindings), ROUTES (§9) and REC (the engineering record:
    code anchors, checks); imported as a module, its checks do not run."""
    spec = importlib.util.spec_from_file_location("swpc11_record", SWPC_RECORD)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT / "lab"))
    spec.loader.exec_module(mod)
    return mod


def page_file_of(fn):
    import re
    for name, p in PAGE.items():
        if re.search(r"(function " + re.escape(fn) + r"\(|const " + re.escape(fn) + r" = )", p.read_text(encoding="utf-8")):
            return name
    return None


def generate_bindings(reg, merged):
    """One presentation binding per (binding of SWPC-1.1 §9, estimand or fact form): statistical bindings name the claim
    form and where the number is made (a bundle of the server, or a passport the server re-verifies); fact bindings name
    the fact form and the routes that carry the fact (catalog fact_surfaces)."""
    sw = swpc_record()
    forms = {f["estimand"]: f["id"] for f in reg["claim_forms"]}
    served = {}
    for s in reg["surfaces"]:
        for e in s.get("estimands") or []:
            served.setdefault(e, []).append(s["id"])
    facts = {x["fact_form"]: x["surfaces"] for x in merged.get("fact_surfaces", [])}
    # the routes of a binding: those serving the statistics it presents (a page passport's numbers come from the family);
    # a fact binding is carried by the fact form's routes that are also its binding's, or by all of them if it has none
    routes_of = {}
    for rid, bids in sw.ROUTES.items():
        if rid.startswith("EST:"):
            for bid in bids:
                routes_of.setdefault(bid, set()).update(served.get(rid) or ["API:/api/d24/family"])
    out, errs = [], []
    for rid in sorted(sw.ROUTES):
        for bid in sw.ROUTES[rid]:
            rec, b = sw.REC[bid], sw.B[bid]
            anchors = []
            for fn in rec["code"]:
                f = page_file_of(fn)
                if f is None:
                    errs.append(f"{bid}: code anchor {fn} not found in the page")
                else:
                    anchors.append(f"design/sozvezdiya-24/src/{f}::{fn}")
            base = dict(id=f"PB:{bid}/{rid}", binding=bid, semantic_source="SRC:SWPC-1.1", code_anchors=anchors,
                        machine_checks=[f"test:tests/swpc11_browser.mjs#{m.lower()}" for m in b["m"]], human_checks=list(b["h"]))
            if rid.startswith("EST:"):
                site = "SERVER_BUNDLE" if rid in served else "PAGE_PASSPORT"
                surfaces = served.get(rid) or ["API:/api/d24/family", "API:/api/d24/verify"]
                out.append(dict(base, binding_class="StatisticalPresentationBinding", estimand=rid, claim_form=forms.get(rid, "?"), derivation_site=site, surfaces=surfaces))
            else:
                if rid not in facts:
                    errs.append(f"{rid}: no fact_surfaces record in the catalog")
                own = [s for s in facts.get(rid, []) if s in routes_of.get(bid, set())]
                out.append(dict(base, binding_class="FactPresentationBinding", fact_form=rid, surfaces=own or facts.get(rid, [])))
    return out, errs


def build(check=False):
    print("DR Lab trace · building the catalog")
    r = subprocess.run([str(Path(sys.executable).parent / "linkml-lint"), "-c", str(LINT), str(SCHEMA)], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        fail(["linkml-lint: " + (r.stdout + r.stderr)[-2000:]])
    print("  ok   linkml-lint (trace/schema/linkml-lint.yaml)")
    sv = SchemaView(str(SCHEMA))
    validator = Validator(str(SCHEMA), validation_plugins=[JsonschemaValidationPlugin(closed=True)])
    reg_doc = json.loads(SC_REGISTRY.read_text(encoding="utf-8"))
    reg = reg_doc["registry"]
    files, parts, merged = load_catalog()
    gen, gerr = generate_bindings(reg, merged)
    if gerr:
        fail(gerr[:30])
    merged["bindings"] = list(merged.get("bindings", [])) + gen
    errs = []
    for f, d in parts.items():
        errs += [f"{rel(f)}: {res.message}" for res in validator.validate(d, "TraceCatalog").results]
    errs += [f"compiled catalog: {res.message}" for res in validator.validate(merged, "TraceCatalog").results]
    if errs:
        fail(errs[:40])
    print(f"  ok   {len(files)} catalog files and the compiled catalog valid against TraceCatalog (closed world); {len(gen)} bindings generated from SWPC-1.1 §9")
    spec = runtime_spec(sv)
    spec_text = dumps(spec)
    body_text = dumps(merged)
    jschema = JsonSchemaGenerator(str(SCHEMA), top_class="TraceCatalog", include_range_class_descendants=True).serialize()
    sources = {rel(p): sha256_lf(p) for p in [SCHEMA, LINT, SC_SCHEMA, SC_REGISTRY, SWPC_DOC, SWPC_RECORD] + ARCH + files}
    stamps = dict(trace_version="dr-lab-trace-1", sources=dict(sorted(sources.items())), linkml=version("linkml"),
                  runtime_spec_sha256=hashlib.sha256(spec_text.encode()).hexdigest(), catalog_sha256=hashlib.sha256(body_text.encode()).hexdigest(),
                  sc_registry_sha256=reg_doc["stamps"]["registry_sha256"])
    cat_text = dumps(dict(stamps=stamps, catalog=merged))
    products = {OUT / "catalog.json": cat_text, OUT / "trace_runtime_spec.json": spec_text,
                OUT / "dr_lab_trace.schema.json": jschema if jschema.endswith("\n") else jschema + "\n"}
    with tempfile.TemporaryDirectory() as tmp:             # lab/semtrace.py's own static checks, on the fresh products
        tc, ts = Path(tmp) / "catalog.json", Path(tmp) / "trace_runtime_spec.json"
        tc.write_text(cat_text, encoding="utf-8", newline="\n")
        ts.write_text(spec_text, encoding="utf-8", newline="\n")
        sys.path.insert(0, str(ROOT / "lab"))
        import semtrace as T
        st = T.load(tc, ts)
        res, g, _ = T.static_checks(st)
    bad = [c for c in res if c["outcome"] != "PASS"]
    for c in res:
        print(f"  {'ok  ' if c['outcome'] == 'PASS' else 'FAIL'} {c['check']:<18} {c['checked']:>5}")
    if bad:
        fail([f"{c['check']}: {v['where']}: {v['message']}" for c in bad for v in c["violations"][:6]])
    print(f"  ok   the static checks of lab/semtrace.py pass on the fresh products ({len(g.nodes)} nodes)")
    if check:
        diff = [rel(p) for p, t in products.items() if not p.exists() or p.read_text(encoding="utf-8").replace("\r\n", "\n") != t]
        if diff:
            fail([f"{d} is not what the sources produce (run trace/tools/build.py)" for d in diff])
        print("  ok   the committed products equal what the sources produce")
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        for p, t in products.items():
            p.write_text(t, encoding="utf-8", newline="\n")
        print("  ok   wrote " + ", ".join(rel(p) for p in products))
    print("BUILT" if not check else "IN SYNC")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    build(ap.parse_args().check)
