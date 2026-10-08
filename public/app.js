const log = document.getElementById("log");
const form = document.getElementById("form");
const input = document.getElementById("input");
const send = document.getElementById("send");
const tpl = document.getElementById("msg-tpl");

// A random id for this browser. Uploads are stored under it, so only this browser can search them.
const SESSION_KEY = "rag-session-id";
let sessionId;
try {
  sessionId = localStorage.getItem(SESSION_KEY);
  if (!sessionId) localStorage.setItem(SESSION_KEY, (sessionId = crypto.randomUUID()));
} catch {
  sessionId = crypto.randomUUID(); // storage blocked: uploads last for this page view only
}

async function api(path, options = {}) {
  const res = await fetch(path, { ...options, headers: { "X-Session-Id": sessionId, ...(options.headers || {}) } });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : `Request failed (${res.status})`);
  return data;
}

// --- chat -------------------------------------------------------------------------------

function addMessage(kind) {
  document.getElementById("empty")?.remove();
  const node = tpl.content.firstElementChild.cloneNode(true);
  node.classList.add(...kind.split(" "));
  log.appendChild(node);
  log.scrollTop = log.scrollHeight;
  return node;
}

function label(c) {
  const where = c.page ? `p. ${c.page}` : c.heading ? c.heading : `chunk ${c.chunk_index}`;
  return `${c.uploaded ? "📄 " : ""}${c.source} · ${where}`;
}

function renderAnswer(node, data) {
  const body = node.querySelector(".body");
  const cites = node.querySelector(".cites");
  const detail = node.querySelector(".cite-detail");
  const byN = new Map(data.citations.map((c) => [c.n, c]));
  const chips = new Map();

  function toggle(n) {
    const c = byN.get(n);
    const open = !detail.hidden && detail.dataset.n === String(n);
    chips.forEach((chip) => chip.setAttribute("aria-expanded", "false"));
    if (open) {
      detail.hidden = true;
      return;
    }
    detail.dataset.n = n;
    detail.replaceChildren();
    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = `[${n}] ${label(c)} — similarity ${c.similarity.toFixed(2)}`;
    detail.append(meta, document.createTextNode(c.snippet));
    detail.hidden = false;
    chips.get(n)?.setAttribute("aria-expanded", "true");
  }

  // Build the answer as text nodes + [n] buttons (no innerHTML, so model output can't inject markup).
  for (const part of data.answer.split(/(\[\d+\])/g)) {
    const m = part.match(/^\[(\d+)\]$/);
    const n = m && Number(m[1]);
    if (n && byN.has(n)) {
      const ref = document.createElement("button");
      ref.type = "button";
      ref.className = "ref";
      ref.textContent = n;
      ref.title = label(byN.get(n));
      ref.addEventListener("click", () => toggle(n));
      body.appendChild(ref);
    } else if (part) {
      body.appendChild(document.createTextNode(part));
    }
  }

  for (const c of data.citations) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip";
    chip.setAttribute("aria-expanded", "false");
    chip.textContent = `[${c.n}] ${label(c)}`;
    chip.addEventListener("click", () => toggle(c.n));
    chips.set(c.n, chip);
    cites.appendChild(chip);
  }
}

// --- answer feedback (thumbs up / down) -------------------------------------------------

const THUMB_UP = '<path d="M7 10v11H4V10zM7 10l4-7c1.7 0 2.7 1.2 2.4 2.8L12.8 9H19a2 2 0 0 1 2 2.3l-1.2 7.4A2.7 2.7 0 0 1 17.2 21H7"/>';
const THUMB_DOWN = '<path d="M17 14V3h3v11zM17 14l-4 7c-1.7 0-2.7-1.2-2.4-2.8l.6-3.2H5a2 2 0 0 1-2-2.3l1.2-7.4A2.7 2.7 0 0 1 6.8 3H17"/>';

