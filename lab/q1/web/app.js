"use strict";
// DR Lab · Q1 — the review scene of the historical pilot (Q1-PILOT-0.2, C1). Every number comes from the local pilot
// server (lab/q1/server.py); every word next to a number comes from its passport (/api/q1/meta). The page computes no
// share itself: it formats the counts it receives, and a stored answer is shown from its file, never recomputed.

const $ = (id) => document.getElementById(id);
const WD = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"];
const S = { meta: null, inst: "NQ", block: "RDR", dates: [], date: null, cut: null, level: "-1/2", est: null,
            scene: null, seq: 0, reveal: null, lastSave: null };

function remember(k, v) {           // a per-viewer convenience only (the chosen set); the page works without it
  try { if (v === undefined) return localStorage.getItem("q1." + k); localStorage.setItem("q1." + k, v); } catch (e) { return null; }
  return null;
}

async function api(path, body) {
  const opt = body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  try {
    const r = await fetch(path, opt);
    return await r.json();
  } catch (e) {
    return { status: "ERROR", error: "локальный сервер пилота не ответил" };
  }
}

// ---------- formatting (Russian: decimal comma, thin groups) ----------
function pct(num, den) {
  if (!den) return "—";
  const v = Math.round(1000 * num / den) / 10;
  return Number.isInteger(v) ? String(v) : v.toFixed(1).replace(".", ",");
}
function sd(v) { return (v >= 0 ? "+" : "−") + Math.abs(v).toFixed(2).replace(".", ","); }
function price(p, tick) {
  const s = Number(p).toFixed(tick < 1 ? 2 : 0);
  const [i, f] = s.split(".");
  return i.replace(/\B(?=(\d{3})+(?!\d))/g, " ") + (f ? "," + f : "");
}
function hm(m) { m = ((m % 1440) + 1440) % 1440; return String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0"); }
function esc(s) { return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
function short(h) { return h ? h.slice(0, 10) : "—"; }
function words(key, vars) { let s = (S.meta.states[key] || key); for (const [k, v] of Object.entries(vars || {})) s = s.replace("{" + k + "}", v); return s; }
function setName(est) { return S.meta.estimators[est].name; }
function cutClose() { const c = (S.scene.cuts || []).find((x) => x.index === S.scene.cut); return c ? c.close : "—"; }
function cutMinute() { const t = S.scene.target; return t.formed + 5 * (S.scene.cut + 1); }

// ---------- the address: a scene can be reopened from its link ----------
function readHash() {
  const h = new URLSearchParams(location.hash.slice(1));
  if (h.get("inst")) S.inst = h.get("inst");
  if (h.get("block")) S.block = h.get("block");
  if (h.get("date")) S.date = h.get("date");
  if (h.get("cut")) S.cut = Number(h.get("cut"));
  if (h.get("level")) S.level = h.get("level");
  if (h.get("est")) S.est = h.get("est");
}
function writeHash() {
  const h = new URLSearchParams({ inst: S.inst, block: S.block, date: S.date || "", cut: S.cut == null ? "" : String(S.cut), level: S.level });
  if (S.est) h.set("est", S.est);
  history.replaceState(null, "", "#" + h.toString());
}

// ---------- controls ----------
function seg(id, values, label, get, set) {
  const el = $(id);
  el.innerHTML = "";
  for (const v of values) {
    const b = document.createElement("button");
    b.textContent = label(v);
    b.className = get() === v ? "on" : "";
    b.onclick = () => { if (get() !== v) { set(v); } };
    el.appendChild(b);
  }
}
function renderControls() {
  seg("inst", S.meta.instruments, (v) => v, () => S.inst, (v) => { S.inst = v; S.date = null; S.cut = null; loadDates(); });
  seg("block", S.meta.blocks, (v) => v, () => S.block, (v) => { S.block = v; S.date = null; S.cut = null; loadDates(); });
  seg("level", Object.keys(S.meta.levels), (v) => S.meta.levels[v], () => S.level, (v) => { S.level = v; loadScene(); });
  $("date").value = S.date || "";
  const sc = S.scene;
  const r = $("cut");
  if (sc && sc.cuts && sc.cuts.length) {
    r.min = sc.cuts[0].index; r.max = sc.cuts[sc.cuts.length - 1].index; r.value = sc.cut; r.disabled = false;
    $("cutLabel").textContent = cutClose();
  } else { r.disabled = true; $("cutLabel").textContent = "—"; }
}

async function loadDates() {
  renderControls();
  const r = await api(`/api/q1/dates?inst=${S.inst}&block=${S.block}`);
  if (r.status === "ERROR") return fail(r.error);
  S.dates = r.dates;
  $("dates").innerHTML = r.dates.map((d) => `<option value="${d[0]}">${d[1]} · ${d[2] > 0 ? "лонг" : "шорт"}</option>`).join("");
  const have = new Set(r.dates.map((d) => d[0]));
  if (!S.date || !have.has(S.date)) { S.date = snap(S.date) || r.dates[r.dates.length - 1][0]; S.cut = null; }
  await loadScene();
}
function snap(d) {
  if (!d) return null;
  const ds = S.dates.map((x) => x[0]);
  const k = ds.findIndex((x) => x >= d);
  return k < 0 ? ds[ds.length - 1] : ds[k];
}
function stepDate(k) {
  const ds = S.dates.map((x) => x[0]);
  const i = ds.indexOf(S.date);
  const j = Math.min(ds.length - 1, Math.max(0, i + k));
  if (ds[j] !== S.date) { S.date = ds[j]; S.cut = null; loadScene(); }
}

async function loadScene() {
  const seq = ++S.seq;
  S.reveal = null;                                    // the later candles are hidden again on every new scene
  const q = new URLSearchParams({ inst: S.inst, block: S.block, date: S.date, level: S.level });
  if (S.cut != null) q.set("cut", String(S.cut));
  const sc = await api("/api/q1/scene?" + q.toString());
  if (seq !== S.seq) return;                          // a late answer of an earlier scene never becomes this one
  if (sc.status === "ERROR") return fail(sc.error);
  S.scene = sc;
  S.cut = sc.cut;
  writeHash();
  render();
}

function fail(msg) { $("answer").innerHTML = `<h3>Ошибка</h3><div class="bad">${esc(msg || "")}</div>`; }

// ---------- the side panel ----------
function render() {
  renderControls();
  drawChart();
  renderQuestion();
  renderToday();
  renderSets();
  renderAnswer();
  renderBasis();
  renderIssue();
  renderCompare();
  renderPassport();
}

function levelPrice() { const L = S.scene.levels[S.level]; return price(L.price, S.scene.target.tick); }

function renderQuestion() {
  const sc = S.scene, t = sc.target;
  $("question").innerHTML = `<h3>Вопрос</h3>
    <div class="q">Дойдёт ли цена после <b>${cutClose()}</b> до места «${esc(S.meta.levels[S.level])}» — <b>${levelPrice()}</b> — до <b>${hm(t.end)}</b>?</div>
    <div class="sub">${t.instrument} ${t.block} · ${t.date} (${WD[t.weekday]}) · ${t.side > 0 ? "лонг" : "шорт"} · подтверждение ${t.activation_close}</div>`;
}

function renderToday() {
  const sc = S.scene, st = sc.state, t = sc.target;
  let body = "";
  if (st.status === "OPEN") {
    const last = sc.candles[sc.candles.length - 1];
    const left = t.end - cutMinute();
    body = `К ${st.cut_close}: закрытие <b>${price(last[4], t.tick)}</b> (${sd(st.close_v / st.w)} ширины IDR от края), глубже всего после подтверждения ${sd(st.r_v / st.w)}.
      До места цена ещё не доходила; до конца сессии ${left} мин.`;
  } else {
    body = esc(words(st.status, { time: st.time || "" }));
  }
  $("today").innerHTML = `<h3>Сегодня на срезе</h3><div>${body}</div>`;
}

function renderSets() {
  const sc = S.scene;
  const btns = S.meta.order.map((est) => {
    const a = sc.answers && sc.answers[est];
    const n = a && a.counts ? `n = ${a.counts.n_match}` : "";
    return `<button data-est="${est}" class="${S.est === est ? "on" : ""}">${esc(setName(est))}<span class="n">${n}</span></button>`;
  }).join("");
  const desc = S.est ? `<div class="sub">${esc(S.meta.estimators[S.est].set_ru)}${S.est === "GEO" ? " · " + esc(S.meta.estimators.GEO.status) : ""}</div>`
    : `<div class="sub">Выберите, с какими сессиями сравнивать. Какой набор считать основным, решает оператор; здесь можно посмотреть каждый.</div>`;
  $("sets").innerHTML = `<h3>С какими сессиями сравнивать</h3><div class="setbtns">${btns}</div>${desc}`;
  for (const b of $("sets").querySelectorAll("button")) b.onclick = () => { S.est = b.dataset.est; remember("est", S.est); writeHash(); render(); };
}

function answerHtml(c, e, cut, end, n0) {
  if (e.publication === "WITHHELD_FEW_SESSIONS") {
    return `<div class="big small">мало сессий: n = ${c.n_match}</div><div class="sub">Число не показываем: меньше ${n0} сессий в наборе. Кто в наборе и их исходы — в разделе «Из чего ответ».</div>`;
  }
  if (e.publication === "NO_KNOWN_OUTCOME") return `<div class="big small">числа нет</div><div class="sub">У всех ${c.n_match} сессий набора исход неизвестен (нет свечей M5).</div>`;
  if (e.publication === "REFERENCE_MISMATCH") return `<div class="big small bad">число снято</div><div class="sub">Вторая реализация расчёта не совпала по составу; причина записана в выпуске.</div>`;
  const big = c.unknown === 0 ? `${pct(c.yes, c.n_match)} %` : `${pct(c.yes, c.n_match)}–${pct(c.yes + c.unknown, c.n_match)} %`;
  const unk = c.unknown ? `, неизвестно <b class="unk">${c.unknown}</b> (нет свечей M5) — среди известных ${pct(c.yes, c.n_known)} %` : "";
  return `<div class="big">${big}</div>
    <div>Из <b>${c.n_match}</b> сессий набора, которые в ${cut} стояли там же и ещё не были у места, до него потом дошли <b class="yes">${c.yes}</b>,
    не дошли <b>${c.no}</b>${unk}. Срок — до ${end}.</div>`;
}

function renderAnswer() {
  const sc = S.scene, t = sc.target;
  let body;
  if (sc.state.status !== "OPEN") body = `<div class="sub">${esc(words(sc.state.status, { time: sc.state.time || "" }))}</div>`;
  else if (!S.est) body = `<div class="sub">Сначала выберите набор сравнения.</div>`;
  else { const a = sc.answers[S.est]; body = answerHtml(a.counts, a.estimate, cutClose(), hm(t.end), 20); }
  $("answer").innerHTML = `<h3>Что было у таких сессий после ${cutClose()}</h3>${body}`;
}

function rowAction(tr, fn) { tr.onclick = fn; tr.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fn(); } }; }
function winText(w) { const f = S.scene.target.formed; return `${hm(f + 15 * w)}–${hm(f + 15 * w + 15)}`; }
function labelHtml(m) {
  if (m.label === "YES") return `<span class="yes">дошли ${m.first_reach ? m.first_reach.close : ""}${m.first_reach && !m.first_reach.time_known ? " (время неизвестно)" : ""}</span>`;
  if (m.label === "UNKNOWN") return `<span class="unk">неизвестно</span>`;
  return `<span class="no">не дошли</span>`;
}

