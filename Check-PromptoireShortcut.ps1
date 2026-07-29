$ErrorActionPreference = "Stop"

$root = (Get-Item -LiteralPath (Split-Path -Parent $MyInvocation.MyCommand.Path)).FullName
$launcher = (Join-Path $root "Promptoire.bat")
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "PROMPTOIRE.lnk"

if (-not (Test-Path -LiteralPath $launcher)) {
  throw "Promptoire.bat was not found next to this script."
}

if (-not (Test-Path -LiteralPath $shortcutPath)) {
  throw "PROMPTOIRE desktop shortcut is missing. Run setup.bat or Create-PromptoireShortcut.ps1."
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$target = [string]$shortcut.TargetPath
$arguments = [string]$shortcut.Arguments
$workingDirectory = [string]$shortcut.WorkingDirectory

if ($workingDirectory -and $workingDirectory -ine $root) {
  throw "PROMPTOIRE shortcut points at the wrong working folder: $workingDirectory"
}

$pointsAtLauncher = ($target -ine "" -and $target -ieq $launcher) -or
  ($arguments -ine "" -and $arguments.IndexOf($launcher, [StringComparison]::OrdinalIgnoreCase) -ge 0)

if (-not $pointsAtLauncher) {
  throw "PROMPTOIRE shortcut does not launch this checkout's Promptoire.bat."
}

Write-Host "Desktop shortcut verified: $shortcutPath"
