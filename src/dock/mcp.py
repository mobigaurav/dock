"""Stdio MCP so Claude Desktop / Claude Code can use the same engine as Cursor."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TextIO

from dock.inbox import build_inbox
from dock.merge import preview_merge, render_merge_preview
from dock.render import render_markdown

PROTOCOL = "2024-11-05"

TOOLS = [
    {
        "name": "dock_inbox",
        "description": (
            "Inbox of uncommitted work, open PRs, and agent claims with pass/fail/unknown "
            "evidence. Works for Cursor, Claude, Copilot, and other agents. Does not merge."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Git repository path"},
                "since": {"type": "string", "description": "Window like 24h or 7d", "default": "24h"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "dock_merge_preview",
        "description": (
            "Show claim cards and the GitHub merge button URL for a PR. Never merges. "
            "A human must click Merge on GitHub or run dock merge --execute in a terminal."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "pr": {"type": "integer"},
            },
            "required": ["path", "pr"],
        },
    },
]


def _ok(id_: Any, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _err(id_: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def _text(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}]}


def handle(msg: dict) -> dict | None:
    method = msg.get("method")
    id_ = msg.get("id")
    params = msg.get("params") or {}
    if method == "initialize":
        return _ok(
            id_,
            {
                "protocolVersion": PROTOCOL,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "dock", "version": "0.1.0"},
            },
        )
    if method == "notifications/initialized" or method is None or id_ is None:
        return None
    if method == "ping":
        return _ok(id_, {})
    if method == "tools/list":
        return _ok(id_, {"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        try:
            if name == "dock_inbox":
                inbox = build_inbox(Path(str(args["path"])).resolve(), since=str(args.get("since") or "24h"))
                return _ok(id_, _text(render_markdown(inbox)))
            if name == "dock_merge_preview":
                preview = preview_merge(Path(str(args["path"])).resolve(), int(args["pr"]))
                return _ok(id_, _text(render_merge_preview(preview)))
            return _err(id_, -32601, f"unknown tool: {name}")
        except Exception as exc:  # noqa: BLE001 — MCP must return errors, not crash
            return _ok(id_, {"content": [{"type": "text", "text": str(exc)}], "isError": True})
    return _err(id_, -32601, f"unknown method: {method}")


def serve(stdin: TextIO | None = None, stdout: TextIO | None = None) -> int:
    inn = stdin or sys.stdin
    out = stdout or sys.stdout
    for raw in inn:
        line = raw.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        reply = handle(msg)
        if reply is None:
            continue
        out.write(json.dumps(reply, ensure_ascii=True) + "\n")
        out.flush()
    return 0
