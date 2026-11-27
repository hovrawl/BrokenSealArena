@AGENTS.md

## For Claude Code

- Subagents for recurring jobs live in `.claude/agents/` (`smoke-tester`,
  `patch-porter`). Use them for long, self-contained runs; the result comes back
  as text.
- Auto-memory is per machine. The durable, shared version of what has been learned
  is in `docs/memory/` and `docs/GOTCHAS.md`; update those, not only local memory.
- PowerShell here is 7+ with Git Bash also available; builds run in MSYS2
  (`C:\msys64\usr\bin\bash.exe -lc`, with `MSYSTEM` UCRT64, or MINGW32 for the
  desktop build). Quoting between PowerShell, bash and heredocs is the usual
  source of trouble: put anything non-trivial in a script file under `scripts/`
  or a scratch file. Git for Windows here has `core.autocrlf=true`: edit work
  directory files with tools that keep LF, and use MSYS2's git there.
