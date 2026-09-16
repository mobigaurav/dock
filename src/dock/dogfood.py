"""Optional local target list. Public use is `dock inbox --path <repo>`."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
LOCAL_FILE = _ROOT / "dogfood.local.json"
EXAMPLE_FILE = _ROOT / "dogfood.example.json"


@dataclass
class Target:
    id: str
    name: str
    path: Path
    status: str
    notes: str
    exists: bool

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "path": str(self.path),
            "status": self.status,
            "notes": self.notes,
            "exists": self.exists,
        }


def default_config() -> Path:
    if LOCAL_FILE.is_file():
        return LOCAL_FILE
    return EXAMPLE_FILE


def load_targets(config: Path | None = None) -> list[Target]:
    cfg = config or default_config()
    raw = json.loads(cfg.read_text())
    root = cfg.parent
    out: list[Target] = []
    for row in raw.get("targets") or []:
        path = (root / str(row["path"])).resolve()
        out.append(
            Target(
                id=str(row["id"]),
                name=str(row["name"]),
                path=path,
                status=str(row.get("status") or "active"),
                notes=str(row.get("notes") or ""),
                exists=path.is_dir(),
            )
        )
    return out


def resolve_target(target_id: str, config: Path | None = None) -> Target:
    rows = load_targets(config)
    matches = [t for t in rows if t.id == target_id]
    if not matches:
        known = ", ".join(t.id for t in rows)
        raise KeyError(f"unknown target {target_id!r}. known: {known}")
    return matches[0]
