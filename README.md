# Dock

Local inbox and claim evidence for coding agents. Developers still merge. Dock checks whether the agent told the truth.

Works on **any git repo**. Cursor, Claude Code, Copilot, Codex, and the rest are all just git + GitHub.

```bash
pip install -e .
dock inbox --path /path/to/any/repo
dock merge --pr 12          # preview + GitHub merge button — does not merge
```

- Product: [docs/PRODUCT.md](docs/PRODUCT.md)
- Mechanism: [docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md)
- License: [MIT](LICENSE)

Python 3.11+, git, and [GitHub CLI](https://cli.github.com) (`gh`) for pull requests.

```bash
make test
dock inbox --path .
```

## Install in Cursor

```bash
pip install -e /path/to/dock
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

## Use on GitHub PRs

Copy [examples/github-inbox.yml](examples/github-inbox.yml) into another repo.

## Optional shortcuts

Copy `dogfood.example.json` to `dogfood.local.json` (gitignored) if you want `--target` aliases. Otherwise use `--path`.
