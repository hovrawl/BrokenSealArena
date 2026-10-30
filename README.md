# Broken Seal Arena

A Golden Sun: The Broken Seal romhack that turns the game into a team-versus-team
arena: CPU ladders of mixed teams, a party manager with stat, Djinn, Psynergy and
item shops, and saving through the Pause menu. It is a patch series over
[PascalPixel/alchemy](https://github.com/PascalPixel/alchemy), pinned as a
submodule, not a fork.

```
alchemy/        submodule: upstream decompilation at the pinned commit (untouched)
patches/tbs/    the romhack: one git patch per change
scripts/        setup, export patches, update upstream, build, headless smoke tests
docs/           WORKFLOW, CHANGES (what each patch does), GOTCHAS, TESTING, memory/
AGENTS.md       guide for agents (and people) working on the repo
```

Get started (WSL for the build):

```bash
git clone --recurse-submodules <this repo>
bash scripts/setup.sh tbs        # upstream + patches, builds the compilers
cd ~/alchemy && make -j$(nproc) tbs-en     # out/tbs-en/tbs-en.gba
```

On Windows, `build.ps1` builds and copies the ROM to `build\tbs-en.gba`. Start with
`AGENTS.md` and `docs/WORKFLOW.md`.

The Broken Seal builds from source with no cartridge. `rom/` (your own dump, if you
keep one) and `build/` are never committed, and nothing here includes game ROMs.
Golden Sun belongs to Camelot and Nintendo; this is an unofficial fan project.
