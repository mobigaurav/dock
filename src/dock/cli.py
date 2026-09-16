from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dock.dogfood import load_targets, resolve_target
from dock.inbox import build_inbox
from dock.merge import MergeBlocked, confirmation_phrase, execute_merge, preview_merge, render_merge_preview
from dock.render import render_markdown


def _repo_path(args: argparse.Namespace) -> Path:
    if getattr(args, "target", None):
        t = resolve_target(args.target)
        if not t.exists:
            raise SystemExit(f"target {t.id} path does not exist yet: {t.path}")
        return t.path
    return Path(args.path).resolve()


def _print_inbox(inbox, fmt: str) -> int:
    if fmt == "json":
        sys.stdout.write(json.dumps(inbox.to_dict(), indent=2))
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_markdown(inbox))
        sys.stdout.write("\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dock",
        description=(
            "Inbox and claim evidence for coding agents (Cursor, Claude, Copilot, …). "
            "Humans still click merge."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    inbox = sub.add_parser("inbox", help="What needs a human in this repo")
    inbox.add_argument("--path", default=".", help="Git repo (default: cwd)")
    inbox.add_argument("--target", help="Dogfood id: arogya | vedic | dhan")
    inbox.add_argument("--since", default="24h", help="Window like 24h or 7d")
    inbox.add_argument("--format", choices=("md", "json"), default="md")

    merge = sub.add_parser(
        "merge",
        help="Preview a PR merge. --execute only works in an interactive terminal after you type MERGE #N",
    )
    merge.add_argument("--path", default=".", help="Git repo")
    merge.add_argument("--target", help="Dogfood id: arogya | vedic | dhan")
    merge.add_argument("--pr", type=int, required=True)
    merge.add_argument("--format", choices=("md", "json"), default="md")
    merge.add_argument(
        "--accept-unknown",
        action="store_true",
        help="Allow execute when claims are unknown (you looked). Never skips fails.",
    )
    merge.add_argument(
        "--execute",
        action="store_true",
        help="Actually merge. Requires a TTY. You must type MERGE #<n>. Agents cannot do this.",
    )
    merge.add_argument("--method", choices=("squash", "merge", "rebase"), default="squash")

    dog = sub.add_parser("dogfood", help="Run inbox on Vedic AI, Arogya AI, and Dhan AI")
    dog.add_argument("--since", default="24h")
    dog.add_argument("--format", choices=("md", "json"), default="md")

    sub.add_parser("mcp", help="Stdio MCP server for Claude Desktop / Claude Code")
    sub.add_parser("targets", help="List dogfood targets")

    args = parser.parse_args(argv)

    if args.cmd == "targets":
        rows = [t.to_dict() for t in load_targets()]
        sys.stdout.write(json.dumps(rows, indent=2) + "\n")
        return 0

    if args.cmd == "mcp":
        from dock.mcp import serve

        return serve()

    if args.cmd == "dogfood":
        results = []
        for t in load_targets():
            if t.status != "active":
                results.append({"target": t.to_dict(), "skipped": "planned"})
                continue
            if not t.exists:
                results.append({"target": t.to_dict(), "skipped": "missing path"})
                continue
            inbox_payload = build_inbox(t.path, since=args.since)
            results.append({"target": t.to_dict(), "inbox": inbox_payload.to_dict()})
            if args.format == "md":
                sys.stdout.write(f"# {t.name} ({t.id})\n\n")
                sys.stdout.write(render_markdown(inbox_payload))
                sys.stdout.write("\n\n")
        if args.format == "json":
            sys.stdout.write(json.dumps(results, indent=2) + "\n")
        return 0

    if args.cmd == "inbox":
        return _print_inbox(build_inbox(_repo_path(args), since=args.since), args.format)

    if args.cmd == "merge":
        path = _repo_path(args)
        if args.execute:
            try:
                typed = ""
                if sys.stdin.isatty():
                    sys.stderr.write(f"Type {confirmation_phrase(args.pr)} to confirm merge:\n")
                    typed = input()
                text = execute_merge(
                    path,
                    args.pr,
                    accept_unknown=args.accept_unknown,
                    method=args.method,
                    isatty=sys.stdin.isatty(),
                    typed=typed,
                )
            except MergeBlocked as exc:
                sys.stderr.write(render_merge_preview(exc.preview))
                sys.stderr.write(f"\nmerge blocked: {exc}\n")
                return 2
            sys.stdout.write(text + "\n")
            return 0
        preview = preview_merge(path, args.pr, accept_unknown=args.accept_unknown)
        if args.format == "json":
            sys.stdout.write(json.dumps(preview.to_dict(), indent=2) + "\n")
        else:
            sys.stdout.write(render_merge_preview(preview))
        return 2 if preview.blocked else 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
