# log

Chronological record of every action on TradingView made from this repo (times UTC, 25.11.2026).

- 00:39 baseline snapshot of all 4 windows (read-only); commit + tag `baseline`.
- 00:40 saveToJSON of every window into baseline/ (read-only).
- ~00:41 INCIDENT 1: while opening chart Settings → Template → Save as on window 1, a mis-targeted click unticked «Vertical grid lines» (left pane) and a second mis-targeted click hit the layout «Save» button: layout BASE was saved to the server with the left pane's vertical grid off. Fixed within ~1 min by Cancel in the dialog; model state verified IDENTICAL to baseline (tools/diff.mjs); autosave on. Side effect that cannot be undone: the server copy of BASE now holds window 1's state (all 4 windows share BASE; whichever saves last wins).
- ~00:43 chart template «Светлая исходная» saved (Settings → Template → Save as…), from window 1 left pane. State IDENTICAL after.
- ~00:45 tried per-indicator named settings template: TV indicator dialogs only have «Reset settings / Save as default». Nothing clicked there. INCIDENT 2: the typed name went to a dialog button (no effect); state IDENTICAL.
- ~00:46 indicator templates «светлая-исходная MNQ» (left pane) and «светлая-исходная QQQ» (right pane) saved via Indicators ▾ → Templates → Save indicator template…; active pane clicked to the right then back to the left. State IDENTICAL.
- ~00:48 layout menu → «Make a copy…» → paywall «Your plan has a limit — 5 saved layouts». Closed with ×. No copy. Phase 2 stopped (no changes to BASE allowed). Reported to the coordinator.
- restore.mjs tested in dry-run both directions on window 1: 102 items resolved, 0 errors; baseline direction 0 would change; write refused on BASE as designed. Write path not exercised.
- 2026-11-24T22:51:19.899Z restore all --to baseline --dry-run window 309200BC "BASE": 102 items, 0 would change, 0 errors
- 2026-11-24T22:51:20.655Z restore all --to v2 --dry-run window 309200BC "BASE": 102 items, 90 would change, 0 errors

