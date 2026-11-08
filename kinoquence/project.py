from __future__ import annotations

import csv
from pathlib import Path

from .schema import starter_story
from .utils import write_json


def create_project(path: Path, title: str | None = None) -> Path:
    path = path.expanduser().resolve()
    if path.exists() and any(path.iterdir()):
        raise ValueError(f"Refusing to overwrite a non-empty directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    for name in ("assets", "research", "exports", "notes"):
        (path / name).mkdir(exist_ok=True)
    write_json(path / "story.json", starter_story(title or path.name.replace("-", " ").title()))

    with (path / "assets.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["path", "asset_type", "creator", "source_url", "license", "attribution", "commercial_use", "notes"])

    with (path / "research" / "claims.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["claim_id", "claim", "source_id", "source_url", "source_title", "checked_by", "checked_at", "status", "notes"])

    (path / "CREDITS.md").write_text(
        "# Credits and provenance\n\n"
        "List every third-party image, sound, font, video, model output or code component used in the final export. "
        "See `assets.csv` and `research/claims.csv`. Do not distribute assets with unknown or incompatible terms.\n",
        encoding="utf-8",
    )
    (path / "PROJECT_NOTES.md").write_text(
        f"# {title or path.name}\n\n"
        "- Story type: fictional sample; replace or reclassify before publication.\n"
        "- Review every narration line and visual asset.\n"
        "- Add source records for factual claims.\n"
        "- Add provenance for every imported or generated asset.\n",
        encoding="utf-8",
    )
    return path
