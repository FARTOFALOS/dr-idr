# Decisions

Dated, with where each came from. "Operator" = the human trader, in the live chat with Claude Code (Opus 5.5) on
2026-09-24. Paraphrases, not quotes. A decision here is evidence of what was agreed, not a new authority: if a record
and the operator disagree, the operator wins.

| Date | Decision | Source |
|---|---|---|
| 2026-09-24 | Build a clone of the M7 "DR lab" idea on our own 20-year data: same DR/IDR rules, statistics of where price went after similar inputs ("кластеры"). Jev (a probabilistic model) may be attached later, not now. | operator |
| 2026-09-24 | Real data only on the site: NQ, ES, YM 2006–2025 from the G3 corpus; the synthetic demo stays only behind `--data demo`. | operator |
| 2026-09-24 | 2026 stays hidden in the history base (the G3 forward observation). No Volume. Local only (127.0.0.1). | Claude, as defaults under G3 rules; operator did not object |
| 2026-09-24 | One-screen layout, then the live session chart as the main element; secondary charts in one narrow row; no headings and no explanatory text on screen. | operator |
| 2026-09-24 | Live candles from the operator's TradingView Desktop via the debugging port; read an existing 5m pane without switching when possible. The operator added an NQ 5m pane. | operator (asked for TradingView), Claude (mechanism) |
| 2026-09-24 | Recompute the overlay from the whole history every minute while the session runs. | operator |
| 2026-09-24 | Clusters always as time × price; colours by probability (green, yellow, red); one active pick; clickable clusters with a card; guides with boundary time and price. | operator |
| 2026-09-24 | Replay: a click on a candle shows the screen as of its close; the same click returns to live. | operator |
| 2026-09-24 | TradingView fonts and bright text; DR/IDR lines light and heavier; STD and mid white dash-dot; the 0.1…0.9 IDR grid only inside the DR window; confirmation as a small pill with the time. | operator |
| 2026-09-24 | A separate **public** repository `dr-idr` for the tool, written for agents; the operator only uses the desktop shortcut. G3 keeps the research standards and the tape. | operator (public, name), Claude (separation from G3) |
| 2026-09-24 | Redesign the screen: the chart and its candles first (TradingView structure of candles, not its colours), readable colours and contrast, no text on text, three variants to choose from. Everything on screen linked to the chart both ways. The whole trading day (ADR, ODR, RDR) on one chart with mouse-wheel zoom and scrolling. | operator |
| 2026-09-25 | Formalize the author's DR/IDR method from the 156 subtitles the operator collected into one strategy file precise enough for an autonomous LLM agent (`docs/STRATEGY.md`, Russian); fill gaps from the internet; research-grade, not only agentic. Use at most one subagent at a time. A second agent re-checks the rules from public sources only (`docs/DR_RULES_WEB.md`, `docs/DR_RULES_CROSSCHECK.md`). | operator |
| 2026-09-25 | The strategy file keeps the author's rules and marks what our tape confirms (`studies/m7_claims.py`). Retirement setup and time-and-price did not show an edge on NQ/ES/YM, so the agent defaults to `observe`/`signal`; the 12 open choices in `docs/STRATEGY.md` §15.1 are defaults until the operator decides. | Claude (proposal; operator has not ratified) |
| 2026-09-25 | Variant B «Сценарий» chosen (`docs/DESIGN.md`) with changes: continuation / extreme clusters green (clouds), pullback clusters red and drawn as triangles so the two never blend; percentages quieter, without frames; the scrub band from variant C (past = the forecast of that moment, future = the clusters of that time); both cluster kinds visible. Replaces rules 13 and 21 of `docs/UI_RULES.md` when implemented. | operator |
| 2026-09-25 | Mockups keep synthetic data only (the public-repo rule for market data); the redesign lives in `docs/DESIGN.md` and `design/` and is not implemented in the running tool yet. | Claude (mechanism) |
