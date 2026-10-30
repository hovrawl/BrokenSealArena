@AGENTS.md

## For Claude Code

- Subagents for recurring jobs live in `.claude/agents/` (`smoke-tester`,
  `patch-porter`). Use them for long, self-contained runs; the result comes back
  as text.
- Auto-memory is per machine. The durable, shared version of what has been learned
  is in `docs/memory/` and `docs/GOTCHAS.md`; update those, not only local memory.
- PowerShell here is 7+ with Git Bash also available. Quoting between PowerShell,
  `wsl -- bash -lc '...'` and heredocs is the usual source of trouble: put
  anything non-trivial in a script file under `scripts/` or a scratch file.
