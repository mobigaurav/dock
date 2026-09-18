---
name: dock
description: >-
  Builds a morning inbox of uncommitted work, open PRs, and agent claims with
  pass/fail/unknown evidence for Cursor, Claude, Copilot, Codex, and other
  coding agents. Previews a human merge button; never merges unless a person
  confirms in a terminal. Use when the user asks what needs them, dock inbox,
  dock merge, review agent PRs, or verify agent claims in any git repo.
---

# Dock

The engine is git + GitHub. Cursor is one client. Claude uses `dock mcp`.
Unknown is not pass. Agents must not merge.

Prefer the `dock` binary if it is on PATH (`pip install dock-inbox`).

## Inbox

1. Resolve the git repo (cwd or a path the user named).
2. Run:

```bash
dock inbox --path <repo> --format json
```

If `dock` is missing, run `scripts/inbox.sh` next to this skill with the same flags.

3. Lead with `needs_human`. Name `agent_source` when present.
4. Extra claims you extract from prose are **unknown** unless a path in `facts.files` supports them.

## Merge (human click only)

1. Preview only — never `--execute`:

```bash
dock merge --path <repo> --pr <n>
```

2. Show the **Merge button** URL. That is the click.
3. Do not pass `--execute`, do not type `MERGE #N`, do not pipe confirmation, do not call `gh pr merge`.
4. CLI merge is only for the human’s own terminal: `dock merge --pr <n> --execute`

Dock does not call a model. Test-plan `npx jest` lines are not claims. A README path without a URL in the claim stays **unknown**.

Fail blocks execute. Unknown blocks execute unless they pass `--accept-unknown` themselves.

How it works: `docs/SYSTEM_DESIGN.md` in the Dock repo.
