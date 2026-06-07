/* launcher.js — the search-and-copy core */
(function () {
  "use strict";
  const PR = window.PROMPTOIRE;
  const { el, escapeHtml, highlight, icon, toast, modal, findPlaceholders, fillPlaceholders } = PR.ui;

  let resultsEl, searchEl, debounceTimer;

  function init() {
    resultsEl = document.getElementById("results");
    searchEl = document.getElementById("search");

    searchEl.addEventListener("input", () => {
      PR.state.query = searchEl.value;
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(runSearch, 70);
    });
    searchEl.addEventListener("keydown", onSearchKey);

    document.getElementById("filters").addEventListener("click", (e) => {
      const chip = e.target.closest(".chip");
      if (!chip) return;
      document.querySelectorAll("#filters .chip").forEach((c) => c.classList.remove("is-active"));
      chip.classList.add("is-active");
      PR.state.filter = chip.dataset.filter;
      runSearch();
    });

    resultsEl.addEventListener("mousemove", (e) => {
      const card = e.target.closest(".card");
      if (card && card.dataset.idx != null) setSelected(+card.dataset.idx, false);
    });
  }

  async function runSearch() {
    const { query, filter } = PR.state;
    const favOnly = filter === "favorites";
    const typeFilter = filter === "text" || filter === "image" ? filter : "all";
    const res = await PR.bridge.call("search", query, typeFilter, favOnly, "");
    PR.state.results = (res && res.results) || [];
    PR.state.selected = 0;
    render();
  }

  function render() {
    const { results, query } = PR.state;
    resultsEl.innerHTML = "";
    if (!results.length) {
      resultsEl.appendChild(emptyState(query));
      return;
    }
    const frag = document.createDocumentFragment();
    results.forEach((p, i) => frag.appendChild(card(p, i, query)));
    resultsEl.appendChild(frag);
    scrollSelectedIntoView();
  }

  function emptyState(query) {
    if (query) {
      return el("div", { class: "empty" }, [
        el("div", { class: "emoji", text: "🔍" }),
        el("h3", { text: "No matches" }),
        el("p", { html: `Nothing for “${escapeHtml(query)}”. Try a different word, or <b>create it</b>.` }),
        el("button", { class: "btn btn-primary btn-sm", text: "New prompt", onclick: () => PR.editor.newPrompt(null, { title: query }) }),
      ]);
    }
    return el("div", { class: "empty" }, [
      el("div", { class: "emoji", text: "✨" }),
      el("h3", { text: "Your prompt library is empty" }),
      el("p", { html: "Add your first prompt, or use <b>Improve&nbsp;library</b> to seed it with AI." }),
      el("button", { class: "btn btn-primary btn-sm", text: "New prompt", onclick: () => PR.editor.newPrompt(null) }),
    ]);
  }

  function card(p, i, query) {
    const accent = p.category_color || "";
    const glyph = p.type === "image" ? "▦" : "✎";
    const tags = (p.tags || []).slice(0, 3).map((t) => el("span", { class: "tag", text: t }));

    const node = el("button", {
      class: "card", dataset: { idx: i, id: p.id },
      style: accent ? { "--card-accent": accent } : {},
    }, [
      el("div", { class: "card-top" }, [
        el("span", { class: "type-glyph " + (p.type === "image" ? "image" : ""), text: glyph }),
        el("span", { class: "card-title", html: highlight(p.title || "Untitled", query) }),
      ]),
      p.prompt ? el("div", { class: "card-preview", html: highlight(p.prompt, query) }) : null,
      el("div", { class: "card-meta" }, [
        p.category_name ? el("span", { class: "cat-chip", text: p.category_name }) : null,
        ...tags,
      ]),
      cardActions(p),
      el("div", { class: "copied-cue", text: "Copied ✓" }),
    ]);

    node.addEventListener("click", (e) => {
      if (e.target.closest(".card-actions")) return;
      copy(p, node);
    });
    return node;
  }

  function cardActions(p) {
    const fav = el("button", { class: "iconbtn fav " + (p.favorite ? "on" : ""), title: "Favorite",
      html: icon("star") });
    fav.addEventListener("click", async (e) => {
      e.stopPropagation();
      const r = await PR.bridge.call("toggle_favorite", p.id);
      if (r && r.ok) { p.favorite = r.favorite; fav.classList.toggle("on", r.favorite);
        const local = PR.findPrompt(p.id); if (local) local.p.favorite = r.favorite; }
    });
    const edit = el("button", { class: "iconbtn", title: "Edit", html: icon("edit") });
    edit.addEventListener("click", (e) => { e.stopPropagation(); PR.editor.editPrompt(p.id); });
    return el("div", { class: "card-actions" }, [fav, edit]);
  }

  /* ---- copy (with placeholder fill) ------------------------------------- */
  async function copy(p, node) {
    const placeholders = findPlaceholders(p.prompt || "");
    if (placeholders.length) {
      openFillModal(p, placeholders);
      return;
    }
    await doCopy(p.id, p.prompt, node, p.title);
  }

  async function doCopy(id, text, node, title) {
    const r = await PR.bridge.call("copy_prompt", id, text);
    if (r && r.ok) {
      if (node) { node.classList.add("flash"); setTimeout(() => node && node.classList.remove("flash"), 520); }
      toast("Copied “" + (title || "prompt") + "”");
      if (r.spring && !PR.state.pinned && PR.app) {
        // window hides itself Python-side; nothing else to do
      }
    } else {
      toast((r && r.error) || "Copy failed", { bad: true });
    }
  }

  function openFillModal(p, names) {
    PR.state.suppressBlur = true;
    const values = {};
    const inputs = {};
    const preview = el("div", { class: "ph-preview" });
    function refresh() {
      let html = escapeHtml(p.prompt);
      names.forEach((n) => {
        const v = values[n.toLowerCase()];
        const re = new RegExp("\\{\\{?\\s*" + n.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\s*\\}?\\}", "g");
        html = html.replace(re, v ? `<mark>${escapeHtml(v)}</mark>` : `<mark>{${escapeHtml(n)}}</mark>`);
      });
      preview.innerHTML = html;
    }
    const rows = names.map((n) => {
      const inp = el("input", { class: "input", placeholder: "value for " + n });
      inp.addEventListener("input", () => { values[n.toLowerCase()] = inp.value; refresh(); });
      inputs[n] = inp;
      return el("div", { class: "ph-row" }, [el("label", { text: n }), inp]);
    });
    refresh();
    const body = el("div", {}, [...rows,
      el("label", { class: "txt-muted", style: { fontSize: "11px", margin: "8px 0 5px", display: "block" }, text: "Preview" }),
      preview]);

    const copyBtn = el("button", { class: "btn btn-primary", text: "Fill & copy" });
    const closeBtn = el("button", { class: "btn btn-ghost", text: "Cancel", onclick: () => { PR.ui.closeModal(); PR.state.suppressBlur = false; } });
    const m = modal({ title: "Fill in placeholders", body, footer: [closeBtn, copyBtn],
      onClose: () => { PR.state.suppressBlur = false; } });
    copyBtn.addEventListener("click", async () => {
      const text = fillPlaceholders(p.prompt, values);
      m.close();
      await doCopy(p.id, text, null, p.title);
    });
    setTimeout(() => inputs[names[0]] && inputs[names[0]].focus(), 50);
  }

  /* ---- keyboard nav ----------------------------------------------------- */
  function onSearchKey(e) {
    const n = PR.state.results.length;
    if (e.key === "ArrowDown") { e.preventDefault(); setSelected(Math.min(PR.state.selected + 1, n - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setSelected(Math.max(PR.state.selected - 1, 0)); }
    else if (e.key === "Enter") {
      e.preventDefault();
      const p = PR.state.results[PR.state.selected];
      if (p) { const node = resultsEl.querySelector(`.card[data-idx="${PR.state.selected}"]`); copy(p, node); }
    } else if (e.key === "Tab") {
      // cycle filters with Tab
      e.preventDefault();
      const chips = [...document.querySelectorAll("#filters .chip")];
      const cur = chips.findIndex((c) => c.classList.contains("is-active"));
      const next = chips[(cur + (e.shiftKey ? -1 + chips.length : 1)) % chips.length];
      next.click();
    }
  }

  function setSelected(i, scroll = true) {
    PR.state.selected = i;
    resultsEl.querySelectorAll(".card").forEach((c) => c.classList.toggle("sel", +c.dataset.idx === i));
    if (scroll) scrollSelectedIntoView();
  }
  function scrollSelectedIntoView() {
    const cur = resultsEl.querySelector(`.card[data-idx="${PR.state.selected}"]`);
    if (cur) {
      cur.classList.add("sel");
      cur.scrollIntoView({ block: "nearest" });
    }
  }

  function focusSearch() { if (searchEl) { searchEl.focus(); searchEl.select(); } }

  PR.launcher = { init, runSearch, render, focusSearch };
})();
