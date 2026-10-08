// Minimal, safe Markdown → DOM renderer for answers. Supports paragraphs, line breaks, headings,
// bulleted and numbered lists (one nested level), **bold**, *italic*, `code`, and [n] citations.
// Everything is built with createElement/text nodes (never innerHTML), so model output can't inject markup.

const INLINE = /(\*\*[^*\n]+?\*\*|__[^_\n]+?__|`[^`\n]+`|\[\d+\]|(?<![\w*])\*(?!\s)[^*\n]+?\*(?!\w)|(?<![\w_])_(?!\s)[^_\n]+?_(?!\w))/g;

function renderInline(text, cite) {
  const frag = document.createDocumentFragment();
  let last = 0;
  for (const m of text.matchAll(INLINE)) {
    if (m.index > last) frag.append(text.slice(last, m.index));
    const tok = m[0];
    if (tok.startsWith("**") || tok.startsWith("__")) {
      const el = document.createElement("strong");
      el.append(renderInline(tok.slice(2, -2), cite));
      frag.append(el);
    } else if (tok.startsWith("`")) {
      const el = document.createElement("code");
      el.textContent = tok.slice(1, -1);
      frag.append(el);
    } else if (tok.startsWith("[")) {
      const ref = cite ? cite(Number(tok.slice(1, -1))) : null;
      frag.append(ref || tok);
    } else {
      const el = document.createElement("em");
      el.append(renderInline(tok.slice(1, -1), cite));
      frag.append(el);
    }
    last = m.index + tok.length;
  }
  if (last < text.length) frag.append(text.slice(last));
  return frag;
}

function renderMarkdown(text, cite) {
  const root = document.createDocumentFragment();
  let para = null; // current <p>
  let list = null; // { el, ordered }
  let sub = null; // nested list inside the last <li>

  const closePara = () => { para = null; };
  const closeLists = () => { list = null; sub = null; };

  for (const raw of text.replace(/\r\n?/g, "\n").split("\n")) {
    const line = raw.replace(/\s+$/, "");
    if (!line.trim()) {
      closePara();
      sub = null;
      continue;
    }
    const indent = line.match(/^\s*/)[0].length;
    const heading = line.match(/^\s*(#{1,4})\s+(.*)$/);
    const bullet = line.match(/^\s*[-*•]\s+(.*)$/);
    const numbered = line.match(/^\s*(\d+)[.)]\s+(.*)$/);

    if (heading) {
      closePara();
      closeLists();
      const h = document.createElement("p");
      h.className = `md-h md-h${heading[1].length}`;
      h.append(renderInline(heading[2].replace(/[#\s]+$/, ""), cite));
      root.append(h);
    } else if (bullet || numbered) {
      closePara();
      const ordered = Boolean(numbered);
      const content = ordered ? numbered[2] : bullet[1];
      const li = document.createElement("li");
      li.append(renderInline(content, cite));
      if (indent >= 2 && list) {
        // Nested item under the previous top-level item.
        const parentLi = list.el.lastElementChild;
        if (!sub || sub.ordered !== ordered) {
          sub = { el: document.createElement(ordered ? "ol" : "ul"), ordered };
          parentLi.append(sub.el);
        }
        sub.el.append(li);
      } else {
        if (!list || list.ordered !== ordered) {
          list = { el: document.createElement(ordered ? "ol" : "ul"), ordered };
          if (ordered && numbered[1] !== "1") list.el.start = Number(numbered[1]);
          root.append(list.el);
        }
        sub = null;
        list.el.append(li);
      }
    } else if (list && indent >= 2 && list.el.lastElementChild) {
      // Continuation line of a list item.
      list.el.lastElementChild.append(" ", renderInline(line.trim(), cite));
    } else {
      closeLists();
      if (!para) {
        para = document.createElement("p");
        root.append(para);
      } else {
        para.append(document.createElement("br"));
      }
      para.append(renderInline(line.trim(), cite));
    }
  }
  return root;
}
