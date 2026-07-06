$ErrorActionPreference = "Stop"

$rootItem = Get-Item -LiteralPath (Split-Path -Parent $MyInvocation.MyCommand.Path)
$root = $rootItem.FullName
$parent = Split-Path -Parent $root
$currentName = $rootItem.Name
$tmpName = "PROMPTOIRE.__case_rename_tmp__"
$targetName = "PROMPTOIRE"
$tmpPath = Join-Path $parent $tmpName
$targetPath = Join-Path $parent $targetName

if ($currentName -ceq $targetName) {
  Write-Host "Folder is already named $targetName."
  powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "Create-PromptoireShortcut.ps1")
  exit 0
}

if ($currentName -cne "promptoire") {
  throw "Expected folder name 'promptoire' or '$targetName', found '$currentName'."
}

if (Test-Path -LiteralPath $tmpPath) {
  throw "Temporary path already exists: $tmpPath"
}

Set-Location -LiteralPath $parent

try {
  Rename-Item -LiteralPath $root -NewName $tmpName
  Rename-Item -LiteralPath $tmpPath -NewName $targetName
} catch {
  $message = $_.Exception.Message
  if ((Test-Path -LiteralPath $tmpPath) -and -not (Test-Path -LiteralPath $root)) {
    try {
      Rename-Item -LiteralPath $tmpPath -NewName "promptoire"
    } catch {
      Write-Host "Could not roll back temporary rename: $($_.Exception.Message)"
    }
  }
  throw "Could not rename folder. Close Promptoire, Codex, terminals, and File Explorer windows that are inside the project, then run this again. Original error: $message"
}

$shortcutScript = Join-Path $targetPath "Create-PromptoireShortcut.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File $shortcutScript
Write-Host "Folder renamed to: $targetPath"
