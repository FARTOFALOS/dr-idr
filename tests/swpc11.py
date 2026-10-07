"""DR-LAB-SWPC-1.1 on screen 24: the static checks and the passports of its bindings B01-B16.

    python -B tests/swpc11.py            check (exit code 0 = all good)
    python -B tests/swpc11.py --write    regenerate spec/ekran-24/12-swpc.md from its sources, then check

The normative text is spec/DR-LAB-SWPC-1.1.md and it is the only source of the contract: this file reads its tables (W,
roles, anchors, B, M, H, the routes of §9) instead of copying them, so the text and the checks cannot drift apart. What
this file adds is the engineering record SWPC §3.1 and §10 ask for: for every binding, where it lives in the code, which
clock and context drive it, which channels carry what, how it recovers, what the viewer may tune, and which executed
check proves it. From both it generates the binding passports (spec/ekran-24/12-swpc.md, never edited by hand).

Checks: the document is closed (every reference of a B row exists; every W is served by a binding; every M by a B row);
§9 routes exactly the 53 estimands and 8 fact forms of the compiled SC-1.1 registry, by exact ids; every estimand the
page can make a passport of is routed; every code anchor of the record exists; every M has an executed check in
tests/swpc11_browser.mjs; SC-1.1 stays pinned and compiled; the generated passports equal what the sources give.
The run of the browser checks themselves is `node tests/swpc11_browser.mjs` (the server must run).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lab"))
import contract as C  # noqa: E402

DOC = ROOT / "spec" / "DR-LAB-SWPC-1.1.md"
OUT = ROOT / "spec" / "ekran-24" / "12-swpc.md"
SRC = ROOT / "design" / "sozvezdiya-24" / "src"
HARNESS = ROOT / "tests" / "swpc11_browser.mjs"
BASE_COMMIT = "4526d30"
failures = []


def check(cond, msg):
    print(("  ok  " if cond else "  FAIL ") + msg)
    if not cond: failures.append(msg)


# ===================================================================================== the document (the only source)
TEXT = DOC.read_text(encoding="utf-8").replace("\r\n", "\n")


def section(n):
    return TEXT.split(f"\n## {n}. ")[1].split("\n## ")[0]


def ids(s, letter):
    """W01–W03, W05/W07, B01–B03 … → the exact ids (ranges with an en dash or a hyphen)."""
    out = []
    for a, b in re.findall(rf"{letter}(\d\d)(?:[–-]{letter}(\d\d))?", s):
        out += [f"{letter}{i:02d}" for i in range(int(a), int(b or a) + 1)]
    return out


W = {m[0]: dict(diff=m[1].strip(), supports=m[2].strip(), hazard=m[3].strip())
     for m in re.findall(r"^\| (W\d\d) \| (.+?) \| (.+?) \| (.+?) \|$", section(2), flags=re.M)}
DEADLINE = {}
for name, body in re.findall(r"^- \*\*(.+?):\*\* (.+?)\. ", section(2), flags=re.M):
    for w in ids(body, "W"): DEADLINE[w] = name
ROLES = re.findall(r"^\| `([A-Z_]+)` — ", section(3), flags=re.M)
ANCHORS = {m[0]: m[1].strip() for m in re.findall(r"^\| (A\d) · (.+?) \| ", section(3), flags=re.M)}
B = {}
for m in re.findall(r"^\| \*\*(B\d\d) · (.+?)\*\* \| (.+?) \| (.+?) \| (.+?) \|$", section(5), flags=re.M):
    bid, name, head, keep, forbid = m
    parts = head.split(";")
    roles = [("AMBIENT_STATE" if r == "AMBIENT" else r) for r in re.findall(r"SCAFFOLD|AMBIENT_STATE|AMBIENT|TRANSITION|ON_DEMAND|WITHHELD|USER_ALERT", parts[1])]
    B[bid] = dict(name=name, w=ids(parts[0], "W"), roles=roles, role_text=parts[1].strip(), anchors=re.findall(r"A\d", parts[2]), anchor_text=parts[2].strip(),
                  keep=keep.strip(), forbid=forbid.strip(), m=ids(forbid, "M"), h=ids(forbid, "H"))
M = {m[0]: m[1].strip() for m in re.findall(r"^\| (M\d\d) \| (.+?) \| .+? \|$", section(8), flags=re.M)}
H = {m[0]: m[1].strip() for m in re.findall(r"^\| (H\d\d) \| (.+?) \| .+? \|$", section(8), flags=re.M)}
ROUTES = {}
for m in re.finditer(r"^\| `((?:EST|FF):[A-Z0-9-]+?)(-\{R,X\})?` \| ([^|]+) \|$", section(9), flags=re.M):
    for i in ([m[1] + "-R", m[1] + "-X"] if m[2] else [m[1]]): ROUTES[i] = ids(m[3], "B")

# ===================================================================================== the engineering record (§3.1, §10)
# per binding: code = the functions that carry it (app.js / panel.js); clock / context = what drives it (§6.1); channels =
# which data drives which visual channel (§4); recover = what survives a distraction (§3.1); tune = what the viewer may
# change in ⚙ without changing a count (§7.4); rules = non-statistical sources (§9, §11); origin = §3.4 and this work;
# checks = the scenarios of tests/swpc11_browser.mjs that execute the binding's M-ids
BASE_CTX = "реестр SC-1.1, инструмент, торговая дата, блок, view conf/brk, scope, family_id, snapshot_id"
REC = {
    "B01": dict(code=["toolbar", "panelHtml", "viewSwitch", "famKey", "snapOf", "loadDay", "statusMsg"], clock="BASE-снимок (семья фиксирована при активации); действие пользователя (смена сцены и вида)",
                ctx=BASE_CTX, channels="текст: инструмент, блок, дата, ключ семьи, вид (подписи FF:PASSPORT-VIEW); место: верхняя строка и заголовок сводки; взаимодействие: «Семья слома / Исходная», «день недели / все дни»",
                recover="верхняя строка и заголовок сводки всегда называют сцену; переключатель вида показывает активную семью", tune="нет (только раскладка окна)",
                rules=["meaning/13 № 20, 47", "spec/ekran-24/10-semya-sloma.md"],
                origin="INHERITED; NEW_SWPC: поздний ответ дня отбрасывается (M02), при нехватке места названия событий сворачиваются, чтобы срез не уходил за край (§8.4)", checks=["m01", "m02", "a1"]),
    "B02": dict(code=["drawCandles", "drawNow", "drawPriceAxis", "drawTimeAxis", "sliceOf", "todayRows", "sess"], clock="закрытая M5 (статистика и факты); живая котировка (линия цены); секунды таймера (отсчёт до закрытия M5)",
                ctx="инструмент, дата, блок, срез", channels="положение: время и цена; прозрачность: свечи после среза в повторе 22 %; стиль: точечная линия цены, штрих среза; текст: метки среза и цены на осях",
                recover="метка среза на оси и плашка «История / Повтор / LIVE» в верхней строке", tune="⚙ «Свечи и фон», «Прошлые сессии и вчера»",
                rules=["AGENTS.md правило 6", "meaning/13 № 17, 43"], origin="INHERITED", checks=["m03"]),
    "B03": dict(code=["levels", "drawLevels", "drawTags", "stdState", "sideCol", "drawVib", "vibsOf", "drawPrev"], clock="закрытая M5 (коробка, подтверждение, слом, взятые STD); наблюдение (VI)",
                ctx="инструмент, дата, блок, срез", channels="стиль и толщина линии: DR сплошная, IDR штрих, STD по состоянию (взят — точки, следующий — ярче, дальние — тонкие); цвет: сторона активации; текст: названия в разрыве линии",
                recover="линии и их названия стоят весь день", tune="⚙ «Уровни сессии», «Коробка сессии», «VI», «Прошлые сессии и вчера»",
                rules=["meaning/13 № 8, 21, 24, 27, 34–36", "docs/STRATEGY.md §1.7 (VI)"], origin="INHERITED", checks=["m04"]),
    "B04": dict(code=["drawPoints", "drawClouds", "cloudsOf", "drawMemberPath", "drawPair"], clock="BASE-снимок", ctx=BASE_CTX,
                channels="положение: окончательные R/X каждой сессии в её времени и цене (шкала сегодняшней IDR); цвет: R янтарный, X небесный, оттенок состояния своей зоны; размер: точка зоны крупнее; дымка и нити — рисунок точек, без числа",
                recover="неизменны в пределах снимка", tune="⚙ «Точки сессий», «Созвездия · цвет и дымка»", rules=["meaning/13 № 5, 10, 32"], origin="INHERITED", checks=["m05"]),
    "B05": dict(code=["zonePass", "zoneMark", "drawZones", "zonesHtml", "zoneTip", "zoneRows", "drawBand", "zoneHeld"], clock="BASE-снимок (доли); закрытая M5 (статус)", ctx=BASE_CTX,
                channels="текст: имя и n/N зоны (подписи реестра); размер: историческая доля; цвет и прозрачность: статус по каталогу № 26; капсула: окно зоны; при снятом числе — имя с «—», без дымки, капсулы и холма",
                recover="имена и доли зон на созвездиях и в списке сводки по времени", tune="⚙ «Созвездия · подписи», «Лента времени»", rules=["meaning/12", "meaning/13 № 11, 31, 41, 42"],
                origin="INHERITED; NEW_SWPC: снятая доля зоны не утверждается рисунком (M14)", checks=["m05", "m06", "m07", "m14"]),
    "B06": dict(code=["drawProjRX", "evPass", "outPass", "ppHeld"], clock="BASE-снимок (длина); срез (часть «уже по часам»); закрытая M5 (невозможное сегодня)", ctx=BASE_CTX,
                channels="длина: доля полосы за весь горизонт, не меняется от статуса; цвет части: впереди / прошло по часам (зелёный) / невозможно сегодня (серый); кегль подписи по доле; ▲ / ▼ — доли за кадром",
                recover="колонка стоит у шкалы цены всегда", tune="⚙ «Колонка у цены»", rules=["meaning/13 № 3, 12, 16, 44", "meaning/14"],
                origin="INHERITED; NEW_SWPC: снятая доля полосы — без столбика (M14)", checks=["m06", "m10", "m14"]),
    "B07": dict(code=["drawBand", "bandHills", "bandOverlay", "evPass"], clock="BASE-снимок; срез (прошедшие окна тише)", ctx=BASE_CTX,
                channels="высота: доля окна по одной линейной шкале; яркость и тонкий контур большей стороны — рисунок тех же двух долей; капсула — окно зоны; холм — форма времени зоны, без числа",
                recover="лента внизу под той же осью времени", tune="⚙ «Лента времени»", rules=["meaning/13 № 4, 14, 28, 29, 40"],
                origin="INHERITED; NEW_SWPC: снятая доля окна — без столбика (M14)", checks=["m06", "m14"]),
    "B08": dict(code=["zoneStatus", "zoneClock", "zoneLook", "reachOf", "winLine", "stateCol"], clock="закрытая M5 (достижимость); срез (часы истории)", ctx=BASE_CTX + ", срез",
                channels="оттенок по каталогу № 26: активное, HOLDS светлее, QUIET зеленоватый, IMPOSSIBLE сланцевый с пунктиром; текст статуса — подписи FF:TODAY-Z и FF:HISTORY-CLOCK; снятый статус — «—» без вида состояния",
                recover="статус в строке зоны сводки и в инспекторе", tune="⚙ «Созвездия · цвет и дымка» (яркость отработанных)", rules=["meaning/14", "meaning/15 F1–F3"],
                origin="INHERITED; NEW_SWPC: снятый статус не утверждается (M14)", checks=["m07", "m14"]),
    "B09": dict(code=["outcomeHtml", "drPass", "detBody"], clock="BASE-снимок", ctx=BASE_CTX, channels="одна полоса на 100 % N из четырёх категорий; строки с долями; неизвестно и «нет периода» только при наличии; снятая категория — пустой отрезок",
                recover="блок «Исход DR» в постоянном месте сводки", tune="нет", rules=["spec/ekran-24/03-obzor-panel.md № 13–14"], origin="INHERITED", checks=["m08", "m14"]),
    "B10": dict(code=["nowOf", "nowHtml", "nowBundle", "drawNowLevels", "drawNowRange"], clock="закрытая M5 (срез NOW)", ctx=BASE_CTX + ", срез",
                channels="текст: исторические слова K33 (подписи CF:N-*), режим «по времени», опора всегда; наведение: пунктир сегодняшнего экстремума и полоса остатка q25–q75",
                recover="блок «Сейчас» в постоянном месте; загрузка — «считаю…», недоступность — «Локальный сервер не ответил»", tune="нет", rules=["meaning/15", "meaning/13 № 46–48"],
                origin="INHERITED; NEW_SWPC: недоступный ответ называется недоступным, а не «нет данных» (W13)", checks=["m09", "m08", "m14"]),
    "B11": dict(code=["undPass", "resPass", "outPass", "zonesHtml", "drawBand", "drawProjRX"], clock="BASE-снимок", ctx=BASE_CTX,
                channels="строки сводки «вне зон» и «не определено»; столбик «?» ленты; ▲ / ▼ колонки; неизвестное не имеет координаты",
                recover="строки остатка и неизвестного в сводке; причина отсутствия чисел — в сводке и в имени кнопки «Сводка»", tune="слои ⚙ «Слои» не удаляют счёт", rules=["meaning/12 §1", "spec/ekran-24/11-invarianty.md И5, И11"],
                origin="INHERITED", checks=["m08", "m10"]),
    "B12": dict(code=["filmOf", "drawFilm", "drawProj", "drawBandProfile", "closePass", "missPass", "rangePass", "columnHtml"], clock="BASE-снимок; срез (впереди / прошло)", ctx=BASE_CTX,
                channels="яркость клетки: доля N по одной шкале; профиль полосы: столбики n, классы цвета — место n среди впереди (не доля); подписи n из N; снятая доля — без клетки и столбика",
                recover="режим назван на переключателе «Границы хода / Путь семьи»", tune="⚙ «Путь семьи»", rules=["meaning/13 № 37, 38"], origin="INHERITED", checks=["m11", "m12"]),
    "B13": dict(code=["hit", "linkOf", "drawLink", "drawHighlight", "showTip", "tipHtml", "pin", "pinKey", "panelMarks", "areaInfo", "levelQuery"], clock="действие пользователя", ctx=BASE_CTX,
                channels="подсветка предмета (наведение — временно, щелчок — закрепление); инспектор в постоянном месте; окно времени на оси; цены на шкале",
                recover="закреплённый предмет возвращается в инспектор после ухода мыши, иначе слепок семьи", tune="нет", rules=["meaning/13 № 9, 13, 23, 33, 42, 43"], origin="INHERITED", checks=["m12"]),
    "B14": dict(code=["details", "detBody", "orderHtml", "ladderHtml", "drawHeat", "drawFilmMini", "zoneDiag", "hasBundle"], clock="BASE-снимок; действие пользователя", ctx=BASE_CTX,
                channels="шесть окон: паспорт предмета, R и X цена × время, порядок (своя сотня, «нет периода» отдельно), уровни, путь; диагностика без шанса",
                recover="ручка окон внизу, закрепление щелчком", tune="⚙ «Слои» (окна снизу)", rules=["meaning/13 № 23, 47"], origin="INHERITED", checks=["m13"]),
    "B15": dict(code=["kViolate", "kNow", "integrity", "regFault", "envCounts", "bindPassport", "verifyNow", "nowBundle", "snapOf", "ppHeld", "zoneHeld", "scNotice", "toolbar"], clock="состояние запроса и проверки", ctx=BASE_CTX + "; ответ семьи и ответ NOW — каждый своим номером",
                channels="текст: строка контракта в сводке, причина в строке семьи и блоке «Сейчас»; «—» вместо числа; снятие зависимого рисунка; при скрытой сводке — немигающий «!» и контур на кнопке «Сводка», причина в её имени",
                recover="нарушение стоит, пока сцена на экране и не пришёл новый проверенный ответ; чужая сцена его не показывает", tune="нельзя скрыть настройкой слоёв",
                rules=["contract/README.md", "meaning/13 № 47"],
                origin="INHERITED: отзыв числа и scNotice; NEW_SWPC: знак на «Сводке» (§7.2), отзыв зависимого рисунка единицами шлюза сервера (M14), нарушение принадлежит своей сцене (M16)", checks=["m14", "m15", "m16"]),
    "B16": dict(code=["alAdd", "alCheck", "alFire", "chime", "drawAlerts", "cfgPanel"], clock="живая котировка (уведомление); действие пользователя (линия, настройки)", ctx="инструмент; линии хранятся в этом браузере по инструменту",
                channels="жёлтый пунктир и плашка цены своей линии; после срабатывания — серая; плашка-уведомление до клика или 120 с; звук по настройке",
                recover="линия и её состояние сохраняются в браузере", tune="⚙ «Уведомления о цене», все цвета и размеры (счёт не меняется)", rules=["meaning/13 № 19, 45"], origin="INHERITED", checks=["m17", "m18"]),
}
HARNESS_OF = {m: "m" + m[1:] for m in M}          # M01 is executed by the scenario m01, …


def claim_basis(refs, page):
    cls = {"DescriptiveClaim": "C0", "ConditionalDescriptiveClaim": "C1", "PredictiveClaim": "C2", "DecisionClaim": "C3"}
    out = sorted({cls[page["forms"][r]["claim_class"]] for r in refs if r.startswith("EST:")})
    if any(r.startswith("FF:") for r in refs): out.append("наблюдаемый факт")
    return ", ".join(out) or "управление и наблюдение (числа нет)"


def passports(page):
    lines = ["# 12 · SWPC-1.1: паспорта привязок B01–B16", "", "[← к оглавлению](README.md)", "",
             "Сгенерировано `python -B tests/swpc11.py --write` из нормативного текста [DR-LAB-SWPC-1.1](../DR-LAB-SWPC-1.1.md) "
             "(§2, §2.1, §3.4, §5, §9) и инженерной записи в `tests/swpc11.py` (код, часы, каналы, настройки, проверки). Руками не править: "
             "`python -B tests/swpc11.py` сверяет файл с источниками.", "",
             "**Статус.** Машинные обязанности M01–M18 исполняет `tests/swpc11_browser.mjs` (изолированный Chrome; результат прогона — в узле "
             "[`meaning/07`](../../meaning/07-cepochka-reshenij.md)). Человеческие задачи H01–H12 оператором не проводились: "
             "`PERCEPTUALLY_UNVERIFIED`. Протокол — [`meaning/16-priyomka-swpc.md`](../../meaning/16-priyomka-swpc.md).", ""]
    for bid, b in B.items():
        r = REC[bid]
        refs = sorted(k for k, v in ROUTES.items() if bid in v)
        dl = sorted({DEADLINE.get(w, "—") for w in b["w"]})
        row = lambda k, v: lines.append(f"| {k} | {v} |")
        lines += [f"## {bid} · {b['name']}", "", "| Поле | Содержание |", "|---|---|"]
        row("binding_id, version", f"{bid} · SWPC-1.1")
        row("semantic_ref", ", ".join(f"`{x}`" for x in refs) + ("; " if refs and r["rules"] else "") + "; ".join(r["rules"]) if refs or r["rules"] else "—")
        row("claim_basis", claim_basis(refs, page))
        row("context_key", r["ctx"])
        row("clock_basis", r["clock"])
        row("work_ref", ", ".join(b["w"]) + " — " + "; ".join(W[w]["diff"] for w in b["w"]))
        row("comparison_set", "; ".join(f"{w}: {W[w]['supports']}" for w in b["w"]))
        row("hazard", "; ".join(f"{w}: {W[w]['hazard']}" for w in b["w"]))
        row("deadline", "; ".join(dl))
        row("recoverability", r["recover"])
        row("presentation_role", b["role_text"])
        row("anchor", f"{b['anchor_text']} → код: " + ", ".join(f"`{c}`" for c in r["code"]))
        row("channels", r["channels"])
        row("forbidden_encodings", b["forbid"])
        row("persistence", b["keep"])
        row("personalization", r["tune"])
        row("tests", "машинные: " + ", ".join(f"{m} (`{HARNESS_OF[m]}`)" for m in b["m"]) + (" и сценарии " + ", ".join(f"`{c}`" for c in r["checks"] if not re.fullmatch(r"m\d\d", c)) if any(not re.fullmatch(r"m\d\d", c) for c in r["checks"]) else "") +
            "; человеческие: " + (", ".join(b["h"]) + " — ждут оператора" if b["h"] else "—"))
        row("origin_class", r["origin"])
        row("provenance", f"spec/DR-LAB-SWPC-1.1.md §5, §9; база main@{BASE_COMMIT}")
        lines.append("")
    lines += ["## Маршруты §9: величина или форма факта → привязки", "", "| ID | Привязки | Утверждение |", "|---|---|---|"]
    for k in sorted(ROUTES):
        lines.append(f"| `{k}` | {', '.join(ROUTES[k])} | {claim_basis([k], page)} |")
    return "\n".join(lines) + "\n"


# ===================================================================================== checks
def main(write):
    page = json.loads((ROOT / "contract" / "build" / "page_registry.json").read_text(encoding="utf-8"))
    print("The document")
    check(len(W) == 14 and list(W) == [f"W{i:02d}" for i in range(1, 15)], f"§2: W01–W14 ({len(W)})")
    check(set(DEADLINE) == set(W), f"§2.1: every W has its term ({len(DEADLINE)})")
    check(ROLES == ["SCAFFOLD", "AMBIENT_STATE", "TRANSITION", "ON_DEMAND", "WITHHELD", "USER_ALERT"], f"§3.2: six roles {ROLES}")
    check(list(ANCHORS) == [f"A{i}" for i in range(1, 10)], f"§3.3: anchors A1–A9 ({len(ANCHORS)})")
    check(list(B) == [f"B{i:02d}" for i in range(1, 17)], f"§5: bindings B01–B16 ({len(B)})")
    check(list(M) == [f"M{i:02d}" for i in range(1, 19)] and list(H) == [f"H{i:02d}" for i in range(1, 13)], f"§8: M01–M18 ({len(M)}) and H01–H12 ({len(H)})")
    bad = [(b, x) for b, v in B.items() for x in v["w"] if x not in W] + [(b, x) for b, v in B.items() for x in v["roles"] if x not in ROLES] + \
          [(b, x) for b, v in B.items() for x in v["anchors"] if x not in ANCHORS] + [(b, x) for b, v in B.items() for x in v["m"] + v["h"] if x not in M and x not in H]
    check(not bad and all(v["w"] and v["roles"] and v["anchors"] and v["m"] for v in B.values()), f"every B row names existing W, roles, anchors, M and H{': ' + str(bad) if bad else ''}")
    check(set(W) <= {w for v in B.values() for w in v["w"]}, "every distinction W is served by a binding")
    check(set(M) <= {m for v in B.values() for m in v["m"]} | {"M01", "M18"}, "every M is the check of some binding (M01 and M18 are general)")
    print("§9 against the compiled SC-1.1 registry and the page")
    est, ff = {k for k in ROUTES if k.startswith("EST:")}, {k for k in ROUTES if k.startswith("FF:")}
    check(est == set(page["estimands"]) and len(est) == 53, f"§9 routes exactly the {len(page['estimands'])} estimands of the registry by exact ids{': ' + str(sorted(est ^ set(page['estimands']))) if est != set(page['estimands']) else ''}")
    check(ff == set(page["facts"]) and len(ff) == 8, f"§9 routes exactly the {len(page['facts'])} fact forms{': ' + str(sorted(ff ^ set(page['facts']))) if ff != set(page['facts']) else ''}")
    check(all(set(v) <= set(B) for v in ROUTES.values()), "every route names existing bindings")
    both = (SRC / "app.js").read_text(encoding="utf-8") + (SRC / "panel.js").read_text(encoding="utf-8")
    EV = r"(?:ev|h\.ev|r\.ev|e|I\.ev|g\.ev)"
    used = set()
    for name, plus in re.findall(r"'(EST:[A-Z0-9-]+)'(\s*\+\s*" + EV + r")?", both):
        if plus or name.endswith("-"): used.update({name + "R", name + "X"} if name.endswith("-") else {name})
        else: used.add(name)
    used -= {"EST:B-RX-R", "EST:B-RX-X"}
    used |= {f"EST:B-RX-{k}-{e}" for k in ("BAND", "WINDOW", "REGION") for e in "RX"}
    check(used and used <= est, f"every estimand the page can make a passport of ({len(used)}) is routed{': ' + str(sorted(used - est)) if not used <= est else ''}")
    print("The engineering record")
    missing = [(b, c) for b, r in REC.items() for c in r["code"] if not re.search(r"(function " + re.escape(c) + r"\(|const " + re.escape(c) + r" = )", both)]
    check(set(REC) == set(B) and not missing, f"every binding has its record and every code anchor exists{': ' + str(missing) if missing else ''}")
    harness = HARNESS.read_text(encoding="utf-8")
    lost = [m for m in M if f"check('{m}'" not in harness or not re.search(rf"\n  async {HARNESS_OF[m]}\(B\)", harness)]
    check(not lost, f"every M01–M18 is executed by its scenario of tests/swpc11_browser.mjs{': ' + str(lost) if lost else ''}")
    gen = passports(page)
    filled = all("|  |" not in gen.split(f"## {b} ")[1].split("\n## ")[0] for b in B)
    check(filled, "every passport of B01–B16 has every field of §3.1")
    print("SC-1.1 and the generated passports")
    reg = C.registry()
    ed = next(e for e in reg["editions"] if e["id"] == "DR-LAB-SC-1.1")
    check(ed["document_sha256_lf"] == C.sha256_lf(ROOT / "spec" / "DR-LAB-Semantic-Contract-1.1-(patched).md") and not C.stale(), "SC-1.1 stays pinned and its machine form compiled (SWPC changes no meaning)")
    if write:
        OUT.write_text(gen, encoding="utf-8", newline="\n")
        print("  ..  wrote " + str(OUT.relative_to(ROOT)))
    current = OUT.read_text(encoding="utf-8").replace("\r\n", "\n") if OUT.exists() else ""
    check(current == gen, f"{OUT.relative_to(ROOT)} equals what the document and the record give (python -B tests/swpc11.py --write)")
    # the candidate under acceptance (meaning/16): is the build on disk the one its passport names? (information only)
    kp = ROOT / "spec" / "ekran-24" / "swpc-kandidat.json"
    if kp.exists():
        import hashlib
        k = json.loads(kp.read_text(encoding="utf-8"))
        disk = {f: hashlib.sha256((ROOT / "lab" / "dist" / "24" / f).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for f in ("index.html", "d24.js")}
        print(f"  ..  the build on disk {'IS' if disk == k['served_sha256'] else 'is NOT'} the candidate of the passport ({k['candidate_commit'][:10]})")
    print()
    print("ALL GOOD" if not failures else f"{len(failures)} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv[1:]))
