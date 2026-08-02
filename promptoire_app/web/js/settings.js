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
    { id: "paper", name: "Paper", c1: "#ffffff", c2: "#cbd0dc", light: true },
  ];
  const BACKGROUNDS = [
    { id: "", name: "Theme", c: "linear-gradient(135deg, var(--accent), var(--accent-2))" },
    { id: "obsidian", name: "Obsidian", c: "#08090e" },
    { id: "graphite", name: "Graphite", c: "#18191f" },
    { id: "midnight", name: "Midnight", c: "#0a1428" },
    { id: "forest", name: "Forest", c: "#0d1d19" },
    { id: "plum", name: "Plum", c: "#201427" },
    { id: "mist", name: "Mist", c: "#eaf0f8", light: true },
    { id: "linen", name: "Linen", c: "#f5efe5", light: true },
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
      toggleRow("Hide when it loses focus", "Close as soon as you click away.", b.hide_on_blur, (v) => save({ behavior: { hide_on_blur: v } })),
      toggleRow("Paste after copy", "Send Ctrl+V to the window you were in (best-effort).", b.paste_after_copy, (v) => save({ behavior: { paste_after_copy: v } })),
    ])));

    /* Appearance */
    const themeGrid = el("div", { class: "themes" });
    THEMES.forEach((t) => {
      const nameStyle = t.light ? { color: "#1a1d26", textShadow: "none" } : {};
      const sw = el("button", { class: "swatch" + (s.theme === t.id ? " on" : ""),
        style: { background: `linear-gradient(135deg, ${t.c1}, ${t.c2})` }, dataset: { theme: t.id } },
        [el("span", { class: "sw-name", text: t.name, style: nameStyle })]);
      sw.addEventListener("click", async () => {
        const previous = (PR.state.settings && PR.state.settings.theme) || "matrix";
        document.documentElement.setAttribute("data-theme", t.id);
        themeGrid.querySelectorAll(".swatch").forEach((x) => x.classList.remove("on"));
        sw.classList.add("on");
        if (!await save({ theme: t.id })) {
          document.documentElement.setAttribute("data-theme", previous);
          themeGrid.querySelectorAll(".swatch").forEach((x) => x.classList.toggle("on", x.dataset.theme === previous));
        }
      });
      themeGrid.appendChild(sw);
    });
    host.appendChild(section("Appearance", el("div", {}, [
      card([
        row("Prompt density", "Choose more context or fit more prompts at once.", densityPicker(s)),
        row("Font", "Change the app's reading style.", fontPicker(s)),
      ]),
      themeGrid,
      backgroundPicker(s),
      accentPicker(s),
    ])));

    /* System */
    host.appendChild(section("System", card([
      toggleRow("Show tray icon", "Keep Promptoire in the Windows notification area when hidden.", b.show_tray, (v) => save({ behavior: { show_tray: v } })),
      toggleRow("Launch at startup", "Start Promptoire when you sign in.", b.launch_at_startup, async (v) => {
        const saved = await save({ behavior: { launch_at_startup: v } });
        if (saved) toast(v ? "Promptoire will start with Windows" : "Startup disabled");
        return saved;
      }),
      rowBtn("Back up now", "Save a timestamped copy of your library.", "Backup", backupNow),
      rowBtn("Local data folder", "Open prompts, settings, and backups.", "Open", openDataFolder),
    ])));

    /* About */
    host.appendChild(aboutBlock());
  }
  function sBtn(label, on, onclick) { return el("button", { class: on ? "on" : "", text: label, onclick }); }

  function densityPicker(s) {
    const names = [
      { id: "comfortable", label: "Roomy" },
      { id: "compact", label: "Compact" },
      { id: "titles", label: "Titles" },
    ];
    const current = names.some((x) => x.id === s.density) ? s.density : "compact";
    const seg = el("div", { class: "segmented density-picker" });
    names.forEach((item) => {
      const button = sBtn(item.label, current === item.id, async () => {
        const previous = (PR.state.settings && PR.state.settings.density) || "compact";
        seg.querySelectorAll("button").forEach((x) => x.classList.remove("on"));
        button.classList.add("on");
        if (PR.app && PR.app.applyDensity) PR.app.applyDensity(item.id);
        if (!await save({ density: item.id })) {
          seg.querySelectorAll("button").forEach((x) => x.classList.toggle("on", x.dataset.density === previous));
          if (PR.app && PR.app.applyDensity) PR.app.applyDensity(previous);
        }
      });
      button.dataset.density = item.id;
      button.title = item.id === "comfortable" ? "Two-line previews and full metadata" :
        item.id === "compact" ? "One-line previews with less metadata" : "Prompt titles only";
      seg.appendChild(button);
    });
    return seg;
  }

  function accentPicker(s) {
    const colors = ["#7c5cff", "#22d3ee", "#34d399", "#f472b6", "#fb923c", "#f43f5e", "#fbbf24", "#e5e7eb"];
    const wrap = el("div", { class: "accent-picker" }, [
      el("div", { class: "accent-label", text: "Accent" }),
    ]);
    const row = el("div", { class: "picker-row" });
    const clear = el("button", { class: "pick accent-reset" + (!s.accent ? " on" : ""), text: "Theme", title: "Use theme accent",
      onclick: () => setAccent("") });
    row.appendChild(clear);
    colors.forEach((c) => {
      row.appendChild(el("button", { class: "pick colorpick" + (s.accent === c ? " on" : ""),
        style: { background: c }, title: c, onclick: () => setAccent(c) }));
    });
    wrap.appendChild(row);
    async function setAccent(color) {
      const previous = (PR.state.settings && PR.state.settings.accent) || "";
      row.querySelectorAll(".pick").forEach((x) => x.classList.remove("on"));
      if (!color) clear.classList.add("on");
      else [...row.querySelectorAll(".colorpick")].find((x) => x.title === color)?.classList.add("on");
      if (PR.app && PR.app.applyAccent) PR.app.applyAccent(color);
      if (!await save({ accent: color })) {
        row.querySelectorAll(".pick").forEach((x) => x.classList.remove("on"));
        if (!previous) clear.classList.add("on");
        else [...row.querySelectorAll(".colorpick")].find((x) => x.title === previous)?.classList.add("on");
        if (PR.app && PR.app.applyAccent) PR.app.applyAccent(previous);
      }
    }
    return wrap;
  }

  function backgroundPicker(s) {
    const wrap = el("div", { class: "appearance-picker" }, [
      el("div", { class: "accent-label", text: "Background" }),
    ]);
    const choices = el("div", { class: "background-picker" });
    BACKGROUNDS.forEach((item) => {
      const button = el("button", {
        class: "background-choice" + ((s.background || "") === item.id ? " on" : ""),
        title: item.name,
        "aria-label": item.name + " background",
        dataset: { background: item.id },
      }, [
        el("span", { class: "background-chip", style: { background: item.c } }),
        el("span", { text: item.name }),
      ]);
      button.addEventListener("click", async () => {
        const previous = (PR.state.settings && PR.state.settings.background) || "";
        choices.querySelectorAll(".background-choice").forEach((x) => x.classList.remove("on"));
        button.classList.add("on");
        if (PR.app && PR.app.applyBackground) PR.app.applyBackground(item.id);
        if (!await save({ background: item.id })) {
          choices.querySelectorAll(".background-choice").forEach((x) =>
            x.classList.toggle("on", x.dataset.background === previous));
          if (PR.app && PR.app.applyBackground) PR.app.applyBackground(previous);
        }
      });
      choices.appendChild(button);
    });
    wrap.appendChild(choices);
    return wrap;
  }

  function fontPicker(s) {
    const fonts = [
      { id: "system", name: "System" },
      { id: "rounded", name: "Rounded" },
      { id: "humanist", name: "Humanist" },
      { id: "mono", name: "Mono" },
    ];
    const select = el("select", { class: "select appearance-select", "aria-label": "App font" });
    fonts.forEach((item) => select.appendChild(el("option", {
      value: item.id, text: item.name, selected: (s.font || "system") === item.id ? "selected" : null,
    })));
    select.addEventListener("change", async () => {
      const previous = (PR.state.settings && PR.state.settings.font) || "system";
      const next = select.value;
      if (PR.app && PR.app.applyFont) PR.app.applyFont(next);
      if (!await save({ font: next })) {
        select.value = previous;
        if (PR.app && PR.app.applyFont) PR.app.applyFont(previous);
      }
    });
    return select;
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
    input.setAttribute("aria-label", t);
    input.addEventListener("change", async () => {
      const next = input.checked;
      input.disabled = true;
      const saved = await onChange(next);
      if (saved === false) input.checked = !next;
      input.disabled = false;
    });
    const sw = el("span", { class: "switch" }, [input, el("span", { class: "track" }), el("span", { class: "knob" })]);
    return row(t, d, sw);
  }
  function rowBtn(t, d, label, onclick) { return row(t, d, el("button", { class: "btn btn-sm", text: label, onclick })); }

  async function backupNow() {
    const r = await PR.bridge.call("backup_now");
    if (r && r.ok) toast("Backup saved");
    else toast((r && r.error) || "Backup failed", { bad: true });
  }

  async function openDataFolder() {
    const r = await PR.bridge.call("open_data_folder");
    if (r && r.ok) toast("Data folder opened");
    else toast((r && r.error) || "Could not open data folder", { bad: true });
  }

  function hotkeyCapture(current) {
    const cap = el("div", { class: "hotkey-cap", text: pretty(current), tabindex: "0",
      role: "button", "aria-label": "Change global hotkey" });
    let capturing = false;
    function start() {
      capturing = true;
      cap.classList.add("capturing");
      cap.textContent = "Press keys…";
      cap.focus();
    }
    function stop() { capturing = false; cap.classList.remove("capturing"); }
    cap.addEventListener("click", start);
    cap.addEventListener("keydown", async (e) => {
      if (!capturing) { if (e.key === "Enter") start(); return; }
      e.preventDefault();
      e.stopPropagation();
      const mods = [];
      if (e.ctrlKey) mods.push("ctrl");
      if (e.altKey) mods.push("alt");
      if (e.shiftKey) mods.push("shift");
      if (e.metaKey) mods.push("win");
      const k = e.key.toLowerCase();
      if (["control", "alt", "shift", "meta"].includes(k)) return;
      const key = e.code === "Backquote" ? "`" : (k === " " ? "space" : k);
      const combo = [...mods, key].join("+");
      const safeSingleKey = /^f(?:[1-9]|1\d|2[0-4])$/.test(key) || key === "`";
      if (!mods.length && !safeSingleKey) {
        cap.textContent = "Use Ctrl/Alt/Shift, F1–F24, or `";
        return;
      }
      cap.textContent = pretty(combo); stop();
      const r = await PR.bridge.call("set_hotkey", combo);
      if (r && r.ok && r.applied) {
        PR.state.settings.hotkey = combo;
        toast("Hotkey set: " + pretty(combo));
      } else {
        cap.textContent = pretty(PR.state.settings.hotkey || current);
        toast((r && r.error) || "That hotkey could not be registered", { bad: true });
      }
    });
    cap.addEventListener("blur", stop);
    return cap;
  }
  function pretty(combo) {
    return (combo || "").split("+").map((p) => p === "ctrl" ? "Ctrl" : p === "alt" ? "Alt" : p === "shift" ? "Shift" :
      p === "win" ? "Win" : p === "space" ? "Space" : p === "`" ? "` / ~" : p.toUpperCase()).join(" + ");
  }

  function aboutBlock() {
    const links = (PR.state.settings && PR.state.settings.links) || {};
    const currentRepo = configuredRepoUrl(links.repo);
    const s = el("div", { class: "set-section" }, [el("div", { class: "set-title", text: "About" })]);
    s.appendChild(el("div", { class: "about" }, [
      el("img", { class: "logo-big", src: "assets/tray.png", alt: "Promptoire magical scroll" }),
      el("div", { style: { fontWeight: "700", fontSize: "15px" }, text: "Promptoire" }),
      el("div", { class: "ver", text: "v" + (PR.state.version || "2.4.0") + " · local-first · open source" }),
      el("div", { class: "creator-credit", text: "Brought to you by Stoned Ape" }),
      el("div", { class: "tagline", text: "A fast, beautiful home for your text and image prompts — with one-click AI bulk-improve." }),
      el("div", { class: "about-actions" }, [
        currentRepo ? el("button", { class: "source-link", text: "GitHub",
          title: "Open Promptoire on GitHub",
          onclick: () => PR.bridge.call("open_external", configuredRepoUrl((PR.state.settings.links || {}).repo)) }) : null,
      ]),
    ]));
    return s;
  }

  function configuredRepoUrl(raw) {
    const url = normalizeUrl(raw);
    if (!url) return "";
    try {
      const parsed = new URL(url);
      const host = parsed.hostname.toLowerCase().replace(/^www\./, "");
      const path = parsed.pathname.replace(/\/+$/, "");
      if (!["http:", "https:"].includes(parsed.protocol) || (host === "github.com" && !path)) return "";
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

  async function save(patch) {
    const previous = PR.state.settings;
    const optimistic = deepMerge(previous, patch);
    PR.state.settings = optimistic;
    const result = await PR.bridge.call("update_settings", patch);
    if (!result || !result.ok) {
      PR.state.settings = previous;
      toast((result && result.error) || "Setting could not be saved", { bad: true });
      return false;
    }
    PR.state.settings = result.settings || optimistic;
    return true;
  }
  function deepMerge(a, b) {
    const out = Object.assign({}, a);
    for (const k in b) out[k] = (b[k] && typeof b[k] === "object" && !Array.isArray(b[k])) ? deepMerge(a[k] || {}, b[k]) : b[k];
    return out;
  }

  PR.settings = { render };
})();
