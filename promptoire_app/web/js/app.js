/* app.js — bootstrap, routing, global keys, Python<->JS hooks */
(function () {
  "use strict";
  const PR = window.PROMPTOIRE;

  const views = { launcher: "viewLauncher", editor: "viewEditor", bulk: "viewBulk", settings: "viewSettings" };
  const DENSITIES = ["comfortable", "compact", "titles"];
  const DENSITY_NAMES = { comfortable: "Comfortable", compact: "Compact", titles: "Titles only" };
  const BACKGROUNDS = ["", "obsidian", "graphite", "midnight", "forest", "plum", "mist", "linen"];
  const FONTS = ["system", "rounded", "humanist", "mono"];

  async function boot() {
    let bootError = "";
    try {
      await PR.bridge.ready();
      await refreshState();
      applyTheme();
      PR.launcher.init();
      wireChrome();
      wireResizeHandles();
      wireGlobalKeys();
      wireBlur();
      showView("launcher");
      await PR.launcher.runSearch();
      PR.launcher.focusSearch();
      if (PR.bridge.isMock()) {
        document.getElementById("brandCount").textContent = "· preview";
      }
    } catch (e) {
      bootError = String((e && e.stack) || e);
    }
    selftestReport(bootError);
  }

  // Real-app self-test hook. Harmless no-op unless Python runs with --selftest.
  // Called directly (not via PR.bridge) and even when boot failed, so a broken
  // build reports its own error instead of timing out silently.
  function selftestReport(bootError) {
    try {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.selftest_report) {
        const s = PR.state.stats || {};
        const api = window.pywebview.api;
        window.pywebview.api.selftest_report({
          cards: document.querySelectorAll(".card").length,
          groups: document.querySelectorAll(".group").length,
          total: s.total || 0,
          cats: (PR.state.categories || []).length,
          mock: PR.bridge.isMock(),
          theme: document.documentElement.getAttribute("data-theme"),
          density: document.documentElement.getAttribute("data-density"),
          background: document.documentElement.getAttribute("data-background") || "theme",
          font: document.documentElement.getAttribute("data-font") || "system",
          first: (document.querySelector(".card-title") || {}).textContent || "",
          get_state_type: typeof api.get_state,
          api_count: Object.keys(api).length,
          error: bootError || "",
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
    applyAccent((PR.state.settings && PR.state.settings.accent) || "");
    applyBackground((PR.state.settings && PR.state.settings.background) || "");
    applyFont((PR.state.settings && PR.state.settings.font) || "system");
    applyDensity((PR.state.settings && PR.state.settings.density) || "compact");
  }

  function applyBackground(value) {
    const background = BACKGROUNDS.includes(value) ? value : "";
    if (background) document.documentElement.setAttribute("data-background", background);
    else document.documentElement.removeAttribute("data-background");
    return background;
  }

  function applyFont(value) {
    const font = FONTS.includes(value) ? value : "system";
    document.documentElement.setAttribute("data-font", font);
    return font;
  }

  function applyDensity(value) {
    const density = DENSITIES.includes(value) ? value : "compact";
    document.documentElement.setAttribute("data-density", density);
    const button = document.getElementById("btnDensity");
    if (button) {
      const name = DENSITY_NAMES[density];
      button.dataset.density = density;
      button.title = "Prompt density: " + name + " (click to change)";
      button.setAttribute("aria-label", "Prompt density: " + name + ". Click to change.");
    }
    return density;
  }

  function applyAccent(hex) {
    const root = document.documentElement;
    const value = String(hex || "").trim();
    if (!/^#[0-9a-fA-F]{6}$/.test(value)) {
      root.style.removeProperty("--accent");
      root.style.removeProperty("--accent-soft");
      root.style.removeProperty("--accent-glow");
      return;
    }
    const r = parseInt(value.slice(1, 3), 16);
    const g = parseInt(value.slice(3, 5), 16);
    const b = parseInt(value.slice(5, 7), 16);
    root.style.setProperty("--accent", value);
    root.style.setProperty("--accent-soft", `rgba(${r},${g},${b},0.16)`);
    root.style.setProperty("--accent-glow", `rgba(${r},${g},${b},0.45)`);
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
    document.getElementById("btnSettings").addEventListener("click", go("settings"));
    document.getElementById("btnCoffee").addEventListener("click", openCoffee);
    document.getElementById("btnAdd").addEventListener("click", () => PR.editor.newPrompt(null));
    document.getElementById("btnAddCategory").addEventListener("click", () => PR.editor.addCategory(null));
    document.getElementById("btnClose").addEventListener("click", () => PR.bridge.call("hide_window"));
    document.getElementById("btnDensity").addEventListener("click", cycleDensity);

    const pin = document.getElementById("btnPin");
    pin.addEventListener("click", () => {
      PR.state.pinned = !PR.state.pinned;
      pin.classList.toggle("is-on", PR.state.pinned);
      pin.setAttribute("aria-pressed", String(PR.state.pinned));
      pin.title = PR.state.pinned
        ? "Pinned open (enable auto-hide)"
        : "Keep open (disable auto-hide)";
      pin.setAttribute("aria-label", pin.title);
      PR.ui.toast(PR.state.pinned ? "Pinned — auto-hide disabled" : "Auto-hide enabled");
    });

    document.querySelectorAll("[data-back]").forEach((b) => b.addEventListener("click", () => showView("launcher")));
  }

  function cycleDensity() {
    const current = applyDensity((PR.state.settings && PR.state.settings.density) || "compact");
    const next = DENSITIES[(DENSITIES.indexOf(current) + 1) % DENSITIES.length];
    PR.state.settings.density = next;
    applyDensity(next);
    PR.bridge.call("update_settings", { density: next });
    PR.ui.toast("Prompt density: " + DENSITY_NAMES[next]);
  }

  function wireResizeHandles() {
    document.querySelectorAll("[data-resize]").forEach((handle) => {
      handle.addEventListener("pointerdown", async (e) => {
        if (e.button !== 0) return;
        e.preventDefault();
        e.stopPropagation();
        PR.state.suppressBlur = true;
        try {
          const result = await PR.bridge.call("begin_window_resize", handle.dataset.resize);
          if (result && result.ok && result.started === false) {
            PR.ui.toast("Window resizing could not start", { bad: true });
          }
        } finally {
          setTimeout(() => { PR.state.suppressBlur = false; }, 120);
        }
      });
    });
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
      if (mod && (e.key === "f" || e.key === "k")) { e.preventDefault(); showView("launcher"); PR.launcher.focusSearch(); }
      else if (mod && e.key === "e") { e.preventDefault(); showView(PR.state.view === "editor" ? "launcher" : "editor"); }
      else if (mod && e.key === "i") { e.preventDefault(); showView(PR.state.view === "bulk" ? "launcher" : "bulk"); }
      else if (mod && e.key === ",") { e.preventDefault(); showView(PR.state.view === "settings" ? "launcher" : "settings"); }
      else if (mod && e.key === "n") { e.preventDefault(); PR.editor.newPrompt(null); }
      else if (mod && "1234".includes(e.key) && PR.state.view === "launcher") {
        e.preventDefault();
        PR.launcher.setFilter(["all", "text", "image", "favorites"]["1234".indexOf(e.key)]);
      }
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

  function openCoffee() {
    const url = configuredCoffeeUrl();
    if (url) {
      PR.bridge.call("open_external", url);
      return;
    }
    PR.ui.toast("Support page is being set up");
  }

  function configuredCoffeeUrl() {
    const links = (PR.state.settings && PR.state.settings.links) || {};
    const url = normalizeUrl(links.coffee);
    if (!url) return "";
    try {
      const parsed = new URL(url);
      if (!["http:", "https:"].includes(parsed.protocol) || isGenericCoffeeUrl(parsed)) return "";
      return parsed.href;
    } catch (e) {
      return "";
    }
  }
  function normalizeUrl(raw) {
    const url = String(raw || "").trim();
    if (!url) return "";
    if (/^[a-z][a-z0-9+.-]*:\/\//i.test(url)) return url;
    if (/^[^\s/]+\.[^\s]+/i.test(url)) return "https://" + url;
    return url;
  }

  function isGenericCoffeeUrl(parsed) {
    const host = parsed.hostname.toLowerCase().replace(/^www\./, "");
    const path = parsed.pathname.replace(/\/+$/, "");
    return host === "buymeacoffee.com" && !path && !parsed.search && !parsed.hash;
  }

  /* ---- hooks Python calls ------------------------------------------------ */
  PR.app = {
    refreshState,
    showView,
    applyAccent,
    applyBackground,
    applyDensity,
    applyFont,
    openCoffee,
    onShown() { showView("launcher"); PR.launcher.runSearch().then(() => PR.launcher.focusSearch()); },
    openSettings() { showView("settings"); },
    onSettingsChanged() { refreshState().then(applyTheme); },
    // The real bridge appeared after we booted against the mock (slow
    // pywebview injection): swap in the real library and re-render.
    async onBridgeReal() {
      document.getElementById("brandCount").textContent = "";
      await refreshState();
      applyTheme();
      if (PR.state.view === "launcher") await PR.launcher.runSearch();
      else if (PR.state.view === "editor") PR.editor.render();
      selftestReport("");
    },
  };
  PR.onShown = PR.app.onShown;
  PR.openSettings = PR.app.openSettings;
  PR.onSettingsChanged = PR.app.onSettingsChanged;

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
