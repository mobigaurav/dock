from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Verdict = Literal["pass", "fail", "unknown"]


@dataclass
class Claim:
    text: str
    verdict: Verdict = "unknown"
    checker: str | None = None
    evidence: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class InboxItem:
    id: str
    kind: str
    title: str
    needs_human: bool
    agent_likely: bool = False
    agent_source: str | None = None
    url: str | None = None
    facts: dict[str, Any] = field(default_factory=dict)
    claims: list[Claim] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "needs_human": self.needs_human,
            "agent_likely": self.agent_likely,
            "agent_source": self.agent_source,
            "url": self.url,
            "facts": self.facts,
            "claims": [c.to_dict() for c in self.claims],
        }


@dataclass
class Inbox:
    repo: str
    generated_at: str
    since: str
    warnings: list[str]
    items: list[InboxItem]
    summary: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo": self.repo,
            "generated_at": self.generated_at,
            "since": self.since,
            "warnings": self.warnings,
            "items": [i.to_dict() for i in self.items],
            "summary": self.summary,
        }