function renderBasis() {
  const sc = S.scene;
  if (sc.state.status !== "OPEN" || !S.est) { $("basis").innerHTML = `<h3>Из чего ответ</h3><div class="sub">—</div>`; return; }
  const a = sc.answers[S.est], c = a.counts, R = S.meta.reasons;
  const ex = Object.entries(c.excluded).filter(([, n]) => n > 0).map(([k, n]) => `${esc(R[k])}: ${n}`).join(" · ");
  const rows = a.members.map((m) => `<tr class="click" role="button" tabindex="0" data-id="${m.id}"><td>${m.date}</td><td>${m.side > 0 ? "лонг" : "шорт"}</td><td>${winText(m.window)}</td>
      <td>${sd(m.close_v / m.w)}</td><td>${sd(m.r_v / m.w)}</td><td>${labelHtml(m)}</td></tr>`).join("");
  $("basis").innerHTML = `<h3>Из чего ответ</h3>
    <div class="funnel">
      <span class="k">сессий в наборе, раньше этой даты</span><span class="v">${c.N_parent}</span>
      <span class="k">к ${cutClose()} подтвердились, свечи после — целые, DR цел</span><span class="v">${c.N_eligible}</span>
      <span class="k">ещё не были у места</span><span class="v">${c.N_not_yet}</span>
      <span class="k">стояли там же: закрытие в пределах ¼ ширины IDR</span><span class="v"><b>${c.n_match}</b></span>
      <span class="k">дошли · не дошли · неизвестно</span><span class="v"><span class="yes">${c.yes}</span> · ${c.no} · <span class="unk">${c.unknown}</span></span>
    </div>
    <div class="sub">Не вошли: ${ex || "—"}. <span class="link" id="popLink">все сессии набора с причиной</span></div>
    <table><thead><tr><th>дата</th><th>сторона</th><th>окно подтв.</th><th>закрытие</th><th>откат к срезу</th><th>потом</th></tr></thead><tbody>${rows}</tbody></table>
    <div class="sub">Закрытие и откат — в ширинах IDR своей сессии, на тот же час. Нажмите строку, чтобы увидеть путь сессии.</div>`;
  $("popLink").onclick = openPopulation;
  for (const tr of $("basis").querySelectorAll("tr.click")) rowAction(tr, () => openCase(tr.dataset.id));
}

