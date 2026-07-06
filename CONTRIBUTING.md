# Contributing To Promptoire

Promptoire is intentionally small: a local-first prompt launcher, organizer, and outline/JSON import loop. Contributions should make that core workflow clearer, safer, faster, or easier to use.

## Keep It Focused

- Prefer simple prompt-library improvements over broad productivity features.
- Keep the outline import/export flow first-class; JSON support exists for compatibility and precise merges.
- Avoid changes that make the main window feel crowded, tutorial-heavy, or cloud-dependent.
- Preserve local-first behavior. Network calls should stay optional and explicit.

## Protect Private Data

Do not commit or paste:

- `prompts.json`
- `promptoire.config.json`
- API keys, tokens, `.env` files, backups, caches, screenshots with private prompts, or personal prompt libraries

Use `prompts.example.json` and short sample outlines when describing behavior.

## Local Setup

```bat
setup.bat
Promptoire.bat
```

`setup.bat` creates the virtual environment, installs dependencies, and refreshes the `PROMPTOIRE` desktop shortcut when Windows allows it.

## Before Opening A Pull Request

Run:

```bat
check-release.bat
```

That runs the smoke suite, Python compile checks, frontend syntax checks, a real WebView self-test, and a guard that fails if private runtime files are tracked.

Before the first push to GitHub, also run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Check-GitHubPublish.ps1
```

That checks the GitHub remote, clean working tree, private-file guard, local release gate, and `gh` token scope needed for workflow files.

## UI And Workflow Guidelines

- Keep the main experience usable without an AI API key.
- Put safe merge paths before destructive replacement paths.
- Use clear controls instead of long in-app explanations.
- When adding import/export behavior, update `README.md`, `docs/GITHUB_RELEASE_CHECKLIST.md`, and `tests/test_smoke.py`.
- For app UI changes, verify the real app with `Promptoire.bat --selftest`.
