import shutil
import subprocess
import tempfile
from unittest.mock import patch
import unittest
from pathlib import Path

from kinoquence.qa import QAError, inspect_video


class VideoQATests(unittest.TestCase):
    def test_probe_failure_does_not_echo_local_video_path(self):
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "private-customer-project.mp4"
            video.write_bytes(b"not a real video")
            failed = subprocess.CompletedProcess(["ffprobe"], 1, "", f"cannot read {video}")
            with patch("kinoquence.qa.shutil.which", side_effect=lambda name: f"/usr/bin/{name}"):
                with patch("kinoquence.qa._run", return_value=failed):
                    with self.assertRaises(QAError) as raised:
                        inspect_video(video)
            self.assertNotIn(str(video), str(raised.exception))

    def test_missing_video_error_does_not_echo_local_path(self):
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "private-customer-project.mp4"
            with self.assertRaises(QAError) as raised:
                inspect_video(video)
            self.assertNotIn(str(video), str(raised.exception))

    def test_ffmpeg_generated_clip_is_inspected_without_exposing_full_path(self):
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg and ffprobe are required for this integration test")
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "sample.mp4"
            command = [
                ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "color=c=blue:s=540x960:d=2:r=30",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(video),
            ]
            generated = subprocess.run(command, capture_output=True, text=True, check=False, timeout=120)
            if generated.returncode != 0:
                self.skipTest(f"FFmpeg build could not create the integration fixture: {generated.stderr[-300:]}")
            report = inspect_video(video)
            self.assertEqual(report["file"], "sample.mp4")
            self.assertEqual(report["width"], 540)
            self.assertEqual(report["height"], 960)
            self.assertGreaterEqual(report["duration_seconds"], 1.9)
            self.assertEqual(report["black_spans"], [])
            self.assertEqual(report["freeze_spans"], [])


if __name__ == "__main__":
    unittest.main()
