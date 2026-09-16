import json
from pathlib import Path

from dock.dogfood import load_targets
from dock.inbox import build_inbox
from dock.collect import CollectError, git_root


def test_git_root_rejects_non_repo(tmp_path: Path):
    try:
        git_root(tmp_path)
        assert False, "expected CollectError"
    except CollectError:
        pass


def test_inbox_on_non_repo_is_warning_not_crash(tmp_path: Path):
    inbox = build_inbox(tmp_path)
    assert inbox.items == []
    assert inbox.warnings
    assert inbox.summary["items"] == 0


def test_dogfood_loader_reads_explicit_config(tmp_path: Path):
    cfg = tmp_path / "dogfood.json"
    cfg.write_text(
        json.dumps(
            {
                "targets": [
                    {
                        "id": "demo",
                        "name": "Demo",
                        "path": ".",
                        "status": "active",
                        "notes": "",
                    }
                ]
            }
        )
    )
    rows = load_targets(cfg)
    assert len(rows) == 1
    assert rows[0].id == "demo"
    assert rows[0].exists is True
