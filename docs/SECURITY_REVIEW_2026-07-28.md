# Promptoire Security Review — 2026-07-28

## Executive Summary

Promptoire's runtime design is appropriately narrow for a local-first desktop
app: it loads bundled local frontend assets, has no telemetry or third-party
scripts, escapes prompt content before search highlighting, fixes the optional
AI call to the official OpenAI HTTPS endpoint, uses atomic local writes, and
keeps GitHub workflow permissions scoped to their jobs.

The security release gate is **passed**. The private prompt library was removed
from every reachable local and private-remote ref, the old blob was pruned, and
a fresh mirror of the private GitHub repository independently passed the
reachable-history scan. Pillow was upgraded to 12.3.0, all installed direct
dependencies returned zero OSV advisories, and the two defense-in-depth code
findings were fixed with smoke coverage.

GitHub remains private, PR #1 remains the release vehicle, and Pages remains
inactive until the scheduled launch. An offline private recovery bundle was
created before the rewrite and must never be published.

## Scope and Method

Reviewed the Python/pywebview backend, vanilla HTML/CSS/JavaScript frontend,
local persistence, clipboard and external-link paths, optional OpenAI request,
build scripts, dependency state, GitHub workflows, documentation, current git
tree, and all reachable git history.

The dependency check queried OSV for the installed direct dependencies. The
attempt to install `pip-audit` timed out, so OSV's version-specific API was used
directly instead.

## Critical Severity

No critical findings.

## High Severity

### SEC-001 — Private prompt library remains in reachable git history

**Status: Resolved 2026-07-28.**

**Evidence:** Commit `cdc9ac2a` contains a 40-prompt legacy `prompts.json`.
Commit `96584e68` removes the current path, but deletion does not remove the
older blob. The commit is an ancestor of the current branch and is reachable
from local and remote branches.

**Impact:** Changing the repository from private to public would expose the
historical prompt library to anyone who clones or browses the repository
history.

**Required remediation:** While the remote is still private, rewrite every
reachable branch and tag so the private path and blob are absent, force-update
the intended private remote refs carefully, and independently verify the result
before changing visibility. Rotate any credential if later inspection finds
one in the removed data.

**Guard added:** `Check-GitHubPublish.ps1:151-173` now fails when sensitive
runtime paths occur anywhere in reachable history.

**Verification:** The rewritten object database no longer contains the old
private blob. The guarded scan passes locally, the intended private PR branch
was updated with an exact force-with-lease, and a new mirror clone from GitHub
contains no reachable private runtime path.

## Medium Severity

### SEC-002 — Current packaging environment contains vulnerable Pillow 12.2.0

**Status: Resolved 2026-07-28.**

**Evidence:** The active `.venv` has `Pillow==12.2.0`. A version-specific OSV
query returned 26 advisories for 12.2.0, including
[`GHSA-45hq-cxwh-f6vc`](https://osv.dev/vulnerability/GHSA-45hq-cxwh-f6vc)
and [`PYSEC-2026-3496`](https://osv.dev/vulnerability/PYSEC-2026-3496), both
fixed in 12.3.0. The same OSV query returned zero advisories for Pillow 12.3.0
and for the other installed direct dependencies checked.

`requirements.txt:7` allows the old version, and `build.bat:7` refreshes only
PyInstaller before packaging, so the stale Pillow wheel would be copied into a
build made from this environment.

**Impact:** The reviewed Pillow issues concern malformed image/font parsing,
memory safety, and denial of service. Promptoire currently opens only its own
bundled tray asset, which reduces practical exposure, but shipping a dependency
with known fixes available is not an acceptable release baseline.

**Required remediation:** Require Pillow 12.3.0 or newer, install the complete
runtime requirements in the build step, rebuild in a clean environment, and
rerun a version-specific dependency audit before packaging.

**Verification:** `requirements.txt` now requires Pillow 12.3.0 or newer,
`build.bat` upgrades the complete requirements set before packaging, the active
build environment contains Pillow 12.3.0, and version-specific OSV queries
returned zero advisories for Pillow, pywebview, pyperclip, pystray, keyboard,
and PyInstaller. Dependabot now checks Python dependencies weekly.

## Low Severity

### SEC-003 — External-link bridge does not enforce an HTTP(S) scheme

**Status: Resolved 2026-07-28.**

**Evidence:** `promptoire_app/api.py:428-433` passes the received value directly
to `webbrowser.open`. Frontend and settings normalization reduce accidental
bad values, but the Python trust boundary accepts any scheme.

**Impact:** If bundled frontend execution were compromised or local config were
tampered with, a crafted value could invoke a registered local protocol handler.
The current escaped rendering and local-only frontend make exploitation
unlikely.

**Recommended remediation:** Parse the URL again in Python and allow only
`https` (or explicitly `http` and `https`) before opening it.

**Verification:** The Python bridge now requires an HTTPS URL with a hostname.
Smoke coverage confirms that valid GitHub HTTPS links open while HTTP, `file:`,
`javascript:`, and non-URL values are rejected without invoking the browser.

### SEC-004 — Windows clipboard fallback unnecessarily invokes a shell

**Status: Resolved 2026-07-28.**

**Evidence:** `promptoire_app/platform/clipboard.py:26` launches the constant
command `clip` with `shell=True`.

**Impact:** The command is constant and prompt text is sent through standard
input, so no direct command-injection path was found. Removing the shell is
still safer and easier to reason about.

**Recommended remediation:** Invoke `clip.exe` as an argument list with
`shell=False`.

**Verification:** The fallback now launches `["clip.exe"]` directly and the
smoke test asserts both the argument list and absence of a shell invocation.

## Informational / Accepted Local Tradeoffs

### SEC-005 — Optional API key is stored as plain text locally

**Evidence:** `promptoire_app/core/settings.py:181-188` keeps the configured key,
and `promptoire_app/core/settings.py:220-225` serializes settings as JSON.

**Assessment:** This is disclosed in Privacy and Security documentation, no key
is required for the normal copy/paste workflow, non-OpenAI credentials are
removed during migration, and the network client uses the fixed official
OpenAI endpoint (`promptoire_app/core/ai_improve.py:14-39`). A future Windows
Credential Manager integration would improve local credential protection.

## Positive Controls Verified

- Dynamic prompt/category content uses text nodes; search and placeholder
  markup paths escape content first (`components.js:38-45`,
  `launcher.js:445-455`).
- No `eval`, `Function`, `document.write`, third-party script, telemetry, or
  analytics path was found.
- OpenAI requests use a fixed HTTPS endpoint and a model allowlist.
- Library and settings writes use temporary files plus atomic replacement;
  rolling backups are created locally.
- Private runtime data is ignored, current-tree publication guards exist, and
  the strengthened guard now checks reachable history.
- CI defaults to read-only repository contents; Pages deployment is manual and
  has only the permissions required for Pages.

## Release Decision

**Security-approved for the scheduled release.** The full source release gate,
native WebView self-test, dependency query, and local/remote history scans pass.
The remaining operational gate is to build and test the clean portable package,
verify its checksum and draft release, and perform the signed-out GitHub/Pages
review before changing repository visibility.
