$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcher = Join-Path $root "Promptoire.bat"
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "PROMPTOIRE.lnk"
$iconPath = Join-Path $root "icons\replicate-prediction-2j5y20xssnrmc0crx40tp1mzjc.ico"

if (-not (Test-Path -LiteralPath $launcher)) {
  throw "Promptoire.bat was not found next to this script."
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $env:WINDIR "System32\cmd.exe"
$shortcut.Arguments = "/c """"$launcher"""""
$shortcut.WorkingDirectory = $root
if (Test-Path -LiteralPath $iconPath) {
  $shortcut.IconLocation = $iconPath
}
$shortcut.Save()

Write-Host "Shortcut ready: $shortcutPath"
