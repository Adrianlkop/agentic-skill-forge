#!/usr/bin/env python3
"""Extract readable text from a public documentation page.

Outputs:
  <temp>/skill_forge_work/raw_docs.md
  <temp>/skill_forge_work/metadata.json
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path


BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "dd",
    "details",
    "div",
    "dl",
    "dt",
    "figcaption",
    "figure",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "td",
    "th",
    "tr",
    "ul",
}


class DocumentationHTMLParser(HTMLParser):
    """Small stdlib HTML-to-text parser tuned for documentation pages."""

    HIDDEN_TAGS = {"aside", "footer", "header", "nav", "noscript", "script", "style", "svg", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.title_parts: list[str] = []
        self.links: list[dict[str, str]] = []
        self._hidden_depth = 0
        self._in_title = False
        self._link_href: str | None = None
        self._link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_map = {name.lower(): value for name, value in attrs if value is not None}

        if tag in self.HIDDEN_TAGS:
            self._hidden_depth += 1
            return

        if tag == "title":
            self._in_title = True

        if self._hidden_depth:
            return

        if tag in BLOCK_TAGS:
            self.parts.append("\n")

        if tag == "a" and attr_map.get("href"):
            self._link_href = attr_map["href"]
            self._link_text = []

        if tag == "code":
            self.parts.append("`")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if tag in self.HIDDEN_TAGS and self._hidden_depth:
            self._hidden_depth -= 1
            return

        if tag == "title":
            self._in_title = False

        if self._hidden_depth:
            return

        if tag == "code":
            self.parts.append("`")

        if tag == "a" and self._link_href:
            text = normalize_space(" ".join(self._link_text))
            if text:
                self.links.append({"text": text[:120], "href": self._link_href})
            self._link_href = None
            self._link_text = []

        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)

        if self._hidden_depth:
            return

        if data.strip():
            self.parts.append(data)
            if self._link_href:
                self._link_text.append(data)

    @property
    def title(self) -> str:
        return normalize_space(" ".join(self.title_parts))

    @property
    def text(self) -> str:
        raw = html.unescape("".join(self.parts))
        lines = [normalize_space(line) for line in raw.splitlines()]
        compact_lines = [line for line in lines if line]
        return "\n\n".join(compact_lines)


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def validate_url(url: str) -> urllib.parse.ParseResult:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must start with http:// or https://")
    return parsed


def fetch(url: str, timeout: int) -> tuple[str, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "SkillForge/1.0",
            "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.8",
        },
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("content-type", "")
        charset = response.headers.get_content_charset() or "utf-8"
        body = response.read()

    text = body.decode(charset, errors="replace")
    return text, content_type


def write_outputs(url: str, html_text: str, content_type: str, out_dir: Path) -> None:
    parser = DocumentationHTMLParser()
    parser.feed(html_text)

    text = parser.text
    title = parser.title or urllib.parse.urlparse(url).netloc
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_docs_path = out_dir / "raw_docs.md"
    metadata_path = out_dir / "metadata.json"

    raw_docs_path.write_text(
        f"# Source: {url}\n\n"
        f"Title: {title}\n"
        f"Fetched: {datetime.now(timezone.utc).isoformat()}\n"
        f"Content-Type: {content_type or 'unknown'}\n\n"
        "## Extracted Text\n\n"
        f"{text}\n",
        encoding="utf-8",
    )

    same_host_links = []
    parsed_url = urllib.parse.urlparse(url)
    for link in parser.links:
        absolute = urllib.parse.urljoin(url, link["href"])
        if urllib.parse.urlparse(absolute).netloc == parsed_url.netloc:
            same_host_links.append({"text": link["text"], "href": absolute})

    metadata = {
        "source_url": url,
        "title": title,
        "content_type": content_type,
        "output_dir": str(out_dir),
        "raw_docs_path": str(raw_docs_path),
        "word_count": len(text.split()),
        "char_count": len(text),
        "same_host_links_sample": same_host_links[:50],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"OK: scraped {url}")
    print(f"WORK_DIR={out_dir}")
    print(f"RAW_DOCS={raw_docs_path}")
    print(f"METADATA={metadata_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape readable text from a docs page.")
    parser.add_argument("url", help="http:// or https:// documentation URL")
    parser.add_argument(
        "--out-dir",
        default=os.path.join(tempfile.gettempdir(), "skill_forge_work"),
        help="Output directory for raw_docs.md and metadata.json",
    )
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds")
    args = parser.parse_args()

    try:
        validate_url(args.url)
        html_text, content_type = fetch(args.url, args.timeout)
        write_outputs(args.url, html_text, content_type, Path(args.out_dir))
        return 0
    except (ValueError, urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
