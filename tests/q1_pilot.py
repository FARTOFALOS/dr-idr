"""Q1 pilot (Q1-PILOT-0.2): the contract's discriminating examples on synthetic paths, and the storage invariants.

    python -B tests/q1_pilot.py

Offline: no session base, no browser, no server. Every expected value below is written from the text of Q1-PILOT-0.2
(§2-§5) and the engineer's roadmap §4, not read off the code: a definition both implementations shared wrongly would
fail here. Exit code 0 = all good.
"""
from __future__ import annotations

import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lab"))
from q1 import engine as E  # noqa: E402
from q1.store import Collision, Store, canonical, sha  # noqa: E402

failures = []
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def check(cond, msg):
    print(("  ok  " if cond else "  FAIL ") + msg)
    if not cond:
        failures.append(msg)


# ---------- synthetic paths ----------
GRID = list(range(245, 245 + 5 * 24, 5))        # 24 common-clock M5 after a box that ends at 04:00; H = 06:00
L = len(GRID)
NAN = (np.nan, np.nan, np.nan)


def path(base=(20, 30, 25), **rows):
    """A directed path: every M5 = base (low, high, close) in ticks unless given as rows (k=(lo, hi, cl) or NAN)."""
    P = np.array([base] * L, dtype=float)
    for k, v in rows.items():
        P[int(k[1:])] = v
    return P


def case(sid, date, P, side=1, win=0, weekday=0, a=1, w=40, oppv=-60):
    return dict(id=sid, date=date, P=np.array(P, dtype=float), side=side, win=win, weekday=weekday, a=a, w=w, oppv=oppv)


def table(cases):
    return E.Table("NQ", "ODR", cases, GRID, E.SyntheticProvider(cases, GRID))


def day(k):
    return f"2010-{1 + k // 28:02d}-{1 + k % 28:02d}"


TARGET_DATE = "2011-06-01"
# the target: activation at index 1 (its own M5 closes beyond DR there), then a calm prefix above every place
TGT = dict(base=(10, 30, 20))                    # low 10 (u = 0.25 > 0), close 20 (u = 0.5) on w = 40


def tgt_case(**rows):
    return case("T", TARGET_DATE, path(TGT["base"], k1=(50, 70, 60), **rows))


def analogue(k, close=20, w=40, low=10, side=1, win=0, weekday=0, a=1, oppv=-60, cut=5, after=None, **rows):
    """An analogue standing at the cut with this close and low (its own units), and its rest given by `after`:
    'yes' (reaches L=0 at cut+2), 'no' (stays above), or explicit rows."""
    base = (low, max(close, low) + 10, close)
    P = path(base, **{f"k{a}": (low + 40, low + 60, low + 50)})
    if after == "yes":
        P[cut + 2] = (-5, close, 5)
    for kk, v in rows.items():
        P[int(kk[1:])] = v
    return case(f"A{k:02d}", day(k), P, side=side, win=win, weekday=weekday, a=a, w=w, oppv=oppv)


CUT = 5


