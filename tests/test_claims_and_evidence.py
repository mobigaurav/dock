from dock.agentish import detect_source, likely_agent
from dock.claims import extract_claims
from dock.collect import PullRequestSnapshot
from dock.evidence import check_claim
from dock.merge import MergeBlocked, confirmation_phrase, execute_merge, preview_from_pr
from dock.mcp import handle


def test_extracts_bullets_not_closes():
    body = """
## Summary
This PR adds caching to the user endpoint.

- Adds unit tests for cache miss
- No API change
- Updates README

Closes #12
Co-authored-by: Cursor <cursor@example.com>
"""
    claims = extract_claims(body)
    assert "Adds unit tests for cache miss" in claims
    assert "No API change" in claims
    assert "Updates README" in claims
    assert all("Closes" not in c for c in claims)


def test_skips_short_and_headings_only():
    assert extract_claims("## Test plan\n\n- x") == []


def test_tests_claim_fails_without_test_paths():
    claim = check_claim("Adds unit tests for cache miss", ["src/cache.py"])
    assert claim.verdict == "fail"
    assert claim.checker == "tests_in_diff"


def test_tests_claim_passes_with_test_path():
    claim = check_claim("Adds unit tests for cache miss", ["src/cache.py", "tests/test_cache.py"])
    assert claim.verdict == "pass"


def test_docs_claim_fails_without_readme():
    claim = check_claim("Updates README", ["src/cache.py"])
    assert claim.verdict == "fail"


def test_named_file_must_appear():
    claim = check_claim("Fixes src/dock/cli.py timeout handling", ["src/dock/inbox.py"])
    assert claim.verdict == "fail"
    claim_ok = check_claim("Fixes src/dock/cli.py timeout handling", ["src/dock/cli.py"])
    assert claim_ok.verdict == "pass"


def test_compat_claim_never_passes():
    claim = check_claim("No API change", ["src/cache.py"])
    assert claim.verdict == "unknown"
    assert claim.checker == "api_compat"


def test_compat_claim_fails_on_removed_export():
    patch = "-export function fetchUser() {\n+function fetchUser() {\n"
    claim = check_claim("This is backward compatible", ["src/api.ts"], patch)
    assert claim.verdict == "fail"


def test_empty_diff_is_unknown_not_fail():
    claim = check_claim("Adds unit tests for cache miss", [])
    assert claim.verdict == "unknown"
    assert claim.checker == "no_diff"


def test_unknown_when_no_checker():
    claim = check_claim("Improve readability of the parser", ["src/parse.py"])
    assert claim.verdict == "unknown"


def test_detects_cursor_claude_and_copilot():
    assert detect_source(body="Co-authored-by: Cursor <cursoragent@cursor.com>") == "cursor"
    assert detect_source(body="Co-authored-by: Claude <noreply@anthropic.com>") == "claude"
    assert detect_source(login="copilot-swe-agent[bot]") == "copilot"
    assert likely_agent(title="feat", body="hand written") is False
    assert likely_agent(login="dependabot[bot]") is False


def _pr(**kwargs) -> PullRequestSnapshot:
    base = dict(
        number=12,
        title="Adds unit tests for cache miss",
        url="https://github.com/acme/app/pull/12",
        body="- Adds unit tests for cache miss\n",
        author="alice",
        files=["tests/test_cache.py"],
        updated_at="",
        is_draft=False,
        agent_likely=True,
        agent_source="claude",
    )
    base.update(kwargs)
    return PullRequestSnapshot(**base)


def test_merge_preview_ready_when_tests_land():
    preview = preview_from_pr(_pr())
    assert preview.blocked is False
    assert preview.merge_button.endswith("/12")
    assert preview.claims[0].verdict == "pass"
    assert preview.agent_source == "claude"


def test_merge_preview_blocks_failed_claims():
    preview = preview_from_pr(_pr(files=["src/cache.py"]))
    assert preview.blocked is True
    assert any("failed" in r for r in preview.reasons)


def test_execute_refuses_without_tty(monkeypatch):
    monkeypatch.setattr("dock.merge.preview_merge", lambda *a, **k: preview_from_pr(_pr()))

    def boom(*_a, **_k):
        raise AssertionError("must not call github")

    try:
        execute_merge(".", 12, isatty=False, typed="MERGE #12", merger=boom)
        assert False, "expected MergeBlocked"
    except MergeBlocked as exc:
        assert "interactive terminal" in str(exc)


def test_execute_refuses_wrong_phrase(monkeypatch):
    monkeypatch.setattr("dock.merge.preview_merge", lambda *a, **k: preview_from_pr(_pr()))
    called = {"n": 0}

    def merger(*_a, **_k):
        called["n"] += 1
        return "ok"

    try:
        execute_merge(".", 12, isatty=True, typed="lgtm", merger=merger)
        assert False, "expected MergeBlocked"
    except MergeBlocked:
        assert called["n"] == 0


def test_execute_merges_after_exact_phrase(monkeypatch):
    monkeypatch.setattr("dock.merge.preview_merge", lambda *a, **k: preview_from_pr(_pr()))

    def merger(path, number, method):
        assert number == 12
        assert method == "squash"
        return "merged"

    out = execute_merge(".", 12, isatty=True, typed=confirmation_phrase(12), merger=merger)
    assert out == "merged"


def test_mcp_lists_inbox_and_preview_not_merge():
    listed = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    names = [t["name"] for t in listed["result"]["tools"]]
    assert names == ["dock_inbox", "dock_merge_preview"]
