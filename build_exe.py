"""Build the Windows executable with PyInstaller."""

import argparse
import os
from pathlib import Path


HIDDEN_IMPORTS = [
    "game.story.chapter1",
    "game.story.chapter2",
    "game.story.chapter3",
    "game.story.chapter4",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Build 绝夜之旅 as a single-file executable.")
    parser.add_argument("--name", default="绝夜之旅", help="Output executable name.")
    parser.add_argument("--console", action="store_true", help="Keep a console window for diagnostics.")
    parser.add_argument("--no-clean", action="store_true", help="Reuse PyInstaller's build cache.")
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        from PyInstaller.__main__ import run
    except ImportError as exc:
        raise SystemExit(
            "PyInstaller is not installed. Run: python -m pip install pyinstaller"
        ) from exc

    project_dir = Path(__file__).resolve().parent
    command = [
        str(project_dir / "main.py"),
        "--onefile",
        "--name", args.name,
        "--distpath", str(project_dir / "dist"),
        "--workpath", str(project_dir / "build"),
        "--specpath", str(project_dir),
        "--add-data", f"{project_dir / 'game'}{os.pathsep}game",
        "--icon", str(project_dir / "game" / "assets" / "app_icon.ico"),
    ]
    if not args.console:
        command.append("--noconsole")
    if not args.no_clean:
        command.append("--clean")
    for module in HIDDEN_IMPORTS:
        command.extend(["--hidden-import", module])

    run(command)


if __name__ == "__main__":
    main()
