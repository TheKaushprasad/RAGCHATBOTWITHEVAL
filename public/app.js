const log = document.getElementById("log");
const form = document.getElementById("form");
const input = document.getElementById("input");
const send = document.getElementById("send");
const tpl = document.getElementById("msg-tpl");
const historyNav = document.getElementById("history");
const convTitle = document.getElementById("conv-title");

const STARTERS = [
  "What does the swiss cheese capability model mean?",
  "What are the main agentic design patterns?",
  "What are embeddings and embedding models?",
  "regression vs classification?",
];

let conversationId = null; // null = a new chat that hasn't been saved yet
let docCounts = { shared: 0, mine: 0 };

// --- auth + API -------------------------------------------------------------------------

async function token() {
  const session = await getSession(); // supabase-js refreshes the token when needed
  if (!session) return goToLogin();
  return session.access_token;
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    ...options,
    headers: { Authorization: `Bearer ${await token()}`, ...(options.headers || {}) },
  });
  if (res.status === 401) return goToLogin();
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : `Request failed (${res.status})`);
  return data;
}

// Upload with progress events (fetch can't report upload progress).
async function apiUpload(file, onProgress) {
  const auth = await token();
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/upload");
    xhr.setRequestHeader("Authorization", `Bearer ${auth}`);
    xhr.upload.onprogress = (e) => e.lengthComputable && onProgress(e.loaded / e.total);
    xhr.upload.onload = () => onProgress(1);
    xhr.onload = () => {
      let data = {};
      try { data = JSON.parse(xhr.responseText); } catch { /* non-JSON error page */ }
      if (xhr.status === 401) return goToLogin();
      if (xhr.status >= 200 && xhr.status < 300) resolve(data);
      else reject(new Error(typeof data.detail === "string" ? data.detail : `Upload failed (${xhr.status})`));
    };
    xhr.onerror = () => reject(new Error("Network error during upload."));
    const body = new FormData();
    body.append("file", file);
    xhr.send(body);
  });
}

function goToLogin() {
  location.replace(`/login/?next=${encodeURIComponent(location.pathname + location.hash)}`);
  return new Promise(() => {});
}

// --- small helpers ----------------------------------------------------------------------

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function icon(paths) {
  const span = el("span", "ico");
  span.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true">${paths}</svg>`; // static markup only
  return span;
}

