# Windows: builds Broken Seal Arena with scripts/build.sh in MSYS2 (no WSL) and
# leaves the ROM in build\tbs-en.gba (build\tbs-en.new.gba if an emulator holds
# the first open).
#   .\build.ps1 [-WorkDir DIR] [-Verify]          the GBA ROM
#   .\build.ps1 -Native [-Headless] [-WorkDir DIR] the desktop build, after the ROM:
#                                                 build\native\tbs-native.exe
#                                                 (build\native-headless\ with -Headless)
# -WorkDir  where the upstream clone lives (a Windows path). Without it: the
#           file .alchemy-dir in this folder if there is one, else work\alchemy.
# -Verify   also runs upstream's compare (passes only for unmodified source).
# MSYS2 is looked for at C:\msys64 (or $env:MSYS2_ROOT). See docs\BUILDING.md.
param([string]$WorkDir, [switch]$Verify, [switch]$Native, [switch]$Headless)
$ErrorActionPreference = 'Stop'
if ($WorkDir) { $env:ALCHEMY_DIR = [System.IO.Path]::GetFullPath($WorkDir) }
. "$PSScriptRoot\scripts\msys2.ps1"

if ($Native) {
  $opts = if ($Headless) { '--headless' } else { '' }
  Invoke-Sh "bash '$ShRoot/scripts/build-native.sh' $opts" -System MINGW32
  if ($LASTEXITCODE -ne 0) { throw "Native build failed" }
  $dir = if ($Headless) { 'native-headless' } else { 'native' }
  Write-Host "Program: $(Join-Path $PSScriptRoot "build\$dir\tbs-native.exe")"
  return
}

$opts = if ($Verify) { '--verify' } else { '' }
Invoke-Sh "bash '$ShRoot/scripts/build.sh' $opts"
if ($LASTEXITCODE -ne 0) { throw "Build failed" }
if (Test-Path (Join-Path $PSScriptRoot 'build\tbs-en.new.gba')) { Write-Host "Note: build\tbs-en.new.gba is the newer ROM (the other is in use)." }
Write-Host "ROM: $(Join-Path $PSScriptRoot 'build\tbs-en.gba')"
