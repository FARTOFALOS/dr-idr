"""Lens 10, patch 2.1: tests A-D of the patch and a test E of the open fork (clock time or time since activation), on a
toy synthetic history with hierarchy.py. Synthetic only.
python -B synthetic_hierarchy.py  ->  synthetic_hierarchy.log
"""
from __future__ import annotations

from pathlib import Path

from field import session_cells
from hierarchy import Day, activation, broken_by, bucket, cohort, conditional_view, family, family_map, map_at, prefix

HERE = Path(__file__).resolve().parent
BOX = [-0.5, -0.3, -0.6, -0.2, -0.4, 0.0, -0.1, -0.3, 0.05, -0.2, 0.0, 0.1]      # 09:35 ... 10:30, all below DR high


def clock(m):
    return f"{(m // 60) % 24:02d}:{m % 60:02d}"


def session(name, after, end=780):
    """Bars from 09:35: the box, then the closes given for 10:35, 10:40, ..., then a slow wave until `end`."""
    closes = BOX + list(after)
    while 570 + 5 * len(closes) < end:
        k = len(closes); closes.append(round(closes[-1] + (0.06 if (k // 4) % 2 == 0 else -0.05), 2))
    bars, prev = [], closes[0]
    for i, c in enumerate(closes):
        o = prev
        bars.append((575 + 5 * i, o, round(max(o, c) + 0.04, 2), round(min(o, c) - 0.04, 2), c))
        prev = c
    return dict(name=name, bars=bars)


# today: activation at 10:50 (the bar 10:45-10:50 closes above the DR high 0.15) and a second day activating at 11:20
TODAY_A = session("today-A", [0.05, 0.10, 0.12, 0.30, 0.35, 0.25, 0.10, 0.05, 0.20, 0.40, 0.55, 0.50])
TODAY_B = session("today-B", [0.05, 0.08, 0.10, 0.06, 0.02, 0.07, 0.11, 0.12, 0.09, 0.30, 0.38, 0.45])
HISTORY = [
    session("h1 (10:40)", [0.05, 0.25, 0.30, 0.45, 0.40, 0.30, 0.20, 0.35, 0.50, 0.60]),
    session("h2 (10:45)", [0.05, 0.10, 0.28, 0.32, 0.20, 0.10, 0.00, -0.10, 0.05, 0.20]),
    session("h3 (10:50)", [0.02, 0.08, 0.10, 0.22, 0.40, 0.55, 0.70, 0.80, 0.75, 0.90]),
    session("h4 (11:05)", [0.00, 0.05, 0.10, 0.12, 0.08, 0.10, 0.25, 0.30, 0.20, 0.15]),
    session("h5 (11:20)", [0.00, 0.02, 0.05, 0.08, 0.10, 0.06, 0.09, 0.12, 0.10, 0.28, 0.35, 0.30]),
    session("h6 (10:35)", [0.20, 0.30, 0.25, 0.20, 0.15, 0.30, 0.45, 0.50, 0.40, 0.35]),
    session("h7 (нет)", [0.00, 0.05, 0.10, 0.12, 0.10, 0.05, 0.00, -0.10, -0.20, -0.30]),
    session("h8 (10:50, слом 11:10)", [0.02, 0.08, 0.10, 0.20, 0.05, -0.40, -0.90, -1.30, -1.10, -1.00]),
    session("h9 (10:55)", [0.00, 0.05, 0.10, 0.12, 0.25, 0.30, 0.40, 0.35, 0.30, 0.45]),
]


def perturb_after(s, t):
    """The same day, with every bar after t changed (what the operator sees later must not change an earlier map)."""
    return dict(s, bars=[b if b[0] <= t else (b[0], b[1] - 0.5, b[2] - 0.5, b[3] - 0.5, b[4] - 0.5) for b in s["bars"]])


def run():
    R = []
    add = lambda name, expect, got, ok: R.append((name, expect, got, ok))

    # A: activation at 10:50
    kinds = {clock(t): map_at(TODAY_A, HISTORY, t)["kind"] for t in (645, 650, 655, 660)}
    add("A активация в 10:50", "до 10:50 карты нет; 10:50 — Baseline; 10:55 и дальше — Dynamic",
        f"t0 {clock(activation(TODAY_A))}; " + ", ".join(f"{k}: {v or 'нет'}" for k, v in kinds.items()),
        activation(TODAY_A) == 650 and kinds == {"10:45": None, "10:50": "baseline", "10:55": "dynamic", "11:00": "dynamic"})

    # B: activation at 11:20, no binding to a fixed clock time
    b0 = map_at(TODAY_B, HISTORY, 680)
    add("B активация в 11:20", "t0 = 11:20; в 10:50 карты нет; Baseline в 11:20 из подтверждений 11:05–11:20",
        f"t0 {clock(activation(TODAY_B))}; 10:50: {map_at(TODAY_B, HISTORY, 650)['kind'] or 'нет'}; 11:20: {b0['kind']}, похожие {b0['members']}",
        activation(TODAY_B) == 680 and map_at(TODAY_B, HISTORY, 650)["kind"] is None and b0["kind"] == "baseline"
        and all(abs(activation(h) - 680) <= 15 for h in HISTORY if h["name"] in b0["members"]))

    # C: the Baseline is kept and never rewritten while the day goes on
    day = Day()
    for t in range(635, 725, 5):
        day.on_close(prefix(TODAY_A, t), HISTORY, t)           # at each close only what was known then
    base, dyn = day.baseline, day.dynamic[665]
    add("C Baseline не переписывается", "после 17 закрытий Baseline 10:50 тот же; карта 11:05 другая и хранится отдельно",
        f"Baseline {clock(base['t'])}: похожие {base['members']}; 11:05: похожие {dyn['members']}; Baseline цел: {day.baseline_intact()}",
        day.baseline_intact() and base["t"] == 650 and (dyn["members"] != base["members"] or dyn["V"] != base["V"]))

    # D: hover back at 12:00; later bars of today (even changed ones) do not touch an earlier map
    at1050, at1120 = map_at(TODAY_A, HISTORY, 650), map_at(TODAY_A, HISTORY, 680)
    same_base = at1050 == day.baseline == map_at(perturb_after(TODAY_A, 650), HISTORY, 650)
    same_dyn = at1120 == map_at(perturb_after(TODAY_A, 680), HISTORY, 680)
    add("D выбор назад в 12:00", "10:50 — тот же Baseline; 11:20 — Dynamic только по префиксу до 11:20",
        f"10:50: {at1050['kind']}, совпадает с сохранённым и с изменённым хвостом дня: {same_base}; 11:20: {at1120['kind']}, "
        f"не зависит от свечей после 11:20: {same_dyn}", same_base and same_dyn and at1120["kind"] == "dynamic")

    # E: the open fork — a similar session activated 10 minutes before today's t0
    h1 = HISTORY[0]
    c_clock = {h["name"]: ts for h, ts in cohort(prefix(TODAY_A, 650), HISTORY, 650, "clock")}
    c_event = {h["name"]: ts for h, ts in cohort(prefix(TODAY_A, 650), HISTORY, 650, "event")}
    first = lambda ts: sorted(k / 10 for k, j in session_cells(h1, ts, 780)[0] if j == ts + 5)
    got = (f"по часам: h1 стоит на 10:50 (через 10 мин после своей активации), в колонке 10:50–10:55 его свеча 10:50–10:55 "
           f"{first(650)}; по времени от активации: h1 стоит на своём 10:40, в той же колонке его свеча 10:40–10:45 {first(640)}; "
           f"группа по часам {sorted(c_clock)}, по активации {sorted(c_event)}")
    add("E развилка О17 (закрыта оператором: семья по окну, тесты F–L)", "разные свечи в одной колонке; группы могут различаться", got,
        c_clock.get(h1["name"]) == 650 and c_event.get(h1["name"]) == 640 and first(650) != first(640))
    # F-L: the operator's answers (2026-09-30, meaning/lens/2026-09-30-linza-11.md and -12.md): a 15-minute activation
    # family fixed for the day; the main field is always the whole family (one N), read further in clock M5 columns;
    # filters by the lived path are separate conditional views «n из N»
    fam = family(prefix(TODAY_A, 650), HISTORY)
    names = sorted(h["name"] for h in fam)
    add("F семья по 15-минутному окну", "подтверждение 10:50 → окно 10:45–11:00: семья — подтверждения 10:45, 10:50, 10:55; 10:35, 10:40, 11:05, 11:20 — другие семьи",
        f"окно {bucket(activation(TODAY_A))}; семья {names}",
        names == ["h2 (10:45)", "h3 (10:50)", "h8 (10:50, слом 11:10)", "h9 (10:55)"])
    maps = {t: family_map(TODAY_A, HISTORY, t) for t in range(650, 725, 5)}
    add("G новая M5 не меняет семью", "на каждом срезе 10:50–11:55 основное поле — та же семья, чужих нет",
        f"составы на срезах одинаковы: {all(m['members'] == names for m in maps.values())}",
        all(m["members"] == names for m in maps.values()))
    add("H сломавшие DR остаются в основном поле", "h8 сломал DR в 11:10; на срезе 11:15 он в поле, N тот же",
        f"11:15: {maps[675]['kind']}, N {maps[675]['N']}, h8 в поле: {'h8 (10:50, слом 11:10)' in maps[675]['members']}",
        "h8 (10:50, слом 11:10)" in maps[675]["members"] and maps[675]["N"] == maps[650]["N"])
    h9 = HISTORY[8]
    first9 = sorted(k / 10 for k, j in session_cells(h9, 650, 780)[0] if j == 655)
    add("I люфт внутри окна (свойство, не ошибка)", "член семьи, подтверждённый в 10:55, в первой колонке исходной карты 10:50 проходит свою свечу подтверждения",
        f"h9: закрытие 10:50 = {[x[4] for x in h9['bars'] if x[0] == 650][0]}, свеча 10:50–10:55 задевает {first9}, закрытие 10:55 = {[x[4] for x in h9['bars'] if x[0] == 655][0]}",
        activation(h9) == 655)
    base, later = maps[650], maps[675]
    tail = {k: v for k, v in base["V"].items() if k[1] > 675}
    add("J исходная не переписывается", "поле на 11:15 — это колонки исходной карты после 11:15, те же числа",
        f"клеток после 11:15 в исходной {len(tail)}, в поле 11:15 {len(later['V'])}, совпадают: {tail == later['V']}", tail == later["V"])
    # K: one denominator, no DR-true renormalisation (the operator's example in small: of 4, 2 DR false, 1 reached +1.0)
    toy = [session("k1", [0.05, 0.25, 0.60, 1.05, 0.90]), session("k2", [0.05, 0.25, 0.30, 0.40, 0.35]),
           session("k3", [0.05, 0.25, -0.50, -1.30, -1.40]), session("k4", [0.05, 0.25, 0.00, -1.25, -1.35])]
    reached = [h["name"] for h in toy if any(x[2] >= 1.0 for x in h["bars"] if x[0] > 640)]
    dr_true = [h["name"] for h in toy if not broken_by(h, 780)]
    add("K один знаменатель N, без пересчёта на DR true", "из 4 двое сломали DR, +1,0 достиг 1: на экране 25 %, а не 50 % среди DR true",
        f"+1,0: {len(reached)}/{len(toy)} = {100 * len(reached) / len(toy):.0f} %; развилка DR true {len(dr_true)}/{len(toy)}",
        len(reached) == 1 and len(dr_true) == 2)
    cv = conditional_view(TODAY_A, HISTORY, 675)
    add("L условный вид — отдельно, «n из N»", "на 11:15 фильтр по прожитому пути даёт часть семьи с подписью; основное поле не меняется",
        f"{cv['label']}: {cv['members']}; основное поле на 11:15 — {maps[675]['N']} сессий",
        cv["N"] == len(fam) and set(cv["members"]) <= set(names) and maps[675]["members"] == names)
    return R


if __name__ == "__main__":
    R = run()
    out = ["Иерархия карт (патч 2.1) на игрушечной истории: тест | ожидание | получено | итог"]
    for name, expect, got, ok in R:
        out.append(f"[{'ok' if ok else 'СБОЙ'}] {name} | {expect} | {got}")
    out.append(f"Итого: {sum(ok for *_, ok in R)} из {len(R)}")
    text = "\n".join(out)
    (HERE / "synthetic_hierarchy.log").write_text(text + "\n", encoding="utf-8")
    print(text)
