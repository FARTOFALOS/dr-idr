'use strict';
// Live session panel: today's M5 bars from TradingView + the historical probability overlay (see live.py).
// While the session runs, it refreshes itself after every M5 close and the backend re-matches the whole history.
let liveData = null, liveKey = '', liveTimer = null, liveCd = null;
const zoneSel = new Set();                       // zones clicked in the side column: kind|lo|t
let replayAt = null;                             // candle close minute being replayed; null = live
const binSel = new Set();                        // bottom-chart picks: retr|lo, ext|lo, rtime|t, etime|t, cell|r|t
const PROB = ['#4ade80', '#facc15', '#f87171'];                 // most likely -> least likely: green, yellow, red
const probColor = f => f >= .67 ? PROB[0] : f >= .34 ? PROB[1] : PROB[2];
const rankColors = zs => { const out = []; zs.forEach((z, i) => out.push(i && Math.round(z.pct) === Math.round(zs[i - 1].pct) ? out[i - 1] : PROB[Math.min(i, 2)])); return out; };
const etClock = new Intl.DateTimeFormat('ru-RU', {timeZone: 'America/New_York', hour: '2-digit', minute: '2-digit'});
const etParts = new Intl.DateTimeFormat('en-US', {timeZone: 'America/New_York', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false});
let layers = {rclust: true, eclust: false, fan: true, ladder: true};
try { Object.assign(layers, JSON.parse(localStorage.getItem('dr-lab-layers-v2') || '{}')); } catch { /* per-viewer preference only */ }
document.querySelectorAll('[data-layer]').forEach(b => b.classList.toggle('active', !!layers[b.dataset.layer]));
try { const a = localStorage.getItem('dr-lab-auto'); if (a !== null) $('live-auto').checked = a === '1'; } catch { /* optional */ }

function etNow() {
  const p = Object.fromEntries(etParts.formatToParts(new Date()).map(x => [x.type, x.value]));
  return (+p.hour % 24) * 60 + (+p.minute) + (+p.second) / 60;
}
function sessionRunning(L) {
  if (!L || L.start == null) return false;
  let m = etNow(); if (state.session === 'ADR' && m < 720) m += 1440;
  return m >= L.start && m < L.end + 1;
}
function scheduleLive() {
  clearTimeout(liveTimer); clearInterval(liveCd); $('live-countdown').textContent = '';
  if (!$('live-auto').checked || !sessionRunning(liveData)) return;
  const step = liveData.switched ? 5 : 1, m = etNow(), wait = ((Math.floor(m / step) + 1) * step + (step === 1 ? 3 : 20) / 60 - m) * 60000, due = Date.now() + wait;
  liveTimer = setTimeout(() => liveFetch(true), wait);
  liveCd = setInterval(() => { const s = Math.max(0, Math.round((due - Date.now()) / 1000)); $('live-countdown').textContent = `· через ${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`; }, 1000);
}
async function liveFetch(refresh) {
  const inst = state.instrument || 'NQ', ses = state.session;
  $('live-status').textContent = refresh ? 'Загружаю из TradingView…' : 'Читаю…';
  $('live-refresh').disabled = true;
  try {
    const r = await fetch(`/api/live${refresh ? '/refresh' : ''}?instrument=${inst}&session=${ses}${replayAt != null ? '&at=' + replayAt : ''}`);
    const d = await r.json();
    if (inst !== (state.instrument || 'NQ') || ses !== state.session) return null;
    liveData = d;
    try { drawLive(d); } catch (err) { console.error('drawLive', err); }
    return d;
  } catch (e) {
    liveData = {status: 'error', message: 'Локальный сервер не ответил.'}; drawLive(liveData); return null;
  } finally { $('live-refresh').disabled = false; scheduleLive(); }
}
window.liveOnQuery = async function () {
  const key = (state.instrument || 'NQ') + '|' + state.session;
  if (key === liveKey) return;
  liveKey = key; replayAt = null;
  const d = await liveFetch(false);
  if (d && (d.status === 'no_data' || !d.fetched_at || Date.now() - Date.parse(d.fetched_at) > 180000)) await liveFetch(true);
};
window.liveRedraw = () => { if (liveData) drawLive(liveData); };
$('live-refresh').addEventListener('click', () => liveFetch(true));
$('live-auto').addEventListener('change', () => { try { localStorage.setItem('dr-lab-auto', $('live-auto').checked ? '1' : '0'); } catch {} scheduleLive(); });
document.querySelectorAll('[data-layer]').forEach(b => b.addEventListener('click', () => {
  layers[b.dataset.layer] = !layers[b.dataset.layer]; b.classList.toggle('active', layers[b.dataset.layer]);
  try { localStorage.setItem('dr-lab-layers-v2', JSON.stringify(layers)); } catch {}
  window.liveRedraw();
}));
try { if (localStorage.getItem('dr-lab-focus') === '0') document.body.classList.remove('focus'); } catch { /* optional */ }
$('focus-toggle').addEventListener('click', () => {
  const f = document.body.classList.toggle('focus');
  try { localStorage.setItem('dr-lab-focus', f ? '1' : '0'); } catch {}
  setTimeout(() => { if (data) render(); else window.liveRedraw(); }, 30);
});
$('live-toggle').addEventListener('click', () => {
  const c = $('live-panel').classList.toggle('collapsed');
  $('live-toggle').textContent = c ? 'Развернуть' : 'Свернуть';
  setTimeout(() => { if (data) render(); }, 30);
});

