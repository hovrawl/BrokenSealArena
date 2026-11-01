# Export the romhack as a patch series: every commit on the WSL working copy's
# arena branch since the upstream commit this repo pins (the `alchemy`
# submodule) becomes one .patch file in patches\<game>\. Run after committing in
# the work directory. The submodule itself is never touched.
#   .\scripts\export-patches.ps1            # The Broken Seal (branch `arena`)
#   .\scripts\export-patches.ps1 -Game tla  # The Lost Age (branch `arena-tla`)
param([string]$Game = 'tbs')
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
. "$PSScriptRoot\wsl.ps1"
& "$PSScriptRoot\check-submodule.ps1"
$base = ((git -C $root ls-files -s alchemy) -split '\s+')[1]
if (-not $base) { throw "The alchemy submodule is not recorded in this repo" }
$branch = if ($Game -eq 'tbs') { 'arena' } else { "arena-$Game" }
$patches = Join-Path $root "patches\$Game"
New-Item -ItemType Directory -Force $patches | Out-Null
Get-ChildItem $patches -Filter *.patch -ErrorAction SilentlyContinue | Remove-Item
$wslPatches = ConvertTo-WslPath $patches
wsl @WslArgs -- bash -lc "cd '$AlchemyDir' && git status --short | grep -q . && { echo 'Uncommitted changes in ${AlchemyDir}: commit them first'; exit 1; }; git format-patch -N -o '$wslPatches' $base..$branch"
if ($LASTEXITCODE -ne 0) { throw "Export failed" }
Write-Host "Exported $Game patches (base $($base.Substring(0, 10))) to $patches"