function pubText(s) {
  if (s.publication === "PUBLISHED") return s.counts.unknown ? `${pct(s.counts.yes, s.counts.n_match)}–${pct(s.counts.yes + s.counts.unknown, s.counts.n_match)} %` : `${pct(s.counts.yes, s.counts.n_match)} %`;
  if (s.publication === "WITHHELD_FEW_SESSIONS") return `мало сессий (n = ${s.counts.n_match})`;
  if (s.publication === "NO_KNOWN_OUTCOME") return "исход неизвестен у всех";
  return "число снято";
}

function renderIssue() {
  const sc = S.scene;
  const can = sc.state.status === "OPEN" && !!S.est;
  const saved = (sc.saved || []).slice().sort((x, y) => (x.cut.index - y.cut.index) || x.estimator.localeCompare(y.estimator));
  const list = saved.length ? `<table><thead><tr><th>срез</th><th>набор</th><th>ответ</th><th>исход</th></tr></thead><tbody>${saved.map((s) =>
      `<tr class="click" role="button" tabindex="0" data-id="${s.issue_id}"><td>${s.cut.close}</td><td>${esc(setName(s.estimator))}</td><td>${pubText(s)}</td><td>${s.outcomes ? "присоединён" : "—"}</td></tr>`).join("")}</tbody></table>`
    : `<div class="sub">Для этого места этой сессии сохранённых ответов пока нет.</div>`;
  const last = S.lastSave ? `<div class="sub">${S.lastSave}</div>` : "";
  $("issue").innerHTML = `<h3>Сохранить ответ</h3>
    <button class="btn" id="saveOne" ${can ? "" : "disabled"}>Сохранить ответ этого набора</button>
    <button class="btn ghost" id="saveAll" ${sc.state.status === "OPEN" ? "" : "disabled"}>…всех трёх наборов</button>
    ${last}<h3 style="margin-top:8px">Сохранённые ответы для этого места</h3>${list}
    <div class="sub"><span class="link" id="verifyLink">проверить все сохранённые записи</span></div>`;
  $("saveOne").onclick = () => save([S.est]);
  $("saveAll").onclick = () => save(S.meta.order);
  $("verifyLink").onclick = openVerify;
  for (const tr of $("issue").querySelectorAll("tr.click")) rowAction(tr, () => openIssue(tr.dataset.id));
}

