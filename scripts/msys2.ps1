# Shared by the Windows scripts (dot-source it: . "$PSScriptRoot\msys2.ps1").
# The builds and smoke tests are bash scripts; on Windows they run in MSYS2
# (https://www.msys2.org, a native Windows bash with make and GCC; no WSL).
# Gives the scripts:
#   Invoke-Sh COMMAND [-System NAME]  run a bash command line in MSYS2 (from the
#                                     repo root; -System is the MSYS2 shell:
#                                     UCRT64 by default, MINGW32 for the native
#                                     build)
#   ConvertTo-ShPath PATH             C:\a\b -> /c/a/b
#   $ShRoot                           this repo as an MSYS2 path
#   $AlchemyDir                       the upstream working copy, as an MSYS2 path
#                                     ($env:ALCHEMY_DIR, else the file
#                                     .alchemy-dir, else work/alchemy: the
#                                     lookup in alchemy-dir.sh, which it asks)
# MSYS2 is looked for in $env:MSYS2_ROOT, else C:\msys64. docs\BUILDING.md
# lists the packages.
$Msys2Root = if ($env:MSYS2_ROOT) { $env:MSYS2_ROOT } else { 'C:\msys64' }
$Msys2Bash = Join-Path $Msys2Root 'usr\bin\bash.exe'
if (-not (Test-Path $Msys2Bash)) {
  throw "MSYS2 is not installed at $Msys2Root (winget install MSYS2.MSYS2; see docs\BUILDING.md), or set MSYS2_ROOT"
}
$RepoRoot = Split-Path $PSScriptRoot -Parent

function ConvertTo-ShPath([string]$Path) {
  $full = [System.IO.Path]::GetFullPath($Path)
  if ($full -match '^([A-Za-z]):\\?(.*)$') {
    return '/' + $Matches[1].ToLower() + '/' + ($Matches[2] -replace '\\', '/')
  }
  return $full -replace '\\', '/'
}

function Invoke-Sh([string]$Command, [string]$System = 'UCRT64') {
  $saved = @($env:MSYSTEM, $env:CHERE_INVOKING)
  $env:MSYSTEM = $System
  $env:CHERE_INVOKING = '1'   # a login shell that stays in the current folder
  Push-Location $RepoRoot
  try { & $Msys2Bash -lc $Command }
  finally {
    Pop-Location
    $env:MSYSTEM, $env:CHERE_INVOKING = $saved
  }
}

$ShRoot = ConvertTo-ShPath $RepoRoot
$AlchemyDir = (Invoke-Sh "bash '$ShRoot/scripts/alchemy-dir.sh'" | Select-Object -Last 1).Trim()
