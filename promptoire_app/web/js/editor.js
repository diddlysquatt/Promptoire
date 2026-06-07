/* editor.js — manage the library: categories, prompts, image fields, reorder */
(function () {
  "use strict";
  const PR = window.PROMPTOIRE;
  const { el, icon, toast, modal, confirmDialog, escapeHtml } = PR.ui;

  function render() {
    const host = document.getElementById("editorBody");
    host.innerHTML = "";
    const cats = PR.state.categories;
    if (!cats.length) {
      host.appendChild(el("div", { class: "empty" }, [
        el("div", { class: "emoji", text: "📁" }),
        el("h3", { text: "No categories yet" }),
        el("button", { class: "btn btn-primary btn-sm", text: "+ Add category", onclick: addCategory }),
      ]));
      return;
    }
    cats.forEach((c) => host.appendChild(catGroup(c)));
  }

  function catGroup(cat) {
    const collapsed = cat.collapsed;
    const group = el("div", { class: "cat-group" + (collapsed ? " collapsed" : ""), dataset: { id: cat.id } });
    const accent = cat.color || "";
    const count = (cat.prompts || []).length;

    const header = el("div", { class: "cat-header", style: accent ? { "--cat-accent": accent } : {} }, [
      el("span", { class: "cat-caret", html: icon("caret") }),
      el("span", { class: "cat-dot" }),
      el("span", { class: "cat-name", text: cat.name }),
      el("span", { class: "cat-count", text: count }),
      el("div", { class: "cat-actions" }, [
        iconBtn("plus", "Add prompt", (e) => { e.stopPropagation(); newPrompt(cat.id); }),
        iconBtn("edit", "Rename / color", (e) => { e.stopPropagation(); editCategory(cat); }),
        iconBtn("trash", "Delete category", (e) => { e.stopPropagation(); deleteCategory(cat); }),
      ]),
    ]);
    header.addEventListener("click", () => toggleCollapse(cat, group));

    const list = el("div", { class: "cat-prompts" });
    (cat.prompts || []).forEach((p, i) => list.appendChild(promptRow(p, cat, i)));
    (cat.subcategories || []).forEach((sc) => list.appendChild(catGroup(sc)));

    group.appendChild(header);
    group.appendChild(list);
    enableDrag(list, cat);
    return group;
  }

  function promptRow(p, cat, index) {
    const row = el("div", { class: "prow", draggable: "true", dataset: { id: p.id, idx: index } }, [
      el("span", { class: "grip", html: icon("grip") }),
      el("span", { class: "ptype " + (p.type === "image" ? "image" : ""), text: p.type === "image" ? "IMG" : "TXT" }),
      el("span", { class: "ptitle", text: p.title || "Untitled" }),
      el("div", { class: "prow-actions" }, [
        iconBtn("copy", "Copy", (e) => { e.stopPropagation(); PR.bridge.call("copy_prompt", p.id, p.prompt).then(() => toast("Copied")); }),
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
    const model = el("input", { class: "input", value: p.model || "", placeholder: "e.g. Midjourney v6, SDXL, Flux.1" });
    const params = el("input", { class: "input", value: p.params || "", placeholder: "--ar 16:9 --stylize 250 / Steps, CFG…" });
    const imageBlock = el("div", { class: "image-fields" }, [
      el("div", { class: "field" }, [el("label", { text: "Negative prompt" }), neg]),
      el("div", { class: "field-row" }, [
        el("div", { class: "field" }, [el("label", { text: "Model" }), model]),
        el("div", { class: "field" }, [el("label", { text: "Parameters" }), params]),
      ]),
    ]);
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
      if (r && r.ok) { m.close(); await PR.app.refreshState(); render(); toast(isNew ? "Prompt created" : "Saved"); }
      else toast((r && r.error) || "Save failed", { bad: true });
    });
    setTimeout(() => title.focus(), 50);
  }

  function segBtn(label, on, onclick) { return el("button", { class: "" + (on ? "on" : ""), text: label, onclick }); }

  function flatCats(cats, depth = 0, out = []) {
    cats.forEach((c) => {
      out.push({ id: c.id, label: "  ".repeat(depth) + (depth ? "↳ " : "") + c.name });
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
    confirmDialog({
      title: "Delete category?",
      message: `“${cat.name}” and its ${(cat.prompts || []).length} prompt(s) will be removed.`,
      confirmText: "Delete", danger: true,
      onConfirm: async () => { await PR.bridge.call("delete_category", cat.id); await PR.app.refreshState(); render(); toast("Category deleted"); },
    });
  }

  /* ---- category add / edit ---------------------------------------------- */
  function addCategory() {
    PR.state.suppressBlur = true;
    const name = el("input", { class: "input", placeholder: "Category name" });
    const color = colorPicker("");
    const save = el("button", { class: "btn btn-primary", text: "Create" });
    const cancel = el("button", { class: "btn btn-ghost", text: "Cancel", onclick: () => { PR.ui.closeModal(); PR.state.suppressBlur = false; } });
    const m = modal({ title: "New category",
      body: el("div", {}, [
        el("div", { class: "field" }, [el("label", { text: "Name" }), name]),
        el("div", { class: "field" }, [el("label", { text: "Accent color" }), color.node]),
      ]), footer: [cancel, save], onClose: () => { PR.state.suppressBlur = false; } });
    save.addEventListener("click", async () => {
      if (!name.value.trim()) { toast("Name it first", { bad: true }); return; }
      const r = await PR.bridge.call("add_category", name.value.trim(), null);
      if (r && r.ok && color.value()) await PR.bridge.call("update_category", r.category.id, { color: color.value() });
      m.close(); await PR.app.refreshState(); render(); toast("Category created");
    });
    setTimeout(() => name.focus(), 50);
  }

  function editCategory(cat) {
    PR.state.suppressBlur = true;
    const name = el("input", { class: "input", value: cat.name });
    const color = colorPicker(cat.color || "");
    const save = el("button", { class: "btn btn-primary", text: "Save" });
    const cancel = el("button", { class: "btn btn-ghost", text: "Cancel", onclick: () => { PR.ui.closeModal(); PR.state.suppressBlur = false; } });
    const m = modal({ title: "Edit category",
      body: el("div", {}, [
        el("div", { class: "field" }, [el("label", { text: "Name" }), name]),
        el("div", { class: "field" }, [el("label", { text: "Accent color" }), color.node]),
      ]), footer: [cancel, save], onClose: () => { PR.state.suppressBlur = false; } });
    save.addEventListener("click", async () => {
      await PR.bridge.call("update_category", cat.id, { name: name.value.trim() || cat.name, color: color.value() });
      m.close(); await PR.app.refreshState(); render();
    });
  }

  const SWATCHES = ["#7c5cff", "#22d3ee", "#f472b6", "#34d399", "#fb923c", "#f43f5e", "#a78bfa", "#eab308", "#3b82f6", ""];
  function colorPicker(current) {
    let value = current;
    const node = el("div", { style: { display: "flex", gap: "6px", flexWrap: "wrap" } });
    SWATCHES.forEach((c) => {
      const sw = el("button", { class: "iconbtn", title: c || "none",
        style: { width: "26px", height: "26px", background: c || "transparent",
          border: c ? "1px solid rgba(255,255,255,0.2)" : "1px dashed var(--border-2)" } });
      if (c === current) sw.style.outline = "2px solid #fff";
      sw.addEventListener("click", () => {
        value = c; [...node.children].forEach((x) => (x.style.outline = "none")); sw.style.outline = "2px solid #fff";
      });
      node.appendChild(sw);
    });
    return { node, value: () => value };
  }

  /* ---- drag reorder within a category ----------------------------------- */
  function enableDrag(list, cat) {
    let dragEl = null;
    list.addEventListener("dragstart", (e) => {
      const row = e.target.closest(".prow"); if (!row) return;
      dragEl = row; row.classList.add("dragging");
      e.dataTransfer.effectAllowed = "move";
    });
    list.addEventListener("dragend", () => { if (dragEl) dragEl.classList.remove("dragging"); dragEl = null;
      list.querySelectorAll(".drop-target").forEach((r) => r.classList.remove("drop-target")); });
    list.addEventListener("dragover", (e) => {
      e.preventDefault();
      const row = e.target.closest(".prow");
      list.querySelectorAll(".drop-target").forEach((r) => r.classList.remove("drop-target"));
      if (row && row !== dragEl) row.classList.add("drop-target");
    });
    list.addEventListener("drop", async (e) => {
      e.preventDefault();
      const target = e.target.closest(".prow");
      if (!dragEl || !target || dragEl === target) return;
      const from = +dragEl.dataset.idx, to = +target.dataset.idx;
      await PR.bridge.call("reorder_prompt", cat.id, from, to);
      await PR.app.refreshState(); render();
    });
  }

  PR.editor = { render, newPrompt, editPrompt, addCategory };
})();
