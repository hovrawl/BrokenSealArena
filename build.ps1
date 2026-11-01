# Rebuild TBS (English) in WSL and copy the ROM to build\tbs-en.gba
# Usage: .\build.ps1 [-Verify]   (-Verify also runs compare; only passes for unmodified source)
param([switch]$Verify)
$ErrorActionPreference = 'Stop'
$dest = Join-Path $PSScriptRoot 'build\tbs-en.gba'
# ARENA_LINK4: the half-size opponent sheets are made from the game's own, and
# the ROM is 20 KB longer than the original's 8 MB (main.ld moves the last
# region on by 0x5000 to make room, and the image is padded to match).
$gen = 'python3 /mnt/c/Dev/NahFarn/BrokenSealArena/scripts/gen-opponent-sprites.py ~/alchemy/games/tbs/src/graphics/sprite'
$genTrophies = 'python3 /mnt/c/Dev/NahFarn/BrokenSealArena/scripts/gen-trophy-sprites.py ~/alchemy/games/tbs/src/graphics/sprite'
$cmd = "$gen && $genTrophies && cd ~/alchemy && make -j`$(nproc) tbs-en ROM_END_tbs=0x08805000"
if ($Verify) { $cmd += ' && make compare-tbs-en' }
wsl -d Ubuntu -- bash -lc $cmd
if ($LASTEXITCODE -ne 0) { throw "Build failed" }
$src = '\\wsl.localhost\Ubuntu\home\nathan\alchemy\out\tbs-en\tbs-en.gba'
try {
  Copy-Item $src $dest -Force -ErrorAction Stop
  Write-Host "ROM: $dest"
} catch {
  # An emulator holding the ROM open locks it; leave that copy alone.
  $alt = Join-Path $PSScriptRoot 'build\tbs-en.new.gba'
  Copy-Item $src $alt -Force
  Write-Host "ROM is in use; wrote $alt instead"
}
