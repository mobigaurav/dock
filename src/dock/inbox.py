from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from dock.claims import extract_claims
from dock.collect import CollectError, collect_local, collect_prs
from dock.evidence import check_claims
from dock.models import Claim, Inbox, InboxItem


def _since_to_git(since: str) -> str:
    s = since.strip().lower()
    if s.endswith("h") and s[:-1].isdigit():
        return f"{int(s[:-1])} hours ago"
    if s.endswith("d") and s[:-1].isdigit():
        return f"{int(s[:-1])} days ago"
    return since


def _needs_human(claims: list[Claim], *, always: bool = False) -> bool:
    if always:
        return True
    if not claims:
        return True
    return any(c.verdict != "pass" for c in claims)


def build_inbox(path: Path, since: str = "24h") -> Inbox:
    git_since = _since_to_git(since)
    try:
        local = collect_local(path, git_since)
    except CollectError as exc:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return Inbox(
            repo=str(path),
            generated_at=now,
            since=since,
            warnings=[str(exc)],
            items=[],
            summary={"items": 0, "needs_human": 0, "claims_fail": 0, "claims_unknown": 0, "claims_pass": 0},
        )

    warnings = list(local.warnings)
    prs, pr_warnings = collect_prs(path)
    warnings.extend(pr_warnings)

    items: list[InboxItem] = []

    dirty = local.dirty_files + local.untracked
    if dirty:
        items.append(
            InboxItem(
                id="local-dirty",
                kind="local",
                title=f"Uncommitted work on {local.branch}",
                needs_human=True,
                agent_likely=False,
                facts={
                    "branch": local.branch,
                    "dirty_files": local.dirty_files,
                    "untracked": local.untracked,
                },
                claims=[
                    Claim(
                        text="Uncommitted work has no PR prose to verify",
                        verdict="unknown",
                        checker="local_dirty",
                        evidence=f"{len(dirty)} paths; a human must review or open a PR with claims",
                    )
                ],
            )
        )

    for pr in prs:
        texts = extract_claims(pr.body) or extract_claims(pr.title)
        claims = check_claims(texts, pr.files)
        items.append(
            InboxItem(
                id=f"pr-{pr.number}",
                kind="pull_request",
                title=f"#{pr.number} {pr.title}",
                needs_human=_needs_human(claims, always=pr.agent_likely or not claims),
                agent_likely=pr.agent_likely,
                agent_source=pr.agent_source,
                url=pr.url,
                facts={
                    "author": pr.author,
                    "files": pr.files,
                    "updated_at": pr.updated_at,
                    "is_draft": pr.is_draft,
                },
                claims=claims,
            )
        )

    for commit in local.recent_commits:
        prose = f"{commit['subject']}\n{commit.get('body') or ''}"
        texts = extract_claims(prose)
        claims = check_claims(texts, commit.get("files") or [])
        agent = bool(commit.get("agent_likely"))
        interesting = agent or any(c.verdict == "fail" for c in claims)
        if not interesting:
            continue
        items.append(
            InboxItem(
                id=f"commit-{commit['sha'][:10]}",
                kind="commit",
                title=commit["subject"],
                needs_human=_needs_human(claims, always=agent),
                agent_likely=agent,
                agent_source=commit.get("agent_source"),
                facts={
                    "sha": commit["sha"],
                    "author": commit["author"],
                    "files": commit.get("files") or [],
                },
                claims=claims,
            )
        )

    fail = sum(1 for i in items for c in i.claims if c.verdict == "fail")
    unknown = sum(1 for i in items for c in i.claims if c.verdict == "unknown")
    passed = sum(1 for i in items for c in i.claims if c.verdict == "pass")
    needs = sum(1 for i in items if i.needs_human)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return Inbox(
        repo=local.repo,
        generated_at=now,
        since=since,
        warnings=warnings,
        items=items,
        summary={
            "items": len(items),
            "needs_human": needs,
            "claims_fail": fail,
            "claims_unknown": unknown,
            "claims_pass": passed,
        },
    )
