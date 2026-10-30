# Export the romhack as a patch series: every commit on the WSL working copy's
# arena branch since the upstream commit this repo pins (the `alchemy`
# submodule) becomes one .patch file in patches\<game>\. Run after committing in
# ~/alchemy. The submodule itself is never touched.
#   .\scripts\export-patches.ps1            # The Broken Seal (branch `arena`)
#   .\scripts\export-patches.ps1 -Game tla  # The Lost Age (branch `arena-tla`)
param([string]$Game = 'tbs')
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$base = ((git -C $root ls-files -s alchemy) -split '\s+')[1]
if (-not $base) { throw "The alchemy submodule is not recorded in this repo" }
$branch = if ($Game -eq 'tbs') { 'arena' } else { "arena-$Game" }
$patches = Join-Path $root "patches\$Game"
New-Item -ItemType Directory -Force $patches | Out-Null
Get-ChildItem $patches -Filter *.patch -ErrorAction SilentlyContinue | Remove-Item
# C:\a\b -> /mnt/c/a/b (wslpath loses the backslashes when called from here)
$wslPatches = '/mnt/' + $patches.Substring(0, 1).ToLower() + $patches.Substring(2).Replace('\', '/')
wsl -d Ubuntu -- bash -lc "cd ~/alchemy && git status --short | grep -q . && { echo 'Uncommitted changes in ~/alchemy: commit them first'; exit 1; }; git format-patch -N -o '$wslPatches' $base..$branch"
if ($LASTEXITCODE -ne 0) { throw "Export failed" }
Write-Host "Exported $Game patches (base $($base.Substring(0, 10))) to $patches"
