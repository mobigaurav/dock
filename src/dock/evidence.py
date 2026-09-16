"""Deterministic evidence. Unknown is not pass. Never trust model confidence."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from dock.models import Claim

TEST_PATH_RE = re.compile(
    r"(^|/)(tests?/|__tests__/|spec/)|"
    r"(_test|\.test|\.spec|test_)[^/]*\.(py|ts|tsx|js|jsx|go|rs|rb)$",
    re.I,
)
DOC_PATH_RE = re.compile(r"(^|/)(readme(\.[a-z]+)?$|docs?/)", re.I)
FILE_IN_CLAIM_RE = re.compile(
    r"\b([\w./-]+\.(?:py|ts|tsx|js|jsx|go|rs|rb|md|json|yml|yaml|toml))\b",
    re.I,
)
TESTS_IN_CLAIM_RE = re.compile(r"\b(tests?|specs?|coverage|unit tests?|e2e)\b", re.I)
DOCS_IN_CLAIM_RE = re.compile(r"\b(readme|docs?|documentation)\b", re.I)
NO_API_RE = re.compile(
    r"\b(no api change|backwards?[- ]compat(?:ible|ibility)|"
    r"behaviou?r[- ]preserv(?:ed|ing|es)?|"
    r"non[- ]breaking|does not change the api|no breaking(?: changes?)?)\b",
    re.I,
)
API_SURFACE_RE = re.compile(
    r"(^|/)(src/.*/(api|routes?|endpoints?)/)|"
    r"\.(proto|graphql)$|"
    r"(openapi|swagger).*\.(ya?ml|json)$",
    re.I,
)
REMOVED_EXPORT_RE = re.compile(
    r"^-\s*(export\s+(async\s+)?(function|const|class|type|interface)|"
    r"def\s+\w+|class\s+\w+|pub\s+fn\s+|func\s+\()",
    re.M,
)


def _norm(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def test_files(paths: list[str]) -> list[str]:
    return [p for p in paths if TEST_PATH_RE.search(_norm(p))]


def doc_files(paths: list[str]) -> list[str]:
    return [p for p in paths if DOC_PATH_RE.search(_norm(p))]


def api_surface_files(paths: list[str]) -> list[str]:
    return [p for p in paths if API_SURFACE_RE.search(_norm(p))]


def check_claim(text: str, diff_files: list[str], diff_text: str | None = None) -> Claim:
    """Score one claim against the changed file list (and optional patch)."""
    files = [_norm(p) for p in diff_files]
    if not files and not diff_text:
        return Claim(
            text=text,
            verdict="unknown",
            checker="no_diff",
            evidence="no changed-file list; cannot verify",
        )
    named = [m.group(1) for m in FILE_IN_CLAIM_RE.finditer(text)]

    if named:
        missing = []
        found = []
        for name in named:
            hit = next((p for p in files if p.endswith(name) or PurePosixPath(p).name == PurePosixPath(name).name), None)
            if hit:
                found.append(hit)
            else:
                missing.append(name)
        if missing:
            return Claim(
                text=text,
                verdict="fail",
                checker="named_files_in_diff",
                evidence=f"claimed {', '.join(missing)} but not in the diff",
            )
        return Claim(
            text=text,
            verdict="pass",
            checker="named_files_in_diff",
            evidence=f"found {', '.join(found)}",
        )

    if TESTS_IN_CLAIM_RE.search(text):
        tests = test_files(files)
        if tests:
            return Claim(
                text=text,
                verdict="pass",
                checker="tests_in_diff",
                evidence=f"test paths: {', '.join(tests[:6])}",
            )
        return Claim(
            text=text,
            verdict="fail",
            checker="tests_in_diff",
            evidence="claim mentions tests; no test path in the diff",
        )

    if DOCS_IN_CLAIM_RE.search(text):
        docs = doc_files(files)
        if docs:
            return Claim(
                text=text,
                verdict="pass",
                checker="docs_in_diff",
                evidence=f"doc paths: {', '.join(docs[:6])}",
            )
        return Claim(
            text=text,
            verdict="fail",
            checker="docs_in_diff",
            evidence="claim mentions docs; no README/docs path in the diff",
        )

    if NO_API_RE.search(text):
        # Fail-closed: we can falsify, we cannot prove.
        if diff_text and REMOVED_EXPORT_RE.search(diff_text):
            return Claim(
                text=text,
                verdict="fail",
                checker="api_compat",
                evidence="patch removes an exported symbol",
            )
        surface = api_surface_files(files)
        if surface:
            return Claim(
                text=text,
                verdict="unknown",
                checker="api_compat",
                evidence=f"API-ish paths changed ({', '.join(surface[:4])}); cannot prove non-breaking",
            )
        return Claim(
            text=text,
            verdict="unknown",
            checker="api_compat",
            evidence="non-breaking claims cannot pass without a contract test",
        )

    return Claim(
        text=text,
        verdict="unknown",
        checker="none",
        evidence="no deterministic checker matched; needs a human",
    )


def check_claims(texts: list[str], diff_files: list[str], diff_text: str | None = None) -> list[Claim]:
    return [check_claim(t, diff_files, diff_text) for t in texts]
