"""Q1 pilot — the acceptance walk-through on a real historical scene, end to end, in a fresh local store.

    python -B lab/q1/demo.py [--inst NQ --block RDR --date 2025-12-17 --cut 11:10 --level -1/2]

1. Issue the answer of each of the three estimators at the cut (CREATED), then again (IDEMPOTENT: nothing rewritten).
2. Reopen each issue from its file and recompute it on its original inputs (IDENTICAL, byte for byte).
3. Attach the observed outcome to each issue as a separate record; the issue's bytes are the same before and after.
4. Issue every open cut of the same target and place, for every estimator: each estimator's coverage is then
   reconstructible from the stored attempts alone (published / few sessions / no known outcome).
5. The information boundary on the real base: rewrite the target's candles after the cut — the recomputed issue is
   byte-identical (its id included) while the target's own outcome flips; rewrite one member's candles after the cut —
   the same members, its label moves, the input snapshot (and so the issue) differs. The base in memory is restored.
6. Verify the store.

Writes only under lab/.q1-pilot/demo/<run>/ (store and evidence.json; case-level, local, git-ignored).
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB))
from q1 import engine as E  # noqa: E402
from q1.store import Store, canonical, sha  # noqa: E402


def pct(n, d):
    return "—" if not d else f"{100 * n / d:.1f}".replace(".", ",")


def say(s=""):
    print(s, flush=True)


def answer_line(pl):
    c, e = pl["counts"], pl["estimate"]
    if e["publication"] == "WITHHELD_FEW_SESSIONS":
        return f"мало сессий: n = {c['n_match']} (число не показывается; дошли {c['yes']}, не дошли {c['no']}, неизвестно {c['unknown']})"
    if e["publication"] == "NO_KNOWN_OUTCOME":
        return f"у всех {c['n_match']} исход неизвестен"
    share = f"{pct(c['yes'], c['n_match'])} %" if not c["unknown"] else f"{pct(c['yes'], c['n_match'])}–{pct(c['yes'] + c['unknown'], c['n_match'])} %"
    return f"{share}: из {c['n_match']} дошли {c['yes']}, не дошли {c['no']}, неизвестно {c['unknown']}"


def patched_table(inst, block, date, cut_minute, edit):
    """A table rebuilt from a copy of the session base in which `edit` rewrote some bars (the real loader and digests)."""
    B = E.scene21._B[inst]
    B2 = dict(B, bars=B["bars"].copy())
    edit(B2)
    E.scene21._B[inst] = B2
    E.scene24._MISSING.clear()
    try:
        U, grid = E.V.universe(inst, block, "conf")
        return E.Table(inst, block, U, grid, E.BaseProvider(inst, block))
    finally:
        E.scene21._B[inst] = B
        E.scene24._MISSING.clear()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inst", default="NQ")
    ap.add_argument("--block", default="RDR")
    ap.add_argument("--date", default="2025-12-17")
    ap.add_argument("--cut", default="11:10")
    ap.add_argument("--level", default="-1/2")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    E.bind_corpus()
    run = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    root = LAB / ".q1-pilot" / "demo" / run
    S = Store(root / "store")
    T = E.table(a.inst, a.block)
    i = T.row(a.date)
    hh, mm = map(int, a.cut.split(":"))
    c = T.grid.index(hh * 60 + mm)
    ev = dict(run=run, scene=vars(a), model=E.MODEL, code=E.code_version(), corpus=str(E.CORPUS["path"]), steps={})
    st = T.target_state(i, c, E.LEVELS[a.level])
    say(f"Сцена: {a.inst} {a.block} {a.date}, срез {a.cut}, место {a.level}; сегодня: {st['status']}")
    if st["status"] != "OPEN":
        say("Вопрос на этом срезе не открыт — выберите другой срез."); return 1

    say("\n1. Выпуск трёх оценивателей (и повторная запись того же ответа)")
    ids, before = {}, {}
    for est in E.ESTIMATORS:
        s1, _, rec = E.issue(S, T, i, c, a.level, est)
        s2, _, _ = E.issue(S, T, i, c, a.level, est)
        iid = rec["payload"]["issue_id"]
        ids[est], before[est] = iid, S.raw_bytes("issues", iid)
        say(f"   {est:12s} {s1} → {s2}; выпуск {iid[:12]}; {answer_line(rec['payload'])}")
        ev["steps"].setdefault("issue", {})[est] = dict(first=s1, second=s2, issue_id=iid, payload_sha256=rec["meta"]["payload_sha256"],
                                                        counts=rec["payload"]["counts"], estimate=rec["payload"]["estimate"],
                                                        reference_check={k: v for k, v in rec["payload"]["reference_check"].items() if k != "disagreements"},
                                                        disagreements=len(rec["payload"]["reference_check"]["disagreements"]))

    say("\n2. Повтор на исходных входах")
    for est, iid in ids.items():
        r = E.reproduce(S, T, iid)
        say(f"   {est:12s} {r['status']}")
        ev["steps"].setdefault("reproduce", {})[est] = r["status"]

    say("\n3. Исход — отдельной записью; байты выпуска до и после")
    for est, iid in ids.items():
        so, orec = E.attach_outcome(S, T, iid)
        same = S.raw_bytes("issues", iid) == before[est]
        ob = orec["payload"]["observed"]
        say(f"   {est:12s} {so}: {ob['label']} {('в ' + ob['first_reach']['close']) if ob['first_reach'] else ''}; выпуск не изменился: {same}")
        ev["steps"].setdefault("outcome", {})[est] = dict(status=so, outcome_id=orec["payload"]["outcome_id"], observed=ob,
                                                          check=orec["payload"]["check"], issue_bytes_unchanged=same)

    say("\n4. Все открытые срезы этой цели: охват восстанавливается по сохранённым попыткам")
    cuts = [k for k in T.open_cuts(i) if T.target_state(i, k, E.LEVELS[a.level])["status"] == "OPEN"]
    for est in E.ESTIMATORS:
        for k in cuts:
            E.issue(S, T, i, k, a.level, est)
    tid = E.target_id(T.target_record(i, a.level))
    cov = {}
    for r in S.issues(tid):
        p = r["payload"]
        d = cov.setdefault(p["estimator"]["id"], {"attempts": 0, "PUBLISHED": 0, "WITHHELD_FEW_SESSIONS": 0, "NO_KNOWN_OUTCOME": 0, "REFERENCE_MISMATCH": 0})
        d["attempts"] += 1
        d[p["estimate"]["publication"]] += 1
    for est, d in cov.items():
        say(f"   {est:12s} попыток {d['attempts']}: число показано {d['PUBLISHED']}, мало сессий {d['WITHHELD_FEW_SESSIONS']}, исход неизвестен у всех {d['NO_KNOWN_OUTCOME']}")
    ev["steps"]["coverage"] = dict(open_cuts=len(cuts), by_estimator=cov)

    say("\n5. Граница информации на настоящей базе")
    est = "GEO"
    pl0 = S.get_issue(ids[est])["payload"]
    k = T.keys[i]
    side = int(T.side[i])
    fr = T.provider.frame(k, side)
    cut_min = T.grid[c]
    lvl = E.LEVELS[a.level]
    deep = int(fr["e"] + side * fr["w"] * (lvl[0] / lvl[1] - 2))      # far beyond the place, on the target's side of play

    def rewrite_target(B2):
        lo, hi = B2["off"][k], B2["off"][k + 1]
        rows = B2["bars"][lo:hi]
        after = rows[:, 0] - E.scene24.SHIFT[a.block] > cut_min
        if side == 1: rows[after, 3] = deep                           # physical low far below the place
        else: rows[after, 2] = deep                                   # physical high far above it
        B2["bars"][lo:hi] = rows
    T2 = patched_table(a.inst, a.block, a.date, cut_min, rewrite_target)
    pl2, _ = T2.issue_payload(T2.row(a.date), c, a.level, est)
    o1, o2 = T.observe(i, lvl)["label"], T2.observe(T2.row(a.date), lvl)["label"]
    same_issue = canonical(pl2) == canonical(pl0)
    say(f"   будущее цели переписано: выпуск байт в байт тот же: {same_issue} (id {pl2['issue_id'][:12]}); исход цели {o1} → {o2}")
    m = next((x for x in pl0["members"] if x["label"] == "NO"), None) or pl0["members"][0]
    j = T.pos[m["id"]]
    kj, sj = T.keys[j], int(T.side[j])
    frj = T.provider.frame(kj, sj)
    deepj = int(frj["e"] + sj * frj["w"] * (lvl[0] / lvl[1] - 2))

    def rewrite_member(B2):
        lo, hi = B2["off"][kj], B2["off"][kj + 1]
        rows = B2["bars"][lo:hi]
        after = rows[:, 0] - E.scene24.SHIFT[a.block] > cut_min
        if sj == 1: rows[after, 3] = deepj
        else: rows[after, 2] = deepj
        B2["bars"][lo:hi] = rows
    T3 = patched_table(a.inst, a.block, a.date, cut_min, rewrite_member)
    pl3, _ = T3.issue_payload(T3.row(a.date), c, a.level, est)
    same_members = sorted(x["id"] for x in pl3["members"]) == sorted(x["id"] for x in pl0["members"])
    lab3 = next(x["label"] for x in pl3["members"] if x["id"] == m["id"])
    say(f"   будущее участника {m['id']} переписано: состав тот же: {same_members}; его метка {m['label']} → {lab3}; "
        f"дошли {pl0['counts']['yes']} → {pl3['counts']['yes']}; входы другие: {pl3['inputs']['input_digest'] != pl0['inputs']['input_digest']}; "
        f"другой выпуск: {pl3['issue_id'] != pl0['issue_id']}")
    ev["steps"]["boundary"] = dict(target_future_rewritten=dict(issue_byte_identical=same_issue, outcome_before=o1, outcome_after=o2),
                                   member_future_rewritten=dict(member=m["id"], same_members=same_members, label_before=m["label"], label_after=lab3,
                                                                yes_before=pl0["counts"]["yes"], yes_after=pl3["counts"]["yes"],
                                                                input_digest_changed=pl3["inputs"]["input_digest"] != pl0["inputs"]["input_digest"],
                                                                issue_id_changed=pl3["issue_id"] != pl0["issue_id"]))
    say("\n6. Проверка хранилища")
    v = S.verify()
    say(f"   выпусков {v['issues']}, исходов {v['outcomes']}; всё сходится: {v['ok']}; файлов, доступных для записи: {len(v['writable'])}")
    ev["steps"]["verify"] = v
    (root / "evidence.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1), encoding="utf-8")
    say(f"\nЗаписи: {root}")
    ok = (all(x["first"] == "CREATED" and x["second"] == "IDEMPOTENT" and x["disagreements"] == 0 for x in ev["steps"]["issue"].values())
          and all(x == "IDENTICAL" for x in ev["steps"]["reproduce"].values())
          and all(x["issue_bytes_unchanged"] and all(x["check"].values()) for x in ev["steps"]["outcome"].values())
          and same_issue and o1 != o2 and same_members and ev["steps"]["boundary"]["member_future_rewritten"]["input_digest_changed"] and v["ok"])
    say("DEMO OK" if ok else "DEMO: SOMETHING FAILED (see above)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
