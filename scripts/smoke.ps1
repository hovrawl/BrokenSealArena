# Run a headless smoke script against the built ROM and collect its screenshots.
#   .\scripts\smoke.ps1 pause.txt          (scripts live in scripts\smoke\)
#   .\scripts\smoke.ps1 save.txt -Fresh    (-Fresh deletes the test cartridge save first)
# Screenshots (the script's `shot /tmp/shots/NAME.png` lines) are copied to
# build\smoke\shots, with a contact sheet at build\smoke\shots\sheet.png.
# Runs in MSYS2 (scripts\msys2.ps1). See docs\TESTING.md.
param(
  [Parameter(Mandatory)][string]$Script,
  [switch]$Fresh
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
. "$PSScriptRoot\msys2.ps1"
$out = Join-Path $root 'build\smoke\shots'
New-Item -ItemType Directory -Force $out | Out-Null
Get-ChildItem $out -Filter *.png | Remove-Item

$freshArg = if ($Fresh) { 'fresh' } else { 'keep' }
Invoke-Sh "bash '$ShRoot/scripts/smoke/run.sh' '$Script' $freshArg"
# The driver is a Windows program: the script's /tmp/shots is C:\tmp\shots.
Copy-Item 'C:\tmp\shots\*.png' $out -ErrorAction SilentlyContinue
Write-Host "Screenshots: $out"
