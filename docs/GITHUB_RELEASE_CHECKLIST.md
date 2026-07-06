# PROMPTOIRE GitHub Release Checklist

Use this before the first public push.

## Local Data

- Keep your real `prompts.json` on your machine.
- Do not publish API keys, `promptoire.config.json`, backups, caches, or virtual environments.
- Use `prompts.example.json` as the public reference data file.
- If `prompts.json` is still tracked, run:

```bash
git rm --cached prompts.json
```

That removes it from git without deleting the file locally.

## Preflight

GitHub Actions runs the portable subset of these checks. The local gate is
stricter because it also verifies the real WebView launch, desktop shortcut,
and private-file guard on this Windows machine.

Run the one-command local gate first:

```bat
check-release.bat
```

Before the first push, run the publish-readiness check:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Check-GitHubPublish.ps1
```

Use `-SkipReleaseGate` for a quick auth/remote/private-file check after `check-release.bat` has already passed.

If that fails, run the individual checks below to isolate the problem:

```bash
python tests/test_smoke.py
python -m compileall -q promptoire_app tests
node --check promptoire_app/web/js/app.js
node --check promptoire_app/web/js/settings.js
node --check promptoire_app/web/js/bulk.js
node --check promptoire_app/web/js/bridge.js
.\.venv\Scripts\python.exe -m promptoire_app --selftest
```

## Repository Setup

- Add the real GitHub remote.
- Run `Check-GitHubPublish.ps1` and fix any failures before pushing. Treat its Buy Me a Coffee support-link warning as a reminder to set the final link before packaging or public release.
- Before pushing workflow changes for the first time, confirm `gh auth status` includes `workflow`.
  If GitHub rejects the push for workflow scope, run:

```bash
gh auth refresh --scopes workflow
```

- Commit on a clean branch.
- Confirm GitHub Actions CI is green after the first push.
- Confirm `.gitignore` excludes local runtime data.
- Confirm `docs/PRIVACY.md` and `SECURITY.md` accurately describe current local data, optional AI calls, and sensitive files.
- Confirm `CHANGELOG.md` lists the release version shown in Settings.
- Confirm GitHub issue and pull request templates warn contributors not to paste private prompts, `prompts.json`, `promptoire.config.json`, or API keys.
- Set the final Buy Me a Coffee link in Settings or keep the blank default; blank/generic root links prompt the user to configure support instead of opening a generic page.
- Confirm the Improve Library panel shows `Copy outline library` as the default export action, offers `Edit instructions` and `Save outline`, keeps `Copy outline request` beside it, and tucks `Copy for AI` / JSON export under `JSON options`.
- Confirm `Edit instructions` changes the outline prompt used by `Copy outline library` and `Improve with AI now`; `Reset default` restores the built-in instruction; JSON instructions stay under `JSON options`.
- Confirm `Paste from clipboard` fills the import box and previews the pasted outline or JSON before merge.
- Confirm `Load from file` accepts outline `.txt` / `.md`, CSV `.csv`, and `.json` files.
- Confirm nested bullet outlines and `Sub-subsection:` / `Nested subsection:` labels import as nested sections.
- Confirm deeper Markdown prompt headings like `### Prompt title` import as prompt titles when followed by body text.
- Confirm YAML-style `- Title:` blocks with indented `Prompt:` / `Tags:` fields import as separate prompts.
- Confirm Markdown tables with `Title` and `Prompt` columns import as prompts.
- Confirm CSV tables with `Title` and `Prompt` columns import as prompts.
- Confirm JSON compatibility imports accept `sections/subsections/items` aliases as well as the native `categories/subcategories/prompts` shape.
- Confirm flat JSON prompt rows can use `path`, `section`, and `subsection` fields to choose their destination section.
- Confirm JSON image prompt rows accept aliases such as `negative_prompt`, `image_model`, `parameters`, and `cfg_scale`.
- Confirm plain JSON string prompts import as prompts with derived titles.
- Confirm import preview shows incoming/new/updated/unchanged counts and that the safe-merge note changes when only Add or only Update is selected.
- Confirm the merge button is disabled when the selected Add/Update mode has no selected changes to merge.
- Confirm normal imports use the safe merge card, and `Replace library` stays tucked in the danger section.
- Build from source once with `setup.bat` and `Promptoire.bat`.
- Confirm `Create-PromptoireShortcut.ps1` creates or refreshes the `PROMPTOIRE` desktop shortcut.
- Confirm `Check-PromptoireShortcut.ps1` verifies that the desktop shortcut launches this checkout.
- If the folder display name is still lowercase, close tools that are inside it and run `Rename-PromptoireFolder.ps1`.
- Launch `Promptoire.bat --selftest` once and confirm `_selftest.json` reports `"mock": false` and an empty `"error"`.

## Optional Build

```bat
build.bat
```

The build output lives in `dist\Promptoire\` and should not be committed.
