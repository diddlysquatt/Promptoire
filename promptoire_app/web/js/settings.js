/* settings.js — hotkey, theme, behavior, about */
(function () {
  "use strict";
  const PR = window.PROMPTOIRE;
  const { el, toast } = PR.ui;
  const GENERIC_COFFEE_URL = "https://www.buymeacoffee.com/";

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
      const nameStyle = t.light ? { color: "#1a1d26", textShadow: "none" } : {};
      const sw = el("button", { class: "swatch" + (s.theme === t.id ? " on" : ""),
        style: { background: `linear-gradient(135deg, ${t.c1}, ${t.c2})` }, dataset: { theme: t.id } },
        [el("span", { class: "sw-name", text: t.name, style: nameStyle })]);
      sw.addEventListener("click", () => {
        document.documentElement.setAttribute("data-theme", t.id);
        themeGrid.querySelectorAll(".swatch").forEach((x) => x.classList.remove("on"));
        sw.classList.add("on");
        s.theme = t.id; save({ theme: t.id });
      });
      themeGrid.appendChild(sw);
    });
    host.appendChild(section("Appearance", el("div", {}, [themeGrid, accentPicker(s)])));

    /* System */
    host.appendChild(section("System", card([
      toggleRow("Show tray icon", "Quick access from the system tray.", b.show_tray, (v) => save({ behavior: { show_tray: v } })),
      toggleRow("Launch at startup", "Start Promptoire when you sign in.", b.launch_at_startup, (v) => { save({ behavior: { launch_at_startup: v } }); toast(v ? "Promptoire will start with Windows" : "Startup disabled"); }),
      rowBtn("Back up now", "Save a timestamped copy of your library.", "Backup", async () => { await PR.bridge.call("backup_now"); toast("Backup saved"); }),
    ])));

    /* AI (optional direct improve) */
    host.appendChild(aiBlock(s));

    /* About */
    host.appendChild(aboutBlock());
  }

  function aiBlock(s) {
    const ai = s.ai || {};
    const sec = el("div", { class: "set-section" }, [el("div", { class: "set-title", text: "AI · optional" })]);
    const body = el("div", { class: "set-card", style: { padding: "14px" } });

    body.appendChild(el("p", { class: "hint", style: { marginBottom: "12px" },
      html: "Set this up to <b>Improve with AI now</b> (one click, no copy-paste) from the Improve&nbsp;Library panel. Your key is stored locally on this machine only. Leave blank to just use copy-paste." }));

    let provider = ai.provider || "anthropic";
    const baseField = el("div", { class: "field" });

    const seg = el("div", { class: "segmented", style: { marginBottom: "12px" } }, [
      sBtn("Anthropic", provider === "anthropic", () => setProv("anthropic")),
      sBtn("OpenAI-compatible", provider === "openai", () => setProv("openai")),
    ]);
    function setProv(p) {
      provider = p;
      [...seg.children].forEach((b, i) => b.classList.toggle("on", (i === 0) === (p === "anthropic")));
      baseField.style.display = p === "openai" ? "block" : "none";
      model.placeholder = p === "anthropic" ? "claude-opus-4-8 (default)" : "gpt-4o";
      save({ ai: { provider: p } });
    }

    const key = el("input", { class: "input", type: "password", value: ai.api_key || "",
      placeholder: "API key (stored locally)", id: "aiKeyField" });
    key.addEventListener("change", () => save({ ai: { api_key: key.value.trim() } }));

    const model = el("input", { class: "input", value: ai.model || "",
      placeholder: provider === "anthropic" ? "claude-opus-4-8 (default)" : "gpt-4o" });
    model.addEventListener("change", () => save({ ai: { model: model.value.trim() } }));

    const base = el("input", { class: "input", value: ai.base_url || "",
      placeholder: "https://api.openai.com/v1" });
    base.addEventListener("change", () => save({ ai: { base_url: base.value.trim() } }));
    baseField.appendChild(el("label", { text: "Base URL" }));
    baseField.appendChild(base);
    baseField.style.display = provider === "openai" ? "block" : "none";

    body.appendChild(seg);
    body.appendChild(el("div", { class: "field" }, [el("label", { text: "API key" }), key]));
    body.appendChild(el("div", { class: "field" }, [el("label", { text: "Model" }), model]));
    body.appendChild(baseField);

    sec.appendChild(body);
    return sec;
  }
  function sBtn(label, on, onclick) { return el("button", { class: on ? "on" : "", text: label, onclick }); }

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
    function setAccent(color) {
      s.accent = color;
      row.querySelectorAll(".pick").forEach((x) => x.classList.remove("on"));
      if (!color) clear.classList.add("on");
      else [...row.querySelectorAll(".colorpick")].find((x) => x.title === color)?.classList.add("on");
      if (PR.app && PR.app.applyAccent) PR.app.applyAccent(color);
      save({ accent: color });
    }
    return wrap;
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
    const links = (PR.state.settings && PR.state.settings.links) || {};
    const currentCoffee = configuredCoffeeUrl(links.coffee);
    const coffeeUrl = el("input", { class: "input coffee-link", value: currentCoffee,
      id: "coffeeLinkField",
      placeholder: "https://www.buymeacoffee.com/yourname" });
    coffeeUrl.addEventListener("change", () => {
      const value = coffeeUrl.value.trim();
      const clean = configuredCoffeeUrl(value);
      if (value && !clean) {
        coffeeUrl.classList.add("is-invalid");
        toast("Use a full http:// or https:// link", { bad: true });
        return;
      }
      coffeeUrl.classList.remove("is-invalid");
      coffeeUrl.value = clean;
      save({ links: { coffee: clean } });
      toast(clean ? "Coffee link saved" : "Coffee link cleared");
    });
    const s = el("div", { class: "set-section" }, [el("div", { class: "set-title", text: "About" })]);
    s.appendChild(el("div", { class: "about" }, [
      el("div", { class: "logo-big", text: "P" }),
      el("div", { style: { fontWeight: "700", fontSize: "15px" }, text: "Promptoire" }),
      el("div", { class: "ver", text: "v" + (PR.state.version || "2.2.0") + " · local-first · open source" }),
      el("div", { class: "tagline", text: "A fast, beautiful home for your text and image prompts — with one-click AI bulk-improve." }),
      el("button", { class: "coffee", html: "☕ &nbsp;" + (currentCoffee ? "Buy me a coffee" : "Set coffee link"),
        onclick: () => {
          const url = configuredCoffeeUrl((PR.state.settings.links || {}).coffee);
          if (url) PR.bridge.call("open_external", url);
          else { coffeeUrl.focus(); coffeeUrl.select && coffeeUrl.select(); toast("Paste your Buy Me a Coffee link here"); }
        } }),
      el("div", { class: "coffee-url" }, [coffeeUrl]),
    ]));
    return s;
  }

  function configuredCoffeeUrl(raw) {
    const url = String(raw || "").trim();
    if (!url || url === GENERIC_COFFEE_URL) return "";
    try {
      const parsed = new URL(url);
      return ["http:", "https:"].includes(parsed.protocol) ? parsed.href : "";
    } catch (e) {
      return "";
    }
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