function drawLive(L) {
  const host = $('live-chart'), side = $('live-side'), inst = state.instrument || 'NQ';
  $('live-title').textContent = `${inst} · ${state.session}${L.day ? ' · ' + L.day : ''}`;
  $('live-status').textContent = L.fetched_at ? `${L.replay != null ? 'история на ' + time(L.replay) + ' · ' : ''}${L.feed || ''} · ${etClock.format(new Date(L.fetched_at))} ET · ${L.switched ? 'переключение графика, раз в 5 мин' : 'панель ' + (L.source_interval || 5) + 'm, каждую минуту'}` : '';
  if (L.status === 'error' || L.status === 'no_data' || L.status === 'no_session' || !L.bars || !L.bars.length) {
    host.innerHTML = `<div class="live-msg"><div>${xml(L.message || 'Нет данных')}</div><small>TradingView Desktop должен быть запущен (его открывает инструмент tv_launch).</small></div>`;
    side.innerHTML = ''; return;
  }
  if ($('live-panel').classList.contains('collapsed')) return;
  const px = v => number(Math.round(v / L.tick) * L.tick, L.tick < 1 ? 2 : 0);   // prices on the tick grid
  const conf = L.status === 'confirmed', s = L.direction === 'short' ? -1 : 1, o = L.overlay || {};
  const lvPrice = v => L.edge + s * v * L.width;
  const w = Math.max(480, host.clientWidth), h = Math.max(220, host.clientHeight), ladder = layers.ladder && conf && o.n ? 130 : 0;
  const p = {l: 30, r: ladder + 120, t: 14, b: 24};
  const ys = [];
  for (const b of L.bars) ys.push(b[2], b[3]);
  if (L.dr_high != null) ys.push(L.dr_high, L.dr_low);
  if (conf && o.n) {
    const lowest = Math.min(L.now_coord, ...(o.zones_min || []).map(z => z.lo)) - .15, highest = Math.max(L.now_coord, ...(o.zones_max || []).map(z => z.hi)) + .15;
    ys.push(lvPrice(lowest), lvPrice(highest));
    if (layers.fan) for (const f of o.fan || []) ys.push(lvPrice(f.low), lvPrice(f.high));
  }
  if (conf) for (const k of ['retr', 'ext']) if (state[k] != null) ys.push(lvPrice(+state[k]), lvPrice((state[k + '_hi'] != null ? +state[k + '_hi'] : +state[k]) + .1));
  let lo = Math.min(...ys), hi = Math.max(...ys); const pad = (hi - lo) * .03; lo -= pad; hi += pad;
  const x = t => p.l + (t - L.start) / (L.end - L.start) * (w - p.l - p.r), y = v => p.t + (hi - v) / (hi - lo) * (h - p.t - p.b);
  const xe = x(L.end);
  let g = `<rect x="${x(L.start)}" y="${p.t}" width="${x(L.formed) - x(L.start)}" height="${h - p.t - p.b}" fill="#fff" opacity=".04"/>`;
  g += `<text x="${x(L.start) + 4}" y="${p.t + 10}" class="lv-label">окно DR</text>`;
  for (let t = Math.ceil(L.start / 30) * 30; t <= L.end; t += 30) {
    if (t % 60 === 0) g += `<text x="${x(t)}" y="${h - 6}" text-anchor="middle" class="axis-text">${time(t)}</text>`;
  }
  const labels = [], LBL = {'lv-dr': '#f8fafc', 'lv-idr': '#f1f5f9', 'lv-level': '#e2e8f0', 'lv-mid': '#e2e8f0', 'lv-open': '#4cd07d'};
  const hline = (v, cls, label) => {
    if (v == null || v < lo || v > hi) return;
    g += `<line x1="${x(L.start)}" x2="${xe}" y1="${y(v)}" y2="${y(v)}" class="${cls}"/>`;
    if (label) labels.push({y: y(v), text: label, color: LBL[cls] || '#8fa3b8'});
  };
  if (L.dr_high != null) {                      // STD lines exactly as in the Pine script: 0.5 IDR steps from the IDR edges
    const step = (L.idr_high - L.idr_low) / 2;
    for (let k = 1; k <= 10; k++) { hline(L.idr_high + k * step, 'lv-level', `${number(k * .5, 1)} · ${px(L.idr_high + k * step)}`); hline(L.idr_low - k * step, 'lv-level', `-${number(k * .5, 1)} · ${px(L.idr_low - k * step)}`); }
  }
  if (L.dr_high != null) {
    hline(L.dr_high, 'lv-dr', `DR ${px(L.dr_high)}`); hline(L.dr_low, 'lv-dr', `DR ${px(L.dr_low)}`);
    hline(L.idr_high, 'lv-idr', `IDR ${px(L.idr_high)}`); hline(L.idr_low, 'lv-idr', `IDR ${px(L.idr_low)}`);
    hline((L.idr_high + L.idr_low) / 2, 'lv-mid', 'mid'); hline(L.open, 'lv-open', 'open');
    const wIdr = L.idr_high - L.idr_low, fromLow = L.direction === 'short';
    for (let k = 1; k <= 9; k++) {
      const v = fromLow ? L.idr_low + k * wIdr / 10 : L.idr_high - k * wIdr / 10, yy = y(v);
      g += `<line x1="${x(L.start)}" x2="${x(L.formed)}" y1="${yy}" y2="${yy}" class="lv-dec"/>`;
      if (k !== 5) g += `<text x="${x(L.start) - 4}" y="${yy + 3.5}" text-anchor="end" class="lv-dec-t">${number(k / 10, 1)}</text>`;
    }
  }
  if (conf && o.n) {
    const now = L.observed, nowP = lvPrice(L.now_coord);
    // price x time clusters: where and when the future minimum / maximum of similar sessions landed
    const cells = (all, color, what) => {
      const sorted = [...all].filter(c => c.n >= 2 && c.t + 15 > now).sort((u, v) => v.n - u.n), list = [];
      let acc = 0; for (const c of sorted) { if (acc >= .4 * o.n) break; list.push(c); acc += c.n; }
      const m = Math.max(1, ...list.map(c => c.n));
      for (const c of list) {
        const a = lvPrice(c.lo), z = lvPrice(c.lo + .1), top = Math.max(a, z), bot = Math.min(a, z);
        if (bot > hi || top < lo || c.t + 15 <= now) continue;
        g += `<rect x="${x(Math.max(c.t, now))}" y="${y(Math.min(top, hi))}" width="${Math.max(1, x(c.t + 15) - x(Math.max(c.t, now)))}" height="${Math.max(1, y(Math.max(bot, lo)) - y(Math.min(top, hi)))}" fill="${probColor(c.n / m)}" opacity="${(.14 + .26 * c.n / m).toFixed(2)}"${color === 'max' ? ' stroke="#9fb3c6" stroke-width=".6" stroke-dasharray="2 2"' : ''} class="lv-hit" data-g="${time(Math.max(c.t, now))}|${time(c.t + 15)}|${px(Math.min(a, z))}|${px(Math.max(a, z))}" data-info="${what}|${time(c.t)}–${time(c.t + 15)}|${signed(c.lo, 1)}…${signed(c.lo + .1, 1)} IDR|${px(Math.min(a, z))} – ${px(Math.max(a, z))}|${c.n} из ${o.n} похожих сессий|${number(100 * c.n / o.n, 0)}%" data-tip="${what} ${time(c.t)}–${time(c.t + 15)} · ${number(100 * c.n / o.n, 0)}%"/>`;
      }
    };
    if (layers.eclust) cells(o.cluster_max || [], 'max', 'Дальний экстремум');
    if (layers.rclust) cells(o.cluster_min || [], 'min', 'Откат закончится');
    const zone = (z, color, what) => {
      if (!z) return;
      const a = lvPrice(z.lo), b = lvPrice(z.hi), x0 = x(Math.max(z.t, now)), x1 = x(z.t_hi);
      if (x1 <= x0) return;
      g += `<rect x="${x0}" y="${y(Math.max(a, b))}" width="${x1 - x0}" height="${Math.abs(y(a) - y(b))}" fill="none" stroke="${color}" stroke-width="1.2" stroke-dasharray="4 3" opacity=".8"/>`;
    };
    if (layers.rclust) zone((o.zones_min || [])[0], PROB[0], 'откат');
    if (layers.eclust) zone((o.zones_max || [])[0], PROB[0], 'экстремум');
    for (const kind of ['min', 'max']) { const zs = o['zones_' + kind] || [], cs = rankColors(zs); zs.forEach((z, i) => {
      if (!zoneSel.has(`${kind}|${z.lo}|${z.t}`)) return;
      const c = cs[i], a = lvPrice(z.lo), b = lvPrice(z.hi), yt = y(Math.max(a, b)), yb = y(Math.min(a, b));
      const x0 = x(Math.max(z.t, now)), x1 = x(z.t_hi);
      g += `<rect x="${x0}" y="${yt}" width="${Math.max(2, x1 - x0)}" height="${Math.max(2, yb - yt)}" fill="${c}" opacity=".38" stroke="${c}" stroke-width="1.8" class="lv-hit" data-g="${time(Math.max(z.t, now))}|${time(z.t_hi)}|${px(Math.min(a, b))}|${px(Math.max(a, b))}" data-info="${kind === 'min' ? 'Откат закончится' : 'Экстремум'}|${time(z.t)}–${time(z.t_hi)}|${signed(z.lo, 1)}…${signed(z.hi, 1)} IDR|${px(Math.min(a, b))} – ${px(Math.max(a, b))}|${z.n} из ${o.n} похожих сессий|${number(z.pct, 0)}%"/>`;
    }); }
    if (layers.fan && o.fan && o.fan.length) {
      const up = o.fan.map(f => `L${x(f.t).toFixed(1)},${y(lvPrice(f.high)).toFixed(1)}`).join(' ');
      const dn = [...o.fan].reverse().map(f => `L${x(f.t).toFixed(1)},${y(lvPrice(f.low)).toFixed(1)}`).join(' ');
      g += `<path d="M${x(now)},${y(nowP)} ${up} ${dn} Z" fill="#8bc7ff" opacity=".07"/>`;
      g += `<path d="M${x(now)},${y(nowP)} ${o.fan.map(f => `L${x(f.t).toFixed(1)},${y(lvPrice(f.mid)).toFixed(1)}`).join(' ')}" fill="none" stroke="#8bc7ff" stroke-width="1.4" stroke-dasharray="5 4" opacity=".8"/>`;
    }
    if (ladder) {
      const x0 = xe + 116, bw = ladder - 34;
      g += `<text x="${x0}" y="${p.t - 3}" class="lv-label">касание до ${time(L.end)}</text>`;
      let lastPct = -99;
      for (const [k, pct] of Object.entries(o.touch || {}).sort((u, v) => y(lvPrice(+u[0])) - y(lvPrice(+v[0])))) {
        const v = +k, pr = lvPrice(v), yy = y(pr);
        if (pr < lo || pr > hi) continue;
        const col = v >= L.now_coord ? '#39d8bd' : '#e9b86e';
        g += `<rect x="${x0}" y="${yy - 3}" width="${Math.max(1, bw * pct / 100)}" height="6" fill="${col}" opacity=".75" data-tip="${signed(v, 2)} IDR · ${px(pr)} · касание после ${time(L.observed)}: ${number(pct, 1)}% (${o.n} сессий)"/>`;
        if (Math.abs(v * 2 - Math.round(v * 2)) < 1e-6 && yy - lastPct >= 16) { g += `<text x="${x0 + bw + 3}" y="${yy + 4}" class="lv-pct" fill="${col}">${Math.round(pct)}%</text>`; lastPct = yy; }
      }
    }
  }
  if (conf && o.n && binSel.size) {               // bottom-chart picks -> their clusters in time x price
    const near = (u, v) => Math.abs(u - v) < 1e-6, picked = [];
    for (const k of binSel) {
      const [kind, u, v] = k.split('|'), a1 = +u, a2 = v != null ? +v : null;
      const src = kind === 'ext' || kind === 'etime' ? (o.cluster_max || []) : (o.cluster_min || []);
      for (const c of src) {
        if ((kind === 'retr' || kind === 'ext') && near(c.lo, a1)) picked.push([c, kind]);
        else if ((kind === 'rtime' || kind === 'etime') && c.t === a1) picked.push([c, kind]);
        else if (kind === 'cell' && near(c.lo, a1) && c.t === a2) picked.push([c, kind]);
      }
    }
    const m = Math.max(1, ...picked.map(q => q[0].n));
    for (const [c, kind] of picked) {
      const a = lvPrice(c.lo), z = lvPrice(c.lo + .1), top = Math.max(a, z), bot = Math.min(a, z);
      if (bot > hi || top < lo) continue;
      const col = probColor(c.n / m), what = kind === 'ext' || kind === 'etime' ? 'Экстремум' : 'Откат закончится';
      g += `<rect x="${x(c.t)}" y="${y(top)}" width="${Math.max(2, x(c.t + 15) - x(c.t))}" height="${Math.max(2, y(bot) - y(top))}" fill="${col}" opacity=".55" stroke="#f1f5f9" stroke-width=".8" class="lv-hit" data-g="${time(c.t)}|${time(c.t + 15)}|${px(bot)}|${px(top)}" data-info="${what}|${time(c.t)}–${time(c.t + 15)}|${signed(c.lo, 1)}…${signed(c.lo + .1, 1)} IDR|${px(bot)} – ${px(top)}|${c.n} из ${o.n} похожих сессий|${number(100 * c.n / o.n, 0)}%" data-tip="${what} ${time(c.t)}–${time(c.t + 15)} · ${number(100 * c.n / o.n, 0)}%"/>`;
    }
  }
  if (conf && !(window.liveOwnsCharts && window.liveOwnsCharts())) {   // research mode: X-ray filters of the history charts
    const sel = (k, st) => state[k] != null ? [+state[k], (state[k + '_hi'] != null ? +state[k + '_hi'] : +state[k]) + st] : null;
    const r = sel('retr', .1), e = sel('ext', .1), rt = sel('rtime', 15), et = sel('etime', 15);
    const band = (rng, color, label) => { if (!rng) return; const a = lvPrice(rng[0]), b = lvPrice(rng[1]); const y0 = y(Math.max(a, b)), y1 = y(Math.min(a, b));
      g += `<rect x="${x(L.formed)}" y="${y0}" width="${xe - x(L.formed)}" height="${Math.max(2, y1 - y0)}" fill="${color}" opacity=".16" stroke="${color}" stroke-width="1"/><text x="${x(L.formed) + 4}" y="${y0 - 3}" class="lv-zone" fill="${color}">${label} ${signed(rng[0], 1)}…${signed(rng[1], 1)} IDR · ${px(Math.min(a, b))}–${px(Math.max(a, b))}</text>`; };
    const vband = (rng, color, label) => { if (!rng) return; g += `<rect x="${x(rng[0])}" y="${p.t}" width="${Math.max(2, x(rng[1]) - x(rng[0]))}" height="${h - p.t - p.b}" fill="${color}" opacity=".10"/><text x="${x(rng[0]) + 3}" y="${h - p.b - 18}" class="lv-zone" fill="${color}">${label} ${time(rng[0])}–${time(rng[1])}</text>`; };
    if (r && rt) { const a = lvPrice(r[0]), b = lvPrice(r[1]);
      g += `<rect x="${x(rt[0])}" y="${y(Math.max(a, b))}" width="${Math.max(2, x(rt[1]) - x(rt[0]))}" height="${Math.max(2, Math.abs(y(a) - y(b)))}" fill="#e9b86e" opacity=".35" stroke="#ffd79a" stroke-width="1.5"/><text x="${x(rt[0]) + 3}" y="${y(Math.max(a, b)) - 3}" class="lv-zone" fill="#ffd79a">выбранная клетка: откат ${signed(r[0], 1)}…${signed(r[1], 1)} IDR · ${time(rt[0])}–${time(rt[1])} · ${px(Math.min(a, b))}–${px(Math.max(a, b))}</text>`; }
    else { band(r, '#e9b86e', 'выбран откат'); vband(rt, '#e9b86e', 'время отката'); }
    band(e, '#39d8bd', 'выбрано расширение'); vband(et, '#39d8bd', 'время экстремума');
  }
  const cw = Math.max(1.5, Math.min(10, (x(L.start + 5) - x(L.start)) * .7));
  for (const [t, op, hh, ll, c, closed] of L.bars) {
    const xc = x(t + 2.5), col = c >= op ? '#49d6b6' : '#ee8b96';
    g += `<g class="lv-bar${L.replay === t + 5 ? ' on' : ''}" data-bar="${t}" opacity="${closed ? 1 : .45}"><rect x="${xc - Math.max(cw, 6) / 2}" y="${y(hh) - 3}" width="${Math.max(cw, 6)}" height="${y(ll) - y(hh) + 6}" fill="transparent"/><line x1="${xc}" x2="${xc}" y1="${y(hh)}" y2="${y(ll)}" stroke="${col}"/><rect x="${xc - cw / 2}" y="${y(Math.max(op, c))}" width="${cw}" height="${Math.max(1, Math.abs(y(op) - y(c)))}" fill="${col}" data-tip="${time(t)}–${time(t + 5)} · O ${px(op)} H ${px(hh)} L ${px(ll)} C ${px(c)}${closed ? '' : ' · свеча формируется'}"/></g>`;
  }
  if (conf) {
    const pill = (minute, color, tip) => {
      const b = L.bars.find(q => q[0] + 5 === minute); if (!b) return;
      const cx = x(b[0] + 2.5), cy = y(b[4]);
      g += `<g class="lv-pill" data-tip="${tip} ${time(minute)}"><rect x="${cx - 19}" y="${cy - 8}" width="38" height="16" rx="8" fill="${color}" stroke="#f8fafc" stroke-width=".7" opacity=".92"/><text x="${cx}" y="${cy + 3.8}" text-anchor="middle" class="lv-pill-t">${time(minute)}</text></g>`;
    };
    pill(L.confirmation, s === 1 ? '#15803d' : '#b91c1c', s === 1 ? 'Подтверждение вверх' : 'Подтверждение вниз');
    if (L.failed_at) pill(L.failed_at, '#7f1d1d', 'DR сломан');
  }
  if (L.observed) g += `<line x1="${x(L.observed)}" x2="${x(L.observed)}" y1="${p.t}" y2="${h - p.b}" stroke="#8fb4d6" stroke-width=".8" stroke-dasharray="6 3 1 3" opacity=".35"/><text x="${x(L.observed) > xe - 110 ? x(L.observed) - 4 : x(L.observed) + 4}" text-anchor="${x(L.observed) > xe - 110 ? 'end' : 'start'}" y="${h - p.b - 4}" class="lv-label" fill="${L.replay != null ? '#facc15' : '#7f9bb5'}" opacity=".8">${L.replay != null ? 'момент' : 'сейчас'} ${time(L.observed)}</text>`;
  labels.sort((u, v) => u.y - v.y);
  const GAP = 17; labels.forEach((l, i) => { l.ty = i ? Math.max(l.y, labels[i - 1].ty + GAP) : l.y; });
  for (let i = labels.length - 1; i >= 0; i--) { const lim = i === labels.length - 1 ? h - p.b : labels[i + 1].ty - GAP; if (labels[i].ty > lim) labels[i].ty = lim; }
  for (const l of labels) {
    if (Math.abs(l.ty - l.y) > 1.5) g += `<line x1="${xe}" y1="${l.y}" x2="${xe + 6}" y2="${l.ty}" stroke="${l.color}" stroke-width=".8" opacity=".7"/>`;
    g += `<text x="${xe + 8}" y="${l.ty + 4}" class="lv-label" fill="${l.color}">${l.text}</text>`;
  }
  host.innerHTML = svg(w, h, g, 'Текущая сессия с уровнями DR/IDR и кластерами из истории');
  host.dataset.geo = JSON.stringify({h, pb: p.b, xe});
  restorePin();
  if (window.liveOwnsCharts()) drawBottom(o);
  // side column
  const row = (a, b) => `<div class="row"><span>${a}</span><span>${b}</span></div>`;
  let html = '';
  if (conf) {
    const arrow = s === 1 ? '↑' : '↓';
    if (L.failed_at) html += `<div><div class="big bad">DR сломан ${time(L.failed_at)}</div><small>Подтверждение ${arrow} ${time(L.confirmation)} уже не действует; ниже — сессии, где DR тоже был сломан к ${time(L.observed)}.</small></div>`;
    else if (o.n) { const v = o.dr_true_pct; html += `<div><small>DR удержится до ${time(L.end)}</small><div class="big ${v >= 80 ? '' : v >= 60 ? 'warn' : 'bad'}">${number(v, 1)}%</div></div>`; }
    html += row('Подтверждение', `${arrow} ${time(L.confirmation)}`) + row('Цена сейчас', `${signed(L.now_coord, 2)} IDR · ${px(lvPrice(L.now_coord))}`);
    if (o.n) {
      const zrow = (kind) => (z, i, zs) => { const key = `${kind}|${z.lo}|${z.t}`, c = rankColors(zs)[i];
        return `<button type="button" class="zone-row ${zoneSel.has(key) ? 'active' : ''}" data-zone="${key}" style="--c:${c}"><i class="dot"></i>${time(z.t)}–${time(z.t_hi)} <b>${px(Math.min(lvPrice(z.lo), lvPrice(z.hi)))}–${px(Math.max(lvPrice(z.lo), lvPrice(z.hi)))}</b><span>${number(z.pct, 0)}%</span></button>`; };
      html += '<h4>ОТКАТ ЗАКОНЧИТСЯ</h4>' + (o.zones_min || []).map(zrow('min')).join('');
      html += '<h4>ЭКСТРЕМУМ</h4>' + (o.zones_max || []).map(zrow('max')).join('');
      html += '<h4>КАСАНИЕ ДО КОНЦА СЕССИИ</h4>';
      const ups = [], dns = [];
      for (let v = Math.ceil((L.now_coord + .01) * 2) / 2; v <= 3 && ups.length < 3; v += .5) ups.push(v);
      for (let v = Math.floor((L.now_coord - .01) * 2) / 2; v >= -1.5 && dns.length < 3; v -= .5) dns.push(v);
      for (const v of [...ups].reverse().concat(dns)) { const pct = (o.touch || {})[String(+v.toFixed(2))] ?? (o.touch || {})[v.toFixed(1)]; if (pct != null) html += row(`${signed(v)} · ${px(lvPrice(v))}`, `${number(pct, 0)}%`); }
      html += `<small>${o.n} похожих сессий 2006–2025 (из ${o.pool}): подтверждение ${arrow} ±15 мин от ${time(L.confirmation)}, DR ${L.failed_at ? 'сломан' : 'цел'} на ${time(L.observed)}, цена ${o.band ? '±' + o.band + ' IDR от сегодняшней' : 'в любом положении'}.</small>`;
    } else html += '<small>В истории нет похожих сессий с продолжением после этой минуты (сессия завершена или редкий случай).</small>';
  } else if (L.status === 'waiting') {
    const q = L.pending || {};
    html += `<div class="big warn">Подтверждения нет</div><small>DR сформирован, закрытия M5 за DR пока не было (на ${time(L.observed)}).</small><h4>ИСТОРИЯ: ЧТО БЫЛО ДАЛЬШЕ</h4>` +
      row('Позже вверх', `${number(q.long_pct, 0)}% · ${q.long_median || '—'}`) + row('Позже вниз', `${number(q.short_pct, 0)}% · ${q.short_median || '—'}`) +
      row('Без подтверждения', `${number(q.none_pct, 0)}%`) + `<small>Сессии, не подтвердившиеся к этой минуте; время — медиана подтверждения.</small>`;
  } else {
    html += `<div class="big warn">DR формируется</div><small>Окно ${time(L.start)}–${time(L.formed)} ET ещё не закрыто.</small>`;
  }
  if (L.dr_high != null) html += '<h4>УРОВНИ</h4>' + row('DR', `${px(L.dr_low)} – ${px(L.dr_high)}`) + row('IDR', `${px(L.idr_low)} – ${px(L.idr_high)}`);
  side.innerHTML = html;
}

