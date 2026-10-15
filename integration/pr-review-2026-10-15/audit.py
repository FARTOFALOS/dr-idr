"""Bounded PR source/unit reconciliation and semantic counterexamples, before main.

No PR changes, no merge, no working market-data changes. GitHub source metadata is
the separately saved API snapshot, not an invented authorization/acceptance record.
"""
from __future__ import annotations

import ast
import collections
import copy
import hashlib
from functools import lru_cache
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "lab"))
import continuity24 as E
import contract as C
from q1.engine import BaseProvider
from q1.store import canonical, sha


def git(*args, binary=False):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=not binary, encoding=None if binary else "utf-8")


@lru_cache(maxsize=None)
def blob(sha, path):
    p = subprocess.run(["git", "show", sha + ":" + path], cwd=ROOT, capture_output=True)
    return p.stdout if p.returncode == 0 else None


@lru_cache(maxsize=None)
def tree(sha):
    records = git("ls-tree", "-rz", sha, binary=True).split(b"\0")
    return {r.split(b"\t", 1)[1].decode("utf-8"): r.split(b"\t", 1)[0].split()[-1].decode("ascii")
            for r in records if r}


def h(data):
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest() if data is not None else None


def semantic_examples():
    grid = list(range(605, 666, 5))
    a = np.tile([-5., 5., 0.], (len(grid), 1))
    a[10] = [-100, 5, 0]
    a[11] = [-5, 100, 0]
    b = a.copy()
    a[5, 1], b[5, 1] = 60, 20
    frame = E.Frame("NQ", "2025-12-17", "RDR", 1, "100", "10", 605, 665)
    target = E.pin(frame, ".4", ".6", 625, 640, 620)
    paths = [a.tolist(), b.tolist()]
    extremes = [[C.ref_final_extreme(p, grid, 605, 665, ev) for ev in ("R", "X")] for p in paths]
    visits = [E.visit(dict(P=p, w=100), grid, target) for p in (a, b)]
    group_a, group_b = np.array([[0, 0], [1, 1]]), np.array([[0, 1], [1, 0]])
    columns = lambda group: [[int((group[:, j] == k).sum()) for k in (0, 1)] for j in (0, 1)]
    pairs = dict(equal_final_R_X_and_times=extremes[0] == extremes[1],
                 equal_full_close_paths=bool(np.array_equal(a[:, 2], b[:, 2])),
                 different_window_range_visits=visits,
                 equal_close_column_frequencies=columns(group_a) == columns(group_b),
                 ordered_A_then_B_counts=[int(((g[:, 0] == 0) & (g[:, 1] == 1)).sum()) for g in (group_a, group_b)],
                 origin="RUN_HERE_SYNTHETIC_COUNTEREXAMPLES")
    assert pairs["equal_final_R_X_and_times"] and pairs["equal_full_close_paths"]
    assert visits == ["YES", "NO"] and pairs["equal_close_column_frequencies"]
    assert pairs["ordered_A_then_B_counts"] == [0, 1]
    return pairs


def metadata_example(method=None):
    p = BaseProvider("NQ", "RDR")
    k = p.B["idx"][("2025-12-17", "RDR")]
    q = copy.copy(p)
    q.B = dict(p.B)
    q.B["boxes"] = list(p.B["boxes"])
    q.B["boxes"][k] = dict(p.B["boxes"][k])
    q.B["boxes"][k]["complete"] = not p.B["boxes"][k]["complete"]
    q._dig = {}
    prefix = method or BaseProvider.prefix_digest
    old, new = prefix(p, k, 0, 670), prefix(q, k, 0, 670)
    return dict(case="NQ/RDR/2025-12-17", cut="11:10", only_metadata_complete_changed=True,
                same_closed_prefix=bool(np.array_equal(p.bars(k)[p.bars(k)[:, 0] <= 670], q.bars(k)[q.bars(k)[:, 0] <= 670])),
                prefix_digest_changed=old != new, old=old, new=new,
                origin="RUN_HERE_REAL_PREFIX_IN_MEMORY_METADATA_COUNTERFACTUAL")


