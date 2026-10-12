// Q1 pilot — in-page check of the review scene. Evaluate in the browser on http://127.0.0.1:8771/ once a scene has
// loaded and a comparison set is chosen (the address carries est=...). Returns {problems: [...], checked: [...]}.
// It compares what the page SHOWS with what the pilot server SAYS: the page must not invent, round away or drop a count.
(async () => {
  const problems = [], checked = [];
  const h = new URLSearchParams(location.hash.slice(1));
  const est = h.get("est");
  const q = new URLSearchParams({ inst: h.get("inst"), block: h.get("block"), date: h.get("date"), cut: h.get("cut"), level: h.get("level") });
  const resp = await fetch("/api/q1/scene?" + q.toString());
  const sc = await resp.json();
  const has = (el, v, what) => { checked.push(what); if (!document.getElementById(el).innerText.includes(String(v))) problems.push(`${what}: ${v} not shown in #${el}`); };
  // 1. the scene the page received carries no candle after the cut (the future comes only with an outcome)
  const cutMin = sc.target.formed + 5 * (sc.cut + 1);
  checked.push("no candle after the cut in the scene");
  if (sc.candles.some((r) => r[0] + 5 > cutMin)) problems.push("the scene carries candles after the cut");
  // 2. the marking of the pilot's own passport, never the accepted gate
  checked.push("contract header");
  if (!(resp.headers.get("X-DR-Lab-Contract") || "").includes("PILOT_OUTSIDE_SC11_GATE")) problems.push("the response is not marked as the pilot outside the SC-1.1 gate");
  // 3. the question and today's state
  has("question", sc.levels[h.get("level")].price.toFixed(sc.target.tick < 1 ? 2 : 0).split(".")[0].replace(/\B(?=(\d{3})+(?!\d))/g, " "), "place price in the question");
  if (sc.state.status === "OPEN" && est) {
    const a = sc.answers[est], c = a.counts;
    // 4. the answer: the counts, and the share computed from exactly those counts
    for (const [v, w] of [[c.n_match, "n"], [c.yes, "yes"], [c.no, "no"]]) has("answer", v, "answer shows " + w);
    if (a.estimate.publication === "PUBLISHED") {
      const p = (n, d) => { const x = Math.round(1000 * n / d) / 10; return Number.isInteger(x) ? String(x) : x.toFixed(1).replace(".", ","); };
      has("answer", p(c.yes, c.n_match), "share lower bound = yes / n");
      if (c.unknown) { has("answer", p(c.yes + c.unknown, c.n_match), "share upper bound = (yes + unknown) / n"); has("answer", c.unknown, "unknown count"); }
    } else has("answer", c.n_match, "withheld: n shown, no share");
    // 5. the eligibility chain and every member row
    for (const [v, w] of [[c.N_parent, "N_parent"], [c.N_eligible, "N_eligible"], [c.N_not_yet, "N_not_yet"]]) has("basis", v, "funnel " + w);
    checked.push("member rows");
    const rows = [...document.querySelectorAll("#basis tr[role=button]")].map((tr) => tr.dataset.id);
    const ids = a.members.map((m) => m.id);
    if (rows.length !== ids.length || rows.some((x, k) => x !== ids[k])) problems.push(`member rows ${rows.length} vs members ${ids.length}`);
    const yesRows = [...document.querySelectorAll("#basis tr[role=button] .yes")].length;
    checked.push("YES rows");
    if (yesRows !== c.yes) problems.push(`rows marked «дошли» ${yesRows} vs yes ${c.yes}`);
  }
  // 6. the saved answers listed are the store's issues of this target, nothing more
  const st = await (await fetch("/api/q1/issues?target_id=" + sc.target_id)).json();
  checked.push("saved answers list");
  const listed = document.querySelectorAll("#issue tr[role=button]").length;
  if (listed !== st.issues.length) problems.push(`saved answers listed ${listed} vs stored ${st.issues.length}`);
  return { problems, checked: checked.length, scene: `${h.get("inst")} ${h.get("block")} ${h.get("date")} cut ${sc.cut} ${h.get("level")} ${est || "(no set)"}` };
})();
