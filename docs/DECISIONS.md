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
