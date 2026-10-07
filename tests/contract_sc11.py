"""DR-LAB-SC-1.1 conformance of the machine contract and of its integration with the server and the page.

    python -B tests/contract_sc11.py          (the operator's Python with numpy / pandas; LinkML parts run in .venv-linkml)

Part 1, the contract's own artifacts: the products equal what their sources produce (contract/tools/build.py --check
in the LinkML environment) and carry the SHA-256 of every source, the document among them; every check named by the
enforcement map of §14.4 exists; the examples K01-K33 carry the document's own words; every card of the document is
represented by the schema or the registry or named by a coverage note; the enums that mirror the document's lists hold
its tokens; every registry object is structurally valid for the runtime validator.
Part 2, K01-K33 executed on the reference definitions (lab/contract.py) and the working code (lab/scene24.py,
lab/zonemap24.py, lab/now24.py): synthetic paths in integer ticks; K05, K08, K26-K28, K30, K31 on the session base
(lab/.runtime/boxes_*; aggregates only, nothing written).
Part 3, integration: every route of lab/server.py is declared and marked; real responses of the SC-1.1 routes carry
structurally valid envelopes (the runtime validator here, LinkML in a temporary folder) and no undeclared number; a
stale contract publishes no statistic; the page embeds the registry it was built from and renders only registered
words. Exit code 0 = all good. A green run proves these predicates, not the truth of the questions (§14.4).
"""
import copy
import hashlib
import inspect
import json
import os
import re
import subprocess
import sys
import tempfile
from fractions import Fraction as Q
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lab"))
import contract as C  # noqa: E402
import now24 as N  # noqa: E402
import scene24 as S  # noqa: E402
import zonemap24 as Z  # noqa: E402

DOC = ROOT / "spec" / "DR-LAB-Semantic-Contract-1.1-(patched).md"
BUILD = ROOT / "contract" / "build"
VENV = ROOT / ".venv-linkml" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
failures = []


def check(cond, msg):
    print(("  ok  " if cond else "  FAIL ") + msg)
    if not cond: failures.append(msg)


REG = C.registry()
SPEC = json.loads((BUILD / "runtime_spec.json").read_text(encoding="utf-8"))
PAGE = json.loads((BUILD / "page_registry.json").read_text(encoding="utf-8"))
DOC_TEXT = DOC.read_text(encoding="utf-8")


# =====================================================================================================================
# synthetic material (integer ticks; RDR: box 09:30-10:30, f = 630, block end E = 960)
# =====================================================================================================================
F_, E_ = 630, 960
GRID = list(range(F_ + 5, E_ + 1, 5))
J = {T: j for j, T in enumerate(GRID)}


def path_of(rows, fill=None):
    """rows: {close minute: (low_u, high_u, close_u)} -> a path on the common clock grid (None = a missing M5)."""
    return [list(rows[T]) if T in rows else (list(fill) if fill is not None else None) for T in GRID]


def box_bars(extra):
    """A synthetic RDR day in prices [open minute, o, h, l, c]: DR 90-110 from two wicks, IDR 95-105, then `extra`."""
    out = []
    for i, t in enumerate(range(570, 630, 5)):
        o, c = (95.0, 105.0) if i % 2 == 0 else (105.0, 95.0)
        out.append([t, o, 110.0 if i == 3 else 106.0, 90.0 if i == 7 else 94.0, c])
    return out + extra


def base_of(days):
    """A synthetic session base (the structure of lab/.runtime/boxes_*) from {date: bars in prices}, tick 0.25."""
    tk = lambda p: int(round(p / 0.25))
    boxes, rows, off = [], [], [0]
    for date, bars in days.items():
        rr = [[int(b[0]) + 5, tk(b[1]), tk(b[2]), tk(b[3]), tk(b[4])] for b in bars]
        box = [r for r in rr if 575 <= r[0] <= 630]
        d = dict(session="RDR", weekday=int(pd.Timestamp(date).weekday()), date=date, dr_high=max(r[2] for r in box), dr_low=min(r[3] for r in box),
                 idr_high=max(max(r[1], r[4]) for r in box), idr_low=min(min(r[1], r[4]) for r in box))
        conf = side = fail = None
        for r in rr:
            if r[0] <= 630: continue
            if r[4] > d["dr_high"]: conf, side = r[0], 1; break
            if r[4] < d["dr_low"]: conf, side = r[0], -1; break
        if conf is not None:
            opp = d["dr_low"] if side == 1 else d["dr_high"]
            fail = next((r[0] for r in rr if r[0] > conf and side * (r[4] - opp) < 0), None)
        d.update(conf=conf, side=side, fail=fail)
        boxes.append(d); rows += rr; off.append(len(rows))
    return dict(boxes=boxes, bars=np.array(rows, dtype=np.int64), off=off, info=dict(boxes=len(boxes)))


# =====================================================================================================================
# part 1: the contract's own artifacts
# =====================================================================================================================
def test_pins_and_products():
    reg = json.loads((BUILD / "registry.json").read_text(encoding="utf-8"))
    st = reg["stamps"]
    bad = [rel for rel, want in st["sources"].items() if C.sha256_lf(ROOT / rel) != want]
    check(not bad, f"every source of the compiled contract has its stamped SHA-256 ({len(st['sources'])} sources){': ' + str(bad) if bad else ''}")
    ed = next(e for e in REG["editions"] if e["id"] == "DR-LAB-SC-1.1")
    check(ed["document_sha256_lf"] == C.sha256_lf(DOC) == st["document_sha256_lf"], "the registry pins DR-LAB-SC-1.1 at the document's SHA-256 (LF)")
    check(PAGE["registry_hash"] == st["registry_sha256"][:16] == C.registry_hash(), "the page registry carries the compiled registry's hash")
    d24 = (ROOT / "lab" / "dist" / "24" / "d24.js").read_text(encoding="utf-8")
    check((BUILD / "page_registry.json").read_text(encoding="utf-8").strip() in d24 and "/*__SC11__*/" not in d24, "the built page embeds exactly the current page registry")
    if VENV.exists():
        r = subprocess.run([str(VENV), str(ROOT / "contract" / "tools" / "build.py"), "--check"], capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONUTF8="1"))
        check(r.returncode == 0 and "IN SYNC" in r.stdout, "contract/tools/build.py --check: lint, closed-world validation, references, semantic checks; the products equal what the sources produce" + ("" if r.returncode == 0 else ": " + (r.stdout + r.stderr)[-600:]))
    else:
        print("  ..  .venv-linkml absent: build.py --check not run (the stamps above still pin every source)")


