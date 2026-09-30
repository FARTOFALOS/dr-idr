"""Lens 8, part B: the distinguishing paths of the directive (section 7) through the frozen contract (dogovor.md).

Synthetic paths only, in a session's own units (see contract.py). All paths are long, the slice t = 11:00, the opposite
DR ou = -1.2, the illustrative areas A = [-0.30; -0.10] and B = [-0.70; -0.50] (the directive allows them only for
synthetic traces), L = +1.0. Before 10:35 every bar lies inside [-1.0; +0.15].

python -B synthetic_trace.py            the trace, the small-cohort numbers and the checks -> synthetic_trace.log
python -B synthetic_trace.py --paths    the paths alone, without any answer -> puti.md (for an independent reading)
python -B synthetic_trace.py --screen   lens 9 (15.3): for paths 3, 1, 5, 12a and 7, where the working screen's star would
                                        stand and where the event «the near edge reached» lies -> screen_vs_event.log
"""
from __future__ import annotations

import sys
from pathlib import Path

from contract import classify, clock, eligible, status_at

HERE = Path(__file__).resolve().parent
A, B, L, T, OU = (-0.30, -0.10), (-0.70, -0.50), 1.0, 660, -1.2

P0 = [(635, .10, .25, .05, .20), (640, .20, .35, .15, .30), (645, .30, .40, .20, .25),
      (650, .25, .30, .12, .18), (655, .18, .28, .10, .22), (660, .22, .30, .15, .20)]
F1 = [(665, .20, .22, .00, .05), (670, .05, .08, -.18, -.12), (675, -.12, .15, -.15, .12),
      (680, .12, .50, .10, .45), (685, .45, .85, .40, .80), (690, .80, 1.05, .75, .95), (695, .95, 1.00, .85, .90)]
F3 = [(665, .20, .22, -.05, .00), (670, .00, .02, -.22, -.18), (675, -.18, -.10, -.62, -.58),
      (680, -.58, -.50, -1.30, -1.25), (685, -1.25, -.60, -1.28, -.65), (690, -.65, .30, -.70, .25),
      (695, .25, 1.05, .20, 1.00)]
P12 = [(635, .10, .20, .00, .05), (640, .05, .08, -.20, -.15), (645, -.15, .10, -.18, .08),
       (650, .08, .30, .05, .25), (655, .25, .35, .18, .30), (660, .30, .32, .15, .20)]
F10 = [(665, .20, .30, .10, .25), (670, .25, 1.05, -.20, .90), (675, .90, .95, .80, .85)]


def path(name, bars, H, complete=True, minutes=None, note=""):
    return dict(name=name, bars=bars, t=T, ou=OU, H=H, complete=complete, minutes=minutes or {}, note=note)


