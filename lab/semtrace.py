"""DR Lab — the executable semantic trace: DR-LAB-SEMANTIC-ARCHITECTURE 0.1 with its addendum 0.2 (standard library and
the lab's own modules; LinkML is needed only to build trace/build/).

What it is. An index and a verifier over objects that already exist: the compiled SC-1.1 registry (contract/build), the
trace catalog (trace/build: the architecture's entries, the standing of every profile on independent axes, the
boundaries, the declared scenes, the presentation bindings generated from SWPC-1.1 §9), the code these name, the
responses of the routes of lab/server.py (computed in-process by the very functions the routes call, through the
SC-1.1 gate), the records of the Q1 pilot's stores, and the state screen 24 actually rendered. From them it builds one
graph of typed links and answers:
  - check   — does every definition resolve to objects of its type, every reference to existing code and checks, every
              estimand to its question, case set, outcome, claim form, estimator, route and presentation;
  - scene   — for one claim of a declared scene, the chain observation → state → question → set → outcomes →
              computation → estimate and support → admission → presentation (→ issue), each link with its status in
              this run: VERIFIED, IMPLEMENTED_UNVERIFIED, PROPOSED, MISSING or NOT_APPLICABLE;
  - impact  — what depends on a changed definition, rule or function (the reverse closure);
  - lineage — what one claim depends on, back to its sources (the backward reconstruction).

What it does not do. It computes no statistic of its own: every number is the one the gate (lab/contract.py) published
and re-derived by the gate's reference definitions; the trace adds what the gate does not check (links and their types,
the standing of the profiles, the future of the target and of the analogues replaced in memory, identities across runs
and against the accepted line, the stored issues, the screen against the bundle) and the report. The three operations
of 0.2 — computing an answer, presenting it, saving an issue — are recorded apart; none is taken as evidence of another.
Nothing is written except where `run` is asked to write; the market base and the Q1 stores are only read.

    python -B lab/semtrace.py check                      static link checks (no market base needed)
    python -B lab/semtrace.py scene SCENE:ARRIVE-HALF    trace one declared scene (the base needed)
    python -B lab/semtrace.py impact OUT:REACH-REST-1    what depends on a definition, a rule or code
    python -B lab/semtrace.py lineage EST:K-ARRIVE       what a claim depends on
    python -B lab/semtrace.py q1                         the stored Q1 issues and outcomes
    python -B lab/semtrace.py counterexamples            the six kinds of broken dependencies, each must be detected
    python -B lab/semtrace.py run --out studies/trace_2026_10_13 [--screens]   everything, with the evidence written
"""
from __future__ import annotations

import argparse
import ast
import copy
import difflib
import hashlib
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
from collections import defaultdict, deque
from contextlib import contextmanager
from pathlib import Path

LAB = Path(__file__).resolve().parent
ROOT = LAB.parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

import contract as C  # noqa: E402

TRACE = ROOT / "trace"
BUILD = TRACE / "build"
CATALOG_FILE = BUILD / "catalog.json"
SPEC_FILE = BUILD / "trace_runtime_spec.json"
ARCH_DOC = ROOT / "meaning" / "lens" / "2026-10-13-semantic-architecture" / "01-DR-LAB-SEMANTIC-ARCHITECTURE-0.1.md"
VERSION = "dr-lab-trace-1"
WORST = ["MISSING", "PROPOSED", "IMPLEMENTED_UNVERIFIED", "VERIFIED", "NOT_APPLICABLE"]       # worst first

TRACE_CHECKS = {
    "REF-RESOLVE": "every reference of the registry and the catalog resolves to an object of its class",
    "ID-UNIQUE": "identifiers are unique across the SC-1.1 registry and the trace catalog",
    "CODE-REFS": "every code reference (reference definitions, implementations, code anchors, page words) exists",
    "CHECK-REFS": "every check reference (test, runtime, page, build, schema, human, reported, trace) exists",
    "ESTIMAND-CHAIN": "every estimand has its question, case sets, outcome with a reference definition, one claim form, an estimator, a route or a page verification, a presentation binding and a profile standing",
    "CLAIM-PROFILE": "every claim form is of a class admissible on every case set of its estimand; C1 names its condition; no C2 / C3; the estimand's profile is its route's",
    "STANDING": "every profile has its standing from sources; a decision that is not ACCEPTED under an ACTIVE registry status is a registered boundary",
    "EDITION-ADDITIVE": "the text the line pins is the accepted text, or keeps every accepted line (an additive amendment, reported as proposed)",
    "ACCEPTED-CODE-IDENTITY": "BASE-24 and NOW-1.0 are computed on this line by the code the operator accepted: the modules compared, and the bundles of the declared scenes recomputed on the accepted commit",
    "CATALOG-COVERAGE": "every entry of the architecture 0.1 (ENT, R, INV, PROC, T, A, GAP) has its catalog record, and no record names an id 0.1 does not have",
    "BINDING-COVERAGE": "every estimand and fact form is presented by a binding of SWPC-1.1 §9; every absence binding names a registered label or a page function",
    "GATE-CONFORMANT": "the response passed the SC-1.1 gate: envelope valid and CONFORMANT, every gate check PASS, the bundle verified by reference",
    "BUNDLE-CLAIM": "the bundle's estimand, claim form, class, case set, route and profile agree with the registry",
    "BUNDLE-COUNTS": "numerators, denominators, supports and unknowns agree with each other and with a recount by the reference definitions",
    "IDENTITY": "family, snapshot and zone identities re-derived; the same request computed twice gives the same bundle",
    "FUTURE-TARGET": "the target day's candles after the cut, replaced in memory, change nothing the response computed",
    "FUTURE-MEMBERS": "the analogues' candles after the cut and after their own activation, replaced in memory, change no membership (labels may change)",
    "Q1-STORE": "stored Q1 issues and outcomes: identities recomputed, payload fingerprints, outcome links and revisions, the store's own verify(); bytes unchanged by the run",
    "Q1-ISSUE-MATCH": "the stored issue of the same target, cut, set and model answers what the screen block answers; reproduced IDENTICAL on its inputs",
    "SCREEN": "the element the page rendered is bound to the published bundle or a reference-checked passport, shows its value in the value form and its registered words, with no violation",
    "IMPACT": "the reverse closure of every definition on a traced chain contains the traced claim and its presentation",
}


def _rel(p):
    return str(Path(p).resolve().relative_to(ROOT)).replace("\\", "/")


def sha256_lf(p):
    return C.sha256_lf(p)


