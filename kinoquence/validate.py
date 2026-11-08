from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .schema import CAMERA_MOVES, ELEMENT_TYPES, SCHEMA_VERSION
from .utils import project_story_path, read_json


MAX_SCENES = 100
MAX_ELEMENTS_PER_SCENE = 200
MAX_SCENE_SECONDS = 60.0
MAX_STORY_SECONDS = 180.0
MAX_DIMENSION = 3840
MAX_PIXELS = 8_294_400
ALLOWED_SFX = {"soft_pop", "whoosh", "impact", "chime", "warm_chime", "rain_light", "birds_soft"}
_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
_SCENE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


@dataclass(frozen=True)
class Issue:
    severity: str
    location: str
    message: str

    def __str__(self) -> str:
        return f"{self.severity.upper():7} {self.location}: {self.message}"


def _num(value: Any) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _valid_web_url(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip() or any(ch.isspace() for ch in value):
        return False
    try:
        parsed = urlsplit(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.hostname) and parsed.username is None and parsed.password is None
    except ValueError:
        return False


def _check_color(value: Any, location: str, issues: list[Issue], *, optional: bool = False) -> None:
    if value is None and optional:
        return
    if not isinstance(value, str) or not _HEX_COLOR.fullmatch(value):
        issues.append(Issue("error", location, "must be a six-digit CSS hex colour such as #12ABEF"))


def _check_coordinate(value: Any, field: str, location: str, issues: list[Issue]) -> None:
    if not _num(value):
        issues.append(Issue("error", f"{location}.{field}", "must be a finite number"))
        return
    upper = 100 if field in {"x", "x2"} else 177.78
    if not -10 <= value <= upper + 10:
        issues.append(Issue("warning", f"{location}.{field}", f"coordinate is outside the normalized composition grid (x≤100, y≤177.78)"))


def validate_story(story: Any) -> list[Issue]:
    issues: list[Issue] = []
    if not isinstance(story, dict):
        return [Issue("error", "story", "top-level JSON value must be an object")]

    required = ("title", "story_type", "fps", "width", "height", "scenes")
    missing = [key for key in required if key not in story]
    for key in missing:
        issues.append(Issue("error", key, "required field is missing"))
    if missing:
        return issues

    if story.get("schema_version") != SCHEMA_VERSION:
        issues.append(Issue("error", "schema_version", f"must be the supported schema version {SCHEMA_VERSION!r}"))

    title = story.get("title")
    if not isinstance(title, str) or not title.strip() or len(title) > 120:
        issues.append(Issue("error", "title", "must be a non-empty string no longer than 120 characters"))
    if not isinstance(story.get("language", "en"), str) or not 2 <= len(story.get("language", "en")) <= 32:
        issues.append(Issue("error", "language", "must be a language tag between 2 and 32 characters"))
    story_type = story.get("story_type")
    if not isinstance(story_type, str) or story_type not in {"fiction", "nonfiction", "hybrid", "promotional", "educational"}:
        issues.append(Issue("error", "story_type", "must be fiction, nonfiction, hybrid, promotional, or educational"))

    for key, lower, upper in (("fps", 1, 120), ("width", 64, MAX_DIMENSION), ("height", 64, MAX_DIMENSION)):
        value = story.get(key)
        if not _num(value) or value < lower or value > upper:
            issues.append(Issue("error", key, f"must be a finite number between {lower} and {upper}"))
        elif key in {"width", "height"} and int(value) != value:
            issues.append(Issue("error", key, "must be a whole number of pixels"))

    width, height = story.get("width"), story.get("height")
    if _num(width) and _num(height):
        if width * height > MAX_PIXELS:
            issues.append(Issue("error", "resolution", f"canvas exceeds the {MAX_PIXELS:,}-pixel safety limit"))
        if width / height > 1:
            issues.append(Issue("warning", "aspect_ratio", "canvas is landscape; vertical shorts are usually 9:16"))

    scenes = story.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        issues.append(Issue("error", "scenes", "must be a non-empty array"))
        return issues
    if len(scenes) > MAX_SCENES:
        issues.append(Issue("error", "scenes", f"must contain no more than {MAX_SCENES} scenes"))

    scene_ids: set[str] = set()
    total = 0.0
    for index, scene in enumerate(scenes[:MAX_SCENES]):
        loc = f"scenes[{index}]"
        if not isinstance(scene, dict):
            issues.append(Issue("error", loc, "scene must be an object"))
            continue

        scene_id = scene.get("id")
        if not isinstance(scene_id, str) or not _SCENE_ID.fullmatch(scene_id):
            issues.append(Issue("error", f"{loc}.id", "must use 1–64 letters, digits, underscores or hyphens; start with a letter or digit"))
        elif scene_id in scene_ids:
            issues.append(Issue("error", f"{loc}.id", f"duplicate scene id {scene_id!r}"))
        else:
            scene_ids.add(scene_id)

        duration = scene.get("duration_seconds")
        if not _num(duration) or not 0.5 <= duration <= MAX_SCENE_SECONDS:
            issues.append(Issue("error", f"{loc}.duration_seconds", f"must be a finite number between 0.5 and {MAX_SCENE_SECONDS:g} seconds"))
        else:
            total += float(duration)

        narration = scene.get("narration")
        if not isinstance(narration, str) or not narration.strip():
            issues.append(Issue("warning", f"{loc}.narration", "no narration supplied"))
        elif len(narration) > 2000:
            issues.append(Issue("error", f"{loc}.narration", "must be no longer than 2,000 characters"))
        caption = scene.get("caption")
        if caption is not None and (not isinstance(caption, str) or len(caption) > 300):
            issues.append(Issue("error", f"{loc}.caption", "must be a string no longer than 300 characters"))

        move = scene.get("camera_move", "static")
        if not isinstance(move, str) or move not in CAMERA_MOVES:
            issues.append(Issue("error", f"{loc}.camera_move", f"unsupported camera move {move!r}"))
        cues = scene.get("sfx", [])
        if not isinstance(cues, list):
            issues.append(Issue("error", f"{loc}.sfx", "must be an array of supported sound-effect cue names"))
        else:
            if len(cues) > 20:
                issues.append(Issue("error", f"{loc}.sfx", "must contain no more than 20 sound-effect cues per scene"))
            for cue_index, cue in enumerate(cues[:20]):
                if not isinstance(cue, str) or cue not in ALLOWED_SFX:
                    issues.append(Issue("error", f"{loc}.sfx[{cue_index}]", f"unsupported sound-effect cue {cue!r}"))

        visual = scene.get("visual")
        if not isinstance(visual, dict):
            issues.append(Issue("error", f"{loc}.visual", "must be an object"))
            continue
        _check_color(visual.get("background"), f"{loc}.visual.background", issues)
        _check_color(visual.get("secondary_background"), f"{loc}.visual.secondary_background", issues, optional=True)
        for field, limit in (("title", 120), ("subtitle", 180)):
            value = visual.get(field)
            if value is not None and (not isinstance(value, str) or len(value) > limit):
                issues.append(Issue("error", f"{loc}.visual.{field}", f"must be a string no longer than {limit} characters"))

        elements = visual.get("elements")
        if not isinstance(elements, list):
            issues.append(Issue("error", f"{loc}.visual.elements", "must be an array"))
            continue
        if len(elements) > MAX_ELEMENTS_PER_SCENE:
            issues.append(Issue("error", f"{loc}.visual.elements", f"must contain no more than {MAX_ELEMENTS_PER_SCENE} elements"))
        for j, element in enumerate(elements[:MAX_ELEMENTS_PER_SCENE]):
            eloc = f"{loc}.visual.elements[{j}]"
            if not isinstance(element, dict):
                issues.append(Issue("error", eloc, "element must be an object"))
                continue
            kind = element.get("type")
            if not isinstance(kind, str) or kind not in ELEMENT_TYPES:
                issues.append(Issue("error", f"{eloc}.type", f"unsupported element type {kind!r}"))
                continue

            coordinate_fields = ("x", "y", "x2", "y2") if kind == "line" else (() if kind == "polygon" else ("x", "y"))
            for field in coordinate_fields:
                _check_coordinate(element.get(field), field, eloc, issues)

            if kind == "polygon":
                points = element.get("points")
                if not isinstance(points, list) or not 3 <= len(points) <= 100 or not all(
                    isinstance(point, list) and len(point) == 2 and all(_num(value) for value in point)
                    for point in points
                ):
                    issues.append(Issue("error", f"{eloc}.points", "polygon requires 3–100 finite [x, y] point pairs"))
                elif isinstance(points, list):
                    for point_index, point in enumerate(points):
                        _check_coordinate(point[0], "x", f"{eloc}.points[{point_index}]", issues)
                        _check_coordinate(point[1], "y", f"{eloc}.points[{point_index}]", issues)
            elif kind not in {"line", "text"}:
                for field in ("w", "h"):
                    value = element.get(field)
                    if not _num(value) or not 0 < value <= 200:
                        issues.append(Issue("error", f"{eloc}.{field}", "must be a finite number greater than 0 and no greater than 200"))

            if kind == "text":
                text_value = element.get("text")
                if not isinstance(text_value, str) or len(text_value) > 300:
                    issues.append(Issue("error", f"{eloc}.text", "text element requires a string no longer than 300 characters"))
                font_size = element.get("font_size", 4)
                if not _num(font_size) or not 0.5 <= font_size <= 30:
                    issues.append(Issue("error", f"{eloc}.font_size", "must be between 0.5 and 30"))

            _check_color(element.get("fill"), f"{eloc}.fill", issues, optional=True)
            stroke = element.get("stroke")
            if stroke is not None and stroke != "none":
                _check_color(stroke, f"{eloc}.stroke", issues)
            stroke_width = element.get("stroke_width", 0.5)
            if not _num(stroke_width) or not 0 <= stroke_width <= 20:
                issues.append(Issue("error", f"{eloc}.stroke_width", "must be between 0 and 20"))
            rotation = element.get("rotation")
            if rotation is not None and (not _num(rotation) or abs(rotation) > 36000):
                issues.append(Issue("error", f"{eloc}.rotation", "must be a finite angle between -36000 and 36000 degrees"))

    if total > MAX_STORY_SECONDS:
        issues.append(Issue("error", "duration", f"total duration {total:.1f}s exceeds the {MAX_STORY_SECONDS:g}s safety limit"))
    elif total < 10:
        issues.append(Issue("warning", "duration", f"total duration is {total:.1f}s; typical shorts are 15–90s"))

    target = story.get("target_duration_seconds")
    if target is not None:
        if not _num(target) or not 1 <= target <= MAX_STORY_SECONDS:
            issues.append(Issue("error", "target_duration_seconds", f"must be between 1 and {MAX_STORY_SECONDS:g} seconds"))
        elif abs(total - target) > max(3.0, target * 0.12):
            issues.append(Issue("warning", "target_duration_seconds", f"scene total is {total:.1f}s but target is {target:.1f}s"))

    if story_type in {"nonfiction", "hybrid", "educational"}:
        sources = story.get("sources", [])
        claims = story.get("claims", [])
        if not isinstance(sources, list) or not sources:
            issues.append(Issue("error", "sources", "fact-based stories require source records"))
            sources = []
        elif len(sources) > 500:
            issues.append(Issue("error", "sources", "must contain no more than 500 source records"))
        if not isinstance(claims, list) or not claims:
            issues.append(Issue("error", "claims", "fact-based stories require a claim-to-source map"))
            claims = []
        elif len(claims) > 1000:
            issues.append(Issue("error", "claims", "must contain no more than 1,000 factual claims"))
        known: set[str] = set()
        for i, source in enumerate(sources[:500]):
            if not isinstance(source, dict):
                issues.append(Issue("error", f"sources[{i}]", "source must be an object"))
                continue
            source_id = source.get("id")
            if not isinstance(source_id, str) or not source_id.strip() or len(source_id) > 80:
                issues.append(Issue("error", f"sources[{i}].id", "source needs a stable non-empty id no longer than 80 characters"))
            else:
                if source_id in known:
                    issues.append(Issue("error", f"sources[{i}].id", f"duplicate source id {source_id!r}"))
                known.add(source_id)
            if not isinstance(source.get("title"), str) or not source.get("title", "").strip():
                issues.append(Issue("error", f"sources[{i}].title", "source title is required"))
            if not _valid_web_url(source.get("url")):
                issues.append(Issue("error", f"sources[{i}].url", "source must have a valid http(s) URL without embedded credentials"))
        for i, claim in enumerate(claims[:1000]):
            if not isinstance(claim, dict) or not isinstance(claim.get("claim"), str) or not claim.get("claim", "").strip():
                issues.append(Issue("error", f"claims[{i}]", "each claim needs non-empty claim text"))
                continue
            refs = claim.get("source_ids")
            if not isinstance(refs, list) or not refs or any(not isinstance(ref, str) or ref not in known for ref in refs):
                issues.append(Issue("error", f"claims[{i}].source_ids", "each factual claim must link to known source ids"))

    assets = story.get("assets", {})
    if assets is not None:
        if not isinstance(assets, dict):
            issues.append(Issue("error", "assets", "must be an object mapping audio roles to project-relative paths"))
        else:
            for role in ("narration_audio", "music_audio", "sfx_audio"):
                value = assets.get(role)
                if value is not None:
                    if not isinstance(value, str) or not value.strip():
                        issues.append(Issue("error", f"assets.{role}", "must be a non-empty project-relative path string"))
                    elif Path(value).is_absolute() or ".." in Path(value).parts:
                        issues.append(Issue("error", f"assets.{role}", "must not be absolute or contain parent-directory traversal"))

    return issues


def validate_asset_manifest(project_dir: Path) -> list[Issue]:
    manifest = project_dir / "assets.csv"
    if not manifest.exists():
        return [Issue("warning", "assets.csv", "manifest not found; create one before distributing assets")]
    required = {"path", "asset_type", "creator", "source_url", "license", "attribution", "commercial_use"}
    issues: list[Issue] = []
    try:
        root = project_dir.resolve()
        resolved_manifest = manifest.resolve()
        try:
            resolved_manifest.relative_to(root)
        except ValueError:
            return [Issue("error", "assets.csv", "manifest symlink must not point outside the project directory")]
        with resolved_manifest.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            missing = required - set(reader.fieldnames or [])
            if missing:
                return [Issue("error", "assets.csv", f"missing columns: {', '.join(sorted(missing))}")]
            for line, row in enumerate(reader, start=2):
                if not any((value or "").strip() for value in row.values()):
                    continue
                for field in required:
                    if not (row.get(field) or "").strip():
                        issues.append(Issue("error", f"assets.csv:{line}.{field}", "required attribution field is blank"))
                rel = (row.get("path") or "").strip()
                if rel:
                    if rel.startswith(("http://", "https://")):
                        if not _valid_web_url(rel):
                            issues.append(Issue("error", f"assets.csv:{line}.path", "asset URL is malformed or contains embedded credentials"))
                    else:
                        candidate = Path(rel)
                        if candidate.is_absolute():
                            issues.append(Issue("error", f"assets.csv:{line}.path", "local asset paths must be project-relative"))
                        else:
                            resolved = (root / candidate).resolve()
                            try:
                                resolved.relative_to(root)
                            except ValueError:
                                issues.append(Issue("error", f"assets.csv:{line}.path", "local asset path escapes the project directory"))
                            else:
                                if not resolved.exists():
                                    issues.append(Issue("warning", f"assets.csv:{line}.path", f"local asset is missing: {rel}"))
                if (row.get("license") or "").strip().lower() in {"unknown", "n/a", "unspecified"}:
                    issues.append(Issue("error", f"assets.csv:{line}.license", "unknown asset license; do not redistribute until verified"))
    except (OSError, UnicodeError, csv.Error, RuntimeError, ValueError) as exc:
        issues.append(Issue("error", "assets.csv", f"could not read manifest: {type(exc).__name__}"))
    return issues


def validate_project(path: Path) -> tuple[list[Issue], Any]:
    story_path = project_story_path(path)
    story = read_json(story_path)
    project_dir = story_path.parent.resolve()
    issues = validate_story(story)
    issues.extend(validate_asset_manifest(project_dir))
    if isinstance(story, dict) and isinstance(story.get("assets"), dict):
        for role in ("narration_audio", "music_audio", "sfx_audio"):
            relative = story["assets"].get(role)
            if isinstance(relative, str) and relative.strip() and not Path(relative).is_absolute() and ".." not in Path(relative).parts:
                try:
                    candidate = (project_dir / relative).resolve()
                    candidate.relative_to(project_dir)
                except (ValueError, OSError, RuntimeError):
                    issues.append(Issue("error", f"assets.{role}", "asset path resolves outside the project directory or contains a symlink loop"))
                else:
                    if not candidate.is_file():
                        issues.append(Issue("warning", f"assets.{role}", "listed audio asset does not exist yet"))
    return issues, story
