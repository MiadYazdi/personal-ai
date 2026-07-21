#!/usr/bin/env python3
"""Apply Personal AI folder/file icons to Nautilus using portable project assets."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = PROJECT_ROOT / "assets/icons/project-theme"
ROOT_ICON = PROJECT_ROOT / "assets/icons/personal-ai-folder.svg"

EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".idea",
    ".vscode",
    ".venv",
    "node_modules",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".rsync-partial",
}

TOP_LEVEL_FOLDER_ICONS = {
    "apps": ICON_DIR / "folder-app.svg",
    "assets": ICON_DIR / "folder-assets.svg",
    "data": ICON_DIR / "folder-data.svg",
    "docs": ICON_DIR / "folder-docs.svg",
    "models": ICON_DIR / "folder-models.svg",
    "requirements": ICON_DIR / "folder-packages.svg",
    "scripts": ICON_DIR / "folder-scripts.svg",
    "src": ICON_DIR / "folder-code.svg",
    "tests": ICON_DIR / "folder-tests.svg",
}

FILE_ICON_MAP = {
    ".py": ICON_DIR / "file-python.svg",
    ".ts": ICON_DIR / "file-react.svg",
    ".tsx": ICON_DIR / "file-react.svg",
    ".md": ICON_DIR / "file-markdown.svg",
    ".json": ICON_DIR / "file-config.svg",
    ".svg": ICON_DIR / "file-svg.svg",
    ".gguf": ICON_DIR / "file-model.svg",
    ".desktop": ICON_DIR / "file-run.svg",
}


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIRECTORY_NAMES for part in path.parts)


def icon_uri(icon_path: Path) -> str:
    return icon_path.resolve().as_uri()


def apply_gio_icon(target: Path, icon_path: Path, dry_run: bool) -> bool:
    if dry_run:
        print(f"DRY-RUN gio icon: {target} -> {icon_path.name}")
        return True

    result = subprocess.run(
        [
            "gio",
            "set",
            "-t",
            "string",
            str(target),
            "metadata::custom-icon",
            icon_uri(icon_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"ERROR gio icon: {target}: {result.stderr.strip()}")
        return False

    return True


def write_directory_fallback(folder: Path, icon_path: Path, dry_run: bool) -> bool:
    directory_file = folder / ".directory"
    content = (
        "[Desktop Entry]\n"
        f"Icon={icon_path.resolve()}\n"
        "Type=Directory\n"
    )

    if dry_run:
        print(f"DRY-RUN .directory: {directory_file}")
        return True

    directory_file.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned icon changes without applying metadata.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print each file icon assignment.",
    )
    args = parser.parse_args()

    if not ROOT_ICON.is_file():
        print(f"ERROR: Missing root icon: {ROOT_ICON}")
        return 1

    if not ICON_DIR.is_dir():
        print(f"ERROR: Missing icon directory: {ICON_DIR}")
        return 1

    applied = 0
    failed = 0

    folders = [PROJECT_ROOT]
    folders.extend(
        path
        for path in PROJECT_ROOT.rglob("*")
        if path.is_dir() and not is_excluded(path)
    )

    for folder in folders:
        if folder == PROJECT_ROOT:
            icon = ROOT_ICON
        else:
            relative = folder.relative_to(PROJECT_ROOT)
            category = relative.parts[0]
            icon = TOP_LEVEL_FOLDER_ICONS.get(
                category,
                ICON_DIR / "folder-code.svg",
            )

        if icon.is_file():
            if apply_gio_icon(folder, icon, args.dry_run):
                write_directory_fallback(folder, icon, args.dry_run)
                applied += 1
            else:
                failed += 1

    for path in PROJECT_ROOT.rglob("*"):
        if is_excluded(path) or path.name == ".directory":
            continue

        if path.is_file():
            icon = FILE_ICON_MAP.get(path.suffix.lower())

            if icon and icon.is_file():
                if args.verbose or args.dry_run:
                    print(f"File icon: {path.relative_to(PROJECT_ROOT)} -> {icon.name}")

                if apply_gio_icon(path, icon, args.dry_run):
                    applied += 1
                else:
                    failed += 1

    print(f"Icon targets processed: {applied}")
    print(f"Icon targets failed: {failed}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
