# Promptoire Launch Checklist

Target launch window: **Wednesday, July 29, 2026 at 9:00 AM Central**
(10:00 AM Eastern / 7:00 AM Pacific).

This is the GitHub/X launch window, not an automatic publication. If Product
Hunt is part of the launch, schedule that listing separately for **12:01 AM
Pacific** so it receives a full Product Hunt day.

## Thirty minutes before

- Confirm the repository is still **Private**.
- Confirm PR #1 is still a **Draft**.
- Confirm `Check-GitHubPublish.ps1` reports no private runtime paths anywhere in reachable git history.
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

Use the channel-specific copy in [LAUNCH_POSTS.md](LAUNCH_POSTS.md).

## Launch channels

- GitHub release and repository first.
- X at 9:00 AM Central.
- Pin Promptoire on the maintainer's GitHub profile after it becomes public.
- LinkedIn between 10:00 AM and noon Central if it fits the audience.
- A carefully written Show HN after the public download and documentation have been verified.
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