PATHS = [
    path("1", P0 + F1, 695),
    path("2", P0 + [(665, .20, .22, -.05, -.02), (670, -.02, .00, -.20, -.15), (675, -.15, -.05, -.35, -.30),
                    (680, -.30, -.25, -.58, -.52), (685, -.52, -.10, -.55, -.12), (690, -.12, .40, -.15, .35),
                    (695, .35, .80, .30, .75), (700, .75, 1.02, .70, .98)], 700),
    path("3", P0 + F3, 695),
    path("3b", P0 + [(665, .20, .22, .05, .10), (670, .10, .12, -1.35, -1.30), (675, -1.30, -.80, -1.32, -.85),
                     (680, -.85, 1.05, -.90, 1.00)], 680),
    path("4", P0 + [(665, .20, .50, .18, .45), (670, .45, .90, .40, .85), (675, .85, 1.10, .80, 1.00),
                    (680, 1.00, 1.02, .30, .35), (685, .35, .40, -.20, -.15), (690, -.15, .20, -.18, .15)], 690),
    path("5", [(635, .10, .40, .05, .35), (640, .35, .80, .30, .75), (645, .75, 1.10, .70, .90),
               (650, .90, .95, .40, .45), (655, .45, .50, .15, .25), (660, .25, .30, .12, .20),
               (665, .20, .22, -.20, -.15), (670, -.15, .50, -.18, .45), (675, .45, 1.05, .40, 1.00)], 675),
    path("6", P0 + [(665, .20, .22, -.02, .00), (670, .00, .05, -.16, -.10), (675, -.10, .30, -.12, .25),
                    (680, .25, .55, .20, .50), (685, .50, .60, .10, .15), (690, .15, .45, .05, .40)], 690),
    path("7", [(635, .10, .25, .05, .20), (640, .20, .30, .00, .05), (645, .05, .08, -.15, -.12),
               (650, -.12, -.02, -.22, -.18), (655, -.18, -.08, -.25, -.20), (660, -.20, -.12, -.24, -.20),
               (665, -.20, -.10, -.28, -.15), (670, -.15, .30, -.18, .25), (675, .25, .70, .20, .65),
               (680, .65, 1.02, .60, .95)], 680),
    path("8", [(635, .10, .20, .00, .05), (640, .05, .08, -.20, -.18), (645, -.18, -.10, -.38, -.35),
               (650, -.35, -.25, -.45, -.40), (655, -.40, -.30, -.46, -.42), (660, -.42, -.35, -.46, -.40),
               (665, -.40, -.36, -.56, -.52), (670, -.52, -.10, -.55, -.15), (675, -.15, .40, -.18, .35),
               (680, .35, .80, .30, .75), (685, .75, 1.00, .70, .95)], 685),
    path("9a", [(635, .10, .20, .02, .15), (640, .15, .18, -.02, .00), (645, .00, .05, -.08, -.05),
                (650, -.05, .00, -.09, -.06), (655, -.06, -.02, -.09, -.08), (660, -.08, -.05, -.10, -.10),
                (665, -.10, -.05, -.22, -.18), (670, -.18, .30, -.20, .25), (675, .25, .70, .20, .65),
                (680, .65, 1.01, .60, .95)], 680),
    path("9b", P0 + [(665, .20, .22, .00, .02), (670, .02, .05, -.10, -.05), (675, -.05, .40, -.08, .35),
                     (680, .35, .75, .30, .70), (685, .70, 1.00, .65, .98)], 685),
    path("10a", P0 + [(665, .20, .22, -.15, -.12), (670, -.12, .30, -.15, .25), (675, .25, .60, .20, .55),
                      (680, .55, 1.05, -1.30, -1.25)], 680),
    path("10b", P0 + F10, 675, minutes={670: [(665, .30, -.20), (666, .40, .10), (667, .70, .35), (668, 1.05, .65),
                                              (669, .95, .85)]}),
    path("10c", P0 + F10, 675, minutes={670: [(665, .30, .10), (666, .40, .15), (667, 1.05, -.20), (668, .95, .80),
                                              (669, .92, .85)]}),
    path("11", P0 + [(665, .20, .22, -.05, -.02), (670, -.02, .00, -.20, -.15), (675, -.15, .10, -.18, .05),
                     (680, .05, .40, .00, .35)], 960, complete=False),
    path("12a", P12 + [(665, .20, .25, .05, .10), (670, .10, .15, -.02, .00), (675, .00, .05, -.14, -.10),
                       (680, -.10, .40, -.12, .35), (685, .35, .80, .30, .75), (690, .75, 1.03, .70, 1.00)], 690),
    path("12b", P12 + [(665, .20, .30, .05, .25), (670, .25, .60, .20, .55), (675, .55, 1.02, .50, .95)], 675),
    path("13a", P0 + F1, 695, note="префикс тот же, что у 13b"),
    path("13b", P0 + F3, 695, note="префикс тот же, что у 13a"),
    path("14", P0[:-1] + F1, 695, note="свечи 11:00 нет"),
    path("15", P0 + [(665, .20, .22, .02, .05), (675, -.05, .00, -.18, -.12), (680, -.12, .40, -.15, .35),
                     (685, .35, 1.02, .30, .95)], 685, note="свечи 11:10 нет"),
]
DIRECTIVE = {"1": "K → L, DR цел", "2": "A → B → L до отмены", "3": "K → отмена → L",
             "3b": "(доп.) приход и закрытие за DR в одной свече", "4": "L после t, но до K", "5": "L достигнута до t",
             "6": "K допустим, до H ни L, ни отмены", "7": "на t уже внутри K", "8": "на t уже за K",
             "9a": "на t ровно на границе K", "9b": "(доп.) после t касание ровно границы K",
             "10a": "L и закрытие за DR в одной свече", "10b": "K и L в одной свече, минуты решают",
             "10c": "K и L в одной минуте", "11": "история оборвана до исхода",
             "12a": "K был до t, новый приход после t", "12b": "K был до t, после t прихода нет",
             "13a": "тот же префикс, хвост 1", "13b": "тот же префикс, хвост 2",
             "14": "(доп.) нет свечи в t", "15": "(доп.) пропуск свечи до прихода"}


