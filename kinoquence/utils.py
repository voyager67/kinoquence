from __future__ import annotations

import json
import os
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    try:
        if path.stat().st_size > 16 * 1024 * 1024:
            raise ValueError(f"JSON file exceeds the 16 MiB safety limit: {path.name}")
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path} at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc


def write_json(path: Path, value: Any) -> None:
    """Write JSON atomically so an interrupted write cannot truncate an approved file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def find_executable(name: str) -> str | None:
    return shutil.which(name)


def load_dotenv(path: Path) -> None:
    """Load simple KEY=VALUE lines without overriding existing environment values."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def project_child_path(project_dir: Path, relative_path: str) -> Path:
    """Resolve a project-relative path and reject symlink or traversal escapes."""
    candidate = Path(relative_path)
    if candidate.is_absolute():
        raise ValueError("Project output path must be relative to the project directory")
    try:
        root = project_dir.resolve()
        resolved = (root / candidate).resolve()
    except (OSError, RuntimeError) as exc:
        raise ValueError("Project output path cannot be safely resolved") from exc
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("Project output path resolves outside the project directory") from exc
    return resolved


def project_story_path(path: Path) -> Path:
    if path.is_dir():
        try:
            root = path.resolve()
            candidate = path / "story.json"
            resolved = candidate.resolve()
        except (OSError, RuntimeError) as exc:
            raise ValueError("Project story.json path cannot be safely resolved") from exc
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError("Project story.json must not be a symlink to a file outside the project directory") from exc
        candidate = resolved
    else:
        candidate = path
    if not candidate.is_file():
        raise ValueError(f"Could not find story.json at {candidate}")
    return candidate


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)