def test_registry_structure():
    slots = SPEC["classes"]["Registry"]["slots"]
    errs, n = [], 0
    for coll, items in REG.items():
        if not isinstance(items, list): continue
        cls = slots[coll]["range"]
        for it in items:
            n += 1
            errs += [f"{coll}: {e}" for e in C.validate(it, cls)]
    check(not errs, f"{n} registry objects structurally valid for the runtime validator (classes of the LinkML schema){': ' + '; '.join(errs[:4]) if errs else ''}")


def _check_exists(ref):
    kind, _, rest = ref.partition(":")
    if kind == "human": return rest in ("operator",)
    if kind == "schema": return rest in SPEC["classes"]
    if kind == "test" and "#" in rest:
        f, _, mark = rest.partition("#")
        return (ROOT / f).exists() and f"[{mark}]" in (ROOT / f).read_text(encoding="utf-8")
    f, _, name = rest.partition("::")
    p = ROOT / f
    if not p.exists(): return False
    if not name: return True
    src = p.read_text(encoding="utf-8")
    if f.endswith(".py") and f.startswith("tests/"): return callable(globals().get(name))
    if f == "lab/contract.py": return hasattr(C, name)
    if f.endswith(".js"):
        both = src + ((ROOT / "design/sozvezdiya-24/src/panel.js").read_text(encoding="utf-8") if f.endswith("app.js") else "")
        return re.search(r"function " + re.escape(name) + r"\(", both) is not None
    return re.search(r"def " + re.escape(name) + r"\(", src) is not None


def test_enforcement_map():
    obs, ex = REG.get("obligations", []), REG.get("examples", [])
    missing = [(o["id"], e["check"]) for o in obs for e in o["enforcement"] if not _check_exists(e["check"])]
    missing += [(k["id"], c) for k in ex for c in k["checks"] if not _check_exists(c)]
    check(obs and not missing, f"§14.4: {len(obs)} obligations and {len(ex)} examples name only checks that exist{': ' + str(missing[:6]) if missing else ''}")
    human_only = [o["id"] for o in obs if all(e["mechanism"] == "HUMAN_ACCEPTANCE" or e["check"].startswith("schema:") for e in o["enforcement"])]
    check(human_only == ["OB:HUMAN-ACCEPTANCE"] and all(o.get("residual_ru") for o in obs if o["id"] in human_only), "only the human acts are enforced by a human and the record says so")
    mech = {e["mechanism"] for o in obs for e in o["enforcement"]}
    check(mech == {"STRUCTURAL_SCHEMA", "PATH_COMPUTATION", "PROVENANCE_RECONCILIATION", "STATISTICAL_CHECK", "HUMAN_ACCEPTANCE"}, "all five mechanisms of §14.4 are used, each where it applies")


def test_examples_verbatim():
    rows = re.findall(r"^\| (K\d\d) \| (.+?) \| (.+?) \|$", DOC_TEXT, flags=re.M)
    ex = {k["id"]: k for k in REG.get("examples", [])}
    bad = [k for k, s, e in rows if k not in ex or ex[k]["situation_ru"] != s.strip() or ex[k]["expected_ru"] != e.strip()]
    check(len(rows) == 33 and len(ex) == 33 and not bad, f"the registry's K01-K33 carry the document's words verbatim{': ' + str(bad) if bad else ''}")
    check(all(f"test:tests/contract_sc11.py::{k.lower()}" in ex[k]["checks"] for k, _, _ in rows), "every example K01-K33 is executed by its own check below")


def test_coverage():
    cards = re.findall(r"^#{3,4} ((?:O|S|M|E|H|P|T|V|C|D)\d(?:\.\d)?)\. ", DOC_TEXT, flags=re.M)
    refs = set()

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k == "sc_ref": refs.update(v if isinstance(v, list) else [v])
                else: walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(REG)
    schema_text = (ROOT / "contract" / "schema" / "dr_lab_sc.yaml").read_text(encoding="utf-8")
    for m in re.findall(r'sc_ref:\s*"([^"]+)"', schema_text): refs.update(t.strip() for t in re.split(r"[;,]", m))
    notes = {n["clause"] for n in REG.get("coverage_notes", [])}
    lost = [c for c in cards if c not in refs and c not in notes]
    check(len(cards) >= 40 and not lost, f"every card of the document ({len(cards)}) is represented by the schema or the registry or named by a coverage note{': ' + str(lost) if lost else ''}")
    for cl in ("C2", "C3", "D0", "D1", "D2"):
        check(cl in notes, f"{cl} is named by a coverage note (defined, not instantiated in this edition)")


def test_enums_match_document():
    enums = SPEC["enums"]

    def holds(tokens, what):
        in_doc = all(t in DOC_TEXT for t in tokens)
        e = [n for n, vals in enums.items() if set(tokens) <= set(vals)]
        check(in_doc and e, f"{what}: the document's tokens {'/'.join(tokens)} are one enum of the schema ({e[0] if e else 'none'})")
    holds(["R_BEFORE_X", "X_BEFORE_R", "SAME_M5", "UNKNOWN", "NO_PERIOD"], "P0.2 order of the first R and X")
    holds(["BROKEN", "HELD", "UNKNOWN", "NO_PERIOD"], "P0.2 DR outcome")
    holds(["HOLDS", "POSSIBLE", "IMPOSSIBLE"], "E3 reachability")
    holds(["FUTURE_PRESENT", "FUTURE_EMPTY", "PAST_ONLY"], "E4 history clock")
    names = re.findall(r"^### C\d\. [^`]+`([A-Za-z]+)`", DOC_TEXT, flags=re.M)
    check(names == ["DescriptiveClaim", "ConditionalDescriptiveClaim", "PredictiveClaim", "DecisionClaim"] and all(n in SPEC["classes"] for n in names),
          "C0-C3: the four claim kinds of the document are four classes of the schema")


