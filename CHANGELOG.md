# Changelog

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
