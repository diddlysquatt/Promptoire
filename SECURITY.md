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

## Supported Versions

Security fixes are handled on the active `main` branch once the project is published.
