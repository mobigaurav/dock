"""Extract claim-like sentences from PR/commit prose. Does not score them."""

from __future__ import annotations

import re

_SKIP_PREFIXES = (
    "closes ",
    "close ",
    "fixes #",
    "fix #",
    "resolves ",
    "signed-off-by:",
    "co-authored-by:",
    "made-with:",
    "powered by",
)

_HEADING_RE = re.compile(r"^#{1,6}\s+")
_BULLET_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s+")
_CHECKBOX_RE = re.compile(r"^\s*(?:[-*]\s+)?\[(?: |x|X)\]\s+")

# A line is claim-like if it asserts something about the change.
_CLAIM_HINT = re.compile(
    r"\b("
    r"add(?:s|ed|ing)?|remove(?:s|d|ing)?|delet(?:e|es|ed|ing)|"
    r"updat(?:e|es|ed|ing)|fix(?:es|ed|ing)?|introduc(?:e|es|ed)|"
    r"no longer|does not|without|backward|compat|breaking|"
    r"test(?:s|ed|ing)?|coverage|readme|docs?|"
    r"api|endpoint|migrat(?:e|ion)|refactor"
    r")\b",
    re.I,
)


def _strip_line(raw: str) -> str:
    line = raw.strip()
    line = _HEADING_RE.sub("", line).strip()
    line = _CHECKBOX_RE.sub("", line).strip()
    line = _BULLET_RE.sub("", line).strip()
    return line


def _should_skip(line: str) -> bool:
    if not line or len(line) < 8:
        return True
    lower = line.lower()
    if any(lower.startswith(p) for p in _SKIP_PREFIXES):
        return True
    if lower in {"summary", "description", "test plan", "checklist"}:
        return True
    return False


def extract_claims(prose: str | None) -> list[str]:
    if not prose:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for raw in prose.splitlines():
        line = _strip_line(raw)
        if _should_skip(line):
            continue
        if not _CLAIM_HINT.search(line):
            continue
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(line)
    return out