$('live-side').addEventListener('click', event => {
  const b = event.target.closest('[data-zone]'); if (!b) return;
  const k = b.dataset.zone, was = zoneSel.has(k); zoneSel.clear(); binSel.clear(); if (!was) zoneSel.add(k);
  window.liveRedraw();
});

window.liveOwnsCharts = () => document.body.classList.contains('focus') && !!liveData && liveData.status === 'confirmed' && !!liveData.overlay && liveData.overlay.n > 0 && !!liveData.overlay.charts;

function drawBottom(o) {
  drawPath(o); drawHeat(o);
  for (const key of ['retr', 'ext', 'rtime', 'etime']) drawHist(key, o.charts[key], o);
  // picks stay visible, the rest dims but stays clickable
  for (const key of ['retr', 'ext', 'rtime', 'etime']) {
    const mine = [...binSel].filter(k => k.startsWith(key + '|'));
    document.querySelectorAll(`#${key}-chart [data-bin]`).forEach(r => {
      const on = mine.some(k => Math.abs(+k.split('|')[1] - +r.dataset.lo) < 1e-6);
      r.classList.toggle('selected', on); r.style.opacity = mine.length && !on ? '.45' : '';
    });
  }
  const cells = [...binSel].filter(k => k.startsWith('cell|'));
  document.querySelectorAll('#heatmap [data-heat-r]').forEach(c => {
    const on = cells.some(k => { const [, r, t] = k.split('|'); return Math.abs(+r - +c.dataset.heatR) < 1e-6 && +t === +c.dataset.heatT; });
    c.classList.toggle('selected', on); c.style.outline = on ? '2px solid #facc15' : '';
  });
}

