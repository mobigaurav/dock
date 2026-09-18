# Dock

Local inbox and claim evidence for coding agents. Developers still merge. Dock checks whether the agent told the truth.

It is **not** a model. It does not review architecture. It does not run your tests. It scores **PR prose** against **git/GitHub facts** (changed paths + patch) with fail-closed checkers. Unknown is the point: a human still looks.

Works on **any git repo**. Cursor, Claude Code, Copilot, Codex, and the rest are all just git + GitHub.

The product and CLI are **Dock**. The install name is **`dock-inbox`** (`dock` on PyPI is a chemistry toolkit).

```bash
pip install dock-inbox
dock inbox --path /path/to/any/repo
dock merge --pr 12          # preview + GitHub merge button — does not merge
```

Until the first PyPI release, this also works:

```bash
pip install "git+https://github.com/mobigaurav/dock.git"
```

Copy [examples/github-inbox.yml](examples/github-inbox.yml) to `.github/workflows/dock.yml` so every PR gets a pass/fail/unknown comment.

- Product: [docs/PRODUCT.md](docs/PRODUCT.md)
- Mechanism: [docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md)
- Release / PyPI: [docs/RELEASE.md](docs/RELEASE.md)
- License: [MIT](LICENSE)

Python 3.11+, git, and [GitHub CLI](https://cli.github.com) (`gh`) for pull requests.

```bash
make test
dock inbox --path .
```

## What a “pass” means

| Claim shape | When it can pass |
|---|---|
| Names a file | That path is in the diff |
| Mentions tests (in Summary, not a Test plan command) | A test path is in the diff |
| Mentions README/docs **and a URL** | That URL appears in the patch |
| Mentions README/docs with no URL | **unknown** — a changed README is not enough |
| Test plan `npx jest foo.test.ts` | **ignored** — files existing is not tests passing |
| Anything else | **unknown** |

Pass is not an approve. Dock will not merge until a person clicks Merge on GitHub.

## Install in Cursor

```bash
pip install dock-inbox
ln -s /path/to/dock/.cursor/skills/dock ~/.cursor/skills/dock
```

Say **what needs me** or **dock inbox**.

## Claude Desktop / Claude Code

```json
{
  "mcpServers": {
    "dock": {
      "command": "dock",
      "args": ["mcp"]
    }
  }
}
```

MCP tools: `dock_inbox`, `dock_merge_preview`. There is no merge tool.

## Merge

`dock merge --pr N` never merges. It prints claim cards and the GitHub Merge URL.

`dock merge --pr N --execute` only works in an interactive terminal after you type `MERGE #N`.

## Optional shortcuts

Copy `dogfood.example.json` to `dogfood.local.json` (gitignored) if you want `--target` aliases. Otherwise use `--path`.
