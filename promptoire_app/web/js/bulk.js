/* bulk.js — the outline/JSON ⇄ LLM "improve my whole library" loop */
(function () {
  "use strict";
  const PR = window.PROMPTOIRE;
  const { el, icon, toast, escapeHtml } = PR.ui;

  const OPENAI_MODELS = [
    { id: "gpt-5.6", label: "GPT-5.6 · recommended alias" },
    { id: "gpt-5.6-sol", label: "GPT-5.6 sol · highest capability" },
    { id: "gpt-5.6-terra", label: "GPT-5.6 terra · balanced" },
    { id: "gpt-5.6-luna", label: "GPT-5.6 luna · fast and efficient" },
  ];

  const OUTLINE_REQUEST =
    "Create a batch of prompts for my Promptoire library using this simple import outline format.\n\n" +
    "Rules:\n" +
    "- Return only the outline. Do not wrap it in a code fence.\n" +
    "- Use # headings, Path: Section > Subsection > Nested subsection, Section/Subsection labels, or indentation for nested sections.\n" +
    "- Nested bullet outlines are fine: - Section, - Subsection, - Prompt title: prompt body.\n" +
    "- Markdown prompt headings are fine: ### Prompt title followed by the prompt body.\n" +
    "- For deeper labels, use Sub-subsection: or Nested subsection:.\n" +
    "- Use prompt rows like: Title: Prompt body\n" +
    "- Numbered blocks like Prompt 1: are fine when a prompt needs multiple lines.\n" +
    "- YAML-style lists like - Title: ... with indented Prompt:/Tags: fields are fine.\n" +
    "- Markdown tables and CSV tables are fine if they include Title and Prompt columns.\n" +
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

  let pasteArea, previewBox, applyBtn, optUpdate, optAdd, mergeNote, lastPreview;
  let instructionsArea, aiKeyField, aiModelField;

  function render() {
    const host = document.getElementById("bulkBody");
    host.innerHTML = "";

    host.appendChild(el("p", { class: "bulk-intro", html:
      "Improve or share your <b>entire</b> prompt library with any LLM, then safely merge the result back. " +
      "Promptoire matches an id first, otherwise the same title in the same section." }));

    instructionsArea = el("textarea", { class: "textarea instructions-area", id: "outlineInstructions",
      "aria-label": "Improvement instructions", spellcheck: "true" });
    instructionsArea.value = (PR.state.settings.bulk_improve && PR.state.settings.bulk_improve.outline_prompt) || "";
    instructionsArea.addEventListener("change", () => persistOutlineInstructions(false));

    // STEP 1 — export
    const step1 = el("div", { class: "step" }, [
      el("div", { class: "step-head" }, [
        el("span", { class: "step-num", text: "1" }),
        el("div", {}, [ el("div", { class: "t", text: "Improve or export your library" }),
          el("div", { class: "d", text: "Use OpenAI directly, or copy a clean request to any LLM." }) ]),
      ]),
      el("div", { class: "ai-direct" }, [
        el("button", { class: "btn btn-primary ai-go",
          html: '<svg viewBox="0 0 24 24" class="ic" style="fill:currentColor;stroke-width:.6"><path d="M13 2L3 14h7l-1 8 10-12h-7z"/></svg> Improve with AI now',
          onclick: improveNow }),
        el("span", { class: "ai-direct-hint", id: "aiHint", text: "Optional · uses your own OpenAI API key" }),
      ]),
      el("div", { class: "instructions-block" }, [
        el("label", { class: "instructions-label", for: "outlineInstructions", text: "Improvement instructions" }),
        instructionsArea,
        el("div", { class: "instructions-hint", text: "These instructions go first; your complete outline library is appended below." }),
        el("div", { class: "btn-row instructions-actions" }, [
          el("button", { class: "btn btn-sm", text: "Save instructions", onclick: () => persistOutlineInstructions(true) }),
          el("button", { class: "btn btn-sm btn-ghost", text: "Reset default", onclick: resetOutlineInstructions }),
          el("button", { class: "btn btn-sm btn-ghost", html: icon("copy") + " Copy instructions only", onclick: copyInstructionsOnly }),
        ]),
      ]),
      el("div", { class: "btn-row" }, [
        el("button", { class: "btn btn-primary", html: icon("copy") + " Copy instructions + library", onclick: () => copyOutlineExport(true) }),
        el("button", { class: "btn", html: icon("copy") + " Copy library only", onclick: () => copyOutlineExport(false) }),
        el("button", { class: "btn btn-ghost", text: "Save library outline", onclick: saveOutlineFile }),
      ]),
      el("details", { class: "export-more" }, [
        el("summary", { text: "More options" }),
        el("div", { class: "btn-row" }, [
          el("button", { class: "btn", text: "Create prompts for a topic…", onclick: copyOutlineRequest }),
          el("button", { class: "btn", html: icon("copy") + " Copy JSON request + library", onclick: copyForAI }),
          el("button", { class: "btn", text: "Copy JSON only", onclick: () => copyExport(false) }),
          el("button", { class: "btn btn-ghost", text: "Save .json", onclick: saveFile }),
          el("button", { class: "btn btn-ghost", text: "Edit JSON instructions", onclick: editJsonInstructions }),
        ]),
      ]),
    ]);

    // STEP 2 — import
    pasteArea = el("textarea", { class: "textarea", style: { minHeight: "150px" },
      placeholder: "Paste an improved outline, or JSON:\n\nCoding\n  Debugging\n    Bug sweep: Review this code for edge cases, broken assumptions, and missing tests.\n\nPath: AI Art > Characters > Portraits\nTitle: Cinematic portrait\nType: image\nPrompt: A dramatic 85mm portrait of {subject}...\nNegative prompt: blurry, watermark\nParameters: --ar 4:5" });
    pasteArea.addEventListener("input", () => {
      previewBox.innerHTML = "";
      delete previewBox.dataset.ready;
      lastPreview = null;
      syncMergeState();
    });
    pasteArea.addEventListener("paste", () => {
      setTimeout(() => {
        if (pasteArea.value.trim()) preview();
      }, 0);
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
        el("button", { class: "btn btn-ghost", text: "Clear", onclick: clearImport }),
        el("button", { class: "btn btn-primary", html: icon("check") + " Preview changes", onclick: preview }),
      ]),
    ]);

    // preview + apply
    previewBox = el("div", {});
    mergeNote = el("div", { class: "merge-note", text: "Preview an import first" });
    const opts = el("div", { class: "merge-options" }, [
      toggleInline("Update existing", "Replace changed, nonblank fields on exact matches; never move or delete.", true,
        (r) => (optUpdate = r), syncMergeState),
      toggleInline("Add new", "Add only unmatched prompts and create any missing section path.", true,
        (r) => (optAdd = r), syncMergeState),
    ]);
    applyBtn = el("button", { class: "btn btn-primary", html: icon("check") + " Merge into library", disabled: "disabled",
      onclick: apply });
    const mergeCard = el("div", { class: "merge-card" }, [
      el("div", { class: "merge-head" }, [
        el("div", { class: "merge-title", text: "Safe merge" }),
        mergeNote,
      ]),
      opts,
      el("div", { class: "merge-safety", text: "Blank imported fields never erase local content. Duplicate or ambiguous matches are skipped." }),
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
    host.appendChild(openAiSettings());
    syncMergeState();
  }

  function toggleInline(label, description, checked, ref, onChange) {
    const input = el("input", { type: "checkbox" });
    input.checked = checked;
    if (ref) ref(input);
    if (onChange) input.addEventListener("change", onChange);
    return el("label", { class: "merge-option" }, [
      wrapSwitch(input),
      el("span", {}, [el("span", { class: "merge-option-title", text: label }),
        el("span", { class: "merge-option-desc", text: description })]),
    ]);
  }
  function wrapSwitch(input) {
    return el("span", { class: "switch" }, [input, el("span", { class: "track" }), el("span", { class: "knob" })]);
  }

  async function improveNow(e) {
    const btn = e.currentTarget;
    if (!await persistOutlineInstructions(true)) return;
    if (!await saveAiSettings(false)) return;
    const ai = PR.state.settings.ai || {};
    if (!ai.api_key) {
      const panel = document.getElementById("aiSettings");
      if (panel) panel.open = true;
      toast("Add your OpenAI API key below first", { bad: true });
      setTimeout(() => {
        if (panel) panel.scrollIntoView({ block: "center", behavior: "smooth" });
        if (aiKeyField) aiKeyField.focus();
      }, 80);
      return;
    }
    const hint = document.getElementById("aiHint");
    btn.disabled = true;
    const orig = btn.innerHTML;
    btn.innerHTML = '<span class="spinner"></span> Improving…';
    if (hint) hint.textContent = "Calling OpenAI · " + (ai.model || "gpt-5.6") + "…";
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
  async function copyOutlineExport(includeInstructions) {
    if (includeInstructions && !await persistOutlineInstructions(true)) return;
    const r = await PR.bridge.call("copy_outline_export", !!includeInstructions);
    if (r && r.ok) toast(includeInstructions
      ? "Instructions + library copied — paste into any LLM"
      : "Library outline copied");
    else toast((r && r.error) || "Copy failed", { bad: true });
  }
  async function copyInstructionsOnly() {
    const text = String((instructionsArea && instructionsArea.value) || "").trim();
    if (!text) { toast("Add instructions first", { bad: true }); return; }
    const r = await PR.bridge.call("copy_text", text);
    if (r && r.ok) toast("Instructions copied");
    else toast((r && r.error) || "Copy failed", { bad: true });
  }
  async function persistOutlineInstructions(showToast) {
    if (!instructionsArea) return true;
    const value = instructionsArea.value.trim();
    if (!value) {
      if (showToast) toast("Improvement instructions cannot be blank", { bad: true });
      return false;
    }
    const current = (PR.state.settings.bulk_improve && PR.state.settings.bulk_improve.outline_prompt) || "";
    if (value === current) {
      if (showToast) toast("Instructions already saved");
      return true;
    }
    const r = await PR.bridge.call("update_settings", { bulk_improve: { outline_prompt: value } });
    if (!r || !r.ok) {
      toast((r && r.error) || "Could not save instructions", { bad: true });
      return false;
    }
    PR.state.settings = r.settings || PR.state.settings;
    PR.state.settings.bulk_improve = { ...(PR.state.settings.bulk_improve || {}), outline_prompt: value };
    if (showToast) toast("Improvement instructions saved");
    return true;
  }
  async function resetOutlineInstructions() {
    const r = await PR.bridge.call("bulk_prompt_defaults");
    if (!r || !r.ok) {
      toast((r && r.error) || "Could not load default instructions", { bad: true });
      return;
    }
    instructionsArea.value = r.outline_prompt || "";
    if (await persistOutlineInstructions(false)) toast("Default instructions restored");
  }
  function buildOutlineRequest(topic) {
    const clean = String(topic || "").trim();
    return OUTLINE_REQUEST + (clean ? clean + "\n" : "");
  }
  function copyOutlineRequest() {
    PR.state.suppressBlur = true;
    const topic = el("textarea", { class: "textarea", style: { minHeight: "92px" },
      placeholder: "e.g. onboarding email sequence, code review workflow, fantasy map prompts" });
    const copyBtn = el("button", { class: "btn btn-primary", text: "Copy request" });
    const blankBtn = el("button", { class: "btn btn-ghost", text: "Copy blank" });
    const cancelBtn = el("button", { class: "btn btn-ghost", text: "Cancel", onclick: () => { m.close(); } });
    const m = PR.ui.modal({ title: "Prompt batch request",
      body: el("div", { class: "field" }, [el("label", { text: "Topic or workflow" }), topic]),
      footer: [blankBtn, cancelBtn, copyBtn], onClose: () => { PR.state.suppressBlur = false; } });
    setTimeout(() => topic.focus(), 40);
    copyBtn.addEventListener("click", () => copyOutlineRequestText(buildOutlineRequest(topic.value), m));
    blankBtn.addEventListener("click", () => copyOutlineRequestText(buildOutlineRequest(""), m));
  }
  async function copyOutlineRequestText(text, modal) {
    const r = await PR.bridge.call("copy_text", text);
    if (r && r.ok) {
      modal.close();
      toast("Outline request copied — paste it into any LLM");
    } else {
      toast((r && r.error) || "Copy failed", { bad: true });
    }
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
    lastPreview = null;
    syncMergeState();
    pasteArea.focus();
    toast("Outline example inserted");
  }
  function clearImport() {
    pasteArea.value = "";
    previewBox.innerHTML = "";
    delete previewBox.dataset.ready;
    lastPreview = null;
    syncMergeState();
    pasteArea.focus();
    toast("Import cleared");
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
      lastPreview = null;
      syncMergeState();
      return;
    }
    renderPreview(r.preview);
    previewBox.dataset.ready = "1";
    syncMergeState();
  }

  function renderPreview(pv) {
    previewBox.innerHTML = "";
    lastPreview = pv || null;
    const duplicates = pv.duplicates || [];
    const ambiguous = pv.ambiguous || [];
    const incomingTotal = Number.isFinite(Number(pv.incoming_total))
      ? Number(pv.incoming_total)
      : (pv.added.length + pv.updated.length + pv.unchanged_count);
    const summary = el("div", { class: "diff-summary" }, [
      el("span", { class: "diff-pill total", text: incomingTotal + " incoming" }),
      el("span", { class: "diff-pill add", text: pv.added.length + " new" }),
      el("span", { class: "diff-pill upd", text: pv.updated.length + " updated" }),
      el("span", { class: "diff-pill same", text: pv.unchanged_count + " unchanged" }),
      pv.new_categories.length ? el("span", { class: "diff-pill", text: pv.new_categories.length + " new categories" }) : null,
      duplicates.length ? el("span", { class: "diff-pill skip", text: duplicates.length + " duplicate skipped" }) : null,
      ambiguous.length ? el("span", { class: "diff-pill warn", text: ambiguous.length + " ambiguous skipped" }) : null,
    ]);
    previewBox.appendChild(summary);
    if (pv.new_categories.length) previewBox.appendChild(newCategoryPreview(pv.new_categories));
    if (duplicates.length || ambiguous.length) {
      const parts = [];
      if (duplicates.length) parts.push(duplicates.length + " repeated incoming " + (duplicates.length === 1 ? "prompt was" : "prompts were") + " ignored");
      if (ambiguous.length) parts.push(ambiguous.length + " prompt " + (ambiguous.length === 1 ? "matched" : "matched") + " more than one local item and was skipped");
      previewBox.appendChild(el("div", { class: "diff-warning", text: parts.join("; ") + "." }));
    }

    const list = el("div", { class: "diff-list" });
    pv.updated.forEach((it) => list.appendChild(diffItem("upd", it)));
    pv.added.forEach((it) => list.appendChild(diffItem("add", it)));
    if (!pv.updated.length && !pv.added.length) {
      list.appendChild(el("div", { class: "txt-muted", style: { fontSize: "12.5px", padding: "8px 2px" },
        text: duplicates.length || ambiguous.length
          ? "No unambiguous changes are available to merge."
          : "Nothing would change — the incoming library matches what you have." }));
    }
    previewBox.appendChild(list);
  }

  function renderImportError(message) {
    previewBox.innerHTML = "";
    lastPreview = null;
    previewBox.appendChild(el("div", { class: "import-error-card" }, [
      el("div", { class: "import-error-title", text: "Import not readable" }),
      el("div", { class: "import-error-detail", text: message }),
      el("div", { class: "import-error-formats", text: "Expected an outline, JSON, YAML-style list, Markdown table, or CSV table." }),
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
    if (previewBox && previewBox.dataset.ready === "1" && lastPreview) {
      const selected = selectedChangeCount(upd, add);
      if (!selected) {
        toast("No selected changes to merge", { bad: true });
        return;
      }
    }
    const r = await PR.bridge.call("apply_merge", text, upd, add);
    if (r && r.ok) {
      await PR.app.refreshState();
      const res = r.result || {};
      const skipped = (res.duplicates_skipped || 0) + (res.ambiguous_skipped || 0);
      toast(`Merged into library: ${res.updated || 0} updated, ${res.added || 0} added` +
        (skipped ? `, ${skipped} safely skipped` : ""));
      pasteArea.value = "";
      previewBox.innerHTML = "";
      delete previewBox.dataset.ready;
      lastPreview = null;
      syncMergeState();
    } else toast((r && r.error) || "Merge failed", { bad: true });
  }

  function selectedChangeCount(updateSelected, addSelected) {
    if (!lastPreview) return 0;
    return (updateSelected ? (lastPreview.updated || []).length : 0) +
      (addSelected ? (lastPreview.added || []).length : 0);
  }

  function syncMergeState() {
    if (!applyBtn || !previewBox) return;
    const hasPreview = previewBox.dataset.ready === "1";
    const updateSelected = !optUpdate || optUpdate.checked;
    const addSelected = !optAdd || optAdd.checked;
    const canApply = updateSelected || addSelected;
    const selectedChanges = hasPreview ? selectedChangeCount(updateSelected, addSelected) : 0;
    applyBtn.disabled = !hasPreview || !canApply || selectedChanges === 0;
    if (!mergeNote) return;
    if (!hasPreview) mergeNote.textContent = "Preview an import first";
    else if (!canApply) mergeNote.textContent = "Choose at least one merge action";
    else if (!selectedChanges) mergeNote.textContent = "No selected changes to merge";
    else if (updateSelected && !addSelected) mergeNote.textContent = "Updates existing only";
    else if (addSelected && !updateSelected) mergeNote.textContent = "Adds new only";
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
        if (r && r.ok) { await PR.app.refreshState(); toast("Library replaced"); pasteArea.value = ""; previewBox.innerHTML = ""; lastPreview = null; }
        else toast((r && r.error) || "Failed", { bad: true });
      },
    });
  }

  function editJsonInstructions() {
    PR.state.suppressBlur = true;
    const ta = el("textarea", { class: "textarea", style: { minHeight: "200px" } });
    ta.value = (PR.state.settings.bulk_improve && PR.state.settings.bulk_improve.meta_prompt) || "";
    const save = el("button", { class: "btn btn-primary", text: "Save instructions" });
    const reset = el("button", { class: "btn btn-ghost", text: "Reset default" });
    const cancel = el("button", { class: "btn btn-ghost", text: "Cancel", onclick: () => { PR.ui.closeModal(); PR.state.suppressBlur = false; } });
    const m = PR.ui.modal({ title: "JSON AI instructions", wide: true,
      body: el("div", {}, [
        el("p", { class: "hint", style: { marginBottom: "8px" }, html: "Prepended before your JSON when you click <b>Copy JSON request + library</b>. The simpler default uses the readable outline buttons above." }),
        ta ]),
      footer: [reset, cancel, save], onClose: () => { PR.state.suppressBlur = false; } });
    reset.addEventListener("click", async () => {
      const r = await PR.bridge.call("bulk_prompt_defaults");
      if (r && r.ok) { ta.value = r.meta_prompt || ""; toast("Default JSON instructions loaded"); }
      else toast((r && r.error) || "Could not load default instructions", { bad: true });
    });
    save.addEventListener("click", async () => {
      await PR.bridge.call("update_settings", { bulk_improve: { meta_prompt: ta.value } });
      PR.state.settings.bulk_improve = { ...(PR.state.settings.bulk_improve || {}), meta_prompt: ta.value };
      m.close(); toast("JSON instructions saved");
    });
  }

  function openAiSettings() {
    const ai = PR.state.settings.ai || {};
    const currentModel = OPENAI_MODELS.some((m) => m.id === ai.model) ? ai.model : "gpt-5.6";
    const details = el("details", { class: "ai-settings", id: "aiSettings" });
    details.appendChild(el("summary", {}, [
      el("span", { text: "OpenAI connection · optional" }),
      el("span", { class: "ai-status", text: ai.api_key ? currentModel + " · key saved locally" : "not configured" }),
    ]));

    aiKeyField = el("input", { class: "input", type: "password", id: "aiKeyField",
      value: ai.api_key || "", placeholder: "sk-…", autocomplete: "off", spellcheck: "false" });
    aiModelField = el("select", { class: "input", id: "aiModelField", "aria-label": "OpenAI model" });
    OPENAI_MODELS.forEach((model) => aiModelField.appendChild(el("option", { value: model.id, text: model.label })));
    aiModelField.value = currentModel;

    const saveButton = el("button", { class: "btn btn-primary btn-sm", type: "submit", text: "Save OpenAI settings" });
    aiKeyField.addEventListener("change", () => saveAiSettings(false));
    aiModelField.addEventListener("change", () => saveAiSettings(false));

    details.appendChild(el("form", { class: "ai-settings-body", onsubmit: (event) => {
      event.preventDefault();
      saveAiSettings(true);
    } }, [
      el("p", { class: "hint", html: "Only needed for <b>Improve with AI now</b>. Manual copy/paste works without an account or key. Your key stays in Promptoire's local settings file and is sent only to OpenAI when you click the button." }),
      el("div", { class: "field" }, [el("label", { for: "aiKeyField", text: "OpenAI API key" }), aiKeyField]),
      el("div", { class: "field" }, [el("label", { for: "aiModelField", text: "Model" }), aiModelField]),
      el("div", { class: "ai-model-note", text: "GPT-5.6 follows OpenAI's recommended alias; choose a fixed family member when you want stable cost/capability behavior." }),
      el("div", { class: "btn-row" }, [saveButton]),
    ]));
    return details;
  }

  async function saveAiSettings(showToast) {
    if (!aiKeyField || !aiModelField) return true;
    const patch = { ai: {
      provider: "openai",
      api_key: aiKeyField.value.trim(),
      model: aiModelField.value || "gpt-5.6",
      base_url: "",
    } };
    const r = await PR.bridge.call("update_settings", patch);
    if (!r || !r.ok) {
      toast((r && r.error) || "Could not save OpenAI settings", { bad: true });
      return false;
    }
    PR.state.settings = r.settings || { ...PR.state.settings, ai: patch.ai };
    if (showToast) toast("OpenAI settings saved locally");
    const status = document.querySelector("#aiSettings .ai-status");
    if (status) status.textContent = patch.ai.api_key
      ? patch.ai.model + " · key saved locally"
      : "not configured";
    return true;
  }

  PR.bulk = { render };
})();
