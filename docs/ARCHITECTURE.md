# Architecture

Everything runs on the operator's Windows PC. No cloud, no database server, no LLM at run time: the numbers come from
plain arithmetic over the history base, so the same candles always give the same screen. The main line is screen 24
(`/24/`, the root redirects there) with its routes `/api/d24/*` behind the contract gate of DR-LAB-SC-1.1
(`lab/contract.py`, `contract/README.md`); the other routes serve legacy surfaces (design 22, the classic screen, the
research dashboard, design 23) and are marked `OUTSIDE_SC11`.

**Presentation layer status (07.10.2026):** `spec/DR-LAB-SWPC-1.1.md` is the current implementation target between
SC-1.1 semantic truth and the screen-24 frontend. It is not a runtime service yet: the engineer must bind existing
components to its PresentationBindings and M01–M18, then the operator performs H01–H12. Until that work is accepted,
the current frontend remains the product baseline.

## Processes and ports

```
TradingView Desktop  --(Chrome DevTools, 127.0.0.1:9222)-->  lab/tv_fetch.mjs  (node, one shot per refresh)
                                                                   |
browser page  <--HTTP 127.0.0.1:8767-->  lab/server.py (python)  --+--> lab/scene21.py --> boxes_* (every session, M5)
 (dist/*.js)                                  |                    |    (design 22 at /22/: /api/day, /api/family, /api/cohort)
                                              |                    +--> lab/scene24.py --> boxes_* (working screen 24 at /24/: /api/d24/*)
                                              |                    +--> lab/live.py  --> lab/engine_market.py
                                              |                         (classic screen: /api/live)   (episodes in RAM)
                                              +--> lab/engine_market.py  (history dashboard of the classic screen)
```

| Process | Started by | Lifetime | Notes |
|---|---|---|---|
| TradingView Desktop with `--remote-debugging-port=9222` | launcher via `tradingview-mcp` (`node <TV_MCP_DIR>/src/cli/index.js launch`) | until the operator closes it | a local copy of the MSIX package, logged in with the operator's account |
| `python -B lab/server.py` | launcher, hidden window, logs to `lab/.runtime/server.{out,err}.log` | until `stop-dr-lab.cmd`, reboot or kill | loads the whole history base at start (~5 s) |
| `node lab/tv_fetch.mjs <symbol> 500` | the server, on every live refresh | ~1–4 s | reads bars and exits |

## Stack

- **Python 3.14** (`%LOCALAPPDATA%\Python\bin\python.exe`): stdlib `http.server` + numpy + pandas. No framework.
- **Node 24**: only for `tv_fetch.mjs`, which imports `connection.js` of the local
  tradingview-mcp checkout (`TV_MCP_DIR`) and evaluates JavaScript inside TradingView's page.
- **Front end**: static HTML/CSS/vanilla JS, SVG drawn by hand. No build step, no packages. The page is served from
  `lab/dist/`.
- **Data**: the G3 minute spine `<DR_IDR_MARKET>/<inst>/{close_ts_utc_ns,open,high,low,close}.npy` (UTC close
  timestamps, prices as float64; the tape itself never enters this repository).

## The session base of the working screen (`lab/build_boxes.py` → `lab/.runtime/boxes_*`)

Every session instance whose formation hour is complete (confirmed or not), with its seven box levels, confirmation and
DR break (if any) and its clock M5 bars from the start of the box to the end of the session (`bars` int32 [N,5] = close
minute, o, h, l, c in ticks; `offsets`; `boxes_<inst>_meta.json` → `boxes`). Same tape and definitions as below, 2026
hidden. The launcher builds it when missing. `lab/scene21.py` reads it.

## The history base (`lab/build_market.py` → `lab/.runtime/`)

Built once (the launcher builds it when missing; ~30 s per instrument):

- reads 2006-01-01 … 2025-12-31 ET for NQ, ES, YM (2026 hidden);
- groups minutes into session instances: RDR 09:30–10:30 / until 16:00, ODR 03:00–04:00 / until 08:30, ADR 19:30–20:30
  / until 02:00 next day (trading day = next day); ADR minutes after midnight are +1440;