def fmt(v):
    return f"{v:+.2f}".replace(".", ",").replace("+0,00", "0,00")


def write_paths():
    L_ = ["# Синтетические пути линзы 8 (только входные данные, без ответов)", "",
          "Договор: [dogovor.md](dogovor.md). Все пути — лонг, своя шкала сессии, срез t = 11:00 (закрытие M5), "
          "противоположный DR `ou` = −1,20, L = +1,0.",
          "Условные области: A = [−0,30; −0,10], B = [−0,70; −0,50]. До 10:35 все свечи в пределах [−1,00; +0,15].",
          "Свеча: время закрытия, открытие, верх, низ, закрытие. H — конец сессии; «данные полные» — нет обрыва до H.", ""]
    for p in PATHS:
        L_.append(f"## Путь {p['name']}" + (f" ({p['note']})" if p["note"] else ""))
        L_.append(f"H = {clock(p['H'])}; данные {'полные' if p['complete'] else 'обрываются после последней свечи (до H)'}.")
        L_.append("")
        L_.append("| Закрытие | Открытие | Верх | Низ | Закрытие |")
        L_.append("|---|---|---|---|---|")
        for b in p["bars"]:
            L_.append(f"| {clock(b[0])} | {fmt(b[1])} | {fmt(b[2])} | {fmt(b[3])} | {fmt(b[4])} |")
        for bc, mins in p["minutes"].items():
            L_.append("")
            L_.append(f"Минутные свечи внутри свечи, закрывшейся в {clock(bc)} (минута открытия, верх, низ): "
                      + "; ".join(f"{clock(m)} {fmt(tp)} / {fmt(bt)}" for m, tp, bt in mins))
        L_.append("")
    (HERE / "puti.md").write_text("\n".join(L_), encoding="utf-8")
    print("written", HERE / "puti.md")


def row(p, K, nm):
    r = classify(p, K, L)
    pre = [b for b in p["bars"] if b[0] <= p["t"]]
    at = [b for b in pre if b[0] == p["t"]]
    x = fmt(at[0][4]) if at else "нет"
    top = fmt(max(b[2] for b in pre))
    tau = clock(p["t"] + 5 * (r["tau"] + 1)) if r["tau"] is not None else "—"
    yn = lambda v: "да" if v is True else ("нет" if v is False else "?")
    first = f"{r['first'][0]} {clock(r['first'][1])}" if r["first"] and r["first"][1] else (r["first"][0] if r["first"] else "—")
    c = lambda v: "?" if v is None else str(v)
    return (f"{p['name']:4s} {nm} | на t {x}, верх до t {top}, допуск {'да' if r['eligible'] else 'нет'} | {r['status']:7s} | "
            f"новый {yn(r['new']):3s} {tau:5s} | допуст. {yn(r['adm']) if r['eligible'] else '—':3s} | после: {first:11s} | "
            f"исход {r['outcome'] or ('?' if r['adm'] else '—'):11s} | new/adm/q/seq {c(r['c_new'])}/{c(r['c_adm'])}/{c(r['c_q'])}/"
            f"{c(r['c_seq'])} | прежний экран {'да' if r['old'] else 'нет'}" + (f" | {r['why']}" if r["why"] else "")), r


def cohort_numbers(rows, nm):
    """The small synthetic 'cohort' (every eligible path once): each number on its known cases, with the bounds (every
    unknown as 0 ... as 1), and the identity p_seq = p_adm x q on the fully known cases (dogovor.md, section 7)."""
    E = [r for r in rows if r["eligible"]]
    out = [f"{nm}: N_scenario {len(E)} (из {len(rows)} путей; без допуска {len(rows) - len(E)})"]
    for key, name in (("c_new", "p_new"), ("c_adm", "p_adm"), ("c_q", "q"), ("c_seq", "p_seq")):
        v = [r[key] for r in E if r[key] != "-"]
        one, known, unk = sum(1 for x in v if x == 1), sum(1 for x in v if x in (0, 1)), sum(1 for x in v if x is None)
        val = f"{one}/{known} = {one / known:.3f}" if known else "—"
        out.append(f"   {name:5s} на известных {val}; границы {one}/{known + unk} … {one + unk}/{known + unk}; неизвестно {unk}")
    K = [r for r in E if None not in (r["c_new"], r["c_adm"], r["c_q"], r["c_seq"])]
    n_k, adm_k, seq_k = len(K), sum(1 for r in K if r["c_adm"] == 1), sum(1 for r in K if r["c_seq"] == 1)
    ok = adm_k == 0 or abs(seq_k / n_k - (adm_k / n_k) * (seq_k / adm_k)) < 1e-12
    out.append(f"   тождество на полностью известных ({n_k}): p_seq {seq_k}/{n_k} = p_adm {adm_k}/{n_k} × q {seq_k}/{adm_k}: "
               f"{'выполняется' if ok else 'НЕ выполняется'}")
    return out, ok


