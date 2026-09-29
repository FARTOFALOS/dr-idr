# Design 22 «Созвездия · смысл числа» — a mockup (the working screen is still 21)

Design 21 changed by the semantic audit of 2026-09-29. **The meaning of every change, with numbered pictures, is in
[`meaning/04-dizajn-22.md`](../../meaning/04-dizajn-22.md)**; this file is about the code. Synthetic data only: the two
invented days of `design/clusters-2026-09-28` (day A: RDR confirms ↑ 10:55 and holds; day B: confirms ↑ 10:45, then
«Слом DR ↓ 11:45»), similar sessions simulated in `src/app.js`. The broken scene simulates a thin cohort whose price
could not be matched, on purpose (that is what the tape shows after most DR breaks).

## Build, open, check

```bash
cd design/sozvezdiya-22/src
python build.py            # -> ../built/index.html only (lab/dist is NOT touched)
sh shots.sh                # -> ../snap/*.png (git-ignored); look at them before saying "done"
python ../../all-designs/make_history.py      # copies the build and 5 snapshots into the history as design 22
python ../../../meaning/img/annotate.py       # the numbered pictures of meaning/04-dizajn-22.md
```

States by address: `#conf`, `#wait`, `#brk`; `&hl=N` = as if the N-th panel line were hovered (in `#conf`: 1 = the
most frequent pullback place, 4 = the continuation place «+1,5…+2,0»; in `#wait`: 3 = «до своего DR low»); `&strip=1`.
`window.__dr` exposes `st`, `render`, `cur`, `hit`, `V`.

## What differs from design 21 in the code

| Where | What |
|---|---|
| `overlay`, `apiOverlay`, `finishOverlay` | `ov.band` → `ov.match` (`p25` / `p50` / `none`); own DR per session: `uH`, `uL` (wait), `oppU`, `held`, `wick` (conf); `ov.ownH`, `ov.ownL`, `ov.wick`; the API path reads `sims.uH / uL / wick` when the server sends them |
| `PTS.brk`, `zoneDefs` | after a DR break the roles are «По слому» / «Против слома» and the pullback places «у нового края IDR / середина IDR / к старому краю IDR» |
| `entryOf` (new), `zoneOf` | `k.entry`: the densest 5-minute window of the first arrival of the place's sessions at its band edge nearest to the price, or `{now: true}` |
| `fanOf`, `drawFanBand` | the fan as 15-minute slices; `ov.fanCover` = share of similar sessions whose whole path stayed inside |
| `drawMarks`, `hit`, `click` | a place's share on a bracket right of the session end (hover / pin = `{k: 'place'}`); no marks when `match === 'none'` |
| `drawGlow`, `geom`, `drawProj`, `drawStrip`, `drawHist` | with `match === 'none'`: no glow, no density column, no time strip, no history charts, no numbers |
| `mfoot`, `tipHtml` | every tooltip ends with «событие · после HH:MM до HH:MM · сопоставление» |
| `panel.js` | match mark ● ◐ ○; dashes instead of percentages when unmatched; places show «впервые»; «до своего DR high / low»; «Противоположная сторона» with «тенью за DR»; no «пусто»; `firstTouch(ov, p, own)` for own-DR lines |
| removed | the hint texts «наведите, чтобы раскрыть», «клик — закрепить», the long replay caption (UI rule 4) |
| view | 45 minutes kept right of the session end for the brackets (`fitSession`, default `v1`) |

## To make it the working screen (only with the operator's go-ahead, outside trading hours)

`lab/scene21.py` must add per similar session `uH`, `uL` (wait: its own DR high / low on the 0 = IDR low, 1 = IDR high
scale) and `wick` (conf: a low / high beyond its own opposite DR after the minute); `build.py` must then also write
`lab/dist` like design 21's does; `docs/SEMANTICS.md` «Дизайн 22» becomes the definitions of the working screen;
`tests/ui_check21.js` must know the dashes and the match mark.
