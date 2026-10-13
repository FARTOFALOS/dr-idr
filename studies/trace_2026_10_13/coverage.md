# Покрытие архитектуры 0.1 / 0.2 — сгенерировано `python -B lab/semtrace.py run`

Прогон 2026-10-13T07:38:05Z · git:HEAD b08fb11450d9aab5 · DR-LAB-SC-1.1:registry 91f2b874fb5efe9d · DR-LAB-SC-1.1:document-pin 895948b9926bfaf7 · trace:catalog 48af53fc9a6e67aa

Статус проверки — результат ЭТОГО прогона (`trace:`), запуск существующих тестов (`test:`) — их собственными командами; `reported:` — отчёт исполнителя без повтора; `human:` — человеческий акт, машиной не заменяется.

| ID | Что | Решение | Реализовано | Проверки этого прогона | Прочие проверки | Границы |
|---|---|---|---|---|---|---|
| ENT-01 | наблюдение M1 (ObservationM1) | ACCEPTED | OBS:G3-TAPE, class:ObservationSource | — | test:tests/smoke.py | GAP-09 |
| ENT-02 | закрытая M5 — атом измерения (ObservationM5) | ACCEPTED | TF:ET-M5-1, class:ObservationRecordForm, SRC:OPERATOR-ATOM-2026-10-01 | GATE-CONFORMANT PASS | test:tests/sem24.py, test:tests/contract_sc11.py::k12, runtime:lab/contract.py::attach_day | — |
| ENT-03 | торговая сессия (TradingSession) | ACCEPTED | RULE:DRIDR-24-1, class:StrategySessionRecord, class:SessionBlock | GATE-CONFORMANT PASS | test:tests/contract_sc11.py::k05, test:tests/smoke.py | BND-01 |
| ENT-04 | коробка DR / IDR | ACCEPTED | RULE:DRIDR-24-1, class:StrategySessionRecord | GATE-CONFORMANT PASS | test:tests/sem24.py, runtime:lab/contract.py::verify_snapshot | — |
| ENT-05 | подтверждение (Confirmation) | ACCEPTED | RULE:DRIDR-24-1, class:ActivationEvent | GATE-CONFORMANT PASS | test:tests/contract_sc11.py::k01, test:tests/contract_sc11.py::k02, test:tests/sem24.py | — |
| ENT-06 | слом DR (DRBreak) | ACCEPTED | RULE:DRIDR-24-1, CS:F-BREAK-1, OUT:DR-OUTCOME-1 | — | test:tests/contract_sc11.py::k14, test:tests/contract_sc11.py::k26, test:tests/sem24.py | — |
| ENT-07 | измерительная рамка u = d (p − e) / w | ACCEPTED | MF:CONFIRMATION-1, MF:BREAK-1, GRID:K10-J15-1, class:MeasurementFrameRecord | GATE-CONFORMANT PASS | test:tests/contract_sc11.py::k06, test:tests/contract_sc11.py::k07, test:tests/q1_pilot.py | — |
| ENT-08 | часы и срез (Clock / Cut) | ACCEPTED | TF:ET-M5-1, CUT:LAST-CLOSED-M5-1, CUT:NOW-COMMON-CLOCK-1, class:KnowledgeCut | FUTURE-TARGET PASS | test:tests/contract_sc11.py::k04, test:tests/contract_sc11.py::k10 | — |
| ENT-09 | известный префикс (ObservedPrefix) | ACCEPTED | CUT:NOW-COMMON-CLOCK-1, class:PrefixState | FUTURE-TARGET PASS | test:tests/contract_sc11.py::k08, test:tests/now24.py, test:tests/arrive24.py::test_boundary | — |
| ENT-10 | состояние на срезе (CurrentState) | ACCEPTED | class:PrefixState, class:ReachabilityAssessment, class:HistoryClockAssessment, FF:TODAY-PREFIX, FF:K-TARGET | FUTURE-TARGET PASS | test:tests/contract_sc11.py::k24, test:tests/contract_sc11.py::k25, test:tests/arrive24.py::test_statuses | — |
| ENT-11 | базовая семья F (BASEFamily) | ACCEPTED | CS:F-CONF-1, CS:F-CONF-ALL-1, CS:F-BREAK-1, CS:F-BREAK-ALL-1, class:CaseSetSnapshot | IDENTITY PASS, FUTURE-MEMBERS PASS | runtime:lab/contract.py::verify_snapshot, test:tests/contract_sc11.py::k09, test:tests/contract_sc11.py::k11 | — |
| ENT-12 | исторический путь (HistoryPath) | ACCEPTED | OBS:G3-TAPE, class:CaseSetSnapshot | GATE-CONFORMANT PASS | runtime:lab/contract.py::verify_snapshot, test:tests/sem24.py | — |
| ENT-13 | окончательные R / X (ProjectionR/X) | ACCEPTED | OUT:FINAL-R-1, OUT:FINAL-X-1, EST:B-RX-JOINT-R, EST:B-RX-JOINT-X | GATE-CONFORMANT PASS | test:tests/contract_sc11.py::k03, test:tests/contract_sc11.py::k04, test:tests/contract_sc11.py::k31 | — |
| ENT-14 | карта зон (ZoneMap) | ACCEPTED | ALG:ZONE-MAP-3, REG:ZONE-MASK-1, OUT:ZONE-MEMBERSHIP-1, EST:B-ZONE-R, EST:B-ZONE-X, class:DensityRegion | IDENTITY PASS | runtime:lab/contract.py::verify_zones, test:tests/contract_sc11.py::k30, test:tests/sem24.py | — |
| ENT-15 | набор NOW (NOWCaseSet) | ACCEPTED | CS:NOW-ELIGIBLE-1, CS:NOW-MATCH-M1-1, CS:NOW-MATCH-M2-1, CS:NOW-MATCH-M3-1, CMP:B0-1 | FUTURE-MEMBERS PASS | test:tests/now24.py, test:tests/contract_sc11.py::k27 | — |
| ENT-16 | вопрос (Question) — определение, запрос, цель, оцениваемая величина | ACCEPTED | class:TraderQuestionSpecification, class:QuestionRequest, class:EstimandSpecification, Q:B-ZONE, Q:N-NEW, Q:K-ARRIVE | ESTIMAND-CHAIN PASS | test:tests/contract_sc11.py::test_registry_structure | — |
| ENT-17 | цель Q1 (Target) | PILOT_OUTSIDE_GATE | class:Q1TargetIdentity, SRC:Q1-STORE | Q1-STORE PASS | test:tests/q1_pilot.py | — |
| ENT-18 | правило сопоставления и способ оценки (Estimator / Matcher) | ACCEPTED | CMP:B0-1, CMP:M1-1, CMP:K-POS-1, ESTR:NOW-POINT-BOUNDS-1, ESTR:K-POINT-BOUNDS-1 | — | test:tests/now24.py, test:tests/arrive24.py::test_identity, reported:studies/q1_pilot_2026_10_12/README.md | — |
| ENT-19 | родитель Q1 (Q1Parent) | PROPOSED_FOR_ACCEPTANCE | CS:F-CONF-1, CS:F-CONF-ALL-1 | Q1-ISSUE-MATCH PASS | test:tests/arrive24.py::test_identity | GAP-01 |
| ENT-20 | набор сопоставимых Q1 (Q1MatchSet) | PROPOSED_FOR_ACCEPTANCE | CS:K-ARRIVE-1, CS:K-ARRIVE-ALL-1, CMP:K-POS-1 | FUTURE-MEMBERS PASS, BUNDLE-COUNTS PASS | runtime:lab/contract.py::verify_arrive, test:tests/arrive24.py::test_identity | — |
| ENT-21 | метка исхода YES / NO / UNKNOWN (OutcomeLabel) | ACCEPTED | OUT:REACH-REST-1, OUT:NEW-R-1, enum:BinaryKnowledge | BUNDLE-COUNTS PASS | test:tests/contract_sc11.py::k13, test:tests/contract_sc11.py::k23, test:tests/q1_pilot.py | — |
| ENT-22 | опора (Support) | ACCEPTED | class:SupportRecord, class:ComponentSupport | BUNDLE-COUNTS PASS | test:tests/contract_sc11.py::test_live_envelopes | — |
| ENT-23 | оценка (Estimate) | ACCEPTED | class:Estimate, class:DerivationRecord, class:StatisticalResultBundle | BUNDLE-COUNTS PASS, GATE-CONFORMANT PASS | test:tests/contract_sc11.py::k16 | — |
| ENT-24 | допустимое утверждение (Claim) | ACCEPTED | class:ClaimForm, class:Claim, CF:B-ZONE-R, CF:N-NEW-R, CF:K-ARRIVE | CLAIM-PROFILE PASS, BUNDLE-CLAIM PASS | test:tests/contract_sc11.py::k28, test:tests/contract_sc11.py::k33 | — |
| ENT-25 | выпуск (Issue) | PILOT_OUTSIDE_GATE | class:Q1IssueIdentity, SRC:Q1-STORE | Q1-STORE PASS | test:tests/q1_pilot.py | BND-07 |
| ENT-26 | последующий исход и его ревизии (ObservedOutcome) | PILOT_OUTSIDE_GATE | class:Q1OutcomeLink, SRC:Q1-STORE | Q1-STORE PASS | test:tests/q1_pilot.py | — |
| ENT-27 | свидетельство и проверка (Evidence / Validation) | ACCEPTED | class:ValidationRecord, class:ContractObligation, class:ArchitectureCheckEvidence, VAL:NOW-1.0-WALKFORWARD, VAL:SC-1.1-C | CHECK-REFS PASS | test:tests/contract_sc11.py::test_enforcement_map | — |
| ENT-28 | привязка представления (PresentationBinding) | IMPLEMENTATION_TARGET | class:StatisticalPresentationBinding, class:FactPresentationBinding, class:AbsencePresentationBinding, SRC:SWPC-1.1 | BINDING-COVERAGE PASS, SCREEN PASS | test:tests/swpc11.py | — |
| ENT-29 | состояние экрана (ScreenState) | IMPLEMENTATION_TARGET | class:ScreenStateRecord, class:ScreenElementRecord | SCREEN PASS | test:tests/ui_check24.js | BND-05 |
| ENT-30 | прочтение трейдером (OperatorReading) | OPEN | SRC:SWPC-H-PROTOCOL, SRC:OPERATOR-2026-10-13-NO-READING-QUESTIONS | — | human:operator | GAP-10 |
| ENT-31 | решение оператора (OperatorDecision) | ACCEPTED | class:AcceptanceRecord, class:ProfileStanding, SRC:DECISIONS, SRC:M07 | STANDING PASS | human:operator | GAP-01, GAP-02, GAP-03 |
| ENT-32 | реестр контракта и шлюз (ContractRegistry / Gate) | ACCEPTED | DR-LAB-SC-1.1, OB:SOURCE-OF-TRUTH, OB:CLAIM-ADMISSION, class:ContractEnvelope | GATE-CONFORMANT PASS | test:tests/contract_sc11.py::test_stale_fails_closed | — |
| R01 | M1 → M5 | ACCEPTED | TF:ET-M5-1 | — | test:tests/smoke.py | GAP-09 |
| R02 | M5 → сессия | ACCEPTED | RULE:DRIDR-24-1, TF:ET-M5-1 | — | test:tests/contract_sc11.py::k05, test:tests/sem24.py | — |
| R03 | сессия → коробка DR / IDR | ACCEPTED | RULE:DRIDR-24-1 | GATE-CONFORMANT PASS | runtime:lab/contract.py::verify_snapshot | — |
| R04 | коробка + M5 после неё → подтверждение / слом | ACCEPTED | RULE:DRIDR-24-1, class:ActivationEvent | GATE-CONFORMANT PASS | test:tests/contract_sc11.py::k02 | — |
| R05 | подтверждение → рамка (d, e, w своей сессии) | ACCEPTED | MF:CONFIRMATION-1, MF:BREAK-1 | — | test:tests/contract_sc11.py::k06 | — |
| R06 | подтверждение + ключ → семья F (один N) | ACCEPTED | CS:F-CONF-1, CS:F-BREAK-1 | IDENTITY PASS | runtime:lab/contract.py::verify_snapshot, test:tests/contract_sc11.py::k26 | — |
| R07 | сессия + срез → префикс / состояние | ACCEPTED | CUT:LAST-CLOSED-M5-1, CUT:NOW-COMMON-CLOCK-1, class:PrefixState | FUTURE-TARGET PASS | test:tests/contract_sc11.py::k08 | — |
| R08 | вопрос + цель + рамка + срез → предикат события | ACCEPTED | class:EstimandSpecification, OUT:REACH-REST-1, OUT:NEW-R-1 | ESTIMAND-CHAIN PASS | — | — |
| R09 | допустимый префикс → отбор набора (метка не выбирает) | ACCEPTED | CS:NOW-ELIGIBLE-1, CS:K-ARRIVE-1, CS:K-ARRIVE-ALL-1 | FUTURE-MEMBERS PASS | test:tests/contract_sc11.py::k09 | — |
| R10 | путь + предикат → метка исхода | ACCEPTED | OUT:REACH-REST-1, OUT:NEW-R-1, OUT:FINAL-R-1 | BUNDLE-COUNTS PASS | test:tests/contract_sc11.py::k13, test:tests/contract_sc11.py::k23 | — |
| R11 | набор + метки + правило неизвестного → оценка и опора (параллельно) | ACCEPTED | class:DerivationRecord, class:Estimate, class:SupportRecord | BUNDLE-COUNTS PASS | test:tests/contract_sc11.py::k16 | — |
| R12 | оценка + форма утверждения + профиль → допуск | ACCEPTED | class:ClaimForm, OB:CLAIM-ADMISSION | CLAIM-PROFILE PASS, BUNDLE-CLAIM PASS | test:tests/contract_sc11.py::k32 | — |
| R13 | утверждение + привязка → элемент экрана | IMPLEMENTATION_TARGET | class:StatisticalPresentationBinding, SRC:SWPC-1.1 | SCREEN PASS | test:tests/ui_check24.js | — |
| R14 | элемент экрана + H-задача → свидетельство прочтения | OPEN | SRC:SWPC-H-PROTOCOL | — | human:operator | GAP-10 |
| R15 | выпуск + последующий исход → связь (выпуск не меняется) | PILOT_OUTSIDE_GATE | class:Q1OutcomeLink | Q1-STORE PASS | test:tests/q1_pilot.py | — |
| R16 | результат проверки → новая модель / решение (не задним числом) | OPEN | class:ValidationRecord, class:AcceptanceRecord | — | human:operator | GAP-07 |
| INV-01 | измерительная шкала u = d (p − e) / w, целые тики | ACCEPTED | MF:CONFIRMATION-1, GRID:K10-J15-1 | — | test:tests/contract_sc11.py::k06, test:tests/contract_sc11.py::k07 | — |
| INV-02 | часы ET, метка M5 = открытие, знание = закрытие | ACCEPTED | TF:ET-M5-1, RULE:DRIDR-24-1 | — | test:tests/contract_sc11.py::k01, test:tests/contract_sc11.py::k05, test:tests/contract_sc11.py::k10 | — |
| INV-03 | асимметрия знания: будущее цели не вход; будущее аналога — метка, не отбор | ACCEPTED | CUT:NOW-COMMON-CLOCK-1, CS:NOW-ELIGIBLE-1, CS:K-ARRIVE-ALL-1 | FUTURE-TARGET PASS, FUTURE-MEMBERS PASS | test:tests/contract_sc11.py::k08, test:tests/contract_sc11.py::k09, test:tests/arrive24.py::test_boundary | — |
| INV-04 | разные вопросы — разные величины | ACCEPTED | OUT:FINAL-R-1, OUT:REACH-REST-1, OUT:NEW-R-1 | ESTIMAND-CHAIN PASS | test:tests/contract_sc11.py::k31 | — |
| INV-05 | честный знаменатель: N семьи, n набора, n_known отдельно | ACCEPTED | class:SupportRecord, EST:B-ZONE-R, EST:N-NEW-R, EST:K-ARRIVE | BUNDLE-COUNTS PASS | test:tests/contract_sc11.py::k16, test:tests/contract_sc11.py::k27 | — |
| INV-06 | бинарный Q1: YES / NO / UNKNOWN на (t, H] | PROPOSED_FOR_ACCEPTANCE | OUT:REACH-REST-1, EST:K-ARRIVE | BUNDLE-COUNTS PASS | test:tests/q1_pilot.py, runtime:lab/contract.py::verify_arrive | — |
| INV-07 | точная близость Q1: 4 |v_h w_t − v_t w_h| ≤ w_h w_t | PROPOSED_FOR_ACCEPTANCE | CMP:K-POS-1 | — | test:tests/q1_pilot.py, runtime:lab/contract.py::verify_arrive | — |
| INV-08 | неизвестность и публикация Q1: n < 20 — без числа, точка среди известных, границы всей группы | PROPOSED_FOR_ACCEPTANCE | ESTR:K-POINT-BOUNDS-1, FF:FEW-SESSIONS, CF:K-ARRIVE | BUNDLE-COUNTS PASS | test:tests/arrive24.py::test_statuses | — |
| INV-09 | неизменяемость ответа: target_id, issue_id, отдельный исход, ревизии | PILOT_OUTSIDE_GATE | class:Q1IssueIdentity, class:Q1OutcomeLink | Q1-STORE PASS | test:tests/q1_pilot.py | — |
| INV-10 | утверждение о прошлом не становится прогнозом (C1 ≠ C2 ≠ C3) | ACCEPTED | OB:CLAIM-ADMISSION, K33 | CLAIM-PROFILE PASS | test:tests/contract_sc11.py::k33 | — |
| INV-11 | графические каналы не меняют величину; при ошибке число скрыто | IMPLEMENTATION_TARGET | K30, SRC:SWPC-1.1 | SCREEN PASS | test:tests/contract_sc11.py::k30, test:tests/swpc11_browser.mjs#m14 | — |
| INV-12 | происхождение каждой версии; 2026 закрыт | ACCEPTED | OB:NAMED-VERSIONS, OB:PROVENANCE, EDST:SC-1.1 | EDITION-ADDITIVE PASS, ACCEPTED-CODE-IDENTITY PASS | test:tests/smoke.py, test:tests/contract_sc11.py::test_pins_and_products | — |
| PROC-01 | приём истории | ACCEPTED | OBS:G3-TAPE | — | test:tests/smoke.py | GAP-09 |
| PROC-02 | сборка свечей M5 | ACCEPTED | TF:ET-M5-1 | — | test:tests/smoke.py, test:tests/sem24.py | — |
| PROC-03 | сегментация ADR / ODR / RDR | ACCEPTED | RULE:DRIDR-24-1 | — | test:tests/contract_sc11.py::k05 | — |
| PROC-04 | коробка | ACCEPTED | RULE:DRIDR-24-1 | — | runtime:lab/contract.py::verify_snapshot, test:tests/sem24.py | — |
| PROC-05 | события правила: подтверждение, окно, слом | ACCEPTED | RULE:DRIDR-24-1 | GATE-CONFORMANT PASS | test:tests/contract_sc11.py::k01, test:tests/contract_sc11.py::k02 | — |
| PROC-06 | время знания: префикс и фаза на срезе | ACCEPTED | CUT:LAST-CLOSED-M5-1, CUT:NOW-COMMON-CLOCK-1 | FUTURE-TARGET PASS | test:tests/contract_sc11.py::k08 | — |
| PROC-07 | статическая семья F / N | ACCEPTED | CS:F-CONF-1, CS:F-CONF-ALL-1 | FUTURE-MEMBERS PASS, IDENTITY PASS | runtime:lab/contract.py::verify_snapshot | — |
| PROC-08 | исторический фильм: R / X, порядок, зоны | ACCEPTED | OUT:FINAL-R-1, OUT:FIRST-ORDER-1, ALG:ZONE-MAP-3 | GATE-CONFORMANT PASS | runtime:lab/contract.py::verify_snapshot, runtime:lab/contract.py::verify_zones | — |
| PROC-09 | NOW на общем часу | ACCEPTED | CS:NOW-ELIGIBLE-1, EST:N-NEW-R | FUTURE-TARGET PASS, FUTURE-MEMBERS PASS | test:tests/now24.py, runtime:lab/contract.py::attach_now | — |
| PROC-10 | постановка вопроса Q1: OPEN / решён / неприменим | PROPOSED_FOR_ACCEPTANCE | FF:K-TARGET | FUTURE-TARGET PASS | test:tests/arrive24.py::test_statuses, test:tests/q1_pilot.py | — |
| PROC-11 | родитель и сопоставление Q1 | PROPOSED_FOR_ACCEPTANCE | CS:K-ARRIVE-1, CS:K-ARRIVE-ALL-1, CMP:K-POS-1 | FUTURE-MEMBERS PASS | test:tests/arrive24.py::test_identity, runtime:lab/contract.py::verify_arrive | GAP-01 |
| PROC-12 | разрешение исторического исхода (метка аналога) | PROPOSED_FOR_ACCEPTANCE | OUT:REACH-REST-1 | BUNDLE-COUNTS PASS | runtime:lab/contract.py::verify_arrive, reported:studies/q1_pilot_2026_10_12/README.md | — |
| PROC-13 | оценка и публикация Q1 | PROPOSED_FOR_ACCEPTANCE | EST:K-ARRIVE, CF:K-ARRIVE, ESTR:K-POINT-BOUNDS-1 | BUNDLE-CLAIM PASS, BUNDLE-COUNTS PASS | test:tests/arrive24.py::test_gate | — |
| PROC-14 | контрактный шлюз main | ACCEPTED | OB:CLAIM-ADMISSION, OB:REFERENCE-RECOMPUTATION | GATE-CONFORMANT PASS | test:tests/contract_sc11.py::test_live_envelopes | — |
| PROC-15 | выпуск и ревизии Q1 | PILOT_OUTSIDE_GATE | class:Q1IssueIdentity, class:Q1OutcomeLink | Q1-STORE PASS | test:tests/q1_pilot.py | BND-07 |
| PROC-16 | API: ответ или отказ с контекстом и версией | ACCEPTED | API:/api/d24/family, API:/api/d24/now, API:/api/d24/arrive, class:ContractEnvelope | GATE-CONFORMANT PASS | test:tests/contract_sc11.py::test_routes_and_encodings | GAP-08 |
| PROC-17 | представление на экране 24 | IMPLEMENTATION_TARGET | SRC:SWPC-1.1, class:StatisticalPresentationBinding | SCREEN PASS | test:tests/swpc11.py, test:tests/ui_check24.js, reported:spec/ekran-24/swpc-kandidat.json | — |
| PROC-18 | прочтение трейдером | OPEN | SRC:SWPC-H-PROTOCOL | — | human:operator | GAP-10 |
| PROC-19 | внешний прогнозный тест (C2) | OPEN | OB:STATISTICAL-TRANSFER | — | human:operator | GAP-07 |
| PROC-20 | эволюция определений и версий | ACCEPTED | OB:NAMED-VERSIONS, OB:SOURCE-OF-TRUTH, EDST:SC-1.1 | EDITION-ADDITIVE PASS, IMPACT PASS | test:tests/contract_sc11.py::test_pins_and_products | — |
| T01 | G3 → M1 | ACCEPTED | OBS:G3-TAPE | — | test:tests/smoke.py | GAP-09 |
| T02 | M1 → M5 | ACCEPTED | TF:ET-M5-1 | — | test:tests/sem24.py, test:tests/smoke.py | — |
| T03 | M5 → DR / IDR | ACCEPTED | RULE:DRIDR-24-1 | GATE-CONFORMANT PASS | runtime:lab/contract.py::verify_snapshot | — |
| T04 | DR / IDR → подтверждение | ACCEPTED | RULE:DRIDR-24-1, class:ActivationEvent | GATE-CONFORMANT PASS | test:tests/contract_sc11.py::k02 | — |
| T05 | подтверждение → F / N | ACCEPTED | CS:F-CONF-1 | FUTURE-MEMBERS PASS, IDENTITY PASS | runtime:lab/contract.py::verify_snapshot | — |
| T06 | F и пути → R / X / зоны | ACCEPTED | OUT:FINAL-R-1, ALG:ZONE-MAP-3 | GATE-CONFORMANT PASS | runtime:lab/contract.py::verify_zones | — |
| T07 | срез → состояние NOW | ACCEPTED | CUT:NOW-COMMON-CLOCK-1, class:PrefixState | FUTURE-TARGET PASS | test:tests/now24.py | — |
| T08 | состояние → отбор NOW | ACCEPTED | CS:NOW-ELIGIBLE-1, CMP:B0-1 | FUTURE-MEMBERS PASS | runtime:lab/contract.py::attach_now | — |
| T09 | текущая цель → вопрос Q1 | PROPOSED_FOR_ACCEPTANCE | FF:K-TARGET, class:Q1TargetIdentity | FUTURE-TARGET PASS | test:tests/arrive24.py::test_statuses | — |
| T10 | родитель Q1 → состав набора | PROPOSED_FOR_ACCEPTANCE | CS:K-ARRIVE-1, CS:K-ARRIVE-ALL-1 | FUTURE-MEMBERS PASS | test:tests/arrive24.py::test_identity, reported:studies/q1_pilot_2026_10_12/README.md | GAP-01 |
| T11 | состав → метки | PROPOSED_FOR_ACCEPTANCE | OUT:REACH-REST-1 | BUNDLE-COUNTS PASS | runtime:lab/contract.py::verify_arrive | — |
| T12 | метки → неизменяемый выпуск / исход | PILOT_OUTSIDE_GATE | class:Q1IssueIdentity, class:Q1OutcomeLink | Q1-STORE PASS, Q1-ISSUE-MATCH PASS | — | BND-07 |
| T13 | оценка BASE / NOW → утверждение | ACCEPTED | OB:CLAIM-ADMISSION, CF:B-ZONE-R, CF:N-NEW-R | BUNDLE-CLAIM PASS | test:tests/contract_sc11.py::k28 | — |
| T14 | оценка Q1 → утверждение под шлюзом SC-1.1 | PROPOSED_FOR_ACCEPTANCE | EST:K-ARRIVE, CF:K-ARRIVE, API:/api/d24/arrive, STANDING:ARRIVE-24 | BUNDLE-CLAIM PASS | test:tests/contract_sc11.py::test_arrive_profile, test:tests/arrive24.py::test_gate | GAP-06 |
| T15 | утверждение → экран 24 | IMPLEMENTATION_TARGET | class:StatisticalPresentationBinding, SRC:SWPC-1.1 | SCREEN PASS | test:tests/ui_check24.js | BND-05 |
| T16 | Q1 → экран 24 | PROPOSED_FOR_ACCEPTANCE | STANDING:ARRIVE-24, SRC:M18 | SCREEN PASS | test:tests/swpc11_browser.mjs#m20 | GAP-02 |
| T17 | экран → понимание трейдера | OPEN | SRC:SWPC-H-PROTOCOL | — | human:operator | GAP-10 |
| T18 | C1 → C2 | OPEN | OB:STATISTICAL-TRANSFER | — | test:tests/contract_sc11.py::k28, human:operator | GAP-07 |
| T19 | C2 → C3 | OUT_OF_SCOPE | K32 | — | test:tests/contract_sc11.py::k32 | — |
| A01 | использована реальная история, а не demo | ACCEPTED | OBS:G3-TAPE | GATE-CONFORMANT PASS | test:tests/smoke.py | GAP-09 |
| A02 | 2026 не вошёл в историческую базу | ACCEPTED | OBS:G3-TAPE | — | test:tests/smoke.py | — |
| A03 | DR / IDR по действующей M5-формуле | ACCEPTED | RULE:DRIDR-24-1 | — | test:tests/sem24.py, runtime:lab/contract.py::verify_snapshot | — |
| A04 | окно 15m / день / сторона вычислены верно | ACCEPTED | CS:F-CONF-1 | — | test:tests/contract_sc11.py::k01, runtime:lab/contract.py::verify_snapshot | — |
| A05 | после слома исходная F не перезаписана | ACCEPTED | CS:F-BREAK-1 | — | test:tests/contract_sc11.py::k26 | — |
| A06 | доля BASE имеет один N | ACCEPTED | EST:B-ZONE-R | BUNDLE-COUNTS PASS | test:tests/ui_check24.js | — |
| A07 | NOW не использует будущее цели для отбора | ACCEPTED | CS:NOW-ELIGIBLE-1 | FUTURE-TARGET PASS | test:tests/contract_sc11.py::k08 | — |
| A08 | будущее цели Q1 не влияет на выпуск | PILOT_OUTSIDE_GATE | class:Q1IssueIdentity | FUTURE-TARGET PASS | test:tests/q1_pilot.py, test:tests/arrive24.py::test_boundary | — |
| A09 | аналог Q1 выбирается без будущего | PROPOSED_FOR_ACCEPTANCE | CS:K-ARRIVE-ALL-1 | FUTURE-MEMBERS PASS | reported:studies/q1_pilot_2026_10_12/README.md | — |
| A10 | точное сравнение ±1/4 без округления | PROPOSED_FOR_ACCEPTANCE | CMP:K-POS-1 | — | test:tests/q1_pilot.py | — |
| A11 | UNKNOWN не исчезает из группы | PROPOSED_FOR_ACCEPTANCE | ESTR:K-POINT-BOUNDS-1 | BUNDLE-COUNTS PASS | test:tests/q1_pilot.py | — |
| A12 | n < 20 оставляет след, но не число | PROPOSED_FOR_ACCEPTANCE | FF:FEW-SESSIONS | Q1-STORE PASS | test:tests/arrive24.py::test_statuses | — |
| A13 | выпуск неизменен, исход отдельный | PILOT_OUTSIDE_GATE | class:Q1OutcomeLink | Q1-STORE PASS | test:tests/q1_pilot.py | — |
| A14 | повтор воспроизводит входы выпуска | PILOT_OUTSIDE_GATE | class:Q1IssueIdentity | Q1-STORE PASS | — | — |
| A15 | пройденный A/D — равенство процедур | PILOT_OUTSIDE_GATE | SRC:Q1-EVIDENCE | — | reported:studies/q1_pilot_2026_10_12/README.md, test:tests/arrive24.py::test_identity | BND-08 |
| A16 | счёт и слова экрана 24 относятся к одному estimand | ACCEPTED | OB:PAGE-PASSPORTS, OB:PAGE-WORDS | SCREEN PASS | test:tests/ui_check24.js | GAP-10 |
| A17 | ошибки контракта скрывают число | ACCEPTED | OB:SOURCE-OF-TRUTH | — | test:tests/contract_sc11.py::test_stale_fails_closed, test:tests/arrive24.py::test_gate | — |
| A18 | Q1 не спутают с BASE, NOW, прогнозом | OPEN | CF:K-ARRIVE | — | human:operator | GAP-10 |
| A19 | Q1 переносим на следующие дни | OPEN | OB:STATISTICAL-TRANSFER | — | human:operator | GAP-07 |
| A20 | визуальная интеграция Q1 сохраняет смысл экрана 24 | PROPOSED_FOR_ACCEPTANCE | STANDING:ARRIVE-24 | SCREEN PASS | test:tests/swpc11_browser.mjs#m20, human:operator | GAP-02, GAP-10 |

