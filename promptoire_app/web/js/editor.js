/* editor.js — manage the library tree: categories, subcategories, prompts.

   Drag & drop:
     · prompt rows reorder within their category, or drop onto another
       category's header to move them there
     · category groups reorder among their siblings (drag the header)
   All drag handlers stop propagation so nested lists never double-handle.
*/
(function () {
  "use strict";
  const PR = window.PROMPTOIRE;
  const { el, icon, toast, modal, confirmDialog, escapeHtml } = PR.ui;

  let filterText = "";
  // One in-flight drag at a time; dataTransfer payloads are unreadable during
  // dragover in WebView2, so we track the payload here.
  let drag = null; // { kind: "prompt"|"category", id, fromCatId }

  /* ---- render ------------------------------------------------------------ */

  function render() {
    const host = document.getElementById("editorBody");
    host.innerHTML = "";
    const cats = PR.state.categories;

    host.appendChild(toolbar());

    if (!cats.length) {
      host.appendChild(el("div", { class: "empty" }, [
        el("div", { class: "emoji", text: "📁" }),
        el("h3", { text: "No categories yet" }),
        el("button", { class: "btn btn-primary btn-sm", text: "+ Add category", onclick: () => addCategory(null) }),
      ]));
      return;
    }

    const tree = el("div", { class: "cat-tree" });
    cats.forEach((c) => {
      const g = catGroup(c, null);
      if (g) tree.appendChild(g);
    });
    if (!tree.childNodes.length && filterText) {
      tree.appendChild(el("div", { class: "empty" }, [
        el("div", { class: "emoji", text: "🔍" }),
        el("h3", { text: "No matches in the library" }),
        el("p", { text: "Try a different filter." }),
      ]));
    }
    host.appendChild(tree);
    enableCategoryDrag(tree, null);
  }

  function toolbar() {
    const input = el("input", {
      class: "input editor-filter", placeholder: "Filter prompts & categories…",
      value: filterText, type: "search", spellcheck: "false",
    });
    let t;
    input.addEventListener("input", () => {
      clearTimeout(t);
      t = setTimeout(() => { filterText = input.value.trim().toLowerCase(); rerenderKeepFilter(); }, 90);
    });

    const expand = el("button", { class: "iconbtn", title: "Expand all", html: icon("expand"),
      onclick: () => setAllCollapsed(false) });
    const collapse = el("button", { class: "iconbtn", title: "Collapse all", html: icon("collapse"),
      onclick: () => setAllCollapsed(true) });

    return el("div", { class: "editor-toolbar" }, [input, expand, collapse]);
  }

  function rerenderKeepFilter() {
    const host = document.getElementById("editorBody");
    const had = host.querySelector(".editor-filter");
    const pos = had ? had.selectionStart : null;
    render();
    const inp = host.querySelector(".editor-filter");
    if (inp) { inp.focus(); if (pos != null) inp.setSelectionRange(pos, pos); }
  }

  async function setAllCollapsed(v) {
    const ops = [];
    (function walk(cats) {
      cats.forEach((c) => { c.collapsed = v; ops.push(PR.bridge.call("update_category", c.id, { collapsed: v })); walk(c.subcategories || []); });
    })(PR.state.categories);
    render();
    await Promise.all(ops);
  }

  function matches(p) {
    if (!filterText) return true;
    const hay = (p.title + " " + (p.tags || []).join(" ")).toLowerCase();
    return hay.includes(filterText);
  }
  function catMatches(cat) {
    return cat.name.toLowerCase().includes(filterText);
  }

  function catGroup(cat, parent) {
    const ownAll = cat.prompts || [];
    const own = filterText && !catMatches(cat) ? ownAll.filter(matches) : ownAll;
    const subs = (cat.subcategories || [])
      .map((sc) => catGroup(sc, cat))
      .filter(Boolean);
    // While filtering, hide categories with nothing to show.
    if (filterText && !own.length && !subs.length && !catMatches(cat)) return null;

    const collapsed = filterText ? false : !!cat.collapsed; // filter forces open
    const group = el("div", {
      class: "cat-group" + (collapsed ? " collapsed" : ""),
      dataset: { id: cat.id },
    });
    const accent = cat.color || "";
    const total = countTree(cat);

    const header = el("div", {
      class: "cat-header", draggable: "true",
      style: accent ? { "--cat-accent": accent } : {},
    }, [
      el("span", { class: "cat-caret", html: icon("caret") }),
      cat.icon ? el("span", { class: "cat-icon", text: cat.icon }) : el("span", { class: "cat-dot" }),
      el("span", { class: "cat-name", text: cat.name }),
      el("span", { class: "cat-count", text: total }),
      el("div", { class: "cat-actions" }, [
        iconBtn("plus", "Add prompt here", (e) => { e.stopPropagation(); newPrompt(cat.id); }),
        iconBtn("folder-plus", "Add subcategory", (e) => { e.stopPropagation(); addCategory(cat.id); }),
        iconBtn("edit", "Rename / icon / color", (e) => { e.stopPropagation(); editCategory(cat); }),
        iconBtn("trash", "Delete category", (e) => { e.stopPropagation(); deleteCategory(cat); }),
      ]),
    ]);
    header.addEventListener("click", () => toggleCollapse(cat, group));
    // Dropping a prompt on a header moves it into that category.
    header.addEventListener("dragover", (e) => {
      if (drag && drag.kind === "prompt" && drag.fromCatId !== cat.id) {
        e.preventDefault(); e.stopPropagation();
        header.classList.add("drop-into");
      }
    });
    header.addEventListener("dragleave", () => header.classList.remove("drop-into"));
    header.addEventListener("drop", async (e) => {
      header.classList.remove("drop-into");
      if (!drag || drag.kind !== "prompt" || drag.fromCatId === cat.id) return;
      e.preventDefault(); e.stopPropagation();
      const moved = drag; drag = null;
      const r = await PR.bridge.call("move_prompt", moved.id, cat.id, null);
      if (r && r.ok) { await PR.app.refreshState(); render(); toast("Moved to “" + cat.name + "”"); }
    });

    const list = el("div", { class: "cat-prompts" });
    own.forEach((p, i) => list.appendChild(promptRow(p, cat, ownAll.indexOf(p))));
    if (!own.length && !subs.length) {
      list.appendChild(el("div", { class: "cat-empty", text: "Empty — drop prompts here or hit +" }));
    }
    enablePromptDrag(list, cat);

    const subwrap = el("div", { class: "cat-subs" });
    subs.forEach((sc) => subwrap.appendChild(sc));
    if (subs.length) enableCategoryDrag(subwrap, cat);

    group.appendChild(header);
    group.appendChild(list);
    group.appendChild(subwrap);
    return group;
  }

  function countTree(cat) {
    let n = (cat.prompts || []).length;
    (cat.subcategories || []).forEach((s) => (n += countTree(s)));
    return n;
  }

  function promptRow(p, cat, index) {
    const row = el("div", { class: "prow", draggable: "true", dataset: { id: p.id, idx: index } }, [
      el("span", { class: "grip", html: icon("grip") }),
      el("span", { class: "ptype " + (p.type === "image" ? "image" : ""), text: p.type === "image" ? "IMG" : "TXT" }),
      el("span", { class: "ptitle", text: p.title || "Untitled" }),
      p.favorite ? el("span", { class: "pfav", html: icon("star") }) : null,
      el("div", { class: "prow-actions" }, [
        iconBtn("copy", "Copy", async (e) => { e.stopPropagation(); const r = await PR.bridge.call("copy_prompt", p.id, p.prompt); if (r && r.ok) toast("Copied"); }),
        iconBtn("edit", "Edit", (e) => { e.stopPropagation(); editPrompt(p.id); }),
        iconBtn("trash", "Delete", (e) => { e.stopPropagation(); deletePrompt(p, cat); }),
      ]),
    ]);
    row.addEventListener("click", (e) => { if (!e.target.closest(".prow-actions")) editPrompt(p.id); });
    return row;
  }

  function iconBtn(name, title, onclick) {
    return el("button", { class: "iconbtn", title, html: icon(name), onclick });
  }

  async function toggleCollapse(cat, group) {
    cat.collapsed = !cat.collapsed;
    group.classList.toggle("collapsed", cat.collapsed);
    PR.bridge.call("update_category", cat.id, { collapsed: cat.collapsed });
  }

  /* ---- drag: prompts ------------------------------------------------------ */

  function enablePromptDrag(list, cat) {
    list.addEventListener("dragstart", (e) => {
      const row = e.target.closest(".prow");
      if (!row || !list.contains(row)) return;
      e.stopPropagation();
      drag = { kind: "prompt", id: row.dataset.id, fromCatId: cat.id };
      row.classList.add("dragging");
      e.dataTransfer.effectAllowed = "move";
      try { e.dataTransfer.setData("text/plain", row.dataset.id); } catch (err) {}
    });
    list.addEventListener("dragend", (e) => {
      e.stopPropagation();
      drag = null;
      document.querySelectorAll(".dragging, .drop-target, .drop-into").forEach((node) =>
        node.classList.remove("dragging", "drop-target", "drop-into"));
    });
    list.addEventListener("dragover", (e) => {
      if (!drag || drag.kind !== "prompt") return;
      e.preventDefault(); e.stopPropagation();
      const row = e.target.closest(".prow");
      document.querySelectorAll(".prow.drop-target").forEach((r) => r.classList.remove("drop-target"));
      document.querySelectorAll(".cat-prompts.drop-into").forEach((other) => {
        if (other !== list) other.classList.remove("drop-into");
      });
      list.classList.toggle("drop-into", drag.fromCatId !== cat.id);
      if (row && row.dataset.id !== drag.id) row.classList.add("drop-target");
    });
    list.addEventListener("dragleave", (e) => {
      if (!list.contains(e.relatedTarget)) list.classList.remove("drop-into");
    });
    list.addEventListener("drop", async (e) => {
      if (!drag || drag.kind !== "prompt") return;
      e.preventDefault(); e.stopPropagation();
      const target = e.target.closest(".prow");
      const moved = drag; drag = null;
      list.classList.remove("drop-into");
      if (moved.fromCatId !== cat.id) {
        const to = target ? +target.dataset.idx : null;
        const r = await PR.bridge.call("move_prompt", moved.id, cat.id, to);
        if (r && r.ok) {
          await PR.app.refreshState(); render(); toast("Moved to “" + cat.name + "”");
        }
        return;
      }
      if (!target || target.dataset.id === moved.id) return;
      const from = (cat.prompts || []).findIndex((x) => x.id === moved.id);
      const to = +target.dataset.idx;
      if (from < 0 || from === to) return;
      await PR.bridge.call("reorder_prompt", cat.id, from, to);
      await PR.app.refreshState(); render();
    });
  }

  /* ---- drag: categories among siblings ------------------------------------ */

  function enableCategoryDrag(container, parentCat) {
    container.addEventListener("dragstart", (e) => {
      const header = e.target.closest(".cat-header");
      if (!header) return;
      const group = header.closest(".cat-group");
      // Only handle groups that are DIRECT children of this container.
      if (!group || group.parentElement !== container) return;
      e.stopPropagation();
      drag = { kind: "category", id: group.dataset.id, parentId: parentCat ? parentCat.id : null };
      group.classList.add("dragging");
      e.dataTransfer.effectAllowed = "move";
    });
    container.addEventListener("dragend", (e) => {
      e.stopPropagation();
      drag = null;
      container.querySelectorAll(".dragging, .drop-before").forEach((g) => g.classList.remove("dragging", "drop-before"));
    });
    container.addEventListener("dragover", (e) => {
      if (!drag || drag.kind !== "category") return;
      const myParent = parentCat ? parentCat.id : null;
      if (drag.parentId !== myParent) return;
      const over = e.target.closest(".cat-group");
      if (!over || over.parentElement !== container) return;
      e.preventDefault(); e.stopPropagation();
      container.querySelectorAll(".drop-before").forEach((g) => g.classList.remove("drop-before"));
      if (over.dataset.id !== drag.id) over.classList.add("drop-before");
    });
    container.addEventListener("drop", async (e) => {
      if (!drag || drag.kind !== "category") return;
      const myParent = parentCat ? parentCat.id : null;
      if (drag.parentId !== myParent) return;
      const over = e.target.closest(".cat-group");
      if (!over || over.parentElement !== container) return;
      e.preventDefault(); e.stopPropagation();
      const moved = drag; drag = null;
      if (over.dataset.id === moved.id) return;
      const siblings = parentCat ? parentCat.subcategories : PR.state.categories;
      const to = siblings.findIndex((c) => c.id === over.dataset.id);
      if (to < 0) return;
      await PR.bridge.call("reorder_category", moved.id, to);
      await PR.app.refreshState(); render();
    });
  }

  /* ---- prompt editor modal ---------------------------------------------- */
  function newPrompt(categoryId, prefill) {
    if (!categoryId) {
      const first = PR.state.categories[0];
      categoryId = first ? first.id : null;
    }
    openPromptModal(Object.assign({ type: "text", title: "", prompt: "", tags: [], note: "" }, prefill || {}), categoryId, true);
  }
  function editPrompt(id) {
    const f = PR.findPrompt(id);
    if (!f) return;
    openPromptModal(f.p, f.c.id, false);
  }

  function openPromptModal(p, categoryId, isNew) {
    PR.state.suppressBlur = true;
    let type = p.type || "text";

    const title = el("input", { class: "input", value: p.title || "", placeholder: "Title" });
    const body = el("textarea", { class: "textarea", placeholder: "The prompt…", style: { minHeight: "130px" } });
    body.value = p.prompt || "";
    const tags = el("input", { class: "input", value: (p.tags || []).join(", "), placeholder: "tags, comma, separated" });
    const note = el("input", { class: "input", value: p.note || "", placeholder: "Optional note" });

    // category select
    const catSel = el("select", { class: "select" });
    flatCats(PR.state.categories).forEach(({ id, label }) =>
      catSel.appendChild(el("option", { value: id, text: label, selected: id === categoryId ? "selected" : null })));

    // image fields
    const neg = el("input", { class: "input", value: p.negative || "", placeholder: "things to avoid" });
    const model = el("input", { class: "input", value: p.model || "", placeholder: "e.g. Midjourney v7, SDXL, Flux.1" });
    const params = el("input", { class: "input", value: p.params || "", placeholder: "--ar 16:9 --stylize 250 / Steps, CFG…" });
    const imageBlock = el("details", { class: "image-fields image-details" }, [
      el("summary", { text: "Optional image details" }),
      el("div", { class: "image-details-body" }, [
        el("div", { class: "image-copy-hint", text:
          "Put Midjourney flags and other copyable suffixes directly at the end of the Prompt above. These fields are optional metadata." }),
        el("div", { class: "field" }, [el("label", { text: "Negative prompt" }), neg]),
        el("div", { class: "field-row" }, [
          el("div", { class: "field" }, [el("label", { text: "Model" }), model]),
          el("div", { class: "field" }, [el("label", { text: "Parameters" }), params]),
        ]),
      ]),
    ]);
    imageBlock.open = !!(p.negative || p.model || p.params);
    imageBlock.style.display = type === "image" ? "block" : "none";

    const seg = el("div", { class: "segmented" }, [
      segBtn("Text", type === "text", () => setType("text")),
      segBtn("Image", type === "image", () => setType("image")),
    ]);
    function setType(t) {
      type = t;
      [...seg.children].forEach((b, i) => b.classList.toggle("on", (i === 0) === (t === "text")));
      imageBlock.style.display = t === "image" ? "block" : "none";
    }

    const form = el("div", {}, [
      el("div", { class: "field-row" }, [
        el("div", { class: "field", style: { flex: "0 0 auto" } }, [el("label", { text: "Type" }), seg]),
        el("div", { class: "field" }, [el("label", { text: "Category" }), catSel]),
      ]),
      el("div", { class: "field" }, [el("label", { text: "Title" }), title]),
      el("div", { class: "field" }, [el("label", { text: "Prompt" }), body]),
      imageBlock,
      el("div", { class: "field-row" }, [
        el("div", { class: "field" }, [el("label", { text: "Tags" }), tags]),
        el("div", { class: "field" }, [el("label", { text: "Note" }), note]),
      ]),
    ]);

    const save = el("button", { class: "btn btn-primary", text: isNew ? "Create" : "Save" });
    const cancel = el("button", { class: "btn btn-ghost", text: "Cancel", onclick: () => { PR.ui.closeModal(); PR.state.suppressBlur = false; } });
    const m = modal({ title: isNew ? "New prompt" : "Edit prompt", body: form, footer: [cancel, save], wide: true,
      onClose: () => { PR.state.suppressBlur = false; } });

    save.addEventListener("click", async () => {
      const fields = {
        type, title: title.value.trim(), prompt: body.value,
        tags: tags.value.split(",").map((t) => t.trim()).filter(Boolean),
        note: note.value.trim(),
        negative: neg.value, model: model.value, params: params.value,
      };
      if (!fields.title && !fields.prompt) { toast("Add a title or prompt", { bad: true }); return; }
      let r;
      if (isNew) r = await PR.bridge.call("add_prompt", catSel.value, fields);
      else {
        r = await PR.bridge.call("update_prompt", p.id, fields);
        if (r && r.ok && catSel.value !== categoryId) await PR.bridge.call("move_prompt", p.id, catSel.value, null);
      }
      if (r && r.ok) {
        m.close(); await PR.app.refreshState();
        if (PR.state.view === "editor") render(); else PR.launcher.runSearch();
        toast(isNew ? "Prompt created" : "Saved");
      }
      else toast((r && r.error) || "Save failed", { bad: true });
    });
    setTimeout(() => title.focus(), 50);
  }

  function segBtn(label, on, onclick) { return el("button", { class: "" + (on ? "on" : ""), text: label, onclick }); }

  function flatCats(cats, depth = 0, out = []) {
    cats.forEach((c) => {
      out.push({ id: c.id, label: "  ".repeat(depth) + (depth ? "↳ " : "") + (c.icon ? c.icon + " " : "") + c.name });
      if (c.subcategories) flatCats(c.subcategories, depth + 1, out);
    });
    return out;
  }

  /* ---- deletes ---------------------------------------------------------- */
  function deletePrompt(p, cat) {
    const index = (cat.prompts || []).findIndex((x) => x.id === p.id);
    PR.bridge.call("delete_prompt", p.id).then(async (r) => {
      if (r && r.ok) {
        await PR.app.refreshState(); render();
        toast("Deleted “" + (p.title || "prompt") + "”", { undo: async () => {
          await PR.bridge.call("restore_prompt", cat.id, r.removed || p, index);
          await PR.app.refreshState(); render();
        }});
      }
    });
  }

  function deleteCategory(cat) {
    const n = countTree(cat);
    const subs = (cat.subcategories || []).length;
    confirmDialog({
      title: "Delete category?",
      message: `“${cat.name}” will be removed along with ${n} prompt${n === 1 ? "" : "s"}` +
               (subs ? ` and ${subs} subcategor${subs === 1 ? "y" : "ies"}.` : "."),
      confirmText: "Delete", danger: true,
      onConfirm: async () => { await PR.bridge.call("delete_category", cat.id); await PR.app.refreshState(); render(); toast("Category deleted"); },
    });
  }

  /* ---- category add / edit ---------------------------------------------- */
  const CAT_EMOJI = ["💻", "🎨", "⚖️", "🧠", "✍️", "📈", "🚀", "🤖", "🌌", "📚", "🧪", "🎬", "🎵", "🗂️", "💡", "🔥"];

  function categoryModal({ title, initial, onSave }) {
    PR.state.suppressBlur = true;
    const name = el("input", { class: "input", value: initial.name || "", placeholder: "Category name" });
    const color = colorPicker(initial.color || "");
    const emoji = emojiPicker(initial.icon || "");
    const save = el("button", { class: "btn btn-primary", text: initial.name ? "Save" : "Create" });
    const cancel = el("button", { class: "btn btn-ghost", text: "Cancel", onclick: () => { PR.ui.closeModal(); PR.state.suppressBlur = false; } });
    const m = modal({ title,
      body: el("div", {}, [
        el("div", { class: "field" }, [el("label", { text: "Name" }), name]),
        el("div", { class: "field" }, [el("label", { text: "Icon" }), emoji.node]),
        el("div", { class: "field" }, [el("label", { text: "Accent color" }), color.node]),
      ]), footer: [cancel, save], onClose: () => { PR.state.suppressBlur = false; } });
    save.addEventListener("click", async () => {
      if (!name.value.trim()) { toast("Name it first", { bad: true }); return; }
      await onSave({ name: name.value.trim(), color: color.value(), icon: emoji.value() });
      m.close();
    });
    setTimeout(() => name.focus(), 50);
    return m;
  }

  function addCategory(parentId) {
    categoryModal({
      title: parentId ? "New subcategory" : "New category",
      initial: {},
      onSave: async ({ name, color, icon }) => {
        const r = await PR.bridge.call("add_category", name, parentId);
        if (r && r.ok && (color || icon)) await PR.bridge.call("update_category", r.category.id, { color, icon });
        await PR.app.refreshState(); render(); toast(parentId ? "Subcategory created" : "Category created");
      },
    });
  }

  function editCategory(cat) {
    categoryModal({
      title: "Edit category",
      initial: { name: cat.name, color: cat.color || "", icon: cat.icon || "" },
      onSave: async ({ name, color, icon }) => {
        await PR.bridge.call("update_category", cat.id, { name: name || cat.name, color, icon });
        await PR.app.refreshState(); render();
      },
    });
  }

  const SWATCHES = ["#7c5cff", "#22d3ee", "#f472b6", "#34d399", "#fb923c", "#f43f5e", "#a78bfa", "#eab308", "#3b82f6", ""];
  function colorPicker(current) {
    let value = current;
    const node = el("div", { class: "picker-row" });
    SWATCHES.forEach((c) => {
      const sw = el("button", { class: "pick" + (c === current ? " on" : ""), title: c || "none",
        style: { background: c || "transparent", borderStyle: c ? "solid" : "dashed" } });
      sw.addEventListener("click", () => {
        value = c;
        node.querySelectorAll(".pick").forEach((x) => x.classList.remove("on"));
        sw.classList.add("on");
      });
      node.appendChild(sw);
    });
    return { node, value: () => value };
  }

  function emojiPicker(current) {
    let value = current;
    const node = el("div", { class: "picker-row" });
    const opts = [""].concat(CAT_EMOJI);
    opts.forEach((e) => {
      const b = el("button", { class: "pick emoji" + (e === current ? " on" : ""),
        text: e || "—", title: e ? e : "no icon" });
      b.addEventListener("click", () => {
        value = e;
        node.querySelectorAll(".pick").forEach((x) => x.classList.remove("on"));
        b.classList.add("on");
      });
      node.appendChild(b);
    });
    return { node, value: () => value };
  }

  PR.editor = { render, newPrompt, editPrompt, addCategory };
})();
