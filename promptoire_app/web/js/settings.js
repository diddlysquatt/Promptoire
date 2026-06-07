/* settings.js — hotkey, theme, behavior, about */
(function () {
  "use strict";
  const PR = window.PROMPTOIRE;
  const { el, toast } = PR.ui;

  const THEMES = [
    { id: "matrix", name: "Matrix", c1: "#7c5cff", c2: "#22d3ee" },
    { id: "cyber", name: "Cyber", c1: "#22d3ee", c2: "#a855f7" },
    { id: "aurora", name: "Aurora", c1: "#34d399", c2: "#22d3ee" },
    { id: "ember", name: "Ember", c1: "#fb923c", c2: "#f43f5e" },
    { id: "sunset", name: "Sunset", c1: "#f472b6", c2: "#fb923c" },
    { id: "emerald", name: "Emerald", c1: "#10b981", c2: "#84cc16" },
    { id: "mono", name: "Mono", c1: "#e5e7eb", c2: "#9ca3af" },
  ];

  function render() {
    const host = document.getElementById("settingsBody");
    host.innerHTML = "";
    const s = PR.state.settings;
    const b = s.behavior || {};

    /* Hotkey */
    host.appendChild(section("Activation", card([
      row("Global hotkey", PR.state.hotkeyAvailable
        ? "Press this anywhere to summon Promptoire."
        : "⚠ Global hotkey needs the 'keyboard' module / permission. Tray still works.",
        hotkeyCapture(s.hotkey || "ctrl+alt+space")),
      toggleRow("Open at cursor", "Pop up where your mouse is.", b.open_at_cursor, (v) => save({ behavior: { open_at_cursor: v } })),
      toggleRow("Copy then vanish", "Hide automatically right after you copy a prompt.", b.copy_then_hide, (v) => save({ behavior: { copy_then_hide: v } })),
      toggleRow("Hide when it loses focus", "Close as soon as you click away.", b.hide_on_blur, (v) => save({ behavior: { hide_on_blur: v } })),
      toggleRow("Paste after copy", "Send Ctrl+V to the window you were in (best-effort).", b.paste_after_copy, (v) => save({ behavior: { paste_after_copy: v } })),
    ])));

    /* Appearance */
    const themeGrid = el("div", { class: "themes" });
    THEMES.forEach((t) => {
      const sw = el("button", { class: "swatch" + (s.theme === t.id ? " on" : ""),
        style: { background: `linear-gradient(135deg, ${t.c1}, ${t.c2})` }, dataset: { theme: t.id } },
        [el("span", { class: "sw-name", text: t.name })]);
      sw.addEventListener("click", () => {
        document.documentElement.setAttribute("data-theme", t.id);
        themeGrid.querySelectorAll(".swatch").forEach((x) => x.classList.remove("on"));
        sw.classList.add("on");
        s.theme = t.id; save({ theme: t.id });
      });
      themeGrid.appendChild(sw);
    });
    host.appendChild(section("Appearance", el("div", {}, [themeGrid])));

    /* System */
    host.appendChild(section("System", card([
      toggleRow("Show tray icon", "Quick access from the system tray.", b.show_tray, (v) => save({ behavior: { show_tray: v } })),
      toggleRow("Launch at startup", "Start Promptoire when you sign in.", b.launch_at_startup, (v) => { save({ behavior: { launch_at_startup: v } }); toast(v ? "Will start with Windows (apply on next build)" : "Startup disabled"); }),
      rowBtn("Back up now", "Save a timestamped copy of your library.", "Backup", async () => { await PR.bridge.call("backup_now"); toast("Backup saved"); }),
    ])));

    /* About */
    host.appendChild(aboutBlock());
  }

  function section(title, content) {
    const s = el("div", { class: "set-section" }, [el("div", { class: "set-title", text: title })]);
    s.appendChild(content);
    return s;
  }
  function card(rows) { return el("div", { class: "set-card" }, rows); }
  function row(t, d, control) {
    return el("div", { class: "set-row" }, [
      el("div", { class: "meta" }, [el("div", { class: "t", text: t }), el("div", { class: "d", text: d })]),
      control,
    ]);
  }
  function toggleRow(t, d, checked, onChange) {
    const input = el("input", { type: "checkbox" });
    input.checked = !!checked;
    input.addEventListener("change", () => onChange(input.checked));
    const sw = el("span", { class: "switch" }, [input, el("span", { class: "track" }), el("span", { class: "knob" })]);
    return row(t, d, sw);
  }
  function rowBtn(t, d, label, onclick) { return row(t, d, el("button", { class: "btn btn-sm", text: label, onclick })); }

  function hotkeyCapture(current) {
    const cap = el("div", { class: "hotkey-cap", text: pretty(current), tabindex: "0" });
    let capturing = false;
    function start() { capturing = true; cap.classList.add("capturing"); cap.textContent = "Press keys…"; }
    function stop() { capturing = false; cap.classList.remove("capturing"); }
    cap.addEventListener("click", start);
    cap.addEventListener("keydown", async (e) => {
      if (!capturing) { if (e.key === "Enter") start(); return; }
      e.preventDefault();
      const mods = [];
      if (e.ctrlKey) mods.push("ctrl");
      if (e.altKey) mods.push("alt");
      if (e.shiftKey) mods.push("shift");
      if (e.metaKey) mods.push("win");
      const k = e.key.toLowerCase();
      if (["control", "alt", "shift", "meta"].includes(k)) return;
      const key = k === " " ? "space" : k;
      const combo = [...mods, key].join("+");
      if (!mods.length) { cap.textContent = "Use a modifier (Ctrl/Alt/Shift)"; return; }
      cap.textContent = pretty(combo); stop();
      const r = await PR.bridge.call("set_hotkey", combo);
      PR.state.settings.hotkey = combo;
      if (r && r.ok) toast(r.applied ? "Hotkey set: " + pretty(combo) : "Saved (couldn't bind globally — check permissions)", { bad: !r.applied });
    });
    cap.addEventListener("blur", stop);
    return cap;
  }
  function pretty(combo) {
    return (combo || "").split("+").map((p) => p === "ctrl" ? "Ctrl" : p === "alt" ? "Alt" : p === "shift" ? "Shift" :
      p === "win" ? "Win" : p === "space" ? "Space" : p.toUpperCase()).join(" + ");
  }

  function aboutBlock() {
    const s = el("div", { class: "set-section" }, [el("div", { class: "set-title", text: "About" })]);
    s.appendChild(el("div", { class: "about" }, [
      el("div", { class: "logo-big", text: "P" }),
      el("div", { style: { fontWeight: "700", fontSize: "15px" }, text: "Promptoire" }),
      el("div", { class: "ver", text: "v" + (PR.state.version || "2.0.0") + " · local-first · open source" }),
      el("div", { class: "tagline", text: "A fast, beautiful home for your text and image prompts — with one-click AI bulk-improve." }),
      el("button", { class: "coffee", html: "☕ &nbsp;Buy me a coffee",
        onclick: () => {
          const url = (PR.state.settings.links && PR.state.settings.links.coffee) || "https://www.buymeacoffee.com/";
          PR.bridge.call("open_external", url);
        } }),
    ]));
    return s;
  }

  function save(patch) {
    PR.bridge.call("update_settings", patch);
    PR.state.settings = deepMerge(PR.state.settings, patch);
  }
  function deepMerge(a, b) {
    const out = Object.assign({}, a);
    for (const k in b) out[k] = (b[k] && typeof b[k] === "object" && !Array.isArray(b[k])) ? deepMerge(a[k] || {}, b[k]) : b[k];
    return out;
  }

  PR.settings = { render };
})();
