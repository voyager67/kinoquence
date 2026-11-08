from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

from .utils import project_child_path, project_story_path, read_json
from .validate import validate_story


class RenderError(RuntimeError):
    pass


def _resolve_project_asset(project_dir: Path, relative_path: str) -> Path:
    """Resolve an asset while preventing absolute paths and symlink traversal."""
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise RenderError("Audio asset path must be a non-empty project-relative string")
    candidate = Path(relative_path)
    if candidate.is_absolute():
        raise RenderError("Audio asset paths must be relative to the project directory")
    root = project_dir.resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise RenderError(f"Audio asset path escapes the project directory: {relative_path}") from exc
    if not resolved.is_file():
        raise RenderError("Audio asset listed in story.json is missing from the project")
    return resolved


def _validate_concurrency(value: str) -> str:
    if not isinstance(value, str):
        raise RenderError("Concurrency must be an integer or percentage string")
    if re.fullmatch(r"(?:[1-9]|[1-9][0-9]|100)%", value):
        return value
    if re.fullmatch(r"[1-9][0-9]{0,2}", value) and 1 <= int(value) <= 256:
        return value
    raise RenderError("Concurrency must be 1–256 workers or a percentage from 1% to 100%")


def render_project(project: Path, output: Path | None = None, concurrency: str = "50%") -> Path:
    story_path = project_story_path(project)
    project_dir = story_path.parent.resolve()
    story = read_json(story_path)
    issues = [issue for issue in validate_story(story) if issue.severity == "error"]
    if issues:
        raise RenderError("Cannot render an invalid story: " + "; ".join(map(str, issues[:8])))
    concurrency = _validate_concurrency(str(concurrency))

    root = Path(__file__).resolve().parent.parent / "remotion"
    package_json = root / "package.json"
    if not package_json.is_file():
        raise RenderError("Remotion source directory is missing from this Kinoquence installation")
    if not (root / "node_modules" / ".bin" / "remotion").exists() and not (root / "node_modules" / ".bin" / "remotion.cmd").exists():
        raise RenderError("Remotion dependencies are not installed. Run `npm install` inside the `remotion/` directory for this release candidate.")
    npx = shutil.which("npx")
    if not npx:
        raise RenderError("npx was not found. Install Node.js and npm, then retry.")

    destination = output or (project_dir / "exports" / "final.mp4")
    destination = destination.expanduser()
    if destination.is_symlink():
        raise RenderError("Output path must not be a symlink")
    destination = destination.resolve()
    protected_inputs = {story_path.resolve()}
    for key in ("narration_audio", "music_audio", "sfx_audio"):
        relative = (story.get("assets") or {}).get(key) if isinstance(story.get("assets"), dict) else None
        if isinstance(relative, str) and relative.strip():
            protected_inputs.add(_resolve_project_asset(project_dir, relative))
    if destination in protected_inputs:
        raise RenderError("Output path must not overwrite story.json or an audio input asset")

    slug = "".join(char.lower() if char.isalnum() else "-" for char in project_dir.name).strip("-") or "project"
    # A unique, temporary public directory prevents concurrent renders from overwriting one another
    # and ensures user-supplied audio is removed from the renderer after the job.
    public_root = root / "public"
    public_root.mkdir(parents=True, exist_ok=True)
    temporary_id = uuid.uuid4().hex[:12]
    public_media = Path(tempfile.mkdtemp(prefix=f"kinoquence-{slug[:32]}-{temporary_id}-", dir=public_root))
    props_path: Path | None = None

    try:
        assets = story.get("assets", {}) if isinstance(story.get("assets"), dict) else {}
        props: dict[str, Any] = {"story": story}
        for key in ("narration_audio", "music_audio", "sfx_audio"):
            local = assets.get(key)
            if local:
                source = _resolve_project_asset(project_dir, local)
                destination_name = f"{key}{source.suffix.lower()}"
                shutil.copy2(source, public_media / destination_name)
                props[key] = f"{public_media.relative_to(public_root).as_posix()}/{destination_name}"

        props_dir = project_child_path(project_dir, ".kinoquence")
        props_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json", prefix="render-props-", dir=props_dir, delete=False) as handle:
            json.dump(props, handle, ensure_ascii=False, allow_nan=False)
            handle.write("\n")
            props_path = Path(handle.name)

        destination.parent.mkdir(parents=True, exist_ok=True)
        command = [
            npx, "--no-install", "remotion", "render", "src/index.ts", "KinoquenceShort", str(destination),
            "--props", str(props_path), "--codec", "h264", "--crf", "16", "--concurrency", concurrency,
        ]
        try:
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False, timeout=3600)
        except subprocess.TimeoutExpired as exc:
            raise RenderError("Remotion render exceeded the one-hour safety timeout") from exc
        if result.returncode != 0:
            # Renderer logs may include scene text or local paths. Keep the default diagnostic
            # intentionally terse so a normal CLI failure cannot echo private project content.
            raise RenderError(
                f"Remotion render failed (exit {result.returncode}); renderer output was suppressed to protect project content. "
                "Run the render directly with Remotion in the local project to inspect detailed diagnostics."
            )
        if not destination.is_file() or destination.stat().st_size == 0:
            raise RenderError("Render command returned success but output file is missing or empty")
        return destination
    except OSError as exc:
        raise RenderError(f"File operation failed during rendering ({type(exc).__name__})") from exc
    finally:
        if props_path is not None:
            props_path.unlink(missing_ok=True)
        shutil.rmtree(public_media, ignore_errors=True)