function relTime(iso) {
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  if (s < 86400 * 7) return `${Math.floor(s / 86400)}d ago`;
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

function fileKind(name) {
  const ext = (name.split(".").pop() || "").toLowerCase();
  return { pdf: "pdf", docx: "docx", md: "md", markdown: "md", mdx: "md", txt: "txt" }[ext] || "txt";
}

function fileBadge(name) {
  const kind = fileKind(name);
  return el("span", `ft ${kind}`, { pdf: "PDF", docx: "W", md: "M↓", txt: "TXT" }[kind]);
}

function where(c) {
  const parts = [];
  if (c.page) parts.push(`Page ${c.page}`);
  if (c.heading) parts.push(c.heading);
  if (!parts.length) parts.push(`Passage ${c.chunk_index + 1}`);
  return parts.join(" · ");
}

function plural(n, word) {
  return `${n} ${word}${n === 1 ? "" : "s"}`;
}

// --- empty state ------------------------------------------------------------------------

function showEmpty() {
  log.replaceChildren();
  const box = el("div", "empty");
  box.id = "empty";
  const logo = el("img", "empty-logo");
  logo.src = "/favicon.svg";
  logo.alt = "";
  box.append(
    logo,
    el("h2", "", "Ask your documents anything"),
    el("p", "", "Answers come from the shared AI PM notes and anything you upload, and every claim links to its source."),
  );
  const grid = el("div", "starters");
  for (const q of STARTERS) {
    const b = el("button", "starter", q);
    b.type = "button";
    b.addEventListener("click", () => ask(q));
    grid.append(b);
  }
  const upload = el("button", "link-btn", "Or upload your own document");
  upload.type = "button";
  upload.addEventListener("click", openUploadPicker);
  box.append(grid, upload);
  log.append(box);
}

// --- messages ---------------------------------------------------------------------------

function addMessage(kind) {
  document.getElementById("empty")?.remove();
  const node = tpl.content.firstElementChild.cloneNode(true);
  node.classList.add(...kind.split(" "));
  log.appendChild(node);
  log.scrollTop = log.scrollHeight;
  return node;
}

function renderAnswer(node, question, data) {
  const body = node.querySelector(".body");
  const cites = node.querySelector(".cites");
  body.replaceChildren();

  if (!data.grounded) {
    renderNotFound(node, question, data);
    return;
  }

  const byN = new Map(data.citations.map((c) => [c.n, c]));
  const cite = (n) => {
    if (!byN.has(n)) return null;
    const ref = el("button", "ref", String(n));
    ref.type = "button";
    ref.title = `${byN.get(n).source} · ${where(byN.get(n))}`;
    ref.addEventListener("click", () => openSources(data, n));
    return ref;
  };
  body.append(renderMarkdown(data.answer, cite));

  // Compact source chips under the answer; details open in the side panel.
  const docs = new Set(data.citations.map((c) => c.source));
  if (data.citations.length) {
    const summary = el("button", "src-link", `Based on ${plural(data.citations.length, "passage")} from ${plural(docs.size, "document")}`);
    summary.type = "button";
    summary.addEventListener("click", () => openSources(data, data.citations[0].n));
    cites.append(summary);
    for (const c of data.citations) {
      const chip = el("button", "chip");
      chip.type = "button";
      chip.append(el("b", "", String(c.n)), fileBadge(c.source), el("span", "", c.source), el("small", "", where(c)));
      chip.title = `${c.source} · ${where(c)}`;
      chip.addEventListener("click", () => openSources(data, c.n));
      cites.append(chip);
    }
  }
  if (data.searched_for) {
    const note = el("p", "searched", "");
    note.append("Searched for: ", el("q", "", data.searched_for));
    node.insertBefore(note, body);
  }
}

function renderNotFound(node, question, data) {
  node.classList.add("notfound");
  const body = node.querySelector(".body");
  const head = el("div", "nf-head");
  head.append(icon('<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2M8.5 11h5"/>'), el("strong", "", "Not found in your documents"));
  // Keep the model's explanation if it gave one beyond "I don't know."
  const detail = data.answer.replace(/^\s*I don['’]t know\.?\s*/i, "").trim();
  const text = el("p", "", detail || "I couldn't find anything about this in the shared notes or your uploads, so I won't guess.");
  const actions = el("div", "nf-actions");
  const rephrase = el("button", "nf-btn", "Rephrase question");
  rephrase.type = "button";
  rephrase.addEventListener("click", () => {
    input.value = question;
    input.dispatchEvent(new Event("input"));
    input.focus();
    input.setSelectionRange(input.value.length, input.value.length);
  });
  const upload = el("button", "nf-btn primary", "Upload a document");
  upload.type = "button";
  upload.addEventListener("click", openUploadPicker);
  actions.append(rephrase, upload);
  body.append(head, text, actions);
}

function showExchange(question, answer) {
  addMessage("user").querySelector(".body").textContent = question;
  const bot = addMessage("bot");
  renderAnswer(bot, question, answer);
  renderFeedback(bot, question, answer, answer.answer_id, answer.rating || 0);
  return bot;
}

// --- source panel -----------------------------------------------------------------------

const sourcesPanel = document.getElementById("sources");
const srcList = document.getElementById("src-list");

function openSources(data, selectedN) {
  const docs = new Set(data.citations.map((c) => c.source));
  document.getElementById("src-summary").textContent =
    `${plural(data.citations.length, "passage")} from ${plural(docs.size, "document")}`;
  srcList.replaceChildren();
  for (const c of data.citations) {
    const li = el("li", "src-item" + (c.n === selectedN ? " selected" : ""));
    const headBtn = el("button", "src-item-head");
    headBtn.type = "button";
    headBtn.setAttribute("aria-expanded", String(c.n === selectedN));
    const name = el("span", "src-name");
    name.append(el("b", "", c.source), el("small", "", where(c)));
    headBtn.append(el("span", "src-n", String(c.n)), fileBadge(c.source), name);
    const passage = el("blockquote", "src-passage", c.snippet);
    passage.hidden = c.n !== selectedN;
    const meta = el("p", "src-meta", `${c.uploaded ? "Your upload" : "Shared notes"} · relevance ${Math.round(c.similarity * 100)}%`);
    meta.hidden = passage.hidden;
    headBtn.addEventListener("click", () => {
      const open = passage.hidden;
      passage.hidden = !open;
      meta.hidden = !open;
      li.classList.toggle("selected", open);
      headBtn.setAttribute("aria-expanded", String(open));
    });
    li.append(headBtn, passage, meta);
    srcList.append(li);
  }
  sourcesPanel.hidden = false;
  document.body.classList.add("sources-open");
  srcList.querySelector(".selected")?.scrollIntoView({ block: "nearest" });
}

function closeSources() {
  sourcesPanel.hidden = true;
  document.body.classList.remove("sources-open");
}
document.getElementById("src-close").addEventListener("click", closeSources);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !sourcesPanel.hidden) closeSources();
});

