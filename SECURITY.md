# Security Policy

Promptoire is a local-first desktop app for storing and copying prompts. Please do not post private prompt libraries, API keys, or config files in public issues.

## Reporting A Vulnerability

If you find a vulnerability, open a GitHub issue with reproduction steps that use sample data only. If the report requires sensitive details, share the minimum needed information and redact secrets, prompt contents, machine paths, and API keys.

## Sensitive Local Files

These files and folders can contain private data and should stay out of commits:

- `prompts.json`
- `promptoire.config.json`
- `backups/`
- `.webcache/`
- `.env` and `.env.local`

The repository includes `.gitignore` rules for these paths, and CI runs smoke checks against `prompts.example.json` rather than a real local library.

Before changing repository visibility, run `Check-GitHubPublish.ps1`. It checks both the current tree and reachable git history because deleting a private file in a later commit does not remove it from earlier commits.

## Local Security Model

- The app renders bundled local HTML/CSS/JavaScript and does not load third-party scripts.
- Prompt and category text is rendered as text; search highlighting escapes prompt content before adding markup.
- The optional direct AI action uses the fixed official OpenAI HTTPS endpoint. Manual copy/paste works without a network call or API key.
- The optional API key is stored as plain text in the local config file, not in an OS credential vault. See [Privacy](docs/PRIVACY.md) for the exact boundary.
- Portable releases are initially unsigned. Verify the published SHA-256 checksum before running a download.

## Supported Versions

Security fixes are handled on the active `main` branch once the project is published.

The latest pre-release repository audit is
[Security Review — 2026-07-28](docs/SECURITY_REVIEW_2026-07-28.md).
