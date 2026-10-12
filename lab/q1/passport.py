"""What the Q1 pilot claims and in which words (its own passport; it is not a profile of the accepted SC-1.1 gate).

Source of meaning: meaning/lens/2026-10-12-independent-srs/03-q1-historical-pilot.md (Q1-PILOT-0.2, frozen at commit
3dac913, PR #5); supporting definitions KADR-1.1 ed. 2 §§3-5; AGENTS.md and DR-LAB-SC-1.1 govern both. Every word the
review page shows next to a number comes from here (the page writes none of its own).
"""
from __future__ import annotations

PROFILE = "Q1-PILOT-0.2"
STATUS = "PILOT_OUTSIDE_SC11_GATE"
HEADER = f"profile={PROFILE}; claim=C1; status={STATUS}"

LEVEL_NAMES = {"0": "край IDR (0)", "-1/2": "середина IDR (−0,5)", "-7/10": "начало retirement (−0,7)"}

ESTIMATORS = {
    # the order of decision D1 (Q1 §2): weekday family / the same key without the weekday / GEO; no default is chosen here
    "NODEPOS_WD": dict(
        name="Семья дня недели",
        set_ru="та же сторона, то же 15-минутное окно подтверждения и тот же день недели (как семья карты экрана 24)",
        rule="instrument x block x weekday x side x 15-minute confirmation window, dates strictly earlier",
        status="кандидат D1"),
    "NODEPOS_ALL": dict(
        name="Ключ без дня недели",
        set_ru="та же сторона и то же 15-минутное окно подтверждения, все дни недели",
        rule="instrument x block x side x 15-minute confirmation window, dates strictly earlier",
        status="кандидат D1"),
    "GEO": dict(
        name="Все подтверждённые сессии",
        set_ru="все подтверждённые сессии этого инструмента и этой сессии: любая сторона (в зеркальной шкале своей "
               "стороны), любое окно подтверждения, любой день недели",
        rule="instrument x block, any side / window / weekday, dates strictly earlier",
        status="исследовательский кандидат (замер D), не выбранный оператором вариант"),
}

CLAIM = dict(
    claim_class="C1",
    question_ru="Дойдёт ли цена после этого среза до выбранного места до конца сессии?",
    event_ru="хотя бы одна свеча M5, закрывшаяся после среза и не позже конца сессии, дошла до места "
             "(минимум свечи на месте или за ним; открытие за местом тоже считается)",
    condition_ru="в этот же час по часам Нью-Йорка: подтверждение уже было и после него закрылась хотя бы одна свеча M5, "
                 "все свечи после подтверждения есть, DR цел; после своего подтверждения до места ещё не доходили; "
                 "закрытие на срезе — в пределах ¼ ширины IDR от сегодняшнего, каждая в своей шкале",
    horizon_ru="от среза до конца сессии; слом DR после среза горизонт не сокращает",
    unknown_ru="неизвестно — до места не дошли среди имеющихся свечей, но какой-то свечи M5 после среза в базе нет",
    forbidden_ru=["шанс, что сегодня дойдёт", "место разворота или конец отката", "вход или исполнение ордера на месте",
                  "доля всей семьи", "время, когда дойдёт"],
    grammar_ru="история прошедшим временем: «дошли», «не дошли»; не «дойдёт с вероятностью»",
)

STATES = {
    "OPEN": "Вопрос открыт: после подтверждения до места ещё не доходили, время до конца сессии есть",
    "RESOLVED": "Уже дошли: свеча {time} дошла до места — вопрос решён фактом, доли нет",
    "PREFIX_UNKNOWN": "Ответа нет: в пути после подтверждения нет целой свечи M5, состояние на срезе не определено",
    "DR_BROKEN": "DR сломан закрытием {time}: вопрос этого пилота больше не задаётся (прежние выпуски сохраняются)",
    "NO_PREFIX": "После подтверждения ещё не закрылась ни одна свеча M5",
    "BLOCK_OVER": "Сессия закончилась: после среза свечей нет",
}

PUBLICATION = {
    "PUBLISHED": "число показано",
    "WITHHELD_FEW_SESSIONS": "мало сессий: n={n} — число не показываем, счёт сохранён",
    "NO_KNOWN_OUTCOME": "у всех сессий набора исход неизвестен — числа нет",
    "REFERENCE_MISMATCH": "вторая реализация не совпала — число снято, причина в выпуске",
}

REASONS = {
    "NOT_ACTIVATED": "к этому часу ещё не подтвердилась",
    "PREFIX_HOLE": "после подтверждения нет целой свечи M5",
    "DR_BROKEN": "к этому часу DR уже сломан",
    "ALREADY_AT_L": "после подтверждения уже была у места",
    "FAR": "закрытие дальше ¼ ширины IDR от сегодняшнего",
    "MATCH": "в наборе",
}

LABELS = {"YES": "дошли", "NO": "не дошли", "UNKNOWN": "неизвестно"}


def catalog():
    return dict(profile=PROFILE, status=STATUS, levels=LEVEL_NAMES, estimators=ESTIMATORS, claim=CLAIM, states=STATES,
                publication=PUBLICATION, reasons=REASONS, labels=LABELS)
