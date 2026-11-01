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
. "$PSScriptRoot\wsl.ps1"
$wslRoot = $WslRoot
$out = Join-Path $root 'build\smoke\shots'
New-Item -ItemType Directory -Force $out | Out-Null
Get-ChildItem $out -Filter *.png | Remove-Item

$freshArg = if ($Fresh) { 'fresh' } else { 'keep' }
wsl @WslArgs -- bash "$wslRoot/scripts/smoke/run.sh" $Script $freshArg
wsl @WslArgs -- bash -c "cp /tmp/shots/*.png $wslRoot/build/smoke/shots/ 2>/dev/null; true"
Write-Host "Screenshots: $out"
