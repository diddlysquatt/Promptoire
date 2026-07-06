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

These are the same checks run by `.github/workflows/ci.yml`.

```bash
python tests/test_smoke.py
python -m py_compile promptoire_app/api.py promptoire_app/core/library.py tests/test_smoke.py
node --check promptoire_app/web/js/app.js
node --check promptoire_app/web/js/settings.js
node --check promptoire_app/web/js/bulk.js
node --check promptoire_app/web/js/bridge.js
.\.venv\Scripts\python.exe -m promptoire_app --selftest
```

## Repository Setup

- Add the real GitHub remote.
- Commit on a clean branch.
- Confirm GitHub Actions CI is green after the first push.
- Confirm `.gitignore` excludes local runtime data.
- Confirm `docs/PRIVACY.md` and `SECURITY.md` accurately describe current local data, optional AI calls, and sensitive files.
- Confirm GitHub issue and pull request templates warn contributors not to paste private prompts, `prompts.json`, `promptoire.config.json`, or API keys.
- Set the final Buy Me a Coffee link in Settings or keep the blank default; blank links prompt the user to configure support instead of opening a generic page.
- Confirm the Improve Library panel has both `Copy for AI` for JSON updates and `Copy outline request` for non-JSON prompt batches.
- Confirm normal imports use the safe merge card, and `Replace library` stays tucked in the danger section.
- Build from source once with `setup.bat` and `Promptoire.bat`.
- Launch `Promptoire.bat --selftest` once and confirm `_selftest.json` reports `"mock": false` and an empty `"error"`.

## Optional Build

```bat
build.bat
```

The build output lives in `dist\Promptoire\` and should not be committed.
