<div align="center">

# Promptoire

**A fast, beautiful, local-first home for your text *and* image prompts — with one-click AI bulk-improve.**

*Hit a hotkey → fuzzy-search your library → click to copy → it vanishes. Then hand your whole library to any LLM and let it rewrite everything at once.*

![status](https://img.shields.io/badge/status-active-brightgreen) ![platform](https://img.shields.io/badge/Windows-supported-blue) ![license](https://img.shields.io/badge/license-MIT-green) ![local-first](https://img.shields.io/badge/local--first-no%20account-7c5cff)

</div>

---

## Why Promptoire

Most prompt tools are cloud apps, browser extensions that die the moment you leave the tab, or generic clipboard managers that don't understand prompts. Promptoire is a small, gorgeous desktop launcher that sits quietly in your tray and does three things nobody else combines:

- **🧠→📄→🧠 Bulk-improve loop.** Export your *entire* library as clean JSON, paste it into ChatGPT / Claude / any LLM with a built-in "improve & expand these" instruction, then re-import. Changes are matched by id and shown in a **diff preview** before anything is written. Every other tool's "improve" works one prompt at a time — this refactors your whole collection in one pass.
- **✎ + ▦ Text *and* image prompts, first-class.** Keep your LLM prompts next to your Midjourney / Stable Diffusion / Flux prompts. Image prompts carry their own fields — negative prompt, model, parameters (`--ar`, `--stylize`, steps, CFG…).
- **🔒 Local-first, free, open source.** Your prompts live in a plain `prompts.json` on your machine. No account, no cloud, no telemetry. Back up by copying a file.

Plus the basics done well: a global hotkey that pops the launcher at your cursor, fuzzy search with keyboard nav, `{placeholder}` fill-in before copy, favorites, tags, nested categories, drag-to-reorder, timestamped backups, and a handful of themes.

## ✨ Highlights

| | |
|---|---|
| ⌨️ **Global hotkey** | Summon it anywhere (default `Ctrl+Alt+Space`), at your cursor. |
| ⚡ **Copy & vanish** | Click a prompt → it's on your clipboard → window hides. Or pin it open. |
| 🔣 **Placeholders** | `{topic}`, `{tone}`, `{code}` → quick fill-in form before copy. |
| 🪶 **Light & fast** | Renders through the system WebView (no bundled browser). Tiny footprint. |
| 🎨 **Themeable** | Matrix, Cyber, Aurora, Ember, Sunset, Emerald, Mono. |
| 🗂️ **Organized** | Nested categories, tags, favorites, fuzzy search, drag-reorder. |
| 💾 **Safe** | Atomic saves + rolling timestamped backups. |

## 🚀 Quick start (from source)

Requires **Python 3.9+** and the **WebView2 runtime** (preinstalled on Windows 11 and most Windows 10).

```bat
:: 1. one-time setup (creates a venv, installs deps)
setup.bat

:: 2. run it
Promptoire.bat
```

…or manually:

```bash
pip install -r requirements.txt
python -m promptoire_app
```

To launch at login, drop a shortcut to `Promptoire.bat` in `shell:startup` (Win+R → `shell:startup`).

## 📦 Build a standalone .exe

```bat
build.bat            :: → dist\Promptoire\Promptoire.exe
```

(Uses PyInstaller via `Promptoire.spec`; one-dir build for fast, AV-friendly startup.)

## 🔁 The bulk-improve loop

1. Open **Improve library** (sparkle icon).
2. **Copy for AI** — puts an editable instruction + your whole library (as JSON) on your clipboard.
3. Paste into any LLM. It returns improved JSON in the same schema.
4. Paste that back, hit **Preview changes** — see exactly what's new vs. updated.
5. **Merge** (matched by prompt id; your local prompts are never deleted).

The instruction (meta-prompt) is fully editable in that panel.

## 🗃️ Data format

Everything lives in `prompts.json` next to the app — human-readable and easy to edit by hand or with an LLM:

```jsonc
{
  "version": 3,
  "categories": [
    {
      "id": "cat_…", "name": "AI Art", "color": "#f472b6",
      "prompts": [
        {
          "id": "prm_…", "type": "image",
          "title": "Cinematic portrait",
          "prompt": "cinematic portrait of {subject}, dramatic rim lighting, 85mm…",
          "tags": ["portrait"],
          "negative": "blurry, watermark", "model": "Midjourney v6", "params": "--ar 4:5 --stylize 250"
        }
      ],
      "subcategories": []
    }
  ]
}
```

## ⌨️ Shortcuts

| Action | Key |
|---|---|
| Summon launcher (global) | `Ctrl+Alt+Space` *(configurable)* |
| Focus search | `Ctrl+F` |
| Manage library | `Ctrl+E` |
| Improve library | `Ctrl+I` |
| Settings | `Ctrl+,` |
| New prompt | `Ctrl+N` |
| Navigate / copy | `↑ ↓` / `Enter` |
| Back / hide | `Esc` |

## 🛠️ Architecture

- **Backend** (`promptoire_app/core`, `/platform`): Python. Data layer (v3 schema, migration, search, merge), settings, global hotkey, tray, clipboard.
- **Frontend** (`promptoire_app/web`): zero-build vanilla HTML/CSS/JS, rendered by the system WebView through [pywebview](https://pywebview.flowrl.com/). No framework, no bundler.

## ❤️ Support

Promptoire is free and open source. If it earns a spot in your workflow, you can **buy me a coffee** (link in Settings → About). That's the whole business model.

## 📄 License

MIT — use it, fork it, ship it.
