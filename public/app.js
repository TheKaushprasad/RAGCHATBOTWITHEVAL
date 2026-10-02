const log = document.getElementById("log");
const form = document.getElementById("form");
const input = document.getElementById("input");
const send = document.getElementById("send");
const tpl = document.getElementById("msg-tpl");

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
  return `${c.source} · ${where}`;
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
  const parts = data.answer.split(/(\[\d+\])/g);
  for (const part of parts) {
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

async function ask(message) {
  addMessage("user").querySelector(".body").textContent = message;
  const bot = addMessage("bot pending");
  bot.querySelector(".body").textContent = "Searching the documents…";
  send.disabled = true;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : `Request failed (${res.status})`);
    bot.classList.remove("pending");
    bot.querySelector(".body").textContent = "";
    renderAnswer(bot, data);
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