## Границы, не объявленные закрытыми

| ID | Вид | Что | Чей ход |
|---|---|---|---|
| GAP-01 | OPEN_DECISION | какой родитель основной для ответа «отсюда» (D1) | оператор |
| GAP-02 | OPEN_DECISION | как встроить «отсюда» в экран 24 (D2) | оператор |
| GAP-03 | OPEN_DECISION | остаток после общего t или после собственной активации в лесенке (N5) | оператор |
| GAP-04 | OPEN_DECISION | вариант 08.10 (PR #2) не принят | оператор |
| GAP-05 | OPEN_EVIDENCE | SWPC-1.1 — реализация есть, человеческая приёмка нет | оператор (H-сессия); исполнитель (переписать лист задач словами трейдера) |
| GAP-06 | OPEN_DECISION | Q1 под шлюзом SC-1.1 — только кандидатная поправка | оператор |
| GAP-07 | OPEN_EVIDENCE | перенос на новые дни (C2) не проверен | оператор (протокол и допуск); исследование |
| GAP-08 | KNOWN_LIMIT | диагностический API пилота отдаёт полный путь | инженер (ограничить endpoint или сузить утверждение) |
| GAP-09 | OUT_OF_SCOPE | происхождение и качество ленты G3 не переаудированы | исследование G3 |
| GAP-10 | OPEN_EVIDENCE | экран → человек | оператор |
| GAP-11 | OUT_OF_SCOPE | широкая исследовательская программа (SRS 0.2) | исследование |
| BND-01 | KNOWN_LIMIT | запись сессии требует коробку и активацию | инженер (новый тип записи при расширении области) |
| BND-02 | FINDING | статус профиля в реестре смешивает «действует» и «принято» | оператор (принять или отклонить варианты); инженер (отдельная ось решения в реестре — изменение SC-1.1, только с полномочием) |
| BND-03 | FINDING | версия кода во входах bundle шире, чем вычисление | инженер (по-функциональный штамп — правка шлюза, только с полномочием) |
| BND-04 | KNOWN_LIMIT | числа страницы без bundle сервера | инженер |
| BND-05 | KNOWN_LIMIT | показ проверен на безголовом экране заявленных сцен | инженер; оператор (H) |
| BND-06 | KNOWN_LIMIT | мутационные проверки будущего — на заявленных сценах | инженер |
| BND-07 | KNOWN_LIMIT | выпуски Q1 — исторические воспроизведения | оператор (нужен ли журнал показанных ответов) |
| BND-08 | OPEN_EVIDENCE | сверка A/D и скалярный пересчёт заявлены исполнителем пилота | инженер (lab/q1/recon.py --golden, ~10 минут) |
| BND-09 | OUT_OF_SCOPE | PRE-24 вне заявленной области | оператор (расширение области) |
| BND-10 | OUT_OF_SCOPE | устаревшие поверхности вне SC-1.1 | оператор |
| BND-11 | KNOWN_LIMIT | связи «код → код» статические | инженер |

## Сквозные сцены

| Сцена | Утверждение | Решение | Модель | Реализация | Показ (машина) | Показ (человек) | Достоверно в заявленной области |
|---|---|---|---|---|---|---|---|
| SCENE:BASE-ZONE | EST:B-ZONE-R {"label": "R1"} | ACCEPTED | DEFINED | VERIFIED_IN_RUN | VERIFIED_IN_RUN | PENDING | да |
| SCENE:NOW-NEW | EST:N-NEW-R {"role": "MAIN"} | ACCEPTED | DEFINED | VERIFIED_IN_RUN | VERIFIED_IN_RUN | PENDING | да |
| SCENE:ARRIVE-HALF | EST:K-ARRIVE {"level": "-1/2"} | PROPOSED_FOR_ACCEPTANCE | DEFINED | VERIFIED_IN_RUN | VERIFIED_IN_RUN | PENDING | да |
| SCENE:ARRIVE-FEW | EST:K-ARRIVE {"level": "-1/2"} — нет числа: FEW_SESSIONS | PROPOSED_FOR_ACCEPTANCE | DEFINED | VERIFIED_IN_RUN | VERIFIED_IN_RUN | PENDING | да |
