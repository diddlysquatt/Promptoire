# PROMPTOIRE GitHub Release Checklist

Use this before the first public push.

## Local Data

- Keep your real `prompts.json` on your machine.
- Do not publish API keys, `promptoire.config.json`, backups, caches, or virtual environments.
- Confirm those paths never occur in any reachable branch or tag; deleting them in a later commit is not enough.
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
node --check promptoire_app/web/js/bridge.js
node --check promptoire_app/web/js/state.js
node --check promptoire_app/web/js/components.js
node --check promptoire_app/web/js/launcher.js
node --check promptoire_app/web/js/editor.js
node --check promptoire_app/web/js/bulk.js
node --check promptoire_app/web/js/settings.js
node --check promptoire_app/web/js/app.js
.\.venv\Scripts\python.exe -m promptoire_app --selftest
```

## Repository Setup

- Add the real GitHub remote.
- Run `Check-GitHubPublish.ps1` and fix any failures before pushing. Treat its folder-name and Buy Me a Coffee support-link warnings as reminders to finish local polish before packaging or public release; scheme-less support links are normalized before that check.
- Before pushing workflow changes for the first time, confirm `gh auth status` includes `workflow`.
  If GitHub rejects the push for workflow scope, run:

```bash
gh auth refresh --scopes workflow
```

- Commit on a clean branch.
- Confirm GitHub Actions CI is green after the first push.
- Confirm `.gitignore` excludes local runtime data.
- Confirm `Check-GitHubPublish.ps1` reports no private runtime paths in reachable git history before changing visibility.
- Confirm `docs/PRIVACY.md` and `SECURITY.md` accurately describe current local data, optional AI calls, and sensitive files.
- Confirm `CHANGELOG.md` lists the release version shown in Settings.
- Confirm GitHub issue and pull request templates warn contributors not to paste private prompts, `prompts.json`, `promptoire.config.json`, or API keys.
- Confirm Settings -> About opens the GitHub source link.
- Confirm Settings -> About displays **Brought to you by Stoned Ape**.
- Confirm the built-in `links.coffee` default points to the finished Promptoire Buy Me a Coffee profile; links with or without `https://` are normalized, and blank/generic root links never open a generic page.
- Confirm Settings -> System can open the local data folder for `prompts.json`, `promptoire.config.json`, and backups.
- Confirm the launcher has no bottom action footer, **+ New** sits beside All/Text/Image/Favorites, the pencil opens **Edit Library**, and the recovered height belongs to prompt results.
- Confirm All/Text/Image/Favorites, **+ New**, and the density button stay on one row at the 360px minimum width in every density mode.
- Confirm the top pin prevents both blur hiding and copy-then-hide, unpinning restores auto-hide, and Settings has no duplicate **Copy then vanish** control.
- Confirm category rail buttons select on the first click, clearly show their selected state, and can still be dragged horizontally.
- Confirm the sticky Edit Library filter is fully opaque while categories and prompts scroll beneath it.
- Confirm every window edge/corner resizes in both axes, the result list expands with the window, and 360×420 remains the minimum size.
- Confirm Improve Library shows `Improve with AI now` near the top, keeps the improvement instructions visible, and offers `Copy instructions + library`, `Copy library only`, `Copy instructions only`, and `Save library outline` with unambiguous labels.
- Confirm `Save instructions` changes the prompt used by `Copy instructions + library` and `Improve with AI now`; `Reset default` restores the built-in instruction; `Create prompts for a topic` accepts an optional topic/workflow; JSON instructions and exports stay under `More options`.
- Confirm the optional OpenAI connection is at the bottom of Improve Library (not Settings), only offers the current GPT-5.6 family, saves locally, and opens/focuses itself when direct improve is clicked without a key.
- Confirm an empty library offers both `New prompt` and `Import prompts`, with `Import prompts` opening the Improve Library flow.
- Confirm `Paste from clipboard` fills the import box and previews the pasted outline or JSON before merge; manual paste into the import box should auto-preview too.
- Confirm the five import actions remain compact and occupy exactly two rows at the default and minimum window widths.
- Confirm `Clear` empties the import box, preview, and safe-merge state.
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
- Confirm import preview shows incoming/new/updated/unchanged counts plus repeated/ambiguous skips, and that the safe-merge note changes when only Add or only Update is selected.
- Confirm the merge button is disabled when the selected Add/Update mode has no selected changes to merge.
- Confirm **Update existing** uses id first, otherwise a unique title in the exact section path, never moves/deletes prompts, and never clears a nonblank local field with a blank import value.
- Confirm **Add new** adds only unmatched prompts, creates missing nested paths, and preview/apply report the same result for duplicate input.
- Confirm normal imports use the safe merge card, and `Replace library` stays tucked in the danger section.
- Build from source once with `setup.bat` and `Promptoire.bat`.
- Confirm `Create-PromptoireShortcut.ps1` creates or refreshes the `PROMPTOIRE` desktop shortcut.
- Confirm `Check-PromptoireShortcut.ps1` verifies that the desktop shortcut launches this checkout.
- If the folder display name is still lowercase, close tools that are inside it and run `Rename-PromptoireFolder.ps1`.
- Launch `Promptoire.bat --selftest` once and confirm `_selftest.json` reports `"mock": false`, `"native_hwnd": true`, `"window_icon": true`, `"window_icon_applied": true`, `"minimum_window": [360, 420]`, and an empty `"error"`.
- Require the release gate's isolated Windows tray probe to pass real minimize-to-tray, native close-to-tray, restore, notification-icon, and explicit-quit behavior.
- Preview `docs/index.html`, `docs/privacy.html`, and `docs/smartscreen.html` at desktop and mobile widths; confirm all four current app screenshots render and contain only the clean starter library.
- Keep `.github/workflows/pages.yml` manual-only while the repository is private. After making the repository public, select GitHub Actions under **Settings → Pages**, run **Publish documentation site**, and verify `https://diddlysquatt.github.io/Promptoire/` in a signed-out browser.

## Optional Build

```bat
build.bat
```

The build output lives in `dist\Promptoire\` and should not be committed.