# =====================================================================================================================
# part 2: K01-K33
# =====================================================================================================================
def k01():
    check(C.ref_window(660, F_) == 1 and C.ref_window(665, F_) == 2 and S.window_of(660, F_) == 1 and S.window_of(665, F_) == 2,
          "K01 the M5 10:55-11:00 is in the window 10:45-11:00, the next one in 11:00-11:15 (by the open minute; reference and scene24)")
    bars = box_bars([[630, 100, 104, 99, 103], [635, 103, 105, 101, 104], [640, 104, 106, 102, 105], [645, 105, 107, 103, 106], [650, 106, 109, 104, 108], [655, 108, 112, 107, 111]])
    before, at = C.today_state(bars, "RDR", 659, 659, False, 0.25), C.today_state(bars, "RDR", 660, 660, False, 0.25)
    check(before["conf"] is None and at["conf"] == 660, "K01 the confirmation is known only at its close (none at 10:59, at 11:00 yes)")


def k02():
    eq = box_bars([[630, 100, 115, 99, 110.0], [635, 109, 110, 104, 106]])
    st = box_bars([[630, 100, 115, 99, 110.0], [635, 109, 111, 108, 110.25]])
    a, b = C.today_state(eq, "RDR", 700, 700, False, 0.25), C.today_state(st, "RDR", 700, 700, False, 0.25)
    check(a["conf"] is None and b["conf"] == 640 and b["side"] == 1, "K02 a wick beyond DR and a close equal to DR confirm nothing; a strictly beyond close does")
    eqb = st + [[640, 108, 109, 89, 90.0], [645, 92, 95, 91, 94]]
    stb = st + [[640, 108, 109, 89, 90.0], [645, 90, 91, 88, 89.75]]
    a, b = C.today_state(eqb, "RDR", 700, 700, False, 0.25), C.today_state(stb, "RDR", 700, 700, False, 0.25)
    check(a["brk"] is None and b["brk"] == 650, "K02 a close equal to the opposite DR is no break; strictly beyond is")
    B = base_of({"2025-01-01": stb})
    d = C.derive_base("SYN", B, "RDR")[0]
    check((d["conf"], d["side"], d["fail"]) == (640, 1, 650), "K02 the session base is re-derived by the same rule (derive_base)")


def k03():
    rows = {640: (-50, 5, 0), 645: (-10, 8, 2), 650: (-20, 9, 3)}
    p = path_of(rows, fill=(-5, 5, 0))
    r = C.ref_final_extreme(p, GRID, 640, E_, "R")
    srows = {T: (T, c, h, l, c) for T, (l, h, c) in rows.items()}
    srows.update({T: (T, 0, 5, -5, 0) for T in GRID if T not in rows})
    m = S.measure(srows, 640, E_, 1, 0)
    check(r["s"] == "known" and r["v"] == -20 and m["R"]["v"] == -20, "K03 the depth of the activating M5 is not in R (reference and scene24.measure: R = -20, not -50)")


def k04():
    rows = {T: (-5, 5, 0) for T in GRID}
    rows[E_] = (-30, 5, 0)
    p = path_of(rows)
    srows = {T: (T, c, h, l, c) for T, (l, h, c) in rows.items()}
    srows[E_ + 5] = (E_ + 5, 0, 5, -90, 0)                       # opens at H: the next block
    r, m = C.ref_final_extreme(p, GRID, 640, E_, "R"), S.measure(srows, 640, E_, 1, 0)
    check(r["v"] == -30 and m["R"]["v"] == -30 and r["t"] == E_ - 5, "K04 the M5 closing at H is in the block, the one opening at H is not")


def k05():
    rule = C.get("RULE:DRIDR-24-1")
    adr = next(b for b in rule["blocks"] if b["block"] == "ADR")
    tf = C.get("TF:ET-M5-1")
    check(adr["trading_date_offset_days"] == 1 and "America/New_York" in tf["dst_rule"], "K05 the registry: ADR belongs to the next trading date; DST through the zone")
    eve_est, eve_edt = pd.Timestamp("2025-03-06 19:30", tz="America/New_York"), pd.Timestamp("2025-03-10 19:30", tz="America/New_York")
    u1, u2 = eve_est.tz_convert("UTC"), eve_edt.tz_convert("UTC")
    check((u1.hour, u1.minute, u2.hour, u2.minute) == (0, 30, 23, 30) and str(u2.date()) == "2025-03-10", "K05 19:30 ET is 00:30 UTC in winter and 23:30 UTC in summer: no fixed offset; the UTC date of the 03-10 evening is 03-10")
    B = S._base("NQ")
    if B is None: print("  ..  K05 base check skipped: no session base"); return
    i7, i11, i10 = B["idx"].get(("2025-03-07", "ADR")), B["idx"].get(("2025-03-11", "ADR")), B["idx"].get(("2025-03-10", "ADR"))
    first = lambda i: int(B["bars"][B["off"][i]][0])
    check(None not in (i7, i11, i10) and first(i7) == first(i11) == -265 + adr["history_minute_shift"], "K05 the ADR boxes on both sides of the DST switch start at the same ET minute (19:30 the evening before)")
    check(B["boxes"][i10]["weekday"] == 0 and ("2025-03-09", "ADR") not in B["idx"] and ("2025-03-08", "ADR") not in B["idx"],
          "K05 the Sunday-evening ADR belongs to Monday's trading date; Saturday and Sunday are not trading dates")


def _real(inst, session, at, date, view="auto"):
    fam = S.family(inst, session, at, date, view)
    day = S.day_view(inst, date)
    return fam, day["bars"], float(day.get("tick") or 0.25)


def k06():
    e, w = 440, 40                                              # IDR [100, 110] in ticks of 0.25, long: edge = IDR high
    lo, hi, c = C.ref_directed((0, 432, 428, 430), 1, e)
    mlo, mhi, mc = C.ref_directed((0, -428, -432, -430), -1, -e)   # the mirrored short: IDR [-110, -100], edge = IDR low
    check(Q(c, w) == Q(-1, 4) and (lo, hi, c) == (mlo, mhi, mc) and lo <= hi, "K06 107.5 in IDR [100, 110] long is u = -0.25; the reflected short gives the same u; low_u <= high_u")


def k07():
    check(C.ref_cell(-1, 100) == -1 and C.ref_cell(0, 100) == 0 and Z.cell_of(-1, 100, 640, F_)[0] == -1, "K07 u = -0.01 is in cell -1, not 0 (reference and zonemap24.cell_of)")


