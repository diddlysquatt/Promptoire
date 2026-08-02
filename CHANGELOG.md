# Changelog

## Unreleased

## 2.4.0 - 2026-08-01

### Changed

- Remove the launcher footer so every recovered pixel belongs to prompt results; move **+ New** beside the All/Text/Image/Favorites filters and rename the pencil action to **Edit Library**.
- Fix the pywebview startup race that could leave frameless edge/corner resizing connected to a zero native handle; 360×420 remains the minimum while both axes can expand.
- Keep improvement instructions visible in Improve Library, clarify library/instruction copy actions, move optional AI configuration to that panel, and narrow direct calls to OpenAI's current GPT-5.6 family.
- Make safe-merge preview and apply share one plan, skip repeated or ambiguous rows, preserve nonblank local fields when an import omits them, and report missing nested category nodes consistently.
- Generate unique prompt ids instead of content-derived ids and repair duplicate ids from older local libraries at load time.
- Default the launcher to a compact one-line prompt layout, with Comfortable and Titles-only density choices available from the launcher or Settings.
- Fix every Settings toggle so the visible switch is the real click target, and roll the UI back with an error message if a system setting cannot be applied.
- Repair Windows launch-at-startup registration, remove the obsolete pre-rebuild Startup-folder script, and keep the displayed setting synchronized with the actual Run entry.
- Allow modifier-free `F1`–`F24` and tilde/backquote global hotkeys while retaining modifier combinations such as `Alt+C`.
- Reopen the hidden existing window when Promptoire is launched a second time instead of silently exiting.
- Keep support to the compact coffee icon in the top toolbar and remove the oversized donation treatment and link editor from Settings.
- Make the category rail reliably mouse-draggable and translate vertical wheel input into horizontal rail scrolling when needed.
- Add native side and corner resizing to the frameless Windows window and remember the resulting size between launches.
- Require the local release gate to generate a fresh WebView self-test report instead of accepting a stale report when another instance is running.
- Add proper Windows product/version metadata to the standalone executable.
- Keep unused AVIF and WebP codecs out of the portable build to reduce its footprint.
- Let prompts be dropped anywhere in a destination category, including its empty-state area or a specific row position.
- Validate drag-and-drop destinations before removing prompts from their current category.
- Stop continuously animating the decorative background aura so the open app stays quiet at idle.
- Silence the standalone browser-preview favicon request and ignore local visual-QA artifacts.
- Keep every launcher filter, **+ New**, and density control on one row at the minimum window width, and compact the five import actions into two rows.
- Make the top pin the single visible copy/blur auto-hide override and remove the redundant **Copy then vanish** Settings row.
- Ship the finished Promptoire Buy Me a Coffee profile as the built-in support link so the toolbar button also works on a fresh install.
- Require Pillow 12.3.0 or newer, refresh the complete dependency set before packaging, and add weekly Dependabot checks.
- Consolidate the prompt editor around Title, Category, Prompt, Tags, and Note; remove the type toggle and advanced image-detail controls while preserving legacy import data.
- Add curated dark and light background surfaces, four font choices, and visible per-category header colors without changing plain-text prompt portability.
- Make the global hotkey hide Promptoire on the first press whenever it is visible, even when another window has focus.
- Minimize and native close requests now hide Promptoire to the Windows notification area instead of leaving a taskbar button or quitting; the tray menu remains the explicit exit path.
- Replace the detailed legacy artwork with a crisp magical-scroll icon shared by the window, taskbar, notification area, desktop shortcut, and packaged executable.
- Replace separate expand/collapse-all controls with one stateful tree button and tighten the Edit Library styling with solid category tints and outlined hover feedback.

### Fixed

- Keep the sticky **Edit Library** filter toolbar fully opaque while categories and prompts scroll beneath it.
- Ignore copied LLM conversation/request prose before the first canonical `Path:` record instead of importing it as `Imported` or `Rules` prompts.
- Preserve headings, bullets, rubrics, and multi-paragraph content inside explicit `Prompt:` bodies instead of turning phrases such as `CONSTRAINTS` or `DECISION DATE` into categories.
- Serialize merge mutations and disable the merge action while it is running so a rapid double activation cannot add duplicate prompts.
- Make category-rail clicks navigate directly to the selected category.
- Apply the native Promptoire icon to the source-run window and taskbar entry.
- Keep optional image metadata collapsed while directing copyable model suffixes to the end of the main prompt.
- Keep pinned copies open through the native bridge, make selected categories unmistakable, and make category clicks less likely to be mistaken for a horizontal drag.
- Restrict external links at the Python bridge to valid HTTPS destinations and invoke the Windows clipboard fallback without a shell.