def main():
    source = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))
    units = json.loads((HERE / "units.json").read_text(encoding="utf-8"))["units"]
    prs = {p["number"]: p for p in source["pull_requests"]}
    old = json.loads((ROOT / "meaning/lens/2026-10-14-integration/sources.json").read_text(encoding="utf-8"))["refs"]
    current = git("rev-parse", source["candidate"]).strip()
    # Reproduce the finding with the actual frozen method, then check today's fix.
    original_engine = ast.parse(blob(current, "lab/q1/engine.py").decode("utf-8"))
    provider = next(n for n in original_engine.body if isinstance(n, ast.ClassDef) and n.name == "BaseProvider")
    method = next(n for n in provider.body if isinstance(n, ast.FunctionDef) and n.name == "prefix_digest")
    scope = dict(sha=sha, canonical=canonical)
    exec(compile(ast.Module(body=[method], type_ignores=[]), "frozen-prefix-method", "exec"), scope)
    original_metadata = metadata_example(scope["prefix_digest"])
    current_metadata = metadata_example()
    assert original_metadata["prefix_digest_changed"] and not current_metadata["prefix_digest_changed"]
    restored = json.loads((ROOT / "integration/restored-sources.json").read_text(encoding="utf-8"))
    for item in restored:
        assert h(blob(item["source"], item["path"])) == h((ROOT / item.get("destination", item["path"])).read_bytes()) == item["sha256_lf"]
    assert subprocess.run(["git", "merge-base", "--is-ancestor", current, "HEAD"], cwd=ROOT).returncode == 0
    assert set(prs) == set(range(2, 14))
    assert all(p["state"] == "open" and not p["merged"] for p in prs.values())
    for p in prs.values():
        assert git("cat-file", "-t", p["head_sha"]).strip() == "commit"
    assert all(p["head_sha"] in old.values() for p in prs.values())
    for n in prs:
        assert any(n in u["prs"] for u in units), "PR without semantic disposition: " + str(n)
    unit_evidence = []
    for u in units:
        for n in u["prs"]:
            assert blob(prs[n]["head_sha"], u["source_path"]) is not None, (u["id"], n, u["source_path"])
        dst = u["current_destination"]
        if dst:
            assert (ROOT / dst).is_file(), (u["id"], "missing destination", dst)
        original = blob(prs[u["prs"][0]]["head_sha"], u["source_path"])
        actual = (ROOT / dst).read_bytes() if dst else None
        unit_evidence.append(dict(unit=u["id"], source_sha256_lf=h(original), destination_sha256_lf=h(actual),
                                  byte_identical=actual is not None and h(actual) == h(original)))
    # Isolate the unique source line, not the public PR's inherited main diff.
    parents = {2: ["main"], 3: ["main"], 4: [3], 5: [4], 6: [5], 7: [2, 6], 8: [7],
               9: [13], 10: [8], 11: ["main"], 12: [8], 13: [8]}
    inventory, summaries = [], []
    for n, p in prs.items():
        bases = [source["baseline"] if x == "main" else prs[x]["head_sha"] for x in parents[n]]
        src, parent = tree(p["head_sha"]), tree(bases[0])
        changed = sorted(path for path in src.keys() | parent.keys() if src.get(path) != parent.get(path))
        own, inherited = [], []
        for path in changed:
            data = src.get(path)
            inherited_from = [parents[n][i] for i, base in enumerate(bases[1:], 1) if data is not None and data == tree(base).get(path)]
            if inherited_from:
                inherited.append(path)
            else:
                own.append(path)
            now = tree(current).get(path)
            inventory.append(dict(pr=n, path=path, source_git_blob=data,
                                  semantic_parents=parents[n], inherited_from=inherited_from,
                                  current_tree="ABSENT" if now is None else "IDENTICAL" if data == now else "DIFFERENT_OR_ADAPTED"))
        summaries.append(dict(pr=n, unique_line_parents=parents[n], changed_paths=len(changed),
                              already_from_other_parent=len(inherited), unique_or_composed_paths=len(own),
                              current_tree_counts=dict(collections.Counter(x["current_tree"] for x in inventory if x["pr"] == n))))
    duplicate = prs[2]["head_sha"] == prs[11]["head_sha"]
    absorbed = subprocess.run(["git", "merge-base", "--is-ancestor", prs[13]["head_sha"], prs[9]["head_sha"]], cwd=ROOT).returncode == 0
    assert duplicate and absorbed and prs[9]["head_sha"] != prs[13]["head_sha"]
    witness = json.loads((ROOT / "studies/scene_continuity_2026_10_15/results.json").read_text(encoding="utf-8"))
    result = dict(status="REVIEW_CHECKS_COMPLETE_NOT_MERGE_ACCEPTANCE", open_prs=12,
                  candidate_commit=current, main_baseline=source["baseline"], source_heads_match_previous_reconstruction=12,
                  semantic_units=len(units), every_pr_has_disposition=True, every_unit_has_verified_source_path=True,
                  exact_duplicate=[2, 11], source_13_is_ancestor_of_9=absorbed, pr9_adds_to_pr13=True,
                  file_summaries=summaries, unit_content_witnesses=unit_evidence,
                  semantic_counterexamples=semantic_examples(), metadata_counterexample=original_metadata,
                  current_metadata_check=current_metadata, restored_source_files=len(restored),
                  current_dynamic_witness=dict(origin="EXISTING_CURRENT_RUN_RESULT_RECHECKED_SOURCE_HASHES",
                                              first_M=witness["releases"][0]["M_position"],
                                              in_F=witness["releases"][0]["M_in_F"], outside_F=witness["releases"][0]["M_outside_F"]),
                  ready_for_main=False,
                  scope="Frozen pre-main review at candidate_commit; current fixes are separately checked. This is not current merge authority.",
                  remaining=["current UI/regression/reveal tests and decisions review are a separate final run",
                             "current Trace/FOM coverage remains scoped; frozen is not rebound",
                             "operator perception and fixed/residual calibration remain separate"])
    assert result["metadata_counterexample"]["same_closed_prefix"] and result["metadata_counterexample"]["prefix_digest_changed"]
    for stamp in witness["source_hashes"]:
        assert h(blob(current, stamp["artifact"])) == stamp["version"], "stale frozen continuity witness"
    (HERE / "current-checks.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "open_prs", "semantic_units", "exact_duplicate", "pr9_adds_to_pr13", "ready_for_main")}, ensure_ascii=False))
    print("confirmed metadata identity defect:", result["metadata_counterexample"]["prefix_digest_changed"])
    print("current prefix retains its identity:", not current_metadata["prefix_digest_changed"])
    print("restored source files verified:", len(restored))
    print("counterexamples:", result["semantic_counterexamples"])


if __name__ == "__main__":
    main()
