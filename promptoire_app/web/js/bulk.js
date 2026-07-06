/* bulk.js — the outline/JSON ⇄ LLM "improve my whole library" loop */
(function () {
  "use strict";
  const PR = window.PROMPTOIRE;
  const { el, icon, toast, escapeHtml } = PR.ui;

  const OUTLINE_REQUEST =
    "Create a batch of prompts for my Promptoire library using this simple import outline format.\n\n" +
    "Rules:\n" +
    "- Return only the outline. Do not wrap it in a code fence.\n" +
    "- Use # headings, Path: Section > Subsection > Nested subsection, Section/Subsection labels, or indentation for nested sections.\n" +
    "- Nested bullet outlines are fine: - Section, - Subsection, - Prompt title: prompt body.\n" +
    "- For deeper labels, use Sub-subsection: or Nested subsection:.\n" +
    "- Use prompt rows like: Title: Prompt body\n" +
    "- Numbered blocks like Prompt 1: are fine when a prompt needs multiple lines.\n" +
    "- YAML-style lists like - Title: ... with indented Prompt:/Tags: fields are fine.\n" +
    "- Markdown tables are fine if they include Title and Prompt columns.\n" +
    "- For image prompts, use fields like Type: image, Negative prompt, Image model, Parameters, and CFG scale.\n" +
    "- Keep each prompt clear, specific, reusable, and easy to scan.\n" +
    "- Use {placeholders} where the user should fill in a value.\n" +
    "- Make sections and subsections organized enough that I can merge them into an existing library.\n\n" +
    "Example format:\n\n" +
    "Coding\n" +
    "  Debugging\n" +
    "    Bug sweep: Review {code} for edge cases, broken assumptions, and missing tests. Return prioritized findings with minimal fixes.\n\n" +
    "Section: Writing\n" +
    "Subsection: Editing\n" +
    "Prompt 1:\n" +
    "Rewrite {text} to be clearer and more direct while preserving the original voice.\n\n" +
    "Subsection: Drafting\n" +
    "First draft: Draft a first pass about {topic} in a clear, useful structure.\n\n" +
    "Path: AI Art > Characters > Portraits\n" +
    "Title: Cinematic portrait\n" +
    "Type: image\n" +
    "Prompt: A dramatic 85mm portrait of {subject}, rim lighting, shallow depth of field.\n" +
    "Negative prompt: blurry, watermark, extra fingers\n" +
    "Image model: Midjourney v6\n" +
    "Parameters: --ar 4:5 --stylize 250\n\n" +
    "Now create prompts for this topic or workflow:\n\n";

  const EXAMPLE_OUTLINE =
    "Coding\n" +
    "  Debugging\n" +
    "    Bug sweep: Review {code} for edge cases, broken assumptions, and missing tests. Return prioritized findings with minimal fixes.\n\n" +
    "Section: Writing\n" +
    "Subsection: Editing\n" +
    "Prompt 1:\n" +
    "Rewrite {text} to be clearer and more direct while preserving the original voice.\n\n" +
    "Subsection: Drafting\n" +
    "First draft: Draft a first pass about {topic} in a clear, useful structure.\n\n" +
    "Path: AI Art > Characters > Portraits\n" +
    "Title: Cinematic portrait\n" +
    "Type: image\n" +
    "Prompt: A dramatic 85mm portrait of {subject}, rim lighting, shallow depth of field.\n" +
    "Negative prompt: blurry, watermark, extra fingers\n" +
    "Image model: Midjourney v6\n" +
    "Parameters: --ar 4:5 --stylize 250\n";

  let pasteArea, previewBox, applyBtn, optUpdate, optAdd, mergeNote;

  function render() {
    const host = document.getElementById("bulkBody");
    host.innerHTML = "";

    host.appendChild(el("p", { class: "bulk-intro", html:
      "Hand your <b>entire</b> prompt library to any LLM in one shot, let it rewrite and expand everything, " +
      "then merge the result back. Imports match by id first, then by title inside the same section." }));

    // STEP 1 — export
    const step1 = el("div", { class: "step" }, [
      el("div", { class: "step-head" }, [
        el("span", { class: "step-num", text: "1" }),
        el("div", {}, [ el("div", { class: "t", text: "Send your library to an AI" }),
          el("div", { class: "d", text: "Copies a ready-to-paste prompt plus your library." }) ]),
      ]),
      el("div", { class: "btn-row" }, [
        el("button", { class: "btn btn-primary", html: icon("copy") + " Copy outline library", onclick: copyOutlineExport }),
        el("button", { class: "btn", text: "Copy outline request", onclick: copyOutlineRequest }),
        el("button", { class: "btn btn-ghost", text: "Save outline", onclick: saveOutlineFile }),
        el("button", { class: "btn btn-ghost", text: "Edit instructions", onclick: editOutlineInstructions }),
      ]),
      el("details", { class: "export-more" }, [
        el("summary", { text: "JSON options" }),
        el("div", { class: "btn-row" }, [
          el("button", { class: "btn", html: icon("copy") + " Copy for AI", onclick: copyForAI }),
          el("button", { class: "btn", text: "Copy JSON only", onclick: () => copyExport(false) }),
          el("button", { class: "btn btn-ghost", text: "Save .json", onclick: saveFile }),
          el("button", { class: "btn btn-ghost", text: "Edit JSON instructions", onclick: editJsonInstructions }),
        ]),
      ]),
      el("div", { class: "ai-direct" }, [
        el("div", { class: "ai-direct-or", text: "— or skip the copy/paste —" }),
        el("button", { class: "btn btn-primary ai-go",
          html: '<svg viewBox="0 0 24 24" class="ic" style="fill:currentColor;stroke-width:.6"><path d="M13 2L3 14h7l-1 8 10-12h-7z"/></svg> Improve with AI now',
          onclick: improveNow }),
        el("span", { class: "ai-direct-hint", id: "aiHint" }),
      ]),
    ]);

    // STEP 2 — import
    pasteArea = el("textarea", { class: "textarea", style: { minHeight: "150px" },
      placeholder: "Paste an improved outline, or JSON:\n\nCoding\n  Debugging\n    Bug sweep: Review this code for edge cases, broken assumptions, and missing tests.\n\nPath: AI Art > Characters > Portraits\nTitle: Cinematic portrait\nType: image\nPrompt: A dramatic 85mm portrait of {subject}...\nNegative prompt: blurry, watermark\nParameters: --ar 4:5" });
    pasteArea.addEventListener("input", () => {
      previewBox.innerHTML = "";
      delete previewBox.dataset.ready;
      syncMergeState();
    });

    const step2 = el("div", { class: "step" }, [
      el("div", { class: "step-head" }, [
        el("span", { class: "step-num", text: "2" }),
        el("div", {}, [ el("div", { class: "t", text: "Bring changes or new prompts back" }),
          el("div", { class: "d", text: "Paste an outline or JSON, preview it, then merge into what you already have." }) ]),
      ]),
      pasteArea,
      el("div", { class: "btn-row", style: { marginTop: "10px" } }, [
        el("button", { class: "btn", html: icon("copy") + " Paste from clipboard", onclick: pasteClipboard }),
        el("button", { class: "btn", text: "Load from file…", onclick: loadFile }),
        el("button", { class: "btn", text: "Use outline example", onclick: insertOutlineExample }),
        el("button", { class: "btn btn-primary", html: icon("check") + " Preview changes", onclick: preview }),
      ]),
    ]);

    // preview + apply
    previewBox = el("div", {});
    mergeNote = el("div", { class: "merge-note", text: "Preview an import first" });
    const opts = el("div", { class: "merge-options" }, [
      toggleInline("Update existing", true, (r) => (optUpdate = r), syncMergeState),
      toggleInline("Add new", true, (r) => (optAdd = r), syncMergeState),
    ]);
    applyBtn = el("button", { class: "btn btn-primary", html: icon("check") + " Merge into library", disabled: "disabled",
      onclick: apply });
    const mergeCard = el("div", { class: "merge-card" }, [
      el("div", { class: "merge-head" }, [
        el("div", { class: "merge-title", text: "Safe merge" }),
        mergeNote,
      ]),
      opts,
      el("div", { class: "btn-row" }, [ applyBtn ]),
    ]);
    const replaceDanger = el("details", { class: "danger-zone" }, [
      el("summary", { text: "Replace library" }),
      el("div", { class: "danger-body" }, [
        el("p", { class: "txt-muted", text: "Replaces every local prompt with the pasted import after saving a backup." }),
        el("button", { class: "btn btn-danger", text: "Replace everything…", onclick: replaceAll }),
      ]),
    ]);

    host.appendChild(step1);
    host.appendChild(step2);
    host.appendChild(previewBox);
    host.appendChild(mergeCard);
    host.appendChild(replaceDanger);
    syncMergeState();
  }

  function toggleInline(label, checked, ref, onChange) {
    const input = el("input", { type: "checkbox" });
    input.checked = checked;
    if (ref) ref(input);
    if (onChange) input.addEventListener("change", onChange);
    return el("label", { style: { display: "flex", alignItems: "center", gap: "8px", fontSize: "12.5px", color: "var(--muted)" } },
      [ wrapSwitch(input), label ]);
  }
  function wrapSwitch(input) {
    return el("span", { class: "switch" }, [input, el("span", { class: "track" }), el("span", { class: "knob" })]);
  }

  async function improveNow(e) {
    const btn = e.currentTarget;
    const ai = PR.state.settings.ai || {};
    if (!ai.api_key) {
      toast("Add an API key in Settings → AI first", { bad: true });
      PR.app.showView("settings");
      setTimeout(() => { const s = document.getElementById("aiKeyField"); if (s) s.focus(); }, 120);
      return;
    }
    const hint = document.getElementById("aiHint");
    btn.disabled = true;
    const orig = btn.innerHTML;
    btn.innerHTML = '<span class="spinner"></span> Improving…';
    if (hint) hint.textContent = "Calling " + (ai.provider || "anthropic") + "…";
    try {
      const r = await PR.bridge.call("ai_improve", false);
      if (r && r.ok) {
        pasteArea.value = r.text;
        if (hint) hint.textContent = "Got a reply" + (r.model ? " from " + r.model : "") + " — previewing…";
        await preview();
        toast("AI improved your library — review the changes below");
        pasteArea.scrollIntoView({ block: "center", behavior: "smooth" });
      } else {
        if (hint) hint.textContent = "";
        toast((r && r.error) || "AI request failed", { bad: true, duration: 6000 });
      }
    } finally {
      btn.disabled = false;
      btn.innerHTML = orig;
    }
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
  async function copyOutlineExport() {
    const r = await PR.bridge.call("copy_outline_export", true);
    if (r && r.ok) toast("Outline library copied — paste into any LLM");
    else toast((r && r.error) || "Copy failed", { bad: true });
  }
  async function copyOutlineRequest() {
    const r = await PR.bridge.call("copy_text", OUTLINE_REQUEST);
    if (r && r.ok) toast("Outline request copied — paste it into any LLM");
    else toast((r && r.error) || "Copy failed", { bad: true });
  }
  async function saveFile() {
    PR.state.suppressBlur = true;
    const r = await PR.bridge.call("save_export_file", false);
    PR.state.suppressBlur = false;
    if (r && r.ok && !r.cancelled) toast("Saved");
  }
  async function saveOutlineFile() {
    PR.state.suppressBlur = true;
    const r = await PR.bridge.call("save_outline_file");
    PR.state.suppressBlur = false;
    if (r && r.ok && !r.cancelled) toast("Outline saved");
  }
  async function loadFile() {
    PR.state.suppressBlur = true;
    const r = await PR.bridge.call("load_import_file");
    PR.state.suppressBlur = false;
    if (r && r.ok && r.text) { pasteArea.value = r.text; preview(); }
  }
  async function pasteClipboard() {
    const r = await PR.bridge.call("get_clipboard_text");
    const text = r && r.ok ? (r.text || "").trim() : "";
    if (!text) {
      toast((r && r.error) || "Clipboard is empty", { bad: true });
      return;
    }
    pasteArea.value = r.text;
    await preview();
  }
  function insertOutlineExample() {
    pasteArea.value = EXAMPLE_OUTLINE;
    previewBox.innerHTML = "";
    delete previewBox.dataset.ready;
    syncMergeState();
    pasteArea.focus();
    toast("Outline example inserted");
  }

  async function preview() {
    const text = pasteArea.value.trim();
    if (!text) { toast("Paste an outline or JSON first", { bad: true }); return; }
    const r = await PR.bridge.call("merge_preview", text);
    if (!r || !r.ok) {
      const message = (r && r.error) || "Could not read import";
      toast(message, { bad: true });
      renderImportError(message);
      delete previewBox.dataset.ready;
      syncMergeState();
      return;
    }
    renderPreview(r.preview);
    previewBox.dataset.ready = "1";
    syncMergeState();
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
    if (pv.new_categories.length) previewBox.appendChild(newCategoryPreview(pv.new_categories));

    const list = el("div", { class: "diff-list" });
    pv.updated.forEach((it) => list.appendChild(diffItem("upd", it)));
    pv.added.forEach((it) => list.appendChild(diffItem("add", it)));
    if (!pv.updated.length && !pv.added.length) {
      list.appendChild(el("div", { class: "txt-muted", style: { fontSize: "12.5px", padding: "8px 2px" },
        text: "Nothing would change — the incoming library matches what you have." }));
    }
    previewBox.appendChild(list);
  }

  function renderImportError(message) {
    previewBox.innerHTML = "";
    previewBox.appendChild(el("div", { class: "import-error-card" }, [
      el("div", { class: "import-error-title", text: "Import not readable" }),
      el("div", { class: "import-error-detail", text: message }),
      el("div", { class: "import-error-formats", text: "Expected an outline, JSON, YAML-style list, or Markdown table." }),
      el("pre", { class: "import-error-example", text:
        "Section: Coding\n" +
        "Subsection: Debugging\n" +
        "Bug sweep: Review {code} for edge cases, broken assumptions, and missing tests." }),
      el("button", { class: "btn btn-ghost", text: "Insert example", onclick: insertOutlineExample }),
    ]));
  }

  function newCategoryPreview(categories) {
    const limit = 8;
    const shown = categories.slice(0, limit);
    const chips = [
      el("span", { class: "newcat-label", text: "New sections" }),
      ...shown.map((name) => el("span", { class: "diff-cat-chip", text: name })),
    ];
    if (categories.length > limit) {
      chips.push(el("span", { class: "diff-cat-chip more", text: "+" + (categories.length - limit) + " more" }));
    }
    return el("div", { class: "diff-newcats" }, chips);
  }

  function diffItem(kind, it) {
    const changes = it.changes ? Object.keys(it.changes).join(", ") : "";
    const matchLabel = it.matched_by === "title" ? "matched by title" : "";
    return el("div", { class: "diff-item" }, [
      el("div", { class: "di-top" }, [
        el("span", { class: "di-badge " + kind, text: kind === "add" ? "NEW" : "UPD" }),
        el("span", { class: "di-title", text: it.title || "Untitled" }),
        matchLabel ? el("span", { class: "di-match", text: matchLabel }) : null,
        el("span", { class: "di-cat", text: it.category_name || "" }),
      ]),
      changes ? el("div", { class: "di-changes", text: "changes: " + changes }) : null,
    ]);
  }

  async function apply() {
    const text = pasteArea.value.trim();
    const upd = optUpdate ? optUpdate.checked : true;
    const add = optAdd ? optAdd.checked : true;
    if (!upd && !add) {
      toast("Choose Add new or Update existing", { bad: true });
      return;
    }
    const r = await PR.bridge.call("apply_merge", text, upd, add);
    if (r && r.ok) {
      await PR.app.refreshState();
      const res = r.result || {};
      toast(`Merged into library: ${res.updated || 0} updated, ${res.added || 0} added`);
      pasteArea.value = "";
      previewBox.innerHTML = "";
      delete previewBox.dataset.ready;
      syncMergeState();
    } else toast((r && r.error) || "Merge failed", { bad: true });
  }

  function syncMergeState() {
    if (!applyBtn || !previewBox) return;
    const hasPreview = previewBox.dataset.ready === "1";
    const canApply = (!optUpdate || optUpdate.checked) || (!optAdd || optAdd.checked);
    applyBtn.disabled = !hasPreview || !canApply;
    if (!mergeNote) return;
    if (!hasPreview) mergeNote.textContent = "Preview an import first";
    else if (!canApply) mergeNote.textContent = "Choose at least one merge action";
    else mergeNote.textContent = "Adds and updates only";
  }

  function replaceAll() {
    const text = pasteArea.value.trim();
    if (!text) { toast("Paste the replacement library first", { bad: true }); return; }
    PR.ui.confirmDialog({
      title: "Replace the entire library?",
      message: "This discards your current library and replaces it with the pasted import. Use Merge for normal appends. A backup is saved first, but this can't be undone in-app.",
      confirmText: "Replace everything", danger: true,
      onConfirm: async () => {
        const r = await PR.bridge.call("replace_all", text);
        if (r && r.ok) { await PR.app.refreshState(); toast("Library replaced"); pasteArea.value = ""; previewBox.innerHTML = ""; }
        else toast((r && r.error) || "Failed", { bad: true });
      },
    });
  }

  function editOutlineInstructions() {
    PR.state.suppressBlur = true;
    const ta = el("textarea", { class: "textarea", style: { minHeight: "220px" } });
    ta.value = (PR.state.settings.bulk_improve && PR.state.settings.bulk_improve.outline_prompt) || "";
    const save = el("button", { class: "btn btn-primary", text: "Save instructions" });
    const cancel = el("button", { class: "btn btn-ghost", text: "Cancel", onclick: () => { PR.ui.closeModal(); PR.state.suppressBlur = false; } });
    const m = PR.ui.modal({ title: "Outline AI instructions", wide: true,
      body: el("div", {}, [
        el("p", { class: "hint", style: { marginBottom: "8px" }, html: "Used by <b>Copy outline library</b> and <b>Improve with AI now</b>. The app adds your outline library after this text." }),
        ta ]),
      footer: [cancel, save], onClose: () => { PR.state.suppressBlur = false; } });
    save.addEventListener("click", async () => {
      await PR.bridge.call("update_settings", { bulk_improve: { outline_prompt: ta.value } });
      PR.state.settings.bulk_improve = { ...(PR.state.settings.bulk_improve || {}), outline_prompt: ta.value };
      m.close(); toast("Outline instructions saved");
    });
  }

  function editJsonInstructions() {
    PR.state.suppressBlur = true;
    const ta = el("textarea", { class: "textarea", style: { minHeight: "200px" } });
    ta.value = (PR.state.settings.bulk_improve && PR.state.settings.bulk_improve.meta_prompt) || "";
    const save = el("button", { class: "btn btn-primary", text: "Save instructions" });
    const cancel = el("button", { class: "btn btn-ghost", text: "Cancel", onclick: () => { PR.ui.closeModal(); PR.state.suppressBlur = false; } });
    const m = PR.ui.modal({ title: "JSON AI instructions", wide: true,
      body: el("div", {}, [
        el("p", { class: "hint", style: { marginBottom: "8px" }, html: "Prepended before your JSON when you click <b>Copy for AI</b>. The simpler default loop uses <b>Copy outline library</b>." }),
        ta ]),
      footer: [cancel, save], onClose: () => { PR.state.suppressBlur = false; } });
    save.addEventListener("click", async () => {
      await PR.bridge.call("update_settings", { bulk_improve: { meta_prompt: ta.value } });
      PR.state.settings.bulk_improve = { ...(PR.state.settings.bulk_improve || {}), meta_prompt: ta.value };
      m.close(); toast("JSON instructions saved");
    });
  }

  PR.bulk = { render };
})();
