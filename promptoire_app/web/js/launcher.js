/* launcher.js — the search-and-copy core.

   Two modes:
     browse (empty query)  — the full prompt tree, grouped by category with
                             collapsible color-coded headers and a category rail
     search (typed query)  — flat ranked hits with a breadcrumb on each card
*/
(function () {
  "use strict";
  const PR = window.PROMPTOIRE;
  const { el, escapeHtml, highlight, icon, toast, modal, findPlaceholders, fillPlaceholders } = PR.ui;

  const COLLAPSE_KEY = "promptoire.launcher.collapsed";

  let resultsEl, searchEl, railEl, debounceTimer, staggerNext = true;
  let railDrag = null, suppressRailClick = false;
  let collapsed = loadCollapsed();

  function loadCollapsed() {
    try { return new Set(JSON.parse(localStorage.getItem(COLLAPSE_KEY) || "[]")); }
    catch (e) { return new Set(); }
  }
  function saveCollapsed() {
    try { localStorage.setItem(COLLAPSE_KEY, JSON.stringify([...collapsed])); }
    catch (e) { /* private mode etc. — collapse state just won't persist */ }
  }

  function init() {
    resultsEl = document.getElementById("results");
    searchEl = document.getElementById("search");
    railEl = document.getElementById("catrail");

    searchEl.addEventListener("input", () => {
      PR.state.query = searchEl.value;
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => runSearch(false), 70); // typing: no re-stagger
    });
    searchEl.addEventListener("keydown", onSearchKey);
    wireRailDrag();

    document.getElementById("filters").addEventListener("click", (e) => {
      const chip = e.target.closest(".chip");
      if (!chip) return;
      setFilter(chip.dataset.filter);
    });

    railEl.addEventListener("click", (e) => {
      if (suppressRailClick) {
        e.preventDefault();
        e.stopPropagation();
        suppressRailClick = false;
        return;
      }
      const chip = e.target.closest(".railchip");
      if (!chip) return;
      const id = chip.dataset.id;
      PR.state.catFilter = PR.state.catFilter === id ? null : id;
      runSearch();
      focusSearch();
    });

    resultsEl.addEventListener("mousemove", (e) => {
      const card = e.target.closest(".card");
      if (card && card.dataset.idx != null) setSelected(+card.dataset.idx, false);
    });

    // Clicking a tag chip searches for that tag.
    resultsEl.addEventListener("click", (e) => {
      const tag = e.target.closest(".tag");
      if (!tag) return;
      e.stopPropagation();
      searchEl.value = PR.state.query = "#" + tag.dataset.tag;
      runSearch();
      focusSearch();
    });
  }

  function wireRailDrag() {
    railEl.addEventListener("pointerdown", (e) => {
      if (e.button !== 0) return;
      railDrag = {
        pointerId: e.pointerId,
        startX: e.clientX,
        startScroll: railEl.scrollLeft,
        moved: false,
      };
      try { railEl.setPointerCapture(e.pointerId); } catch (err) {}
    });
    railEl.addEventListener("pointermove", (e) => {
      if (!railDrag || railDrag.pointerId !== e.pointerId) return;
      const dx = e.clientX - railDrag.startX;
      if (!railDrag.moved && Math.abs(dx) < 4) return;
      railDrag.moved = true;
      railEl.classList.add("is-dragging");
      railEl.scrollLeft = railDrag.startScroll - dx;
      e.preventDefault();
    });
    const finish = (e) => {
      if (!railDrag || railDrag.pointerId !== e.pointerId) return;
      if (railDrag.moved) {
        suppressRailClick = true;
        setTimeout(() => { suppressRailClick = false; }, 150);
      }
      try { railEl.releasePointerCapture(e.pointerId); } catch (err) {}
      railEl.classList.remove("is-dragging");
      railDrag = null;
    };
    railEl.addEventListener("pointerup", finish);
    railEl.addEventListener("pointercancel", finish);
    railEl.addEventListener("wheel", (e) => {
      if (railEl.scrollWidth <= railEl.clientWidth) return;
      if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
        railEl.scrollLeft += e.deltaY;
        e.preventDefault();
      }
    }, { passive: false });
  }

  function setFilter(f) {
    PR.state.filter = f;
    document.querySelectorAll("#filters .chip").forEach((c) =>
      c.classList.toggle("is-active", c.dataset.filter === f));
    runSearch();
  }

  /* ---- category helpers --------------------------------------------------- */

  function passesFilter(p) {
    const f = PR.state.filter;
    if (f === "text" || f === "image") return (p.type || "text") === f;
    if (f === "favorites") return !!p.favorite;
    return true;
  }

  // ids of a category and all its descendants (for search-mode cat filtering)
  function subtreeIds(cat) {
    const ids = new Set([cat.id]);
    (function walk(c) {
      (c.subcategories || []).forEach((s) => { ids.add(s.id); walk(s); });
    })(cat);
    return ids;
  }

  function findTopCat(id) {
    return (PR.state.categories || []).find((c) => c.id === id) || null;
  }

  /* ---- search / render dispatch ------------------------------------------- */

  async function runSearch(fresh = true) {
    staggerNext = fresh;
    const { query, filter } = PR.state;
    renderRail();
    if (!query.trim()) {
      renderBrowse();
      return;
    }
    const favOnly = filter === "favorites";
    const typeFilter = filter === "text" || filter === "image" ? filter : "all";
    const res = await PR.bridge.call("search", query, typeFilter, favOnly, "");
    let hits = (res && res.results) || [];
    if (PR.state.catFilter) {
      const top = findTopCat(PR.state.catFilter);
      if (top) {
        const ids = subtreeIds(top);
        hits = hits.filter((h) => ids.has(h.category_id));
      }
    }
    PR.state.results = hits;
    PR.state.selected = 0;
    renderFlat();
  }

  /* ---- category rail -------------------------------------------------------- */

  function renderRail() {
    const cats = PR.state.categories || [];
    railEl.innerHTML = "";
    railEl.classList.toggle("hidden", cats.length < 2);
    if (cats.length < 2) return;
    cats.forEach((c) => {
      const n = countTree(c);
      const chip = el("button", {
        class: "railchip" + (PR.state.catFilter === c.id ? " is-active" : ""),
        dataset: { id: c.id },
        style: c.color ? { "--rail-accent": c.color } : {},
        title: c.name + " — " + n + " prompt" + (n === 1 ? "" : "s"),
      }, [
        c.icon ? el("span", { class: "railicon", text: c.icon }) : null,
        el("span", { class: "railname", text: c.name }),
        el("span", { class: "railcount", text: n }),
      ]);
      railEl.appendChild(chip);
    });
  }

  function countTree(cat) {
    let n = (cat.prompts || []).filter(passesFilter).length;
    (cat.subcategories || []).forEach((s) => (n += countTree(s)));
    return n;
  }

  /* ---- browse mode: the grouped prompt tree --------------------------------- */

  function renderBrowse() {
    const cats = (PR.state.categories || []).filter(
      (c) => !PR.state.catFilter || c.id === PR.state.catFilter
    );
    resultsEl.classList.toggle("stagger", staggerNext);
    resultsEl.innerHTML = "";

    const flat = [];   // visible cards in render order -> PR.state.results
    const frag = document.createDocumentFragment();
    const forceOpen = !!PR.state.catFilter;

    cats.forEach((c) => {
      const g = groupNode(c, "", 0, flat, forceOpen);
      if (g) frag.appendChild(g);
    });

    PR.state.results = flat;
    PR.state.selected = 0;

    if (!flat.length && !frag.childNodes.length) {
      resultsEl.appendChild(emptyState(""));
      return;
    }
    resultsEl.appendChild(frag);
    scrollSelectedIntoView();
  }

  function groupNode(cat, inheritedColor, depth, flat, forceOpen) {
    const color = cat.color || inheritedColor;
    const own = (cat.prompts || []).filter(passesFilter);
    const kids = (cat.subcategories || [])
      .map((s) => groupNode(s, color, depth + 1, flat, forceOpen))
      .filter(Boolean);
    const total = countTree(cat);
    if (!own.length && !kids.length) return null; // nothing visible under filter

    const isCollapsed = !forceOpen && collapsed.has(cat.id);
    const group = el("section", {
      class: "group" + (isCollapsed ? " collapsed" : "") + (depth ? " nested" : ""),
      style: color ? { "--group-accent": color } : {},
    });

    const head = el("button", { class: "group-head", "aria-expanded": String(!isCollapsed) }, [
      el("span", { class: "group-caret", html: icon("caret") }),
      cat.icon ? el("span", { class: "group-icon", text: cat.icon }) : el("span", { class: "group-dot" }),
      el("span", { class: "group-name", text: cat.name }),
      el("span", { class: "group-count", text: total }),
    ]);
    head.addEventListener("click", () => {
      if (collapsed.has(cat.id)) collapsed.delete(cat.id);
      else collapsed.add(cat.id);
      saveCollapsed();
      renderBrowse();
      focusSearch();
    });
    group.appendChild(head);

    const body = el("div", { class: "group-body" });
    if (!isCollapsed) {
      own.forEach((p) => {
        const hit = browseHit(p, cat, color);
        const idx = flat.length;
        flat.push(hit);
        body.appendChild(card(hit, idx, "", { hideCat: true }));
      });
      kids.forEach((k) => body.appendChild(k));
      group.appendChild(body);
    }
    return group;
  }

  // Shape a raw library prompt like a search hit so card() can render either.
  function browseHit(p, cat, effColor) {
    return Object.assign({}, p, {
      category_id: cat.id,
      category_name: cat.name,
      category_color: effColor || cat.color || "",
      category_icon: cat.icon || "",
    });
  }

  /* ---- search mode: flat ranked list ---------------------------------------- */

  function renderFlat() {
    const { results, query } = PR.state;
    resultsEl.classList.toggle("stagger", staggerNext);
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
    if (PR.state.filter === "favorites" && !query) {
      return el("div", { class: "empty" }, [
        el("div", { class: "emoji", text: "★" }),
        el("h3", { text: "No favorites yet" }),
        el("p", { html: "Hover any prompt and hit the <b>star</b> — favorites float to the top of search." }),
      ]);
    }
    if (PR.state.catFilter && !query) {
      const top = findTopCat(PR.state.catFilter);
      const name = top ? top.name : "this category";
      return el("div", { class: "empty" }, [
        el("div", { class: "emoji", text: (top && top.icon) || "📁" }),
        el("h3", { text: "Nothing in " + name + " yet" }),
        el("p", { html: "Add the first prompt — it'll live right here." }),
        el("button", { class: "btn btn-primary btn-sm", text: "New prompt",
          onclick: () => PR.editor.newPrompt(PR.state.catFilter) }),
      ]);
    }
    if (query) {
      return el("div", { class: "empty" }, [
        el("div", { class: "emoji", text: "🔍" }),
        el("h3", { text: "No matches" }),
        el("p", { html: `Nothing for “${escapeHtml(query)}”. Try a different word, or <b>create it</b>.` }),
        el("button", { class: "btn btn-primary btn-sm", text: "New prompt", onclick: () => PR.editor.newPrompt(null, { title: query.replace(/#\S+\s*/g, "").trim() }) }),
      ]);
    }
    return el("div", { class: "empty" }, [
      el("div", { class: "emoji", text: "✨" }),
      el("h3", { text: "Your prompt library is empty" }),
      el("p", { html: "Add one prompt, or import an outline from an LLM." }),
      el("div", { class: "empty-actions" }, [
        el("button", { class: "btn btn-primary btn-sm", text: "New prompt", onclick: () => PR.editor.newPrompt(null) }),
        el("button", { class: "btn btn-sm", html: icon("copy") + " Import prompts", onclick: () => PR.app.showView("bulk") }),
      ]),
    ]);
  }

  /* ---- cards ----------------------------------------------------------------- */

  function card(p, i, query, opts) {
    opts = opts || {};
    const accent = p.category_color || "";
    const glyph = p.type === "image" ? "▦" : "✎";
    const tags = (p.tags || []).slice(0, 3).map((t) =>
      el("button", { class: "tag", text: t, dataset: { tag: t }, title: "Filter by #" + t }));

    const crumb = !opts.hideCat && (p.path && p.path.length > 1)
      ? p.path.join(" › ")
      : (!opts.hideCat ? p.category_name : "");

    const node = el("button", {
      class: "card " + (opts.hideCat ? "browse-card" : "search-card"), dataset: { idx: i, id: p.id },
      style: accent ? { "--card-accent": accent } : {},
    }, [
      el("div", { class: "card-top" }, [
        el("span", { class: "type-glyph " + (p.type === "image" ? "image" : ""), text: glyph }),
        el("span", { class: "card-title", html: highlight(p.title || "Untitled", query) }),
        p.favorite ? el("span", { class: "card-fav", html: icon("star") }) : null,
      ]),
      p.prompt ? el("div", { class: "card-preview", html: highlight(preview(p.prompt, query), query) }) : null,
      (crumb || tags.length) ? el("div", { class: "card-meta" }, [
        crumb ? el("span", { class: "cat-chip", text: (p.category_icon ? p.category_icon + " " : "") + crumb }) : null,
        ...tags,
      ]) : null,
      cardActions(p),
      el("div", { class: "copied-cue", text: "Copied ✓" }),
    ]);

    node.addEventListener("click", (e) => {
      if (e.target.closest(".card-actions") || e.target.closest(".tag")) return;
      copy(p, node);
    });
    return node;
  }

  // Trim very long bodies to a window around the first match (keeps the
  // 2-line clamp showing something relevant instead of always the opening).
  function preview(text, query) {
    const MAX = 220;
    if (text.length <= MAX) return text;
    const q = (query || "").replace(/#\S+/g, "").trim();
    let at = 0;
    if (q) {
      const hit = text.toLowerCase().indexOf(q.split(/\s+/)[0].toLowerCase());
      if (hit > 60) at = Math.max(0, hit - 40);
    }
    const slice = text.slice(at, at + MAX);
    return (at ? "…" : "") + slice + (at + MAX < text.length ? "…" : "");
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
    else if (e.key === "PageDown") { e.preventDefault(); setSelected(Math.min(PR.state.selected + 5, n - 1)); }
    else if (e.key === "PageUp") { e.preventDefault(); setSelected(Math.max(PR.state.selected - 5, 0)); }
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

  PR.launcher = { init, runSearch, render: renderFlat, focusSearch, setFilter };
})();