def run_examples():
    print("Selection, coordinates and the exact 1/4 (Q1 §2)")
    t = tgt_case()
    cs = [t,
          analogue(1, close=40, w=80, low=20, after="yes"),      # the same u = 0.5 at another price scale
          analogue(2, close=30, after="no"),                     # u = 0.75: |0.75 - 0.5| = 1/4 exactly — included
          analogue(3, close=31, after="no"),                     # one tick further — excluded
          analogue(4, close=30, side=-1, after="yes")]           # a short in its own mirrored scale
    T = table(cs)
    i = T.row(TARGET_DATE)
    geo = T.attempt(i, CUT, "0", "GEO")
    key = T.attempt(i, CUT, "0", "NODEPOS_ALL")
    ids = lambda a: sorted(m["id"] for m in a["members"])        # noqa: E731
    check(geo["state"]["status"] == "OPEN", "target open at the cut: post-activation low above L = 0")
    check(ids(geo) == ["A01", "A02", "A04"], f"GEO: same u at another scale, the 1/4 boundary and the mirrored short are in, one tick beyond is out ({ids(geo)})")
    check(ids(key) == ["A01", "A02"], f"key without weekday: the other side is not in the parent ({ids(key)})")
    rs = dict(zip([T.ids[j] for j in geo["par"]], geo["reason"]))
    check(rs["A03"] == "FAR", "A03 excluded as «дальше 1/4»")

    print("Eligibility chain: not activated, hole, DR broken, already at L, the activating M5 (Q1 §2)")
    cs = [t,
          analogue(1, a=7, after="no"),                                  # activates after the cut
          analogue(2, after="no", k3=NAN),                               # a whole M5 missing in the prefix
          analogue(3, after="no", k3=(10, 30, -61)),                     # a close strictly beyond its opposite DR
          analogue(4, after="no", k3=(10, 30, -60)),                     # a close exactly ON it: not a break
          analogue(5, after="no", k3=(-2, 30, 20)),                      # already reached L = 0 after activation
          analogue(6, after="no", k1=(-50, 70, 60)),                     # its activating M5 dipped below L: not counted
          analogue(7, after="no", a=5)]                                  # activating M5 = the cut: no whole M5 after it
    T = table(cs)
    a = T.attempt(T.row(TARGET_DATE), CUT, "0", "GEO")
    rs = dict(zip([T.ids[j] for j in a["par"]], a["reason"]))
    want = dict(A01="NOT_ACTIVATED", A02="PREFIX_HOLE", A03="DR_BROKEN", A04="MATCH", A05="ALREADY_AT_L", A06="MATCH", A07="NOT_ACTIVATED")
    check(rs == want, f"reasons per case: {rs}")
    c = a["counts"]
    check((c["N_parent"], c["N_eligible"], c["N_not_yet"], c["n_match"]) == (7, 3, 2, 2), f"counters N_parent → eligible → not yet → n: {c}")

    print("Outcomes YES / NO / UNKNOWN and the 8 / 10 / 2 example (Q1 §3, roadmap §4)")
    cs = [t] + [analogue(k, after="yes") for k in range(8)] + [analogue(8 + k, after="no") for k in range(10)] \
        + [analogue(18, after="no", k20=NAN), analogue(19, after="no", k9=NAN)]
    T = table(cs)
    a = T.attempt(T.row(TARGET_DATE), CUT, "0", "GEO")
    c, e = a["counts"], a["estimate"]
    check((c["n_match"], c["yes"], c["no"], c["unknown"], c["n_known"]) == (20, 8, 10, 2, 18), f"20 = 8 YES + 10 NO + 2 UNKNOWN; n_known = 18 ({c})")
    check(e["point"] == dict(num=8, den=18) and e["bounds"] == [dict(num=8, den=20), dict(num=10, den=20)] and e["publication"] == "PUBLISHED",
          f"point 8/18 among known, bounds [8/20, 10/20]; unknown kept in n ({e})")

    print("Reach under another hole, reach after a hole, a gap beyond L, a later break (Q1 §2-3)")
    cs = [t,
          analogue(1, after="yes", k20=NAN),                             # seen reach, another M5 missing later
          analogue(2, after="no", k8=NAN, k12=(-3, 25, 5)),              # reach after a hole: YES, first time unknown
          analogue(3, after="no", k10=(-30, -10, -20)),                  # a whole M5 beyond L (gap): reach without a cross
          analogue(4, after="no", k8=(5, 25, -70), k14=(-5, 10, 0))]     # breaks its DR after the cut, then reaches L
    T = table(cs)
    a = T.attempt(T.row(TARGET_DATE), CUT, "0", "GEO")
    lab = {m["id"]: (m["label"], m["first_reach"]) for m in a["members"]}
    check(lab["A01"][0] == "YES", "known reach stays YES despite another missing M5")
    check(lab["A02"] == ("YES", dict(close=E.clk(GRID[12]), time_known=False)), f"reach after a hole: YES, its first time unknown ({lab['A02']})")
    check(lab["A03"][0] == "YES", "an M5 wholly beyond L counts as reaching it (threshold, not a fill)")
    check(lab["A04"][0] == "YES", "a later DR break does not shorten the horizon of the label")

    print("Today: no prefix, hole, DR broken, already reached, block over (Q1 §3)")
    T = table([tgt_case(k3=NAN)] + [analogue(k, after="no") for k in range(3)])
    check(T.target_state(T.row(TARGET_DATE), 1, (0, 1))["status"] == "NO_PREFIX", "cut at the activating M5: no prefix")
    check(T.target_state(T.row(TARGET_DATE), CUT, (0, 1))["status"] == "PREFIX_UNKNOWN", "a hole in today's prefix: unknown state, no answer")
    T = table([tgt_case(k3=(10, 30, -61))])
    check(T.target_state(0, CUT, (0, 1))["status"] == "DR_BROKEN", "today's DR broken before the cut: the question is closed")
    T = table([tgt_case(k3=(-1, 30, 20))])
    st = T.target_state(0, CUT, (0, 1))
    check(st["status"] == "RESOLVED" and st["time"] == E.clk(GRID[3]), f"today already reached L: a fact with its time, no share ({st})")
    check(T.issue_payload(0, CUT, "0", "GEO")[0] is None, "a resolved target gets no issue")
    T = table([tgt_case()])
    check(T.target_state(0, L - 1, (0, 1))["status"] == "BLOCK_OVER", "the cut at H: no horizon")
    check(T.target_state(0, CUT, (-1, 2))["status"] == "OPEN", "the same moment is open for L = −1/2")

    print("Publication: few sessions, no known outcome, strictly earlier dates (Q1 §3)")
    cs = [t] + [analogue(k, after="yes") for k in range(12)]
    T = table(cs)
    a = T.attempt(T.row(TARGET_DATE), CUT, "0", "GEO")
    check(a["estimate"]["publication"] == "WITHHELD_FEW_SESSIONS" and a["counts"]["n_match"] == 12 and a["counts"]["yes"] == 12,
          "n = 12 < 20: no number published, the counts stay")
    cs = [t] + [analogue(k, after="no", k20=NAN) for k in range(25)]
    T = table(cs)
    a = T.attempt(T.row(TARGET_DATE), CUT, "0", "GEO")
    check(a["estimate"]["publication"] == "NO_KNOWN_OUTCOME" and a["estimate"]["point"] is None and a["counts"]["unknown"] == 25,
          "25 matched, all unknown: no point, the bounds stay [0, 1]")
    late = analogue(30, after="yes")
    late["date"] = TARGET_DATE                                           # the same trading date is not history
    later = analogue(31, after="yes")
    later["date"] = "2012-01-02"
    T = table([t, late, later] + [analogue(k, after="no") for k in range(3)])
    a = T.attempt(T.row(TARGET_DATE), CUT, "0", "GEO")
    check(a["counts"]["N_parent"] == 3, "the parent holds only strictly earlier dates")

    print("Identity: new M5 = new issue of the same target; new L = another target; two estimators = two issues (Q1 §4)")
    cs = [t] + [analogue(k, after="yes" if k % 2 else "no") for k in range(24)]
    T = table(cs)
    i = T.row(TARGET_DATE)
    p5, _ = T.issue_payload(i, 5, "0", "GEO")
    p6, _ = T.issue_payload(i, 6, "0", "GEO")
    pm, _ = T.issue_payload(i, 5, "-1/2", "GEO")
    pk, _ = T.issue_payload(i, 5, "0", "NODEPOS_ALL")
    check(p5["target_id"] == p6["target_id"] and p5["issue_id"] != p6["issue_id"], "next M5, same L and H: same target, new issue")
    check(pm["target_id"] != p5["target_id"], "another place: another target")
    check(pk["target_id"] == p5["target_id"] and pk["issue_id"] != p5["issue_id"], "GEO and the key without weekday on one target and cut: two issues")
    check(not p5["reference_check"]["disagreements"] and p5["reference_check"]["members_checked"] == p5["counts"]["n_match"],
          "the second implementation (raw rows) agrees on every member")

    print("Information boundary: the target's future vs an analogue's future (Q1 §5)")
    t2 = tgt_case()
    t2["P"][CUT + 1:] = np.array([(-90, -60, -70)] * (L - CUT - 1))     # today's rest rewritten: falls far below L
    T2 = table([t2] + cs[1:])
    q5, _ = T2.issue_payload(T2.row(TARGET_DATE), 5, "0", "GEO")
    check(canonical(q5) == canonical(p5), "the target's future changed: the issue is byte-identical, issue_id and input digest included")
    check(T.observe(i, (0, 1))["label"] != T2.observe(T2.row(TARGET_DATE), (0, 1))["label"], "… while the target's own outcome may change")
    flip = [dict(x) for x in cs]
    j = next(k for k, x in enumerate(flip) if x["id"] == "A00")              # an analogue labelled NO
    flip[j]["P"] = flip[j]["P"].copy()
    flip[j]["P"][CUT + 3] = (-8, 10, 0)                                       # its rest now reaches L
    T3 = table(flip)
    q5b, _ = T3.issue_payload(T3.row(TARGET_DATE), 5, "0", "GEO")
    check(ids(dict(members=q5b["members"])) == ids(dict(members=p5["members"])), "an analogue's future changed: the same members (selection reads prefixes only)")
    check(q5b["counts"]["yes"] == p5["counts"]["yes"] + 1, "… its label moved one YES (labels are the estimate's input)")
    check(q5b["inputs"]["input_digest"] != p5["inputs"]["input_digest"] and q5b["issue_id"] != p5["issue_id"],
          "… and the input snapshot differs, so it is another issue")
    return T, T2, T3, p5


