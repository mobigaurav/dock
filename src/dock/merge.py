"""Human-gated merge. Agents may preview. Only a person may confirm."""

from __future__ import annotations

from dataclasses import dataclass

from dock.claims import extract_claims
from dock.collect import PullRequestSnapshot, collect_pr, merge_pr
from dock.evidence import check_claims
from dock.models import Claim


class MergeBlocked(RuntimeError):
    def __init__(self, message: str, preview: "MergePreview"):
        super().__init__(message)
        self.preview = preview


@dataclass
class MergePreview:
    pr: int
    title: str
    url: str
    agent_source: str | None
    blocked: bool
    reasons: list[str]
    claims: list[Claim]
    merge_button: str
    execute_hint: str

    def to_dict(self) -> dict:
        return {
            "pr": self.pr,
            "title": self.title,
            "url": self.url,
            "agent_source": self.agent_source,
            "blocked": self.blocked,
            "reasons": self.reasons,
            "claims": [c.to_dict() for c in self.claims],
            "merge_button": self.merge_button,
            "execute_hint": self.execute_hint,
        }


def confirmation_phrase(pr: int) -> str:
    return f"MERGE #{pr}"


def preview_from_pr(pr: PullRequestSnapshot, *, accept_unknown: bool = False) -> MergePreview:
    texts = extract_claims(pr.body) or extract_claims(pr.title)
    claims = check_claims(texts, pr.files)
    reasons: list[str] = []
    if pr.is_draft:
        reasons.append("draft PRs cannot merge")
    fails = [c for c in claims if c.verdict == "fail"]
    unknowns = [c for c in claims if c.verdict == "unknown"]
    if fails:
        reasons.append(f"{len(fails)} claim(s) failed evidence")
    if unknowns and not accept_unknown:
        reasons.append(
            f"{len(unknowns)} claim(s) unknown — pass --accept-unknown only after you looked"
        )
    phrase = confirmation_phrase(pr.number)
    return MergePreview(
        pr=pr.number,
        title=pr.title,
        url=pr.url,
        agent_source=pr.agent_source,
        blocked=bool(reasons),
        reasons=reasons,
        claims=claims,
        merge_button=pr.url,
        execute_hint=(
            f"Click Merge on GitHub, or in your own terminal type {phrase} after: "
            f"python3 -m dock merge --pr {pr.number} --execute"
        ),
    )


def preview_merge(path, pr_number: int, *, accept_unknown: bool = False) -> MergePreview:
    pr = collect_pr(path, pr_number)
    return preview_from_pr(pr, accept_unknown=accept_unknown)


def render_merge_preview(preview: MergePreview) -> str:
    lines = [
        f"# Dock merge preview — PR #{preview.pr}",
        "",
        preview.title,
        preview.url,
        "",
    ]
    if preview.agent_source:
        lines.append(f"Detected tool: {preview.agent_source}")
        lines.append("")
    lines.append("Pass is not an approve. Dock will not merge until a human confirms.")
    lines.append("")
    if not preview.claims:
        lines.append("- no extractable claims")
    for claim in preview.claims:
        lines.append(f"- [{claim.verdict}] {claim.text} ({claim.checker}: {claim.evidence})")
    lines.append("")
    if preview.blocked:
        lines.append("BLOCKED")
        for r in preview.reasons:
            lines.append(f"- {r}")
    else:
        lines.append("Ready for a human.")
    lines.append("")
    lines.append(f"Merge button (click this): {preview.merge_button}")
    lines.append(preview.execute_hint)
    lines.append("")
    return "\n".join(lines)


def execute_merge(
    path,
    pr_number: int,
    *,
    accept_unknown: bool = False,
    method: str = "squash",
    isatty: bool,
    typed: str,
    merger=None,
) -> str:
    preview = preview_merge(path, pr_number, accept_unknown=accept_unknown)
    if preview.blocked:
        raise MergeBlocked("; ".join(preview.reasons), preview)
    if not isatty:
        raise MergeBlocked(
            "merge execute requires an interactive terminal so an agent cannot click it. "
            f"Use the GitHub button: {preview.merge_button}",
            preview,
        )
    expected = confirmation_phrase(pr_number)
    if typed.strip() != expected:
        raise MergeBlocked(f"typed confirmation must be exactly {expected!r}", preview)
    fn = merger or merge_pr
    return fn(path, pr_number, method)