// --- answer feedback (thumbs up / down) -------------------------------------------------

const THUMB_UP = '<path d="M7 10v11H4V10zM7 10l4-7c1.7 0 2.7 1.2 2.4 2.8L12.8 9H19a2 2 0 0 1 2 2.3l-1.2 7.4A2.7 2.7 0 0 1 17.2 21H7"/>';
const THUMB_DOWN = '<path d="M17 14V3h3v11zM17 14l-4 7c-1.7 0-2.7-1.2-2.4-2.8l.6-3.2H5a2 2 0 0 1-2-2.3l1.2-7.4A2.7 2.7 0 0 1 6.8 3H17"/>';

function renderFeedback(node, question, data, answerId, initialRating = 0) {
  if (!answerId) return;
  let rating = initialRating;

  const bar = el("div", "feedback");
  const fbLabel = el("span", "fb-label", "Was this helpful?");

  const makeThumb = (value, svg, name) => {
    const b = el("button", "thumb");
    b.type = "button";
    b.setAttribute("aria-label", name);
    b.setAttribute("aria-pressed", String(rating === value));
    b.title = name;
    b.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true">${svg}</svg>`; // static icon markup only
    b.addEventListener("click", () => vote(rating === value ? 0 : value));
    return b;
  };
  const up = makeThumb(1, THUMB_UP, "Helpful");
  const down = makeThumb(-1, THUMB_DOWN, "Not helpful");
  const status = el("span", "fb-status");
  status.setAttribute("role", "status");

  // Optional reason, shown after a thumbs down.
  const fbForm = el("form", "fb-form");
  fbForm.hidden = true;
  const reason = el("input");
  reason.type = "text";
  reason.maxLength = 1000;
  reason.placeholder = "What was wrong? (optional)";
  reason.setAttribute("aria-label", "What was wrong with this answer?");
  const sendReason = el("button", "", "Send");
  sendReason.type = "submit";
  fbForm.append(reason, sendReason);

  async function save(value, comment = null) {
    await api("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        answer_id: answerId,
        rating: value,
        comment,
        question,
        answer: data.answer,
        sources: data.citations.map((c) => ({ source: c.source, chunk_index: c.chunk_index, page: c.page })),
        grounded: data.grounded,
      }),
    });
  }

  function setPressed(value) {
    up.setAttribute("aria-pressed", String(value === 1));
    down.setAttribute("aria-pressed", String(value === -1));
  }

  async function vote(value) {
    const previous = rating;
    rating = value;
    setPressed(value);
    fbForm.hidden = value !== -1;
    status.textContent = "";
    try {
      await save(value);
      status.textContent = value === 1 ? "Thanks!" : value === -1 ? "Thanks — tell us what was wrong?" : "";
      if (value === -1) reason.focus();
    } catch (err) {
      rating = previous;
      setPressed(previous);
      fbForm.hidden = previous !== -1;
      status.textContent = `Couldn't save feedback: ${err.message}`;
    }
  }

  fbForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const comment = reason.value.trim();
    if (!comment) return;
    sendReason.disabled = true;
    try {
      await save(-1, comment);
      fbForm.hidden = true;
      status.textContent = "Thanks — that helps improve the answers.";
    } catch (err) {
      status.textContent = `Couldn't save feedback: ${err.message}`;
    } finally {
      sendReason.disabled = false;
    }
  });

  bar.append(fbLabel, up, down, status);
  node.append(bar, fbForm);
}

// --- suggested follow-ups ---------------------------------------------------------------

