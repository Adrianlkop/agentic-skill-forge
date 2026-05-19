#!/usr/bin/env python3
"""Create a compact repository tree for repo-to-skill processing.

Outputs:
  <temp>/skill_forge_work/repo_tree.txt
  <temp>/skill_forge_work/metadata.json
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".next",
    ".nuxt",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "venv",
}

DEFAULT_IGNORE_FILES = {
    ".DS_Store",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "Cargo.lock",
}

MANIFEST_NAMES = {
    "README.md",
    "README",
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "settings.gradle",
    "Makefile",
    "justfile",
    "docker-compose.yml",
    "Dockerfile",
    ".github",
    "tsconfig.json",
    "vite.config.ts",
    "next.config.js",
    "next.config.ts",
}


def should_ignore_dir(path: Path) -> bool:
    return path.name in DEFAULT_IGNORE_DIRS or path.name.startswith(".cache")


def should_ignore_file(path: Path) -> bool:
    if path.name in DEFAULT_IGNORE_FILES:
        return True
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip"}:
        return True
    return False


def map_repo(repo_path: Path, max_files: int) -> tuple[list[str], dict[str, object]]:
    repo_path = repo_path.resolve()
    tree_output: list[str] = [f"{repo_path.name}/"]
    file_count = 0
    dir_count = 0
    truncated = False
    manifests: list[str] = []

    for root, dirs, files in os.walk(repo_path):
        root_path = Path(root)
        dirs[:] = sorted(d for d in dirs if not should_ignore_dir(root_path / d))
        files = sorted(f for f in files if not should_ignore_file(root_path / f))

        if root_path != repo_path:
            dir_count += 1
            rel_root = root_path.relative_to(repo_path)
            level = len(rel_root.parts)
            tree_output.append(f"{'    ' * level}{root_path.name}/")

        for file_name in files:
            if file_count >= max_files:
                truncated = True
                continue

            file_path = root_path / file_name
            rel_path = file_path.relative_to(repo_path)
            level = len(rel_path.parts)
            tree_output.append(f"{'    ' * level}{file_name}")
            file_count += 1

            if file_name in MANIFEST_NAMES or rel_path.parts[0] == ".github":
                manifests.append(str(rel_path))

    metadata = {
        "repo_path": str(repo_path),
        "repo_name": repo_path.name,
        "files_listed": file_count,
        "directories_listed": dir_count,
        "truncated": truncated,
        "max_files": max_files,
        "manifest_candidates": sorted(set(manifests))[:100],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return tree_output, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Map a repository tree.")
    parser.add_argument("repo_path", help="Path to a local repository")
    parser.add_argument(
        "--out-dir",
        default=os.path.join(tempfile.gettempdir(), "skill_forge_work"),
        help="Output directory for repo_tree.txt and metadata.json",
    )
    parser.add_argument("--max-files", type=int, default=2000, help="Maximum files to list")
    args = parser.parse_args()

    repo_path = Path(args.repo_path)
    if not repo_path.exists() or not repo_path.is_dir():
        print(f"ERROR: repository path is not a directory: {repo_path}")
        return 1

    tree_output, metadata = map_repo(repo_path, args.max_files)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tree_path = out_dir / "repo_tree.txt"
    metadata_path = out_dir / "metadata.json"

    tree_path.write_text("\n".join(tree_output) + "\n", encoding="utf-8")
    metadata["output_dir"] = str(out_dir)
    metadata["repo_tree_path"] = str(tree_path)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"OK: repo map saved for {repo_path.resolve()}")
    print(f"WORK_DIR={out_dir}")
    print(f"REPO_TREE={tree_path}")
    print(f"METADATA={metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