def checks(res):
    """Boundary, same-bar, re-anchoring and prefix-invariance tests: (name, passed)."""
    g = lambda nm, k: res[(nm, k)]
    T_ = [
        ("9a: закрытие на t ровно на ближнем крае — inside, нового прихода нет", g("9a", "A")["status"] == "inside" and g("9a", "A")["new"] is False),
        ("9b: касание ровно ближнего края после t — приход (граница принадлежит области)", g("9b", "A")["new"] is True),
        ("9b и 8: касание ровно L = +1,00 — успех", g("9b", "A")["outcome"] == "success" and g("8", "B")["outcome"] == "success"),
        ("3b: приход и закрытие за DR в одной свече — приход допустим, затем отмена", g("3b", "A")["adm"] is True and g("3b", "A")["outcome"] == "invalidated"),
        ("10a: L и закрытие за DR в одной свече — L раньше (касание раньше закрытия)", g("10a", "A")["outcome"] == "success"),
        ("10a, область B: приход в K и L в одной свече без минут — допустимость неизвестна", g("10a", "B")["adm"] is None and g("10a", "B")["c_seq"] is None),
        ("10b: K и L в одной свече, минуты — K раньше: допустим, успех в той же свече", g("10b", "A")["adm"] is True and g("10b", "A")["outcome"] == "success"),
        ("10c: K и L в одной минуте — неизвестно, не неудача", g("10c", "A")["adm"] is None and g("10c", "A")["c_adm"] is None),
        ("11: обрыв данных после допустимого прихода — исход неизвестен, не неудача", g("11", "A")["adm"] is True and g("11", "A")["c_q"] is None),
        ("11, область B: прихода в данных нет, данные оборваны — приход неизвестен", g("11", "B")["new"] is None),
        ("12a: касание до t не считается; приход — новое касание в 11:15", g("12a", "A")["tau"] is not None and T + 5 * (g("12a", "A")["tau"] + 1) == 675),
        ("12b: касание до t не считается; после t прихода нет", g("12b", "A")["new"] is False),
        ("4: L после t раньше прихода — приход есть, но недопустим", g("4", "A")["new"] is True and g("4", "A")["adm"] is False),
        ("5: L до t — сессия вне группы сценария", g("5", "A")["c_new"] == "-"),
        ("7 и 8: inside / beyond остаются в N_scenario и дают 0 новых приходов", g("7", "A")["c_new"] == 0 and g("8", "A")["c_new"] == 0),
        ("7, 8, 9a: прежний экран засчитал бы приход", all(g(n, "A")["old"] for n in ("7", "8", "9a"))),
        ("14 A: нет свечи в t, касание после t есть — приход неизвестен", g("14", "A")["status"] == "unknown" and g("14", "A")["c_new"] is None),
        ("14 B: нет свечи в t, касания после t нет — прихода нет при любом статусе (версия 1.1)", g("14", "B")["status"] == "unknown" and g("14", "B")["c_new"] == 0),
        ("15: пропуск свечи до прихода — приход есть, допустимость неизвестна", g("15", "A")["new"] is True and g("15", "A")["adm"] is None),
    ]
    # 13: what is known at t does not depend on the tail
    a, b = PATHS[[p["name"] for p in PATHS].index("13a")], PATHS[[p["name"] for p in PATHS].index("13b")]
    same_t = all(status_at(a["bars"], T, K) == status_at(b["bars"], T, K) for K in (A, B)) and eligible(a["bars"], T, L) == eligible(b["bars"], T, L)
    T_.append(("13: одинаковый префикс — одинаковые статус и допуск на t; исходы разные",
               same_t and g("13a", "A")["outcome"] == "success" and g("13b", "A")["outcome"] == "invalidated"))
    inv = True
    for p in PATHS:
        cut = dict(p, bars=[x for x in p["bars"] if x[0] <= T], complete=False)
        for K in (A, B):
            rf, rc = classify(p, K, L), classify(cut, K, L)
            inv &= (rf["status"], rf["eligible"]) == (rc["status"], rc["eligible"])
    T_.append(("все пути: статус и допуск, посчитанные только по префиксу, совпадают с посчитанными по всему пути", inv))
    return T_


