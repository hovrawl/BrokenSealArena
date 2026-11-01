# Move this repo to newer upstream alchemy, carrying the patches along.
#   .\scripts\try-upstream.ps1              # first: trial-rebase, build, smoke on a scratch branch
#   .\scripts\update-upstream.ps1           # look: what is new upstream, what could clash
#   .\scripts\update-upstream.ps1 -Apply    # rebase the working copy's patches onto it
# Look first. -Apply rebases the `arena` branch in the work directory onto upstream's main,
# stops at the first conflict (resolve in WSL, `git rebase --continue`, then run
# this again with -Finish), and never edits the `alchemy` submodule's files.
param(
  [switch]$Apply,
  [switch]$Finish,
  [string]$Game = 'tbs'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
. "$PSScriptRoot\wsl.ps1"
& "$PSScriptRoot\check-submodule.ps1"
$branch = if ($Game -eq 'tbs') { 'arena' } else { "arena-$Game" }
$pinned = ((git -C $root ls-files -s alchemy) -split '\s+')[1]

git -C "$root\alchemy" fetch origin 2>&1 | Out-Null
$head = (git -C "$root\alchemy" rev-parse origin/main).Trim()
$count = (git -C "$root\alchemy" rev-list --count "$pinned..$head").Trim()
Write-Host "Pinned:   $($pinned.Substring(0, 10))"
Write-Host "Upstream: $($head.Substring(0, 10))  ($count new commits)"
if ($count -eq '0' -and -not $Finish) { Write-Host 'Already up to date.'; return }

if (-not $Apply -and -not $Finish) {
  Write-Host "`nNew upstream commits:"
  git -C "$root\alchemy" log --oneline "$pinned..$head" | Select-Object -First 30
  # Files both sides touch are where a rebase will ask for help.
  $ours = git -C "$root\alchemy" diff --name-only $pinned (wsl @WslArgs -- bash -lc "cd '$AlchemyDir' && git rev-parse $branch").Trim() 2>$null
  $theirs = git -C "$root\alchemy" diff --name-only $pinned $head
  $both = $ours | Where-Object { $theirs -contains $_ }
  Write-Host "`nFiles changed by both upstream and our patches: $(@($both).Count)"
  $both | Select-Object -First 40
  Write-Host "`nRun again with -Apply to rebase."
  return
}

if ($Apply) {
  wsl @WslArgs -- bash -lc "cd '$AlchemyDir' && git status --short | grep -q . && { echo 'Uncommitted changes in $AlchemyDir'; exit 1; }; git fetch origin && git rebase origin/main $branch"
  if ($LASTEXITCODE -ne 0) {
    Write-Host "`nThe rebase stopped. Resolve it in WSL (cd $AlchemyDir), run 'git rebase --continue', then run this script with -Finish."
    return
  }
}

# Pin the new upstream commit, re-export the patches, and leave the rest to a commit.
git -C "$root\alchemy" checkout -q $head
git -C "$root\alchemy" submodule update --init --recursive 2>&1 | Out-Null
git -C $root add alchemy
& "$PSScriptRoot\export-patches.ps1" -Game $Game
Write-Host "`nDone. Build and smoke-test, then commit: alchemy pin, patches\$Game, docs\CHANGES.md."
