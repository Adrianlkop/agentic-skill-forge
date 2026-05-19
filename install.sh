#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_SKILLS_DIR="$SCRIPT_DIR/skills"
SKILLFORGE_TARGETS="${SKILLFORGE_TARGETS:-claude,codex}"

if [ ! -d "$SOURCE_SKILLS_DIR" ]; then
  echo "ERROR: skills directory not found at $SOURCE_SKILLS_DIR" >&2
  exit 1
fi

install_to_dir() {
  local skills_dir="$1"

  echo "Installing SkillForge skills into $skills_dir"
  mkdir -p "$skills_dir"

  for skill_path in "$SOURCE_SKILLS_DIR"/*; do
    if [ -d "$skill_path" ]; then
      skill_name="$(basename "$skill_path")"
      target_dir="$skills_dir/$skill_name"

      echo "Installing $skill_name"
      rm -rf "$target_dir"
      cp -R "$skill_path" "$target_dir"

      find "$target_dir" -type d -name "__pycache__" -prune -exec rm -rf {} \; 2>/dev/null || true
      find "$target_dir" -type f -name "*.pyc" -delete 2>/dev/null || true

      if [ -d "$target_dir/scripts" ]; then
        find "$target_dir/scripts" -type f -name "*.py" -exec chmod +x {} \; 2>/dev/null || true
      fi
    fi
  done
}

IFS=", " read -r -a targets <<< "$SKILLFORGE_TARGETS"
for target in "${targets[@]}"; do
  case "$target" in
    claude)
      install_to_dir "${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
      ;;
    codex)
      install_to_dir "${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
      ;;
    *)
      echo "ERROR: unknown target '$target'. Use claude, codex, or both comma-separated." >&2
      exit 1
      ;;
  esac
done

echo "Done."
echo "Try:"
echo "  Use docs-to-skill on <url> with optional <slug>"
echo "  Use repo-to-skill on <path> with optional <slug>"
echo "  Use slack-to-skill on <json-file-or-export-dir> with optional <slug>"
