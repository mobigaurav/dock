# Dock — system design

How Dock works. Product positioning lives in [PRODUCT.md](PRODUCT.md).

## 1. Problem in one line

Agents write faster than humans can check whether the **prose about the change** is true. Dock is a lie detector for that prose, not a replacement reviewer and not a merge bot.

## 2. Design principles

1. **Facts and verdicts are not the model.** Git and GitHub are the source of files, authors, and PR bodies. Checkers return pass / fail / unknown. The LLM (Cursor, Claude, …) may narrate the inbox; it may not invent PRs or mark pass from confidence.
2. **Unknown is not pass.** A claim we cannot prove is a human item.
3. **Humans merge.** Preview may show a GitHub Merge button. Execute requires a TTY and the exact phrase `MERGE #<n>`. MCP has no merge tool.
4. **Local.** No account and no API key. If git and `gh` work, Dock works.
5. **Tool-agnostic.** Cursor is one client. Claude uses MCP. Copilot/Codex PRs are still git objects.

## 3. Context diagram

```
                    humans
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   Cursor skill    Claude MCP     terminal CLI
        │              │              │
        └──────────────┼──────────────┘
                       │
                 Dock engine
              (Python, local)
                       │
              ┌────────┼────────┐
              │                 │
             git                gh
         (status, log,     (PR list/view,
          diff names)       optional merge)
                       │
                 GitHub.com
              (human Merge click)
```

There is no Dock backend in this revision.

## 4. Components

| Piece | Role | Runs where |
|---|---|---|
| `dock.collect` | git status/log, `gh pr list` / `view` | Local subprocess |
| `dock.agentish` | Heuristic: which tool likely wrote this | Local regex |
| `dock.claims` | Pull claim-like sentences from PR/commit prose | Local regex |
| `dock.evidence` | Score each claim against changed paths / patch | Local regex |
| `dock.inbox` | Compose items + summary | Local |
| `dock.merge` | Preview; optional TTY execute | Local; execute calls `gh pr merge` |
| `dock.mcp` | JSON-RPC stdio tools: inbox + merge preview | Local process spawned by Claude |
| Cursor skill | Instructs the agent to run the CLI, never `--execute` | Cursor |
| GitHub Merge button | Actual approve/merge control | GitHub UI |

## 5. Inbox pipeline

```
repo path + since
        │
        ▼
 collect_local ──► dirty files, untracked, recent commits
 collect_prs    ──► open PRs (skipped with a warning if `gh` missing)
        │
        ▼
 for each PR / interesting commit
        │
        ├─ detect_source (cursor | claude | copilot | …)
        ├─ extract_claims(body or title)
        └─ check_claims(texts, changed files)
                │
                ▼
         pass | fail | unknown
        │
        ▼
 needs_human = any non-pass OR agent-likely OR no claims
        │
        ▼
 markdown or JSON inbox
```

**Interesting commits** (to avoid noise): keep if `agent_likely` or any claim **fail**. Ordinary human commits with no checkable claims are omitted.

**Local dirty work** is always unknown: there is no PR prose to verify.

## 6. Evidence rules (fail-closed)

| Claim shape | Pass | Fail | Unknown |
|---|---|---|---|
| Names a file (`src/foo.py`) | That path is in the diff | Path not in the diff | No file list |
| Mentions tests (Summary) | A test/spec path is in the diff | None is | No file list |
| Test plan run commands (`npx jest a.test.ts`) | — | — | **Not extracted** |
| Mentions README/docs **and a URL** | URL is in the patch (`+` hunks) | URL not in the patch | No patch |
| Mentions README/docs, no URL | — | No docs path in the diff | Docs path changed; will not pass on path alone |
| “No API change” / backward compatible | Never in v1 | Patch removes an exported symbol | Otherwise — cannot prove a negative |
| Anything else | — | — | No checker matched |

Empty file list ⇒ **unknown**, not fail (missing evidence is not a contradiction).

## 7. Merge gate

```
dock merge --pr N
        │
        ▼
 gh pr view → extract claims → gh pr diff → evidence
        │
        ├─ blocked if draft
        ├─ blocked if any fail
        └─ blocked if any unknown unless --accept-unknown
        │
        ▼
 print claim cards + GitHub URL  ← this is the “button”
        │
 dock merge --pr N --execute
        │
        ├─ refuse if blocked
        ├─ refuse if stdin is not a TTY (agents pipe; humans have a terminal)
        └─ refuse unless typed line == MERGE #<n>
                │
                ▼
         gh pr merge --squash|merge|rebase
```

MCP exposes only `dock_merge_preview`. A model cannot satisfy the TTY gate through MCP.

## 8. Clients

**CLI.** `python3 -m dock` / installed `dock` command. Works in any git repo: `--path /that/repo`.

**Cursor skill.** Tells the agent to run `dock inbox` / `dock merge` (preview). Absolute machine paths are not part of the contract; install puts `dock` on PATH.

**MCP.** Newline-delimited JSON-RPC 2.0 on stdio (`protocolVersion` 2024-11-05). Tools: `dock_inbox`, `dock_merge_preview`. Claude Desktop / Claude Code spawn `python3 -m dock mcp`.

## 9. Trust boundary

Dock does not call an LLM, does not store tokens, and does not need a Dock server. Evidence is local subprocesses against git and `gh`. The operator’s GitHub credentials stay in `gh`; Dock does not copy them.

## 10. Optional GitHub App

A required status check on pull requests needs a URL GitHub can call. That would be a GitHub App plus HTTPS webhook, not a change to the local evidence engine. The CLI remains the same command.

## 11. Local aliases

`dogfood.local.json` is gitignored. It is only for `--target` shortcuts on your machine. Public usage is:

```bash
dock inbox --path /path/to/any/git/repo
```

## 12. Threat notes

- Agents will try to merge. TTY + exact phrase + no MCP merge tool is the control. It is not perfect; GitHub branch protection is the real org control later.
- `gh` uses the operator’s GitHub credentials. Dock does not store tokens.
- Heuristic `agent_source` can be wrong. It is a label, not a verdict.