async function showSuggestions(convId) {
  document.querySelectorAll(".suggestions").forEach((n) => n.remove());
  let questions = [];
  try {
    questions = (await api(`/api/conversations/${convId}/suggestions`, { method: "POST" })).questions;
  } catch {
    return; // suggestions are a nice-to-have; never surface an error for them
  }
  if (!questions.length || convId !== conversationId || send.disabled) return;
  const row = el("div", "suggestions");
  row.append(el("span", "sugg-label", "Try asking:"));
  for (const q of questions) {
    const b = el("button", "sugg", q);
    b.type = "button";
    b.addEventListener("click", () => ask(q));
    row.append(b);
  }
  log.append(row);
  log.scrollTop = log.scrollHeight;
}

// --- asking -----------------------------------------------------------------------------

async function ask(message) {
  if (send.disabled) return;
  document.querySelectorAll(".suggestions").forEach((n) => n.remove());
  addMessage("user").querySelector(".body").textContent = message;
  const bot = addMessage("bot pending");
  bot.querySelector(".body").textContent = "Searching your documents…";
  send.disabled = true;

  try {
    const data = await api("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, conversation_id: conversationId }),
    });
    bot.classList.remove("pending");
    renderAnswer(bot, message, data);
    renderFeedback(bot, message, data, data.answer_id);
    if (conversationId !== data.conversation_id) {
      conversationId = data.conversation_id;
      history.replaceState(null, "", `#c=${conversationId}`);
    }
    loadHistory(); // new chats appear, and the active one moves to the top
    if (data.grounded) setTimeout(() => showSuggestions(data.conversation_id), 0);
  } catch (err) {
    bot.classList.remove("pending");
    bot.classList.add("error");
    bot.querySelector(".body").textContent = err.message;
  } finally {
    send.disabled = false;
    input.focus();
    log.scrollTop = log.scrollHeight;
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message || send.disabled) return;
  input.value = "";
  input.style.height = "";
  ask(message);
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 200)}px`;
});

// --- history sidebar --------------------------------------------------------------------

const sidebar = document.getElementById("sidebar");
const scrim = document.getElementById("scrim");
const historySearch = document.getElementById("history-search");
let conversations = [];

function setSidebar(open) {
  sidebar.classList.toggle("open", open);
  scrim.hidden = !open;
}
document.getElementById("side-open").addEventListener("click", () => setSidebar(true));
document.getElementById("side-close").addEventListener("click", () => setSidebar(false));
scrim.addEventListener("click", () => setSidebar(false));
historySearch.addEventListener("input", renderHistory);

function renderHistory() {
  historyNav.replaceChildren();
  const q = historySearch.value.trim().toLowerCase();
  const shown = q ? conversations.filter((c) => c.title.toLowerCase().includes(q)) : conversations;
  if (!shown.length) {
    historyNav.append(el("p", "muted side-empty", q ? "No chats match your search." : "No conversations yet."));
    return;
  }
  for (const c of shown) {
    const row = el("div", "conv" + (c.id === conversationId ? " active" : ""));
    const open = el("button", "conv-open");
    open.type = "button";
    open.title = c.title;
    open.append(el("span", "conv-title", c.title), el("span", "conv-time", relTime(c.updated_at)));
    if (c.id === conversationId) open.setAttribute("aria-current", "true");
    open.addEventListener("click", () => {
      setSidebar(false);
      openConversation(c.id);
    });
    const del = el("button", "conv-del");
    del.type = "button";
    del.setAttribute("aria-label", `Delete “${c.title}”`);
    del.title = "Delete";
    del.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/></svg>';
    del.addEventListener("click", async () => {
      if (!confirm(`Delete “${c.title}”? This can't be undone.`)) return;
      try {
        await api(`/api/conversations/${c.id}`, { method: "DELETE" });
        if (c.id === conversationId) newChat();
        await loadHistory();
      } catch (err) {
        alert(`Couldn't delete: ${err.message}`);
      }
    });
    row.append(open, del);
    historyNav.append(row);
  }
}

async function loadHistory() {
  try {
    conversations = (await api("/api/conversations")).conversations;
  } catch {
    conversations = [];
  }
  renderHistory();
  const current = conversations.find((c) => c.id === conversationId);
  convTitle.textContent = current ? current.title : "New chat";
}

