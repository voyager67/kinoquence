from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__
from .assets import audit_assets, write_credits
from .audio import synthesize_project
from .benchmark import run_benchmark
from .captions import export_captions
from .draft import DraftError, draft_story
from .project import create_project
from .providers import ProviderConfig, ProviderError
from .qa import QAError, inspect_video, write_report
from .render import RenderError, render_project
from .utils import eprint, load_dotenv, project_story_path, read_json, write_json
from .validate import validate_project


class _StrictArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("allow_abbrev", False)
        super().__init__(*args, **kwargs)


def _provider_config(args: argparse.Namespace) -> ProviderConfig:
    # Credentials are loaded only from environment variables or the untracked .env file.
    # Never accept API keys as command-line arguments: shells and process listings may expose them.
    custom_env = getattr(args, "api_key_env", None)
    key = os.getenv(custom_env) if custom_env else None
    if custom_env and not key:
        raise ProviderError("The environment variable selected by --api-key-env is not set")
    return ProviderConfig(
        provider=args.provider,
        model=args.model,
        base_url=args.base_url,
        api_key=key,
        timeout=args.timeout,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
    )


def _add_provider_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--provider", required=True, choices=["openai", "anthropic", "gemini", "xai", "ollama", "lmstudio", "vllm", "llamacpp", "openai-compatible"])
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url", help="Override provider API base URL; useful for OpenAI-compatible local servers")
    parser.add_argument("--api-key-env", help="Name of an environment variable containing the API key (never pass the key itself on the command line)")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--max-tokens", type=int, default=5000)
    parser.add_argument("--temperature", type=float, default=0.35)


def build_parser() -> argparse.ArgumentParser:
    parser = _StrictArgumentParser(
        prog="kinoquence",
        description="Model-agnostic animated short production toolkit",
    )
    parser.add_argument("--version", action="version", version=f"Kinoquence {__version__}")
    parser.add_argument("--env-file", default=".env", help="Optional dotenv file (default: .env in current directory)")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_StrictArgumentParser)

    doctor = sub.add_parser("doctor", help="Check local rendering prerequisites")

    new = sub.add_parser("new", help="Create a new short-video project")
    new.add_argument("path", type=Path)
    new.add_argument("--title")

    validate = sub.add_parser("validate", help="Validate storyboard and asset attribution")
    validate.add_argument("project", type=Path)

    draft = sub.add_parser("draft", help="Ask a selected model for a new story draft")
    draft.add_argument("project", type=Path)
    draft.add_argument("--topic", required=True)
    draft.add_argument("--style", default="storybook_2_5d")
    _add_provider_args(draft)

    captions = sub.add_parser("captions", help="Export scene captions as SRT")
    captions.add_argument("project", type=Path)
    captions.add_argument("--out", type=Path)

    audio = sub.add_parser("audio", help="Generate an original music bed and per-scene sound effects")
    audio.add_argument("project", type=Path)
    audio.add_argument("--seed", type=int, default=21)

    render = sub.add_parser("render", help="Render a project with Remotion")
    render.add_argument("project", type=Path)
    render.add_argument("--out", type=Path)
    render.add_argument("--concurrency", default="50%")

    qa = sub.add_parser("qa", help="Inspect rendered video for black/frozen frames and audio loudness")
    qa.add_argument("video", type=Path)
    qa.add_argument("--out", type=Path)

    credits = sub.add_parser("credits", help="Generate a credits page from assets.csv")
    credits.add_argument("project", type=Path)

    benchmark = sub.add_parser("benchmark", help="Run a small provider compatibility smoke test")
    _add_provider_args(benchmark)
    benchmark.add_argument("--out-dir", type=Path, default=Path("benchmarks/results"))

    return parser


def _doctor() -> int:
    checks = {name: shutil.which(name) for name in ("python", "node", "npm", "npx", "ffmpeg", "ffprobe", "git")}
    print("Kinoquence local environment check")
    for name, found in checks.items():
        status = "OK" if found else ("OPTIONAL" if name in {"git"} else "MISSING")
        print(f"{status:8} {name:8} {found or 'not found'}")
    remotion = Path(__file__).resolve().parent.parent / "remotion"
    deps = remotion / "node_modules"
    remotion_cli = deps / ".bin" / "remotion"
    remotion_installed = remotion_cli.exists() or (deps / ".bin" / "remotion.cmd").exists()
    print(f"{'OK' if remotion_installed else 'NOT INSTALLED':8} Remotion CLI {remotion_cli}")
    missing = [k for k, v in checks.items() if v is None and k not in {"git"}]
    return 1 if missing or not remotion_installed else 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    load_dotenv(Path(args.env_file))
    try:
        if args.command == "doctor":
            return _doctor()
        if args.command == "new":
            path = create_project(args.path, args.title)
            print(f"Created project: {path}")
            print("Next: kinoquence validate", path)
            return 0
        if args.command == "validate":
            issues, story = validate_project(args.project)
            for issue in issues:
                print(issue)
            errors = sum(issue.severity == "error" for issue in issues)
            warnings = sum(issue.severity == "warning" for issue in issues)
            scenes = story.get("scenes", []) if isinstance(story, dict) else []
            duration = 0.0
            if isinstance(scenes, list):
                for scene in scenes:
                    value = scene.get("duration_seconds") if isinstance(scene, dict) else None
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        try:
                            numeric = float(value)
                        except OverflowError:
                            continue
                        if math.isfinite(numeric) and 0 < numeric <= 60:
                            duration += numeric
            print(f"\n{len(scenes) if isinstance(scenes, list) else 0} scenes · {duration:.1f}s · {errors} errors · {warnings} warnings")
            return 1 if errors else 0
        if args.command == "draft":
            destination, notes = draft_story(args.project, _provider_config(args), args.topic, args.style)
            print(f"Draft saved: {destination}")
            print("It has not replaced story.json. Review it, then copy it into place when approved.")
            for note in notes:
                print(note)
            return 0
        if args.command == "captions":
            print(f"Wrote: {export_captions(args.project, args.out)}")
            return 0
        if args.command == "audio":
            music, sfx = synthesize_project(args.project, seed=args.seed)
            print(f"Music: {music}\nSFX:   {sfx}")
            return 0
        if args.command == "render":
            print(f"Rendered: {render_project(args.project, args.out, args.concurrency)}")
            return 0
        if args.command == "qa":
            report = inspect_video(args.video)
            destination = args.out or args.video.with_suffix(".qa.json")
            write_report(report, destination)
            print(json.dumps(report, indent=2))
            print(f"\nQA report: {destination}")
            return 1 if report.get("warnings") else 0
        if args.command == "credits":
            project_dir = project_story_path(args.project).parent
            notes = audit_assets(project_dir)
            for note in notes:
                print(note)
            print(f"Credits: {write_credits(project_dir)}")
            return 1 if any("ERROR" in note for note in notes) else 0
        if args.command == "benchmark":
            output = run_benchmark(_provider_config(args), args.out_dir)
            print(f"Benchmark smoke test: {output}")
            print("Interpretation: structural/API smoke check only; not a content-quality score.")
            return 0
    except (ValueError, ProviderError, DraftError, QAError, RenderError, OSError, subprocess.SubprocessError) as exc:
        eprint(f"error: {exc}")
        return 2
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