- 2026-11-24T22:55:20.320Z restore 08-slt --to v2 --dry-run window 309200BC "BASE": 32 items, 30 would change, 0 errors
- ~01:10 coordinator follow-up (operator authorization of 25.11 covers new Pine versions): built dark sources with tools/make-dark.mjs (counted replacements; existing input order kept, 5 new colour inputs appended in the 90 scripts); tools/pine-check.mjs: 0 errors for all three.
- ~01:15 saved as NEW private scripts via pine-facade save/new (allow_overwrite=false): «RIZ v9.8 · dark» USER;faa68923…, «90 · NQ · dark» USER;a9dacb50…, «90 v92 · dark» USER;e03765a4… (v1.0 each). Not added to any chart. Server sources = parts/*.pine; originals unchanged (90 v92.0, 90 · NQ v2.0, RIZ v161.0, source identical). All 4 windows IDENTICAL to baseline.
- SLT part 08: in_31 → #C8606A t30, in_42 → #A3A8B3 t94 (coordinator); in metadata in_42 belongs to the «Custom Midnight Line Style» row → verify on chart.

- 2026-11-24T22:57:45.154Z restore 08-slt --to v2 --dry-run window 309200BC "BASE": 34 items, 32 would change, 0 errors
- ~01:20 part 08 corrected (coordinator): in_42 is the NY-midnight line → #F29A38 t30, in_40 Dashed; session-box mapping dropped, to be identified visually in the test layout.
- ~01:35 operator chose layout «Unnamed» (w8qiG86Q) as test layout. tab_new (MCP) did not open a tab, so window 1 (target 309200BC, was BASE) was switched to Unnamed via loadLayoutFromServerByLayoutId; BASE checked IDENTICAL in the 3 other windows before/after. Unnamed snapshot (AAPL 1M, no studies) in baseline/unnamed/, tag unnamed-before. Loaded window-1 BASE content (loadContent), renamed to «BASE · dark» (rename dialog), saved. Studies/props identical to baseline window 1. restore.mjs now writes only to layout id w8qiG86Q named «… · dark».

- 2026-11-24T23:06:55.909Z restore 01-canvas --to v2 --dry-run window 309200BC "BASE · dark": 18 items, 12 would change, 0 errors

- 2026-11-24T23:07:30.283Z restore 01-canvas --to v2 --dry-run window 309200BC "BASE · dark": 18 items, 11 would change, 0 errors

- 2026-11-24T23:07:30.850Z restore 02-candles --to v2 --dry-run window 309200BC "BASE · dark": 12 items, 11 would change, 0 errors

- 2026-11-24T23:07:45.847Z restore 01-canvas --to v2 window 309200BC "BASE · dark": 18 items, 11 changed, 0 errors

- 2026-11-24T23:07:55.042Z restore 02-candles --to v2 window 309200BC "BASE · dark": 12 items, 11 changed, 0 errors

- 2026-11-24T23:08:18.055Z restore 03-dr-idr --to v2 window 309200BC "BASE · dark": 24 items, 20 changed, 0 errors

- 2026-11-24T23:08:29.089Z restore 07-riz-blue --to v2 window 309200BC "BASE · dark": 10 items, 10 changed, 0 errors

- 2026-11-24T23:08:37.936Z restore 09-session-highlights --to v2 window 309200BC "BASE · dark": 10 items, 10 changed, 0 errors

- 2026-11-24T23:09:43.923Z restore 08-slt --to v2 window 309200BC "BASE · dark": 34 items, 32 changed, 0 errors

- 2026-11-24T23:10:14.687Z restore 08b-slt-midnight --to baseline window 309200BC "BASE · dark": 4 items, 4 changed, 0 errors

- 2026-11-24T23:10:15.266Z restore 08-slt --to v2 --dry-run window 309200BC "BASE · dark": 30 items, 0 would change, 0 errors
- 2026-11-24T23:11:42.293Z replace-study pane 0 YNtADH -> USER;a9dacb5075374ccc8727bab25562fa24 v1.0: {"error":"insertStudy returned null","removedOld":false}
- 2026-11-24T23:12:42.938Z replace-study pane 0 YNtADH -> USER;a9dacb5075374ccc8727bab25562fa24 v1.0: {"removedOld":false,"newId":"Az5SN1","title":"90min Cycle Extremes + SMT Diagonal v25.3 [Sync + Target + 369] · NQ · dark","carried":22,"mismatch":[]}
- 2026-11-24T23:13:02.663Z replace-study pane 1 6faABb -> USER;e03765a4be0b41f383f59bbc71b1c7db v1.0: {"removedOld":true,"newId":"hwT3Wm","title":"90min Cycle Extremes + SMT Diagonal v25.3 [Sync + Target + 369] · v92 · dark","carried":22,"mismatch":[]}
- 2026-11-24T23:13:18.435Z replace-study pane 0 whP7bS -> USER;faa68923f4a946fd8513f54ea8be1195 v1.0: {"removedOld":true,"newId":"aHkkAo","title":"RIZ v9.8 MTF - Raid Imbalance Zones · dark","carried":17,"mismatch":[]}
- 2026-11-24T23:13:20.778Z replace-study pane 1 UXSpIc -> USER;faa68923f4a946fd8513f54ea8be1195 v1.0: {"removedOld":true,"newId":"6krbp7","title":"RIZ v9.8 MTF - Raid Imbalance Zones · dark","carried":17,"mismatch":[]}
- ~01:45 parts 01, 02, 03, 07, 09 applied to «BASE · dark» (w8qiG86Q) with restore.mjs; first attempt of 01/02 failed after one property each (model.setProperty undo-text error), writer switched to setValue / setInputValues, re-applied; check-base after each part: 3 BASE windows IDENTICAL.
- ~01:50 part 08 applied; confirmed on chart via SLT drawing data (widths 3/2/3/4/1/3/2 px match inputs; 8:30 line turned dashed). Midnight row (in_40/in_42) set Dashed → no SLT line changed → moved to 08b, reverted to baseline; stale palette entry 6 reset.
- ~02:00 90 · NQ, 90 v92 and both RIZ instances replaced by the « · dark» scripts (tools/replace-study.mjs; non-undo model calls because undoable ones fail from CDP); non-colour inputs carried (22/22/17/17, 0 mismatches), RIZ transparencies from new defaults, visibility as baseline. Box border styles present: solid, dashed (SMT), dotted (bridge). Layout saved (list modified 23:15 UTC). BASE IDENTICAL.

- 2026-11-24T23:21:15.638Z restore 11-palette-sync --to v2 window 309200BC "BASE · dark": 46 items, 28 changed, 0 errors

- 2026-11-24T23:22:48.047Z restore 08-slt --to v2 window 309200BC "BASE · dark": 32 items, 10 changed, 0 errors

- 2026-11-24T23:22:49.088Z restore 11-palette-sync --to v2 window 309200BC "BASE · dark": 48 items, 8 changed, 0 errors
- ~02:25 night (coordinator): A) SLT level labels were light text on light tags: part 08 label texts → #08090C, palette entries synced by new part 11 (TV had not updated them; 9:30 line was still black in the palette). Checked on chart: PDH/PDL/9:30/8:30 readable, 8:30 dashed. B) drawings inventory read-only (parts/10-drawings), part 10 prepared, not applied. BASE IDENTICAL after each write.
- ~02:35 C) fib template «dr · dark» created via /save-drawing-template/ (dr read only, verified unchanged): 16 visible levels mapped, labels 14px. First save had unchanged levels (bad filter), immediately overwritten by the correct one.
- ~02:55 D) screenshots (pane-cropped) in screens/v2; once found pane 0 maximized during the run (cause unclear), un-maximized via _setMaximized(null) before shooting. E) measurements.md written (26 elements).
- ~03:00 F) 14 PNGs uploaded as assets to artifact U9taB5dTdHw9TkFPqe8vT6 (ids in screens/v2/assets.md). Final check-base: 3 BASE windows IDENTICAL.