def k08():
    fam, bars, tick = _real("NQ", "RDR", 690, "2025-12-17")
    if fam.get("status") != "ok": print("  ..  K08 skipped: no family"); return
    alt = [b if b[0] + 5 <= 690 else [b[0], b[1] * 1.03, b[2] * 1.05, b[3] * 0.97, b[4] * 0.98] for b in bars]
    a, b = C.ref_now_sets(fam, bars, tick, 690), C.ref_now_sets(fam, alt, tick, 690)
    pa, pb = N.payload(fam, bars, tick), N.payload(fam, alt, tick)
    ta, tb = C.today_state(bars, "RDR", 690, 690, False, tick), C.today_state(alt, "RDR", 690, 690, False, tick)
    check(json.dumps(a, default=str) == json.dumps(b, default=str) and json.dumps(pa, sort_keys=True) == json.dumps(pb, sort_keys=True) and (ta["conf"], ta["brk"]) == (tb["conf"], tb["brk"]),
          "K08 replacing every candle of today after the cut changes neither the prefix, the eligible set, the matchers nor the NOW response at the cut")


def k09():
    pre = {T: (-3, 3, 0) for T in GRID if T <= 700}
    p1, p2 = path_of({**pre, **{T: (-4, 4, 0) for T in GRID if T > 700}}), path_of({**pre, **{T: (-40, 4, 0) for T in GRID if T > 700}})
    a, c = (640 - F_ - 5) // 5, (700 - F_ - 5) // 5
    check(C.ref_prefix(p1, a, c) == C.ref_prefix(p2, a, c) and C.ref_final_extreme(p1, GRID, 640, E_, "R") != C.ref_final_extreme(p2, GRID, 640, E_, "R"),
          "K09 a new tail after t changes the outcome, never the prefix or the eligibility at t")
    fam, _, _ = _real("NQ", "RDR", 690, "2025-12-17")
    raw, B, _ = S._family("NQ", "RDR", 690, "2025-12-17")
    forged = copy.deepcopy(raw)
    m = next(x for x in forged["members"] if x["R"]["s"] == "known")
    m["R"]["v"] -= 1                                               # a silent rewrite of a stored measurement
    v, _ = C.verify_snapshot("NQ", B, forged)
    check({"IDENTITY", "OUTCOME"} <= {x[0] for x in v}, "K09 a stored BASE snapshot rewritten under its old id is rejected: identity (the id binds the measurements) and outcome")


def k10():
    rows = {T: (-2, 2, 0) for T in GRID}
    p = path_of(rows)
    c = (710 - F_ - 5) // 5                                     # the common clock cut 11:50
    a1, a2 = (635 - F_ - 5) // 5, (645 - F_ - 5) // 5             # confirmations 10:35 and 10:45
    s1, s2 = p[a1 + 1:c + 1], p[a2 + 1:c + 1]
    check(C.ref_prefix(p, a1, c) is not None and C.ref_prefix(p, a2, c) is not None and len(s1) - len(s2) == 2 and GRID[c] == 710,
          "K10 both cases are read at their own 11:50; their ages differ by two M5")


def k11():
    good = box_bars([[630, 100, 104, 99, 103], [635, 103, 112, 102, 111]])
    gap = box_bars([[635, 103, 112, 102, 111]])                    # the M5 10:30-10:35 missing before the observed confirmation
    B = base_of({"2025-01-01": good, "2025-01-08": gap})
    mem, journal, errs = C.ref_family("SYN", B, "RDR", 2, 1, "conf", 0, "2026-01-01", "weekday")
    check([i for i, _, _ in mem] == [0] and journal.get("confirmation_undetermined") == 1 and journal.get("confirmation_undetermined_could_be_this_window") == 1 and not errs,
          "K11 a gap before the first observed confirmation: the key is not guessed, the case goes to the journal of undetermined keys")


def k12():
    rows = {T: (-2, 2, 0) for T in GRID}
    del rows[700]
    p = path_of(rows)
    r = C.ref_final_extreme(p, GRID, 640, E_, "R")
    a = (640 - F_ - 5) // 5
    check(r["s"] == "unknown" and r.get("bound") == -2, "K12 a gap after a sure activation: the final R is UNKNOWN (an observed bound kept), the case stays in N")
    check(C.ref_prefix(p, a, J[695]) is not None and C.ref_prefix(p, a, J[710]) is None, "K12 NOW admits the case only with its whole prefix to the cut")


def k13():
    rows = {T: (-2, 2, 0) for T in GRID}
    rows[700] = (-2, 9, 0); del rows[800]
    p = path_of(rows)
    check(C.ref_reach(p, GRID, 640, E_, 5, 1, 1, True) == "yes" and C.ref_final_extreme(p, GRID, 640, E_, "X")["s"] == "unknown",
          "K13 an observed reach is YES despite another missing M5; the final X stays UNKNOWN")
    check(C.ref_reach(p, GRID, 640, E_, 50, 1, 1, True) == "unknown", "K13 no reach on an incomplete path is UNKNOWN, never NO")


def k14():
    rows = {T: (-2, 2, 0) for T in GRID}
    del rows[700]; rows[720] = (-30, 0, -25)
    cat, brk, known_t = C.ref_dr_outcome(path_of(rows), GRID, 640, E_, -20)
    check((cat, brk, known_t) == ("broken", 720, False), "K14 a break seen after a gap: BROKEN, its first time not known")


def k15():
    at_h = C.ref_final_extreme(path_of({}), GRID, E_, E_, "R")
    none_seen = C.ref_final_extreme(path_of({}), GRID, 640, E_, "R")
    check(at_h["s"] == "none" and none_seen["s"] == "unknown", "K15 an activation at H has NO_PERIOD; all M5 after the activation missing is UNKNOWN")
    check(C.ref_first_order(at_h, at_h) == "no_period" and C.ref_first_order(none_seen, none_seen) == "unknown" and S.measure({}, E_, E_, 1, 0)["order"] == "no_period" and S.measure({}, 640, E_, 1, 0)["order"] == "unknown",
          "K15 the order keeps NO_PERIOD apart from UNKNOWN (reference and scene24.measure)")


