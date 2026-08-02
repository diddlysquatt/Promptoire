/* components.js — DOM helpers, toasts, modals, and shared bits of UI */
(function () {
  "use strict";
  const PR = (window.PROMPTOIRE = window.PROMPTOIRE || {});

  /* el(tag, props, children) — tiny hyperscript */
  function el(tag, props, children) {
    const node = document.createElement(tag);
    if (props) {
      for (const k in props) {
        const v = props[k];
        if (k === "class") node.className = v;
        else if (k === "html") node.innerHTML = v;
        else if (k === "text") node.textContent = v;
        else if (k === "style" && typeof v === "object") {
          for (const sk in v) {
            // Custom properties (--foo) must go through setProperty.
            if (sk.startsWith("--")) node.style.setProperty(sk, v[sk]);
            else node.style[sk] = v[sk];
          }
        }
        else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
        else if (k === "dataset") Object.assign(node.dataset, v);
        else if (v !== null && v !== undefined && v !== false) node.setAttribute(k, v);
      }
    }
    if (children != null) {
      (Array.isArray(children) ? children : [children]).forEach((c) => {
        if (c == null || c === false) return;
        node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
      });
    }
    return node;
  }
  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => [...(root || document).querySelectorAll(sel)];

  function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  // highlight each query term (case-insensitive); #tag terms are skipped
  function highlight(text, q) {
    text = escapeHtml(text);
    if (!q) return text;
    const terms = q.split(/\s+/)
      .filter((t) => t && !t.startsWith("#"))
      .map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
    if (!terms.length) return text;
    try {
      const re = new RegExp("(" + terms.join("|") + ")", "ig");
      return text.replace(re, "<mark>$1</mark>");
    } catch (e) { return text; }
  }

  /* SVG icon set (stroke-based, inherit currentColor) */
  const ICONS = {
    copy: '<path d="M9 9h10v10H9zM5 15V5h10"/>',
    star: '<path d="M12 3l2.5 6 6.5.5-5 4.2 1.6 6.3L12 17l-5.6 3 1.6-6.3-5-4.2 6.5-.5z"/>',
    edit: '<path d="M4 20h4l10-10-4-4L4 16zM14 6l4 4"/>',
    trash: '<path d="M5 7h14M9 7V5h6v2M7 7l1 13h8l1-13"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    grip: '<circle cx="9" cy="6" r="1.2"/><circle cx="15" cy="6" r="1.2"/><circle cx="9" cy="12" r="1.2"/><circle cx="15" cy="12" r="1.2"/><circle cx="9" cy="18" r="1.2"/><circle cx="15" cy="18" r="1.2"/>',
    caret: '<path d="M9 6l6 6-6 6"/>',
    check: '<path d="M5 13l4 4L19 7"/>',
    "folder-plus": '<path d="M3 7V5h6l2 2h10v12H3V7zM12 11v6M9 14h6"/>',
    expand: '<path d="M8 4l4 4 4-4M8 20l4-4 4 4"/>',
    collapse: '<path d="M8 8l4-4 4 4M8 16l4 4 4-4"/>',
  };
  function icon(name, cls) {
    return `<svg viewBox="0 0 24 24" class="ic ${cls || ""}">${ICONS[name] || ""}</svg>`;
  }

  /* ---- toasts ----------------------------------------------------------- */
  function toast(message, opts) {
    opts = opts || {};
    const host = document.getElementById("toastHost");
    const t = el("div", { class: "toast" + (opts.bad ? " bad" : ""), role: "status" }, [
      el("span", { class: "dot" }),
      el("span", { text: message }),
    ]);
    if (opts.undo) {
      const u = el("button", { class: "undo", text: "Undo", type: "button" });
      u.addEventListener("click", async () => {
        u.disabled = true;
        try {
          if (await opts.undo() === false) { u.disabled = false; return; }
          dismiss();
        } catch (e) {
          u.disabled = false;
          toast("Could not restore that prompt", { bad: true });
        }
      });
      t.appendChild(u);
    }
    host.appendChild(t);
    let timer;
    function dismiss() {
      clearTimeout(timer);
      t.classList.add("out");
      setTimeout(() => t.remove(), 220);
    }
    timer = setTimeout(dismiss, opts.duration || (opts.undo ? 12000 : 2200));
    return dismiss;
  }

  /* ---- modal ------------------------------------------------------------ */
  function modal({ title, body, footer, onClose, wide }) {
    const host = document.getElementById("modalHost");
    host.innerHTML = "";
    const sheet = el("div", { class: "modal" });
    if (wide) sheet.style.width = "min(520px, 94vw)";
    const head = el("div", { class: "modal-head" }, [
      el("h3", { text: title || "" }),
      el("button", { class: "tbtn", html: '<svg viewBox="0 0 24 24" class="ic"><path d="M6 6l12 12M18 6L6 18"/></svg>', onclick: close }),
    ]);
    const bodyEl = el("div", { class: "modal-body" });
    if (typeof body === "string") bodyEl.innerHTML = body; else if (body) bodyEl.appendChild(body);
    sheet.appendChild(head);
    sheet.appendChild(bodyEl);
    if (footer) {
      const foot = el("div", { class: "modal-foot" });
      footer.forEach((f) => foot.appendChild(f));
      sheet.appendChild(foot);
    }
    host.appendChild(sheet);
    host.classList.remove("hidden");
    function backdrop(e) { if (e.target === host) close(); }
    host.addEventListener("mousedown", backdrop);
    function close() {
      host.classList.add("hidden");
      host.innerHTML = "";
      host.removeEventListener("mousedown", backdrop);
      if (onClose) onClose();
    }
    PR._closeModal = close;
    return { close, bodyEl, sheet };
  }
  function closeModal() { if (PR._closeModal) PR._closeModal(); }

  function confirmDialog({ title, message, confirmText, danger, onConfirm }) {
    const ok = el("button", { class: "btn " + (danger ? "btn-danger" : "btn-primary"), text: confirmText || "Confirm",
      onclick: () => { closeModal(); onConfirm && onConfirm(); } });
    const cancel = el("button", { class: "btn btn-ghost", text: "Cancel", onclick: closeModal });
    return modal({ title, body: el("p", { class: "txt-muted", style:{fontSize:"13px",lineHeight:"1.55"}, text: message }), footer: [cancel, ok] });
  }

  /* ---- placeholder helpers ---------------------------------------------- */
  // find {placeholders}; ignore {{...}} doubled? We accept {name} and {{name}}.
  function findPlaceholders(text) {
    const set = [];
    const seen = new Set();
    const re = /\{\{?\s*([a-zA-Z0-9_\- ]+?)\s*\}?\}/g;
    let m;
    while ((m = re.exec(text))) {
      const name = m[1].trim();
      if (name && !seen.has(name.toLowerCase())) { seen.add(name.toLowerCase()); set.push(name); }
    }
    return set;
  }
  function fillPlaceholders(text, values) {
    return text.replace(/\{\{?\s*([a-zA-Z0-9_\- ]+?)\s*\}?\}/g, (full, name) => {
      const v = values[name.trim().toLowerCase()];
      return v != null && v !== "" ? v : full;
    });
  }

  PR.ui = { el, $, $$, escapeHtml, highlight, icon, toast, modal, closeModal, confirmDialog,
            findPlaceholders, fillPlaceholders };
})();
