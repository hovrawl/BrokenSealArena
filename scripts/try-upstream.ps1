# Try a newer upstream without touching anything real. Rebases a copy of the
# `arena` branch onto the target on a scratch branch (arena-trial) in the work directory,
# builds it, and says what broke and which upstream commit did it. If it builds,
# runs a few smoke scripts. Afterwards the working copy is back on `arena`.
#   .\scripts\try-upstream.ps1                      # origin/main, after a fetch
#   .\scripts\try-upstream.ps1 -Target some-ref     # any ref known to the work directory
#   .\scripts\try-upstream.ps1 -NoSmoke
# To adopt a good trial for real, run update-upstream.ps1 -Apply.
param(
  [string]$Target = 'origin/main',
  [string[]]$Smoke = @('attendant.txt', 'manager.txt', 'win.txt'),
  [switch]$NoSmoke,
  [string]$Game = 'tbs'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
. "$PSScriptRoot\wsl.ps1"
$branch = if ($Game -eq 'tbs') { 'arena' } else { "arena-$Game" }
& "$PSScriptRoot\check-submodule.ps1"
$pinned = ((git -C $root ls-files -s alchemy) -split '\s+')[1]

$wslSh = "$WslRoot/scripts/try-upstream.sh"

wsl @WslArgs -- bash -lc "cd '$AlchemyDir' && git fetch -q origin"
try {
  wsl @WslArgs -- bash $wslSh run $pinned $Target $branch
  $code = $LASTEXITCODE
  switch ($code) {
    0 { Write-Host "`nResult: builds." }
    2 { Write-Host "`nResult: the work directory has uncommitted changes." }
    3 { Write-Host "`nResult: rebase conflict (nothing was changed)." }
    4 { Write-Host "`nResult: our patches break the build; upstream alone is fine." }
    5 { Write-Host "`nResult: upstream itself does not build." }
    default { Write-Host "`nResult: unexpected exit code $code." }
  }
  if ($code -eq 0 -and -not $NoSmoke) {
    foreach ($s in $Smoke) {
      Write-Host "`nSmoke: $s"
      & "$PSScriptRoot\smoke.ps1" $s -Fresh | Select-Object -Last 2
      $dest = Join-Path $root "build\smoke\trial_$($s -replace '\.txt$','').png"
      Copy-Item (Join-Path $root 'build\smoke\shots\sheet.png') $dest -Force
      Write-Host "Sheet: $dest"
    }
    Write-Host "`nLook at the sheets before trusting the trial."
  }
} finally {
  wsl @WslArgs -- bash $wslSh restore $branch
}
Write-Host "Report: $(wsl @WslArgs -- wslpath -w ~/try-upstream-report.txt)"
