# CLAUDE.md

The shared project guide for all agents is in AGENTS.md (imported below) — product rules,
layout, commands, conventions. Keep AGENTS.md as the single source of truth; put only
Claude Code–specific notes here.

@AGENTS.md

## Claude Code notes

- Shell: Windows. Use the venv interpreter explicitly:
  `C:/Users/arjun/.venvs/pathfinder/Scripts/python.exe` and `.../Scripts/pf.exe`.
- Long pipeline steps (`pf fetch`, `pf enrich`, `pf crux`) take minutes; run them in the
  background and keep working.
- Put scratch scripts in the session scratchpad, not the repo.
- Before claiming a pipeline change works, run `python -m pytest -q` *with the graph built*
  so the data-invariant tests actually execute, and inspect real outputs.
