"""Collect git and GitHub facts. The model never invents this layer."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from dock.agentish import detect_source, likely_agent


class CollectError(RuntimeError):
    pass


@dataclass
class LocalSnapshot:
    repo: str
    branch: str
    dirty_files: list[str]
    untracked: list[str]
    recent_commits: list[dict]
    warnings: list[str] = field(default_factory=list)


@dataclass
class PullRequestSnapshot:
    number: int
    title: str
    url: str
    body: str
    author: str
    files: list[str]
    updated_at: str
    is_draft: bool
    agent_likely: bool
    agent_source: str | None


def _run(args: list[str], cwd: Path, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def git_root(path: Path) -> Path:
    proc = _run(["git", "rev-parse", "--show-toplevel"], cwd=path)
    if proc.returncode != 0:
        raise CollectError(proc.stderr.strip() or f"not a git repository: {path}")
    return Path(proc.stdout.strip())


def collect_local(path: Path, since: str) -> LocalSnapshot:
    root = git_root(path)
    warnings: list[str] = []

    branch_p = _run(["git", "branch", "--show-current"], cwd=root)
    branch = branch_p.stdout.strip() or "HEAD"

    status_p = _run(["git", "status", "--porcelain"], cwd=root)
    dirty: list[str] = []
    untracked: list[str] = []
    for line in status_p.stdout.splitlines():
        if len(line) < 4:
            continue
        code, name = line[:2], line[3:]
        if " -> " in name:
            name = name.split(" -> ", 1)[1]
        if code == "??":
            untracked.append(name)
        else:
            dirty.append(name)

    log_p = _run(
        [
            "git",
            "log",
            f"--since={since}",
            "-20",
            "--pretty=format:%H%x09%an%x09%ae%x09%s",
        ],
        cwd=root,
    )
    commits: list[dict] = []
    for line in log_p.stdout.splitlines():
        parts = line.split("\t", 3)
        if len(parts) != 4:
            continue
        sha, author, email, subject = parts
        files_p = _run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", sha], cwd=root)
        files = [f for f in files_p.stdout.splitlines() if f]
        body_p = _run(["git", "log", "-1", "--pretty=%b", sha], cwd=root)
        body = body_p.stdout.strip()
        commits.append(
            {
                "sha": sha,
                "author": author,
                "email": email,
                "subject": subject,
                "body": body,
                "files": files,
                "agent_likely": likely_agent(login=author, title=subject, body=body),
                "agent_source": detect_source(login=author, title=subject, body=body),
            }
        )

    if status_p.returncode != 0:
        warnings.append(status_p.stderr.strip() or "git status failed")

    return LocalSnapshot(
        repo=str(root),
        branch=branch,
        dirty_files=dirty,
        untracked=untracked,
        recent_commits=commits,
        warnings=warnings,
    )


def _files_from_row(row: dict) -> list[str]:
    files: list[str] = []
    for f in row.get("files") or []:
        if isinstance(f, dict) and f.get("path"):
            files.append(str(f["path"]))
        elif isinstance(f, str):
            files.append(f)
    return files


def _pr_from_row(row: dict) -> PullRequestSnapshot:
    author = ""
    author_raw = row.get("author") or {}
    if isinstance(author_raw, dict):
        author = str(author_raw.get("login") or "")
    title = str(row.get("title") or "")
    body = str(row.get("body") or "")
    return PullRequestSnapshot(
        number=int(row.get("number") or 0),
        title=title,
        url=str(row.get("url") or ""),
        body=body,
        author=author,
        files=_files_from_row(row),
        updated_at=str(row.get("updatedAt") or ""),
        is_draft=bool(row.get("isDraft")),
        agent_likely=likely_agent(login=author, title=title, body=body),
        agent_source=detect_source(login=author, title=title, body=body),
    )


def collect_prs(path: Path) -> tuple[list[PullRequestSnapshot], list[str]]:
    if shutil.which("gh") is None:
        return [], ["gh not on PATH; open PRs skipped"]

    root = git_root(path)
    proc = _run(
        [
            "gh",
            "pr",
            "list",
            "--state",
            "open",
            "--limit",
            "30",
            "--json",
            "number,title,body,url,updatedAt,author,isDraft,files",
        ],
        cwd=root,
        timeout=45,
    )
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout).strip() or "gh pr list failed"
        return [], [msg]

    try:
        raw = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return [], ["gh pr list returned non-JSON"]

    return [_pr_from_row(row) for row in raw], []


def collect_pr(path: Path, number: int) -> PullRequestSnapshot:
    if shutil.which("gh") is None:
        raise CollectError("gh not on PATH; cannot load PR")
    root = git_root(path)
    proc = _run(
        [
            "gh",
            "pr",
            "view",
            str(number),
            "--json",
            "number,title,body,url,updatedAt,author,isDraft,files",
        ],
        cwd=root,
        timeout=45,
    )
    if proc.returncode != 0:
        raise CollectError((proc.stderr or proc.stdout).strip() or f"gh pr view {number} failed")
    try:
        row = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise CollectError("gh pr view returned non-JSON") from exc
    return _pr_from_row(row)


def merge_pr(path: Path, number: int, method: str = "squash") -> str:
    if shutil.which("gh") is None:
        raise CollectError("gh not on PATH; cannot merge")
    if method not in {"squash", "merge", "rebase"}:
        raise CollectError(f"unsupported merge method: {method}")
    root = git_root(path)
    flag = {"squash": "--squash", "merge": "--merge", "rebase": "--rebase"}[method]
    proc = _run(["gh", "pr", "merge", str(number), flag], cwd=root, timeout=60)
    if proc.returncode != 0:
        raise CollectError((proc.stderr or proc.stdout).strip() or "gh pr merge failed")
    return (proc.stdout or "merged").strip()