async function save(ests) {
  const out = [];
  for (const est of ests) {
    const r = await api("/api/q1/issue", { inst: S.inst, block: S.block, date: S.date, cut: S.cut, level: S.level, est });
    if (r.status === "CREATED" || r.status === "IDEMPOTENT") {
      out.push(`${esc(setName(est))}: ${r.status === "CREATED" ? "записан" : "уже был записан (тот же ответ, файл не тронут)"} — выпуск ${short(r.summary.issue_id)}, отпечаток ${short(r.summary.payload_sha256)}`);
    } else out.push(`${esc(setName(est))}: ${esc(r.status)} ${esc(r.error || "")}`);
  }
  S.lastSave = out.join("<br>");
  const keep = { cut: S.cut };
  await loadScene();
  S.cut = keep.cut;
}

function renderCompare() {
  const sc = S.scene;
  if (sc.state.status !== "OPEN") { $("compareBody").innerHTML = `<div class="sub">—</div>`; return; }
  const rows = S.meta.order.map((est) => {
    const a = sc.answers[est], c = a.counts;
    return `<tr><td>${esc(setName(est))}</td><td>${c.N_parent}</td><td>${c.n_match}</td><td><span class="yes">${c.yes}</span> · ${c.no} · <span class="unk">${c.unknown}</span></td><td>${pubText({ publication: a.estimate.publication, counts: c })}</td></tr>`;
  }).join("");
  $("compareBody").innerHTML = `<div class="sub" style="margin:6px 0">Один и тот же вопрос, посчитанный по разным наборам истории. Это не три прогноза:
      у каждого числа свой набор и свой знаменатель. Вопрос, срез, место, срок и сегодняшнее состояние у всех одни.</div>
    <table><thead><tr><th>набор</th><th>в наборе</th><th>там же</th><th>дошли · нет · неизв.</th><th>ответ</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function renderPassport() {
  const m = S.meta, C = m.claim;
  $("passportBody").innerHTML = `<div class="sub" style="margin-top:6px">
    <p><b>Что это за число.</b> Описание истории выбранного набора (класс C1), не прогноз на сегодня. ${esc(C.grammar_ru)}.</p>
    <p><b>Событие.</b> ${esc(C.event_ru)}.</p><p><b>Кто в наборе.</b> ${esc(C.condition_ru)}.</p>
    <p><b>Срок.</b> ${esc(C.horizon_ru)}.</p><p><b>Неизвестно.</b> ${esc(C.unknown_ru)}; такие сессии остаются в наборе.</p>
    <p><b>Так читать нельзя:</b> ${C.forbidden_ru.map(esc).join("; ")}.</p>
    <p><b>Где это живёт.</b> ${esc(m.profile)} · ${esc(m.status)}. Модель ${short(m.model)} · код ${esc(short((m.code || {}).commit))} · база ${esc(m.corpus)} · записи ${esc(m.store)}.</p></div>`;
}

// ---------- drawer: population, one case, a stored issue, verification ----------
function drawer(title, html) { $("drawerTitle").textContent = title; $("drawerBody").innerHTML = html; $("drawer").classList.remove("hidden"); }
$("drawerClose").onclick = () => $("drawer").classList.add("hidden");

async function openPopulation() {
  const q = new URLSearchParams({ inst: S.inst, block: S.block, date: S.date, cut: String(S.cut), level: S.level, est: S.est });
  const r = await api("/api/q1/population?" + q.toString());
  if (r.status === "ERROR") return drawer("Ошибка", esc(r.error));
  const R = S.meta.reasons;
  const order = ["MATCH", "FAR", "ALREADY_AT_L", "DR_BROKEN", "PREFIX_HOLE", "NOT_ACTIVATED"];
  const rows = r.rows.slice().sort((x, y) => order.indexOf(x.reason) - order.indexOf(y.reason) || y.date.localeCompare(x.date)).map((x) =>
    `<tr><td>${x.date}</td><td>${x.side > 0 ? "лонг" : "шорт"}</td><td>${winText(x.window)}</td><td>${WD[x.weekday]}</td>
      <td>${x.close_u == null ? "" : sd(x.close_u)}</td><td>${x.r_u == null ? "" : sd(x.r_u)}</td><td>${esc(R[x.reason])}</td></tr>`).join("");
  drawer(`Все сессии набора «${setName(S.est)}» · ${cutClose()}`, `<div class="sub">Сегодня в ${cutClose()} закрытие ${sd(r.today_close_u)}; «там же» — в пределах ±0,25.
    Причина — первая, что не пустила сессию в набор. Всего ${r.rows.length}.</div>
    <table><thead><tr><th>дата</th><th>сторона</th><th>окно</th><th>день</th><th>закрытие</th><th>откат</th><th>почему</th></tr></thead><tbody>${rows}</tbody></table>`);
}

async function openCase(id) {
  const q = new URLSearchParams({ inst: S.inst, block: S.block, id, cut: String(S.cut), level: S.level });
  const r = await api("/api/q1/case?" + q.toString());
  if (r.status === "ERROR") return drawer("Ошибка", esc(r.error));
  const fr = r.first_reach ? `дошла до места в ${r.first_reach.close}${r.first_reach.time_known ? "" : " (время первой свечи неизвестно)"}` : "до места после среза не дошла";
  drawer(`Сессия ${r.date} · ${r.side > 0 ? "лонг" : "шорт"}`, `<div class="sub">Подтверждение ${r.activation_close}; путь в ширинах IDR своей сессии
    (0 — край IDR на стороне подтверждения, −1 — другой край). Срез ${r.grid[r.cut]}; ${fr}. Светлые свечи — до среза, тёмные — после.</div>
    <canvas class="mini" id="mini"></canvas>`);
  drawMini($("mini"), r);
}

function outcomeText(o, end) {
  const ob = o.payload.observed;
  if (ob.label === "YES") return `Исход: <b class="yes">дошли до места в ${ob.first_reach.close}</b>${ob.first_reach.time_known ? "" : " (время первой свечи неизвестно: перед ней нет свечи)"}`;
  if (ob.label === "NO") return `Исход: <b>до ${end} не дошли</b>`;
  return `Исход: <b class="unk">неизвестно</b> — среди имеющихся свечей не дошли; нет свечей ${ob.missing_after_cut.join(", ")}`;
}

async function openIssue(id, msg) {
  const openedAt = S.seq;
  const r = await api("/api/q1/issue?id=" + id);
  if(openedAt!==S.seq)return;
  if (r.status !== "OK") return drawer("Выпуск не найден", esc(id));
  const rec = r.record, pl = rec.payload, mt = rec.meta, t = pl.target;
  const same = pl.target.date === S.date && pl.target.instrument === S.inst && pl.target.block === S.block && pl.cut.index === S.cut && pl.target.level.name === S.level;
  const outs = r.outcomes.map((o) => `<div>${outcomeText(o, t.horizon_end)} · запись ${short(o.payload.outcome_id)} (ревизия ${o.payload.revision}${o.payload.supersedes ? ", заменяет " + short(o.payload.supersedes) : ""})
      · связана с выпуском по отпечатку ${short(o.payload.issue_payload_sha256)} ${o.payload.issue_payload_sha256 === mt.payload_sha256 ? '<span class="ok">— совпадает</span>' : '<span class="bad">— не совпадает</span>'}</div>`).join("");
  drawer(`Сохранённый ответ · выпуск ${short(pl.issue_id)}`, `
    <div class="sub">Записан ${esc(mt.created_utc)} · код ${esc(short((mt.code || {}).commit))} · ${pl.issue_kind === "SIMULATED_ISSUE" ? "восстановленный исторический выпуск: сделан сейчас по данным до этой даты; будущее этого дня в базе уже было" : esc(pl.issue_kind)}
      ${mt.outcomes_on_record_for_target ? " · в момент записи исход этой цели уже был в журнале" : ""}</div>
    <p>${t.instrument} ${t.block} · ${t.date} · место «${esc(S.meta.levels[t.level.name])}» · срез ${pl.cut.close} · до ${t.horizon_end} · набор «${esc(setName(pl.estimator.id))}»</p>
    <div class="card">${answerHtml(pl.counts, pl.estimate, pl.cut.close, t.horizon_end, pl.estimator.support_min)}
      <div class="sub">Числа — из файла выпуска, не пересчитаны. ${r.integrity ? '<span class="ok">Файл не менялся: отпечаток содержимого совпадает.</span>' : '<span class="bad">Содержимое файла не совпадает со своим отпечатком.</span>'}</div></div>
    <div>
      <button class="btn" id="repro">Повторить расчёт на тех же данных</button>
      <button class="btn" id="outc">${r.outcomes.length ? "Обновить исход" : "Показать исход"}</button>
      ${same ? "" : '<button class="btn ghost" id="goto">Открыть эту сцену</button>'}
      <button class="btn ghost" id="raw">Исходный файл</button>
    </div>
    <div id="issueMsg" class="sub" style="margin-top:6px">${msg || ""}</div>
    <h3 style="margin-top:10px">Исход</h3>${outs || '<div class="sub">Исход ещё не присоединён. Он ляжет отдельной записью; сам выпуск не изменится.</div>'}
    <div class="sub">Состав: ${pl.members.length} сессий; входные данные ${short(pl.inputs.input_digest)} (префикс сессии ${short(pl.inputs.target_prefix_digest)}, история до даты ${short(pl.inputs.domain_digest)}, ${pl.inputs.domain_sessions} сессий); модель ${short(pl.inputs.model)}.</div>
    <pre class="raw hidden" id="rawBox">${esc(JSON.stringify(rec, null, 1))}</pre>`);
  $("raw").onclick = () => $("rawBox").classList.toggle("hidden");
  $("rawBox").classList.add("hidden");
  $("repro").onclick = async () => {
    const x = await api("/api/q1/reproduce", { id });
    const m = { IDENTICAL: `<span class="ok">Пересчёт на исходных данных совпал байт в байт</span> (отпечаток ${short(x.recomputed_sha256)}).`,
      INPUTS_CHANGED: `<span class="warn">Данные изменились с момента записи (${(x.changed || []).join(", ")}): точный повтор невозможен; новый расчёт был бы другим выпуском.</span>`,
      MODEL_CHANGED: `<span class="warn">Код расчёта другой, чем при записи: повтор — только на коде ${esc(short(((x.code || {}).commit)))}.</span>`,
      DIFFERENT: `<span class="bad">Пересчёт на тех же входах дал другие байты — ошибка воспроизводимости.</span>` }[x.status] || esc(x.status);
    $("issueMsg").innerHTML = m;
  };
  $("outc").onclick = async () => {
    const token=S.seq;
    const x = await api("/api/q1/outcome", { id });
    if(token!==S.seq||same&&(S.date!==t.date||S.inst!==t.instrument||S.block!==t.block||S.cut!==pl.cut.index||S.level!==t.level.name))return;
    let m = "";
    if (x.status === "REFUSED") m = `<span class="bad">Исход не присоединён: он посчитан на других данных префикса или цель к срезу уже решена (${esc(JSON.stringify(x.check))}).</span>`;
    else if (x.status === "CREATED") m = `<span class="ok">Исход записан отдельной записью; выпуск не изменился.</span>`;
    else if (x.status === "IDEMPOTENT") m = `Исход уже был записан; ничего не переписано.`;
    if (same && x.after) { S.reveal = { id, after: x.after, outcome: x.outcomes[x.outcomes.length - 1] }; drawChart(); }
    if(x.reveal_status==='SOURCE_REVISION_MISMATCH'){S.reveal=null;drawChart();m=esc(x.message);}
    openIssue(id, m);
  };
  if (!same) $("goto").onclick = async () => {
    S.inst = t.instrument; S.block = t.block; S.date = t.date; S.cut = pl.cut.index; S.level = t.level.name; S.est = pl.estimator.id;
    await loadDates();
    const token=S.seq;
    const x = await api("/api/q1/outcome?id=" + id);
    if(token!==S.seq||S.date!==t.date||S.inst!==t.instrument||S.block!==t.block||S.cut!==pl.cut.index||S.level!==t.level.name)return;
    if (x.after) { S.reveal = { id, after: x.after, outcome: x.outcomes[x.outcomes.length - 1] }; drawChart(); }
    openIssue(id);
  };
  if (same && r.outcomes.length) {
    const x = await api("/api/q1/outcome?id=" + id);
    if(openedAt!==S.seq||S.date!==t.date||S.inst!==t.instrument||S.block!==t.block||S.cut!==pl.cut.index||S.level!==t.level.name)return;
    if(x.reveal_status==='SOURCE_REVISION_MISMATCH'){S.reveal=null;drawChart();}
    if (x.after) { S.reveal = { id, after: x.after, outcome: x.outcomes[x.outcomes.length - 1] }; drawChart(); }
  }
}

async function openVerify() {
  const v = await api("/api/q1/verify");
  drawer("Проверка сохранённых записей", `<p>Выпусков: ${v.issues}, исходов: ${v.outcomes}.</p>
    ${v.ok ? '<p class="ok">Все отпечатки содержимого, идентичности и связи исходов с выпусками сходятся.</p>' : `<p class="bad">Найдено: ${v.problems.map(esc).join("<br>")}</p>`}
    <p class="sub">${v.writable.length ? "Файлы, доступные для записи: " + v.writable.map(esc).join(", ") : "Все файлы записей — только для чтения."}</p>`);
}

// ---------- the chart: today's session up to the cut ----------
function drawChart() {
  const cv = $("chart");
  const dpr = window.devicePixelRatio || 1;
  const Wc = cv.clientWidth, Hc = cv.clientHeight;
  cv.width = Math.round(Wc * dpr); cv.height = Math.round(Hc * dpr);
  const g = cv.getContext("2d");
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.clearRect(0, 0, Wc, Hc);
  const sc = S.scene;
  if (!sc) return;
  const t = sc.target, tick = t.tick;
  const padL = 8, padR = 86, padT = 14, padB = 26;
  const W = Wc - padL - padR, H = Hc - padT - padB;
  const x0 = t.start, x1 = t.end + 10;
  const cand = sc.candles, after = S.reveal ? S.reveal.after : [];
  let lo = Infinity, hi = -Infinity;
  for (const r of cand.concat(after)) { lo = Math.min(lo, r[3]); hi = Math.max(hi, r[2]); }
  for (const p of [t.box.drH, t.box.drL, t.box.idrH, t.box.idrL]) { lo = Math.min(lo, p); hi = Math.max(hi, p); }
  for (const L of Object.values(sc.levels)) { lo = Math.min(lo, L.price); hi = Math.max(hi, L.price); }
  const pad = (hi - lo) * 0.06 || 1; lo -= pad; hi += pad;
  const X = (m) => padL + (m - x0) / (x1 - x0) * W;
  const Y = (p) => padT + (hi - p) / (hi - lo) * H;
  const cm = cutMinute();
  // the box hour and the horizon
  g.fillStyle = "rgba(255,255,255,0.035)"; g.fillRect(X(t.start), padT, X(t.formed) - X(t.start), H);
  if (sc.state.status !== "BLOCK_OVER") { g.fillStyle = "rgba(240,167,66,0.055)"; g.fillRect(X(cm), padT, X(t.end) - X(cm), H); }
  // time grid
  g.font = "11px Segoe UI, sans-serif"; g.fillStyle = "#6f7886"; g.strokeStyle = "#1c212b"; g.lineWidth = 1;
  for (let m = Math.ceil(x0 / 30) * 30; m <= t.end; m += 30) { g.beginPath(); g.moveTo(X(m) + .5, padT); g.lineTo(X(m) + .5, padT + H); g.stroke(); g.fillText(hm(m), X(m) - 14, Hc - 8); }
  // box levels
  const hline = (p, color, dash, width) => { g.strokeStyle = color; g.setLineDash(dash); g.lineWidth = width; g.beginPath(); g.moveTo(padL, Y(p) + .5); g.lineTo(padL + W, Y(p) + .5); g.stroke(); g.setLineDash([]); };
  const tagR = (p, text, color) => { g.fillStyle = color; g.fillText(text, padL + W + 6, Y(p) + 4); };
  hline(t.box.drH, "#7b838f", [], 1); hline(t.box.drL, "#7b838f", [], 1);
  hline(t.box.idrH, "#59626e", [4, 3], 1); hline(t.box.idrL, "#59626e", [4, 3], 1);
  tagR(t.box.drH, "DR " + price(t.box.drH, tick), "#8a929d"); tagR(t.box.drL, "DR " + price(t.box.drL, tick), "#8a929d");
  for (const [nm, L] of Object.entries(sc.levels)) {
    if (nm === S.level) continue;
    hline(L.price, "rgba(240,167,66,0.28)", [2, 4], 1);
  }
  const Lsel = sc.levels[S.level];
  hline(Lsel.price, "#f0a742", [], 2);
  tagR(Lsel.price, "место " + price(Lsel.price, tick), "#f0a742");
  // candles up to the cut
  const bar = (r, up, down, alpha) => {
    const xa = X(r[0]), xb = X(r[0] + 5), w = Math.max(1, xb - xa - 1.2);
    const col = r[4] >= r[1] ? up : down;
    g.globalAlpha = alpha; g.strokeStyle = col; g.fillStyle = col;
    g.beginPath(); g.moveTo(xa + w / 2, Y(r[2])); g.lineTo(xa + w / 2, Y(r[3])); g.stroke();
    const yo = Y(r[1]), yc = Y(r[4]);
    g.fillRect(xa, Math.min(yo, yc), w, Math.max(1, Math.abs(yc - yo)));
    g.globalAlpha = 1;
  };
  for (const r of cand) bar(r, "#3daf7c", "#e0565b", 1);
  for (const r of after) bar(r, "#8d96a3", "#5d6570", 0.55);
  // the cut
  g.strokeStyle = "#cfd5dd"; g.setLineDash([5, 4]); g.lineWidth = 1;
  g.beginPath(); g.moveTo(X(cm) + .5, padT); g.lineTo(X(cm) + .5, padT + H); g.stroke(); g.setLineDash([]);
  g.fillStyle = "#cfd5dd"; g.fillText("срез " + hm(cm), X(cm) + 4, padT + 12);
  if (sc.state.status !== "BLOCK_OVER") { g.fillStyle = "#b9894a"; g.fillText("до " + hm(t.end), X(t.end) - 46, padT + 12); }
  // the revealed outcome
  if (S.reveal && S.reveal.outcome) {
    const ob = S.reveal.outcome.payload.observed;
    if (ob.label === "YES") {
      const [hh, mm] = ob.first_reach.close.split(":").map(Number);
      const m = hh * 60 + mm - 2.5;
      g.strokeStyle = "#f0a742"; g.lineWidth = 2; g.beginPath(); g.arc(X(m), Y(Lsel.price), 7, 0, 2 * Math.PI); g.stroke();
      g.fillStyle = "#f0a742"; g.fillText("дошли " + ob.first_reach.close, X(m) + 10, Y(Lsel.price) - 8);
    }
  }
  $("legend").textContent = "Свечи до среза; пунктир — срез; жёлтая линия — выбранное место, бледные — два других; подсвечен срок до конца сессии"
    + (S.reveal ? "; серые свечи — что было дальше (исход)" : ".");
}

function drawMini(cv, r) {
  const dpr = window.devicePixelRatio || 1;
  const Wc = cv.clientWidth, Hc = cv.clientHeight;
  cv.width = Math.round(Wc * dpr); cv.height = Math.round(Hc * dpr);
  const g = cv.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0);
  const n = r.path.length, padL = 40, padR = 10, padT = 10, padB = 22, W = Wc - padL - padR, H = Hc - padT - padB;
  let lo = Math.min(-1.1, r.level - 0.1), hi = 1.1;
  for (const p of r.path) if (p) { lo = Math.min(lo, p[0]); hi = Math.max(hi, p[1]); }
  const X = (k) => padL + (k + 0.5) / n * W, Y = (u) => padT + (hi - u) / (hi - lo) * H;
  g.font = "11px Segoe UI, sans-serif";
  const hl = (u, col, dash, lab) => { g.strokeStyle = col; g.setLineDash(dash); g.beginPath(); g.moveTo(padL, Y(u)); g.lineTo(padL + W, Y(u)); g.stroke(); g.setLineDash([]); g.fillStyle = col; g.fillText(lab, 2, Y(u) + 4); };
  hl(0, "#7b838f", [], "0"); hl(-1, "#7b838f", [4, 3], "−1"); hl(r.level, "#f0a742", [], String(r.level).replace(".", ","));
  g.strokeStyle = "#cfd5dd"; g.setLineDash([5, 4]); g.beginPath(); g.moveTo(X(r.cut) + 3, padT); g.lineTo(X(r.cut) + 3, padT + H); g.stroke(); g.setLineDash([]);
  for (let k = 0; k < n; k++) {
    const p = r.path[k]; if (!p) continue;
    g.strokeStyle = k <= r.activation ? "#4a525d" : k <= r.cut ? "#cfd5dd" : "#6c7480";
    g.beginPath(); g.moveTo(X(k), Y(p[0])); g.lineTo(X(k), Y(p[1])); g.stroke();
    g.beginPath(); g.moveTo(X(k), Y(p[2])); g.lineTo(X(k) + 3, Y(p[2])); g.stroke();
  }
  if (r.first_reach) { g.strokeStyle = "#f0a742"; g.beginPath(); g.arc(X(r.first_reach.index), Y(r.level), 6, 0, 2 * Math.PI); g.stroke(); }
  g.fillStyle = "#6f7886";
  for (let k = 0; k < n; k += 6) g.fillText(r.grid[k], X(k) - 14, Hc - 6);
}

// ---------- start ----------
$("prev").onclick = () => stepDate(-1);
$("next").onclick = () => stepDate(1);
$("date").onchange = () => { const d = snap($("date").value.trim()); if (d && d !== S.date) { S.date = d; S.cut = null; loadScene(); } };
let cutTimer = null;
$("cut").oninput = () => {
  const k = Number($("cut").value);
  const c = (S.scene.cuts || []).find((x) => x.index === k);
  $("cutLabel").textContent = c ? c.close : "—";
  clearTimeout(cutTimer);
  cutTimer = setTimeout(() => { S.cut = k; loadScene(); }, 120);
};
window.addEventListener("resize", () => drawChart());

(async function init() {
  S.meta = await api("/api/q1/meta");
  if (S.meta.status === "ERROR" || !S.meta.levels) return fail(S.meta.error || "нет паспорта пилота");
  readHash();
  if (!S.est) S.est = remember("est");
  if (S.est && !S.meta.estimators[S.est]) S.est = null;
  await loadDates();
})();