- clock M5 buckets inside the window (all 12 required), DR = wick high/low, IDR = M5 body high/low;
- confirmation = first M5 close beyond DR after the window; outcome fields per session (DR true, retracement,
  extension, their times, completeness);
- writes `market_<inst>.npz` (`bars` int32 [N,5] = close-minute, o, h, l, c in ticks; `offsets`) and
  `market_<inst>_meta.json` (`info` incl. `census` of skipped sessions, `episodes` list). ~14 000 sessions per instrument.

Tick sizes: NQ, ES 0.25; YM 1. History bars carry the **close** minute of each M1 bar.

## HTTP API (`lab/server.py`)

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | `{status, data_kind: MARKET|SYNTHETIC, version}` — the launcher polls it |
| `GET /api/query?...` | history dashboard (see `engine_market.query`): params `instrument, session, direction (long|short|all), weekday, from, to` (confirmation minutes, window `[from,to)`), `status`, `mode (history|prefix)`, `observed`, `target`, X-ray filters `retr[_hi], ext[_hi], rtime[_hi], etime[_hi]` |
| `GET /api/scene?id=NQ-20240315-RDR` | one session with its post-confirmation M1 bars |
| `GET /api/spec` | the text of `docs/SEMANTICS.md` (the "Модель системы" view) |
| `GET /api/live?instrument=NQ&session=RDR[&at=<minute>]` | classic screen: live state from the last fetched candles; `at` = replay minute |
| `GET /api/live/refresh?...` | fetch from TradingView first, then the same as `/api/live` |
| `GET /api/day?instrument=NQ` | design 22 (legacy, `/22/`): the trading day's M5 bars from the last fetch and the previous trading day's RDR box |
| `GET /api/day/refresh?instrument=NQ` | fetch from TradingView first, then the same as `/api/day` |
| `GET /api/cohort?instrument=NQ&session=RDR[&at=<day minute>]` | design 22 (legacy): the similar sessions of 2006–2025 at the live minute or the replay minute `at` (used before a confirmation) |
| `GET /api/family?instrument=NQ&session=RDR[&at=<day minute>]` | design 22 (legacy) since 2026-09-30: today's family (after a confirmation) or break family (after today's DR break) and its whole clock M5 film |
| `GET /api/d24/day?instrument=NQ[&date=YYYY-MM-DD][&refresh=1]` | design 24: the live day (as `/api/day`, `source: live`; `refresh=1` fetches from TradingView first) or a trading date of 2006–2025 from the session base (`source: history`: its three blocks' M5, the previous RDR box, `now` = 17:00) |
| `GET /api/d24/family?instrument=NQ&session=RDR[&date=…][&at=<day minute>][&view=auto\|conf][:all]` | design 24: today's state at the slice `at` and the snapshot of its family per DR-LAB-SEM-1.0 (`lab/scene24.py`) with its zone maps (`lab/zonemap24.py`); `:all` = the all-weekdays family, an explicit choice |
| `GET /api/d24/dates?instrument=NQ` | design 24: every trading date of the base with the sessions whose first confirmation is established that day (`[[date, "AOR"], …]`) |
| `GET /api/d24/now?instrument=NQ&session=RDR[&date=…][&at=…][&view=…]` | design 24: the layer «Сейчас» of the family at the slice (DR-LAB-NOW-1.0, `lab/now24.py`) |
| `GET /api/contract` | the compiled machine contract DR-LAB-SC-1.1 (`contract/build/registry.json` with its stamps) and its runtime status (`CONFORMANT` / `CONTRACT_STALE` with reasons) |
| `POST /api/d24/verify` | body `{instrument, session, at, date, view, passports: [{id, estimand, params, yes_count, unknown_count, no_event_count, N}]}`: the page's passports recomputed by the reference definitions (`lab/contract.py::verify_passports`) → `{status, snapshot_id, checked, mismatches}`; the server's only POST, it changes nothing |

### The contract gate (`lab/contract.py`, DR-LAB-SC-1.1; `contract/README.md`)

The routes `/api/d24/family`, `/api/d24/now` and `/api/d24/day` leave through the gate. Their bodies keep the fields
below and gain `contract`: a `ContractEnvelope` of `contract/schema/dr_lab_sc.yaml` (edition, registry hash, status
`CONFORMANT` | `VIOLATION` | `CONTRACT_STALE`, the request, the records it is about — observation, session, frame,
cut, case sets, regions, reachability, history clock, prefix states —, the checks run, the violations, and one
`bundle` per published statistic: estimand, claim form, derivation with its input versions, estimates, supports, the
admissible claim classes and the claim). Before it leaves, the family snapshot, its zones, today's statuses and the NOW
numbers are re-derived by the reference definitions; a failing object is withheld (`status: contract_violation` for a
whole family, `mode: WITHHELD` for a NOW event, a missing zone map for a failed zone check). A number that no field
encoding of `contract/registry/60-surfaces.yaml` declares makes the response a violation. When the compiled contract
differs from its sources, `/api/d24/family` and `/api/d24/now` answer `status: contract_stale` with no statistic and
`/api/d24/day` still serves the candles. Every JSON response carries the header `X-DR-Lab-Contract`
(`DR-LAB-SC-1.1; profile=…; status=…; registry=…`; legacy and service routes: `status=OUTSIDE_SC11`).

### `/api/day` response (`lab/scene21.day_view`)

`status` (`ok` | `no_data`), `instrument, tick, date` (the trading day, which starts at 18:00 ET the evening before),
`weekday, now` (the fetch moment in day minutes: minutes from the trading day's midnight, the evening before negative,
18:00 = −360), `fetched_at, feed, switched, source_interval, bars` (`[day-minute of the bar OPEN, o, h, l, c]`), `prev`
(`{drH, drL, idrH, idrL, open, close, name, date}` of the previous trading day's RDR, or null), `base` (the session base
exists). The page computes DR, IDR, confirmation and DR break itself with the rules of `lab/live.py`.

### `/api/cohort` response (`lab/scene21.cohort`)

`status`: `ok` | `no_data` | `no_base` | `before` | `forming` | `done` | `noconf`. With `ok`: `mode` (`conf` = confirmed
and DR intact, `brk` = DR broken, `wait` = before a confirmation), `session, obs, o5` (the last M5 close at or before the
minute), `n, band` (0.25 | 0.5 | null = the price could not be matched), `cond` (the similarity condition in words),
`grid` (5-minute close minutes after `o5`), `u0` (today's position on the scale of the mode), `models`
(`{up, down, used}` before a confirmation, else null) and `sims` — per similar session, in its own IDR units of the
mode: `date, pos, mx, tmx, mn, tmn` (extremes after `o5` and their day minutes), `cl, hi, lo` (per grid point),
`held` (conf: no later M5 close beyond its own opposite DR), `cross` (wait: side of its first later confirmation, 0 =
none), `uH, uL` (wait: own DR high / low) and `wick` (conf: a wick beyond its own opposite DR after `o5`), the last
three since design 22 became the working screen (2026-09-29). Definitions: `docs/SEMANTICS.md`, section of design 22.

Time contract (checked 2026-09-30): today's state uses the M5 bars closed by the minute and the minute price (`u0`); a
similar session is placed by its close at `o5` and measured from `o5`, so between M5 closes its future includes the
whole current M5, up to 4 minutes that have already passed today. Time precision is M5. Unlike `live.py` `_overlay`
(minute bars strictly after the minute).

### `/api/family` response (`lab/scene21.family`)

`status`: `ok` | `no_data` | `no_base` | today's status when there is nothing to key on (`before`, `forming`, `waiting`,
`noconf`). With `ok`: `mode` (`conf` = the confirmation family, `brk` = the break family after today's DR break),
`session, t0` (the day minute of the activating M5 close: the confirmation, or the break), `side` (today's confirmation
direction), `weekday, window` (`[start, end)` day minutes of the 15-minute window of the activating candle's TradingView
label, `scene21.window_of`), `grid` (M5 close minutes from `t0 + 5` to the session end), `n` (the family size N), `cond`
(the key in words), `members` — per family session: `date, conf, fail` (its confirmation and break close minutes on the
day scale), `held` (conf: no M5 close beyond its opposite DR from its confirmation to the session end; null for brk),
`uOpp` (conf: its opposite DR edge on its scale; null for brk), `last` (its last bar), and `lo, hi, cl` per grid point in
its own IDR units of the mode (conf: 0 = its confirmation-side IDR edge, positive = the confirmation's way; brk: 0 = its
opposite IDR edge, positive = the break's way), null where it has no bar; plus `obs, o5, status_today`. The film does not
depend on the minute (cached per day and `t0`); the page takes the columns after the slice (the last closed M5) and
draws them as design 22 does. Definitions: `docs/SEMANTICS.md`, «Семья на рабочем экране».

### `/api/d24/family` response (`lab/scene24.family`, design 24)

The definitions are those of `meaning/lens/2026-10-01-spec-v1/` (DR-LAB-SEM-1.0), summarised in `docs/SEMANTICS.md`
(«Дизайн 24»). The atom is an existing M5 candle of the session base; a wholly missing M5 on an event's horizon is a hole
(operator, 2026-10-01). Everything is in integer ticks.

`status`: `ok` | `no_data` | `no_base` | today's status when there is no family (`before`, `forming`, `waiting`, `noconf`).
`today`: `{date, source, status, obs, slice, c0, side, window, brk, brkWindow, idrH, idrL, drH, drL}` (closed M5 only).
With `ok`: `semantics` (`DR-LAB-SEM-1.0`), `source` (`{base, boxes, built, history}`), `view` (`conf` | `brk`),
`available` (`{conf, brk}`), `family_id`, `snapshot_id`, `key` (`{instrument, session, weekday, direction, event,
window: [start, end) day minutes, cutoff}` — members are strictly before `cutoff`, the viewed date), `cond`, `N`, `ids`
(the session ids), `scale` (`{orientation, edge, unit, price_cell: "1/10", time_cell: 15, f}`), `schedule` (`{start,
formed, end}`), `rules` (start, end, time of an event, the atom), `grid` (close minutes of the block's common clock M5
after the box), `counts` (`R`, `X`: `{cells: [[k, b, n]], known, unknown, none}`; `order`; `outcome` for `conf`),
`journal` (undetermined keys), and `members`, one per family session:
`{id, date, w, act, conf, fail, confWin, R, X, order, orderDetail, missing, path, [oppv, outcome, brk, brkKnown, drv]}` —
`w` its IDR width in ticks; `act` its own activation close (confirmation, or the break in `brk`); `R` / `X` =
`{s: known | unknown | none, v (directed ticks), t (open minute of the first M5), ties}` (`bound` = observed so far when
unknown); `path[j]` = `[low, high, close]` in directed ticks on `grid[j]`, or null where the M5 is missing; `oppv` its
opposite DR in directed ticks. A member's u = v / w; the page carries it to today's price through today's IDR.
`key.scope` is `weekday` (the default) or `all`; `available.scopes` lists both. `zones` (`zone-map-3`,
`meaning/12-karta-zon.md`): for `R` and `X`, `{algorithm_version, family_scope, family_id, snapshot_id, event_id,
N_family, n_residual_total, unknown_count, no_event_count, min_support, study_refs, zones: [...], residual_ids}`, each
zone `{zone_id, label, peak_anchor, cell_mask: [[k, b]], price_low, price_high, time_start, time_end,
member_session_ids, n_zone, p_snapshot, grid_member_jaccard, bootstrap_recovery, null_model_id, null_status,
[null_frozen_overlap, null_validation_n, p_real_mask, p_null_mask, null_excess, null_interval,
minimum_detectable_excess]}`. `today.zones`: per event `{state: ok | none | unknown, q, v10, w, status: [HOLDS |
POSSIBLE | IMPOSSIBLE | STATUS_UNKNOWN per zone]}` at the request's slice; the page recomputes it at any slice.

### `/api/live` response

`status`: `no_data` | `no_session` | `forming` (DR window not closed) | `waiting` (DR formed, no confirmation) |
`confirmed` | `error` (`message`).

Always: `instrument, session, day, feed, switched (bool: the chart had to be switched), source_interval (5|1),
fetched_at, running, tick, start, formed, end, observed, replay, bars` — `bars` are `[open-minute, o, h, l, c,
closed]` of **M5** (live bars carry the **open** minute; history bars carry the close minute).

When the window is complete: `open, window_complete, dr_high, dr_low, idr_high, idr_low`.
`waiting`: `pending {n, long_pct, short_pct, none_pct, long_median, short_median}`.
`confirmed`: `direction, confirmation, edge, width, failed_at, now_coord, price_now, retr_so_far, ext_so_far, overlay`.

`overlay` (the similar sessions, see `docs/SEMANTICS.md`): `n, pool, band, dr_true_pct, touch {level: pct},
fan [{t, n, low, mid, high}], cluster_min / cluster_max [{lo, t, n}] (0.1 IDR × 15 min), zones_min / zones_max
[{lo, hi, t, t_hi, n, pct}] (0.2 IDR × 30 min, top 3), retr_end {lo: pct}, future_min_median, future_max_median`,
and the same cohort in the dashboard format: `charts {retr, ext, rtime, etime}, heat, curve, formed, end,
complete_n, median_retr, median_ext, median_rtime`.

## Live pipeline (`lab/live.py`)

1. `fetch(inst)` runs `tv_fetch.mjs`: first it looks for a pane of the operator's layout that already shows the future
   on 5 minutes (then 1 minute, aggregated to clock M5 and merged with older saved M5; the last 1500 bars, so the
   trading day from 18:00 ET with the ADR box is covered); only if none, it switches the
   active chart to `CME_MINI:NQ1!` / `CME_MINI:ES1!` / `CBOT_MINI:YM1!` on 5 minutes, waits for the series itself to
   be ready (series `symbolInfo()` matches, not loading, bar count stable) and restores the chart. Saves
   `lab/.runtime/live/<inst>.json`.
2. `state(inst, session, at=None)`: takes the latest instance of the session; the observed minute is the live minute
   (price = last trade of the forming M5) or the replay minute `at` (price = close of that candle; only bars closed by
   then are used). DR/IDR, confirmation, DR break: closed M5 only.
3. `_overlay(...)`: pool = same instrument, session, direction, confirmation within ±15 min, the same DR state at the
   observed minute, completed sessions; cohort = pool members whose IDR position at the observed minute is within
   ±0.25 IDR of today's (±0.5, then no limit, if fewer than 40). Everything is measured on their bars strictly after
   the observed minute.

## Front end (`lab/dist/`)

- `index.html` + `sozvezdiya.js` — **design 22 «Созвездия»** (the working screen 2026-09-29 → 10-01; since then at `/22/`,
  which redirects here), built from `design/sozvezdiya-22/src`
  by its `build.py` (edit there, never the built files): the whole trading day on a canvas, levels, stars, places and
  constellations, the fan, the right panel; data from `/api/day`, `/api/family` (after a confirmation) and `/api/cohort`
  (before one), refreshed after every M5 close while
  a session runs. Check with `tests/ui_check21.js`.
- `24/index.html` + `24/d24.js` — **screen 24 «Границы хода», the working screen since 2026-10-01 night and the main line on `main` since 2026-10-07** at `/24/`
  (the root `/` redirects here; the shortcuts «DR Lab» and «DR Lab 24», `start-dr-lab-24.cmd`
  = `start-dr-lab.ps1 -Page 24/`), built from `design/sozvezdiya-24/src` by its `build.py`: design 22's screen with the
  statistical layer of DR-LAB-SEM-1.0; data from `/api/d24/*`; a history date opens as if it were today. Check with
  `tests/ui_check24.js` (in the page) and `tests/sem24.py` (definitions). Design 22 is not changed by it. Every element,
  its count and code: `spec/ekran-24/`. Its `build.py` embeds `contract/build/page_registry.json` (estimands, claim
  forms with the words of every number, fact forms): the page shows a number only as a passport of a registered
  estimand, renders only those words, refuses envelopes of another registry and sends its passports to
  `POST /api/d24/verify` (`contract/README.md`).
- `classic.html` — **the previous screen**, kept at `/classic.html` (it was `index.html` until 2026-09-28): one page.
  `body.focus` (default) hides the research sidebar and headings; ☰ toggles it (`localStorage dr-lab-focus`).
- `app.js` — the history dashboard (sidebar filters, KPIs, bottom charts `drawPath/drawHeat/drawHist`, scenes view,
  model view). In focus mode with a confirmed live session it yields the bottom charts to `live.js`
  (`window.liveOwnsCharts()`).
- `live.js` — the live panel:
  - `liveFetch / liveOnQuery / scheduleLive`: refresh on open (if data older than 3 min), by button, and automatically
    3 s after every minute (every 5 min when the chart has to be switched); `liveOnQuery` resets replay on
    instrument/session change;
  - `drawLive(L)`: session chart (SVG): DR window shading, DR/IDR/mid/open and Pine STD lines, the 0.1…0.9 grid inside
    the DR window, cluster cells, top zone outline, fan, probability ladder, candles (clickable), confirmation and
    DR-break pills, the observed-minute line; the right-side labels are laid out without overlap; side column;
  - `drawBottom(o)`: bottom charts from the same cohort; selection highlight;
  - selection model: **one active pick at a time** across bottom bars/cells and side zones (`binSel`, `zoneSel`);
    picks are drawn on the chart as time × price cells;
  - replay: click a candle → `replayAt = close minute` → `/api/live?at=` ; click it again → live;
  - cluster card and guides: click a cluster → pinned card (left of the cluster); hover/pin → thin guides to the time
    axis and the price scale with green boundary labels (`showGuides / clearGuides / restorePin`).
- `styles.css` — base styles plus later override blocks (commented by purpose, the last ones win). Consolidating them
  is welcome if the look stays identical (verify with screenshots).

## Performance

History query 0.05–0.25 s; live state with overlay ~0.2–0.5 s; a passive TradingView read ~1–2 s, a switched read
2–4 s. The server holds ~100 MB of history in memory.

## Launcher (`start-dr-lab.ps1`)

Idempotent steps: Python with numpy/pandas → TradingView on 9222 (start via tradingview-mcp if absent; waits for a
`tradingview.com/chart` page) → history base (build if missing) → server (hidden, logs) → open the page. Saved as
UTF-8 with BOM (Windows PowerShell 5.1). `start-dr-lab.cmd -NoBrowser` runs everything except opening the page.
# Интеграционный вариант 15.10.2026

**Текущий этап:** [DELIVERY](../integration/DELIVERY.md). Описания неизменённого main/8767 и отсутствия HTTP/UI
ниже — снимок первого этапа. Текущая сборка использует обычный launcher с `--integration`; отдельный 8773 нужен
для изолированной проверки. Защищённые формулы BASE/NOW остаются прежними.

Отдельная ветка `codex/integration-first` от main267, localhost8773, [описание](../integration/README.md).
Рабочий main/8767 не изменён. `/api/integration/scene` — служебная композиция уже проверенных `day/family/NOW`
и отдельно включённых PRE/ARRIVE. У вложенных ответов собственные конверты; служба не новый оцениватель.
Контекст связывает дату/инструмент/блок/cut/view/scope, family/snapshot, ревизии пути/префикса и реестров/моделей.
Клиент коммитит только текущий контекст; чужой вложенный ответ снимается независимо от исправных частей.

Принятый контракт остаётся в `contract/`, 53 величины и исходный закреплённый текст. Кандидатное расширение
импортирует его схему в `integration/candidates`, имеет отдельную редакцию PROPOSED и не меняет допуск продукта.
`lab/integration24.py` использует существующие `scene24/now24/pre24/arrive24/q1` и тот же gate-код с отдельным
экземпляром реестра. В `revisions24` добавлен content witness для полного пути, не меняющий BASE identities.

`/api/integration/audit` — явная диагностическая операция для ожидаемого context id. Существующие Trace/FOM
функции проверяют дополнительные пересчёты/отношения в заявленной области; NOT_COVERED не превращается в PASS.
Полный исходный каталог сохранён как reference и не объявлен перепривязанным. Вычисление, показ и сохранение
issue остаются отдельными операциями; новый render не пишет issue/store. Оба сервиса объявлены в реестре как SERVICE.

## Закреплённое окно: исполняемый кандидат 15.10.2026

`lab/continuity24.py` — отдельное расчётное ядро без HTTP-маршрута, записи issue или показа процентов в UI.
Цель фиксирует исходную рамку, физические границы и M5-окно; выпуски различают идентичность цели и остаточного
вопроса. G содержит подтверждённые случаи того же инструмента/блока строго из более ранних дат; общий POS_GEO
использует только полный целый префикс на общих часах и quarter-rule по close. Условие известного непосещения
прошедшей части окна создаёт отдельный названный набор риска. Совпадение позиции не объявляется совпадением пути.

`lab/continuity_audit.py` независимо пересчитывает членство и исходы, проверяет переходы и создаёт доказательства
в существующей форме Trace/FOM. Полный замороженный каталог не перепривязан. Реальный сквозной свидетель,
граница эмпирического обоснования, пропуски и воспроизведение —
`studies/scene_continuity_2026_10_15/`; контрпримеры — `tests/continuity24.py`.
Исходный BASE/NOW, контракт, UI и обычный launcher этим модулем не изменены.

## Исполняемый режим «Продолжения»

`POST /api/integration/continuations` — только чтение, доступен при `--integration`. Запрос: instrument, session,
историческая date или live, закрытый at, scope, fixed target (low/high — рациональные координаты, first/last close,
created_at, после первого ответа — неизменная исходная frame), опциональный previous release id.
Результат: status, release_id, proof, отдельно предложенный contract, review standing. SERVICE-маршрут сам не
выдаёт принятую статистику SC-1.1; вложенный bundle имеет профиль CONTINUATIONS-24.

`continuations24` берёт реальные случаи из `now24_validate.universe`, связывает их исходные рамки с M5-путями.
Кэш по инструменту/блоку хранит readonly пути и проверяет stat-ревизии исходной базы; до восьми готовых пакетов
кэшируются по цели, закрытому префиксу, scope, версии базы/реестра и previous. Переходы сравниваются по полным
выпускам (до 64 в памяти). Нет записи торговых данных, issue или исхода при render/hover.

`continuity_audit.check_frame` независимо пересчитывает членство и исходы, проверяет target/question/остаток/факт.
Публикуемые пути проверяются побарно против реального источника, включая w, направление, активацию и исход.
SHA-256 proof связывает полный пакет; каждый путь имеет отдельный hash. Страница принимает только свой cut,
цель, префикс и реестр, повторно считает исходы диапазонов, сверяет числовой bundle и состав рисунка. Любое нарушение
снимает зависимые число/пути. Поздний fetch не меняет новую сцену. Выбор пути меняет только выделение.

`runtime_identity` связывает загруженные Python-модули и stat-ревизии локальной базы. POST проверяет их до и после
расчёта; изменение файлов требует перезапуска. Health показывает loaded/current версии и workspace. Launcher
проверяет владельца порта и запускает один актуальный скрытый процесс. Живой префикс может быть сегодняшним;
исторический запрос после 2025 отклоняется, живые свечи не попадают в статистическую базу.

Q1: prefix-v2 содержит только известные поля formation/confirmation и закрытые бары. Изменение metadata.complete
или будущего fail не меняет prefix identity; текущая версия модели отличается, старые записи остаются write-once.
Раскрываемый путь standalone-пилота требует совпадения session_digest с сохранённым outcome basis; поздний UI-ответ
привязан к исходному target/cut/request sequence. Это отдельная защита сохранённых свидетельств, не новый метод Q1.

## Кандидат «Откаты до обновления» (DR-LAB-PB-0.1), 21.10.2026

`GET /api/integration/pullbacks` — только чтение, доступен при `--integration`, 127.0.0.1. Параметры: instrument,
session, at (закрытая M5), date (история до 31.12.2025; без date — живой день тем же путём, что экран), view
(`auto` следует за экраном, `conf` — рамка подтверждения), scope. Ответ: status, release_id = SHA-256 proof, proof,
отдельный конверт кандидата (`PROFILE:PB-24`, поверхность `SC11_PULLBACKS_0_1`). Маршрут объявлен в принятом
реестре как SERVICE (`contract/registry/60-surfaces.yaml`); сам он принятой статистики SC-1.1 не выдаёт.

`lab/pullbacks24.py` берёт семью через `scene24._family` и `contract.attach_family`. Работа идёт только если семья
CONFORMANT, то есть F, N, рамка и активация те же, что на экране. Для каждого участника строятся:
- свидетельство пути: направленные M5 блока в собственной рамке случая;
- эпизоды H → L → B (определение — `meaning/lens/2026-10-21-otkaty-do-obnovleniya/03`);
- объединённые точки дна;
- порядок слома DR.

Дальше карты зон `zone-map-3` на масштабах 1 / 2 / 3 / 6 с одним голосом сессии в окрестности 3 × 3 и
сегодняшняя часть (только закрытые M5 до среза).

Кэши:
- историческая часть — по (snapshot, view, scope, ревизия кода), до 12 штук; срез её не двигает;
- готовые ответы — по (контекст, сегодняшние бары), до 6.

`lab/pullbacks_ref.py` независимо пересчитывает из базы:
- свидетельства;
- эпизоды — четыре внутрисвечных сценария и потиковый перебор;
- зоны — поиск в ширину без numpy;
- разбиение N;
- сегодняшние отношения.

Историческая сверка — раз на снимок, сегодняшняя — на каждый ответ. При расхождении `REFERENCE_MISMATCH`: ни
proof, ни bundles. Числа — только объявленные в `integration/candidates/registry/90-pullbacks.yaml` (`EST:PB-ZONE`,
`EST:PB-SESSIONS`, 32 кодировки), только C0. Страница проверяет контекст, хеши реестров и выпуска, каждую точку по
барам её сессии, каждую зону по клеткам и сегодняшние бары по своим свечам. Любое нарушение снимает зависимые
числа и рисунок.

Нет записи торговых данных, issue или исхода; объём не используется; 2026 закрыт для истории.


## Отдельная рабочая 23.5: время × SD (23.10.2026)

`design/sozvezdiya-23-5/src/build.py` → `lab/dist/23-5/`, страница `/23-5/`, запуск 8735.
Исходники/сборка 24 и `/`→`/24/` сохранены. 23.5 использует `drlab.d235.*`, 24 — `drlab.d24.*`.
Старые настройки 23.5 на первоначальном порту копируются один раз без записи в исходный namespace.

`GET /api/integration/time-sd` (только `--integration`) публикует новый кандидат DR-LAB-TIME-SD-1.0.
Параметры instrument, session, at, date, view, scope — та же семья; scale=1/2/3/6 — явный масштаб PB.
`region=[k0,k1,b0,b1]` — выбранная область, null неограничен. `link={"source_id":"…","region":[…]}` —
дополнительный целевой прямоугольник после L исходного ядра. Перевёрнутые/дробные/булевы границы отвергаются.

`lab/time_sd235.py` берёт проверенный PB-выпуск, исходную accepted F и строит конечные ядра, пиковые проекции,
связанные пути и текущие факты. `lab/time_sd235_ref.py` независимо пересчитывает результат; связь с gate —
`lab/contract.py::ref_time_sd235`. Новый proof включает исходный PB proof и его хеш, затем `time_sd` и собственный
release_id. Сохраняются отдельные исходные PB-bundles; числа нового экрана имеют EST:TS-*.
`design/sozvezdiya-23-5/src/time_sd235.js` проверяет выпуск и подаёт его в прежние функции рисунка/наведения.
При несовпадении снимаются одновременно числа, проекции и геометрия нового слоя; старый 24 не подставляется.

Старый сервис `/api/integration/pullbacks` остаётся PB-0.1 для кандидата 24. Ни PB, ни TS не являются входом EST:B-*.
Принятых estimands 53; предложенных 72. В принятом реестре добавлена только SERVICE-запись нового маршрута;
после пересборки страницы обеих версий получают новый хеш реестра. Исходники и определения 24 не изменены.

Смысл/фасеты/условия: [единый разбор](DR-LAB-23-5-TIME-SD.md).
Тесты изоляции и реальной отрисовки работают на обеих страницах, не меняя TradingView.