def k16():
    lo, hi = C.est_binary_bounds(3, 5, 2)
    check((lo, hi) == (Q(3, 10), Q(1, 2)) and Q(3, 8) != lo, "K16 N = 10, 3 YES, 5 NO, 2 UNKNOWN: the share of the whole set is [30 %, 50 %]; 37.5 % is of the 8 known only")
    bounded = sorted(e for e, f in PAGE["forms"].items() if f["value_form"] == "BOUNDS_IF_UNKNOWN")
    check(bounded == ["EST:B-CROSS-FULL", "EST:B-LEVEL-FULL", "EST:B-LEVEL-REST", "EST:B-VISIT-FULL", "EST:B-VISIT-REST"], "K16 the binary shares of the page are shown as bounds when unknown mass exists (value form of their claim forms)")


def k17():
    check(C.est_count_over_n(5, 25) == Q(1, 5) and C.est_count_over_n(2, 25) == Q(2, 25), "K17 N = 25: the band 5 points = 20 %, its time window 2 = 8 %")
    b, r = PAGE["forms"]["EST:B-RX-BAND-R"]["labels"], PAGE["forms"]["EST:B-RX-REGION-R"]["labels"]
    check(b["area_row"]["ANY"] != r["area_row"]["ANY"] and "окн" in r["area_row"]["ANY"], "K17 the band's and the window's shares carry their own words: 20 % never labels the smaller contour")


def k18():
    rows = {T: (-2, 2, 0) for T in GRID}
    rows[700] = (-12, 2, 0); rows[760] = (-12, 30, 0)
    p = path_of(rows)
    r = C.ref_final_extreme(p, GRID, 640, E_, "R")
    check(C.ref_visit(p, GRID, 640, E_, -2, -1, 10) == "yes" and C.ref_visit(p, GRID, 640, E_, 2, 3, 10) == "yes" and r["ties"] == [695, 755] and r["t"] == 695,
          "K18 two bands visited are two YES; the repeated final R is one vote with its first and repeated times kept apart")


def _fam(members):
    return dict(grid=GRID, schedule=dict(formed=F_, end=E_), N=len(members), members=members, zones={})


def _mem(i, R=None, X=None):
    ev = lambda t: dict(s="known", v=-5, t=t, ties=[t]) if t is not None else dict(s="known", v=-5, t=900, ties=[900])
    return dict(id=f"M{i}", w=10, act=640, path=path_of({T: (-5, 5, 0) for T in GRID}), R=ev(R), X=ev(X))


