#!/usr/bin/env python3
"""Extract useful text from Slack JSON exports.

Outputs:
  <temp>/skill_forge_work/slack_threads.txt
  <temp>/skill_forge_work/metadata.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SKIP_SUBTYPES = {
    "bot_message",
    "channel_join",
    "channel_leave",
    "message_deleted",
    "message_changed",
}


def discover_json_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob("*.json") if p.is_file())


def load_messages(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))

    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict) and isinstance(data.get("messages"), list):
        return [item for item in data["messages"] if isinstance(item, dict)]
    return []


def clean_slack_text(text: str) -> str:
    text = re.sub(r"<mailto:([^|>]+)(?:\|[^>]+)?>", r"\1", text)
    text = re.sub(r"<(https?://[^|>]+)\|([^>]+)>", r"\2 (\1)", text)
    text = re.sub(r"<(https?://[^>]+)>", r"\1", text)
    text = re.sub(r"<@([A-Z0-9]+)>", r"@\1", text)
    text = re.sub(r"<!subteam\^([A-Z0-9]+)(?:\|[^>]+)?>", r"@\1", text)
    text = re.sub(r"<![^>]+>", "", text)
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    return re.sub(r"[ \t]+", " ", text).strip()


def message_user(message: dict[str, Any]) -> str:
    profile = message.get("user_profile")
    if isinstance(profile, dict):
        for key in ("real_name", "display_name", "name"):
            value = profile.get(key)
            if value:
                return str(value)
    return str(message.get("user") or message.get("username") or "Unknown")


def timestamp_to_iso(ts: str | None) -> str:
    if not ts:
        return "unknown-time"
    try:
        seconds = float(ts)
        return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return str(ts)


def channel_name_for_file(root: Path, file_path: Path) -> str:
    if root.is_file():
        return root.stem
    try:
        rel = file_path.relative_to(root)
        return rel.parts[0] if len(rel.parts) > 1 else root.name
    except ValueError:
        return file_path.parent.name


def extract_messages(source_path: Path) -> tuple[list[str], dict[str, Any]]:
    files = discover_json_files(source_path)
    output: list[str] = []
    messages_seen = 0
    messages_kept = 0
    channels: set[str] = set()

    for file_path in files:
        channel = channel_name_for_file(source_path, file_path)
        channels.add(channel)

        for message in load_messages(file_path):
            messages_seen += 1
            if message.get("subtype") in SKIP_SUBTYPES:
                continue

            text = clean_slack_text(str(message.get("text") or ""))
            if not text:
                continue

            user = message_user(message)
            timestamp = timestamp_to_iso(message.get("ts"))
            thread_ts = message.get("thread_ts")
            thread_marker = ""
            if thread_ts and thread_ts != message.get("ts"):
                thread_marker = f" thread={timestamp_to_iso(thread_ts)}"

            output.append(f"[{channel} {timestamp}{thread_marker} {user}]: {text}")
            messages_kept += 1

    metadata = {
        "source_path": str(source_path.resolve()),
        "json_files_read": len(files),
        "messages_seen": messages_seen,
        "messages_kept": messages_kept,
        "channels": sorted(channels),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return output, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse Slack JSON exports.")
    parser.add_argument("slack_path", help="Slack JSON file or export directory")
    parser.add_argument(
        "--out-dir",
        default=os.path.join(tempfile.gettempdir(), "skill_forge_work"),
        help="Output directory for slack_threads.txt and metadata.json",
    )
    args = parser.parse_args()

    source_path = Path(args.slack_path)
    if not source_path.exists():
        print(f"ERROR: Slack path does not exist: {source_path}")
        return 1

    output, metadata = extract_messages(source_path)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    threads_path = out_dir / "slack_threads.txt"
    metadata_path = out_dir / "metadata.json"

    threads_path.write_text("\n\n".join(output) + ("\n" if output else ""), encoding="utf-8")
    metadata["output_dir"] = str(out_dir)
    metadata["slack_threads_path"] = str(threads_path)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"OK: parsed Slack export {source_path.resolve()}")
    print(f"WORK_DIR={out_dir}")
    print(f"SLACK_THREADS={threads_path}")
    print(f"METADATA={metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
