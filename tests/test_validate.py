import json
import tempfile
import unittest
from pathlib import Path

from kinoquence.schema import starter_story
from kinoquence.validate import validate_asset_manifest, validate_story


class StoryValidationTests(unittest.TestCase):
    def test_starter_story_has_no_errors(self):
        issues = validate_story(starter_story())
        self.assertFalse([issue for issue in issues if issue.severity == "error"], issues)

    def test_duplicate_scene_ids_are_rejected(self):
        story = starter_story()
        story["scenes"].append(dict(story["scenes"][0]))
        errors = [issue for issue in validate_story(story) if issue.severity == "error"]
        self.assertTrue(any("duplicate scene id" in issue.message for issue in errors))

    def test_invalid_camera_move_is_rejected(self):
        story = starter_story()
        story["scenes"][0]["camera_move"] = "spin_around"
        errors = [issue for issue in validate_story(story) if issue.severity == "error"]
        self.assertTrue(any("unsupported camera move" in issue.message for issue in errors))

    def test_fact_based_story_requires_claims_and_sources(self):
        story = starter_story()
        story["story_type"] = "nonfiction"
        errors = [issue for issue in validate_story(story) if issue.severity == "error"]
        self.assertTrue(any(issue.location == "sources" for issue in errors))
        self.assertTrue(any(issue.location == "claims" for issue in errors))

    def test_nonfiction_story_with_mapped_sources_is_valid(self):
        story = starter_story()
        story["story_type"] = "nonfiction"
        story["sources"] = [{"id": "s1", "title": "Primary source", "url": "https://example.com/source"}]
        story["claims"] = [{"claim": "A verifiable statement", "source_ids": ["s1"]}]
        errors = [issue for issue in validate_story(story) if issue.severity == "error"]
        self.assertEqual(errors, [])

    def test_claim_cannot_reference_unknown_source(self):
        story = starter_story()
        story["story_type"] = "nonfiction"
        story["sources"] = [{"id": "s1", "title": "Primary source", "url": "https://example.com/source"}]
        story["claims"] = [{"claim": "A verifiable statement", "source_ids": ["missing"]}]
        errors = [issue for issue in validate_story(story) if issue.severity == "error"]
        self.assertTrue(any("known source id" in issue.message for issue in errors))

    def test_landscape_dimension_type_does_not_crash(self):
        story = starter_story()
        story["width"] = "wide"
        issues = validate_story(story)
        self.assertTrue(any(issue.location == "width" for issue in issues))

    def test_asset_manifest_empty_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "assets.csv").write_text(
                "path,asset_type,creator,source_url,license,attribution,commercial_use,notes\n",
                encoding="utf-8",
            )
            self.assertEqual(validate_asset_manifest(project), [])

    def test_unknown_asset_license_is_error(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "assets.csv").write_text(
                "path,asset_type,creator,source_url,license,attribution,commercial_use,notes\n"
                ",audio,Someone,https://example.com,unknown,,no,verify\n",
                encoding="utf-8",
            )
            issues = validate_asset_manifest(project)
            self.assertTrue(any(issue.severity == "error" and "unknown asset license" in issue.message for issue in issues))

    def test_non_object_story_returns_issue_not_exception(self):
        issues = validate_story(["not", "an", "object"])
        self.assertTrue(any(issue.location == "story" for issue in issues))

    def test_unhashable_camera_move_and_element_type_are_rejected_safely(self):
        story = starter_story()
        story["scenes"][0]["camera_move"] = []
        story["scenes"][0]["visual"]["elements"][0]["type"] = []
        issues = validate_story(story)
        self.assertTrue(any(issue.location.endswith("camera_move") for issue in issues))
        self.assertTrue(any(issue.location.endswith(".type") for issue in issues))

    def test_non_finite_numbers_are_rejected(self):
        story = starter_story()
        story["scenes"][0]["duration_seconds"] = float("nan")
        issues = validate_story(story)
        self.assertTrue(any(issue.location.endswith("duration_seconds") for issue in issues))

    def test_story_duration_has_a_hard_safety_limit(self):
        story = starter_story()
        for scene in story["scenes"]:
            scene["duration_seconds"] = 40
        issues = validate_story(story)
        self.assertTrue(any(issue.location == "duration" and issue.severity == "error" for issue in issues))

    def test_renderer_colors_are_restricted_to_hex_values(self):
        story = starter_story()
        story["scenes"][0]["visual"]["background"] = "url(javascript:alert(1))"
        issues = validate_story(story)
        self.assertTrue(any(issue.location.endswith("visual.background") for issue in issues))

    def test_polygon_does_not_require_unused_x_y_fields(self):
        story = starter_story()
        story["scenes"][0]["visual"]["elements"] = [
            {"type": "polygon", "points": [[10, 10], [20, 10], [15, 20]], "fill": "#AABBCC"}
        ]
        errors = [issue for issue in validate_story(story) if issue.severity == "error"]
        self.assertEqual(errors, [])

    def test_asset_manifest_symlink_cannot_read_outside_project(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            private = root / "private.csv"
            private.write_text(
                "path,asset_type,creator,source_url,license,attribution,commercial_use,notes\n",
                encoding="utf-8",
            )
            try:
                (project / "assets.csv").symlink_to(private)
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks are not available in this environment")
            issues = validate_asset_manifest(project)
            self.assertTrue(any(issue.severity == "error" and "symlink" in issue.message for issue in issues))

    def test_asset_manifest_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            project.mkdir()
            (project / "assets.csv").write_text(
                "path,asset_type,creator,source_url,license,attribution,commercial_use,notes\n"
                "../private.wav,audio,Creator,https://example.com,MIT,credit,no,external file\n",
                encoding="utf-8",
            )
            issues = validate_asset_manifest(project)
            self.assertTrue(any(issue.severity == "error" and "escapes the project" in issue.message for issue in issues))


if __name__ == "__main__":
    unittest.main()
