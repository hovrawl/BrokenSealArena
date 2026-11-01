# Windows wrapper: builds Broken Seal Arena inside WSL with scripts/build.sh and
# leaves the ROM in build\tbs-en.gba (build\tbs-en.new.gba if an emulator holds
# the first open).
#   .\build.ps1 [-WorkDir DIR] [-Distro NAME] [-Verify]
# -WorkDir  where the upstream clone lives, as a path INSIDE WSL (for example
#           '~/alchemy'). Without it: the file .alchemy-dir in this folder if
#           there is one, else ~/brokenseal-arena/alchemy in the WSL home. It must
#           not be under /mnt/c: building on a Windows drive is far too slow and
#           breaks file modes.
# -Distro   the WSL distribution (default: your default one).
# -Verify   also runs upstream's compare (passes only for unmodified source).
# See docs\BUILDING.md.
param([string]$WorkDir, [string]$Distro, [switch]$Verify)
$ErrorActionPreference = 'Stop'
$wsl = @(); if ($Distro) { $wsl = @('-d', $Distro) }
# C:\a\b -> /mnt/c/a/b
$root = (wsl @wsl -- wslpath -a ($PSScriptRoot.Replace('\', '/'))).Trim()
if (-not $root) { throw "WSL is not available (see docs\BUILDING.md)" }
$args2 = @()
if ($WorkDir) { $args2 += @('--work-dir', $WorkDir) }
elseif (-not (Test-Path (Join-Path $PSScriptRoot '.alchemy-dir'))) { $args2 += @('--work-dir', '~/brokenseal-arena/alchemy') }
if ($Verify) { $args2 += '--verify' }
wsl @wsl -- bash "$root/scripts/build.sh" @args2
if ($LASTEXITCODE -ne 0) { throw "Build failed" }
$dest = Join-Path $PSScriptRoot 'build\tbs-en.gba'
if (Test-Path (Join-Path $PSScriptRoot 'build\tbs-en.new.gba')) { Write-Host "Note: build\tbs-en.new.gba is the newer ROM (the other is in use)." }
Write-Host "ROM: $dest"
