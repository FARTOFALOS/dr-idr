# DR Lab redesign mockups (2026-09-24 … 25)

Interactive mockups made on a Claude Design canvas (https://claude.ai/artifact/Hyhworqk9xqZtmWqbV4ev2). The target
design and the operator's decisions are in `docs/DESIGN.md`; this folder only keeps what is needed to see and rebuild
the mockups.

**Synthetic data only.** `src/gen_day.py` (seed 41) makes an invented NQ-like day around 24 500; `engine.js` simulates
the similar-session cohort. No market data, no live candles.

| Path | What |
|---|---|
| `built/ScenarioV2.dc.html` | **B′ · Сценарий — chosen**: green continuation clouds, red pullback triangles, quiet percentages, scrub band |
| `built/Main.dc.html`, `Scenario.dc.html`, `Clean.dc.html` | the first variants A «Терминал», B «Сценарий», C «Чистый график» |
| `built/canvas.json` | the canvas index as published |
| `snapshots/B2_*.png` | B′: live, scrub over the past (11:40), a future column (14:00), an ODR short replay |
| `snapshots/A_live.png`, `B_live.png`, `C_live.png` | the first variants |
| `src/engine.js` | shared engine: sessions (the rules of `lab/live.py`), simulated cohort, clusters/zones/fan/touch, TradingView candle geometry, tag layout, zoom/pan/scrub/replay, linking |
| `src/common.js` | toolbar, session facts, the day's sessions |
| `src/a.*`, `src/b.*`, `src/c.*`, `src/b2.*`, `src/cl_b2.frag.html` | per-variant logic and markup |
| `src/build.py` | assembles the `.dc.html` artboards into `built/` (`python build.py B2` for one) |
| `src/test.js` | runs `renderVals()` of an artboard under many states with a stub runtime and checks every `{{hole}}` resolves |
| `src/render.js`, `src/shot.sh` | static snapshot of an artboard state (expands the template) and a headless Chrome screenshot |

Rebuild and check:

```bash
cd design/redesign-2026-09/src
python gen_day.py            # writes bars.min.json (and day.json); seed 41 is the published day
python build.py B2           # writes ../built/ScenarioV2.dc.html
node test.js ../built/ScenarioV2.dc.html
node render.js ../built/ScenarioV2.dc.html '{"scrub":{"sess":"RDR","at":700}}' snap.html && ./shot.sh snap.html snap.png
```

Rebuilding A, B and C from the current `engine.js` gives files that behave the same but differ from the published
ones (the engine gained the palette hook, the scrub and the column highlight afterwards); `built/` keeps the published
bytes. `.dc.html` is the Design canvas format: `<x-dc>` markup with `{{holes}}`, `<sc-for>`/`<sc-if>`, and a
`class Component extends DCLogic` whose `renderVals()` feeds the markup; it runs only inside the canvas runtime.
