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

def _render_inline_md(text: str) -> str:
    """Converte sintaxe markdown inline pra HTML.

    Suporta: **bold**, *italic*, `code`, [text](url).
    A ordem importa — code primeiro (preserva conteúdo literal), depois links,
    depois bold/italic.
    """
    if not text:
        return text
    # 1. Inline code primeiro (preserva conteúdo, NÃO processa MD dentro)
    placeholders: list[str] = []
    def _code_repl(m: re.Match) -> str:
        idx = len(placeholders)
        placeholders.append(f'<code class="inline">{m.group(1)}</code>')
        return f"\x00CODE{idx}\x00"
    text = re.sub(r"`([^`]+)`", _code_repl, text)

    # 2. Links: [text](url)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2">\1</a>',
        text,
    )

    # 3. Bold: **text** (não-greedy)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)

    # 4. Italic: *text* (não-greedy, evita conflito com bold já tratado)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)

    # Restore code placeholders
    for i, code_html in enumerate(placeholders):
        text = text.replace(f"\x00CODE{i}\x00", code_html)

    return text


def _md(text: str) -> str:
    """Alias curto pra inline MD render — usado nos builders."""
    return _render_inline_md(text)


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
# Cover headline split — destaca apenas os "key terms" finais, pula prepositions
# ---------------------------------------------------------------------------

_PREP_ARTICLES = {
    # preposições + artigos PT-BR + EN simples
    "no", "na", "nos", "nas", "do", "da", "dos", "das",
    "de", "em", "com", "para", "por", "pra", "pro",
    "o", "a", "os", "as", "um", "uma",
    "of", "the", "in", "on", "for", "to", "and",
}


def _split_cover_headline(title: str) -> str:
    """Quebra o título em (não-accent) + (accent yellow).

    Heurística: pega os 1-2 últimos words como accent, parando ao encontrar
    preposição ou artigo. Limita accent a 2 words pra punch visual.
    """
    title = title.strip()
    if not title:
        return ""
    words = title.split()
    if len(words) == 1:
        return f'<span class="accent">{words[0]}</span>'
    if len(words) == 2:
        return f'{words[0]}<br><span class="accent">{words[1]}</span>'

    # Identifica accent_words: trailing words que NÃO são prep/article
    accent_words: list[str] = []
    for w in reversed(words):
        if w.lower().strip(".,!?") in _PREP_ARTICLES:
            break
        accent_words.insert(0, w)

    if not accent_words:
        # Todos os finais são prep? Fallback: última palavra
        accent_words = [words[-1]]

    # Limita accent a 2 palavras pro punch visual
    if len(accent_words) > 2:
        accent_words = accent_words[-2:]

    non_accent_words = words[: len(words) - len(accent_words)]
    accent = " ".join(accent_words)

    # Quebra non-accent em 1 ou 2 linhas dependendo do tamanho
    if len(non_accent_words) == 0:
        return f'<span class="accent">{accent}</span>'

    non_accent_str = " ".join(non_accent_words)
    # Se non-accent é longo (>= 4 words), quebra em 2 linhas pra equilíbrio visual
    if len(non_accent_words) >= 4:
        mid = (len(non_accent_words) + 1) // 2
        line1 = " ".join(non_accent_words[:mid])
        line2 = " ".join(non_accent_words[mid:])
        return f'{line1}<br>{line2}<br><span class="accent">{accent}</span>'

    return f'{non_accent_str}<br><span class="accent">{accent}</span>'


# ---------------------------------------------------------------------------
# Cover mapping
# ---------------------------------------------------------------------------

