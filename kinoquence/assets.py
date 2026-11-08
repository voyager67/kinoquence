from __future__ import annotations

import csv
from pathlib import Path

from .utils import project_child_path
from .validate import validate_asset_manifest


def write_credits(project_dir: Path, output: Path | None = None) -> Path:
    manifest = project_child_path(project_dir, "assets.csv")
    destination = output or project_child_path(project_dir, "CREDITS.md")
    destination = destination.expanduser().resolve()
    rows: list[dict[str, str]] = []
    if manifest.exists():
        with manifest.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    lines = ["# Credits and asset provenance", "", "This file is generated from `assets.csv`. Check each provider's current terms before publishing.", ""]
    if not rows:
        lines.append("No third-party assets are currently listed. Add every imported image, font, video, sound and model-generated asset to `assets.csv`.")
    else:
        for row in rows:
            if not any((v or "").strip() for v in row.values()):
                continue
            label = row.get("path") or row.get("asset_type") or "Asset"
            lines.extend([
                f"## {label}",
                f"- Type: {row.get('asset_type', '')}",
                f"- Creator: {row.get('creator', '')}",
                f"- Source: {row.get('source_url', '')}",
                f"- License: {row.get('license', '')}",
                f"- Attribution: {row.get('attribution', '')}",
                f"- Commercial use: {row.get('commercial_use', '')}",
                f"- Notes: {row.get('notes', '')}",
                "",
            ])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return destination


def audit_assets(project_dir: Path) -> list[str]:
    return [str(issue) for issue in validate_asset_manifest(project_dir)]
