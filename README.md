<div align="center">

# Promptoire

**A fast, beautiful, local-first home for your text *and* image prompts — with one-click AI bulk-improve.**

*Hit a hotkey → fuzzy-search your library → click to copy → it vanishes. Then hand your whole library to any LLM and let it rewrite everything at once.*

![status](https://img.shields.io/badge/status-active-brightgreen) ![platform](https://img.shields.io/badge/Windows-supported-blue) ![license](https://img.shields.io/badge/license-MIT-green) ![local-first](https://img.shields.io/badge/local--first-no%20account-7c5cff)

</div>

---

## Why Promptoire

Most prompt tools are cloud apps, browser extensions that die the moment you leave the tab, or generic clipboard managers that don't understand prompts. Promptoire is a small, gorgeous desktop launcher that sits quietly in your tray and does three things nobody else combines:

- **🧠→📄→🧠 Bulk-improve loop.** Export your *entire* library as a simple outline, paste it into ChatGPT / Claude / any LLM with a built-in "improve & expand these" instruction, then re-import. Outline and JSON changes are shown in a **diff preview** before anything is written.
- **✎ + ▦ Text *and* image prompts, first-class.** Keep your LLM prompts next to your Midjourney / Stable Diffusion / Flux prompts. Image prompts carry their own fields — negative prompt, model, parameters (`--ar`, `--stylize`, steps, CFG…).
- **🔒 Local-first, free, open source.** Your prompts live in a plain `prompts.json` on your machine. No account, no cloud, no telemetry. Back up by copying a file.

Plus the basics done well: a global hotkey that pops the launcher at your cursor, fuzzy search with keyboard nav, `{placeholder}` fill-in before copy, favorites, tags, nested categories, drag-to-reorder, timestamped backups, a one-click local data folder, and a handful of themes.

## ✨ Highlights

| | |
|---|---|
| ⌨️ **Global hotkey** | Summon it anywhere (default `Ctrl+Alt+Space`), at your cursor. |
| 🌳 **The tree, right in the launcher** | Browse your whole library grouped by category — collapsible, color-coded, icons and counts — before you type a single letter. |
| 🏷️ **Category rail + tag search** | One-tap category filter chips; type `#tag` (or click any tag) to filter; multi-word queries must all match. |
| ⚡ **Copy & vanish** | Click a prompt → it's on your clipboard → window hides. Or pin it open. |
| 🔣 **Placeholders** | `{topic}`, `{tone}`, `{code}` → quick fill-in form before copy. |
| 🗂️ **Real organization** | Subcategories, emoji icons, accent colors, drag prompts between categories, drag to reorder categories, filter the manage view. |
| 🪶 **Light & fast** | Renders through the system WebView (no bundled browser). Tiny footprint. |
| 🎨 **Themeable** | Matrix, Cyber, Aurora, Ember, Sunset, Emerald, Mono, Paper (light). |
| 💾 **Safe** | Atomic saves + rolling timestamped backups. |

## 🚀 Quick start (from source)

Requires **Python 3.9+** and the **WebView2 runtime** (preinstalled on Windows 11 and most Windows 10).

```bat
:: 1. one-time setup (creates a venv, installs deps, adds desktop shortcut)
setup.bat

:: 2. run it
Promptoire.bat
```

`setup.bat` also refreshes a `PROMPTOIRE` desktop shortcut that launches the local checkout.
`Check-PromptoireShortcut.ps1` verifies that shortcut, and `check-release.bat` runs it as part of the local release gate.

If the project folder itself still displays as `promptoire`, close Promptoire, Codex, terminals, and File Explorer windows inside the project, then run `Rename-PromptoireFolder.ps1`. It safely renames the folder to `PROMPTOIRE` and refreshes the desktop shortcut.

…or manually:

```bash
pip install -r requirements.txt
python -m promptoire_app
```

To launch at login, enable **Launch at startup** in Settings.

## 📦 Build a standalone .exe

```bat
build.bat            :: → dist\Promptoire\Promptoire.exe
```

(Uses PyInstaller via `Promptoire.spec`; one-dir build for fast, AV-friendly startup.)

## 🔁 The bulk-improve loop

1. Open **Improve library** (sparkle icon).
2. **Copy outline library** puts an editable instruction + your whole library on your clipboard as a plain section/subsection outline. **Edit instructions** customizes that outline request, and **Save outline** writes the same simple library format to a `.txt` file. JSON export is still available under **JSON options**.
3. Paste into any LLM. It can return the plain outline format, or JSON if you use the compatibility tools.
4. Paste that back, click **Paste from clipboard**, or **Load from file** (`.json`, `.txt`, `.md`, or `.csv`), then hit **Preview changes** — see incoming, new, updated, and unchanged counts before anything is written.
5. **Merge** (matched by prompt id first, then by title inside the same section; your local prompts are never deleted). If the selected Add/Update mode would do nothing, Promptoire disables the merge until you choose an applicable action.

The outline instruction is editable in that panel, with **Reset default** if you want the built-in instruction back. The older JSON instruction is still editable under **JSON options** for compatibility.

For brand-new prompt batches without exporting your existing library, use **Copy outline request**. Add a topic or workflow, then it copies a ready instruction that asks an LLM to return sections, subsections, and prompt bullets you can paste straight back into Promptoire.

**Prefer one click?** Add an API key in **Settings → AI** (Anthropic, or any OpenAI-compatible endpoint) and hit **Improve with AI now** — it sends the outline library, gets an importable reply back, and drops you straight into the diff preview. Optional; your key is stored locally only, and the copy/paste loop always works without it.

## 🗃️ Data format

Everything lives in `prompts.json` next to the app — human-readable and easy to edit by hand or with an LLM:

```jsonc
{
  "version": 3,
  "categories": [
    {
      "id": "cat_…", "name": "AI Art", "icon": "🎨", "color": "#f472b6",
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

For quick appends or no-JSON library passes, the import box also accepts a plain outline. **Copy outline library** exports your current prompts in this same format:

```md
Coding
  Debugging
    Bug sweep: Review this code for edge cases, broken assumptions, and missing tests.

Path: AI Art > Characters > Portraits
Title: Cinematic portrait
Type: image
Prompt: A dramatic 85mm portrait of {subject}, rim lighting, shallow depth of field.
Negative prompt: blurry, watermark, extra fingers
Image model: Midjourney v6
Parameters: --ar 4:5 --stylize 250

Subsection: Environments
Dreamy landscape: A vast {place} at golden hour, painterly atmosphere, cinematic light.

- Workflows
  - Research
    - Literature
      - Source map: Map the strongest sources for {topic}.

Prompts:
  - Title: Tight rewrite
    Prompt: Rewrite {text} clearly while preserving voice.
    Tags: editing, clarity
```

Headings, `Path: Section > Subsection > Nested subsection`, `Section:` / `Subsection:` labels, indented plain text, nested bullet trees, YAML-style `- Title:` blocks, and Markdown/CSV tables with `Title` + `Prompt` columns become categories and subcategories. Deeper Markdown headings such as `### Prompt title` can also become prompt titles when followed by prompt body text. JSON compatibility imports accept `categories`/`sections`, `subcategories`/`subsections`, and `prompts`/`items`/`entries` aliases; flat JSON prompt rows can include `path`, `section`, and `subsection` fields; plain JSON string prompts become text prompts with derived titles. JSON image fields can use aliases like `negative_prompt`, `image_model`, `parameters`, and `cfg_scale`. For deeper labels, use `Sub-subsection:` or `Nested subsection:`. Repeated unindented `Subsection:` labels stay under the latest `Section:`. Prompt rows become prompts, and numbered blocks like `Prompt 1:` also work for multi-line prompts. Image labels like `Negative prompt:`, `Image model:`, `Parameters:`, and `CFG scale:` map to the normal image fields. If an LLM wraps the outline in a Markdown code fence, Promptoire reads the fenced outline instead of importing the fence text. Merging an outline adds to matching sections and does not replace the existing library; if a prompt title already exists in that section, Promptoire updates it instead of creating a duplicate.

For public forks and packaged releases, `prompts.json` is treated as local user data and ignored by git. Fresh installs seed a small starter library automatically; `prompts.example.json` is included only as a clean reference file.

## ⌨️ Shortcuts

| Action | Key |
|---|---|
| Summon launcher (global) | `Ctrl+Alt+Space` *(configurable)* |
| Focus search | `Ctrl+F` or `Ctrl+K` |
| Manage library | `Ctrl+E` |
| Improve library | `Ctrl+I` |
| Settings | `Ctrl+,` |
| New prompt | `Ctrl+N` |
| Type filter (All / Text / Image / ★) | `Ctrl+1…4` or `Tab` |
| Navigate / copy | `↑ ↓` (`PgUp/PgDn`) / `Enter` |
| Filter by tag | type `#tag`, or click a tag chip |
| Back / hide | `Esc` |

## 🛠️ Architecture

- **Backend** (`promptoire_app/core`, `/platform`): Python. Data layer (v3 schema, migration, search, merge), settings, global hotkey, tray, clipboard.
- **Frontend** (`promptoire_app/web`): zero-build vanilla HTML/CSS/JS, rendered by the system WebView through [pywebview](https://pywebview.flowrl.com/). No framework, no bundler.

## ✅ GitHub readiness

Before the first public push, make sure your personal library is not part of the commit. This repo ignores `prompts.json`; if an older/local clone still shows it as tracked, remove it from the index without deleting your local file:

```bash
git rm --cached prompts.json
```

Then commit the app changes normally. `prompts.json` stays on your machine, but public commits should use `prompts.example.json` as the reference library.

Run `check-release.bat` before pushing. It runs the smoke tests, compile checks, frontend syntax checks, real WebView self-test, and a guard that fails if private runtime files are tracked.
Before the first GitHub push, run `Check-GitHubPublish.ps1`. It verifies the origin remote, clean working tree, private-file guard, GitHub Actions workflow, local release gate, GitHub CLI `workflow` token scope, and warns if the folder still displays lowercase or the Buy Me a Coffee support link is still blank.

For sharing or review, see [Contributing](CONTRIBUTING.md), [Changelog](CHANGELOG.md), [Privacy](docs/PRIVACY.md), and [Security](SECURITY.md). Short version: Promptoire has no telemetry, stores data locally by default, and only sends prompt data out when you copy it to another tool or use the optional direct AI improve button.

## ❤️ Support

Promptoire is free and open source. If it earns a spot in your workflow, you can **buy me a coffee** from the titlebar or Settings → About. Set your real link in Settings or in `promptoire.config.json` under `links.coffee`.

## 📄 License

MIT — use it, fork it, ship it.