// in focus mode a click on a bar or a cell only toggles its highlight (no filtering, nothing else goes dark)
window.addEventListener('click', event => {
  if (!window.liveOwnsCharts()) return;
  const bin = event.target.closest('.mini-row [data-bin]'), cell = event.target.closest('.mini-row [data-heat-r]');
  if (!bin && !cell) return;
  event.stopPropagation(); event.preventDefault();
  const k = bin ? `${bin.dataset.bin}|${+bin.dataset.lo}` : `cell|${+cell.dataset.heatR}|${+cell.dataset.heatT}`;
  const was = binSel.has(k); binSel.clear(); zoneSel.clear(); if (!was) binSel.add(k);
  window.liveRedraw();
}, true);

// pinned card for a clicked cluster on the session chart
let pinned = null;
$('live-chart').addEventListener('click', event => {
  const r = event.target.closest('.lv-hit');
  document.querySelectorAll('#live-chart .lv-hit.pinned').forEach(e => e.classList.remove('pinned'));
  let card = document.getElementById('lv-card');
  if (!r || (pinned && pinned === r.dataset.info)) { if (card) card.remove(); pinned = null; clearGuides(); return; }
  const [what, when, idr, prices, count, pct] = r.dataset.info.split('|');
  pinned = r.dataset.info; r.classList.add('pinned'); hideTip(); showGuides(r);
  if (!card) { card = document.createElement('div'); card.id = 'lv-card'; $('live-chart').parentElement.appendChild(card); }
  card.innerHTML = `<button type="button" class="lv-card-x" aria-label="Закрыть">×</button><div class="lv-card-t">${what}</div><div class="lv-card-p">${pct}</div>` +
    `<div class="lv-card-r"><span>Время</span><b>${when}</b></div><div class="lv-card-r"><span>Цена</span><b>${prices}</b></div>` +
    `<div class="lv-card-r"><span>Шкала</span><b>${idr}</b></div><div class="lv-card-r"><span>Сессий</span><b>${count}</b></div>`;
  const box = $('live-chart').parentElement.getBoundingClientRect(), rr = r.getBoundingClientRect();
  let left = rr.left - box.left - 232;                                   // left of the cluster: the time and price guides stay visible
  if (left < 4) left = Math.min(rr.right - box.left + 8, box.width - 230);
  const top = Math.max(4, Math.min(rr.top - box.top - 10, box.height - 150));
  card.style.left = left + 'px'; card.style.top = top + 'px';
});

