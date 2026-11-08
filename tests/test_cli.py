import json
import os
import re
import unittest
from pathlib import Path
from argparse import Namespace
from unittest.mock import patch
from kinoquence.cli import _provider_config, build_parser
from kinoquence.providers import ProviderError


class CLITests(unittest.TestCase):
    def test_missing_custom_key_environment_name_is_not_echoed(self):
        args = Namespace(
            api_key_env="PRIVATE_VALUE_SHOULD_NOT_APPEAR", provider="openai", model="test-model",
            base_url=None, timeout=10, max_tokens=100, temperature=0.2,
        )
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ProviderError) as raised:
                _provider_config(args)
        self.assertNotIn("PRIVATE_VALUE_SHOULD_NOT_APPEAR", str(raised.exception))

    def test_release_versions_and_remotion_packages_are_aligned(self):
        root = Path(__file__).resolve().parents[1]
        init_text = (root / "kinoquence" / "__init__.py").read_text(encoding="utf-8")
        pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
        citation = (root / "CITATION.cff").read_text(encoding="utf-8")
        readme = (root / "README.md").read_text(encoding="utf-8")
        site = (root / "site" / "index.html").read_text(encoding="utf-8")
        package = json.loads((root / "remotion" / "package.json").read_text(encoding="utf-8"))

        self.assertRegex(init_text, r'__version__\s*=\s*["\']1\.0\.0rc3["\']')
        self.assertRegex(pyproject, r'(?m)^version\s*=\s*["\']1\.0\.0rc3["\']')
        self.assertRegex(citation, r'(?m)^version:\s*1\.0\.0-rc\.3$')
        self.assertIn("1.0.0-rc.3", readme)
        self.assertIn("1.0.0-rc.3", site)
        self.assertEqual(package["version"], "1.0.0-rc.3")
        self.assertEqual(package["dependencies"]["remotion"], "4.0.540")
        self.assertEqual(package["dependencies"]["@remotion/cli"], "4.0.540")
        self.assertEqual(package["dependencies"]["@remotion/media"], "4.0.540")

    def test_version_parser(self):
        parser = build_parser()
        with self.assertRaises(SystemExit) as raised:
            parser.parse_args(["--version"])
        self.assertEqual(raised.exception.code, 0)

    def test_draft_requires_topic(self):
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["draft", "project", "--provider", "openai", "--model", "model-id"])

    def test_api_keys_cannot_be_passed_as_command_line_arguments(self):
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args([
                "draft", "project", "--topic", "test", "--provider", "openai", "--model", "model-id",
                "--api-key", "do-not-accept-this",
            ])


if __name__ == "__main__":
    unittest.main()