function renderFeedback(node, question, data) {
  const answerId = crypto.randomUUID();
  let rating = 0;

  const bar = document.createElement("div");
  bar.className = "feedback";
  const label = document.createElement("span");
  label.className = "fb-label";
  label.textContent = "Was this helpful?";

  const makeThumb = (value, svg, name) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "thumb";
    b.setAttribute("aria-label", name);
    b.setAttribute("aria-pressed", "false");
    b.title = name;
    b.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true">${svg}</svg>`; // static icon markup only
    b.addEventListener("click", () => vote(rating === value ? 0 : value));
    return b;
  };
  const up = makeThumb(1, THUMB_UP, "Helpful");
  const down = makeThumb(-1, THUMB_DOWN, "Not helpful");
  const status = document.createElement("span");
  status.className = "fb-status";
  status.setAttribute("role", "status");

  // Optional reason, shown after a thumbs down.
  const form = document.createElement("form");
  form.className = "fb-form";
  form.hidden = true;
  const reason = document.createElement("input");
  reason.type = "text";
  reason.maxLength = 1000;
  reason.placeholder = "What was wrong? (optional)";
  reason.setAttribute("aria-label", "What was wrong with this answer?");
  const sendReason = document.createElement("button");
  sendReason.type = "submit";
  sendReason.textContent = "Send";
  form.append(reason, sendReason);

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

  async function vote(value) {
    const previous = rating;
    rating = value;
    up.setAttribute("aria-pressed", String(value === 1));
    down.setAttribute("aria-pressed", String(value === -1));
    form.hidden = value !== -1;
    status.textContent = "";
    try {
      await save(value);
      status.textContent = value === 1 ? "Thanks!" : value === -1 ? "Thanks — tell us what was wrong?" : "";
      if (value === -1) reason.focus();
    } catch (err) {
      rating = previous;
      up.setAttribute("aria-pressed", String(previous === 1));
      down.setAttribute("aria-pressed", String(previous === -1));
      form.hidden = previous !== -1;
      status.textContent = `Couldn't save feedback: ${err.message}`;
    }
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const comment = reason.value.trim();
    if (!comment) return;
    sendReason.disabled = true;
    try {
      await save(-1, comment);
      form.hidden = true;
      status.textContent = "Thanks — that helps improve the answers.";
    } catch (err) {
      status.textContent = `Couldn't save feedback: ${err.message}`;
    } finally {
      sendReason.disabled = false;
    }
  });

  bar.append(label, up, down, status);
  node.append(bar, form);
}

async function ask(message) {
  addMessage("user").querySelector(".body").textContent = message;
  const bot = addMessage("bot pending");
  bot.querySelector(".body").textContent = "Searching the documents…";
  send.disabled = true;

  try {
    const data = await api("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    bot.classList.remove("pending");
    bot.querySelector(".body").textContent = "";
    renderAnswer(bot, data);
    renderFeedback(bot, message, data);
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
  input.style.height = `${input.scrollHeight}px`;
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

function setStatus(text, kind = "") {
  statusEl.textContent = text;
  statusEl.className = `status ${kind}`;
}

function hoursLeft(iso) {
  const h = Math.round((new Date(iso) - Date.now()) / 3.6e6);
  return h >= 1 ? `${h}h left` : "expiring soon";
}

function docItem(d, onRemove) {
  const li = document.createElement("li");
  const name = document.createElement("span");
  name.className = "name";
  name.textContent = d.source;
  name.title = d.source;
  li.appendChild(name);
  if (onRemove) {
    const meta = document.createElement("span");
    meta.className = "meta";
    meta.textContent = `${d.chunks} chunks · ${hoursLeft(d.expires_at)}`;
    const rm = document.createElement("button");
    rm.type = "button";
    rm.className = "remove";
    rm.textContent = "Remove";
    rm.setAttribute("aria-label", `Remove ${d.source}`);
    rm.addEventListener("click", () => onRemove(rm));
    li.append(meta, rm);
  }
  return li;
}

function renderDocs(data) {
  uploadsList.replaceChildren(
    ...(data.uploads.length
      ? data.uploads.map((d) =>
          docItem(d, async (btn) => {
            btn.disabled = true;
            try {
              await api(`/api/documents/${encodeURIComponent(d.source)}`, { method: "DELETE" });
              await loadDocs();
              setStatus(`Removed ${d.source}.`);
            } catch (err) {
              setStatus(err.message, "error");
              btn.disabled = false;
            }
          }),
        )
      : [Object.assign(document.createElement("li"), { className: "muted", textContent: "None yet." })]),
  );
  samplesList.replaceChildren(...data.sample.map((d) => docItem(d)));
  document.getElementById("sample-count").textContent = data.sample.length;
  document.getElementById("docs-count").textContent = data.uploads.length ? `(${data.uploads.length} yours)` : "";

  const { max_mb, max_files, ttl_hours } = data.limits;
  maxBytes = max_mb * 1024 * 1024;
  document.getElementById("limits").textContent = `max ${max_mb} MB each, ${max_files} files`;
  document.getElementById("ttl").textContent = ttl_hours;
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
  drop.classList.add("busy");
  try {
    for (const file of files) {
      if (file.size > maxBytes) {
        setStatus(`${file.name} is larger than ${maxBytes / 1024 / 1024} MB.`, "error");
        continue;
      }
      setStatus(`Uploading and indexing ${file.name}…`, "busy");
      const body = new FormData();
      body.append("file", file);
      try {
        const r = await api("/api/upload", { method: "POST", body });
        setStatus(`Indexed ${r.source} (${r.chunks} chunks). Ask a question about it.`, "ok");
      } catch (err) {
        setStatus(err.message, "error");
      }
    }
  } finally {
    uploading = false;
    drop.classList.remove("busy");
    await loadDocs();
  }
}

docsToggle.addEventListener("click", () => {
  const open = docsPanel.hidden;
  docsPanel.hidden = !open;
  docsToggle.setAttribute("aria-expanded", String(open));
});
document.getElementById("pick").addEventListener("click", () => fileInput.click());
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

loadDocs();
