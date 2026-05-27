"""
select_layout.py — heurística pra escolher layout pra cada seção.

Layouts disponíveis (do plugin):
- cover            : primeira seção, título curto, sem corpo significativo
- opener-spread    : segunda seção (abertura) com lede + comparação dual
- content-only     : seções de fundamento (compare block, grid cards, qtable, callout)
- hero-strip       : seções transitórias / introdutórias curtas
- profile-spread   : perfis/personas com atributos + qtable
- quote-photo      : citação direta entre aspas longa

Output: lista parallel ao input com layout + structured_data já mapeado.

Uso:
    from select_layout import classify_sections
    enriched = classify_sections(sections)
"""
from __future__ import annotations

import re
from typing import Any


def _is_quote(text: str) -> bool:
    """Detecta citações longas entre aspas duplas ou simples."""
    if len(text) < 30:
        return False
    quote_pat = re.search(r"[\"“”](.{20,})[\"“”]", text)
    return bool(quote_pat)


def _looks_like_profile(title: str, body: list[dict]) -> bool:
    """Perfis tipicamente começam com 'Perfil N:' ou 'Persona N:' (numerado)."""
    t = title.lower().strip()
    # Match "Perfil 1:", "Perfil 1 -", "Persona 2 —", etc.
    return bool(re.match(r"^(perfil|persona)\s+\d+\b", t))


def _has_questions_table(tables: list[list[list[str]]]) -> bool:
    """Tabela de perguntas (key→val tipo 'O quê? | descrição') tem 6 linhas × 2 cols."""
    if not tables:
        return False
    t = tables[0]
    return len(t) >= 4 and all(len(row) == 2 for row in t)


def _has_compare_table(tables: list[list[list[str]]]) -> bool:
    """Tabela compare tem header + N linhas × 2 cols com texto longo nos dois lados.

    Heurística melhorada: 2 cols + 2-4 rows + header com palavras antonímicas OU
    body com texto longo (>40 chars) em ambas colunas.
    """
    if not tables:
        return False
    t = tables[0]
    if len(t) < 2 or len(t[0]) != 2:
        return False
    if len(t) > 4:
        return False  # Provavelmente qtable (6 linhas), não compare
    # Header tem palavras antonímicas
    h = " ".join(t[0]).lower()
    antonym_pairs = [
        ("fechada", "aberta"), ("antes", "depois"),
        ("ruim", "bom"), ("certo", "errado"),
        ("convencional", "novo"), ("velho", "novo"),
        ("manual", "automatico"),
    ]
    if any(a in h and b in h for a, b in antonym_pairs):
        return True
    # Header tem palavras distintas (não chave-valor curtas) e body tem texto longo nas 2 colunas
    if any(len(row[0]) > 40 and len(row[1]) > 40 for row in t[1:]):
        return True
    return False


def classify_sections(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Atribui layout + flags pra cada seção."""
    enriched: list[dict[str, Any]] = []
    n = len(sections)

    for i, sec in enumerate(sections):
        title = sec["title"]
        body = sec.get("body", [])
        tables = sec.get("tables", [])

        layout = "content-only"  # default
        reason = []

        # Rule 1: primeira seção = cover
        if i == 0:
            layout = "cover"
            reason.append("first section")

        # Rule 2: perfis = profile-spread
        elif _looks_like_profile(title, body):
            layout = "profile-spread"
            reason.append("title indicates profile")

        # Rule 3: tem citação longa em parágrafos = quote-photo
        elif any(_is_quote(p.get("text", "")) for p in body if p.get("type") == "paragraph"):
            layout = "quote-photo"
            reason.append("contains long quote")

        # Rule 4: seção curta com poucos parágrafos + sem tabela = hero-strip
        elif len(body) <= 4 and not tables and i > 0 and i < n - 1:
            layout = "hero-strip"
            reason.append("transitional short section")

        # Rule 5a: seção com tabela compare → content-only (compare block dedicado)
        elif _has_compare_table(tables):
            layout = "content-only"
            reason.append("has compare table")

        # Rule 5b: segunda seção com muitos parágrafos SEM tabela compare = opener-spread
        elif i == 1 and len(body) >= 5 and not tables:
            layout = "opener-spread"
            reason.append("opener (second section with lots of body, no table)")

        # Default: content-only (compare block, grid cards, qtable, etc.)
        else:
            reason.append("default content")

        enriched.append({
            **sec,
            "layout": layout,
            "layout_reason": "; ".join(reason),
            "section_index": i,
        })

    return enriched


def summary(enriched: list[dict[str, Any]]) -> str:
    """Pretty-print pra confirmação com o user."""
    lines = []
    for sec in enriched:
        lines.append(
            f"{sec['section_index'] + 1}. {sec['title'][:55]:<55}  →  {sec['layout']}  ({sec['layout_reason']})"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    from parse_brief import parse

    if len(sys.argv) < 2:
        print("Usage: select_layout.py <brief.docx|brief.md>")
        sys.exit(1)

    secs = parse(sys.argv[1])
    enriched = classify_sections(secs)
    print(summary(enriched))
