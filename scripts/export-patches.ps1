# Export the romhack as a patch series: every commit on the WSL working copy's
# `arena` branch since the pinned upstream commit (UPSTREAM_BASE) becomes one
# .patch file in patches\. Run after committing in ~/alchemy.
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$base = (Get-Content (Join-Path $root 'UPSTREAM_BASE') -TotalCount 1).Trim()
$patches = Join-Path $root 'patches'
Get-ChildItem $patches -Filter *.patch -ErrorAction SilentlyContinue | Remove-Item
New-Item -ItemType Directory -Force $patches | Out-Null
# C:\a\b -> /mnt/c/a/b (wslpath loses the backslashes when called from here)
$wslPatches = '/mnt/' + $patches.Substring(0, 1).ToLower() + $patches.Substring(2).Replace('\', '/')
wsl -d Ubuntu -- bash -lc "cd ~/alchemy && git status --short | grep -q . && { echo 'Uncommitted changes in ~/alchemy: commit them first'; exit 1; }; git format-patch -N -o '$wslPatches' $base..arena"
if ($LASTEXITCODE -ne 0) { throw "Export failed" }
Write-Host "Exported to $patches"
