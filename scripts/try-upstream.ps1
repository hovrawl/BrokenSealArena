# Try a newer upstream without touching anything real. Rebases a copy of the
# `arena` branch onto the target on a scratch branch (arena-trial) in ~/alchemy,
# builds it, and says what broke and which upstream commit did it. If it builds,
# runs a few smoke scripts. Afterwards the working copy is back on `arena`.
#   .\scripts\try-upstream.ps1                      # origin/main, after a fetch
#   .\scripts\try-upstream.ps1 -Target some-ref     # any ref known to ~/alchemy
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
$branch = if ($Game -eq 'tbs') { 'arena' } else { "arena-$Game" }
& "$PSScriptRoot\check-submodule.ps1"
$pinned = ((git -C $root ls-files -s alchemy) -split '\s+')[1]

# C:\a\b -> /mnt/c/a/b (wslpath loses the backslashes when called from here)
$sh = Join-Path $PSScriptRoot 'try-upstream.sh'
$wslSh = '/mnt/' + $sh.Substring(0, 1).ToLower() + $sh.Substring(2).Replace('\', '/')

wsl -d Ubuntu -- bash -lc "cd ~/alchemy && git fetch -q origin"
try {
  wsl -d Ubuntu -- bash $wslSh run $pinned $Target $branch
  $code = $LASTEXITCODE
  switch ($code) {
    0 { Write-Host "`nResult: builds." }
    2 { Write-Host "`nResult: ~/alchemy has uncommitted changes." }
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
  wsl -d Ubuntu -- bash $wslSh restore $branch
}
Write-Host "Report: \\wsl.localhost\Ubuntu\home\nathan\try-upstream-report.txt"
