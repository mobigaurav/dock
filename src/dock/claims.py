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
_SKIP_SECTION = re.compile(r"^(test plan|checklist|how to test|qa)\b", re.I)
_RUN_HINT = re.compile(
    r"^(cd |npx |npm |pnpm |yarn |bun |make |pytest |cargo |go test\b)"
    r"|\b(npx |npm test|pytest |jest )\b",
    re.I,
)
_TEST_FILE_RUN = re.compile(
    r"\.(test|spec)\.(ts|tsx|js|jsx|py)\b",
    re.I,
)

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


def _is_run_instruction(line: str) -> bool:
    """Test-plan commands are not claims. 'Files exist' is not 'tests passed'."""
    stripped = line.strip().strip("`")
    if _RUN_HINT.search(stripped):
        return True
    if _TEST_FILE_RUN.search(stripped) and re.search(
        r"\b(run|npx|npm|jest|pytest|ci)\b", stripped, re.I
    ):
        return True
    return False


def extract_claims(prose: str | None) -> list[str]:
    if not prose:
        return []
    seen: set[str] = set()
    out: list[str] = []
    skip_section = False
    for raw in prose.splitlines():
        heading_only = _HEADING_RE.match(raw.strip())
        if heading_only:
            title = _HEADING_RE.sub("", raw.strip()).strip()
            skip_section = bool(_SKIP_SECTION.match(title))
            continue
        line = _strip_line(raw)
        if _should_skip(line):
            continue
        if skip_section and _is_run_instruction(line):
            continue
        if _is_run_instruction(line) and _TEST_FILE_RUN.search(line):
            continue
        if not _CLAIM_HINT.search(line):
            continue
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(line)
    return out
