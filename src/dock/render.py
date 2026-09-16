from __future__ import annotations

from dock.models import Inbox


def render_markdown(inbox: Inbox) -> str:
    lines: list[str] = []
    lines.append(f"# Dock inbox — {inbox.repo}")
    lines.append("")
    lines.append(f"Generated {inbox.generated_at} · since {inbox.since}")
    s = inbox.summary
    lines.append(
        f"Items {s.get('items', 0)} · needs human {s.get('needs_human', 0)} · "
        f"claims pass {s.get('claims_pass', 0)} / fail {s.get('claims_fail', 0)} / "
        f"unknown {s.get('claims_unknown', 0)}"
    )
    lines.append("")
    lines.append("Pass is not an approve. Fail and unknown both need a human.")
    lines.append("")
    for w in inbox.warnings:
        lines.append(f"- warning: {w}")
    if inbox.warnings:
        lines.append("")
    if not inbox.items:
        lines.append("Nothing in the inbox for this window.")
        return "\n".join(lines)

    for item in inbox.items:
        flag = "NEEDS HUMAN" if item.needs_human else "claims green (still a human merge)"
        agent = ""
        if item.agent_likely:
            src = item.agent_source or "agent"
            agent = f" · likely {src}"
        lines.append(f"## {item.title}")
        lines.append(f"{item.kind} · {flag}{agent}")
        if item.url:
            lines.append(item.url)
        lines.append("")
        if not item.claims:
            lines.append("- no extractable claims; treat as needs human")
        for claim in item.claims:
            lines.append(
                f"- [{claim.verdict}] {claim.text} "
                f"({claim.checker}: {claim.evidence})"
            )
        lines.append("")
    return "\n".join(lines)
