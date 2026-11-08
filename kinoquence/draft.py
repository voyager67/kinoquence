from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .providers import ProviderConfig, generate_text
from .utils import project_child_path, project_story_path, read_json, write_json
from .validate import validate_story


class DraftError(RuntimeError):
    pass


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise DraftError("Model response did not contain a JSON object")
        try:
            value = json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError as exc:
            raise DraftError(f"Could not parse model JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise DraftError("Model response must be a JSON object")
    return value


def draft_story(project: Path, config: ProviderConfig, topic: str, style: str = "storybook_2_5d") -> tuple[Path, list[str]]:
    story_path = project_story_path(project)
    current = read_json(story_path)
    prompt_file = Path(__file__).resolve().parent / "prompts" / "story_director.md"
    system = prompt_file.read_text(encoding="utf-8")
    user = (
        f"Create a new short video plan about: {topic}\n\n"
        f"Preferred visual style: {style}\n"
        f"Existing canvas: {current.get('width', 1080)}x{current.get('height', 1920)} at {current.get('fps', 30)} fps.\n"
        "Return one complete story.json object. Preserve the schema and required fields. "
        "For nonfiction or educational topics, include sources and claim-to-source links; do not invent citations. "
        "For fiction, set story_type to fiction and do not add fake research claims."
    )
    response = generate_text(config, system, user)
    result = _extract_json(response)
    issues = validate_story(result)
    errors = [str(issue) for issue in issues if issue.severity == "error"]
    destination = project_child_path(story_path.parent, ".kinoquence/last-draft.json")
    write_json(destination, result)
    if errors:
        raise DraftError("Draft was saved for inspection but failed schema validation:\n" + "\n".join(errors))
    # Keep the previous approved story until the user explicitly accepts this draft.
    return destination, [str(issue) for issue in issues]
