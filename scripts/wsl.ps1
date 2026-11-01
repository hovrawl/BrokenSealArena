# Shared by the Windows scripts (dot-source it: . "$PSScriptRoot\wsl.ps1").
# Gives them $WslArgs (the distro, if BSA_DISTRO is set; else the default one),
# $WslRoot (this repo as a WSL path) and $AlchemyDir (the upstream working copy
# as a WSL path: $env:ALCHEMY_DIR, else the file .alchemy-dir, else work/alchemy;
# the same lookup as alchemy-dir.sh, which it asks).
$WslArgs = @()
if ($env:BSA_DISTRO) { $WslArgs = @('-d', $env:BSA_DISTRO) }
function ConvertTo-WslPath([string]$Path) { (wsl @WslArgs -- wslpath -a ($Path.Replace('\', '/'))).Trim() }
$WslRoot = ConvertTo-WslPath (Split-Path $PSScriptRoot -Parent)
$AlchemyDir = (wsl @WslArgs -- bash "$WslRoot/scripts/alchemy-dir.sh").Trim()
