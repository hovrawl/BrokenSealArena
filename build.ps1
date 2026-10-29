# Rebuild TBS (English) in WSL and copy the ROM to build\tbs-en.gba
# Usage: .\build.ps1 [-Verify]   (-Verify also runs compare; only passes for unmodified source)
param([switch]$Verify)
$ErrorActionPreference = 'Stop'
$dest = Join-Path $PSScriptRoot 'build\tbs-en.gba'
$cmd = 'cd ~/alchemy && make -j$(nproc) tbs-en'
if ($Verify) { $cmd += ' && make compare-tbs-en' }
wsl -d Ubuntu -- bash -lc $cmd
if ($LASTEXITCODE -ne 0) { throw "Build failed" }
$src = '\\wsl.localhost\Ubuntu\home\nathan\alchemy\out\tbs-en\tbs-en.gba'
Copy-Item $src $dest -Force
Write-Host "ROM: $dest"
