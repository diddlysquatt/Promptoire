# Promptoire Privacy

Promptoire is local-first. By default, it keeps your prompt library and settings on your own machine and does not send telemetry.

## What Stays Local

- Your real prompt library lives in `prompts.json`.
- App settings, including optional AI provider settings, live in `promptoire.config.json`.
- Backups live in `backups/`.
- These runtime files are ignored by git and should not be published.

## When Data Leaves Your Machine

Promptoire only sends prompt data out when you choose to do it:

- If you click **Copy outline library**, **Copy for AI**, or another export button, the app puts your library on your clipboard so you can paste it into the LLM or tool you choose.
- If you click **Improve with AI now**, Promptoire sends the library and your editable instructions to the AI provider configured in Settings.
- If you open a support or external link, your browser handles that link outside Promptoire.

## API Keys

Optional AI API keys are stored locally in `promptoire.config.json`. Do not commit or share that file. For public releases, keep `promptoire.config.json`, `.env`, backups, caches, and `prompts.json` out of git.

## Public Example Data

The repository includes `prompts.example.json` only as clean sample data. It is not your private library.
