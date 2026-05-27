"""
render_html.py — AST classificado + assets → HTML completo.

Carrega base.html + layouts/*.html via Jinja2, mapeia cada seção pro template
correspondente, concatena no body do base.html.

Uso:
    from render_html import render
    html = render(enriched_sections, doc_title="Visualize o Cenário", meta_text="02 · Visualize o Cenário")
    Path("out.html").write_text(html, encoding="utf-8")
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path
from typing import Any

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PLUGIN_ROOT / "templates"
TOKENS_DIR = PLUGIN_ROOT / "tokens"


def _load_jinja_env():
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=False,
        lstrip_blocks=False,
    )
    return env


# ---------------------------------------------------------------------------
# Per-layout data mapping
# ---------------------------------------------------------------------------

def _para_text(body: list[dict]) -> list[str]:
    return [p["text"] for p in body if p.get("type") == "paragraph"]


def _list_items(body: list[dict]) -> list[str]:
    return [p["text"] for p in body if p.get("type") == "list_item"]


def _split_title_subtitle(title: str) -> tuple[str, str]:
    """Quebra 'Perfil 1: Caminhoneiro Autônomo' em ('Perfil 1', 'Caminhoneiro Autônomo')."""
    if ":" in title:
        prefix, rest = title.split(":", 1)
        return prefix.strip(), rest.strip()
    return "", title.strip()


def _strip_html_safe(s: str) -> str:
    return s


# ---------------------------------------------------------------------------
# Cover mapping
# ---------------------------------------------------------------------------

def _build_cover(sec: dict, ctx: dict) -> dict:
    title = sec["title"]
    # Quebra heuristica em 2 linhas (palavras curtas no topo, palavra-chave embaixo accent)
    words = title.split()
    if len(words) <= 2:
        h_lines = title
    elif len(words) == 3:
        h_lines = f'{words[0]}<br>{words[1]} <span class="accent">{words[2]}</span>'
    else:
        # divide em ~metade
        mid = len(words) // 2
        first = " ".join(words[:mid])
        last_words = words[mid:]
        if len(last_words) >= 2:
            h_lines = f'{first} {last_words[0]}<br><span class="accent">{" ".join(last_words[1:])}</span>'
        else:
            h_lines = f'{first}<br><span class="accent">{last_words[0]}</span>'

    paragraphs = _para_text(sec.get("body", []))
    deck = paragraphs[0] if paragraphs else None

    return {
        "doc_title": ctx.get("doc_title", title),
        "eyebrow": ctx.get("module_label", ""),
        "kicker": ctx.get("kicker", ""),
        "headline_lines": h_lines,
        "deck": deck,
        "footer_left": ctx.get("footer_left", ""),
        "footer_right": ctx.get("footer_right", ""),
        "cover_image": ctx.get("cover_image"),  # path passado em ctx
    }


# ---------------------------------------------------------------------------
# Opener-spread mapping
# ---------------------------------------------------------------------------

def _build_opener(sec: dict, ctx: dict) -> dict:
    body = sec.get("body", [])
    paragraphs = _para_text(body)
    list_items = _list_items(body)

    lede = paragraphs[0] if paragraphs else ""
    extra_paragraphs = paragraphs[1:3]  # próximos 1-2 parágrafos

    blocks = []
    # Se há list items em pares (paragraph→item→paragraph→item), monta compare cards
    # Simpler: se a seção tem N >= 2 list items + parágrafos seguintes, monta benefit_list
    if len(list_items) >= 2:
        # Pareia list_item com o próximo parágrafo (no body original)
        items_with_desc = []
        last_was_li = False
        for entry in body:
            if entry["type"] == "list_item":
                items_with_desc.append({"title": entry["text"], "body": ""})
                last_was_li = True
            elif entry["type"] == "paragraph" and last_was_li and items_with_desc:
                items_with_desc[-1]["body"] = entry["text"]
                last_was_li = False
            else:
                last_was_li = False

        # Os 2 primeiros viram compare cards, o resto vira benefit_list
        if len(items_with_desc) >= 2:
            blocks.append({
                "type": "compare",
                "left": {"eyebrow": "Sem perguntas", "title": items_with_desc[0]["title"], "body": items_with_desc[0]["body"]},
                "right": {"eyebrow": "Vendedor 4.0", "title": items_with_desc[1]["title"], "body": items_with_desc[1]["body"]},
            })

    return {
        "doc_title": ctx.get("doc_title", ""),
        "meta": ctx.get("meta_text", ""),
        "eyebrow": "Abertura",
        "title": sec["title"],
        "lede": lede,
        "paragraphs": extra_paragraphs,
        "image": ctx.get("section_image"),
        "image_placeholder": ctx.get("section_image_placeholder", "atendente em ação na loja do posto"),
        "blocks": blocks,
        "closing": paragraphs[-1] if len(paragraphs) > 3 else "",
        "footer_left": ctx.get("footer_left", ""),
        "page_num": ctx.get("page_num", 0),
    }


# ---------------------------------------------------------------------------
# Content-only mapping
# ---------------------------------------------------------------------------

def _build_content_only(sec: dict, ctx: dict) -> dict:
    body = sec.get("body", [])
    paragraphs = _para_text(body)
    list_items = _list_items(body)
    tables = sec.get("tables", [])

    lede = paragraphs[0] if paragraphs else ""
    blocks = []

    # Se tem tabela 2-col tipo compare (header + body row)
    if tables and len(tables[0]) >= 2 and len(tables[0][0]) == 2:
        t = tables[0]
        # Heurística compare: header + descrição + (opcional) exemplo
        if len(t) >= 2:
            left_head = t[0][0]
            right_head = t[0][1]
            left_body = t[1][0] if len(t) > 1 else ""
            right_body = t[1][1] if len(t) > 1 else ""
            left_ex = t[2][0] if len(t) > 2 else ""
            right_ex = t[2][1] if len(t) > 2 else ""
            blocks.append({
                "type": "compare",
                "left": {"head": left_head, "body": left_body, "example": left_ex},
                "right": {"head": right_head, "body": right_body, "example": right_ex},
            })

    # Se tem >= 4 list items, monta um card grid
    if len(list_items) >= 4:
        cards = []
        # Pareia list_item + próximo parágrafo
        idx = 0
        item_para_pairs = []
        for entry in body:
            if entry["type"] == "list_item":
                item_para_pairs.append({"title": entry["text"], "body": ""})
            elif entry["type"] == "paragraph" and item_para_pairs and item_para_pairs[-1]["body"] == "":
                item_para_pairs[-1]["body"] = entry["text"]

        for i, pair in enumerate(item_para_pairs, 1):
            cards.append({"num": i, "title": pair["title"], "body": pair["body"]})

        if cards:
            blocks.append({"type": "subheading", "text": "Pontos-chave"})
            blocks.append({"type": "card_grid", "cards": cards})

    return {
        "doc_title": ctx.get("doc_title", ""),
        "meta": ctx.get("meta_text", ""),
        "eyebrow": ctx.get("section_eyebrow", "Fundamento"),
        "title": sec["title"],
        "lede": lede,
        "blocks": blocks,
        "closing": "",
        "footer_left": ctx.get("footer_left", ""),
        "page_num": ctx.get("page_num", 0),
    }


# ---------------------------------------------------------------------------
# Hero-strip mapping
# ---------------------------------------------------------------------------

def _build_hero_strip(sec: dict, ctx: dict) -> dict:
    body = sec.get("body", [])
    paragraphs = _para_text(body)
    list_items = _list_items(body)

    blocks = []
    if list_items:
        blocks.append({
            "type": "tags",
            "items": [{"label": t, "filled": True} for t in list_items],
        })
    elif len(paragraphs) >= 3:
        # extrai palavras-chave em destaque dos parágrafos como tags
        pass

    return {
        "doc_title": ctx.get("doc_title", ""),
        "meta": ctx.get("meta_text", ""),
        "eyebrow": ctx.get("section_eyebrow", "Transição"),
        "title": sec["title"],
        "lede": paragraphs[0] if paragraphs else "",
        "paragraphs": paragraphs[1:],
        "image": ctx.get("section_image"),
        "image_placeholder": ctx.get("section_image_placeholder", "leia a cena do posto"),
        "strip_size": "h-sm",
        "blocks": blocks,
        "footer_left": ctx.get("footer_left", ""),
        "page_num": ctx.get("page_num", 0),
    }


# ---------------------------------------------------------------------------
# Profile-spread mapping
# ---------------------------------------------------------------------------

def _build_profile_spread(sec: dict, ctx: dict) -> dict:
    body = sec.get("body", [])
    paragraphs = _para_text(body)
    tables = sec.get("tables", [])

    prefix, name = _split_title_subtitle(sec["title"])
    badge = prefix or "Perfil"

    qtable = []
    if tables and tables[0]:
        for row in tables[0]:
            if len(row) >= 2:
                qtable.append({"key": row[0], "val": row[1]})

    return {
        "doc_title": ctx.get("doc_title", ""),
        "meta": ctx.get("meta_text", ""),
        "eyebrow": ctx.get("section_eyebrow", badge),
        "title": name or sec["title"],
        "description": paragraphs[0] if paragraphs else "",
        "tags": ctx.get("section_tags", []),
        "subheading": "Perguntas-chave",
        "qtable": qtable,
        "image": ctx.get("section_image"),
        "image_placeholder": ctx.get("section_image_placeholder", f"retrato {name}"),
        "callout": ctx.get("section_callout"),
        "footer_left": ctx.get("footer_left", ""),
        "page_num": ctx.get("page_num", 0),
    }


# ---------------------------------------------------------------------------
# Quote-photo mapping
# ---------------------------------------------------------------------------

def _build_quote_photo(sec: dict, ctx: dict) -> dict:
    body = sec.get("body", [])
    paragraphs = _para_text(body)

    lede = paragraphs[0] if paragraphs else ""
    quote = ""
    intro = ""
    for p in paragraphs[1:]:
        if _has_quote_marks(p):
            # remove aspas se presentes
            quote = re.sub(r'^[\"“”\'`]+|[\"“”\'`]+$', "", p).strip()
            break

    if not quote and len(paragraphs) > 1:
        quote = paragraphs[1]  # fallback

    intro = paragraphs[1] if len(paragraphs) > 1 and paragraphs[1] != quote else ""

    blocks = []
    # Equation final se tem "=" ou marcador conclusivo
    closing_p = paragraphs[-1] if paragraphs else ""
    if "=" in closing_p or "✓" in closing_p:
        text = closing_p.replace("✓", "").strip()
        # converte " = " e " + " em spans
        text_html = re.sub(r"\s+=\s+", ' <span class="plus">=</span> ', text)
        text_html = re.sub(r"\s+\+\s+", ' <span class="plus">+</span> ', text_html)
        blocks.append({"type": "equation", "text": text_html})

    return {
        "doc_title": ctx.get("doc_title", ""),
        "meta": ctx.get("meta_text", ""),
        "eyebrow": ctx.get("section_eyebrow", "Permissão"),
        "title": sec["title"],
        "lede": lede,
        "intro": intro,
        "quote": quote,
        "image": ctx.get("section_image"),
        "blocks": blocks,
        "footer_left": ctx.get("footer_left", ""),
        "page_num": ctx.get("page_num", 0),
    }


def _has_quote_marks(text: str) -> bool:
    return bool(re.search(r"[\"“”].{20,}[\"“”]", text))


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

LAYOUT_BUILDERS = {
    "cover": _build_cover,
    "opener-spread": _build_opener,
    "content-only": _build_content_only,
    "hero-strip": _build_hero_strip,
    "profile-spread": _build_profile_spread,
    "quote-photo": _build_quote_photo,
}


def render(
    enriched_sections: list[dict[str, Any]],
    doc_title: str = "",
    meta_text: str = "",
    footer_left: str = "Metta · Inteligência Comercial",
    module_label: str = "",
    image_map: dict[str, dict] | None = None,
) -> str:
    """
    image_map: dict opcional {section_title: {src, alt, badge, caption}} —
               vem do Sprint 2 (sugerir+aprovar) ou pode ser None pra placeholders.
    """
    env = _load_jinja_env()
    base = env.get_template("base.html")

    # Load tokens CSS + logo symbols
    tokens_css = (TOKENS_DIR / "metta-ds.css").read_text(encoding="utf-8")
    logo_symbols = (TOKENS_DIR / "logo-symbols.svg").read_text(encoding="utf-8")

    pages_html = []
    page_num = 0
    for sec in enriched_sections:
        layout = sec["layout"]
        builder = LAYOUT_BUILDERS.get(layout, _build_content_only)

        # Cover não tem page-num footer
        if layout != "cover":
            page_num += 1

        # Per-section image
        section_image = None
        if image_map and sec["title"] in image_map:
            section_image = image_map[sec["title"]]

        ctx = {
            "doc_title": doc_title,
            "meta_text": meta_text,
            "module_label": module_label,
            "footer_left": footer_left,
            "page_num": page_num,
            "section_image": section_image,
            "section_eyebrow": _eyebrow_for(sec),
            "section_tags": _tags_for(sec),
            "cover_image": image_map.get("__cover__", {}).get("src") if image_map else None,
            "kicker": _kicker_for(sec),
            "footer_right": "",
        }
        data = builder(sec, ctx)
        layout_tpl = env.get_template(f"layouts/{layout}.html")
        pages_html.append(layout_tpl.render(**data))

    html = base.render(
        doc_title=doc_title,
        tokens_css=tokens_css,
        logo_symbols=logo_symbols,
        pages=pages_html,
    )
    return html


def _eyebrow_for(sec: dict) -> str:
    idx = sec.get("section_index", 0)
    layout = sec.get("layout", "")
    if layout == "profile-spread":
        prefix, _ = _split_title_subtitle(sec["title"])
        return prefix or f"Perfil {idx}"
    if layout == "opener-spread":
        return "Abertura"
    if layout == "quote-photo":
        return "Permissão"
    if layout == "hero-strip":
        return "Próximo passo"
    return f"Fundamento {idx}"


def _tags_for(sec: dict) -> list[str]:
    """Heurística simples: extrai palavras-chave em destaque dos parágrafos do perfil."""
    if sec.get("layout") != "profile-spread":
        return []
    paragraphs = _para_text(sec.get("body", []))
    text = " ".join(paragraphs)
    # Busca padrões "preocupações: A, B, C"
    m = re.search(r"preocupa[çc]o[ãa]es?:?\s*(.+?)(?:\.|$)", text, re.IGNORECASE)
    if m:
        items = re.split(r"[,;]| e ", m.group(1))
        return [s.strip().capitalize() for s in items if s.strip()][:4]
    return []


def _kicker_for(sec: dict) -> str:
    return ""


if __name__ == "__main__":
    import json
    from parse_brief import parse
    from select_layout import classify_sections

    if len(sys.argv) < 2:
        print("Usage: render_html.py <brief.docx> [out.html]")
        sys.exit(1)

    secs = parse(sys.argv[1])
    enriched = classify_sections(secs)
    html = render(
        enriched,
        doc_title="Visualize o Cenário",
        meta_text="02 · Visualize o Cenário",
        module_label="Módulo 02 · Treinamento",
    )

    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("out.html")
    out.write_text(html, encoding="utf-8")
    print(f"HTML written to {out} ({len(html)} bytes)")