def _build_cover(sec: dict, ctx: dict) -> dict:
    title = sec["title"]
    h_lines = _split_cover_headline(title)

    paragraphs = _para_text(sec.get("body", []))
    deck = paragraphs[0] if paragraphs else None

    return {
        "doc_title": ctx.get("doc_title", title),
        "eyebrow": ctx.get("module_label", ""),
        "kicker": ctx.get("kicker", ""),
        "headline_lines": h_lines,
        "deck": _md(deck) if deck else None,
        "footer_left": _md(ctx.get("footer_left", "")),
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
    # Pareia list_item com o próximo parágrafo (descrição abaixo do item)
    items_with_desc: list[dict] = []
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

    # Heurística:
    # - exatamente 2 items curtos com descrição = compare cards (estilo "antes/depois")
    # - 3+ items = benefit_list
    # - 1 item = paragraph
    is_compare_candidate = (
        len(items_with_desc) == 2 and
        all(len(it["title"]) <= 40 and it["body"] for it in items_with_desc)
    )
    if is_compare_candidate:
        blocks.append({
            "type": "compare",
            "left": {"eyebrow": "", "title": items_with_desc[0]["title"], "body": items_with_desc[0]["body"]},
            "right": {"eyebrow": "", "title": items_with_desc[1]["title"], "body": items_with_desc[1]["body"]},
        })
    elif len(items_with_desc) >= 2:
        blocks.append({
            "type": "benefit_list",
            "entries": [{"title": it["title"], "body": it.get("body", ""), "icon": "•"} for it in items_with_desc],
        })

    # Aplica inline MD em todos blocks
    for blk in blocks:
        if blk.get("type") == "compare":
            for side in ("left", "right"):
                blk[side]["title"] = _md(blk[side].get("title", ""))
                blk[side]["body"] = _md(blk[side].get("body", ""))
        elif blk.get("type") == "benefit_list":
            for it in blk.get("entries", []):
                it["title"] = _md(it.get("title", ""))
                it["body"] = _md(it.get("body", ""))

    return {
        "doc_title": ctx.get("doc_title", ""),
        "meta": ctx.get("meta_text", ""),
        "eyebrow": "Abertura",
        "title": sec["title"],
        "lede": _md(lede),
        "paragraphs": [_md(p) for p in extra_paragraphs],
        "image": ctx.get("section_image"),
        "image_placeholder": ctx.get("section_image_placeholder", "atendente em ação na loja do posto"),
        "blocks": blocks,
        "closing": _md(paragraphs[-1]) if len(paragraphs) > 3 else "",
        "footer_left": ctx.get("footer_left", ""),
        "page_num": ctx.get("page_num", 0),
    }


# ---------------------------------------------------------------------------
# Content-only mapping
# ---------------------------------------------------------------------------

def _build_content_only(sec: dict, ctx: dict) -> dict:
    """Constrói blocks pra content-only emitindo CADA body item + tables.

    Casos especiais:
      - Tabela com 2 cols + compare table (header antonímico ou body longo)
        → compare block
      - Tabela com 2 cols + N rows (key|val) ou tabela com 3+ cols
        → qtable block (rendered como simple table)
      - Sequência de list_item → benefit_list (mas com paragraphs intercalados
        pareados como "title + body")
      - Bloco code → code block (mono)
      - Callout (blockquote) → callout box
      - Subheading inline (### no MD) → subheading
    """
    body = sec.get("body", [])
    tables = sec.get("tables", [])

    blocks: list[dict] = []
    lede = ""

    # Extrai lede = primeiro parágrafo se houver
    body_iter = list(body)
    for i, entry in enumerate(body_iter):
        if entry.get("type") == "paragraph":
            lede = _md(entry["text"])
            body_iter = body_iter[i + 1:]
            break

    # Helper: detecta sequência de list_items pra agrupar como benefit_list
    def flush_pending_list(pending: list[dict]) -> None:
        if not pending:
            return
        # Se >=2 items, vira benefit_list; se 1, vira paragraph
        if len(pending) >= 2:
            blocks.append({
                "type": "benefit_list",
                "entries": [{"title": _md(it["title"]), "body": _md(it.get("body", "")), "icon": "•"} for it in pending],
            })
        else:
            blocks.append({"type": "paragraph", "body": _md(pending[0]["title"])})

    pending_list: list[dict] = []

    j = 0
    while j < len(body_iter):
        entry = body_iter[j]
        etype = entry.get("type")

        if etype == "list_item":
            # Adiciona ao pending; o próximo paragraph pareia como body se vier
            pending_list.append({"title": entry["text"], "body": ""})
            # Olha o próximo: se for paragraph, é o body do item
            if j + 1 < len(body_iter) and body_iter[j + 1].get("type") == "paragraph":
                pending_list[-1]["body"] = body_iter[j + 1]["text"]
                j += 2
                continue
            j += 1
            continue

        # Não é list_item → flush pending primeiro
        flush_pending_list(pending_list)
        pending_list = []

        if etype == "paragraph":
            blocks.append({"type": "paragraph", "body": _md(entry["text"])})
        elif etype == "subheading":
            blocks.append({"type": "subheading", "text": _md(entry["text"])})
        elif etype == "code":
            # Code blocks ficam RAW (sem inline MD)
            blocks.append({"type": "code", "text": entry["text"]})
        elif etype == "callout":
            blocks.append({"type": "callout", "label": "Importante", "body": _md(entry["text"])})

        j += 1

    # Flush final do pending list
    flush_pending_list(pending_list)

    # Tabelas (após todo o conteúdo do body)
    for t in tables:
        if not t or not t[0]:
            continue
        cols = len(t[0])
        rows = len(t)

        # Compare 2-col, 2-3 rows com header antonímico
        if cols == 2 and rows <= 3:
            blocks.append({
                "type": "compare",
                "left": {"head": _md(t[0][0]), "body": _md(t[1][0]) if rows > 1 else "", "example": _md(t[2][0]) if rows > 2 else ""},
                "right": {"head": _md(t[0][1]), "body": _md(t[1][1]) if rows > 1 else "", "example": _md(t[2][1]) if rows > 2 else ""},
            })
        else:
            # Tabela genérica — emite como simple_table (suportada via template)
            blocks.append({
                "type": "simple_table",
                "header": [_md(c) for c in t[0]],
                "rows": [[_md(c) for c in row] for row in t[1:]],
            })

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
    # Tags só pra list items curtos (<= 30 chars) — labels visuais
    short_items = [t for t in list_items if len(t) <= 30]
    long_items = [t for t in list_items if len(t) > 30]

    if short_items and not long_items:
        # Todos curtos → tags filled
        blocks.append({
            "type": "tags",
            "entries": [{"label": _md(t), "filled": True} for t in short_items],
        })
    elif list_items:
        # Tem items longos (ou mix) → benefit_list ao invés de tags
        blocks.append({
            "type": "benefit_list",
            "entries": [{"title": _md(t), "body": "", "icon": "•"} for t in list_items],
        })

    return {
        "doc_title": ctx.get("doc_title", ""),
        "meta": ctx.get("meta_text", ""),
        "eyebrow": ctx.get("section_eyebrow", "Transição"),
        "title": sec["title"],
        "lede": _md(paragraphs[0]) if paragraphs else "",
        "paragraphs": [_md(p) for p in paragraphs[1:]],
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
