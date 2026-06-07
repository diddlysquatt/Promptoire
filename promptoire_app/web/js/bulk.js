/* bulk.js — the JSON ⇄ LLM "improve my whole library" loop */
(function () {
  "use strict";
  const PR = window.PROMPTOIRE;
  const { el, icon, toast, escapeHtml } = PR.ui;

  let pasteArea, previewBox, applyBtn, optUpdate, optAdd;

  function render() {
    const host = document.getElementById("bulkBody");
    host.innerHTML = "";

    host.appendChild(el("p", { class: "bulk-intro", html:
      "Hand your <b>entire</b> prompt library to any LLM in one shot, let it rewrite and expand everything, " +
      "then merge the result back — matched by id, with a preview before anything changes." }));

    // STEP 1 — export
    const step1 = el("div", { class: "step" }, [
      el("div", { class: "step-head" }, [
        el("span", { class: "step-num", text: "1" }),
        el("div", {}, [ el("div", { class: "t", text: "Send your library to an AI" }),
          el("div", { class: "d", text: "Copies a ready-to-paste prompt + your whole library as JSON." }) ]),
      ]),
      el("div", { class: "btn-row" }, [
        el("button", { class: "btn btn-primary", html: icon("copy") + " Copy for AI", onclick: copyForAI }),
        el("button", { class: "btn", text: "Copy JSON only", onclick: () => copyExport(false) }),
        el("button", { class: "btn btn-ghost", text: "Save .json", onclick: saveFile }),
        el("button", { class: "btn btn-ghost", text: "Edit AI instructions", onclick: editMeta }),
      ]),
    ]);

    // STEP 2 — import
    pasteArea = el("textarea", { class: "textarea", style: { minHeight: "120px" },
      placeholder: "Paste the improved JSON the AI gives you here…  (code fences and extra prose are fine)" });
    pasteArea.addEventListener("input", () => { applyBtn.disabled = true; previewBox.innerHTML = ""; });

    const step2 = el("div", { class: "step" }, [
      el("div", { class: "step-head" }, [
        el("span", { class: "step-num", text: "2" }),
        el("div", {}, [ el("div", { class: "t", text: "Bring the improved version back" }),
          el("div", { class: "d", text: "Paste it below (or load a file), preview the changes, then merge." }) ]),
      ]),
      pasteArea,
      el("div", { class: "btn-row", style: { marginTop: "10px" } }, [
        el("button", { class: "btn", text: "Load from file…", onclick: loadFile }),
        el("button", { class: "btn btn-primary", html: icon("check") + " Preview changes", onclick: preview }),
      ]),
    ]);

    // preview + apply
    previewBox = el("div", {});
    const opts = el("div", { class: "row-between", style: { margin: "8px 2px" } }, [
      toggleInline("Update existing", true, (v) => (window._optUpdate = v), (r) => (optUpdate = r)),
      toggleInline("Add new", true, (v) => (window._optAdd = v), (r) => (optAdd = r)),
    ]);
    applyBtn = el("button", { class: "btn btn-primary", html: icon("check") + " Merge into library", disabled: "disabled",
      onclick: apply });
    const applyRow = el("div", { class: "btn-row", style: { marginTop: "6px" } }, [ applyBtn,
      el("button", { class: "btn btn-danger", text: "Replace everything…", onclick: replaceAll }) ]);

    host.appendChild(step1);
    host.appendChild(step2);
    host.appendChild(previewBox);
    host.appendChild(opts);
    host.appendChild(applyRow);
  }

  function toggleInline(label, checked, onChange, ref) {
    const input = el("input", { type: "checkbox" });
    input.checked = checked;
    input.addEventListener("change", () => onChange(input.checked));
    if (ref) ref(input);
    return el("label", { style: { display: "flex", alignItems: "center", gap: "8px", fontSize: "12.5px", color: "var(--muted)" } },
      [ wrapSwitch(input), label ]);
  }
  function wrapSwitch(input) {
    return el("span", { class: "switch" }, [input, el("span", { class: "track" }), el("span", { class: "knob" })]);
  }

  async function copyForAI() {
    const r = await PR.bridge.call("copy_export", true, false);
    if (r && r.ok) toast("Copied — paste into ChatGPT, Claude, etc.");
    else toast((r && r.error) || "Copy failed", { bad: true });
  }
  async function copyExport(meta) {
    const r = await PR.bridge.call("copy_export", meta, false);
    if (r && r.ok) toast("JSON copied (" + (r.chars || 0) + " chars)");
    else toast("Copy failed", { bad: true });
  }
  async function saveFile() {
    PR.state.suppressBlur = true;
    const r = await PR.bridge.call("save_export_file", false);
    PR.state.suppressBlur = false;
    if (r && r.ok && !r.cancelled) toast("Saved");
  }
  async function loadFile() {
    PR.state.suppressBlur = true;
    const r = await PR.bridge.call("load_import_file");
    PR.state.suppressBlur = false;
    if (r && r.ok && r.text) { pasteArea.value = r.text; preview(); }
  }

  async function preview() {
    const text = pasteArea.value.trim();
    if (!text) { toast("Paste some JSON first", { bad: true }); return; }
    const r = await PR.bridge.call("merge_preview", text);
    if (!r || !r.ok) { toast((r && r.error) || "Could not read JSON", { bad: true }); previewBox.innerHTML = ""; applyBtn.disabled = true; return; }
    renderPreview(r.preview);
    applyBtn.disabled = false;
  }

  function renderPreview(pv) {
    previewBox.innerHTML = "";
    const summary = el("div", { class: "diff-summary" }, [
      el("span", { class: "diff-pill add", text: pv.added.length + " new" }),
      el("span", { class: "diff-pill upd", text: pv.updated.length + " updated" }),
      el("span", { class: "diff-pill same", text: pv.unchanged_count + " unchanged" }),
      pv.new_categories.length ? el("span", { class: "diff-pill", text: pv.new_categories.length + " new categories" }) : null,
    ]);
    previewBox.appendChild(summary);

    const list = el("div", { class: "diff-list" });
    pv.updated.forEach((it) => list.appendChild(diffItem("upd", it)));
    pv.added.forEach((it) => list.appendChild(diffItem("add", it)));
    if (!pv.updated.length && !pv.added.length) {
      list.appendChild(el("div", { class: "txt-muted", style: { fontSize: "12.5px", padding: "8px 2px" },
        text: "Nothing would change — the incoming library matches what you have." }));
    }
    previewBox.appendChild(list);
  }

  function diffItem(kind, it) {
    const changes = it.changes ? Object.keys(it.changes).join(", ") : "";
    return el("div", { class: "diff-item" }, [
      el("div", { class: "di-top" }, [
        el("span", { class: "di-badge " + kind, text: kind === "add" ? "NEW" : "UPD" }),
        el("span", { class: "di-title", text: it.title || "Untitled" }),
        el("span", { class: "di-cat", text: it.category_name || "" }),
      ]),
      changes ? el("div", { class: "di-changes", text: "changes: " + changes }) : null,
    ]);
  }

  async function apply() {
    const text = pasteArea.value.trim();
    const upd = optUpdate ? optUpdate.checked : true;
    const add = optAdd ? optAdd.checked : true;
    const r = await PR.bridge.call("apply_merge", text, upd, add);
    if (r && r.ok) {
      await PR.app.refreshState();
      const res = r.result || {};
      toast(`Merged: ${res.updated || 0} updated, ${res.added || 0} added`);
      pasteArea.value = ""; previewBox.innerHTML = ""; applyBtn.disabled = true;
    } else toast((r && r.error) || "Merge failed", { bad: true });
  }

  function replaceAll() {
    const text = pasteArea.value.trim();
    if (!text) { toast("Paste the JSON to replace with first", { bad: true }); return; }
    PR.ui.confirmDialog({
      title: "Replace the entire library?",
      message: "This discards your current library and replaces it with the pasted JSON. A backup is saved first, but this can't be undone in-app.",
      confirmText: "Replace everything", danger: true,
      onConfirm: async () => {
        const r = await PR.bridge.call("replace_all", text);
        if (r && r.ok) { await PR.app.refreshState(); toast("Library replaced"); pasteArea.value = ""; previewBox.innerHTML = ""; }
        else toast((r && r.error) || "Failed", { bad: true });
      },
    });
  }

  function editMeta() {
    PR.state.suppressBlur = true;
    const ta = el("textarea", { class: "textarea", style: { minHeight: "200px" } });
    ta.value = (PR.state.settings.bulk_improve && PR.state.settings.bulk_improve.meta_prompt) || "";
    const save = el("button", { class: "btn btn-primary", text: "Save instructions" });
    const cancel = el("button", { class: "btn btn-ghost", text: "Cancel", onclick: () => { PR.ui.closeModal(); PR.state.suppressBlur = false; } });
    const m = PR.ui.modal({ title: "AI instructions (meta-prompt)", wide: true,
      body: el("div", {}, [
        el("p", { class: "hint", style: { marginBottom: "8px" }, html: "Prepended before your JSON when you click <b>Copy for AI</b>. Tell the model how to improve your prompts." }),
        ta ]),
      footer: [cancel, save], onClose: () => { PR.state.suppressBlur = false; } });
    save.addEventListener("click", async () => {
      await PR.bridge.call("update_settings", { bulk_improve: { meta_prompt: ta.value } });
      PR.state.settings.bulk_improve = { meta_prompt: ta.value };
      m.close(); toast("Saved");
    });
  }

  PR.bulk = { render };
})();
