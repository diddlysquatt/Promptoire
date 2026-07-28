param(
  [switch]$SkipReleaseGate
)

$ErrorActionPreference = "Stop"

$root = (Get-Item -LiteralPath (Split-Path -Parent $MyInvocation.MyCommand.Path)).FullName
Set-Location -LiteralPath $root

# Checks folder naming, git remote, clean state, private files, GitHub auth scope, and the local release gate.
$failed = $false
$warnings = 0
$nextSteps = @()

function Pass($message) {
  Write-Host "[OK] $message"
}

function Warn($message) {
  $script:warnings += 1
  Write-Host "[WARN] $message"
}

function Fail($message) {
  $script:failed = $true
  Write-Host "[FAIL] $message"
}

function NextStep($message) {
  $script:nextSteps += $message
}

function Normalize-Link($value) {
  if ($null -eq $value) {
    return ""
  }
  return ([string]$value).Trim()
}

function Normalize-OptionalUrl($value) {
  $raw = Normalize-Link $value
  if (-not $raw) {
    return ""
  }
  if ($raw -match "^[a-zA-Z][a-zA-Z0-9+.-]*://") {
    return $raw
  }
  if ($raw -notmatch "^[/#]" -and $raw -match "^[^\s/]+\.[^\s]+") {
    return "https://$raw"
  }
  return $raw
}

function Test-GenericCoffeeUrl($value) {
  $raw = Normalize-OptionalUrl $value
  if (-not $raw) {
    return $false
  }
  try {
    $uri = [Uri]$raw
  } catch {
    return $false
  }
  $hostName = $uri.Host.ToLowerInvariant()
  if ($hostName.StartsWith("www.")) {
    $hostName = $hostName.Substring(4)
  }
  $path = $uri.AbsolutePath.Trim("/")
  return (
    $uri.Scheme.ToLowerInvariant() -in @("http", "https") -and
    $hostName -eq "buymeacoffee.com" -and
    -not $path -and
    -not $uri.Query -and
    -not $uri.Fragment
  )
}

function Run-Git($arguments) {
  $previousPreference = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $output = & git @arguments 2>&1
    return @{
      ExitCode = $LASTEXITCODE
      Text = ($output | Out-String).Trim()
    }
  } finally {
    $ErrorActionPreference = $previousPreference
  }
}

Write-Host "Promptoire GitHub publish readiness"
Write-Host "Root: $root"
Write-Host ""

$folderName = Split-Path -Leaf $root
if ($folderName -ceq "PROMPTOIRE") {
  Pass "Project folder display name is PROMPTOIRE."
} elseif ($folderName -ieq "PROMPTOIRE") {
  Warn "Project folder display name is '$folderName'. Close tools in this folder and run Rename-PromptoireFolder.ps1 if you want PROMPTOIRE casing."
  NextStep "Folder casing: close tools in this folder, then run .\Rename-PromptoireFolder.ps1."
} else {
  Warn "Project folder display name is '$folderName'. Expected PROMPTOIRE before packaging or sharing."
  NextStep "Folder casing: move or rename this checkout so the folder displays as PROMPTOIRE."
}

if (-not (Test-Path -LiteralPath (Join-Path $root ".git"))) {
  Fail "This folder is not a git repository."
} else {
  Pass "Git repository found."
}

$branch = Run-Git @("branch", "--show-current")
if ($branch.ExitCode -eq 0 -and $branch.Text) {
  Pass "Current branch: $($branch.Text)"
} else {
  Fail "Could not determine the current branch."
}

$status = Run-Git @("status", "--short")
if ($status.ExitCode -eq 0 -and -not $status.Text) {
  Pass "Working tree is clean."
} elseif ($status.ExitCode -eq 0) {
  Fail "Working tree has uncommitted changes. Commit or stash before publishing."
  NextStep "Git state: commit or stash local changes before publishing."
  Write-Host $status.Text
} else {
  Fail "Could not read git status."
}

$remote = Run-Git @("remote", "get-url", "origin")
if ($remote.ExitCode -eq 0 -and $remote.Text) {
  if ($remote.Text -match "github\.com[:/]") {
    Pass "GitHub origin remote: $($remote.Text)"
  } else {
    Fail "Origin remote is not a GitHub URL: $($remote.Text)"
  }
} else {
  Fail "Missing origin remote."
}

foreach ($file in @("prompts.json", "promptoire.config.json", "_selftest.json")) {
  $tracked = Run-Git @("ls-files", "--error-unmatch", "--", $file)
  if ($tracked.ExitCode -eq 0) {
    Fail "Private runtime file is tracked: $file"
  } else {
    Pass "Private runtime file is not tracked: $file"
  }
}

