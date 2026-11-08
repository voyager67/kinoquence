from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .utils import project_child_path, project_story_path, read_json
from .validate import validate_story


def _timecode(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, ms = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{whole_seconds:02},{ms:03}"


def _chunks(text: str, max_words: int = 9) -> list[str]:
    words = re.sub(r"\s+", " ", text.strip()).split(" ") if text.strip() else []
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]


def build_srt(story: dict[str, Any], max_words: int = 9) -> str:
    if not isinstance(max_words, int) or isinstance(max_words, bool) or max_words < 1:
        raise ValueError("max_words must be a positive whole number")
    lines: list[str] = []
    cursor = 0.0
    counter = 1
    for scene in story.get("scenes", []):
        duration = float(scene.get("duration_seconds", 0))
        source = scene.get("caption") or scene.get("narration", "")
        chunks = _chunks(str(source), max_words=max_words)
        if chunks and duration > 0:
            slice_duration = duration / len(chunks)
            for index, chunk in enumerate(chunks):
                start = cursor + index * slice_duration
                end = cursor + (index + 1) * slice_duration
                lines.extend([str(counter), f"{_timecode(start)} --> {_timecode(end)}", chunk, ""])
                counter += 1
        cursor += duration
    return "\n".join(lines).rstrip() + ("\n" if lines else "")


def export_captions(path: Path, output: Path | None = None) -> Path:
    story_path = project_story_path(path)
    story = read_json(story_path)
    issues = [issue for issue in validate_story(story) if issue.severity == "error"]
    if issues:
        raise ValueError("Cannot export captions from an invalid story: " + "; ".join(map(str, issues[:8])))
    destination = output or project_child_path(story_path.parent, "exports/captions.srt")
    destination = destination.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(build_srt(story), encoding="utf-8")
    return destination
