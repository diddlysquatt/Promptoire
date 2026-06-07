/* app.js — bootstrap, routing, global keys, Python<->JS hooks */
(function () {
  "use strict";
  const PR = window.PROMPTOIRE;

  const views = { launcher: "viewLauncher", editor: "viewEditor", bulk: "viewBulk", settings: "viewSettings" };

  async function boot() {
    await PR.bridge.ready();
    await refreshState();
    applyTheme();
    PR.launcher.init();
    wireChrome();
    wireGlobalKeys();
    wireBlur();
    showView("launcher");
    await PR.launcher.runSearch();
    PR.launcher.focusSearch();
    if (PR.bridge.isMock()) {
      document.getElementById("brandCount").textContent = "· preview";
    }
    // Real-app self-test hook. Harmless no-op unless Python runs with --selftest.
    // Called directly (not via PR.bridge) so it also reports when the bridge
    // itself would fall back to mock.
    try {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.selftest_report) {
        const s = PR.state.stats || {};
        const api = window.pywebview.api;
        window.pywebview.api.selftest_report({
          cards: document.querySelectorAll(".card").length,
          total: s.total || 0,
          cats: (PR.state.categories || []).length,
          mock: PR.bridge.isMock(),
          theme: document.documentElement.getAttribute("data-theme"),
          first: (document.querySelector(".card-title") || {}).textContent || "",
          get_state_type: typeof api.get_state,
          api_count: Object.keys(api).length,
        });
      }
    } catch (e) { /* ignore */ }
  }

  async function refreshState() {
    const st = await PR.bridge.call("get_state");
    if (st && st.ok) {
      PR.state.categories = st.categories || [];
      PR.state.settings = st.settings || {};
      PR.state.stats = st.stats || {};
      PR.state.version = st.version || "";
      PR.state.platform = st.platform || "windows";
      PR.state.hotkeyAvailable = !!st.hotkey_available;
      updateCount();
    }
  }

  function updateCount() {
    const s = PR.state.stats || {};
    const elc = document.getElementById("brandCount");
    if (elc && !PR.bridge.isMock()) elc.textContent = s.total != null ? "· " + s.total : "";
  }

  function applyTheme() {
    const t = (PR.state.settings && PR.state.settings.theme) || "matrix";
    document.documentElement.setAttribute("data-theme", t);
    const op = PR.state.settings && PR.state.settings.window && PR.state.settings.window.opacity;
    if (op != null) document.querySelector(".app").style.opacity = "";
  }

  function showView(name) {
    PR.state.view = name;
    Object.entries(views).forEach(([k, id]) => document.getElementById(id).classList.toggle("hidden", k !== name));
    document.getElementById("btnEditor").classList.toggle("is-on", name === "editor");
    document.getElementById("btnImprove").classList.toggle("is-on", name === "bulk");
    document.getElementById("btnSettings").classList.toggle("is-on", name === "settings");
    if (name === "editor") PR.editor.render();
    else if (name === "bulk") PR.bulk.render();
    else if (name === "settings") PR.settings.render();
    else setTimeout(() => PR.launcher.focusSearch(), 30);
  }

  function wireChrome() {
    const go = (v) => () => showView(PR.state.view === v ? "launcher" : v);
    document.getElementById("btnEditor").addEventListener("click", go("editor"));
    document.getElementById("btnImprove").addEventListener("click", go("bulk"));
    document.getElementById("btnImprove2").addEventListener("click", () => showView("bulk"));
    document.getElementById("btnSettings").addEventListener("click", go("settings"));
    document.getElementById("btnAdd").addEventListener("click", () => PR.editor.newPrompt(null));
    document.getElementById("btnClose").addEventListener("click", () => PR.bridge.call("hide_window"));

    const pin = document.getElementById("btnPin");
    pin.addEventListener("click", () => {
      PR.state.pinned = !PR.state.pinned;
      pin.classList.toggle("is-on", PR.state.pinned);
      pin.setAttribute("aria-pressed", String(PR.state.pinned));
      PR.ui.toast(PR.state.pinned ? "Pinned — won't auto-hide" : "Unpinned");
    });

    document.querySelectorAll("[data-back]").forEach((b) => b.addEventListener("click", () => showView("launcher")));
  }

  function wireGlobalKeys() {
    document.addEventListener("keydown", (e) => {
      // Escape: back to launcher, else hide
      if (e.key === "Escape") {
        if (document.getElementById("modalHost").classList.contains("hidden") === false) { PR.ui.closeModal(); return; }
        if (PR.state.view !== "launcher") { showView("launcher"); return; }
        if (!PR.state.pinned) PR.bridge.call("hide_window");
        return;
      }
      const mod = e.ctrlKey || e.metaKey;
      if (mod && e.key === "f") { e.preventDefault(); showView("launcher"); PR.launcher.focusSearch(); }
      else if (mod && e.key === "e") { e.preventDefault(); showView(PR.state.view === "editor" ? "launcher" : "editor"); }
      else if (mod && e.key === "i") { e.preventDefault(); showView(PR.state.view === "bulk" ? "launcher" : "bulk"); }
      else if (mod && e.key === ",") { e.preventDefault(); showView(PR.state.view === "settings" ? "launcher" : "settings"); }
      else if (mod && e.key === "n") { e.preventDefault(); PR.editor.newPrompt(null); }
    });
  }

  function wireBlur() {
    window.addEventListener("blur", () => {
      // Only the quick launcher auto-hides; respect pin, modals and native dialogs.
      setTimeout(() => {
        const beh = PR.state.settings.behavior || {};
        if (!beh.hide_on_blur) return;
        if (PR.state.pinned || PR.state.suppressBlur) return;
        if (PR.state.view !== "launcher") return;
        if (document.getElementById("modalHost").classList.contains("hidden") === false) return;
        if (document.hasFocus()) return;
        PR.bridge.call("hide_window");
      }, 120);
    });
  }

  /* ---- hooks Python calls ------------------------------------------------ */
  PR.app = {
    refreshState,
    showView,
    onShown() { showView("launcher"); PR.launcher.runSearch().then(() => PR.launcher.focusSearch()); },
    openSettings() { showView("settings"); },
    onSettingsChanged() { refreshState().then(applyTheme); },
  };
  PR.onShown = PR.app.onShown;
  PR.openSettings = PR.app.openSettings;
  PR.onSettingsChanged = PR.app.onSettingsChanged;

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