$privateHistoryPaths = @(
  "prompts.json",
  "promptoire.config.json",
  "_selftest.json",
  "backups",
  ".env",
  ".env.local"
)
$privateHistory = Run-Git @(
  "log",
  "--all",
  "--format=%H",
  "--",
  $privateHistoryPaths
)
if ($privateHistory.ExitCode -ne 0) {
  Fail "Could not inspect reachable git history for private runtime files."
} elseif ($privateHistory.Text) {
  $historyCount = @($privateHistory.Text -split "\r?\n" | Where-Object { $_ }).Count
  Fail "Private runtime paths occur in reachable git history ($historyCount commit(s)). Making the repository public would expose them."
  NextStep "Git history: remove private runtime files from every reachable branch/tag, force-update only the still-private remote, then rerun this check."
} else {
  Pass "No private runtime paths occur in reachable git history."
}

$configPath = Join-Path $root "promptoire.config.json"
if (Test-Path -LiteralPath $configPath) {
  try {
    $config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
    $coffee = ""
    if ($null -ne $config.links -and $null -ne $config.links.coffee) {
      $coffee = Normalize-OptionalUrl $config.links.coffee
    }
    if ($coffee -and -not (Test-GenericCoffeeUrl $coffee)) {
      Pass "Buy Me a Coffee support link is configured locally."
    } else {
      Warn "Buy Me a Coffee support link is blank or generic. Set it in Settings before packaging if you want support links active."
      NextStep "Support link: add your real Buy Me a Coffee URL in Settings before packaging."
    }
  } catch {
    Warn "Could not read promptoire.config.json to check the Buy Me a Coffee link: $($_.Exception.Message)"
    NextStep "Support link: open Settings once, save the support link, then rerun this check."
  }
} else {
  Warn "promptoire.config.json is not present, so the Buy Me a Coffee support link will be blank by default."
  NextStep "Support link: launch Promptoire and save your Buy Me a Coffee URL in Settings."
}

if (Test-Path -LiteralPath (Join-Path $root ".github\workflows\ci.yml")) {
  Pass "GitHub Actions workflow exists."
} else {
  Fail "Missing .github\workflows\ci.yml."
}

$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($gh) {
  $previousPreference = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $authOutput = & gh auth status -h github.com 2>&1
    $authExitCode = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $previousPreference
  }
  $authText = ($authOutput | Out-String).Trim()
  if ($authExitCode -eq 0) {
    Pass "GitHub CLI is authenticated."
    if ($authText -match "Token scopes:\s*.*workflow") {
      Pass "GitHub token includes workflow scope."
    } else {
      Fail "GitHub token is missing workflow scope. Run: gh auth refresh -h github.com -s workflow"
      NextStep "GitHub workflow scope: run gh auth refresh -h github.com -s workflow."
      if ($authText) {
        Write-Host $authText
      }
    }
  } else {
    Fail "GitHub CLI is not authenticated for github.com. Run: gh auth login -h github.com"
    NextStep "GitHub auth: run gh auth login -h github.com."
    if ($authText) {
      Write-Host $authText
    }
  }
} else {
  Fail "GitHub CLI (gh) is not installed or not on PATH."
  NextStep "GitHub CLI: install gh or add it to PATH before publishing."
}

if (-not $SkipReleaseGate) {
  Write-Host ""
  Write-Host "Running local release gate..."
  & (Join-Path $root "check-release.bat")
  if ($LASTEXITCODE -eq 0) {
    Pass "Local release gate passed."
  } else {
    Fail "Local release gate failed."
    NextStep "Local release gate: fix the failure above, then rerun .\check-release.bat."
  }
} else {
  Write-Host ""
  Write-Host "Skipped local release gate."
}

Write-Host ""
if ($nextSteps.Count -gt 0) {
  Write-Host "Next steps:"
  for ($i = 0; $i -lt $nextSteps.Count; $i += 1) {
    Write-Host ("  {0}. {1}" -f ($i + 1), $nextSteps[$i])
  }
  Write-Host ""
}

if ($failed) {
  Write-Host "GitHub publish readiness failed. Fix the items above before pushing."
  exit 1
}

if ($warnings -gt 0) {
  Write-Host "GitHub publish readiness passed with $warnings warning(s)."
  exit 0
}

Write-Host "GitHub publish readiness passed."
exit 0
