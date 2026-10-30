# Run a headless smoke script against the built ROM and collect its screenshots.
#   .\scripts\smoke.ps1 pause.txt          (scripts live in scripts\smoke\)
#   .\scripts\smoke.ps1 save.txt -Fresh    (-Fresh deletes the test cartridge save first)
# Screenshots (the script's `shot /tmp/shots/NAME.png` lines) are copied to
# build\smoke\shots, with a contact sheet at build\smoke\shots\sheet.png.
# See docs\TESTING.md.
param(
  [Parameter(Mandatory)][string]$Script,
  [switch]$Fresh
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$wslRoot = '/mnt/' + $root.Substring(0, 1).ToLower() + $root.Substring(2).Replace('\', '/')
$out = Join-Path $root 'build\smoke\shots'
New-Item -ItemType Directory -Force $out | Out-Null
Get-ChildItem $out -Filter *.png | Remove-Item

$freshArg = if ($Fresh) { 'fresh' } else { 'keep' }
wsl -d Ubuntu -- bash "$wslRoot/scripts/smoke/run.sh" $Script $freshArg
wsl -d Ubuntu -- bash -c "cp /tmp/shots/*.png $wslRoot/build/smoke/shots/ 2>/dev/null; true"
Write-Host "Screenshots: $out"
