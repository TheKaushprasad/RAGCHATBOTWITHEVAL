// Metrics dashboard: reads /api/admin/metrics (admins only) and renders three tables.
const msg = document.getElementById("msg");
const daysSelect = document.getElementById("days");

const secs = (v) => (v == null ? "–" : `${v.toFixed(v < 10 ? 2 : 1)}s`);
const pct = (v) => `${(v * 100).toFixed(v > 0 && v < 0.1 ? 1 : 0)}%`;
const usd = (v) => `$${v < 1 ? v.toFixed(4) : v.toFixed(2)}`;
const num = (v) => v.toLocaleString();

function row(cells, header) {
  const tr = document.createElement("tr");
  cells.forEach((c, i) => {
    const cell = document.createElement(header && i === 0 ? "th" : "td");
    cell.textContent = c;
    tr.append(cell);
  });
  return tr;
}

async function load() {
  msg.textContent = "Loading…";
  msg.className = "admin-msg";
  const session = await requireLogin();
  const res = await fetch(`/api/admin/metrics?days=${daysSelect.value}`, {
    headers: { Authorization: `Bearer ${session.access_token}` },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    msg.textContent = res.status === 403 ? "This page is for admins only." : data.detail || `Couldn't load metrics (${res.status}).`;
    msg.className = "admin-msg error";
    document.getElementById("report").hidden = true;
    return;
  }
  const o = data.overall;
  document.getElementById("overall").replaceChildren(
    row(["Questions", num(o.questions)], true),
    row(["Latency p50 / p95", `${secs(o.p50_s)} / ${secs(o.p95_s)}`], true),
    row(["First word p50 / p95 (streaming)", `${secs(o.first_token_p50_s)} / ${secs(o.first_token_p95_s)}`], true),
    row(["Error rate", `${pct(o.error_rate)} (${num(o.errors)})`], true),
    row(["Cache hit rate", pct(o.cache_hit_rate)], true),
    row(["Answered from documents", pct(o.grounded_rate)], true),
    row(["Tokens", num(o.tokens)], true),
    row(["Estimated cost", `${usd(o.cost_usd)} (${o.questions ? usd(o.cost_usd / o.questions) : "–"} per question)`], true),
  );
  document.getElementById("days-body").replaceChildren(
    ...data.days.slice().reverse().map((d) => row([
      d.day, num(d.questions), secs(d.p50_s), secs(d.p95_s), secs(d.first_token_p95_s),
      `${pct(d.error_rate)}`, pct(d.cache_hit_rate), pct(d.grounded_rate), num(d.tokens), usd(d.cost_usd),
    ])),
  );
  const names = { rewrite: "Rewrite follow-up", cache: "Cache lookup", search: "Search", rerank: "Rerank",
    first_token: "First word", answer: "Write answer", save: "Save to history", total: "Total" };
  document.getElementById("stages").replaceChildren(
    ...Object.entries(data.stages).map(([k, v]) => row([names[k] || k, secs(v.p50), secs(v.p95)])),
  );
  msg.textContent = o.questions ? "" : "No questions in this period yet.";
  document.getElementById("report").hidden = false;
}

daysSelect.addEventListener("change", load);
load().catch((err) => {
  msg.textContent = err.message;
  msg.className = "admin-msg error";
});