function newChat() {
  conversationId = null;
  history.replaceState(null, "", location.pathname);
  closeSources();
  showEmpty();
  convTitle.textContent = "New chat";
  renderHistory();
  input.focus();
}

async function openConversation(id) {
  conversationId = id;
  history.replaceState(null, "", `#c=${id}`);
  closeSources();
  renderHistory();
  log.replaceChildren();
  const loading = addMessage("bot pending");
  loading.querySelector(".body").textContent = "Loading conversation…";
  try {
    const { messages } = await api(`/api/conversations/${id}`);
    log.replaceChildren();
    let question = "";
    let lastGrounded = false;
    for (const m of messages) {
      if (m.role === "user") {
        question = m.content;
        continue;
      }
      showExchange(question, {
        answer: m.content, citations: m.citations || [], grounded: m.grounded,
        answer_id: m.answer_id, rating: m.rating,
      });
      lastGrounded = Boolean(m.grounded);
    }
    if (!messages.length) showEmpty();
    const current = conversations.find((c) => c.id === id);
    convTitle.textContent = current ? current.title : "Chat";
    if (lastGrounded) showSuggestions(id);
  } catch (err) {
    log.replaceChildren();
    addMessage("bot error").querySelector(".body").textContent = err.message;
    conversationId = null;
    history.replaceState(null, "", location.pathname);
  }
  log.scrollTop = log.scrollHeight;
}

document.getElementById("new-chat").addEventListener("click", () => {
  setSidebar(false);
  newChat();
});

document.getElementById("logout").addEventListener("click", async () => {
  const client = await getAuthClient();
  await client.auth.signOut();
  location.replace("/");
});

// --- documents panel --------------------------------------------------------------------

const docsPanel = document.getElementById("docs");
const docsToggle = document.getElementById("docs-toggle");
const uploadsList = document.getElementById("uploads");
const samplesList = document.getElementById("samples");
const statusEl = document.getElementById("upload-status");
const fileInput = document.getElementById("file");
const drop = document.getElementById("drop");
let maxBytes = 4 * 1024 * 1024;
let uploading = false;
const pending = new Map(); // file name -> { state, progress, error } while uploading

function setStatus(text, kind = "") {
  statusEl.textContent = text;
  statusEl.className = `status ${kind}`;
}

function setDocsPanel(open) {
  docsPanel.hidden = !open;
  docsToggle.setAttribute("aria-expanded", String(open));
}

function openUploadPicker() {
  setDocsPanel(true);
  fileInput.click();
}

function updateScope() {
  const total = docCounts.shared + docCounts.mine;
  document.getElementById("scope").textContent = total
    ? `Searching ${plural(total, "document")}${docCounts.mine ? ` · ${docCounts.mine} uploaded by you` : ""}`
    : "Answers come only from your documents, with sources.";
}

function docItem(d, onRemove) {
  const li = el("li");
  li.append(fileBadge(d.source));
  const name = el("span", "name", d.source);
  name.title = d.source;
  li.append(name);
  if (onRemove) {
    li.append(el("span", "doc-state ready", "Ready"), el("span", "meta", plural(d.chunks, "chunk")));
    const rm = el("button", "remove", "Remove");
    rm.type = "button";
    rm.setAttribute("aria-label", `Remove ${d.source}`);
    rm.addEventListener("click", () => onRemove(rm));
    li.append(rm);
  }
  return li;
}

function pendingItem(name, p) {
  const li = el("li", `pending ${p.state}`);
  li.append(fileBadge(name));
  const info = el("span", "name");
  info.append(name);
  if (p.state === "uploading") {
    const bar = el("span", "progress");
    const fill = el("span");
    fill.style.width = `${Math.round(p.progress * 100)}%`;
    bar.append(fill);
    info.append(bar);
  }
  if (p.error) info.append(el("small", "doc-error", p.error));
  li.append(info);
  const label = { uploading: `Uploading ${Math.round(p.progress * 100)}%`, indexing: "Indexing…", failed: "Failed" }[p.state];
  li.append(el("span", `doc-state ${p.state}`, label));
  if (p.state === "failed") {
    const dismiss = el("button", "remove", "Dismiss");
    dismiss.type = "button";
    dismiss.addEventListener("click", () => {
      pending.delete(name);
      renderDocs(lastDocs);
    });
    li.append(dismiss);
  }
  return li;
}

