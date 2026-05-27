"""
parse_brief.py — DOCX/MD → AST de seções pro pipeline metta-pdf.

Saída: lista de dicts com {titulo, nivel, body[], tables[], list_items[]}

Uso:
    from parse_brief import parse_docx, parse_markdown
    sections = parse_docx("brief.docx")
"""
from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Any

# Force UTF-8 stdout on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def parse_docx(path: str | Path) -> list[dict[str, Any]]:
    """Parse a DOCX file into structured sections, preserving inline table order."""
    from docx import Document  # type: ignore[import-not-found]
    from docx.oxml.ns import qn  # type: ignore[import-not-found]
    from docx.text.paragraph import Paragraph  # type: ignore[import-not-found]
    from docx.table import Table  # type: ignore[import-not-found]

    doc = Document(str(path))
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    def new_section(title: str, level: int) -> dict[str, Any]:
        return {
            "title": title.strip(),
            "level": level,
            "body": [],
            "tables": [],
        }

    # Walk body children in their actual XML order — preserves table position.
    body = doc.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            p = Paragraph(child, doc)
            style = (p.style.name if p.style else "Normal") or "Normal"
            text = p.text.strip()

            is_heading = style.startswith("Heading")
            is_h1 = style in {"Heading 1", "Title"}
            is_h2 = style == "Heading 2"

            looks_like_title = (
                text and len(text) <= 60 and text == text.upper() and
                not text.endswith(":") and " " in text and style == "Normal"
                and (current is None or len(current["body"]) == 0)
            )

            if is_heading or looks_like_title:
                level = 1 if (is_h1 or looks_like_title) else 2 if is_h2 else 3
                if current is not None:
                    sections.append(current)
                current = new_section(text, level)
                continue

            if current is None:
                current = new_section("Abertura", 1)

            if not text:
                continue

            if style == "List Paragraph":
                current["body"].append({"type": "list_item", "text": text, "style": style})
            else:
                current["body"].append({"type": "paragraph", "text": text, "style": style})

        elif child.tag == qn("w:tbl"):
            tbl = Table(child, doc)
            tbl_rows = [
                [cell.text.strip() for cell in row.cells] for row in tbl.rows
            ]
            if current is None:
                current = new_section("Abertura", 1)
            current["tables"].append(tbl_rows)

    if current is not None:
        sections.append(current)

    return sections


def parse_markdown(path: str | Path) -> list[dict[str, Any]]:
    """Parse a Markdown file into structured sections."""
    text = Path(path).read_text(encoding="utf-8")
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        # Heading detection
        if line.startswith("# "):
            if current is not None:
                sections.append(current)
            current = {"title": line[2:].strip(), "level": 1, "body": [], "tables": []}
        elif line.startswith("## "):
            if current is not None:
                sections.append(current)
            current = {"title": line[3:].strip(), "level": 2, "body": [], "tables": []}
        elif line.startswith("### "):
            if current is not None:
                sections.append(current)
            current = {"title": line[4:].strip(), "level": 3, "body": [], "tables": []}
        elif line.startswith("- ") or line.startswith("* "):
            if current is None:
                current = {"title": "Abertura", "level": 1, "body": [], "tables": []}
            current["body"].append({"type": "list_item", "text": line[2:].strip()})
        elif line.startswith("|") and "|" in line[1:]:
            # Table — collect contiguous lines
            tbl_rows: list[list[str]] = []
            while i < len(lines) and lines[i].startswith("|"):
                row_line = lines[i].strip()
                cells = [c.strip() for c in row_line.strip("|").split("|")]
                # Skip alignment row (---)
                if not all(set(c) <= set("-: ") for c in cells):
                    tbl_rows.append(cells)
                i += 1
            if current is None:
                current = {"title": "Abertura", "level": 1, "body": [], "tables": []}
            current["tables"].append(tbl_rows)
            continue
        elif line.strip():
            if current is None:
                current = {"title": "Abertura", "level": 1, "body": [], "tables": []}
            current["body"].append({"type": "paragraph", "text": line.strip()})
        i += 1

    if current is not None:
        sections.append(current)

    return sections


def parse(path: str | Path) -> list[dict[str, Any]]:
    """Auto-detect format and parse."""
    p = Path(path)
    if p.suffix.lower() == ".docx":
        return parse_docx(p)
    if p.suffix.lower() in (".md", ".markdown"):
        return parse_markdown(p)
    raise ValueError(f"Unsupported file type: {p.suffix}")


if __name__ == "__main__":
    import json
    if len(sys.argv) < 2:
        print("Usage: parse_brief.py <path.docx|path.md>")
        sys.exit(1)
    secs = parse(sys.argv[1])
    print(json.dumps(secs, ensure_ascii=False, indent=2))
