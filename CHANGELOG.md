# Changelog

## 2.3.0 - 2026-07-06

### Added

- Outline-first bulk workflow: copy the whole library as a plain section/subsection outline for any LLM.
- Safe outline merge support that matches existing prompts by section path and title when ids are not present.
- Plain outline imports from paste, clipboard, `.txt`, `.md`, and `.json` files.
- Nested bullet-tree outline imports and deeper `Sub-subsection:` / `Nested subsection:` labels.
- YAML-style `- Title:` prompt blocks with indented fields.
- Markdown table imports with `Title` and `Prompt` columns.
- Editable outline AI instructions used by both copy/paste export and direct AI improve.
- Outline export to `.txt`, plus an outline request helper for generating new prompt batches.
- Import preview chips for new nested sections and title-matched updates.
- Markdown-fenced outline replies are accepted without importing the fence text.
- Desktop shortcut creation through `setup.bat` and `Create-PromptoireShortcut.ps1`.
- Desktop shortcut verification through `Check-PromptoireShortcut.ps1` and the local release gate.
- GitHub publish-readiness verification through `Check-GitHubPublish.ps1`.
- GitHub release materials: CI, issue templates, PR template, privacy/security docs, contributing guide, and `check-release.bat`.

### Changed

- The Improve Library panel now defaults to the no-JSON outline flow and keeps JSON actions under `JSON options`.
- `Improve with AI now` uses the outline library payload instead of the older JSON payload.
- The old JSON meta-prompt is labeled as JSON-specific so the default outline flow stays clear.
- Generic Buy Me a Coffee and GitHub placeholder links are sanitized instead of opening generic pages, including root Buy Me a Coffee URLs with or without `www`.
- CI and local preflight now compile the full app and tests, run JS syntax checks, and verify the WebView bridge self-test.

### Notes

- Public pushes that include `.github/workflows/ci.yml` still require GitHub auth with the `workflow` scope.
- The real Buy Me a Coffee URL is intentionally left blank until configured locally.
- The folder can be displayed as `PROMPTOIRE` after any process currently holding the lowercase workspace path is closed.

## 2.2.0 - 2026-06-07

- Rebuilt Promptoire on pywebview with Python plus vanilla HTML/CSS/JS.
- Added the local prompt launcher, search, prompt editor, nested categories, image prompt fields, optional direct AI improve, and packaging scripts.
