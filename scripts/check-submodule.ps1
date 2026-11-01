# Fail if the alchemy submodule is not exactly the pinned upstream commit.
# The submodule is the pristine base the patches apply to; all edits happen in
# the WSL working copy (branch arena). Run before export or update.
# Usage: .\scripts\check-submodule.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
  $status = git submodule status alchemy
  if (-not $status) { throw "alchemy is not a registered submodule" }
  # A leading '-' is uninitialised, '+' is a different commit than the pin,
  # 'U' is a merge conflict; a space means it matches the pin.
  $mark = $status.Substring(0, 1)
  if ($mark -ne ' ') { throw "alchemy does not match the pinned commit ($mark): $status" }
  $dirty = git -C alchemy status --porcelain
  if ($dirty) { throw "alchemy has local changes (edit the work directory instead):`n$dirty" }
  Write-Host "alchemy is pristine at the pinned commit."
} finally {
  Pop-Location
}