def canon(x):
    """Canonical JSON values: integral floats as integers (a share 1.0 and 1 are one value)."""
    if isinstance(x, float) and x.is_integer():
        return int(x)
    if isinstance(x, dict):
        return {k: canon(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [canon(v) for v in x]
    return x


def digest(obj):
    return hashlib.sha256(json.dumps(canon(obj), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()



def minute(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


# =====================================================================================================================
# the compiled catalog, its staleness, structural validation (the same closed world as lab/contract.py::validate)
# =====================================================================================================================
def load(catalog_file=CATALOG_FILE, spec_file=SPEC_FILE):
    data = json.loads(Path(catalog_file).read_text(encoding="utf-8"))
    spec = json.loads(Path(spec_file).read_text(encoding="utf-8"))
    reg = C.registry()
    if reg is None:
        raise RuntimeError("the compiled SC-1.1 registry is unreadable (contract/build/registry.json)")
    return dict(stamps=data["stamps"], cat=data["catalog"], spec=spec, reg=reg, sc_stale=C.stale())


def stale_reasons(st):
    """The compiled catalog carries the SHA-256 of every source; a change means it no longer represents them."""
    out = []
    for rel, want in st["stamps"]["sources"].items():
        p = ROOT / rel
        if not p.exists():
            out.append(f"source missing: {rel}")
        elif sha256_lf(p) != want:
            out.append(f"source changed since the build: {rel} (python trace/tools/build.py)")
    for p in sorted((TRACE / "catalog").glob("*.yaml")):
        if _rel(p) not in st["stamps"]["sources"]:
            out.append(f"catalog file not compiled: {_rel(p)}")
    if SPEC_FILE.exists() and sha256_lf(SPEC_FILE) != st["stamps"].get("runtime_spec_sha256"):
        out.append("trace_runtime_spec.json does not match the catalog stamps")
    if st.get("sc_stale"):
        out.append("the SC-1.1 contract itself is CONTRACT_STALE: " + "; ".join(st["sc_stale"])[:200])
    return out


_TYPES = {"string": str, "integer": int, "float": (int, float), "double": (int, float), "boolean": bool, "date": str, "uriorcurie": str}


def validate(obj, cls, spec, path="$"):
    """Structural errors of obj as an instance of class cls of the trace schema (closed world)."""
    errs = []
    K = spec["classes"].get(cls)
    if K is None:
        return [f"{path}: unknown class {cls}"]
    if not isinstance(obj, dict):
        return [f"{path}: {cls} expects an object"]
    dt = K.get("designator")
    if dt and isinstance(obj.get(dt), str):
        sub = obj[dt]
        if sub not in K.get("descendants", []) and sub != cls:
            return [f"{path}.{dt}: {sub} is not a {cls}"]
        if sub != cls:
            K, cls = spec["classes"][sub], sub
    if K.get("abstract"):
        return [f"{path}: abstract class {cls} needs its designator"]
    slots = K["slots"]
    for k in obj:
        if k not in slots:
            errs.append(f"{path}.{k}: not a slot of {cls}")
    for name, S in slots.items():
        v = obj.get(name)
        if v is None:
            if S.get("required"):
                errs.append(f"{path}.{name}: required")
            continue
        if S.get("multivalued"):
            if not isinstance(v, list):
                errs.append(f"{path}.{name}: expects a list")
                continue
            if S.get("min_card") is not None and len(v) < S["min_card"]:
                errs.append(f"{path}.{name}: fewer than {S['min_card']}")
            if S.get("max_card") is not None and len(v) > S["max_card"]:
                errs.append(f"{path}.{name}: more than {S['max_card']}")
        for i, x in enumerate(v if S.get("multivalued") else [v]):
            p = f"{path}.{name}" + (f"[{i}]" if S.get("multivalued") else "")
            rng = S["range"]
            if rng in spec["enums"]:
                if x not in spec["enums"][rng]:
                    errs.append(f"{p}: {x!r} not in {rng}")
            elif rng in spec["classes"]:
                if S.get("inlined"):
                    errs += validate(x, rng, spec, p)
                elif not isinstance(x, str):
                    errs.append(f"{p}: a reference to {rng} is an id string")
            else:
                t = _TYPES.get(rng, str)
                if isinstance(x, bool) and rng != "boolean":
                    errs.append(f"{p}: boolean where {rng} expected")
                    continue
                if not isinstance(x, t):
                    errs.append(f"{p}: {type(x).__name__} where {rng} expected")
                    continue
            if isinstance(x, (int, float)) and not isinstance(x, bool):
                if S.get("min") is not None and x < S["min"]:
                    errs.append(f"{p}: {x} < {S['min']}")
                if S.get("max") is not None and x > S["max"]:
                    errs.append(f"{p}: {x} > {S['max']}")
            if S.get("pattern") and isinstance(x, str) and not re.search(S["pattern"], x):
                errs.append(f"{p}: does not match {S['pattern']}")
    for rule in K.get("rules", []):
        if all(obj.get(s) == c for s, c in rule["pre"].items()):
            for s, cond in rule["post"].items():
                if cond.get("required") and obj.get(s) is None:
                    errs.append(f"{path}.{s}: required when {rule['pre']}")
                if "equals" in cond and obj.get(s) is not None and obj.get(s) != cond["equals"]:
                    errs.append(f"{path}.{s}: must be {cond['equals']} when {rule['pre']}")
                if cond.get("absent") and s in obj:
                    errs.append(f"{path}.{s}: must be absent when {rule['pre']}")
    return errs


# =====================================================================================================================
# the code: names defined in the repository's files and the static calls of the lab's Python
# =====================================================================================================================
class CodeIndex:
    """Python by ast (functions, classes, methods, nested functions, module names); JavaScript by its declarations."""

    def __init__(self, root=ROOT):
        self.root = Path(root)
        self._py, self._txt = {}, {}

    def text(self, rel):
        if rel not in self._txt:
            p = self.root / rel
            self._txt[rel] = p.read_text(encoding="utf-8") if p.is_file() else None
        return self._txt[rel]

    def py(self, rel):
        if rel in self._py:
            return self._py[rel]
        src = self.text(rel)
        if src is None:
            self._py[rel] = None
            return None
        tree = ast.parse(src)
        names, funcs, imports = set(), {}, {}

        def visit(node, prefix, cls):
            for ch in ast.iter_child_nodes(node):
                if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    q = prefix + ch.name
                    names.add(q)
                    if not isinstance(ch, ast.ClassDef):
                        funcs[q] = (ch, cls)
                    visit(ch, q + ".", ch.name if isinstance(ch, ast.ClassDef) else cls)
                elif prefix == "" and isinstance(ch, (ast.Assign, ast.AnnAssign)):
                    for tg in (ch.targets if isinstance(ch, ast.Assign) else [ch.target]):
                        if isinstance(tg, ast.Name):
                            names.add(tg.id)
                elif prefix == "" and isinstance(ch, (ast.Import, ast.ImportFrom)):
                    for a in ch.names:
                        if isinstance(ch, ast.Import):
                            imports[a.asname or a.name] = ("module", a.name)
                        else:
                            mod = ch.module or ""
                            imports[a.asname or a.name] = ("from", mod, a.name)
                elif prefix == "" and isinstance(ch, (ast.If, ast.Try)):
                    visit(ch, prefix, cls)
        visit(tree, "", None)
        self._py[rel] = dict(names=names, funcs=funcs, imports=imports, src=src)
        return self._py[rel]

    def js(self, rel):
        src = self.text(rel)
        return None if src is None else set(re.findall(r"(?:function\s+|(?:const|let|var)\s+)([A-Za-z_$][\w$]*)", src))

    def exists(self, ref):
        """A code reference file::name (Python qualified name, or a JavaScript declaration)."""
        if "::" not in ref:
            return (self.root / ref).is_file(), "file"
        f, name = ref.split("::", 1)
        if f.endswith(".py"):
            info = self.py(f)
            return (info is not None and name in info["names"]), "python"
        if f.endswith((".js", ".mjs")):
            names = self.js(f)
            return (names is not None and name in names), "javascript"
        return False, "unknown file kind"

    def source(self, rel, qual):
        info = self.py(rel)
        if info is None or qual not in info["funcs"]:
            return None
        return ast.get_source_segment(info["src"], info["funcs"][qual][0])

    # -- the static calls (and references) of the lab's Python: caller -> callee, by names (BND-11)
    def lab_module(self, name):
        for cand in (f"lab/{name.replace('.', '/')}.py", f"lab/q1/{name.split('.')[-1]}.py" if name.startswith("q1") else None):
            if cand and (self.root / cand).is_file():
                return cand
        return None

    def calls(self, rel):
        info = self.py(rel)
        if info is None:
            return {}
        alias = {}
        for a, imp in info["imports"].items():
            if imp[0] == "module":
                m = self.lab_module(imp[1])
                if m:
                    alias[a] = ("mod", m)
            else:
                mod, nm = imp[1], imp[2]
                m = self.lab_module(f"{mod}.{nm}") if mod else None
                if m:
                    alias[a] = ("mod", m)
                else:
                    m2 = self.lab_module(mod) if mod else None
                    if m2:
                        alias[a] = ("name", m2, nm)
        out = {}
        for q, (fn, cls) in info["funcs"].items():
            hits = set()
            for node in ast.walk(fn):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    if node.id in info["names"] and node.id != q:
                        hits.add(f"{rel}::{node.id}")
                    elif node.id in alias and alias[node.id][0] == "name":
                        hits.add(f"{alias[node.id][1]}::{alias[node.id][2]}")
                elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                    base = node.value.id
                    if base == "self" and cls:
                        cand = f"{cls}.{node.attr}"
                        if cand in info["names"]:
                            hits.add(f"{rel}::{cand}")
                    elif base in alias and alias[base][0] == "mod":
                        hits.add(f"{alias[base][1]}::{node.attr}")
                    elif base in info["names"] and f"{base}.{node.attr}" in info["names"]:
                        hits.add(f"{rel}::{base}.{node.attr}")
                elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name):
                    base = node.value.value.id
                    if base in alias and alias[base][0] == "mod":
                        hits.add(f"{alias[base][1]}::{node.value.attr}.{node.attr}")
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) \
                        and node.func.value.id not in alias and node.func.value.id != "self":
                    # a method called on a local object (F.select(...)): resolved when exactly one class of the lab defines it
                    owners = self.methods().get(node.func.attr, [])
                    if len(owners) == 1:
                        hits.add(owners[0])
            out[f"{rel}::{q}"] = {h for h in hits if self.exists(h)[0]}
        return out

    def methods(self):
        """method name -> the classes of the lab's Python that define it (for calls on local objects; BND-11)."""
        if getattr(self, "_methods", None) is None:
            self._methods = defaultdict(list)
            for p in sorted(list((self.root / "lab").glob("*.py")) + list((self.root / "lab" / "q1").glob("*.py"))):
                r = str(p.relative_to(self.root)).replace("\\", "/")
                info = self.py(r)
                for q in info["funcs"] if info else []:
                    parts = q.split(".")
                    if len(parts) == 2 and parts[0][:1].isupper() and not parts[1].startswith("__"):
                        self._methods[parts[1]].append(f"{r}::{q}")
        return self._methods


CHECK_ROLES = {"operator"}


def check_ref_ok(code, ref, spec):
    """Does a check reference exist: test:<file>[::<function>|#<marker>], runtime:<file>::<name>, page:<file>::<function>,
    build:<file>[::<function>], schema:<class>, human:<role>, reported:<file>, trace:<check id>."""
    kind, _, rest = ref.partition(":")
    if kind == "trace":
        return rest in TRACE_CHECKS
    if kind == "human":
        return rest in CHECK_ROLES
    if kind == "schema":
        return rest in spec["classes"]
    if kind == "reported":
        return (ROOT / rest).is_file()
    if kind in ("test", "runtime", "page", "build"):
        if "#" in rest:
            f, marker = rest.split("#", 1)
            src = code.text(f)
            return src is not None and marker in src
        if "::" in rest:
            f, name = rest.split("::", 1)
            if f.endswith(".py"):
                info = code.py(f)
                return info is not None and name in info["names"]
            return code.exists(rest)[0]
        return (ROOT / rest).is_file()
    return False


# =====================================================================================================================
# the graph of typed links
# =====================================================================================================================
DEP, IMPL, CHECK, CALLS, SOURCE, BOUND = "dep", "impl", "check", "calls", "source", "bound"
CODE_SLOTS = {"reference_definition", "implementations", "implemented_by", "code_anchors"}
CHECK_SLOTS = {"check", "checks", "checked_by", "machine_checks"}
SOURCE_SLOTS = {"source_refs", "sources", "decision_sources", "human_acceptance_sources", "accepted_by", "semantic_source", "definitions"}
LOOSE_SLOTS = {"realized_by", "affects"}


class Graph:
    def __init__(self):
        self.nodes = {}
        self.out = defaultdict(list)
        self.inn = defaultdict(list)
        self.refs = []          # (src, slot, target, expected class or None, kind) for the resolution check

    def node(self, nid, kind, **data):
        n = self.nodes.get(nid)
        if n is None:
            self.nodes[nid] = n = dict(id=nid, kind=kind, **data)
        else:
            n.update({k: v for k, v in data.items() if v is not None})
        return n

    def edge(self, a, rel, b, cat):
        self.out[a].append((rel, b, cat))
        self.inn[b].append((rel, a, cat))


def _collections(spec, root):
    return {n: S["range"] for n, S in spec["classes"][root]["slots"].items() if S.get("multivalued") and S["range"] in spec["classes"]}


def _idslot(spec, cls):
    return next((n for n, S in spec["classes"][cls]["slots"].items() if S.get("identifier")), None)


def kind_of(nid):
    """The group of a node in the reports (ImpactKind)."""
    if nid.startswith("code:"):
        return "CODE"
    if nid.startswith(("check:", "OB:", "VAL:")) or re.fullmatch(r"K[0-3][0-9]", nid) or nid.startswith("H:"):
        return "CHECK"
    if nid.startswith(("API:", "FE:")):
        return "ROUTE"
    if nid.startswith(("PB:", "B:")):
        return "PRESENTATION"
    if nid.startswith(("EST:", "ESTR:")):
        return "ESTIMAND"
    if nid.startswith(("CF:", "FF:")):
        return "CLAIM"
    if nid.startswith("q1:"):
        return "STORED_RECORD"
    if re.match(r"^(ENT|R|INV|PROC|T|A|GAP|BND)-?\d", nid) or nid.startswith(("STANDING:", "EDST:", "SCENE:")):
        return "ARCHITECTURE"
    return "DEFINITION"


def build_graph(st, code=None):
    """Nodes: every object of the SC-1.1 registry and of the trace catalog, the schema classes and enums they name, the
    code and the checks they reference, the bindings B01-B18. Edges: every reference slot (a depends on b), every code
    reference (a is implemented by b), every check reference (a is checked by b), every source, and the static calls of
    the lab's Python (caller -> callee)."""
    code = code or CodeIndex()
    g = Graph()
    spec, reg, cat = st["spec"], st["reg"], st["cat"]
    origins = (("SC", reg, _collections(spec, "Registry")), ("TRACE", cat, _collections(spec, "TraceCatalog")))
    for origin, data, colls in origins:
        for coll, cls in colls.items():
            idslot = _idslot(spec, cls)
            for it in data.get(coll, []) or []:
                if not isinstance(it, dict) or not idslot or it.get(idslot) is None:
                    continue
                real = it.get(spec["classes"][cls].get("designator") or "") or cls
                g.node(it[idslot], "object", origin=origin, cls=real if real in spec["classes"] else cls, collection=coll)

    def code_node(ref):
        ref = re.sub(r"^(runtime|page|build):", "", ref)
        nid = "code:" + ref
        g.node(nid, "code", ref=ref)
        return nid

    def check_node(ref):
        nid = "check:" + ref
        g.node(nid, "check", ref=ref)
        kind, _, rest = ref.partition(":")
        if kind in ("runtime", "page", "build") and "::" in rest:
            g.edge(nid, "executes", code_node(rest), IMPL)
        return nid

    def loose(src, slot, x):
        if x.startswith("class:"):
            g.node(x, "class", name=x[6:])
            g.refs.append((src, slot, x, None, "class"))
        elif x.startswith("enum:"):
            g.node(x, "enum", name=x[5:])
            g.refs.append((src, slot, x, None, "enum"))
        else:
            g.refs.append((src, slot, x, None, "id"))
        g.edge(src, slot, x, DEP if slot == "realized_by" else BOUND)

    def walk(obj, cls, src):
        K = spec["classes"].get(cls)
        if K is None:
            return
        dt = K.get("designator")
        if dt and isinstance(obj.get(dt), str) and obj[dt] in spec["classes"]:
            K = spec["classes"][obj[dt]]
        for name, S in K["slots"].items():
            v = obj.get(name)
            if v is None:
                continue
            for x in (v if S.get("multivalued") else [v]):
                rng = S["range"]
                if name in CODE_SLOTS and isinstance(x, str):
                    for ref in re.findall(r"[\w./-]+\.(?:py|js|mjs)::[\w.]+", x) or [x]:
                        g.edge(src, name, code_node(ref), IMPL)
                        g.refs.append((src, name, ref, None, "code"))
                elif name in CHECK_SLOTS and isinstance(x, str):
                    g.edge(src, name, check_node(x), CHECK)
                    g.refs.append((src, name, x, None, "check"))
                elif name == "human_checks" and isinstance(x, str):
                    g.node("H:" + x, "human", task=x)
                    g.edge(src, name, "H:" + x, CHECK)
                elif name == "shown_by" and isinstance(x, str):
                    if x.startswith("page:"):
                        g.edge(src, name, code_node(x), IMPL)
                        g.refs.append((src, name, x[5:], None, "code"))
                    else:
                        form, key = x.split("#", 1)
                        g.edge(src, name, form, DEP)
                        g.refs.append((src, name, x, None, "label"))
                elif name in LOOSE_SLOTS and isinstance(x, str):
                    loose(src, name, x)
                elif name == "boundaries" and isinstance(x, str):
                    g.edge(src, name, x, BOUND)
                    g.refs.append((src, name, x, rng, "id"))
                elif rng in spec["classes"]:
                    if S.get("inlined") and isinstance(x, dict):
                        walk(x, x.get(spec["classes"][rng].get("designator") or "") or rng, src)
                    elif isinstance(x, str):
                        g.edge(src, name, x, SOURCE if name in SOURCE_SLOTS else DEP)
                        g.refs.append((src, name, x, rng, "id"))

    for origin, data, colls in origins:
        for coll, cls in colls.items():
            idslot = _idslot(spec, cls)
            for i, it in enumerate(data.get(coll, []) or []):
                if not isinstance(it, dict):
                    continue
                if idslot and it.get(idslot) is not None:
                    walk(it, cls, it[idslot])
                elif not idslot:
                    src = f"{coll}[{i}]"
                    g.node(src, "record", origin=origin, cls=cls, collection=coll)
                    walk(it, cls, src)
    # the bindings of SWPC-1.1 (B01-B18) as nodes of their own: an estimand is presented by B via its binding record
    for b in cat.get("bindings", []):
        g.node("B:" + b["binding"], "binding", binding=b["binding"])
        g.edge("B:" + b["binding"], "presents", b["id"], DEP)
    # the static calls of the lab's Python (approximate, by names: BND-11)
    for p in sorted(list((ROOT / "lab").glob("*.py")) + list((ROOT / "lab" / "q1").glob("*.py"))):
        for caller, callees in code.calls(_rel(p)).items():
            g.node("code:" + caller, "code", ref=caller)
            for callee in callees:
                g.node("code:" + callee, "code", ref=callee)
                g.edge("code:" + caller, "calls", "code:" + callee, CALLS)
    # the Q1 model digest: every stored issue depends on the code its MODEL hashes (lab/q1/engine.py::model_digest)
    for ref in q1_model_code(code):
        g.node("q1:MODEL", "q1model")
        g.edge("q1:MODEL", "hashes", "code:" + ref, DEP)
    # every stored Q1 issue carries that MODEL in its identity: a change of it makes reproduce() say MODEL_CHANGED
    g.node("q1:STORED-ISSUES", "q1records")
    g.edge("q1:STORED-ISSUES", "made_with", "q1:MODEL", DEP)
    return g, code


def q1_model_code(code):
    """The functions lab/q1/engine.py::model_digest hashes into MODEL (read from its source, never copied)."""
    rel = "lab/q1/engine.py"
    info = code.py(rel)
    if info is None or "model_digest" not in info["funcs"]:
        return []
    fn = info["funcs"]["model_digest"][0]
    alias = {}
    for a, imp in info["imports"].items():
        if imp[0] == "module":
            m = code.lab_module(imp[1])
            if m:
                alias[a] = m
    out = {f"{rel}::Table", f"{rel}::model_digest"}
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "used" for t in node.targets):
            for el in getattr(node.value, "elts", []):
                if isinstance(el, ast.Attribute) and isinstance(el.value, ast.Name) and el.value.id in alias:
                    out.add(f"{alias[el.value.id]}::{el.attr}")
    return sorted(r for r in out if code.exists(r)[0])


# =====================================================================================================================
# the static checks
# =====================================================================================================================
def _result(check, ok, checked, violations=None, details=None):
    return dict(check=check, outcome="PASS" if ok else "FAIL", checked=int(checked), violations=violations or [], details=details or {})


def _viol(code_, refs, message, where, severity="BLOCKING"):
    return dict(code=code_, arch_ref=list(refs), message=message, where=where, severity=severity)


def check_refs(st, g, code):
    """REF-RESOLVE, CODE-REFS, CHECK-REFS, ID-UNIQUE."""
    spec, reg, cat = st["spec"], st["reg"], st["cat"]
    objects = {k: n for k, n in g.nodes.items() if n["kind"] == "object"}
    label_keys = {}
    for f in reg.get("claim_forms", []) + reg.get("fact_forms", []):
        label_keys[f["id"]] = {lb["key"] for lb in f.get("labels") or []}
    rr, cr, kr = [], [], []
    n_ref = n_code = n_check = 0
    for src, slot, x, rng, kind in g.refs:
        where = f"{src}.{slot}"
        if kind == "id":
            n_ref += 1
            n = objects.get(x)
            if n is None:
                rr.append(_viol("UNRESOLVED", ["0.2 §5"], f"{x} does not exist", where))
            elif rng and n["cls"] != rng and n["cls"] not in spec["classes"].get(rng, {}).get("descendants", []):
                rr.append(_viol("WRONG_TYPE", ["0.2 §5"], f"{x} is a {n['cls']}, not a {rng}", where))
        elif kind == "class":
            n_ref += 1
            if x[6:] not in spec["classes"]:
                rr.append(_viol("UNRESOLVED", ["0.2 §5"], f"no schema class {x[6:]}", where))
        elif kind == "enum":
            n_ref += 1
            if x[5:] not in spec["enums"]:
                rr.append(_viol("UNRESOLVED", ["0.2 §5"], f"no schema enum {x[5:]}", where))
        elif kind == "label":
            n_ref += 1
            form, key = x.split("#", 1)
            if key not in label_keys.get(form, set()):
                rr.append(_viol("UNRESOLVED_LABEL", ["0.2 §4"], f"{form} has no registered label {key}", where))
        elif kind == "code":
            n_code += 1
            if not code.exists(x)[0]:
                cr.append(_viol("NO_CODE", ["0.1 §2"], f"code {x} does not exist", where))
        elif kind == "check":
            n_check += 1
            if not check_ref_ok(code, x, spec):
                kr.append(_viol("NO_CHECK", ["0.2 §4"], f"check {x} does not exist", where))
    seen, dup = {}, []
    for origin, data, colls in (("SC", reg, _collections(spec, "Registry")), ("TRACE", cat, _collections(spec, "TraceCatalog"))):
        for coll, cls in colls.items():
            idslot = _idslot(spec, cls)
            for it in data.get(coll, []) or []:
                if isinstance(it, dict) and idslot and it.get(idslot) is not None:
                    key = it[idslot]
                    if key in seen:
                        dup.append(_viol("DUPLICATE_ID", ["0.2 §5"], f"{key} in {seen[key]} and {origin}:{coll}", key))
                    seen[key] = f"{origin}:{coll}"
    return [_result("REF-RESOLVE", not rr, n_ref, rr), _result("CODE-REFS", not cr, n_code, cr),
            _result("CHECK-REFS", not kr, n_check, kr), _result("ID-UNIQUE", not dup, len(seen), dup)]


ROUTE_PROFILE = {"SC11_BASE_24": "PROFILE:BASE-24", "SC11_NOW_1_0": "PROFILE:NOW-1.0", "SC11_PRE_24": "PROFILE:PRE-24", "SC11_ARRIVE_24": "PROFILE:ARRIVE-24"}


def page_verified_estimands(code):
    """The estimands POST /api/d24/verify can recompute (read from lab/contract.py::verify_passports)."""
    src = code.source("lab/contract.py", "verify_passports") or ""
    pref = set(re.findall(r'e\.startswith\("([A-Z:-]+)"\)', src))
    exact = set(re.findall(r'"(EST:[A-Z0-9-]+)"', src))
    return pref, exact


def check_estimands(st, g, code):
    """ESTIMAND-CHAIN, CLAIM-PROFILE, BINDING-COVERAGE."""
    reg, cat = st["reg"], st["cat"]
    ids = {k for k, n in g.nodes.items() if n["kind"] == "object"}
    forms = defaultdict(list)
    for f in reg.get("claim_forms", []):
        forms[f["estimand"]].append(f)
    estr = defaultdict(list)
    for e in reg.get("estimators", []):
        for x in e["estimands"]:
            estr[x].append(e["id"])
    served = defaultdict(list)
    for s in reg.get("surfaces", []):
        for x in s.get("estimands") or []:
            served[x].append(s)
    bound = defaultdict(list)
    for b in cat.get("bindings", []):
        for k in ("estimand", "fact_form"):
            if b.get(k):
                bound[b[k]].append(b["id"])
    standing = {s["sc_profile"] for s in cat.get("standings", []) if s.get("sc_profile")}
    outs = {o["id"]: o for o in reg.get("outcomes", [])}
    pref, exact = page_verified_estimands(code)
    chain, prof, cov = [], [], []
    for e in reg.get("estimands", []):
        eid = e["id"]
        if e["question"] not in ids: chain.append(_viol("NO_QUESTION", ["ENT-16"], f"question {e['question']} missing", eid))
        for cs in e["q4_case_set"]:
            if cs not in ids: chain.append(_viol("NO_CASE_SET", ["ENT-11"], f"case set {cs} missing", eid))
        o = outs.get(e["q5_outcome"])
        if o is None: chain.append(_viol("NO_OUTCOME", ["ENT-21"], f"outcome {e['q5_outcome']} missing", eid))
        elif not code.exists(o["reference_definition"])[0]: chain.append(_viol("NO_REFERENCE", ["R10"], f"reference definition {o['reference_definition']} missing", eid))
        if len(forms[eid]) != 1: chain.append(_viol("CLAIM_FORMS", ["ENT-24"], f"{len(forms[eid])} claim forms (one required)", eid))
        if not estr[eid]: chain.append(_viol("NO_ESTIMATOR", ["ENT-18"], "no estimator", eid))
        on_page = any(eid.startswith(p) for p in pref) or eid in exact
        if not served[eid] and not on_page: chain.append(_viol("NO_ROUTE", ["PROC-16"], "neither a route publishes it nor the page verification recomputes it", eid))
        if not bound[eid]: chain.append(_viol("NO_BINDING", ["ENT-28"], "no presentation binding (SWPC-1.1 §9)", eid))
        if e["profile"] not in standing: chain.append(_viol("NO_STANDING", ["ENT-31"], f"profile {e['profile']} has no standing", eid))
        for f in forms[eid]:
            for cs in e["q4_case_set"]:
                adm = C.admissible_claims(eid, cs)
                if f["claim_class"] not in adm: prof.append(_viol("CLAIM_NOT_ADMISSIBLE", ["R12", "INV-10"], f"{f['id']} {f['claim_class']} not admissible on {cs} ({sorted(adm)})", eid))
            if f["claim_class"] == C.C1 and not f.get("condition_ru") and not all(C.get(cs) and C.get(cs).get("condition_ru") for cs in e["q4_case_set"]):
                prof.append(_viol("C1_WITHOUT_CONDITION", ["INV-10"], f"{f['id']} names no condition", eid))
            if f["claim_class"] in (C.C2, C.C3): prof.append(_viol("C2_C3", ["INV-10", "T18"], f"{f['id']} is {f['claim_class']}", eid))
        for s in served[eid]:
            if ROUTE_PROFILE.get(s["surface_profile"]) != e["profile"]: prof.append(_viol("ROUTE_PROFILE", ["PROC-16"], f"{s['id']} serves profile {s['surface_profile']}, the estimand is {e['profile']}", eid))
    for f in reg.get("fact_forms", []):
        if not bound[f["id"]]: cov.append(_viol("NO_BINDING", ["ENT-28"], "fact form without a presentation binding", f["id"]))
    for b in cat.get("bindings", []):
        if b["binding_class"] == "StatisticalPresentationBinding" and b.get("claim_form") != (forms[b["estimand"]][0]["id"] if forms[b["estimand"]] else None):
            cov.append(_viol("BINDING_FORM", ["ENT-28"], f"claim form {b.get('claim_form')} is not the estimand's", b["id"]))
    n = len(reg.get("estimands", []))
    return [_result("ESTIMAND-CHAIN", not chain, n, chain), _result("CLAIM-PROFILE", not prof, n, prof),
            _result("BINDING-COVERAGE", not cov, n + len(reg.get("fact_forms", [])), cov)]


def check_standing(st):
    """STANDING: the decision axis comes from sources; a registry status that reads stronger than the decision must be a
    registered boundary (BND-02), never silent."""
    reg, cat = st["reg"], st["cat"]
    srcs = {s["id"]: s for s in reg.get("source_references", []) + cat.get("source_references", [])}
    by_profile = defaultdict(list)
    for s in cat.get("standings", []):
        by_profile[s.get("sc_profile") or s["profile_key"]].append(s)
    bounds = {b["id"]: b for b in cat.get("boundaries", [])}
    v, details = [], dict(conflicts=[])
    for p in reg.get("profiles", []):
        ss = by_profile.get(p["id"], [])
        if len(ss) != 1:
            v.append(_viol("STANDING_COUNT", ["ENT-31"], f"{len(ss)} standings for {p['id']}", p["id"]))
            continue
        s = ss[0]
        if s["decision"] == "ACCEPTED" and not any(srcs.get(x, {}).get("grounds") == "OPERATOR_REQUIREMENT" for x in s["decision_sources"]):
            v.append(_viol("ACCEPTED_WITHOUT_OPERATOR", ["0.1 §0"], "an ACCEPTED decision without an operator-grounded source", s["id"]))
        if s["decision"] != "ACCEPTED" and p["profile_status"] in ("ACTIVE", "FROZEN"):
            reg_b = [b for b in bounds.values() if b["boundary_kind"] == "FINDING" and p["id"] in b["affects"]]
            details["conflicts"].append(dict(profile=p["id"], registry_status=p["profile_status"], decision=s["decision"], boundary=reg_b[0]["id"] if reg_b else None))
            if not reg_b:
                v.append(_viol("STATUS_CONFLATION", ["0.1 §0", "0.2 §1"], f"registry status {p['profile_status']} reads stronger than the decision {s['decision']} and no boundary names it", p["id"]))
    if "Q1-PILOT-0.2" not in by_profile:
        v.append(_viol("STANDING_COUNT", ["ENT-31"], "the Q1 pilot has no standing", "Q1-PILOT-0.2"))
    return _result("STANDING", not v, len(reg.get("profiles", [])) + 1, v, details)


def git(*args, binary=False):
    try:
        r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, timeout=60)
        if r.returncode != 0:
            return None
        return r.stdout if binary else r.stdout.decode("utf-8", errors="replace").strip()
    except Exception:
        return None


def check_edition(st):
    """EDITION-ADDITIVE: the accepted text (from git, by its commit) against the text this line pins."""
    cat, reg = st["cat"], st["reg"]
    ed = next(iter(cat.get("editions", [])), None)
    if ed is None:
        return _result("EDITION-ADDITIVE", False, 0, [_viol("NO_EDITION_STANDING", ["0.1 §0"], "no EditionStanding", "editions")])
    sc = next((e for e in reg.get("editions", []) if e["id"] == ed["edition"]), None)
    path = sc["document_path"]
    now = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
    pinned, file_sha = sc["document_sha256_lf"], hashlib.sha256(now).hexdigest()
    det = dict(edition=ed["edition"], accepted_sha256=ed["accepted_text_sha256_lf"], pinned_sha256=pinned, file_sha256=file_sha)
    if file_sha != pinned:
        return _result("EDITION-ADDITIVE", False, 1, [_viol("PIN_MISMATCH", ["INV-12"], "the document differs from the registry's pin", path)], det)
    if pinned == ed["accepted_text_sha256_lf"]:
        det["state"] = "the line pins the accepted text"
        return _result("EDITION-ADDITIVE", True, 1, [], det)
    old = git("show", f"{ed['accepted_text_commit']}:{path}", binary=True)
    if old is None:
        return _result("EDITION-ADDITIVE", False, 1, [_viol("ACCEPTED_TEXT_UNREADABLE", ["INV-12"], "the accepted text is not readable from git", ed["accepted_text_commit"])], det)
    old = old.replace(b"\r\n", b"\n")
    if hashlib.sha256(old).hexdigest() != ed["accepted_text_sha256_lf"]:
        return _result("EDITION-ADDITIVE", False, 1, [_viol("ACCEPTED_TEXT_HASH", ["INV-12"], "the accepted commit holds another text than the accepted hash", ed["accepted_text_commit"])], det)
    a, b = old.decode("utf-8").split("\n"), now.decode("utf-8").split("\n")
    bad, extended, added = [], 0, 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if op == "insert":
            added += j2 - j1
        elif op in ("replace", "delete"):
            new = b[j1:j2]
            for line in a[i1:i2]:
                if any(n.rstrip().startswith(line.rstrip()) for n in new):
                    extended += 1
                else:
                    bad.append(line[:120])
            added += max(0, (j2 - j1) - (i2 - i1))
    det.update(state="the line pins an amended text (a proposal, not the accepted one)", accepted_lines_extended=extended, lines_added=added, accepted_lines_removed_or_rewritten=len(bad))
    v = [_viol("AMENDMENT_NOT_ADDITIVE", ["INV-12", "0.1 §0"], f"an accepted line is removed or rewritten: {x}", path) for x in bad[:10]]
    return _result("EDITION-ADDITIVE", not bad, len(a), v, det)


ARCH_PATTERNS = {"ENT": r"^\| (ENT-\d\d) ", "R": r"^\| (R\d\d) \|", "INV": r"\*\*(INV-\d\d) —", "PROC": r"^\| (PROC-\d\d) ",
                 "T": r"^\| (T\d\d) ", "A": r"^\| (A\d\d)\. ", "GAP": r"^\| (GAP-\d\d) "}


def arch_ids():
    text = ARCH_DOC.read_text(encoding="utf-8")
    out = set()
    for pat in ARCH_PATTERNS.values():
        out |= set(re.findall(pat, text, flags=re.M))
    return out


def check_coverage(st):
    """CATALOG-COVERAGE: 0.1's ids against the catalog, both ways."""
    cat = st["cat"]
    want = arch_ids()
    have = {e["id"] for e in cat.get("entries", [])} | {b["id"] for b in cat.get("boundaries", [])}
    missing = sorted(want - have)
    invented = sorted(x for x in have - want if not x.startswith("BND-"))
    v = [_viol("NOT_COVERED", ["0.1 §16"], "an entry of 0.1 without its catalog record", x) for x in missing]
    v += [_viol("NOT_IN_0.1", ["0.1 §16"], "a catalog record with an id 0.1 does not have", x) for x in invented]
    return _result("CATALOG-COVERAGE", not v, len(want), v, dict(arch_ids=len(want), entries=len(cat.get("entries", [])), boundaries=len(cat.get("boundaries", []))))


def static_checks(st, g=None, code=None):
    if g is None:
        g, code = build_graph(st, code)
    out = check_refs(st, g, code) + check_estimands(st, g, code) + [check_standing(st), check_edition(st), check_coverage(st)]
    return out, g, code


# =====================================================================================================================
# computing a declared scene: the very calls of the routes of lab/server.py, through the SC-1.1 gate
# =====================================================================================================================
def scenes(st):
    return {s["id"]: s for s in st["cat"].get("scenes", [])}


def compute(scene):
    """The response of the scene's route as the page asks for it (the parameters of design/sozvezdiya-24/src/app.js)."""
    import arrive24
    import now24
    import scene24
    inst, blk, date, at = scene["instrument"], scene["block"], scene["trading_date"], minute(scene["at_clock_et"])
    allw = scene["scope"] == "ALL_WEEKDAYS"
    route = scene["route"].split(":", 1)[1]
    if route == "/api/d24/family":
        body = scene24.family(inst, blk, at, date, "conf" + (":all" if allw else ""))
    elif route == "/api/d24/now":
        body = now24.live(inst, blk, at, date, "conf" + (":all" if allw else ""))
    elif route == "/api/d24/arrive":
        body = arrive24.arrive(inst, blk, at, date, "all" if allw else "weekday")
    else:
        raise ValueError(f"route {route} is outside the declared area")
    return C.finalize(route, body)


def compute_raw(scene):
    """The production computation of the scene's route BEFORE the SC-1.1 gate — what the gate then verifies and may
    withhold. The checks of the future compare this (a withheld answer would otherwise hide a dependence), and the gate's
    verdict separately. For NOW the selection masks are read the way now24.payload builds them."""
    import arrive24
    import now24
    import scene24
    inst, blk, date, at = scene["instrument"], scene["block"], scene["trading_date"], minute(scene["at_clock_et"])
    allw = scene["scope"] == "ALL_WEEKDAYS"
    route = scene["route"].split(":", 1)[1]
    if route == "/api/d24/family":
        out, _, _ = scene24._family(inst, blk, at, date, "conf" + (":all" if allw else ""))
        return dict(route=route, out=out)
    if route == "/api/d24/arrive":
        out, fam, _, _ = arrive24._arrive(inst, blk, at, date, "all" if allw else "weekday")
        return dict(route=route, out=out, family_id=(fam or {}).get("family_id"))
    fam = scene24.family(inst, blk, at, date, "conf" + (":all" if allw else ""))
    if fam.get("status") != "ok" or "today" not in fam or not fam.get("N"):          # the guard of now24.live
        return dict(route=route, out=dict(status="NO_FAMILY", family_status=fam.get("status")), family_id=fam.get("family_id"), selection={})
    day = scene24.day_view(inst, date)
    tick = float(day.get("tick") or 0.25)
    pay = now24.payload(fam, day["bars"], tick)
    sel = {}
    if pay.get("status") in ("OK", "FROZEN_AT_BREAK"):
        today, grid, formed = fam["today"], fam["grid"], fam["schedule"]["formed"]
        d = today["side"] if fam["view"] == "conf" else -today["side"]
        act = today["c0"] if fam["view"] == "conf" else today["brk"]
        cut = pay["cut"]["cut"]
        c, a_t = (cut - formed - 5) // 5, (act - formed - 5) // 5
        T = now24.series(now24.today_path(day["bars"], grid, tick, d, today["idrH"] if d == 1 else today["idrL"], cut), a_t, None)
        S, w, a_mem = now24._member_series(fam)
        Mk = now24.masks(S, w, a_mem, T, int(round((today["idrH"] - today["idrL"]) / tick)), a_t, [c], tuple(now24.RULES["tol"]))
        ids = [m["id"] for m in fam["members"]]
        sel = {k: sorted(i for i, x in zip(ids, v[:, 0]) if x) for k, v in Mk.items() if hasattr(v, "shape") and v.ndim == 2 and v.shape[0] == len(ids)}
    return dict(route=route, out=pay, family_id=fam.get("family_id"), selection=sel)


def raw_membership(raw):
    """Who the production computation selected (never what happened to them)."""
    out, route = raw["out"], raw["route"]
    if route.endswith("/family"):
        return dict(family_id=out.get("family_id"), ids=out.get("ids"), N=out.get("N"), journal=out.get("journal"))
    if route.endswith("/now"):
        return dict(family_id=raw.get("family_id"), selection=raw.get("selection"),
                    eligible={ev: ((out.get(ev) or {}).get("baseline") or {}).get("support", {}).get("N_match_total") for ev in ("R", "X")})
    return dict(family_id=raw.get("family_id"), N_parent=out.get("N_parent"),
                places=[dict(level=p["level"], state=(p.get("state") or {}).get("status"), members=sorted(x[0] for x in p.get("members") or []),
                             chain=[(p.get("counts") or {}).get(k) for k in ("N_parent", "N_eligible", "N_not_yet", "n_match")]) for p in out.get("places") or []])


def raw_labels(raw):
    """What happened to the selected after the cut, as the production computation counted it."""
    out, route = raw["out"], raw["route"]
    if route.endswith("/family"):
        return dict(snapshot_id=out.get("snapshot_id"), counts=out.get("counts"))
    if route.endswith("/now"):
        return {ev: ((out.get(ev) or {}).get("baseline") or {}).get("support") for ev in ("R", "X")}
    return [(p["level"], sorted(map(tuple, p.get("members") or []))) for p in out.get("places") or []]


def family_of(scene):
    import scene24
    allw = scene["scope"] == "ALL_WEEKDAYS"
    fam = scene24.family(scene["instrument"], scene["block"], minute(scene["at_clock_et"]), scene["trading_date"], "conf" + (":all" if allw else ""))
    day = scene24.day_view(scene["instrument"], scene["trading_date"])
    return fam, day["bars"], float(day.get("tick") or 0.25)


def params_of(b):
    try:
        return json.loads(b.get("parameters") or "{}")
    except ValueError:
        return {}


def pick_bundle(body, estimand, selector):
    sel = json.loads(selector) if isinstance(selector, str) else (selector or {})
    hits = [b for b in (body.get("contract") or {}).get("bundles") or [] if b["estimand"] == estimand and all(params_of(b).get(k) == v for k, v in sel.items())]
    return hits[0] if len(hits) == 1 else None


def norm_bundle(b, cross_line=False):
    """A bundle without what changes from request to request (ids, the clock); cross_line also drops the versions of the
    registry and the code (they differ between lines by construction) — the numbers and the claim stay."""
    d = {k: v for k, v in (b.get("derivation") or {}).items() if k not in ("derivation_id", "executed_at_utc")}
    if cross_line:
        d["inputs"] = [i for i in d.get("inputs", []) if i["input_kind"] not in ("REGISTRY", "CODE")]
    return canon(dict(estimand=b["estimand"], claim_form=b["claim_form"], parameters=params_of(b), derivation=d,
                      estimates=[{k: v for k, v in e.items() if k != "estimate_id"} for e in b["estimates"]],
                      supports=[{k: v for k, v in s.items() if k != "support_id"} for s in b["supports"]],
                      admissible_claims=b.get("admissible_claims"), claim=b.get("claim"), validations=b.get("validations")))


def computed_fields(route, body):
    """What a response computed besides its bundles (for the replaced-future comparisons): the production numbers."""
    if route.endswith("/arrive"):
        return dict(status=body.get("status"), places=[dict(level=p["level"], state=p.get("state"), publication=p.get("publication"), counts=p.get("counts"),
                                                            members=sorted(map(tuple, p.get("members") or [])), withheld=p.get("withheld")) for p in body.get("places") or []])
    if route.endswith("/now"):
        return dict(status=body.get("status"), R=body.get("R"), X=body.get("X"), base=body.get("base"))
    return dict(status=body.get("status"), N=body.get("N"), ids=body.get("ids"), counts=body.get("counts"), family_id=body.get("family_id"),
                snapshot_id=body.get("snapshot_id"), zones={ev: [(z["zone_id"], z["n_zone"], sorted(z["member_session_ids"])) for z in zm["zones"]] for ev, zm in (body.get("zones") or {}).items()},
                today_zones=(body.get("today") or {}).get("zones"))


def outcome_of(route, body):
    """The normalized bundles of a response with the computed fields: the object the replaced-future checks compare."""
    env = body.get("contract") or {}
    return dict(bundles=sorted((norm_bundle(b) for b in env.get("bundles") or []), key=digest), computed=canon(computed_fields(route, body)),
                status=env.get("status"), violations=[v["code"] for v in env.get("violations") or []])


# =====================================================================================================================
# the future replaced in memory (the market base is never written)
# =====================================================================================================================
def _clear_caches():
    import arrive24
    import now24
    import scene21
    import scene24
    scene24._SNAP.clear()
    scene24._MISSING.clear()
    scene21._CACHE.clear()
    C._DERIVED.clear()
    C._VER.clear()
    C._ZV.clear()
    arrive24._TBL.clear()
    now24._SER.clear()
    try:
        from q1 import engine as Q
        Q._TABLES.clear()
    except Exception:
        pass


def _sid_parts(sid):
    inst, d, block = sid.split("-")
    return inst, f"{d[:4]}-{d[4:6]}-{d[6:]}", block


def mutate_future_ohlc(bars, lo, hi, shift, after, width_ticks):
    """Perturb ALL OHLC on observed M5 closing strictly after the allowed cut, never the prefix.

    Use plausible candles (low <= open/close <= high) but deliberately extreme future prices.
    Leaving open/close unchanged would let a selector leaking future closes pass FUTURE-MEMBERS.
    The caller passes an in-memory COPY; this function never opens or writes a market file.
    """
    if width_ticks <= 0:
        raise ValueError("a positive IDR width is required for future mutation")
    changed = 0
    for r in range(lo, hi):
        if int(bars[r, 0]) - shift <= after:
            continue
        high, low = int(bars[r, 2]), int(bars[r, 3])
        low2, high2 = low - 4 * width_ticks, high + 4 * width_ticks
        bars[r, 1:5] = (low2, high2, low2, high2)
        changed += 1
    return changed


def rederive_future_attributes(inst, B, bars, touched):
    """The base stores one attribute derived from a session's own future: its DR break (`fail`, lab/build_boxes.py; the
    box levels, the confirmation, its side and `complete` come from the prefix or from which M5 exist). A replaced future
    must carry its own break, or the base contradicts itself: the gate re-derives the break from the candles and withholds
    the family (BASE_DERIVATION), and a computation reading the stored break would never see the replacement. The break
    is re-derived by the gate's reference (lab/contract.py::derive_base); every attribute of the prefix must come out as
    stored, or the replacement reached the prefix. touched: {box index: block}. Returns (boxes, breaks changed)."""
    boxes, moved = list(B["boxes"]), 0
    B1 = dict(B, bars=bars)
    for block in sorted(set(touched.values())):
        der, shift = C.derive_base(inst, B1, block), C._blocks()[block]["history_minute_shift"]
        for i in (i for i, b in touched.items() if b == block):
            d, m = der[i], B["boxes"][i]
            sc = None if m["conf"] is None else int(m["conf"]) - shift
            same = "box_error" not in d and all(d[k] == m[k] for k in ("dr_high", "dr_low", "idr_high", "idr_low")) \
                and (sc, m["side"] if sc is not None else None) == (d["conf"], d["side"])
            if not same:
                raise ValueError(f"the replaced future reached the prefix of {m['date']} {block}: box or confirmation changed")
            fail = None if d["fail"] is None else int(d["fail"]) + shift
            if fail != m["fail"]:
                boxes[i], moved = dict(m, fail=fail), moved + 1
    return boxes, moved


@contextmanager
def replaced_future(inst, plans):
    """plans: [(trading date, block, after_minute, 'full')].

    For target AND analogue futures, change all four OHLC after the cut. Keep the original
    M5 close-minute clock and every prefix candle byte-identical. Any weaker 'wicks' mode
    is forbidden: it cannot falsify selection depending on a future open or close.
    The stored attribute derived from the future (the DR break) is re-derived from the replaced candles, so the base in
    memory stays one consistent history (rederive_future_attributes).
    Only a temporary copy is changed, with caches invalidated before/after the test.
    Yields dict(m5=replaced M5, fields=the OHLC fields changed on every replaced M5, breaks=stored breaks that changed).
    """
    import numpy as np
    import scene21
    import scene24
    B = scene21._boxes(inst)
    bars = B["bars"].copy()
    changed, touched, rows = 0, {}, []
    for date, block, after, mode in plans:
        if mode != "full":
            raise ValueError("future mutation must replace all four OHLC fields")
        i = B["idx"].get((date, block))
        if i is None:
            continue
        box = B["boxes"][i]
        w = int(box["idr_high"] - box["idr_low"]) or 1
        lo, hi = int(B["off"][i]), int(B["off"][i + 1])
        before = bars[lo:hi].copy()
        n = mutate_future_ohlc(bars, lo, hi, scene24.SHIFT[block], after, w)
        if n:
            touched[i] = block
            rows += [lo + r for r in np.flatnonzero((bars[lo:hi] != before).any(axis=1))]
        changed += n
    rows = np.asarray(rows, dtype=np.int64)
    fields = "".join(f for k, f in enumerate("OHLC", 1) if rows.size and bool(np.all(bars[rows, k] != B["bars"][rows, k])))
    _clear_caches()          # before the re-derivation: the reference's cache is keyed by the id() of the candle array
    boxes, breaks = rederive_future_attributes(inst, B, bars, touched)
    B2 = dict(B, bars=bars, boxes=boxes)
    saved = scene21._B.get(inst)
    scene21._B[inst] = B2
    try:
        yield dict(m5=changed, fields=fields, breaks=breaks)
    finally:
        scene21._B[inst] = saved
        _clear_caches()


def target_plan(scene):
    return [(scene["trading_date"], scene["block"], minute(scene["at_clock_et"]), "full")]


def member_plan(scene, fam):
    """Every member of the family, from the start of what the profile treats as its future: a base family is fixed at
    each member's own activation (BASE-24: after it, everything is a label); a selection at a common cut sees each
    member's prefix up to the cut (NOW, «Отсюда»: after the cut and after its own activation)."""
    route = scene["route"].split(":", 1)[1]
    cut = -10 ** 6 if route.endswith("/family") else minute(scene["at_clock_et"])
    out = []
    for m in fam.get("members") or []:
        _, date, block = _sid_parts(m["id"])
        out.append((date, block, max(int(m["act"]), cut), "full"))
    return out


def membership_of(route, body, scene, fam_bars=None):
    """Who was selected (never what happened to them): the family's members, the NOW eligible set at the cut (by the
    reference C.ref_now_sets), the matched sessions of every place of «Отсюда»."""
    if route.endswith("/family"):
        return dict(family_id=body.get("family_id"), ids=body.get("ids"), N=body.get("N"), journal=body.get("journal"))
    if route.endswith("/now"):
        fam, bars, tick = fam_bars or family_of(scene)
        if fam.get("status") != "ok" or "cut" not in body:
            return dict(status=body.get("status"))
        ref = C.ref_now_sets(fam, bars, tick, body["cut"]["cut"])
        return dict(family_id=fam.get("family_id"), N=fam.get("N"), eligible=sorted(r["id"] for r in ref["rows"]),
                    m1=sorted(r["id"] for r in ref["rows"] if r["match"].get("M1R")), m2=sorted(r["id"] for r in ref["rows"] if r["match"].get("M2")))
    return dict(family_id=body.get("family_id"), N_parent=body.get("N_parent"),
                places=[dict(level=p["level"], state=(p.get("state") or {}).get("status"), members=sorted(x[0] for x in p.get("members") or []),
                             chain=[(p.get("counts") or {}).get(k) for k in ("N_parent", "N_eligible", "N_not_yet", "n_match")]) for p in body.get("places") or []])


def check_future_target(scene, base_body=None):
    """FUTURE-TARGET: the target day's candles after the cut replaced in memory; neither the production computation
    (before the gate) nor the answer the gate lets out may change in anything."""
    route = scene["route"].split(":", 1)[1]
    _clear_caches()
    r0 = canon(computed_fields(route, compute_raw(scene)["out"]))
    _clear_caches()
    b0 = base_body or compute(scene)
    o0 = outcome_of(route, b0)
    with replaced_future(scene["instrument"], target_plan(scene)) as rep:
        n = rep["m5"]
        r1 = canon(computed_fields(route, compute_raw(scene)["out"]))
        _clear_caches()
        o1 = outcome_of(route, compute(scene))
    same = o0 == o1 and r0 == r1
    v = []
    if r0 != r1:
        v.append(_viol("FUTURE_DEPENDENCE", ["INV-03", "R07", "A07", "A08"], "the production computation changed when only the target's candles after the cut changed", f"{scene['id']}:{route} (before the gate)"))
    if o0 != o1:
        v.append(_viol("FUTURE_DEPENDENCE", ["INV-03", "R07", "A07", "A08"], "the published answer changed when only the target's candles after the cut changed", f"{scene['id']}:{route} (after the gate)"))
    if n == 0:
        v.append(_viol("NO_MUTATION", ["INV-03"], "nothing after the cut to replace on this day", scene["id"], "WARNING"))
    return _result("FUTURE-TARGET", same and n > 0, n, v, dict(replaced_m5=n, mutated_fields=rep["fields"], breaks_rederived=rep["breaks"],
                                                               gate_status=[o0["status"], o1["status"]]))


def check_future_members(scene, base_body=None):
    """FUTURE-MEMBERS: the analogues' candles after the cut (and their own activation) replaced; who was selected must not
    change; what happened to them may (a check without that change would have no teeth)."""
    route = scene["route"].split(":", 1)[1]
    _clear_caches()
    raw0 = compute_raw(scene)
    b0 = base_body or compute(scene)
    fb0 = family_of(scene)
    m0, l0, ref0 = raw_membership(raw0), raw_labels(raw0), membership_of(route, b0, scene, fb0)
    plan = member_plan(scene, fb0[0])
    with replaced_future(scene["instrument"], plan) as rep:
        n = rep["m5"]
        raw1 = compute_raw(scene)
        _clear_caches()
        b1 = compute(scene)
        fb1 = family_of(scene)
        m1, l1, ref1 = raw_membership(raw1), raw_labels(raw1), membership_of(route, b1, scene, fb1)
    same = m0 == m1 and ref0 == ref1
    moved = l0 != l1
    v = []
    if m0 != m1:
        v.append(_viol("SELECTION_USES_FUTURE", ["INV-03", "R09", "A09"], "the production selection changed when only the analogues' futures changed", f"{scene['id']}:{route} (before the gate)"))
    if ref0 != ref1:
        v.append(_viol("SELECTION_USES_FUTURE", ["INV-03", "R09", "A09"], "the selection of the published answer changed when only the analogues' futures changed", f"{scene['id']}:{route} (after the gate)"))
    if not moved:
        v.append(_viol("NO_TEETH", ["INV-03"], "the replaced futures changed no label: the check proves nothing here", scene["id"], "WARNING"))
    return _result("FUTURE-MEMBERS", same and moved and n > 0, n, v, dict(replaced_m5=n, sessions=len(plan), labels_changed=moved,
                                                                          mutated_fields=rep["fields"], breaks_rederived=rep["breaks"]))


# =====================================================================================================================
# checks of one published bundle
# =====================================================================================================================
def check_gate(body, bundle):
    env = body.get("contract") or {}
    v = []
    if env.get("status") != "CONFORMANT":
        v.append(_viol("GATE_STATUS", ["PROC-14"], f"envelope status {env.get('status')}: " + "; ".join(x["message"] for x in env.get("violations") or [])[:300], env.get("route", "?")))
    for c in env.get("checks") or []:
        if c["outcome"] != "PASS":
            v.append(_viol("GATE_CHECK", ["PROC-14"], f"gate check failed: {c['check']}", env.get("route", "?")))
    errs = C.validate(env, "ContractEnvelope") if env else ["no envelope"]
    if errs:
        v.append(_viol("ENVELOPE_STRUCTURE", ["ENT-32"], "; ".join(errs[:3]), env.get("route", "?")))
    if bundle is not None and (bundle.get("derivation") or {}).get("verification") != "VERIFIED_BY_REFERENCE":
        v.append(_viol("NOT_VERIFIED_BY_REFERENCE", ["R11"], f"verification {bundle['derivation'].get('verification')}", bundle["id"]))
    return _result("GATE-CONFORMANT", not v, len(env.get("checks") or []), v)


CS_ROLE_OK = {"PROFILE:BASE-24": {"BASE_FAMILY"}, "PROFILE:NOW-1.0": {"ELIGIBLE_AT_CUT", "MATCHED_AT_CUT", "OUTCOME_SUBGROUP"},
              "PROFILE:ARRIVE-24": {"MATCHED_AT_CUT"}}


def bundle_case_set(st, body, bundle):
    """The case-set rule a bundle's claim is admitted on (the spec of its snapshot for C0, the selected set for C1)."""
    cl = bundle.get("claim") or {}
    if cl.get("claim_class") == C.C1:
        return cl.get("selected_case_set")
    env = body.get("contract") or {}
    snaps = {c["snapshot_id"]: c["spec"] for c in env.get("case_sets") or []}
    return snaps.get(cl.get("case_set_snapshot"))


def check_bundle_claim(st, route, body, bundle):
    """BUNDLE-CLAIM: estimand registered and served by this route, its one claim form, the class admissible on the case
    set the bundle names, the role of that set right for the profile, the envelope's profile the estimand's."""
    reg = st["reg"]
    v = []
    est = C.get(bundle["estimand"])
    form = C.claim_form_of(bundle["estimand"])
    where = f"bundle {bundle.get('id')} {bundle['estimand']}"
    if est is None:
        return _result("BUNDLE-CLAIM", False, 1, [_viol("UNREGISTERED", ["ENT-16"], "estimand not in the registry", where)])
    surf = C.surface_of(route) or {}
    if bundle["estimand"] not in (surf.get("estimands") or []):
        v.append(_viol("NOT_SERVED", ["PROC-16"], f"{route} does not declare this estimand", where))
    if form is None or bundle["claim_form"] != form["id"]:
        v.append(_viol("WRONG_FORM", ["ENT-24", "R12"], f"claim form {bundle['claim_form']} is not the registry's {form and form['id']}", where))
    cl = bundle.get("claim") or {}
    if form is not None and cl.get("claim_class") != form["claim_class"]:
        v.append(_viol("WRONG_CLASS", ["R12", "INV-10"], f"claim class {cl.get('claim_class')} is not the form's {form['claim_class']}", where))
    cs = bundle_case_set(st, body, bundle)
    if cs is None or cs not in est["q4_case_set"]:
        v.append(_viol("WRONG_CASE_SET", ["R12", "INV-05"], f"case set {cs} is not one the estimand is defined on", where))
    else:
        adm = C.admissible_claims(bundle["estimand"], cs)
        if cl.get("claim_class") not in adm:
            v.append(_viol("CLAIM_NOT_ADMISSIBLE", ["R12", "INV-10"], f"{cl.get('claim_class')} not admissible on {cs} ({sorted(adm)})", where))
        if sorted(bundle.get("admissible_claims") or []) != sorted(adm):
            v.append(_viol("ADMISSIBLE_SET", ["R12"], "the bundle's admissible classes are not the registry's", where))
        role = (C.get(cs) or {}).get("role")
        if role not in CS_ROLE_OK.get(est["profile"], {role}):
            v.append(_viol("WRONG_PROFILE", ["R12", "INV-05"], f"a {role} set for a {est['profile']} claim", where))
    env = body.get("contract") or {}
    if env.get("profile") != est["profile"]:
        v.append(_viol("WRONG_PROFILE", ["R12"], f"the envelope's profile {env.get('profile')} is not the estimand's {est['profile']}", where))
    return _result("BUNDLE-CLAIM", not v, 1, v)


def _members_digest(pairs):
    return digest(sorted([list(p) for p in pairs]))


def check_bundle_counts(scene, body, bundle):
    """BUNDLE-COUNTS: the bundle's estimates and supports agree with each other and with a recount of the response's own
    case records by the reference definitions (lab/contract.py); returns the recount (aggregates and a digest of the
    labelled members, never the members themselves)."""
    route = scene["route"].split(":", 1)[1]
    est = bundle["estimand"]
    E = {e["value_kind"]: e for e in bundle["estimates"]}
    S = bundle["supports"][0] if bundle["supports"] else {}
    comp = (S.get("components") or [{}])[0]
    where = f"bundle {bundle.get('id')} {est}"
    v, rec = [], {}

    def need(cond, msg, refs=("INV-05", "R11")):
        if not cond:
            v.append(_viol("COUNTS", list(refs), msg, where))

    if est.startswith("EST:B-ZONE-") and not est.startswith("EST:B-ZONE-RESIDUAL"):
        ev = est[-1]
        p = params_of(bundle)
        zm = (body.get("zones") or {}).get(ev) or {"zones": []}
        z = next((z for z in zm["zones"] if z["zone_id"] == p.get("zone_id")), None)
        N = body.get("N")
        need(z is not None, "the bundle's zone is not in the response")
        if z is not None:
            # the recount: every member's final point by the reference definition, in the zone's exact mask
            mask = {tuple(c) for c in z["cell_mask"]}
            formed, end, grid = body["schedule"]["formed"], body["schedule"]["end"], body["grid"]
            inside, unknown, none, pairs = 0, 0, 0, []
            for m in body["members"]:
                x = C.ref_final_extreme(m["path"], grid, m["act"], end, ev)
                if x["s"] == "known":
                    cell = (C.ref_cell(x["v"], m["w"]), (x["t"] - formed) // 15)
                    hit = cell in mask
                    inside += hit
                    pairs.append((m["id"], "IN" if hit else "OUT"))
                elif x["s"] == "unknown":
                    unknown += 1
                    pairs.append((m["id"], "UNKNOWN"))
                else:
                    none += 1
                    pairs.append((m["id"], "NO_PERIOD"))
            P = E.get("POINT", {})
            need(len(body["members"]) == N == len(body.get("ids") or []), "N is not the number of members")
            need(z["n_zone"] == len(z["member_session_ids"]) == inside, f"n_zone {z['n_zone']} vs members {len(z['member_session_ids'])} vs recount {inside}")
            need((P.get("numerator"), P.get("denominator")) == (inside, N), f"estimate {P.get('numerator')}/{P.get('denominator')} vs recount {inside}/{N}")
            need(abs(P.get("value", -1) - inside / N) < 1e-12 if N else P.get("value_kind") == "NO_ESTIMATE", "the share is not n / N")
            need((S.get("n_base"), comp.get("of"), comp.get("yes"), comp.get("unknown"), comp.get("no_period")) == (N, N, inside, unknown, none), "the support is not the recount")
            need(sum(zz["n_zone"] for zz in zm["zones"]) + zm["n_residual_total"] + unknown + none == N, "zones + residual + unknown + no period != N")
            rec = dict(N=N, yes=inside, unknown=unknown, no_period=none, members_digest=_members_digest(pairs))
    elif est.startswith("EST:N-NEW-"):
        ev = est[-1]
        fam, bars, tick = family_of(scene)
        ref = C.ref_now_sets(fam, bars, tick, body["cut"]["cut"])
        role = params_of(bundle).get("set", "B0")
        keep = C._SETS[role][1](ev)
        r = C.ref_forecast(ref["rows"], ev, keep)
        P, Bd = E.get("POINT", {}), E.get("BOUNDS", {})
        known = r["yes"] + r["no"]
        need((comp.get("of"), comp.get("yes"), comp.get("no"), comp.get("unknown")) == (r["total"], r["yes"], r["no"], r["unknown"]), f"support {comp} vs recount yes {r['yes']} no {r['no']} unknown {r['unknown']} of {r['total']}")
        need(S.get("n_match") == r["total"] and S.get("n_base") == fam["N"], "n_match / n_base vs recount")
        need(S.get("n_eligible") == len(ref["rows"]), "n_eligible vs the eligible set at the cut")
        if known:
            need((P.get("numerator"), P.get("denominator")) == (r["yes"], known), "point is not yes among known")
            need(abs(P["value"] - r["yes"] / known) <= 5.0001e-5, "point value")
        lo, hi = C.est_binary_bounds(r["yes"], r["no"], r["unknown"])
        need(Bd.get("denominator") == r["total"] and abs(Bd.get("lower", -1) - float(lo)) < 1e-12 and abs(Bd.get("upper", -1) - float(hi)) < 1e-12, "bounds are not [yes/D, (yes+unknown)/D]")
        pairs = [(row["id"], row["res"][ev]["new"]) for row in ref["rows"] if keep(row)]
        rec = dict(N=fam["N"], eligible=len(ref["rows"]), D=r["total"], yes=r["yes"], no=r["no"], unknown=r["unknown"], members_digest=_members_digest(pairs))
    elif est == "EST:K-ARRIVE":
        lvl = params_of(bundle).get("level")
        place = next((p for p in body.get("places") or [] if p["level"] == lvl), None)
        need(place is not None, "the bundle's place is not in the response")
        if place is not None:
            fam, bars, tick = family_of(scene)
            a, b = C.ARRIVE_LEVELS[lvl]
            ref = C.ref_arrive(fam, bars, tick, body["cut"]["cut"], a, b)
            k = place["counts"]
            yes = sum(1 for _, x in ref["matched"] if x == "YES")
            unk = sum(1 for _, x in ref["matched"] if x == "UNKNOWN")
            n = len(ref["matched"])
            need(sorted(map(tuple, place.get("members") or [])) == sorted(map(tuple, ref["matched"])), "the response's members and labels are not the reference's")
            got = sorted(map(tuple, place.get("members") or []))
            need((sum(1 for _, x in got if x == "YES"), sum(1 for _, x in got if x == "NO"), sum(1 for _, x in got if x == "UNKNOWN")) == (k["yes"], k["no"], k["unknown"]), "the counts are not a count of the members' labels")
            need((k["N_parent"], k["N_eligible"], k["N_not_yet"], k["n_match"]) == (fam["N"], ref["eligible"], ref["notyet"], n), "the selection chain is not the reference's")
            need(k["N_parent"] >= k["N_eligible"] >= k["N_not_yet"] >= k["n_match"], "the selection chain is not monotone")
            need(k["n_match"] == k["yes"] + k["no"] + k["unknown"] and k["n_known"] == k["yes"] + k["no"], "n != yes + no + unknown or n_known != yes + no")
            P, Bd = E.get("POINT", {}), E.get("BOUNDS", {})
            if k["n_known"]:
                need((P.get("numerator"), P.get("denominator")) == (k["yes"], k["n_known"]), "point is not yes among known")
            need(Bd.get("denominator") == k["n_match"] and abs(Bd.get("lower", -1) - k["yes"] / k["n_match"]) < 1e-12 and abs(Bd.get("upper", -1) - (k["yes"] + k["unknown"]) / k["n_match"]) < 1e-12, "bounds are not [yes/n, (yes+unknown)/n]")
            need((S.get("n_base"), S.get("n_eligible"), S.get("n_match")) == (fam["N"], k["N_eligible"], k["n_match"]), "the support's chain is not the counts")
            need((comp.get("of"), comp.get("yes"), comp.get("no"), comp.get("unknown")) == (k["n_match"], k["yes"], k["no"], k["unknown"]), "the support's component is not the counts")
            need(k["n_match"] >= C.ARRIVE_SUPPORT, f"a published share on n {k['n_match']} < {C.ARRIVE_SUPPORT}", ("INV-08",))
            rec = dict(N=fam["N"], eligible=k["N_eligible"], not_yet=k["N_not_yet"], n=n, yes=yes, no=n - yes - unk, unknown=unk, members_digest=_members_digest(ref["matched"]))
    else:
        v.append(_viol("NO_RECOUNT", ["0.2 §5"], "the trace has no recount for this estimand (outside the declared area)", where, "WARNING"))
    return _result("BUNDLE-COUNTS", not [x for x in v if x["severity"] == "BLOCKING"], 1, v, rec)


def check_identity(scene, body, bundle, st):
    """IDENTITY: the identities the gate binds, re-derived (verify_snapshot recomputes family_id and snapshot_id; zone ids
    bind the snapshot, event, apex and algorithm), the parent of NOW / «Отсюда» is the family on screen, and the same
    request computed again (caches cleared) gives the same bundle."""
    route = scene["route"].split(":", 1)[1]
    v = []
    fam, bars, tick = family_of(scene)
    import scene24
    B = scene24._base(scene["instrument"])
    viol, _ = C.verify_snapshot(scene["instrument"], B, fam)
    for code_, refs, msg in viol:
        v.append(_viol("IDENTITY_" + code_, ["INV-09", "R06"], msg, f"family {fam.get('family_id')}"))
    if route.endswith("/family"):
        if (body.get("family_id"), body.get("snapshot_id")) != (fam.get("family_id"), fam.get("snapshot_id")):
            v.append(_viol("IDENTITY", ["R06"], "the response's family is not the re-derived one", scene["id"]))
    elif route.endswith("/now"):
        sid = ((body.get("contract") or {}).get("case_sets") or [{}])[0].get("snapshot_id")
        if sid != fam.get("snapshot_id"):
            v.append(_viol("PARENT", ["R06", "INV-05"], "NOW's parent snapshot is not the family on screen", scene["id"]))
    else:
        if (body.get("family_id"), body.get("snapshot_id"), body.get("N_parent")) != (fam.get("family_id"), fam.get("snapshot_id"), fam.get("N")):
            v.append(_viol("PARENT", ["R06", "INV-05"], "the parent of «Отсюда» is not the family on screen", scene["id"]))
    _clear_caches()
    again = pick_bundle(compute(scene), scene["estimand"], scene["selector"]) if bundle else None
    if bundle is not None and (again is None or norm_bundle(again) != norm_bundle(bundle)):
        v.append(_viol("NOT_DETERMINISTIC", ["INV-12"], "the same request computed again gives another bundle", f"bundle {bundle.get('id')}"))
    return _result("IDENTITY", not v, 1, v, dict(family_id=fam.get("family_id"), snapshot_id=fam.get("snapshot_id"), N=fam.get("N"),
                                                  bundle_digest=digest(norm_bundle(bundle)) if bundle else None))


# =====================================================================================================================
# the Q1 pilot's stores: read only
# =====================================================================================================================
def discover_stores():
    """Q1 stores on this machine: DR_IDR_Q1_STORES (separated by os.pathsep), else every lab/.q1-pilot/**/store* folder
    of this checkout and of its sibling worktrees (git worktree list); only folders holding issues/."""
    env = os.environ.get("DR_IDR_Q1_STORES")
    roots = [Path(p) for p in env.split(os.pathsep) if p] if env else []
    if not roots:
        tops = [ROOT]
        wl = git("worktree", "list", "--porcelain") or ""
        tops += [Path(line[9:]) for line in wl.splitlines() if line.startswith("worktree ")]
        for t in tops:
            base = Path(t) / "lab" / ".q1-pilot"
            if base.is_dir():
                roots += [p for p in base.rglob("store*") if (p / "issues").is_dir()]
    out, seen = [], set()
    for r in roots:
        k = str(Path(r).resolve()).lower()
        if k not in seen and (Path(r) / "issues").is_dir():
            seen.add(k)
            out.append(Path(r))
    return out


def store_label(root):
    p = Path(root).resolve()
    parts = p.parts
    i = max((j for j, x in enumerate(parts) if x == ".q1-pilot"), default=None)
    tail = "/".join(parts[i + 1:]) if i is not None else p.name
    wt = parts[i - 2] if i is not None and i >= 2 else "?"
    return f"{wt}:{tail}"


def file_hashes(root):
    return {str(p.relative_to(root)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(root).rglob("*")) if p.is_file()}


def check_q1_store(root, spec):
    """Q1-STORE for one store: recomputed identities (lab/q1/store.py's own recipe), payload fingerprints, the outcome
    links and the sequence of revisions, the index records (Q1TargetIdentity, Q1IssueIdentity, Q1OutcomeLink) valid
    against the trace schema, and the store's own verify() in agreement."""
    from q1 import store as QS
    root = Path(root)
    label = store_label(root)
    v, targets, issues, outcomes = [], {}, {}, {}
    for p in sorted((root / "issues").glob("*.json")):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
            pl = rec["payload"]
        except Exception as exc:
            v.append(_viol("UNREADABLE", ["INV-09"], f"issue {p.stem}: {exc}", f"{label}/issues/{p.name}"))
            continue
        t = pl["target"]
        tid_ok = QS.target_id(t) == pl["target_id"]
        iid_ok = QS.issue_id(pl["target_id"], pl["cut"]["index"], pl["estimator"]["id"], pl["inputs"]["model"], pl["inputs"]["input_digest"], pl["issue_kind"]) == pl["issue_id"]
        sha_ok = QS.sha(pl) == rec["meta"].get("payload_sha256")
        if not (tid_ok and iid_ok and sha_ok and p.stem == pl["issue_id"]):
            v.append(_viol("ISSUE_IDENTITY", ["INV-09", "ENT-25"], f"target_id {tid_ok}, issue_id {iid_ok}, payload {sha_ok}, file name {p.stem == pl['issue_id']}", f"{label}/issues/{p.name}"))
        targets[pl["target_id"]] = dict(target_id=pl["target_id"], question=t["question"], instrument=t["instrument"], trading_date=t["date"], block=t["block"],
                                        side=int(t["side"]), level_name=t["level"]["name"], horizon_end=t["horizon_end"], recomputed=tid_ok)
        issues[pl["issue_id"]] = dict(issue_id=pl["issue_id"], store=label, target=pl["target_id"], cut_index=int(pl["cut"]["index"]), cut_close=pl["cut"]["close"],
                                      estimator=pl["estimator"]["id"], model=pl["inputs"]["model"], input_digest=pl["inputs"]["input_digest"], issue_kind=pl["issue_kind"],
                                      publication=pl["estimate"]["publication"], payload_sha256=QS.sha(pl), recomputed=bool(tid_ok and iid_ok and sha_ok))
        if pl["issue_kind"] != "SIMULATED_ISSUE":
            v.append(_viol("ISSUE_KIND", ["BND-07"], f"an issue of kind {pl['issue_kind']} in a historical pilot", f"{label}/issues/{p.name}"))
    for p in sorted((root / "outcomes").glob("*.json")):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
            pl = rec["payload"]
        except Exception as exc:
            v.append(_viol("UNREADABLE", ["INV-09"], f"outcome {p.stem}: {exc}", f"{label}/outcomes/{p.name}"))
            continue
        oid_ok = QS.outcome_id(pl["issue_id"], pl["observed"], pl["basis"], pl["revision"], pl["supersedes"]) == pl["outcome_id"]
        sha_ok = QS.sha(pl) == rec["meta"].get("payload_sha256")
        iss = issues.get(pl["issue_id"])
        if iss is None:
            v.append(_viol("OUTCOME_WITHOUT_ISSUE", ["R15", "ENT-26"], f"outcome {pl['outcome_id'][:16]} links to a missing issue {pl['issue_id'][:16]}", f"{label}/outcomes/{p.name}"))
        elif iss["payload_sha256"] != pl["issue_payload_sha256"]:
            v.append(_viol("ISSUE_CHANGED", ["R15", "INV-09"], "the issue's bytes differ from the ones the outcome was attached to", f"{label}/outcomes/{p.name}"))
        if iss is not None and iss["target"] != pl["target_id"]:
            v.append(_viol("OTHER_TARGET", ["R15"], "the outcome's target is not its issue's", f"{label}/outcomes/{p.name}"))
        if not (oid_ok and sha_ok):
            v.append(_viol("OUTCOME_IDENTITY", ["INV-09"], f"outcome_id {oid_ok}, payload {sha_ok}", f"{label}/outcomes/{p.name}"))
        outcomes[pl["outcome_id"]] = dict(outcome_id=pl["outcome_id"], store=label, issue=pl["issue_id"], target=pl["target_id"], issue_payload_sha256=pl["issue_payload_sha256"],
                                          revision=int(pl["revision"]), label=pl["observed"]["label"], recomputed=bool(oid_ok and sha_ok))
        if pl.get("supersedes"):
            outcomes[pl["outcome_id"]]["supersedes"] = pl["supersedes"]
    by_issue = defaultdict(list)
    for o in outcomes.values():
        by_issue[o["issue"]].append(o)
    for iid, os_ in by_issue.items():
        os_.sort(key=lambda o: o["revision"])
        for k, o in enumerate(os_):
            want_prev = os_[k - 1]["outcome_id"] if k else None
            if o["revision"] != k + 1 or o.get("supersedes") != want_prev:
                v.append(_viol("REVISIONS", ["R15", "ENT-26"], f"revision {o['revision']} supersedes {str(o.get('supersedes'))[:16]} (expected {k + 1} superseding {str(want_prev)[:16]})", f"{label}/outcome {o['outcome_id'][:16]}"))
    errs = []
    for t in targets.values():
        errs += validate(t, "Q1TargetIdentity", spec)
    for i in issues.values():
        errs += validate(i, "Q1IssueIdentity", spec)
    for o in outcomes.values():
        errs += validate(o, "Q1OutcomeLink", spec)
    for e in errs[:5]:
        v.append(_viol("INDEX_STRUCTURE", ["0.2 §4"], e, label))
    own = QS.Store(root).verify() if (root / "issues").is_dir() and (root / "outcomes").is_dir() else dict(ok=False, problems=["no outcomes folder"])
    if bool(own["ok"]) != (not [x for x in v if x["code"] not in ("INDEX_STRUCTURE",)]):
        v.append(_viol("TWO_VERDICTS", ["INV-09"], f"the store's own verify() says ok={own['ok']} ({'; '.join(own['problems'][:2])})", label))
    return dict(store=label, issues=len(issues), outcomes=len(outcomes), targets=len(targets), violations=v, own_verify_ok=bool(own["ok"]),
                writable=len(own.get("writable", [])), index=dict(targets=targets, issues=issues, outcomes=outcomes))


def check_q1_stores(spec, roots=None):
    roots = discover_stores() if roots is None else roots
    before = {str(r): file_hashes(r) for r in roots}
    reps = [check_q1_store(r, spec) for r in roots]
    after = {str(r): file_hashes(r) for r in roots}
    v = [x for r in reps for x in r["violations"]]
    if before != after:
        v.append(_viol("STORE_WRITTEN", ["INV-09"], "a store's bytes changed during the run", "stores"))
    det = dict(stores=[{k: r[k] for k in ("store", "issues", "outcomes", "targets", "own_verify_ok", "writable")} for r in reps],
               bytes_unchanged=before == after, files=sum(len(h) for h in before.values()),
               files_digest=digest({store_label(k): v_ for k, v_ in before.items()}))
    return _result("Q1-STORE", not v and bool(roots), sum(r["issues"] + r["outcomes"] for r in reps), v, det), reps


def arrive_issue_match(scene, body, bundle, reps, reproduce=True):
    """Q1-ISSUE-MATCH: the stored issue of the same target (instrument, date, block, place), cut, set (the screen's
    weekday / all-weekdays family = NODEPOS_WD / NODEPOS_ALL) and model answers what «Отсюда» computed: the same counts
    and the same labelled members; reproduced on its own inputs it is IDENTICAL. Presenting is not issuing: a missing
    issue leaves the computed answer as it is (BND-07)."""
    import arrive24
    from q1 import engine as Q
    lvl = params_of(bundle).get("level") if bundle else json.loads(scene["selector"]).get("level")
    est = arrive24.SCOPE_EST["all" if scene["scope"] == "ALL_WEEKDAYS" else "weekday"]
    place = next((p for p in body.get("places") or [] if p["level"] == lvl), None)
    cut_close = scene["at_clock_et"]
    found = []
    for rep in reps:
        for iid, i in rep["index"]["issues"].items():
            t = rep["index"]["targets"].get(i["target"]) or {}
            if (t.get("instrument"), t.get("trading_date"), t.get("block"), t.get("level_name"), i["cut_close"], i["estimator"]) == \
               (scene["instrument"], scene["trading_date"], scene["block"], lvl, cut_close, est):
                found.append((rep, i))
    if not found:
        return _result("Q1-ISSUE-MATCH", False, 0, [_viol("NO_ISSUE", ["BND-07"], "no stored issue for this target, cut and set", scene["id"], "WARNING")], dict(found=0)), None
    v, det = [], dict(found=len(found), stores=sorted({r["store"] for r, _ in found}))
    rep, i = found[0]
    root = next(r for r in discover_stores() if store_label(r) == rep["store"])
    rec = json.loads((Path(root) / "issues" / f"{i['issue_id']}.json").read_text(encoding="utf-8"))
    pl = rec["payload"]
    if pl["inputs"]["model"] != Q.MODEL:
        v.append(_viol("OTHER_MODEL", ["INV-09", "A14"], f"the issue was made by model {pl['inputs']['model'][:12]}, this line computes with {Q.MODEL[:12]}", i["issue_id"][:16]))
    k = (place or {}).get("counts") or {}
    want = {f: pl["counts"][f] for f in ("N_eligible", "N_not_yet", "n_match", "yes", "no", "unknown", "n_known")}
    got = {f: k.get(f) for f in want}
    if want != got:
        v.append(_viol("ANSWERS_DIFFER", ["T12", "A15"], f"issue {want} vs screen block {got}", i["issue_id"][:16]))
    ip = sorted((m["id"], m["label"]) for m in pl["members"])
    sp = sorted(map(tuple, (place or {}).get("members") or []))
    if ip != sp:
        v.append(_viol("MEMBERS_DIFFER", ["T12", "A15"], "the issue's labelled members are not the screen block's", i["issue_id"][:16]))
    det.update(issue_id=i["issue_id"], issue_kind=i["issue_kind"], publication=i["publication"], model=pl["inputs"]["model"][:12], counts=want,
               members_digest=_members_digest(ip), screen_members_digest=_members_digest(sp),
               outcomes=[dict(outcome_id=o["outcome_id"], revision=o["revision"], label=o["label"], linked=bool(o["recomputed"] and o["issue_payload_sha256"] == i["payload_sha256"]))
                         for o in rep["index"]["outcomes"].values() if o["issue"] == i["issue_id"]])
    if reproduce:
        from q1.store import Store
        tbl = Q.table(scene["instrument"], scene["block"])
        r = Q.reproduce(Store(root), tbl, i["issue_id"])
        det["reproduce"] = r.get("status")
        if r.get("status") != "IDENTICAL":
            v.append(_viol("NOT_REPRODUCED", ["A14", "INV-09"], f"reproduce: {r.get('status')}", i["issue_id"][:16]))
    return _result("Q1-ISSUE-MATCH", not v, 1, v, det), dict(rep=rep, issue=i)


# =====================================================================================================================
# the screen: the state the page rendered (collected by tests/trace_page.mjs in a throw-away headless Chrome)
# =====================================================================================================================
def js_pct(v):
    """The page's pct(): one decimal half up, no trailing zero, Russian decimal comma, the percent sign joined."""
    r = int(v * 10 + 0.5 + 1e-9) / 10 if v >= 0 else -int(-v * 10 + 0.5 + 1e-9) / 10
    s = f"{r:.0f}" if float(r).is_integer() else f"{r:.1f}"
    return s.replace(".", ",") + "%"


def expected_shown(bundle_or_passport, kind):
    """The value an element must show, from what it is bound to (value forms of SC-1.1 §12.4)."""
    if kind == "PASSPORT":
        p = bundle_or_passport
        if not p.get("N"):
            return "—"
        lo = 100 * p["yes_count"] / p["N"]
        if p.get("binary") and p.get("unknown_count"):
            return js_pct(lo) + "–" + js_pct(100 * (p["yes_count"] + p["unknown_count"]) / p["N"])
        return js_pct(lo)
    b = bundle_or_passport
    E = {e["value_kind"]: e for e in b["estimates"]}
    comp = (b["supports"][0].get("components") or [{}])[0]
    if b["estimand"].startswith("EST:N-NEW-") or b["estimand"] == "EST:K-ARRIVE":
        if comp.get("unknown"):
            return js_pct(100 * E["BOUNDS"]["lower"]) + "–" + js_pct(100 * E["BOUNDS"]["upper"])
        if b["estimand"] == "EST:K-ARRIVE":
            return js_pct(100 * E["BOUNDS"]["lower"])
        return js_pct(100 * E["POINT"]["value"]) if "POINT" in E else "—"
    if "POINT" in E:
        return js_pct(100 * E["POINT"]["value"])
    return None


def ingest_screen(raw, scene_ids, page_file=None):
    """A ScreenStateRecord (trace schema) from the collector's raw output: visible texts become digests (a row may hold
    a price); the bound bundles become the digests of their normalized form."""
    page_file = page_file or (ROOT / "lab" / "dist" / "24" / "d24.js")
    els = []
    for e in raw["elements"]:
        txt = "\n".join([e.get("text") or "", e.get("title") or ""] + list(e.get("sub") or []))
        rec = dict(element=f"{raw['fragment']}#l21={e['l21']}", block=e["block"], text_sha256=hashlib.sha256(txt.encode("utf-8")).hexdigest(),
                   bound_kind=e["bound_kind"])
        if e.get("shown") is not None:
            rec["shown_value"] = e["shown"]
        if e.get("binding"):
            rec["binding"] = e["binding"]
        for k in ("estimand", "claim_form", "absence_reason"):
            if e.get(k):
                rec[k] = e[k]
        if e.get("parameters") is not None:
            rec["parameters"] = json.dumps(e["parameters"], ensure_ascii=False, sort_keys=True)
        if e.get("counts") is not None:
            rec["counts"] = json.dumps(e["counts"], ensure_ascii=False, sort_keys=True)
        if e.get("passport") is not None:
            rec["passport_checked"] = bool(e["passport"].get("checked"))
            if e["passport"].get("violation"):
                rec["passport_violation"] = str(e["passport"]["violation"])[:200]
        if e.get("bundle") is not None:
            rec["bundle_digest"] = digest(norm_bundle(e["bundle"]))
        if e.get("label_ok") is not None:
            rec["label_ok"] = bool(e["label_ok"])
        els.append(rec)
    # the page build by its LF-normalized SHA-256 (a git checkout on Windows writes CRLF; the page is the same)
    return dict(id=f"SCREEN:{raw['fragment']}", page_build_sha256=sha256_lf(page_file),
                registry_hash=str(raw["contract"].get("registry_hash")), fragment=raw["fragment"], viewport=raw.get("viewport", "?"),
                collected_at_utc=raw.get("collected_at_utc", "?"), page_violations=[str(x)[:200] for x in raw["contract"].get("violations") or []],
                unchecked_passports=int(raw["contract"].get("unchecked") or 0), elements=els, scenes=scene_ids)


def check_screen(st, scene, screen, bundle, body):
    """SCREEN: the element of this claim in the rendered state — bound to the published bundle (same normalized digest)
    or to a passport the reference checked, showing the value its value form gives, in its registered words; the page's
    registry is the server's; the page shows no violation."""
    v = []
    where = screen["id"]
    if screen["registry_hash"] != C.registry_hash():
        v.append(_viol("PAGE_REGISTRY", ["OB:PAGE-WORDS", "R13"], f"the page's registry {screen['registry_hash']} is not the server's {C.registry_hash()}", where))
    for x in screen.get("page_violations") or []:
        v.append(_viol("PAGE_VIOLATION", ["R13", "B15"], x, where))
    est = scene["estimand"]
    sel = json.loads(scene["selector"])
    el = None
    if est.startswith("EST:B-ZONE-"):
        zid = params_of(bundle).get("zone_id") if bundle else None
        el = next((e for e in screen["elements"] if e.get("estimand") == est and json.loads(e.get("parameters") or "{}").get("zone_id") == zid and e["bound_kind"] == "PASSPORT"), None)
    elif est.startswith("EST:N-NEW-"):
        el = next((e for e in screen["elements"] if e["block"] == "NOW" and e.get("estimand") == est), None)
    elif est == "EST:K-ARRIVE":
        el = next((e for e in screen["elements"] if e["block"] == "ARRIVE" and json.loads(e.get("parameters") or "{}").get("level") == sel.get("level")), None)
    if el is None:
        v.append(_viol("NO_ELEMENT", ["R13", "ENT-29"], f"no rendered element carries {est} {sel}", where))
        return _result("SCREEN", False, len(screen["elements"]), v), None
    unbound = [e for e in screen["elements"] if e["bound_kind"] == "UNBOUND"]
    for e in unbound[:3]:
        v.append(_viol("UNBOUND_NUMBER", ["R13", "OB:NO-UNDECLARED-NUMBER"], f"an element shows {e.get('shown_value')!r} with no passport or bundle", e["element"]))
    if bundle is not None:
        if el["bound_kind"] == "BUNDLE":
            if el.get("bundle_digest") != digest(norm_bundle(bundle)):
                v.append(_viol("NOT_THE_BUNDLE", ["R13", "0.2 §1"], "the page shows a bundle other than the one computed for this scene", el["element"]))
            want = expected_shown(bundle, "BUNDLE")
        else:
            P = json.loads(el.get("counts") or "{}")
            E = {e["value_kind"]: e for e in bundle["estimates"]}
            comp = (bundle["supports"][0].get("components") or [{}])[0]
            if (P.get("yes"), P.get("unknown"), P.get("N")) != (E["POINT"]["numerator"], comp.get("unknown"), E["POINT"]["denominator"]):
                v.append(_viol("PASSPORT_COUNTS", ["R13", "OB:PAGE-PASSPORTS"], f"passport {P} vs bundle", el["element"]))
            if not el.get("passport_checked") or el.get("passport_violation"):
                v.append(_viol("PASSPORT_UNCHECKED", ["OB:PAGE-PASSPORTS"], f"the reference did not confirm the passport ({el.get('passport_violation') or 'not checked'})", el["element"]))
            want = expected_shown(dict(yes_count=P.get("yes"), unknown_count=P.get("unknown"), N=P.get("N"), binary=P.get("binary")), "PASSPORT")
        if el.get("shown_value") != want:
            v.append(_viol("SHOWN_VALUE", ["R13", "INV-11"], f"shown {el.get('shown_value')!r}, the value form gives {want!r}", el["element"]))
    else:
        # Candidate §0.4 replaces a resolved ARRIVE percentage by the registered fact mark. Admit it only when the
        # recomputed answer confirms RESOLVED for this exact place; never admit a number or a mark on an open target.
        value = el.get("shown_value") or ""
        place = next((p for p in body.get("places") or [] if p.get("level") == sel.get("level")), {}) if est == "EST:K-ARRIVE" else {}
        mark = next((x["text_ru"] for x in (C.get("FF:K-TARGET") or {}).get("labels", []) if x["key"] == "RESOLVED_mark"), None)
        resolved_mark = el.get("absence_reason") == "RESOLVED_TODAY" and place.get("state", {}).get("status") == "RESOLVED" and value == mark == "✓"
        if el["bound_kind"] != "ABSENCE" or (value not in ("", "—") and not resolved_mark):
            v.append(_viol("NUMBER_WITHOUT_BUNDLE", ["R13", "0.2 §4"], f"the element shows {el.get('shown_value')!r} although no number is published", el["element"]))
    if el.get("label_ok") is False:
        v.append(_viol("WORDS", ["OB:PAGE-WORDS", "R13"], "the visible words are not the registered labels rendered with these values", el["element"]))
    return _result("SCREEN", not v, len(screen["elements"]), v, dict(element=el["element"], shown=el.get("shown_value"), bound_kind=el["bound_kind"])), el


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def collect_screens(fragments, workdir):
    """Starts this checkout's server on a free port (never 8767 / 8771 / 8772), runs tests/trace_page.mjs in a throw-away
    headless Chrome on each fragment, stops the server. Returns {fragment: raw state}. The raw state (it may hold
    prices) stays in workdir; only ingest_screen's digests leave it."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    port = free_port()
    out_f, err_f = open(workdir / "server.out.log", "wb"), open(workdir / "server.err.log", "wb")
    srv = subprocess.Popen([sys.executable, "-B", str(LAB / "server.py"), "--port", str(port)], cwd=str(LAB), stdout=out_f, stderr=err_f)
    try:
        url = f"http://127.0.0.1:{port}"
        for _ in range(240):
            try:
                with urllib.request.urlopen(url + "/api/health", timeout=2) as r:
                    if r.status == 200:
                        break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError("the server of this checkout did not start (see " + str(workdir / "server.err.log") + ")")
        raw_file = workdir / "screens.raw.json"
        r = subprocess.run(["node", str(ROOT / "tests" / "trace_page.mjs"), "--base", url + "/24/", "--out", str(raw_file)] + list(fragments),
                           cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        if r.returncode != 0:
            raise RuntimeError("tests/trace_page.mjs: " + (r.stdout + r.stderr)[-1500:])
        return {x["fragment"]: x for x in json.loads(raw_file.read_text(encoding="utf-8"))}
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=10)
        except Exception:
            srv.kill()
        out_f.close()
        err_f.close()


# =====================================================================================================================
# the trace report of one claim
# =====================================================================================================================
def _link(source, relation, target, status, mandatory, evidence, note=None):
    d = dict(source=source, relation=relation, target=target, status=status, mandatory=bool(mandatory), evidence=evidence)
    if note:
        d["note"] = note
    return d


def _stage(stage, summary, links):
    """The status of a stage is the worst of its mandatory links (the optional ones — the tape before the base, the
    human reading, an issue — are separate axes and stay visible as links); a stage with none takes the worst of all."""
    mand = [l["status"] for l in links if l["mandatory"]]
    worst = min(mand or [l["status"] for l in links], key=WORST.index)
    return dict(stage=stage, status=worst, summary_ru=summary, links=links)


def standing_of(st, profile_key):
    return next((s for s in st["cat"].get("standings", []) if s["profile_key"] == profile_key), None)


def artifact_versions(st, extra=()):
    import scene24
    from q1 import engine as Q
    head = git("rev-parse", "HEAD") or "unknown"
    dirty = bool(git("status", "--porcelain", "--", "lab", "trace", "contract", "design", "tests"))
    B = scene24._base("NQ")
    src = scene24.source_version("NQ", B) if B is not None else {}     # the version the bundles' inputs carry
    sc = next(e for e in st["reg"]["editions"] if e["id"] == "DR-LAB-SC-1.1")
    out = [dict(artifact="git:HEAD", version=head + ("+dirty" if dirty else "")), dict(artifact="DR-LAB-SC-1.1:registry", version=C.registry_hash()),
           dict(artifact="DR-LAB-SC-1.1:document-pin", version=sc["document_sha256_lf"]),
           dict(artifact="trace:catalog", version=st["stamps"]["catalog_sha256"][:16]), dict(artifact="lab/contract.py::_code_hash", version=C._code_hash()),
           dict(artifact="session-base:NQ", version=f"{src.get('base')}@{src.get('built')}"),
           dict(artifact="q1:MODEL", version=Q.MODEL[:12]), dict(artifact=VERSION, version=sha256_lf(Path(__file__))[:12])]
    return out + list(extra)


def trace_scene(st, g, scene, screen=None, reps=None, mutations=True, body=None, static=None, reproduce=True):
    """The provenance report of the scene's claim (a TraceReport of the trace schema). body: an already computed (or a
    tampered) response; when given, the checks run on it instead of a fresh computation."""
    route = scene["route"].split(":", 1)[1]
    est_id, sel = scene["estimand"], json.loads(scene["selector"])
    stg = standing_of(st, scene["profile_key"])
    _clear_caches()
    body = body if body is not None else compute(scene)
    bundle = pick_bundle(body, est_id, sel)
    est = C.get(est_id)
    form = C.claim_form_of(est_id)
    env = body.get("contract") or {}
    checks, ev = [], []
    # ---- the checks of this run
    gate = check_gate(body, bundle)
    checks.append(gate)
    absence = None
    if bundle is None and route.endswith("/arrive"):
        place = next((p for p in body.get("places") or [] if p["level"] == sel.get("level")), None)
        st_ = (place or {}).get("state", {}).get("status")
        absence = "FEW_SESSIONS" if (place or {}).get("publication") == "WITHHELD_FEW_SESSIONS" else "RESOLVED_TODAY" if st_ == "RESOLVED" else \
                  "NO_KNOWN_OUTCOME" if (place or {}).get("publication") == "NO_KNOWN_OUTCOME" else "CONTRACT_WITHHELD" if (place or {}).get("withheld") else \
                  {"PREFIX_UNKNOWN": "PREFIX_UNKNOWN", "DR_BROKEN": "DR_BROKEN", "NO_PREFIX": "NO_PREFIX", "BLOCK_OVER": "BLOCK_OVER"}.get(body.get("status"))
    claim_chk = check_bundle_claim(st, route, body, bundle) if bundle else None
    counts_chk = check_bundle_counts(scene, body, bundle) if bundle else None
    if absence == "FEW_SESSIONS":
        place = next(p for p in body["places"] if p["level"] == sel["level"])
        fam, bars, tick = family_of(scene)
        a, b = C.ARRIVE_LEVELS[sel["level"]]
        ref = C.ref_arrive(fam, bars, tick, body["cut"]["cut"], a, b)
        ok = len(ref["matched"]) == place["counts"]["n_match"] < C.ARRIVE_SUPPORT
        counts_chk = _result("BUNDLE-COUNTS", ok, 1, [] if ok else [_viol("COUNTS", ["INV-08"], "«мало сессий» without n < 20 by the reference", scene["id"])],
                             dict(n=len(ref["matched"]), support_min=C.ARRIVE_SUPPORT, members_digest=_members_digest(ref["matched"])))
    for c in (claim_chk, counts_chk):
        if c:
            checks.append(c)
    ident = check_identity(scene, body, bundle, st)
    checks.append(ident)
    fut_t = fut_m = None
    if mutations:
        fut_t = check_future_target(scene, base_body=body)
        fut_m = check_future_members(scene, base_body=body)
        checks += [fut_t, fut_m]
    q1m = None
    if route.endswith("/arrive") and reps is not None:
        q1m, _ = arrive_issue_match(scene, body, bundle, reps, reproduce=reproduce)
        checks.append(q1m)
    scr = el = None
    if screen is not None:
        scr, el = check_screen(st, scene, screen, bundle, body)
        checks.append(scr)
    by = {c["check"]: c for c in checks}
    st_of = lambda name: "VERIFIED" if by.get(name, {}).get("outcome") == "PASS" else "MISSING" if name in by else "IMPLEMENTED_UNVERIFIED"
    static = static or {}
    st_static = lambda name: "VERIFIED" if static.get(name, {}).get("outcome") == "PASS" else "MISSING" if name in static else "IMPLEMENTED_UNVERIFIED"
    inputs = {(i["input_kind"], i["ref"]): i for i in ((bundle or {}).get("derivation") or {}).get("inputs") or []}
    obs_in = next((i for (k, _), i in inputs.items() if k == "OBSERVATION_SNAPSHOT"), None)
    cs_in = next((i for (k, _), i in inputs.items() if k == "CASE_SET_SNAPSHOT"), None)
    key = f"{scene['instrument']}-{scene['trading_date'].replace('-', '')}-{scene['block']}"
    bid = f"bundle:{route}#{est_id}{json.dumps(sel, ensure_ascii=False)}"
    gate_ok = st_of("GATE-CONFORMANT")
    stages = []
    # OBSERVATION
    stages.append(_stage("OBSERVATION", "история из собранной базы сессий; лента G3 и сборка M1 → M5 вне прогона (GAP-09)", [
        _link("OBS:G3-TAPE", "observed_as", f"base:{obs_in['version'] if obs_in else '?'}", "IMPLEMENTED_UNVERIFIED", False, "lab/build_boxes.py::build (не перезапускалась)", "GAP-09"),
        _link(f"base:{obs_in['version'] if obs_in else '?'}", "input_of", bid if bundle else f"answer:{scene['id']}", ("VERIFIED" if obs_in else "MISSING") if bundle else "NOT_APPLICABLE", bool(bundle), "derivation.inputs[OBSERVATION_SNAPSHOT]"),
        _link(f"base:{obs_in['version'] if obs_in else '?'}", "re_derived_by", "code:lab/contract.py::verify_snapshot", gate_ok if ident["outcome"] == "PASS" else "MISSING", True, "runtime:lab/contract.py::verify_snapshot (пути, коробки, подтверждения членов из M5 базы)")]))
    # STATE
    state_links = [_link(f"session:{key}", "known_at", f"cut:{key}@{scene['at_clock_et']}", gate_ok, True, "runtime:lab/contract.py::today_state (подтверждение / слом сегодня по закрытым M5)")]
    if not route.endswith("/family"):
        state_links.append(_link(f"cut:{key}@{scene['at_clock_et']}", "prefix_only", "CUT:NOW-COMMON-CLOCK-1", st_of("FUTURE-TARGET"), True, "trace:FUTURE-TARGET (будущее сегодняшнего дня заменено в памяти)"))
    else:
        state_links.append(_link(f"cut:{key}@{scene['at_clock_et']}", "fixes_family_key", "CS:F-CONF-1" if scene["scope"] == "WEEKDAY" else "CS:F-CONF-ALL-1", st_of("FUTURE-TARGET"), True, "trace:FUTURE-TARGET"))
    stages.append(_stage("STATE", "сегодняшняя сессия читается только через закрытые M5 до среза", state_links))
    # QUESTION
    q_links = [_link(est["question"], "asks", est_id, st_static("ESTIMAND-CHAIN"), True, "trace:ESTIMAND-CHAIN"),
               _link(est_id, "measures", est["q5_outcome"], st_static("REF-RESOLVE"), True, "trace:REF-RESOLVE"),
               _link(f"request:{(env.get('request') or {}).get('request_id', '?')}", "requests", est_id, gate_ok, True, "ContractEnvelope.request (QuestionRequest: кто и когда спросил, без полномочий)")]
    stages.append(_stage("QUESTION", f"{est['question']}: {(C.get(est['question']) or {}).get('text_ru', '')}", q_links))
    # CASE_SET
    cs_spec = bundle_case_set(st, body, bundle) if bundle else ("CS:K-ARRIVE-ALL-1" if scene["scope"] == "ALL_WEEKDAYS" else "CS:K-ARRIVE-1")
    cs_links = [_link(cs_spec, "instantiated_as", f"snapshot:{cs_in['version'] if cs_in else ident['details'].get('snapshot_id')}", st_of("IDENTITY"), True, "trace:IDENTITY + runtime:lab/contract.py::verify_snapshot"),
                _link(cs_spec, "selects_without_labels", f"selection:{scene['id']}", st_of("FUTURE-MEMBERS"), True, "trace:FUTURE-MEMBERS (будущее аналогов заменено в памяти)")]
    stages.append(_stage("CASE_SET", f"правило {cs_spec}; состав — снимок семьи и отбор на срезе; метки исхода в отбор не входят", cs_links))
    # OUTCOMES
    out_spec = C.get(est["q5_outcome"]) or {}
    oc = [_link(est["q5_outcome"], "defined_by", "code:" + out_spec.get("reference_definition", "?"), st_static("CODE-REFS"), True, "trace:CODE-REFS"),
          _link(f"selection:{scene['id']}", "labelled_by", est["q5_outcome"], st_of("BUNDLE-COUNTS"), True, "trace:BUNDLE-COUNTS (пересчёт по эталонным определениям)")]
    stages.append(_stage("OUTCOMES", f"{est['q5_outcome']}: исход каждого случая по своему определению, отдельной ветвью от отбора", oc))
    # COMPUTATION
    estr = next((e for e in st["reg"]["estimators"] if est_id in e["estimands"]), {})
    comp_links = [_link(estr.get("id", "?"), "computes", est_id, st_static("ESTIMAND-CHAIN"), True, "trace:ESTIMAND-CHAIN")]
    if bundle:
        comp_links += [_link(bid, "derived_by", "code:" + (re.findall(r"[\w./-]+\.py::[\w.]+", bundle["derivation"]["operation"]) or ["?"])[0], gate_ok, True, "derivation.operation; verification VERIFIED_BY_REFERENCE"),
                       _link(bid, "inputs_versioned", "inputs:" + ",".join(sorted(k for k, _ in inputs)), "VERIFIED" if obs_in and cs_in and ("REGISTRY", C.EDITION) in inputs else "MISSING", True, "derivation.inputs: наблюдения, снимок набора, реестр, код")]
    else:
        comp_links.append(_link(f"answer:{scene['id']}", "no_bundle", absence or "?", "NOT_APPLICABLE", False, "числа нет: причина отсутствия"))
    stages.append(_stage("COMPUTATION", "вычисление — то, что опубликовал шлюз; эталон пересчитал его в момент ответа", comp_links))
    # ESTIMATE_SUPPORT
    es = [_link(bid if bundle else f"answer:{scene['id']}", "estimate_and_support", est_id, st_of("BUNDLE-COUNTS"), True, "trace:BUNDLE-COUNTS (числитель, знаменатель, опора, неизвестные)"),
          _link(bid if bundle else f"answer:{scene['id']}", "same_on_recompute", est_id, st_of("IDENTITY"), True, "trace:IDENTITY")]
    stages.append(_stage("ESTIMATE_SUPPORT", "оценка и опора — параллельные результаты одного расчёта", es))
    # ADMISSION
    dec = stg["decision"] if stg else "OPEN"
    adm = [_link(est_id, "worded_by", form["id"] if form else "?", st_of("BUNDLE-CLAIM") if bundle else st_static("CLAIM-PROFILE"), True, "trace:BUNDLE-CLAIM / trace:CLAIM-PROFILE"),
           _link(form["id"] if form else "?", "admitted_on", cs_spec, st_of("BUNDLE-CLAIM") if bundle else st_static("CLAIM-PROFILE"), True, "lab/contract.py::admissible_claims"),
           _link(est["profile"], "decided_by", stg["id"] if stg else "?", "VERIFIED" if dec == "ACCEPTED" else "PROPOSED", False, "ProfileStanding.decision_sources", f"решение: {dec}")]
    stages.append(_stage("ADMISSION", f"форма {form['id'] if form else '?'} ({form['claim_class'] if form else '?'}); решение по профилю: {dec}", adm))
    # PRESENTATION
    pbs = [b for b in st["cat"].get("bindings", []) if b.get("estimand") == est_id and b["binding_class"] == "StatisticalPresentationBinding"]
    abs_b = [b for b in st["cat"].get("bindings", []) if b["binding_class"] == "AbsencePresentationBinding" and est_id in b["applies_to"] and b["absence_reason"] == absence]
    pres = [_link(est_id, "presented_by", ",".join(b["id"] for b in (abs_b if absence else pbs)) or "?", st_static("BINDING-COVERAGE") if (abs_b if absence else pbs) else "MISSING", True, "SWPC-1.1 §9 → trace:BINDING-COVERAGE")]
    if screen is not None:
        pres.append(_link((abs_b or pbs or [{"id": "?"}])[0]["id"], "rendered_as", (el or {}).get("element", "?"), st_of("SCREEN"), True, "trace:SCREEN (снятое состояние экрана)"))
    else:
        pres.append(_link((abs_b or pbs or [{"id": "?"}])[0]["id"], "rendered_as", "screen:not collected", "IMPLEMENTED_UNVERIFIED", False, "состояние экрана в этом прогоне не снималось"))
    pres.append(_link((el or {}).get("element", "screen"), "read_by", "human:operator", "MISSING", False, "H-задачи SWPC не проводились (GAP-10)", "человеческое прочтение — отдельная ось"))
    stages.append(_stage("PRESENTATION", "привязка SWPC и элемент, который страница фактически показала", pres))
    # ISSUE
    if route.endswith("/arrive"):
        if q1m is None:
            stages.append(_stage("ISSUE", "хранилища выпусков в этом прогоне не читались", [_link(f"answer:{scene['id']}", "issued_as", "q1:?", "IMPLEMENTED_UNVERIFIED", False, "trace:Q1-ISSUE-MATCH не запускалась")]))
        else:
            d = q1m["details"]
            iid = d.get("issue_id")
            il = [_link(f"answer:{scene['id']}", "same_question_as", f"q1:issue:{iid[:16]}" if iid else "q1:none", st_of("Q1-ISSUE-MATCH") if iid else "MISSING", False,
                        "trace:Q1-ISSUE-MATCH (та же цель, срез, набор и модель; выпуск — отдельная операция)")]
            for o in d.get("outcomes") or []:
                il.append(_link(f"q1:issue:{iid[:16]}", "resolved_by", f"q1:outcome:{o['outcome_id'][:16]}", "VERIFIED" if o.get("linked") else "MISSING", False,
                                "trace:Q1-STORE (outcome_id пересчитан, ссылка на отпечаток выпуска)", f"ревизия {o['revision']}: {o['label']}"))
            stages.append(_stage("ISSUE", "сохранённый выпуск того же вопроса — отдельная операция; показ его не создаёт", il))
    else:
        stages.append(_stage("ISSUE", "у профиля нет механизма выпусков", [_link(f"answer:{scene['id']}", "issued_as", "none", "NOT_APPLICABLE", False, "BASE-24 и NOW-1.0 не сохраняют выпусков")]))
    # operations, assessment, violations
    ops = [dict(operation="COMPUTE", performed=bool(bundle) or absence is not None, evidence="trace:GATE-CONFORMANT, trace:BUNDLE-COUNTS",
                not_implied_ru="расчёт не доказывает показ и не создаёт выпуск"),
           dict(operation="PRESENT", performed=bool(screen is not None and el is not None), evidence=(screen or {}).get("id", "состояние экрана не снималось"),
                not_implied_ru="показ не доказывает расчёт (сверяется с bundle отдельно) и не создаёт выпуск"),
           dict(operation="ISSUE", performed=bool(q1m and q1m["details"].get("issue_id")), evidence=(q1m or {}).get("details", {}).get("issue_id", "выпуска нет или хранилища не читались"),
                not_implied_ru="выпуск не доказывает, что ответ показан или прочитан")]
    violations = [x for c in checks for x in c["violations"] if x["severity"] == "BLOCKING"]
    for r in stale_reasons(st):                       # fail closed, as CONTRACT_STALE: a stale catalog proves no link
        violations.append(_viol("TRACE_STALE", ["INV-12"], r, "trace/build"))
    mand = [l for s in stages for l in s["links"] if l["mandatory"]]
    for l in mand:
        if l["status"] == "MISSING":
            violations.append(_viol("BROKEN_LINK", ["0.1 §11"], f"{l['source']} —{l['relation']}→ {l['target']}: {l['evidence']}", f"{scene['id']}:{l['relation']}"))
    reliable = all(l["status"] in ("VERIFIED", "NOT_APPLICABLE") for l in mand) and not violations
    static_ok = all(static.get(k, {}).get("outcome") == "PASS" for k in ("REF-RESOLVE", "CODE-REFS", "ESTIMAND-CHAIN", "CLAIM-PROFILE", "BINDING-COVERAGE")) if static else False
    impl_links = [l for s in stages if s["stage"] not in ("PRESENTATION", "QUESTION") for l in s["links"] if l["mandatory"]]
    assessment = dict(decision=dec, model_definiteness="DEFINED" if static_ok else "INCOMPLETE",
                      implementation="VIOLATED" if any(l["status"] == "MISSING" for l in impl_links) or [v for c in checks if c["check"] != "SCREEN" for v in c["violations"] if v["severity"] == "BLOCKING"]
                      else "VERIFIED_IN_RUN" if all(l["status"] in ("VERIFIED", "NOT_APPLICABLE") for l in impl_links) else "NOT_VERIFIED",
                      presentation_machine="NOT_COLLECTED" if scr is None else "VERIFIED_IN_RUN" if scr["outcome"] == "PASS" else "VIOLATED",
                      presentation_human=(stg or {}).get("human_acceptance", "PENDING"), reliable=bool(reliable))
    for c in checks:
        ev.append(dict(check=f"trace:{c['check']}", obligation=c["check"], origin="MACHINE_RUN_HERE", outcome=c["outcome"],
                       artifact_versions=[dict(artifact="git:HEAD", version=git("rev-parse", "HEAD") or "unknown"), dict(artifact="DR-LAB-SC-1.1:registry", version=C.registry_hash())],
                       checked=c["checked"], source=f"lab/semtrace.py ({VERSION})", detail="; ".join(x["message"] for x in c["violations"])[:300] or None))
    for e in ev:
        if e["detail"] is None:
            e.pop("detail")
    if route.endswith("/arrive"):
        ev.append(dict(check="reported:studies/q1_pilot_2026_10_12/README.md", obligation="A15: сверка A/D 296 738 строк × 3 оценивателя, скалярный пересчёт", origin="REPORTED_BY_ENGINEER",
                       outcome="PASS", artifact_versions=[dict(artifact="q1-pilot-c1", version="e9b5bc68cbfe11cc529f11502876cfd748bdba57")], source="studies/q1_pilot_2026_10_12/README.md",
                       detail="заявлено исполнителем пилота; в этом прогоне не повторялось (BND-08)"))
    rep = dict(id=f"TRACE:{scene['id']}", scene=scene["id"], claim=f"{est_id} {json.dumps(sel, ensure_ascii=False)}" + (f" — нет числа: {absence}" if absence else ""),
               profile_key=scene["profile_key"], stages=stages, operations=ops, assessment=assessment, violations=violations,
               artifact_versions=artifact_versions(st), evidence=ev)
    errs = validate(rep, "TraceReport", st["spec"])
    if errs:
        rep["violations"].append(_viol("REPORT_STRUCTURE", ["0.2 §4"], "; ".join(errs[:3]), rep["id"]))
        rep["assessment"]["reliable"] = False
    return rep, dict(body=body, bundle=bundle, checks=checks, element=el)


# =====================================================================================================================
# backward and reverse: lineage and impact
# =====================================================================================================================
def lineage(g, start, max_nodes=4000):
    """What a node depends on, back to its sources: forward over dependency, implementation, source and check links."""
    seen, q = {start}, deque([start])
    while q and len(seen) < max_nodes:
        y = q.popleft()
        for rel, b, cat in g.out.get(y, []):
            if cat in (DEP, IMPL, SOURCE, CHECK, CALLS) and b not in seen:
                seen.add(b)
                q.append(b)
    seen.discard(start)
    return _groups(g, start, seen)


def impact(g, start, max_nodes=20000):
    """What depends on a changed definition, rule or function, by four rules:
      - a definition or record: what refers to it (reverse dependency and source links) and the checks it names;
      - the changed definition itself: also its implementations (the code that executes it);
      - code: its callers, and what it implements (definitions, entries, checks, bindings) — which then pass the change
        on to what refers to them by the first rule;
      - a check is re-run; it changes nothing further.
    A definition reached as a dependent does not pass the change into its other implementations, and an affected entry
    or binding does not pass it into the code it names (otherwise any change would reach everything through shared
    code). The static calls are by names (BND-11): an upper estimate, not the executed graph."""
    parent = impact_walk(g, start, max_nodes)
    parent.pop(start)
    return _groups(g, start, set(parent))


def impact_walk(g, start, max_nodes=20000):
    """The reverse closure with, for every node reached, the link it was reached by (node -> (previous node, relation))."""
    parent, q = {start: None}, deque([start])
    while q and len(parent) < max_nodes:
        y = q.popleft()
        nxt = []
        if y.startswith("code:"):
            nxt += [(a, "← " + rel) for rel, a, cat in g.inn.get(y, []) if cat in (CALLS, IMPL, DEP)]
        elif not y.startswith(("check:", "H:")):
            nxt += [(a, "← " + rel) for rel, a, cat in g.inn.get(y, []) if cat in (DEP, SOURCE)]
            if y == start:
                nxt += [(b, rel + " →") for rel, b, cat in g.out.get(y, []) if cat == IMPL]
            nxt += [(b, rel + " →") for rel, b, cat in g.out.get(y, []) if cat == CHECK]
        for x, rel in nxt:
            if x not in parent:
                parent[x] = (y, rel)
                q.append(x)
    return parent


def why(g, start, target):
    """The chain of links by which a change of start reaches target (or None): the explanation of one impact."""
    parent = impact_walk(g, start)
    if target not in parent:
        return None
    path, x = [], target
    while parent[x] is not None:
        prev, rel = parent[x]
        path.append((prev, rel, x))
        x = prev
    return list(reversed(path))


def claim_binding(st, rep):
    """The place a traced claim is presented by (its first binding of the PRESENTATION stage): where the backward
    reconstruction starts (screen → binding → estimand → definitions → sources, code and checks)."""
    for s in rep["stages"]:
        for l in s["links"]:
            if l["relation"] == "presented_by" and l["target"] != "?":
                return l["target"].split(",")[0]
    return rep["claim"].split()[0]


def _groups(g, start, nodes):
    groups = defaultdict(list)
    for n in nodes:
        groups[kind_of(n)].append(n)
    return dict(changed=start, groups=[dict(group=k, members=sorted(v)) for k, v in sorted(groups.items())],
                unresolved=sorted(n for n in nodes if n not in g.nodes))


def check_impact(g, reports):
    """IMPACT: for every traced claim, the reverse closure of its question, outcome and case-set rule contains the claim's
    estimand and its presentation binding (lineage and impact close on each other)."""
    v, n = [], 0
    for rep in reports:
        est = rep["claim"].split()[0]
        e = C.get(est) or {}
        targets = {est} | {l["target"] for s in rep["stages"] if s["stage"] == "PRESENTATION" for l in s["links"] if l["relation"] == "presented_by" for _ in [0]}
        targets = {t for x in targets for t in x.split(",")} - {"?"}
        for d in [e.get("question"), e.get("q5_outcome")] + list(e.get("q4_case_set") or [])[:1]:
            if not d:
                continue
            n += 1
            imp = {m for gr in impact(g, d)["groups"] for m in gr["members"]}
            miss = sorted(t for t in targets if t not in imp)
            if miss:
                v.append(_viol("IMPACT_INCOMPLETE", ["0.1 §15"], f"changing {d} does not reach {miss}", rep["id"]))
    return _result("IMPACT", not v, n, v)


# =====================================================================================================================
# the accepted line: BASE-24 and NOW-1.0 recomputed by the code of the accepted commit
# =====================================================================================================================
ACCEPTED_MODULES = ("lab/scene24.py", "lab/scene21.py", "lab/zonemap24.py", "lab/now24.py", "lab/now24_validate.py", "lab/build_boxes.py", "lab/build_market.py", "lab/live.py")
_REF_SCRIPT = r'''
import json, sys
from pathlib import Path
tmp, runtime, scenes = Path(sys.argv[1]), Path(sys.argv[2]), json.loads(sys.argv[3])
sys.path.insert(0, str(tmp / "lab"))
import scene21, scene24, now24, contract as C
scene21.RUNTIME = runtime; scene24.RUNTIME = runtime; now24.RUNTIME = runtime
out = {}
for s in scenes:
    h, m = s["at"].split(":"); at = int(h) * 60 + int(m)
    view = "conf" + (":all" if s["all"] else "")
    if s["route"] == "/api/d24/family": body = scene24.family(s["inst"], s["block"], at, s["date"], view)
    else: body = now24.live(s["inst"], s["block"], at, s["date"], view)
    body = C.finalize(s["route"], body)
    out[s["id"]] = dict(status=(body.get("contract") or {}).get("status"), stale=C.stale(), bundles=(body.get("contract") or {}).get("bundles") or [])
print(json.dumps(out, ensure_ascii=False))
'''


def check_accepted_identity(st, scene_list, runtime=None):
    """ACCEPTED-CODE-IDENTITY: (1) the modules computing BASE-24 / NOW-1.0 compared with the accepted commit, and the
    functions of lab/contract.py that differ named; (2) the declared BASE / NOW scenes recomputed by the accepted
    commit's own code (git archive into a temporary folder, the same session base, a separate process) give the same
    bundles as this line, the versions of the registry and of the code aside (they differ between lines by design)."""
    ref = next((s["line"]["commit"] for s in st["cat"]["standings"] if s["profile_key"] == "BASE-24"), None)
    code = CodeIndex()
    v, det = [], dict(accepted_commit=ref)
    same, differ = [], []
    for f in ACCEPTED_MODULES:
        old = git("show", f"{ref}:{f}", binary=True)
        cur = (ROOT / f).read_bytes() if (ROOT / f).exists() else None
        (same if old is not None and cur is not None and old.replace(b"\r\n", b"\n") == cur.replace(b"\r\n", b"\n") else differ).append(f)
    det.update(modules_identical=same, modules_differ=differ)
    old_c = git("show", f"{ref}:lab/contract.py", binary=True)
    if old_c is not None:
        oi = CodeIndex(Path(tempfile.mkdtemp(prefix="drlab-trace-src-")))
        (oi.root / "lab").mkdir(parents=True)
        (oi.root / "lab" / "contract.py").write_bytes(old_c)
        new_f, old_f = code.py("lab/contract.py")["funcs"], oi.py("lab/contract.py")["funcs"]
        det["contract_functions_changed"] = sorted(q for q in new_f if q in old_f and code.source("lab/contract.py", q) != oi.source("lab/contract.py", q))
        det["contract_functions_added"] = len([q for q in new_f if q not in old_f])
        shutil.rmtree(oi.root, ignore_errors=True)
    runtime = Path(runtime or (LAB / ".runtime")).resolve()
    tmp = Path(tempfile.mkdtemp(prefix="drlab-trace-accepted-"))
    try:
        arch = git("archive", ref, "lab", "contract", "spec", binary=True)
        if arch is None:
            v.append(_viol("NO_ACCEPTED_CODE", ["INV-12"], "git archive of the accepted commit failed", ref))
            return _result("ACCEPTED-CODE-IDENTITY", False, 0, v, det)
        with tarfile.open(fileobj=io.BytesIO(arch)) as tf:
            tf.extractall(tmp, filter="data")
        args = [dict(id=s["id"], route=s["route"].split(":", 1)[1], inst=s["instrument"], block=s["block"], date=s["trading_date"], at=s["at_clock_et"], all=s["scope"] == "ALL_WEEKDAYS") for s in scene_list]
        r = subprocess.run([sys.executable, "-B", "-c", _REF_SCRIPT, str(tmp), str(runtime), json.dumps(args)], capture_output=True, text=True, encoding="utf-8", timeout=600,
                           env=dict(os.environ, PYTHONUTF8="1"))
        if r.returncode != 0:
            v.append(_viol("ACCEPTED_RUN", ["INV-12"], (r.stderr or r.stdout)[-400:], ref))
            return _result("ACCEPTED-CODE-IDENTITY", False, 0, v, det)
        old = json.loads(r.stdout)
        cmp = []
        for s in scene_list:
            _clear_caches()
            body = compute(s)
            mine = sorted((norm_bundle(b, cross_line=True) for b in (body.get("contract") or {}).get("bundles") or []), key=digest)
            theirs = sorted((norm_bundle(b, cross_line=True) for b in old[s["id"]]["bundles"]), key=digest)
            nums = lambda xs: sorted(digest({k: x[k] for k in ("estimand", "parameters", "estimates", "supports", "admissible_claims")} | {"claim_class": x["claim"]["claim_class"], "claim_form": x["claim_form"]}) for x in xs)
            words = lambda xs: sorted(digest({"estimand": x["estimand"], "parameters": x["parameters"], "statement": x["claim"]["statement_ru"]}) for x in xs)
            row = dict(scene=s["id"], bundles=len(mine), accepted_bundles=len(theirs), accepted_status=old[s["id"]]["status"], accepted_stale=old[s["id"]]["stale"],
                       numbers_identical=nums(mine) == nums(theirs), words_identical=words(mine) == words(theirs), identical=mine == theirs)
            cmp.append(row)
            if not row["numbers_identical"] or row["accepted_status"] != "CONFORMANT":
                v.append(_viol("ACCEPTED_DIFFERS", ["INV-12", "PROC-20"], f"{s['id']}: the accepted code gives other numbers (or no conformant answer)", s["id"]))
        det["scenes"] = cmp
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return _result("ACCEPTED-CODE-IDENTITY", not v, len(scene_list), v, det)


# =====================================================================================================================
# the counterexamples: six kinds of broken dependencies, each must be detected at its place
# =====================================================================================================================
def counterexamples(st, g, code, static, base_reports=None, reps=None):
    """Every counterexample tampers a copy (or patches the production code in memory) and runs the very check that must
    catch it; detected = the check FAILS and names the place; the claim's report is not reliable."""
    sc = scenes(st)
    out = []

    def add(cid, kind, tamper, res, report=None):
        bad = [x for x in res["violations"] if x["severity"] == "BLOCKING"]
        out.append(dict(id=cid, kind=kind, tamper=tamper, check=res["check"], detected=res["outcome"] == "FAIL" and bool(bad),
                        where=[x["where"] for x in bad][:3], codes=sorted({x["code"] for x in bad}),
                        reliable_after=None if report is None else report["assessment"]["reliable"]))

    arr = sc["SCENE:ARRIVE-HALF"]
    _clear_caches()
    body = compute(arr)
    bundle = pick_bundle(body, arr["estimand"], arr["selector"])
    # 1 · changed label: one member's outcome flipped in the answer (counts left as they were)
    b1 = copy.deepcopy(body)
    pl = next(p for p in b1["places"] if p["level"] == "-1/2")
    k = next(i for i, m in enumerate(pl["members"]) if m[1] == "YES")
    pl["members"][k] = [pl["members"][k][0], "NO"]
    rep1, _ = trace_scene(st, g, arr, body=b1, mutations=False, static=static)
    add("CX-1a", "изменённая метка исхода", f"members[{k}] YES → NO в ответе «Отсюда» −1/2", check_bundle_counts(arr, b1, pick_bundle(b1, arr["estimand"], arr["selector"])), rep1)
    fam, bars, tick = family_of(arr)
    gate_errs = C.verify_arrive(b1, fam, bars, tick)
    out.append(dict(id="CX-1b", kind="изменённая метка исхода", tamper="тот же ответ через эталон шлюза (lab/contract.py::verify_arrive)", check="GATE (verify_arrive)",
                    detected=bool(gate_errs), where=[f"place {x}" for x in gate_errs][:3], codes=["ARRIVE_RECOMPUTATION"] if gate_errs else [], reliable_after=None))
    # 2 · broken reference: an estimand pointing at an outcome that does not exist; an outcome of a missing issue
    st2 = dict(st, reg=copy.deepcopy(st["reg"]))
    e2 = next(e for e in st2["reg"]["estimands"] if e["id"] == "EST:K-ARRIVE")
    e2["q5_outcome"] = "OUT:REACH-REST-9"
    g2, _ = build_graph(st2, code)
    add("CX-2a", "нарушенная ссылка", "EST:K-ARRIVE.q5_outcome → OUT:REACH-REST-9 (несуществующий исход)", check_refs(st2, g2, code)[0])
    if reps:
        rep_t = copy.deepcopy(next(r for r in reps if r["outcomes"]))
        oid = next(iter(rep_t["index"]["outcomes"]))
        rep_t["index"]["outcomes"][oid]["issue"] = "0" * 64
        v = [_viol("OUTCOME_WITHOUT_ISSUE", ["R15"], f"outcome {oid[:16]} links to a missing issue", f"{rep_t['store']}/outcome {oid[:16]}")
             for o in rep_t["index"]["outcomes"].values() if o["issue"] not in rep_t["index"]["issues"]]
        add("CX-2b", "нарушенная ссылка", "исход Q1 ссылается на отсутствующий выпуск (копия индекса хранилища)", _result("Q1-STORE", not v, 1, v))
    # 3 · mismatched denominator: the support's n and the estimate's denominator
    b3 = copy.deepcopy(body)
    bb = pick_bundle(b3, arr["estimand"], arr["selector"])
    bb["supports"][0]["n_match"] += 1
    next(e for e in bb["estimates"] if e["value_kind"] == "BOUNDS")["denominator"] += 1
    rep3, _ = trace_scene(st, g, arr, body=b3, mutations=False, static=static)
    add("CX-3", "несовпадающий знаменатель", "bundle K-ARRIVE −1/2: n_match + 1 и знаменатель границ + 1", check_bundle_counts(arr, b3, bb), rep3)
    # 4 · forbidden future: production code patched in memory to read the target's future, then the analogues'
    import numpy as np
    import now24
    from q1 import engine as Q
    orig, orig_ts = now24.today_path, Q.Table.target_state

    def leaky_ts(self, i, c, level):
        st_ = orig_ts(self, i, c, level)
        if st_.get("status") == "OPEN" and self.P.shape[0] == 1:          # today's one-case table: its LAST close
            seen = np.flatnonzero(~np.isnan(self.P[i][:, 2]))
            if len(seen):
                st_ = dict(st_, close_v=int(self.P[i][seen[-1], 2]))
        return st_
    now24.today_path = lambda bars_, grid, tick_, d, e_px, cut: orig(bars_, grid, tick_, d, e_px, grid[-1])
    Q.Table.target_state = leaky_ts
    try:
        add("CX-4a", "запрещённое будущее", "сегодняшний путь открыт после среза (now24.today_path) и «Отсюда» сравнивает аналоги с последним закрытием дня, а не со срезом", check_future_target(arr))
    finally:
        now24.today_path, Q.Table.target_state = orig, orig_ts
        _clear_caches()
    orig_sel = Q.Table.select

    def leaky(self, par, cs, level, cl_t, w_t):
        m = dict(orig_sel(self, par, cs, level, cl_t, w_t))
        m["match"] = m["match"] & ~m["reach"]
        return m
    Q.Table.select = leaky
    try:
        add("CX-4b", "запрещённое будущее", "Table.select отбрасывает аналоги, которые потом дошли (отбор по будущей метке)", check_future_members(arr))
    finally:
        Q.Table.select = orig_sel
        _clear_caches()
    # CX-4c · specifically falsify a selector that reads a FUTURE CLOSE (not only a future wick/label).
    # Capture the first observed close after the cut as the deliberately forbidden reference.
    # With the old wicks-only mutation, the leaky selector stayed unchanged and this check went green.
    import arrive24
    fam_close, _, _ = family_of(arr)
    table_close = arrive24.family_table(fam_close)
    cut_close = (minute(arr["at_clock_et"]) - fam_close["schedule"]["formed"] - 5) // 5
    original_future_closes = {}
    for j, sid in enumerate(table_close.ids):
        tail = table_close.P[j, cut_close + 1:, 2]
        observed = np.flatnonzero(np.isfinite(tail))
        if observed.size:
            k = cut_close + 1 + int(observed[0])
            original_future_closes[sid] = (k, float(table_close.P[j, k, 2]))

    def leaky_future_close(self, par, cs, level, cl_t, w_t):
        m = dict(orig_sel(self, par, cs, level, cl_t, w_t))
        # An intentionally invalid future-dependent selector: membership hinges on a
        # post-cut CLOSE equalling the reference captured from the unmodified future.
        # The captured value makes the negative control deterministic on real sessions.
        keep = np.ones(len(par), dtype=bool)
        for row, j in enumerate(par):
            witness = original_future_closes.get(self.ids[int(j)])
            if witness is not None:
                k, close0 = witness
                keep[row] = bool(np.isfinite(self.P[int(j), k, 2]) and self.P[int(j), k, 2] == close0)
        m["match"] = m["match"] & keep[:, None]
        return m

    Q.Table.select = leaky_future_close
    try:
        add("CX-4c", "запрещённое будущее",
            "Table.select читает будущее CLOSE после среза для отбора (контроль против wicks-only)",
            check_future_members(arr))
    finally:
        Q.Table.select = orig_sel
        _clear_caches()
    # CX-4d · a selector reading an analogue's STORED future attribute (its DR break in the base), not its candles: caught
    # only because the replacement re-derives the stored break (rederive_future_attributes); without it the stored break
    # stays as it was and the leak passes.
    import scene21

    def leaky_stored_break(self, par, cs, level, cl_t, w_t):
        m = dict(orig_sel(self, par, cs, level, cl_t, w_t))
        B_ = scene21._boxes(arr["instrument"])
        keep = np.ones(len(par), dtype=bool)
        for row, j in enumerate(par):
            _, date_, block_ = _sid_parts(self.ids[int(j)])
            i = B_["idx"].get((date_, block_))
            keep[row] = i is None or B_["boxes"][i]["fail"] is None
        m["match"] = m["match"] & keep[:, None]
        return m

    Q.Table.select = leaky_stored_break
    try:
        add("CX-4d", "запрещённое будущее",
            "Table.select отбирает аналоги, у которых DR потом не сломался, по сохранённому в базе слому (fail)",
            check_future_members(arr))
    finally:
        Q.Table.select = orig_sel
        _clear_caches()
    # 5 · wrong claim profile: the C1 answer published as a C0 statement of a base family; a C2 claim
    b5 = copy.deepcopy(body)
    bb5 = pick_bundle(b5, arr["estimand"], arr["selector"])
    bb5["claim"]["claim_class"] = C.C0
    bb5["claim_form"] = "CF:B-ZONE-R"
    rep5, _ = trace_scene(st, g, arr, body=b5, mutations=False, static=static)
    add("CX-5a", "неправильный профиль утверждения", "bundle K-ARRIVE с классом C0 и формой CF:B-ZONE-R", check_bundle_claim(st, "/api/d24/arrive", b5, bb5), rep5)
    b5b = copy.deepcopy(body)
    bb5b = pick_bundle(b5b, arr["estimand"], arr["selector"])
    bb5b["claim"]["claim_class"] = C.C2
    add("CX-5b", "неправильный профиль утверждения", "bundle K-ARRIVE с классом PredictiveClaim (C2)", check_bundle_claim(st, "/api/d24/arrive", b5b, bb5b))
    # 6 · missing source evidence: a bundle without its observation input; a catalog check that does not exist
    b6 = copy.deepcopy(body)
    bb6 = pick_bundle(b6, arr["estimand"], arr["selector"])
    bb6["derivation"]["inputs"] = [i for i in bb6["derivation"]["inputs"] if i["input_kind"] != "OBSERVATION_SNAPSHOT"]
    rep6, _ = trace_scene(st, g, arr, body=b6, mutations=False, static=static)
    miss = [l for s in rep6["stages"] for l in s["links"] if l["mandatory"] and l["status"] == "MISSING"]
    out.append(dict(id="CX-6a", kind="отсутствие исходных свидетельств", tamper="bundle K-ARRIVE без входа OBSERVATION_SNAPSHOT", check="trace report (обязательная связь)",
                    detected=bool(miss) and not rep6["assessment"]["reliable"], where=[f"{l['source']} —{l['relation']}→ {l['target']}" for l in miss][:3],
                    codes=["BROKEN_LINK"] if miss else [], reliable_after=rep6["assessment"]["reliable"]))
    st6 = dict(st, cat=copy.deepcopy(st["cat"]))
    ent = next(e for e in st6["cat"]["entries"] if e["id"] == "A08")
    ent["checked_by"] = list(ent["checked_by"]) + ["test:tests/no_such_test.py::proof"]
    g6, _ = build_graph(st6, code)
    add("CX-6b", "отсутствие исходных свидетельств", "запись A08 ссылается на несуществующую проверку", check_refs(st6, g6, code)[2])
    # the screen: words and the bound number, when a collected state is at hand
    if base_reports and base_reports.get("screens"):
        scr = copy.deepcopy(base_reports["screens"].get(arr["page_fragment"]))
        if scr:
            el = next(e for e in scr["elements"] if e["block"] == "ARRIVE" and json.loads(e.get("parameters") or "{}").get("level") == "-1/2")
            el["label_ok"] = False
            el["shown_value"] = "41%"
            add("CX-1c", "изменённая метка на экране", "элемент «Отсюда» −1/2: другие слова и другое число", check_screen(st, arr, scr, bundle, body)[0])
    return out


# =====================================================================================================================
# everything, with the evidence written
# =====================================================================================================================
IMPACT_EXAMPLES = ("OUT:REACH-REST-1", "CMP:K-POS-1", "OUT:ZONE-MEMBERSHIP-1", "OUT:NEW-R-1", "code:lab/now24.py::_near")


def run_all(out_dir=None, screens=False, accepted=True, mutations=True, work=None):
    t0 = time.time()
    st = load()
    reasons = stale_reasons(st)
    static_list, g, code = static_checks(st)
    static = {c["check"]: c for c in static_list}
    q1res, reps = check_q1_stores(st["spec"])
    sc = scenes(st)
    shots = {}
    if screens:
        work = Path(work or tempfile.mkdtemp(prefix="drlab-trace-screens-"))
        frags = sorted({s["page_fragment"] for s in sc.values()})
        raw = collect_screens(frags, work)
        for f, r in raw.items():
            shots[f] = ingest_screen(r, [s["id"] for s in sc.values() if s["page_fragment"] == f])
    reports, extras = [], {}
    for sid, s in sc.items():
        rep, ex = trace_scene(st, g, s, screen=shots.get(s["page_fragment"]), reps=reps, mutations=mutations, static=static)
        reports.append(rep)
        extras[sid] = ex
    imp = check_impact(g, reports)
    acc = check_accepted_identity(st, [s for s in sc.values() if s["profile_key"] in ("BASE-24", "NOW-1.0")]) if accepted else None
    cx = counterexamples(st, g, code, static, base_reports=dict(screens=shots), reps=reps)
    summary = dict(version=VERSION, generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), seconds=round(time.time() - t0, 1),
                   stale=reasons, artifact_versions=artifact_versions(st),
                   static=[{k: c[k] for k in ("check", "outcome", "checked")} | dict(violations=c["violations"][:20], details=c["details"]) for c in static_list],
                   q1_store={k: q1res[k] for k in ("outcome", "checked")} | dict(details=q1res["details"], violations=q1res["violations"][:20]),
                   impact={k: imp[k] for k in ("outcome", "checked", "violations")},
                   accepted_identity=None if acc is None else {k: acc[k] for k in ("outcome", "checked", "violations", "details")},
                   scenes=[dict(scene=r["scene"], claim=r["claim"], assessment=r["assessment"], stages={s["stage"]: s["status"] for s in r["stages"]},
                                checks={c["check"]: dict(outcome=c["outcome"], checked=c["checked"], details=c["details"]) for c in extras[r["scene"]]["checks"]},
                                violations=len(r["violations"])) for r in reports],
                   counterexamples=cx, screens={f: dict(elements=len(s["elements"]), violations=len(s["page_violations"]), unchecked=s["unchecked_passports"],
                                                        page_build_sha256=s["page_build_sha256"][:16]) for f, s in shots.items()})
    if out_dir:
        out_dir = Path(out_dir)
        for sub in ("scenes", "screens", "impact", "lineage"):
            (out_dir / sub).mkdir(parents=True, exist_ok=True)
        dump = lambda p, obj: Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        dump(out_dir / "run.json", summary)
        for r in reports:
            dump(out_dir / "scenes" / (r["scene"].split(":", 1)[1].lower() + ".json"), r)
        for f, s in shots.items():
            dump(out_dir / "screens" / (re.sub(r"[^a-z0-9]+", "-", f.lower()).strip("-") + ".json"), s)
        for name in IMPACT_EXAMPLES:
            dump(out_dir / "impact" / (re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-") + ".json"), impact(g, name))
        for r in reports:
            dump(out_dir / "lineage" / (r["scene"].split(":", 1)[1].lower() + ".json"), lineage(g, claim_binding(st, r)))
        (out_dir / "coverage.md").write_text(coverage_md(st, static, reports, summary), encoding="utf-8", newline="\n")
    return summary, reports, dict(static=static_list, g=g, shots=shots)


def coverage_md(st, static, reports, summary):
    """The consolidated, evidence-linked map: every catalog entry with its realisation and the status of its checks in
    this run (generated; never edited by hand)."""
    ran = {c["check"]: c["outcome"] for c in summary["static"]}
    for s in summary["scenes"]:
        for k, v in s["checks"].items():
            ran[k] = "PASS" if ran.get(k, "PASS") == "PASS" and v["outcome"] == "PASS" else "FAIL"
    if summary.get("q1_store"):
        ran["Q1-STORE"] = summary["q1_store"]["outcome"]
    if summary.get("impact"):
        ran["IMPACT"] = summary["impact"]["outcome"]
    if summary.get("accepted_identity"):
        ran["ACCEPTED-CODE-IDENTITY"] = summary["accepted_identity"]["outcome"]
    lines = ["# Покрытие архитектуры 0.1 / 0.2 — сгенерировано `python -B lab/semtrace.py run`", "",
             f"Прогон {summary['generated_utc']} · " + " · ".join(f"{a['artifact']} {a['version'][:16]}" for a in summary["artifact_versions"][:4]), "",
             "Статус проверки — результат ЭТОГО прогона (`trace:`), запуск существующих тестов (`test:`) — их собственными командами; "
             "`reported:` — отчёт исполнителя без повтора; `human:` — человеческий акт, машиной не заменяется.", "",
             "| ID | Что | Решение | Реализовано | Проверки этого прогона | Прочие проверки | Границы |", "|---|---|---|---|---|---|---|"]
    for e in st["cat"]["entries"]:
        tr = [c for c in e.get("checked_by") or [] if c.startswith("trace:")]
        other = [c for c in e.get("checked_by") or [] if not c.startswith("trace:")]
        tr_s = ", ".join(f"{c[6:]} {ran.get(c[6:], 'не запускалась')}" for c in tr) or "—"
        lines.append(f"| {e['id']} | {e['title_ru']} | {e['decision']} | {', '.join(e.get('realized_by') or [])[:120]} | {tr_s} | {', '.join(other)[:140] or '—'} | {', '.join(e.get('boundaries') or []) or '—'} |")
    lines += ["", "## Границы, не объявленные закрытыми", "", "| ID | Вид | Что | Чей ход |", "|---|---|---|---|"]
    for b in st["cat"]["boundaries"]:
        lines.append(f"| {b['id']} | {b['boundary_kind']} | {b['title_ru']} | {b['owner_ru']} |")
    lines += ["", "## Сквозные сцены", "", "| Сцена | Утверждение | Решение | Модель | Реализация | Показ (машина) | Показ (человек) | Достоверно в заявленной области |", "|---|---|---|---|---|---|---|---|"]
    for s in summary["scenes"]:
        a = s["assessment"]
        lines.append(f"| {s['scene']} | {s['claim']} | {a['decision']} | {a['model_definiteness']} | {a['implementation']} | {a['presentation_machine']} | {a['presentation_human']} | {'да' if a['reliable'] else 'нет'} |")
    return "\n".join(lines) + "\n"


# =====================================================================================================================
# the readable report (Russian: the semantic layer's language)
# =====================================================================================================================
STAGE_RU = {"OBSERVATION": "наблюдение", "STATE": "состояние", "QUESTION": "вопрос", "CASE_SET": "набор", "OUTCOMES": "исходы", "COMPUTATION": "расчёт",
            "ESTIMATE_SUPPORT": "оценка и опора", "ADMISSION": "допуск", "PRESENTATION": "представление", "ISSUE": "выпуск"}
STATUS_RU = {"VERIFIED": "проверено", "IMPLEMENTED_UNVERIFIED": "реализовано, не проверено", "PROPOSED": "предложено", "MISSING": "отсутствует", "NOT_APPLICABLE": "неприменимо"}


def render(rep):
    a = rep["assessment"]
    out = [f"{rep['id']} · {rep['claim']}",
           f"  решение: {a['decision']} · модель: {a['model_definiteness']} · реализация: {a['implementation']} · показ (машина): {a['presentation_machine']} · показ (человек): {a['presentation_human']}",
           f"  достоверно в заявленной области: {'ДА' if a['reliable'] else 'НЕТ'}"]
    for s in rep["stages"]:
        out.append(f"  [{STATUS_RU[s['status']]:>26}] {STAGE_RU[s['stage']]}: {s['summary_ru']}")
        for l in s["links"]:
            out.append(f"      {'*' if l['mandatory'] else ' '} {l['source']} —{l['relation']}→ {l['target']}  ({STATUS_RU[l['status']]}; {l['evidence']}{'; ' + l['note'] if l.get('note') else ''})")
    for o in rep["operations"]:
        out.append(f"  операция {o['operation']}: {'была' if o['performed'] else 'не было'} · {o['evidence']} · {o['not_implied_ru']}")
    for v in rep["violations"]:
        out.append(f"  НАРУШЕНИЕ {v['code']} [{', '.join(v['arch_ref'])}] {v['where']}: {v['message']}")
    return "\n".join(out)


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="DR Lab — the executable semantic trace")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    p = sub.add_parser("scene")
    p.add_argument("scene")
    p.add_argument("--json")
    p.add_argument("--no-mutations", action="store_true")
    p.add_argument("--no-q1", action="store_true")
    for name in ("impact", "lineage"):
        p = sub.add_parser(name)
        p.add_argument("node")
    p = sub.add_parser("why")
    p.add_argument("changed")
    p.add_argument("affected")
    sub.add_parser("q1")
    sub.add_parser("counterexamples")
    p = sub.add_parser("run")
    p.add_argument("--out")
    p.add_argument("--screens", action="store_true")
    p.add_argument("--no-accepted", action="store_true")
    a = ap.parse_args(argv)
    st = load()
    for r in stale_reasons(st):
        print("  STALE", r)
    if a.cmd == "check":
        res, g, _ = static_checks(st)
        for c in res:
            print(f"  {c['outcome']:4} {c['check']:<18} {c['checked']:>5}  {TRACE_CHECKS[c['check']]}")
            for v in c["violations"][:8]:
                print(f"         {v['code']} {v['where']}: {v['message']}")
            if c["details"]:
                print("         " + json.dumps(c["details"], ensure_ascii=False)[:400])
        print(f"  graph: {len(g.nodes)} nodes, {sum(len(x) for x in g.out.values())} links")
        return 0 if all(c["outcome"] == "PASS" for c in res) else 1
    if a.cmd == "why":
        g, _ = build_graph(st)
        path = why(g, a.changed, a.affected)
        if path is None:
            print(f"  a change of {a.changed} does not reach {a.affected}")
            return 1
        for prev, rel, x in path:
            print(f"  {prev}  {rel}  {x}")
        return 0
    if a.cmd in ("impact", "lineage"):
        g, _ = build_graph(st)
        r = impact(g, a.node) if a.cmd == "impact" else lineage(g, a.node)
        if a.node not in g.nodes:
            print(f"  {a.node}: no such node")
            return 1
        for gr in r["groups"]:
            print(f"  {gr['group']} ({len(gr['members'])}): " + ", ".join(gr["members"][:40]) + (" …" if len(gr["members"]) > 40 else ""))
        return 0
    if a.cmd == "q1":
        res, reps = check_q1_stores(st["spec"])
        print(f"  {res['outcome']} Q1-STORE {res['checked']} records · " + json.dumps(res["details"], ensure_ascii=False))
        for v in res["violations"][:10]:
            print(f"         {v['code']} {v['where']}: {v['message']}")
        return 0 if res["outcome"] == "PASS" else 1
    if a.cmd == "scene":
        res, g, _ = static_checks(st)
        static = {c["check"]: c for c in res}
        reps = None if a.no_q1 else check_q1_stores(st["spec"])[1]
        rep, _ = trace_scene(st, g, scenes(st)[a.scene], reps=reps, mutations=not a.no_mutations, static=static)
        print(render(rep))
        if a.json:
            Path(a.json).write_text(json.dumps(rep, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        return 0 if rep["assessment"]["reliable"] else 1
    if a.cmd == "counterexamples":
        res, g, code = static_checks(st)
        static = {c["check"]: c for c in res}
        cx = counterexamples(st, g, code, static, reps=check_q1_stores(st["spec"])[1])
        for x in cx:
            print(f"  {'ok  ' if x['detected'] else 'MISS'} {x['id']} {x['kind']}: {x['tamper']} → {x['check']} {x['codes']} {x['where'][:2]}")
        return 0 if all(x["detected"] for x in cx) else 1
    if a.cmd == "run":
        summary, reports, _ = run_all(a.out, screens=a.screens, accepted=not a.no_accepted)
        for r in reports:
            print(render(r))
            print()
        print(json.dumps({k: summary[k] for k in ("seconds", "stale")}, ensure_ascii=False))
        ok = all(c["outcome"] == "PASS" for c in summary["static"]) and all(s["assessment"]["reliable"] for s in summary["scenes"]) and all(x["detected"] for x in summary["counterexamples"])
        return 0 if ok else 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