// a click on a candle replays the whole screen as of its close; a second click on it returns to live
$('live-chart').addEventListener('click', event => {
  if (event.target.closest('.lv-hit')) return;
  const bar = event.target.closest('[data-bar]'); if (!bar) return;
  const at = +bar.dataset.bar + 5;
  replayAt = replayAt === at ? null : at;
  liveFetch(false);
});

// thin guides from a cluster to the time axis (bottom) and the price scale (right), with boundary labels
const NS = 'http://www.w3.org/2000/svg';
let hiddenLabels = [];
function clearGuides() {
  const old = document.getElementById('lv-guides'); if (old) old.remove();
  hiddenLabels.forEach(e => { e.style.visibility = ''; }); hiddenLabels = [];
}
function showGuides(r) {
  const svgEl = $('live-chart').querySelector('svg'); if (!svgEl || !r || !r.dataset.g) return;
  clearGuides();
  const geo = JSON.parse($('live-chart').dataset.geo || '{}'), [tl, tr, plo, phi] = r.dataset.g.split('|');
  const x0 = +r.getAttribute('x'), w = +r.getAttribute('width'), y0 = +r.getAttribute('y'), hh = +r.getAttribute('height');
  const base = geo.h - geo.pb, g = document.createElementNS(NS, 'g'); g.id = 'lv-guides'; g.setAttribute('pointer-events', 'none');
  const line = (a, b, c, d) => { const l = document.createElementNS(NS, 'line'); Object.entries({x1: a, y1: b, x2: c, y2: d, stroke: '#cbd5e1', 'stroke-width': .6, 'stroke-dasharray': '2 3', opacity: .55}).forEach(([k, v]) => l.setAttribute(k, v)); g.appendChild(l); };
  const label = (tx, ty, text, anchor) => {
    const t = document.createElementNS(NS, 'text'); t.textContent = text; t.setAttribute('x', tx); t.setAttribute('y', ty); t.setAttribute('text-anchor', anchor);
    t.setAttribute('fill', '#4ade80'); t.setAttribute('class', 'lv-guide'); g.appendChild(t); return t;
  };
  line(x0, y0 + hh, x0, base); line(x0 + w, y0 + hh, x0 + w, base);
  line(x0 + w, y0, geo.xe, y0); line(x0 + w, y0 + hh, geo.xe, y0 + hh);
  const narrow = w < 40, ty = geo.h - 6;
  const labs = [label(narrow ? x0 - 2 : x0, ty, tl, narrow ? 'end' : 'middle'), label(narrow ? x0 + w + 2 : x0 + w, ty, tr, narrow ? 'start' : 'middle')];
  const flat = hh < 15;
  labs.push(label(geo.xe + 8, (flat ? y0 - 4 : y0 + 4), phi, 'start'), label(geo.xe + 8, (flat ? y0 + hh + 12 : y0 + hh + 4), plo, 'start'));
  svgEl.appendChild(g);
  // dark pills under the labels, and the labels they would cover step aside for a moment
  const boxes = labs.map(t => t.getBBox());
  labs.forEach((t, i) => { const b = boxes[i], bg = document.createElementNS(NS, 'rect');
    Object.entries({x: b.x - 3, y: b.y - 1, width: b.width + 6, height: b.height + 2, rx: 3, fill: '#0b131c', opacity: .95}).forEach(([k, v]) => bg.setAttribute(k, v));
    g.insertBefore(bg, t); });
  svgEl.querySelectorAll('text').forEach(e => {
    if (e.closest('#lv-guides')) return;
    const b = e.getBBox();
    if (boxes.some(q => q.x < b.x + b.width + 2 && b.x < q.x + q.width + 2 && q.y < b.y + b.height && b.y < q.y + q.height)) { e.style.visibility = 'hidden'; hiddenLabels.push(e); }
  });
}
function restorePin() {
  hiddenLabels = [];
  if (!pinned) return;
  const r = [...document.querySelectorAll('#live-chart .lv-hit')].find(e => e.dataset.info === pinned);
  if (!r) { const card = document.getElementById('lv-card'); if (card) card.remove(); pinned = null; return; }
  r.classList.add('pinned'); showGuides(r);
}
$('live-chart').addEventListener('mouseover', e => { const r = e.target.closest('.lv-hit'); if (r) showGuides(r); });
$('live-chart').addEventListener('mouseout', e => {
  if (!e.target.closest('.lv-hit')) return;
  const pin = pinned && [...document.querySelectorAll('#live-chart .lv-hit')].find(q => q.dataset.info === pinned);
  if (pin) showGuides(pin); else clearGuides();
});
// while a card is open, cluster hover shows guides only: no second box on top of the card
$('live-chart').addEventListener('pointermove', e => { if (pinned && e.target.closest('.lv-hit')) { e.stopPropagation(); hideTip(); } });

// the × on the card closes it
document.addEventListener('click', e => {
  if (!e.target.closest('#lv-card .lv-card-x')) return;
  const card = document.getElementById('lv-card'); if (card) card.remove();
  document.querySelectorAll('#live-chart .lv-hit.pinned').forEach(q => q.classList.remove('pinned'));
  pinned = null; clearGuides();
});
