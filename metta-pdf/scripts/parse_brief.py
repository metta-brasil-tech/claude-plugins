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
    """Parse a Markdown file into structured sections.

    Lida com:
      - Headings (# / ## / ### / ####)
      - Listas (- / * / 1.)
      - Tabelas (|...|...|)
      - Code blocks (```...```)
      - Blockquotes (>)
      - Horizontal rules (---) → ignorados
      - Subheadings dentro de seções (### vira subheading inline, não nova seção
        se o pai for ##; default: cria nova seção)
    """
    import re
    text = Path(path).read_text(encoding="utf-8")
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    def ensure_current() -> dict[str, Any]:
        nonlocal current
        if current is None:
            current = {"title": "Abertura", "level": 1, "body": [], "tables": []}
        return current

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]

        # Code fence
        if line.lstrip().startswith("```"):
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].lstrip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            # i is now on closing ``` or EOF
            i += 1
            sec = ensure_current()
            sec["body"].append({
                "type": "code",
                "text": "\n".join(code_lines).rstrip(),
            })
            continue

        # Horizontal rule
        if re.match(r"^\s*-{3,}\s*$", line) or re.match(r"^\s*={3,}\s*$", line):
            i += 1
            continue

        stripped = line.strip()

        # Heading detection
        if stripped.startswith("# "):
            if current is not None:
                sections.append(current)
            current = {"title": stripped[2:].strip(), "level": 1, "body": [], "tables": []}
            i += 1
            continue
        if stripped.startswith("## "):
            if current is not None:
                sections.append(current)
            current = {"title": stripped[3:].strip(), "level": 2, "body": [], "tables": []}
            i += 1
            continue
        if stripped.startswith("### "):
            # Sub-heading dentro de seção — adiciona como subheading no body
            ensure_current()["body"].append({
                "type": "subheading",
                "text": stripped[4:].strip(),
            })
            i += 1
            continue
        if stripped.startswith("#### "):
            ensure_current()["body"].append({
                "type": "subheading",
                "text": stripped[5:].strip(),
            })
            i += 1
            continue

        # Blockquote
        if stripped.startswith(">"):
            quote_text = stripped[1:].strip()
            # Coleta linhas seguintes do mesmo blockquote
            while i + 1 < len(lines) and lines[i + 1].strip().startswith(">"):
                i += 1
                quote_text += " " + lines[i].strip()[1:].strip()
            ensure_current()["body"].append({
                "type": "callout",
                "text": quote_text,
            })
            i += 1
            continue

        # Unordered list
        if stripped.startswith("- ") or stripped.startswith("* "):
            ensure_current()["body"].append({
                "type": "list_item",
                "text": stripped[2:].strip(),
            })
            i += 1
            continue

        # Ordered list (1. 2. ...)
        if re.match(r"^\d+\.\s", stripped):
            text_content = re.sub(r"^\d+\.\s", "", stripped)
            ensure_current()["body"].append({
                "type": "list_item",
                "text": text_content,
            })
            i += 1
            continue

        # Tables
        if stripped.startswith("|") and "|" in stripped[1:]:
            tbl_rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row_line = lines[i].strip()
                cells = [c.strip() for c in row_line.strip("|").split("|")]
                # Skip alignment row (---)
                if not all(set(c) <= set("-: ") for c in cells):
                    tbl_rows.append(cells)
                i += 1
            ensure_current()["tables"].append(tbl_rows)
            continue

        # Plain paragraph
        if stripped:
            ensure_current()["body"].append({
                "type": "paragraph",
                "text": stripped,
            })
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