def k19():
    ms = [_mem(0, R=645, X=645), _mem(1, R=650), _mem(2, X=650), _mem(3, X=655)] + [_mem(i) for i in range(4, 10)]
    fam = _fam(ms)
    pp = lambda y: dict(id=1, estimand="EST:B-RX-DIFF", params=dict(k0=None, k1=None, b0=1, b1=2), yes_count=y, unknown_count=0, no_event_count=0, N=10)
    nX = sum(1 for m in ms if (m["X"]["t"] - F_) // 15 == 1); nR = sum(1 for m in ms if (m["R"]["t"] - F_) // 15 == 1)
    both = sum(1 for m in ms if (m["X"]["t"] - F_) // 15 == 1 or (m["R"]["t"] - F_) // 15 == 1)
    check((nX, nR, both) == (3, 2, 4) and C.verify_passports(fam, [], 0.25, [pp(1)]) == [] and C.verify_passports(fam, [], 0.25, [pp(5)]) != [],
          "K19 N = 10, two R and three X in one window, one session both: the difference is 10 p.p.; the sum 50 % is not the 40 % of sessions with any event")


def k20():
    R = dict(s="known", v=-9, t=700, ties=[700, 760]); X = dict(s="known", v=9, t=720, ties=[720, 780])
    d = C.ref_order_detail(R, X)
    check(C.ref_first_order(R, X) == "R_before_X" and d["x_again_after_r"] and not d["all_r_before_all_x"], "K20 the first R was before the first X, and X repeats after R: checked apart, no trade route follows")


def k21():
    R = dict(s="known", v=-9, t=700, ties=[700]); X = dict(s="known", v=9, t=700, ties=[700])
    check(C.ref_first_order(R, X) == "same_M5", "K21 R and X in one M5: SAME_M5, the order inside the candle is unknown")


def k22():
    rows = {T: (-5, 5, 0) for T in GRID}
    rows[700] = (12, 20, 15)                                      # a gap: the whole M5 above L = 1.0 (w = 10, L = 10)
    p = path_of(rows)
    check(C.ref_reach(p, GRID, 640, E_, 1, 1, 10, True) == "yes" and C.ref_cross(p, GRID, 640, E_, 1, 1, 10) == "no", "K22 a gap past L: «on L or beyond» YES without a literal crossing")


def k23():
    c = J[700]
    tie = path_of({T: ((-10, 0, -5) if T > 700 else (-10, 0, -5)) for T in GRID})
    deeper = path_of({T: ((-11, 0, -5) if T == 760 else (-10, 0, -5)) for T in GRID})
    a, b = C.ref_residual(tie, c, -10, "R"), C.ref_residual(deeper, c, -10, "R")
    check(a["new"] == "NO" and a["delta"] == 0 and a["tau_s"] == "NO_EVENT" and b["new"] == "YES" and b["delta"] == 1 and b["tau"] == J[760] - c,
          "K23 a tail repeating r_seen is no new R; one tick deeper is; delta and tau carry their own knowledge")
    holed = copy.deepcopy(deeper); holed[J[740]] = None
    h = C.ref_residual(holed, c, -10, "R")
    check(h["new"] == "YES" and h["delta"] is None and h["tau_s"] == "UNKNOWN", "K23 with a hole before it: YES stands, delta and tau become unknown")


def k24():
    w, q = 10, (-1, 0)                                            # r_seen = -1 tick of 10: u = -0.1, cell [-0.1, 0) in window 0
    check(C.ref_reachability([[-1, 0]], "R", q, -10, w, 800, F_, E_ - 5) == "HOLDS", "K24 the region holding today's extreme stays HOLDS after its window passed")


def k25():
    cells = [[-3, 10], [-3, 11]]
    check(C.ref_reachability(cells, "R", (-1, 0), -10, 10, 700, F_, E_ - 5) == "POSSIBLE" and C.ref_history_clock(cells, [650, 660], 700, F_, E_ - 5) == "FUTURE_EMPTY",
          "K25 a zone logically possible with no historical event after t: POSSIBLE and FUTURE_EMPTY together")
    check("cut" not in inspect.signature(Z.evaluate).parameters, "K25 the zone's share never depends on the cut (zonemap24.evaluate takes no cut)")


def k26():
    f = S.family("NQ", "RDR", 960, "2025-12-10", "conf")
    if f.get("status") != "ok" or f["today"].get("brk") is None: print("  ..  K26 skipped: no break day"); return
    brk = f["today"]["brk"]
    before, kept, broke = S.family("NQ", "RDR", brk - 5, "2025-12-10"), S.family("NQ", "RDR", brk + 30, "2025-12-10", "conf"), S.family("NQ", "RDR", brk + 30, "2025-12-10")
    check(before["view"] == kept["view"] == "conf" and before["snapshot_id"] == kept["snapshot_id"] and broke["view"] == "brk" and broke["snapshot_id"] != kept["snapshot_id"],
          "K26 after today's break the break family is another snapshot; the original stays the same snapshot")
    check(broke["key"]["event"] == "break" and "outcome" not in broke["counts"] and broke["contract"]["frame"]["spec"] == "MF:BREAK-1" and kept["contract"]["frame"]["spec"] == "MF:CONFIRMATION-1",
          "K26 the break family has its own N, its own scale and no DR-outcome share")


def k27():
    fam = S.family("ES", "ADR", -40, "2025-11-05")
    now = N.live("ES", "ADR", -40, "2025-11-05")
    if fam.get("status") != "ok": print("  ..  K27 skipped"); return
    nb = [b["estimand"] for b in now["contract"].get("bundles", [])]
    check(fam["N"] < 20 and fam["contract"]["status"] == "CONFORMANT" and any(b["estimand"] == "EST:B-RX-JOINT-R" for b in fam["contract"]["bundles"]),
          f"K27 the base family of {fam['N']} cases is published with its shares")
    check(all((now.get(ev) or {}).get("mode") == "INSUFFICIENT_SUPPORT" and not (now.get(ev) or {}).get("continuation") for ev in ("R", "X")) and not any(e.startswith("EST:N-NEW") for e in nb),
          "K27 NOW's own support limit withholds its number without hiding the base")


def k28():
    fam, bars, tick = _real("NQ", "RDR", 700, "2025-12-17")
    raw = N.payload(fam, bars, tick)
    forged = copy.deepcopy(raw)
    forged["R"].update(mode="PATH_CONDITIONED", matcher="M1")
    forged["R"].setdefault("validation", {})["status"] = "NOT_VALIDATED"
    out = C.attach_now(forged, fam, bars, tick, {})
    check(any(v["code"] == "CLAIM_NOT_ADMISSIBLE" for v in out["contract"]["violations"]) and out["R"]["mode"] == "WITHHELD", "K28 a path forecast without its passed validation is not published")
    e1 = C.get("VAL:NOW-E1-EXPLORATION")
    check(e1["lifecycle"] == "HYPOTHESIS" and not REG.get("predictive_admissions") and "PredictiveClaim" not in C.admissible_claims("EST:N-NEW-R", "CS:NOW-MATCH-M1-1"),
          "K28 E1 stays a research hypothesis; nothing is promoted to a predictive claim")


def k29():
    check(C.ref_quantile([0, 0, Q(1, 5), Q(2, 5)], 0.5) == Q(1, 10) and C.ref_quantile([Q(1, 5), Q(2, 5)], 0.5) == Q(3, 10), "K29 the median of all known deltas 0.1, of those with a new extreme 0.3: two quantities, two supports")


def k30():
    fam = S.family("NQ", "RDR", 690, "2025-12-17")
    alg = C.get("ALG:ZONE-MAP-3")
    zs = [(ev, z) for ev in ("R", "X") for z in (fam.get("zones") or {}).get(ev, {}).get("zones", [])]
    ok = all(z["zone_id"] == hashlib.sha1("|".join(map(str, (fam["snapshot_id"], ev, tuple(z["peak_anchor"]), alg["version"]))).encode()).hexdigest()[:12] for ev, z in zs)
    check(zs and ok and list(inspect.signature(Z.evaluate).parameters) == ["snap", "e"], "K30 a zone's identity binds snapshot, event, apex and algorithm version; no drawing parameter is an input")


def k31():
    raw, B, day = S._family("NQ", "RDR", 690, "2025-12-17")
    forged = copy.deepcopy(raw)
    grid, formed = forged["grid"], forged["schedule"]["formed"]
    for m in forged["members"]:                                   # R «from visits»: the low of the first M5 after the activation
        j = next((j for j, T in enumerate(grid) if T > m["act"] and m["path"][j]), None)
        if j is None or m["R"]["s"] != "known": continue
        m["R"] = dict(s="known", v=m["path"][j][0], t=grid[j] - 5, ties=[grid[j] - 5])
    cells = {}
    for m in forged["members"]:
        if m["R"]["s"] == "known":
            k = (C.ref_cell(m["R"]["v"], m["w"]), (m["R"]["t"] - formed) // 15); cells[k] = cells.get(k, 0) + 1
    forged["counts"]["R"]["cells"] = sorted([k, b, n] for (k, b), n in cells.items())
    env = C.Envelope("/api/d24/family", "PROFILE:BASE-24", {})
    c = forged["counts"]["R"]
    b = env.bundle("EST:B-RX-JOINT-R", "CS:F-CONF-1", forged["snapshot_id"], "forged", C._inputs(forged), [dict(estimator="ESTR:JOINT-CELLS-1", value_kind="DISTRIBUTION", unit="cells", denominator=forged["N"],
                   cells=[dict(price_cell=k, time_cell=t, count=n) for k, t, n in forged["counts"]["R"]["cells"]])], [dict(case_set=forged["snapshot_id"], n_base=forged["N"], components=[dict(component="ENDPOINT", of=forged["N"], known=sum(cells.values()), unknown=c["unknown"], no_period=c["none"])])], {})
    check(b is not None and C.validate(b, "StatisticalResultBundle") == [], "K31 a FINAL_R table computed from visits is structurally valid")
    out = C.attach_family(forged, "NQ", B, day, {})
    codes = {v["code"] for v in out["contract"]["violations"]}
    check(out["status"] == "contract_violation" and "OUTCOME" in codes and "members" not in out, "K31 the semantic gate rejects it: the reference recomputes R from the path and withholds the family")


def k32():
    bad = [(e["id"], cs) for e in REG["estimands"] for cs in e["q4_case_set"] if C.admissible_claims(e["id"], cs) & {"PredictiveClaim", "DecisionClaim"}]
    check(not bad and not REG.get("policies") and not REG.get("authorities"), "K32 no policy and no authority: no estimand admits a decision (or a forecast) anywhere")

    # Future guard: SC-1.1 stays closed even if an unrelated/generic record is accidentally added to the loaded
    # registry. A later edition must introduce an explicit target/case-set/evidence/policy/authority binding and change
    # the gate deliberately; mere record presence must never promote a historical number.
    old_pred, old_pol, old_auth = REG.get("predictive_admissions", []), REG.get("policies", []), REG.get("authorities", [])
    REG["predictive_admissions"] = [{"estimand": "EST:N-NEW-R", "validation": "VAL:NOW-1.0-WALKFORWARD"}]
    REG["policies"] = [{"id": "POL:FORGED"}]
    REG["authorities"] = [{"id": "AUTH:FORGED", "revoked": False}]
    try:
        c2 = C.admissible_claims("EST:N-NEW-R", "CS:NOW-ELIGIBLE-1")
        c3 = C.admissible_claims("EST:B-RX-BAND-R", "CS:F-CONF-1")
    finally:
        REG["predictive_admissions"], REG["policies"], REG["authorities"] = old_pred, old_pol, old_auth
    check("PredictiveClaim" not in c2 and "DecisionClaim" not in c3,
          "K32 future guard: generic admission / policy / authority records cannot silently open C2 or C3 in SC-1.1")

    real = C.claim_form_of
    C.claim_form_of = lambda e: dict(real(e), claim_class="DecisionClaim", id="CF:FORGED") if e == "EST:B-RX-BAND-R" else real(e)
    try:
        env = C.Envelope("/api/d24/family", "PROFILE:BASE-24", {})
        b = env.bundle("EST:B-RX-BAND-R", "CS:F-CONF-1", "x", "forged", [], [], [], {})
    finally:
        C.claim_form_of = real
    check(b is None and any(v["code"] == "CLAIM_NOT_ADMISSIBLE" for v in env.d["violations"]), "K32 a 80 % share under a decision claim is refused at publication")


def k33():
    check(C.admissible_claims("EST:N-NEW-R", "CS:NOW-ELIGIBLE-1") == {"ConditionalDescriptiveClaim"} and PAGE["forms"]["EST:N-NEW-R"]["claim_class"] == "ConditionalDescriptiveClaim",
          "K33 the NOW share admits C1 only, and its form is C1")
    future = re.compile(r"углуб[ия]тся|пойд[её]т|будет|если да")
    words = [t for e, f in PAGE["forms"].items() if e.startswith("EST:N-") for v in f["labels"].values() for t in v.values()]
    d24 = (ROOT / "lab" / "dist" / "24" / "d24.js").read_text(encoding="utf-8")
    src = (ROOT / "design/sozvezdiya-24/src/panel.js").read_text(encoding="utf-8")
    check(words and not any(future.search(t) for t in words) and not future.search(src) and "откат углубится" not in d24 and "если да:" not in d24,
          "K33 the NOW words are historical: no forecast grammar about today in the registry, the panel's source or the built page")


# =====================================================================================================================
# part 3: integration
# =====================================================================================================================
def test_routes_and_encodings():
    src = (ROOT / "lab" / "server.py").read_text(encoding="utf-8")
    routes = set(re.findall(r"'(/api/[A-Za-z0-9/_-]+)'", src)) - {"/api/"}
    declared = {s["route"]: s for s in REG["surfaces"]}
    check(routes == set(declared), f"every route of server.py is declared, and only those ({len(routes)}){': ' + str(sorted(routes ^ set(declared))) if routes != set(declared) else ''}")
    marks = {r: C.header_for(r) for r in declared}
    check(all(("status=OUTSIDE_SC11" in h) == (declared[r]["surface_profile"].startswith("LEGACY") or declared[r]["surface_profile"] == "SERVICE") for r, h in marks.items()),
          "every legacy and service route is marked OUTSIDE_SC11, every SC-1.1 route with its profile and registry")
    bodies = {"/api/d24/family": S.family("NQ", "RDR", 690, "2025-12-17"), "/api/d24/now": N.live("NQ", "RDR", 690, "2025-12-17"),
              "/api/d24/day": C.attach_day(S.day_view("NQ", "2025-12-17"), {}), "/api/d24/dates": S.dates("NQ")}
    bad = {r: C.undeclared_numbers(r, b) for r, b in bodies.items() if C.undeclared_numbers(r, b)}
    check(not bad, f"no number without a declared meaning in real responses of the four SC-1.1 routes{': ' + str(bad) if bad else ''}")
    legacy = [e for e in REG["estimands"] for s in REG["surfaces"] if s["surface_profile"].startswith("LEGACY") and e["id"] in (s.get("estimands") or [])]
    check(not legacy, "no SC-1.1 estimand is declared on a legacy route")


def test_live_envelopes():
    envs = {"family conf": S.family("NQ", "RDR", 690, "2025-12-17")["contract"], "family brk": S.family("NQ", "RDR", 900, "2025-12-10")["contract"],
            "family ODR": S.family("NQ", "ODR", 330, "2025-12-19")["contract"], "now": N.live("NQ", "RDR", 690, "2025-12-17")["contract"],
            "day": C.attach_day(S.day_view("NQ", "2025-12-17"), {})["contract"]}
    for name, e in envs.items():
        errs = C.validate(e, "ContractEnvelope")
        check(e["status"] == "CONFORMANT" and not errs and e["registry_hash"] == C.registry_hash(), f"{name}: the envelope is CONFORMANT and structurally valid ({len(e.get('bundles', []))} bundles){': ' + str(errs[:3]) if errs else ''}")
    if not VENV.exists():
        print("  ..  .venv-linkml absent: the LinkML validation of live envelopes not run"); return
    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for i, (name, e) in enumerate(envs.items()):
            f = Path(tmp) / f"env{i}.json"; f.write_text(json.dumps(e, ensure_ascii=False), encoding="utf-8"); files.append(str(f))
        code = ("import json,sys\nfrom linkml.validator import Validator\nfrom linkml.validator.plugins import JsonschemaValidationPlugin\n"
                f"v=Validator({str(ROOT / 'contract' / 'schema' / 'dr_lab_sc.yaml')!r}, validation_plugins=[JsonschemaValidationPlugin(closed=True)])\n"
                "n=0\nfor f in sys.argv[1:]:\n    r=v.validate(json.load(open(f,encoding='utf-8')),'ContractEnvelope'); n+=len(r.results)\n    [print(f, x.message[:200]) for x in r.results[:3]]\nprint('ERRORS', n)\n")
        r = subprocess.run([str(VENV), "-c", code] + files, capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONUTF8="1"))
        check(r.returncode == 0 and "ERRORS 0" in r.stdout, f"LinkML validates the {len(files)} live envelopes against ContractEnvelope (closed world, temporary folder)" + ("" if "ERRORS 0" in r.stdout else ": " + (r.stdout + r.stderr)[-500:]))


def test_stale_fails_closed():
    reg = json.loads((BUILD / "registry.json").read_text(encoding="utf-8"))
    first = next(iter(reg["stamps"]["sources"]))
    reg["stamps"]["sources"][first] = "0" * 64
    old = C.REGISTRY_FILE
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp) / "registry.json"
        t.write_text(json.dumps(reg, ensure_ascii=False), encoding="utf-8")
        C.REGISTRY_FILE = t; C._S["loaded"] = None; C._TTL["at"] = 0.0
        try:
            reasons = C.stale()
            body = C.stale_response("/api/d24/family", {})
            now = C.stale_response("/api/d24/now", {})
            check(reasons and body["status"] == "contract_stale" and body["contract"]["status"] == "CONTRACT_STALE" and "bundles" not in body["contract"] and "members" not in body and now["status"] == "CONTRACT_STALE",
                  "a source changed since the build makes the contract stale: no statistic is published")
            check("status=CONTRACT_STALE" in C.header_for("/api/d24/family"), "the stale state is marked on every SC-1.1 response")
        finally:
            C.REGISTRY_FILE = old; C._S["loaded"] = None; C._TTL["at"] = 0.0
    check(not C.stale(), "the compiled contract represents its sources again")
    src = (ROOT / "lab" / "server.py").read_text(encoding="utf-8")
    check("if url.path in ('/api/d24/family', '/api/d24/now') and contract.stale():" in src and src.index("contract.stale()") < src.index("if url.path in ('/api/d24/day'"),
          "the server answers the statistical routes from the stale gate before computing them; the day's observations are still served")


def test_page_contract():
    app = (ROOT / "design/sozvezdiya-24/src/app.js").read_text(encoding="utf-8")
    pnl = (ROOT / "design/sozvezdiya-24/src/panel.js").read_text(encoding="utf-8")
    both = app + pnl
    EV = r"(?:ev|h\.ev|r\.ev|e|I\.ev|g\.ev)"
    calls = re.findall(r"lbl\('((?:EST|FF):[A-Z0-9:-]+)', '([A-Za-z0-9_]+)'(?=\s*[,)])", both)
    dyn = re.findall(r"lbl\('(EST:[A-Z0-9-]+-)' \+ " + EV + r", '([A-Za-z0-9_]+)'(?=\s*[,)])", both)
    dkey = re.findall(r"lbl\('((?:EST|FF):[A-Z0-9:-]+)', '([A-Za-z0-9_]+_)' \+ " + EV, both)
    box = lambda i: PAGE["facts"].get(i) if i.startswith("FF:") else PAGE["forms"].get(i)
    lost = [(i, k) for i, k in calls if not box(i) or k not in box(i)["labels"]] + [(p + e, k) for p, k in dyn for e in "RX" if not box(p + e) or k not in box(p + e)["labels"]]
    lost += [(i, k + e) for i, k in dkey for e in "RX" if not box(i) or k + e not in box(i)["labels"]]
    n = len(calls) + len(dyn) + len(dkey)
    check(n > 80 and not lost, f"every label the page asks for by name ({n} calls) is registered{': ' + str(lost[:6]) if lost else ''}")
    texts = {t for f in list(PAGE["forms"].values()) + list(PAGE["facts"].values()) for v in f["labels"].values() for t in v.values() if "{" not in t and len(t) >= 14}
    written = sorted(t for t in texts if ("'" + t + "'") in both or (">" + t + "<") in both)
    check(not written, f"the page writes none of the registered words itself ({len(texts)} words checked){': ' + str(written[:5]) if written else ''}")
    for f in ("kViolate", "bindPassport", "envCounts", "regFault", "nowBundle", "verifyNow"):
        check(re.search(r"function " + f + r"\(", app) is not None, f"the page's contract layer has {f}")
    # every estimand id the page writes: literal ('EST:B-CLOSE') or an event's pair ('EST:B-ZONE-' + ev -> -R and -X)
    used = set()
    for name, plus in re.findall(r"'(EST:[A-Z0-9-]+)'(\s*\+\s*" + EV + r")?", both):
        if plus or name.endswith("-"): used.update({name + "R", name + "X"} if name.endswith("-") else {name})
        else: used.add(name)
    used.discard("EST:B-RX-R"); used.discard("EST:B-RX-X")         # 'EST:B-RX-' + (BAND | WINDOW | REGION) + '-' + ev: expanded below
    used.update(f"EST:B-RX-{k}-{e}" for k in ("BAND", "WINDOW", "REGION") for e in "RX")
    unreg = sorted(u for u in used if u not in PAGE["estimands"])
    check(used and not unreg, f"every estimand the page makes a passport of is registered ({len(used)}){': ' + str(unreg) if unreg else ''}")


# =====================================================================================================================
print("Part 1: the contract's own artifacts")
for t in (test_pins_and_products, test_registry_structure, test_enforcement_map, test_examples_verbatim, test_coverage, test_enums_match_document): t()
print("Part 2: the discriminating examples K01-K33")
for i in range(1, 34): globals()[f"k{i:02d}"]()
print("Part 3: integration with the server and the page")
for t in (test_routes_and_encodings, test_live_envelopes, test_stale_fails_closed, test_page_contract): t()
print()
print("ALL GOOD" if not failures else f"{len(failures)} FAILED")
sys.exit(1 if failures else 0)