def screen_star(p, K):
    """The working screen's star for one similar session and one pullback place (design 22, app.js arrivalsOf): the first
    bar after t whose bottom is strictly below the near edge; price = that bar's bottom clamped into the band; time =
    the bar's open. Returns (price, open minute) or None."""
    lo, hi = K
    for b in p["bars"]:
        if b[0] > p["t"] and b[3] < hi: return max(b[3], lo), b[0] - 5
    return None


def illustrate():
    out = ["Lens 9, 15.3: the working screen's star against the event «the near edge reached» (synthetic, M5 bars).",
           "Base map = the similar sessions of the screen (no target filter); the percentage a star enters is the place's share of them.", ""]
    for nm in ("3", "1", "5", "12a", "7"):
        p = PATHS[[q["name"] for q in PATHS].index(nm)]
        pre = [b for b in p["bars"] if b[0] <= p["t"]]
        out.append(f"-- path {nm}: {DIRECTIVE[nm]}; close at t {fmt(pre[-1][4])}, top before t {fmt(max(b[2] for b in pre))}")
        for K, an in ((A, "A"), (B, "B")):
            r = classify(p, K, L)
            st = screen_star(p, K)
            ev = (f"new arrival: near edge {fmt(K[1])} reached in the M5 {clock(p['t'] + 5 * r['tau'])}-{clock(p['t'] + 5 * (r['tau'] + 1))}"
                  if r["new"] else f"no new arrival ({r['status']} at t)" if r["status"] in ("inside", "beyond") else "no new arrival")
            scr = f"screen star at {fmt(st[0])}, drawn at {clock(st[1])} (the bar's open)" if st else "no screen star"
            out.append(f"   {an}: status {r['status']:7s} | {ev} | {scr} | base share: {'counts' if r['new'] else 'does not count'}"
                       f" as a new arrival, the old screen {'counts it' if r['old'] else 'does not count it'}")
        out.append("")
    text = "\n".join(out)
    (HERE / "screen_vs_event.log").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    if "--paths" in sys.argv:
        write_paths(); sys.exit(0)
    if "--screen" in sys.argv:
        illustrate(); sys.exit(0)
    out, res = [], {}
    out.append("Строка: путь, область | префикс | статус на t | новый приход (свеча) | допустим | первое событие после прихода | "
               "исход | вклад в p_new/p_adm/q/p_seq (1, 0, ? = неизвестно, - = вне знаменателя) | прежний экран | причина")
    for p in PATHS:
        out.append("")
        out.append(f"-- путь {p['name']}: {DIRECTIVE[p['name']]}")
        for K, nm in ((A, "A"), (B, "B")):
            line, r = row(p, K, nm)
            res[(p["name"], nm)] = r
            out.append(line)
    out.append("")
    out.append("Малая синтетическая группа (каждый путь один раз, 13a/13b вместо 1 и 3 не дублируются):")
    ok_all = True
    for K, nm in ((A, "A"), (B, "B")):
        rows = [res[(p["name"], nm)] for p in PATHS if p["name"] not in ("13a", "13b")]
        lines, ok = cohort_numbers(rows, nm)
        out += lines; ok_all &= ok
    out.append("")
    out.append("Проверки:")
    T_ = checks(res)
    for nm, ok in T_:
        out.append(f"  [{'ok' if ok else 'СБОЙ'}] {nm}")
    out.append(f"Итого: {sum(ok for _, ok in T_)} из {len(T_)} проверок, тождество {'выполняется' if ok_all else 'НЕ выполняется'}")
    text = "\n".join(out)
    (HERE / "synthetic_trace.log").write_text(text + "\n", encoding="utf-8")
    print(text)