let lastDocs = { uploads: [], sample: [], limits: { max_mb: 4, max_files: 5 } };

function renderDocs(data) {
  lastDocs = data;
  const items = [...pending.entries()].map(([name, p]) => pendingItem(name, p));
  for (const d of data.uploads) {
    if (pending.has(d.source) && pending.get(d.source).state !== "failed") continue;
    items.push(docItem(d, async (btn) => {
      if (!confirm(`Remove ${d.source}? Answers will no longer use it.`)) return;
      btn.disabled = true;
      try {
        await api(`/api/documents/${encodeURIComponent(d.source)}`, { method: "DELETE" });
        await loadDocs();
        setStatus(`Removed ${d.source}.`);
      } catch (err) {
        setStatus(err.message, "error");
        btn.disabled = false;
      }
    }));
  }
  if (!items.length) {
    const li = el("li", "muted doc-empty");
    li.append("No uploads yet. Add a PDF, Word, Markdown or text file and ask about it.");
    items.push(li);
  }
  uploadsList.replaceChildren(...items);
  samplesList.replaceChildren(...data.sample.map((d) => docItem(d)));
  document.getElementById("sample-count").textContent = data.sample.length;
  document.getElementById("docs-count").textContent = data.uploads.length ? `(${data.uploads.length} yours)` : "";

  const { max_mb, max_files } = data.limits;
  maxBytes = max_mb * 1024 * 1024;
  document.getElementById("limits").textContent = `max ${max_mb} MB each, ${max_files} files`;
  docCounts = { shared: data.sample.length, mine: data.uploads.length };
  updateScope();
}

async function loadDocs() {
  try {
    renderDocs(await api("/api/documents"));
  } catch (err) {
    setStatus(`Couldn't load documents: ${err.message}`, "error");
  }
}

async function uploadFiles(files) {
  if (uploading || !files.length) return;
  uploading = true;
  setDocsPanel(true);
  setStatus("");
  for (const file of files) pending.set(file.name, { state: "uploading", progress: 0 });
  renderDocs(lastDocs);
  try {
    for (const file of files) {
      const p = pending.get(file.name);
      if (file.size > maxBytes) {
        Object.assign(p, { state: "failed", error: `Larger than ${maxBytes / 1024 / 1024} MB.` });
        renderDocs(lastDocs);
        continue;
      }
      try {
        const r = await apiUpload(file, (fraction) => {
          Object.assign(p, fraction >= 1 ? { state: "indexing", progress: 1 } : { progress: fraction });
          renderDocs(lastDocs);
        });
        pending.delete(file.name);
        setStatus(`${r.source} is ready (${plural(r.chunks, "chunk")}). Ask a question about it.`, "ok");
      } catch (err) {
        Object.assign(p, { state: "failed", error: err.message });
      }
      await loadDocs();
    }
  } finally {
    uploading = false;
  }
}

docsToggle.addEventListener("click", () => setDocsPanel(docsPanel.hidden));
document.getElementById("pick").addEventListener("click", () => fileInput.click());
document.getElementById("attach").addEventListener("click", openUploadPicker);
fileInput.addEventListener("change", () => {
  uploadFiles([...fileInput.files]);
  fileInput.value = "";
});
drop.addEventListener("dragover", (e) => {
  e.preventDefault();
  drop.classList.add("over");
});
drop.addEventListener("dragleave", () => drop.classList.remove("over"));
drop.addEventListener("drop", (e) => {
  e.preventDefault();
  drop.classList.remove("over");
  uploadFiles([...e.dataTransfer.files]);
});

// --- start ------------------------------------------------------------------------------

(async () => {
  const session = await requireLogin();
  const email = session.user.email || "";
  const emailEl = document.getElementById("user-email");
  emailEl.textContent = email;
  emailEl.title = email;
  document.getElementById("avatar").textContent = (email[0] || "?").toUpperCase();
  document.body.classList.remove("is-loading");

  // If the session ends in another tab, leave this one too.
  (await getAuthClient()).auth.onAuthStateChange((event) => {
    if (event === "SIGNED_OUT") location.replace("/");
  });

  showEmpty();
  loadDocs();
  await loadHistory();
  const fromHash = location.hash.match(/^#c=([0-9a-f-]{36})$/i);
  if (fromHash) await openConversation(fromHash[1]);
})();
