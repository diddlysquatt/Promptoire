# Promptoire Launch Checklist

Target launch window: **Tuesday, July 21, 2026 at 9:00 AM Central**
(10:00 AM Eastern / 7:00 AM Pacific).

The local heartbeat is scheduled for **8:30 AM Central**. It is notification-only:
it cannot merge, publish a release, or change repository visibility.

## Thirty minutes before

- Confirm the repository is still **Private**.
- Confirm PR #1 is still a **Draft**.
- Confirm GitHub Actions is green on the latest commit.
- Run `git status --short` and confirm the branch is clean.
- Run `check-release.bat` if anything changed after the final packaged build.
- Create or update the draft release and confirm both the ZIP and SHA-256 file are attached.
- Test the ZIP once from a clean temporary folder.
- Read the README from top to bottom in GitHub's rendered view.
- Confirm the GitHub Pages workflow is present but has not been run while the repository is private.
- Confirm the top coffee icon opens the finished Promptoire support profile.

## Publish order

Do these manually. The heartbeat never performs them.

1. Merge PR #1 into `main`.
2. Confirm CI is green on `main`.
3. Publish the prepared GitHub release.
4. Change repository visibility from **Private** to **Public**.
5. In **Settings → Pages**, select **GitHub Actions**, then manually run the
   **Publish documentation site** workflow. Confirm
   `https://diddlysquatt.github.io/Promptoire/` loads.
6. Open the public repository in a signed-out browser and verify:
   - README images render.
   - Latest Release download works.
   - License, Privacy, Security, and Contributing links work.
   - No personal `prompts.json`, configuration, backups, or API keys are present.
7. Post the launch message at **9:00 AM Central** and stay available for replies.

## Suggested launch copy

> I built Promptoire: a fast, local-first Windows prompt library.
>
> Hit a global hotkey, find the prompt you need, click once to copy, and get
> straight back to work. It supports nested categories, compact layouts,
> drag-and-drop organization, placeholders, image prompts, and an outline-first
> workflow for improving or generating whole prompt libraries with any LLM.
>
> No account, no telemetry, no cloud lock-in. Free and open source:
> https://github.com/diddlysquatt/Promptoire

## Launch channels

- GitHub release and repository first.
- X at 9:00 AM Central.
- LinkedIn between 10:00 AM and noon Central.
- Relevant communities only where self-promotion is permitted; tailor the post
  to each community instead of dropping the same link everywhere.
- If using Product Hunt, schedule it separately for the start of its Pacific
  Time launch day and be available throughout that day.

## After launch

- Reply quickly to early questions and bug reports.
- Pin a concise GitHub issue for known limitations if any surface.
- Record downloads, stars, issues, and referral sources after 1 hour, 24 hours,
  72 hours, and 7 days.
- Do not ship rushed launch-day features; prioritize installation blockers and
  data-safety issues.
