# Windows SmartScreen and Promptoire

Promptoire is a portable Windows application. Windows may show an **Unknown
publisher** or **Windows protected your PC** warning for an unsigned release,
even when that release is safe and its source is public.

## Before running a release

Only download Promptoire from the official GitHub repository:

`https://github.com/diddlysquatt/Promptoire`

Every release includes a SHA-256 checksum file. Compare it with the downloaded
ZIP before running the application:

```powershell
Get-FileHash .\Promptoire-2.5.0-windows-x64.zip -Algorithm SHA256
```

The resulting hash must exactly match the published `.sha256.txt` file. You can
also inspect the complete source and build instructions in the repository.

## Why the warning appears

Microsoft Defender SmartScreen evaluates both the reputation of the downloaded
file and the reputation of its signing publisher. A new unsigned binary starts
without either form of reputation, and each unsigned update starts over.

A self-signed certificate does not help public users. A normal OV or EV
certificate shows a verified publisher and allows publisher reputation to build,
but Microsoft no longer grants EV certificates an automatic first-download
SmartScreen bypass.

## Practical signing options for the project

1. **Microsoft Store using MSIX** — the most reliable way to avoid download
   warnings because Store-packaged apps are signed by Microsoft. This requires a
   separate Store package and submission process.
2. **Microsoft Artifact Signing** — Microsoft's recommended non-Store option.
   The Basic tier is currently about $9.99/month and integrates with GitHub
   Actions. It establishes a verified publisher, but a brand-new app can still
   show warnings while reputation develops.
3. **SignPath Foundation for open source** — qualifying open-source projects can
   apply for free signing. The project must already be public, released,
   documented, actively maintained, and accepted under SignPath's policies.
4. **Unsigned GitHub release with checksums** — reasonable for an initial
   community release when the warning and verification steps are explained
   honestly. It does not remove SmartScreen.

Promptoire's initial launch uses the fourth option while preserving a clean path
to SignPath or Microsoft Artifact Signing after the first public release.

## Maintainer policy

- Build releases only from reviewed, committed source.
- Publish the release ZIP and checksum together.
- Never modify a signed binary after signing.
- Use the same signing identity for every version once signing is introduced.
- Keep release provenance, privacy behavior, and external network actions
  documented.

Official references:

- [SmartScreen reputation for Windows app developers](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation)
- [Windows code-signing options](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options)
- [SignPath Foundation conditions for open-source projects](https://signpath.org/terms.html)