### Added

- Credit **Stoned Ape** in the in-app About section.

## 2.3.0 - 2026-07-06

### Added

- Outline-first bulk workflow: copy the whole library as a plain section/subsection outline for any LLM.
- Safe outline merge support that matches existing prompts by section path and title when ids are not present.
- Plain outline imports from paste, clipboard, `.txt`, `.md`, and `.json` files.
- Nested bullet-tree outline imports and deeper `Sub-subsection:` / `Nested subsection:` labels.
- Deeper Markdown prompt headings such as `### Prompt title` can import as prompt titles when followed by body text.
- YAML-style `- Title:` prompt blocks with indented fields.
- Markdown table imports with `Title` and `Prompt` columns.
- CSV table imports with `Title` and `Prompt` columns.
- JSON compatibility imports accept common LLM aliases such as `sections`, `subsections`, `items`, and `entries`.
- Flat JSON prompt rows can use `path`, `section`, and `subsection` fields to land in the right nested section.
- JSON image prompt imports accept common field aliases such as `negative_prompt`, `image_model`, `parameters`, and `cfg_scale`.
- Plain JSON string prompts import as prompts with derived titles.
- Editable outline AI instructions used by both copy/paste export and direct AI improve.
- Reset buttons for restoring the default outline and JSON AI instructions.
- Outline export to `.txt`, plus an outline request helper for generating new prompt batches.
- Topic-aware outline requests for asking an LLM to generate a brand-new prompt batch.
- Import preview chips for new nested sections and title-matched updates.
- Import preview now shows total incoming prompts and clearer safe-merge mode notes.
- Manual paste into the import box now auto-previews changes.
- The import panel now has a `Clear` action for resetting the pasted text and preview.
- Settings can open the local data folder that contains prompts, settings, and backups.
- Settings About includes a GitHub source link for the public repository.
- Safe merge disables the merge action when the selected Add/Update mode has no applicable changes.
- Markdown-fenced outline replies are accepted without importing the fence text.
- Desktop shortcut creation through `setup.bat` and `Create-PromptoireShortcut.ps1`.
- Desktop shortcut verification through `Check-PromptoireShortcut.ps1` and the local release gate.
- GitHub publish-readiness verification through `Check-GitHubPublish.ps1`.
- Publish-readiness warnings when the project folder still displays with non-`PROMPTOIRE` casing.
- Publish-readiness warnings for blank/generic Buy Me a Coffee support links.
- Publish-readiness checks now normalize support links before judging whether they are generic placeholders.
- Publish-readiness checks now summarize the remaining next steps at the end of the report.
- Support links typed without `https://` are normalized before saving or opening.
- GitHub release materials: CI, issue templates, PR template, privacy/security docs, contributing guide, and `check-release.bat`.

### Changed

- The Improve Library panel now defaults to the no-JSON outline flow and keeps JSON actions under `JSON options`.
- Empty libraries now offer a direct `Import prompts` shortcut into the Improve Library flow.
- `Improve with AI now` uses the outline library payload instead of the older JSON payload.
- The old JSON meta-prompt is labeled as JSON-specific so the default outline flow stays clear.
- Generic Buy Me a Coffee and GitHub placeholder links are sanitized instead of opening generic pages, including root Buy Me a Coffee URLs with or without `www`.
- Runtime settings updates now sanitize support links immediately, matching startup/load behavior.
- CI and local preflight now compile the full app and tests, run every frontend JS syntax check, and verify the WebView bridge self-test.

### Notes

- Public pushes that include `.github/workflows/ci.yml` still require GitHub auth with the `workflow` scope.
- The real Buy Me a Coffee URL is intentionally left blank until configured locally.
- The folder can be displayed as `PROMPTOIRE` after any process currently holding the lowercase workspace path is closed.

## 2.2.0 - 2026-06-07

- Rebuilt Promptoire on pywebview with Python plus vanilla HTML/CSS/JS.
- Added the local prompt launcher, search, prompt editor, nested categories, image prompt fields, optional direct AI improve, and packaging scripts.
