# Promptoire Privacy

Promptoire is local-first. By default, it keeps your prompt library and settings on your own machine and does not send telemetry.

## What Stays Local

- Your real prompt library lives in `prompts.json`.
- App settings, including an optional OpenAI API key/model choice, live in `promptoire.config.json`.
- Backups live in `backups/`.
- These runtime files are ignored by git and should not be published.

## When Data Leaves Your Machine

Promptoire only sends prompt data out when you choose to do it:

- If you click **Copy instructions + library**, **Copy library only**, a JSON export, or another export button, the app puts the selected content on your clipboard so you can paste it into the LLM or tool you choose.
- If you click **Paste from clipboard**, the app reads your current clipboard text into the import box for previewing.
- If you click **Improve with AI now**, Promptoire sends your outline library and visible outline improvement instructions directly to OpenAI using the model selected at the bottom of Improve Library.
- If you open a support or external link, your browser handles that link outside Promptoire.

## API Keys

The optional OpenAI API key is stored locally in `promptoire.config.json`. Do not commit or share that file. For public releases, keep `promptoire.config.json`, `.env`, backups, caches, and `prompts.json` out of git.

## Public Example Data

The repository includes `prompts.example.json` only as clean sample data. It is not your private library.
