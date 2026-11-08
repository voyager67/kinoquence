import json
import shutil
from array import array
import subprocess
import tempfile
import unittest
from pathlib import Path

from kinoquence.audio import generate_music, generate_sfx, synthesize_project
from kinoquence.captions import build_srt
from kinoquence.draft import _extract_json, draft_story
from kinoquence.project import create_project
from kinoquence.render import RenderError, _resolve_project_asset
from kinoquence.providers import ProviderConfig
from kinoquence.utils import read_json
from kinoquence.validate import validate_project
from unittest.mock import patch


class ProjectAndMediaTests(unittest.TestCase):
    def test_create_project_and_validate(self):
        with tempfile.TemporaryDirectory() as directory:
            project = create_project(Path(directory) / "story", "A Test Story")
            issues, story = validate_project(project)
            self.assertEqual(story["title"], "A Test Story")
            self.assertFalse([issue for issue in issues if issue.severity == "error"], issues)
            self.assertTrue((project / "assets.csv").exists())
            self.assertTrue((project / "research" / "claims.csv").exists())

    def test_captions_include_ordered_timecodes(self):
        story = {
            "scenes": [
                {"duration_seconds": 4, "caption": "One small line that should split into two caption chunks now"},
                {"duration_seconds": 2, "caption": "Another line"},
            ]
        }
        srt = build_srt(story, max_words=5)
        self.assertIn("00:00:00,000 -->", srt)
        self.assertIn("00:00:04,000 --> 00:00:06,000", srt)
        self.assertTrue(srt.startswith("1\n"))

    def test_procedural_audio_is_deterministic(self):
        first = generate_music(0.1, seed=7)
        second = generate_music(0.1, seed=7)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 4800)
        self.assertTrue(any(abs(sample) > 0 for sample in first))

    def test_audio_uses_compact_float_buffers(self):
        samples = generate_music(0.1, seed=7)
        self.assertIsInstance(samples, array)
        self.assertEqual(samples.typecode, "f")
        self.assertLess(samples.itemsize, 8)

    def test_audio_duration_guard_rejects_unbounded_generation(self):
        with self.assertRaises(ValueError):
            generate_music(181)

    def test_audio_duration_guard_rejects_extremely_large_integer(self):
        with self.assertRaises(ValueError):
            generate_music(10 ** 1000)

    def test_project_audio_writes_tracks_and_updates_story(self):
        with tempfile.TemporaryDirectory() as directory:
            project = create_project(Path(directory) / "story", "Audio Test")
            music, sfx = synthesize_project(project)
            self.assertTrue(music.exists())
            self.assertTrue(sfx.exists())
            story = read_json(project / "story.json")
            self.assertEqual(story["assets"]["music_audio"], "assets/generated_music.wav")
            self.assertEqual(story["assets"]["sfx_audio"], "assets/generated_sfx.wav")

    def test_audio_output_rejects_symlinked_assets_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            project = create_project(Path(directory) / "project", "Symlink test")
            outside = Path(directory) / "outside"
            outside.mkdir()
            assets = project / "assets"
            assets.rmdir()
            try:
                assets.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Directory symlinks are not available in this environment")
            with self.assertRaises(ValueError):
                synthesize_project(project)
            self.assertEqual(list(outside.iterdir()), [])

    def test_render_asset_must_stay_inside_project(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project"
            root.mkdir()
            outside = Path(directory) / "private.wav"
            outside.write_bytes(b"not audio")
            with self.assertRaises(RenderError):
                _resolve_project_asset(root, "../private.wav")
            with self.assertRaises(RenderError):
                _resolve_project_asset(root, str(outside))

    def test_render_asset_rejects_symlink_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project"
            root.mkdir()
            outside = Path(directory) / "outside.wav"
            outside.write_bytes(b"not audio")
            link = root / "audio.wav"
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks are not available in this environment")
            with self.assertRaises(RenderError):
                _resolve_project_asset(root, "audio.wav")

    def test_render_stages_private_audio_temporarily_and_cleans_it(self):
        from kinoquence import render as render_module

        project_root = Path(__file__).resolve().parents[1]
        remotion_root = project_root / "remotion"
        node_modules = remotion_root / "node_modules"
        made_node_modules = not node_modules.exists()
        (node_modules / ".bin").mkdir(parents=True, exist_ok=True)
        fake_executable = node_modules / ".bin" / "remotion"
        fake_executable.write_text("test marker", encoding="utf-8")
        try:
            with tempfile.TemporaryDirectory() as directory:
                project = create_project(Path(directory) / "render-test", "Render test")
                audio = project / "assets" / "private-track.wav"
                audio.write_bytes(b"private audio")
                story = read_json(project / "story.json")
                story["assets"] = {"music_audio": "assets/private-track.wav"}
                from kinoquence.utils import write_json
                write_json(project / "story.json", story)
                output = project / "exports" / "test.mp4"

                def fake_render(command, cwd, capture_output, text, check, timeout):
                    props_arg = command[command.index("--props") + 1]
                    self.assertTrue(Path(props_arg).is_file())
                    props = json.loads(Path(props_arg).read_text(encoding="utf-8"))
                    self.assertIn("music_audio", props)
                    staged_path = remotion_root / "public" / props["music_audio"]
                    self.assertTrue(staged_path.is_file())
                    output.write_bytes(b"test mp4 bytes")
                    return subprocess.CompletedProcess(command, 0, "ok", "")

                with patch("kinoquence.render.subprocess.run", side_effect=fake_render):
                    result = render_module.render_project(project, output)
                self.assertEqual(result, output.resolve())
                self.assertFalse(list((remotion_root / "public").glob("kinoquence-*")))
                self.assertFalse(list((project / ".kinoquence").glob("render-props-*.json")))
        finally:
            fake_executable.unlink(missing_ok=True)
            if made_node_modules:
                shutil.rmtree(node_modules, ignore_errors=True)

    def test_render_cannot_overwrite_declared_audio_input(self):
        from kinoquence import render as render_module

        project_root = Path(__file__).resolve().parents[1]
        remotion_root = project_root / "remotion"
        node_modules = remotion_root / "node_modules"
        made_node_modules = not node_modules.exists()
        (node_modules / ".bin").mkdir(parents=True, exist_ok=True)
        fake_executable = node_modules / ".bin" / "remotion"
        fake_executable.write_text("test marker", encoding="utf-8")
        try:
            with tempfile.TemporaryDirectory() as directory:
                project = create_project(Path(directory) / "protected-output", "Protected output")
                audio = project / "assets" / "do-not-overwrite.wav"
                audio.write_bytes(b"private audio input")
                story = read_json(project / "story.json")
                story["assets"] = {"music_audio": "assets/do-not-overwrite.wav"}
                from kinoquence.utils import write_json
                write_json(project / "story.json", story)
                with self.assertRaisesRegex(RenderError, "must not overwrite"):
                    render_module.render_project(project, audio)
                self.assertEqual(audio.read_bytes(), b"private audio input")
        finally:
            fake_executable.unlink(missing_ok=True)
            if made_node_modules:
                shutil.rmtree(node_modules, ignore_errors=True)

    def test_render_failure_does_not_echo_renderer_output(self):
        from kinoquence import render as render_module

        project_root = Path(__file__).resolve().parents[1]
        remotion_root = project_root / "remotion"
        node_modules = remotion_root / "node_modules"
        made_node_modules = not node_modules.exists()
        (node_modules / ".bin").mkdir(parents=True, exist_ok=True)
        fake_executable = node_modules / ".bin" / "remotion"
        fake_executable.write_text("test marker", encoding="utf-8")
        try:
            with tempfile.TemporaryDirectory() as directory:
                project = create_project(Path(directory) / "failed-render", "Private storyboard title")
                output = project / "exports" / "failed.mp4"
                def fake_render(command, cwd, capture_output, text, check, timeout):
                    return subprocess.CompletedProcess(command, 1, "PRIVATE_RENDER_STDOUT", "PRIVATE_RENDER_STDERR")
                with patch("kinoquence.render.subprocess.run", side_effect=fake_render):
                    with self.assertRaises(RenderError) as raised:
                        render_module.render_project(project, output)
                message = str(raised.exception)
                self.assertNotIn("PRIVATE_RENDER_STDOUT", message)
                self.assertNotIn("PRIVATE_RENDER_STDERR", message)
                self.assertFalse(list((remotion_root / "public").glob("kinoquence-*")))
                self.assertFalse(list((project / ".kinoquence").glob("render-props-*.json")))
        finally:
            fake_executable.unlink(missing_ok=True)
            if made_node_modules:
                shutil.rmtree(node_modules, ignore_errors=True)

    def test_draft_accepts_story_file_path_and_preserves_approved_story(self):
        with tempfile.TemporaryDirectory() as directory:
            project = create_project(Path(directory) / "story", "Approved Story")
            original = read_json(project / "story.json")
            draft = dict(original)
            draft["title"] = "Model Draft"
            with patch("kinoquence.draft.generate_text", return_value=json.dumps(draft)):
                destination, notes = draft_story(
                    project / "story.json",
                    ProviderConfig(provider="ollama", model="fake-model"),
                    "A fictional test topic",
                )
            self.assertEqual(destination, project / ".kinoquence" / "last-draft.json")
            self.assertEqual(read_json(destination)["title"], "Model Draft")
            self.assertEqual(read_json(project / "story.json"), original)

    def test_model_json_parser_accepts_fenced_payload(self):
        value = _extract_json('```json\n{"title":"Test","scenes":[]}\n```')
        self.assertEqual(value["title"], "Test")

    def test_model_json_parser_rejects_non_object(self):
        with self.assertRaises(Exception):
            _extract_json('["not", "an object"]')


if __name__ == "__main__":
    unittest.main()
