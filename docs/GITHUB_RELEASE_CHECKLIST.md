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

```bash
python tests/test_smoke.py
python -m py_compile promptoire_app/api.py promptoire_app/core/library.py tests/test_smoke.py
node --check promptoire_app/web/js/app.js
node --check promptoire_app/web/js/settings.js
node --check promptoire_app/web/js/bulk.js
node --check promptoire_app/web/js/bridge.js
```

## Repository Setup

- Add the real GitHub remote.
- Commit on a clean branch.
- Confirm `.gitignore` excludes local runtime data.
- Confirm `README.md` has the final Buy Me a Coffee link or explains where to set it.
- Build from source once with `setup.bat` and `Promptoire.bat`.

## Optional Build

```bat
build.bat
```

The build output lives in `dist\Promptoire\` and should not be committed.