def rmtree(p):
    def onerr(func, path, exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    shutil.rmtree(p, onerror=onerr) if sys.version_info < (3, 12) else shutil.rmtree(p, onexc=onerr)


def run_storage(T, T2, T3):
    print("Storage: write once, idempotent access, collision, read-only (Q1 §4, roadmap §3)")
    root = Path(tempfile.mkdtemp(prefix="q1-store-"))
    try:
        S = Store(root)
        i = T.row(TARGET_DATE)
        st1, att, rec1 = E.issue(S, T, i, 5, "0", "GEO")
        iid = rec1["payload"]["issue_id"]
        before = S.raw_bytes("issues", iid)
        st2, _, rec2 = E.issue(S, T, i, 5, "0", "GEO")
        check(st1 == "CREATED" and st2 == "IDEMPOTENT" and S.raw_bytes("issues", iid) == before,
              "the same issue again: idempotent, nothing rewritten")
        forged = dict(rec1["payload"], counts=dict(rec1["payload"]["counts"], yes=rec1["payload"]["counts"]["yes"] + 1))
        try:
            S.put_issue(forged)
            check(False, "a different payload under the same issue_id must be refused")
        except Collision:
            check(S.raw_bytes("issues", iid) == before, "a different payload under the same issue_id: refused, bytes untouched")
        try:
            with open(root / "issues" / f"{iid}.json", "wb") as f:
                f.write(b"{}")
            check(False, "an ordinary overwrite of an issue file should be refused by the read-only attribute")
        except PermissionError:
            check(S.raw_bytes("issues", iid) == before, "an ordinary file overwrite is refused (read-only attribute)")
        _, _, reck = E.issue(S, T, i, 5, "0", "NODEPOS_ALL")
        check(reck["payload"]["issue_id"] != iid and len(S.issues()) == 2 and S.raw_bytes("issues", iid) == before,
              "a second estimator on the same target and cut: its own issue, the first one unchanged")

        print("Outcome: a separate record; correction = new revision; the issue never changes (Q1 §4)")
        so, orec = E.attach_outcome(S, T, iid)
        check(so == "CREATED" and S.raw_bytes("issues", iid) == before and orec["payload"]["issue_payload_sha256"] == sha(rec1["payload"]),
              "outcome attached as its own file, linked to the issue's payload hash; the issue bytes unchanged")
        so2, _ = E.attach_outcome(S, T, iid)
        check(so2 == "IDEMPOTENT", "the same outcome again: idempotent")
        so3, orec3 = E.attach_outcome(S, T2, iid)            # the target's rows after the cut were corrected
        check(so3 == "CREATED" and orec3["payload"]["revision"] == 2 and orec3["payload"]["supersedes"] == orec["payload"]["outcome_id"]
              and orec3["payload"]["observed"]["label"] != orec["payload"]["observed"]["label"] and S.raw_bytes("issues", iid) == before
              and S.get_outcome(orec["payload"]["outcome_id"]) is not None,
              "corrected target rows after the cut: revision 2 supersedes 1, both kept, the issue unchanged")
        pre = [dict(x) for x in T.cases]
        pre[i] = dict(pre[i], P=pre[i]["P"].copy())
        pre[i]["P"][3] = (12, 30, 22)                        # a correction INSIDE the issue's prefix
        so4, probe = E.attach_outcome(S, table(pre), iid)
        check(so4 == "REFUSED" and probe["check"]["same_prefix"] is False, "an outcome computed on another prefix is refused, not attached")

        print("Reopen and reproduce on the original inputs; a changed analogue or model is reported, never passed off")
        r = E.reproduce(S, T, iid)
        check(r["status"] == "IDENTICAL" and r["integrity"], f"reproduced byte-identically ({r['status']})")
        r = E.reproduce(S, T2, iid)
        check(r["status"] == "IDENTICAL", "the target's corrected future does not touch the issue's inputs: still identical")
        r = E.reproduce(S, T3, iid)
        check(r["status"] == "INPUTS_CHANGED" and r["changed"] == ["domain_digest"], f"an analogue's rows changed: INPUTS_CHANGED ({r})")
        st5, _, rec5 = E.issue(S, T3, T3.row(TARGET_DATE), 5, "0", "GEO", meta=dict(recomputed_from=iid))
        check(st5 == "CREATED" and rec5["payload"]["issue_id"] != iid and S.raw_bytes("issues", iid) == before,
              "recomputation on revised inputs is a distinct record; the original stays")
        saved = E.MODEL
        E.MODEL = "another-model"
        try:
            r = E.reproduce(S, T, iid)
            check(r["status"] == "MODEL_CHANGED", "a changed model is reported as such")
            st6, _, rec6 = E.issue(S, T, i, 5, "0", "GEO")
            check(st6 == "CREATED" and rec6["payload"]["issue_id"] != iid, "an issue of another model version is another record")
        finally:
            E.MODEL = saved

        print("Outcome on record does not touch a later issue; verify() detects a changed issue")
        root2 = Path(tempfile.mkdtemp(prefix="q1-store-"))
        try:
            S2 = Store(root2)
            _, _, a1 = E.issue(S2, T, i, 6, "0", "GEO")
            E.attach_outcome(S2, T, a1["payload"]["issue_id"])
            _, _, a2 = E.issue(S2, T, i, 7, "0", "GEO")              # issued after an outcome of this target exists
            fresh, _ = T.issue_payload(i, 7, "0", "GEO")
            check(canonical(a2["payload"]) == canonical(fresh) and a2["meta"]["outcomes_on_record_for_target"] == 1,
                  "an issue made while an outcome is on record is the same payload; the meta says the outcome was on record")
        finally:
            rmtree(root2)
        v = S.verify()
        check(v["ok"] and not v["writable"], f"verify(): every hash, identity and link holds; all files read-only ({v['issues']} issues, {v['outcomes']} outcomes)")
        p = root / "issues" / f"{iid}.json"
        os.chmod(p, stat.S_IWRITE)
        p.write_bytes(p.read_bytes().replace(b'"yes":', b'"yes":1', 1))
        v = S.verify()
        check(not v["ok"] and any("payload hash differs" in x for x in v["problems"]) and any("changed after this outcome" in x for x in v["problems"]),
              "a hand-edited issue is detected: its own hash and its outcome links both fail")
    finally:
        rmtree(root)


def run_gate(T):
    print("The second implementation withholds a number when the vectorised path disagrees (fail closed)")
    orig = E.Table.select

    def broken(self, par, cs, level, cl_t, w_t):
        m = orig(self, par, cs, level, cl_t, w_t)
        m["near"] = m["near"].copy()
        m["near"][0, 0] = ~m["near"][0, 0]
        m["match"] = m["notyet"] & m["near"]
        return m
    E.Table.select = broken
    try:
        p, _ = T.issue_payload(T.row(TARGET_DATE), 5, "0", "GEO")
        check(p["estimate"]["publication"] == "REFERENCE_MISMATCH" and p["reference_check"]["disagreements"],
              "a disagreeing member makes the issue REFERENCE_MISMATCH with the case named")
    finally:
        E.Table.select = orig


if __name__ == "__main__":
    T, T2, T3, _ = run_examples()
    run_storage(T, T2, T3)
    run_gate(T)
    print()
    print("ALL GOOD" if not failures else f"{len(failures)} FAILED")
    sys.exit(1 if failures else 0)
