"""
suggest_images.py — propõe pontos editoriais pra geração de imagens.

Pra cada seção elegível, escolhe o arquétipo de prompt (cover/opener/hero-strip/
profile/quote) e preenche os slots dinâmicos com o contexto da seção.

Output: list[dict] com {section_title, layout, prompt, aspect, size, filename, badge}

Uso:
    from suggest_images import suggest
    points = suggest(enriched_sections, brief_context={"setor": "loja de posto", ...})
"""
from __future__ import annotations

import io
import re
import sys
import unicodedata
from typing import Any

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


# ---------------------------------------------------------------------------
# Slot config per layout
# ---------------------------------------------------------------------------

LAYOUT_SLOT = {
    "cover":           {"aspect": "16:9", "size": "1K"},
    "opener-spread":   {"aspect": "1:1",  "size": "1K"},
    "hero-strip":      {"aspect": "16:9", "size": "1K"},
    "profile-spread":  {"aspect": "4:5",  "size": "1K"},
    "quote-photo":     {"aspect": "16:9", "size": "1K"},
}

# Negative cues universal — concatenado no fim de todo prompt
NEGATIVE_CUES = (
    "Avoid stock photo cliches, fake smiles, plastic-looking skin, "
    "oversaturated colors, text or logos visible, readable brands or signage, "
    "watermarks, illustrations, cartoon style, lifestyle ad gloss, "
    "americana aesthetic, posed corporate model headshot, fluorescent flat lighting."
)


# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------

def _slugify(s: str, max_len: int = 30) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:max_len] or "section"


# ---------------------------------------------------------------------------
# Prompt builders per archetype
# ---------------------------------------------------------------------------

def _prompt_cover(sec: dict, ctx: dict) -> str:
    setor = ctx.get("setor", "the workplace context")
    return (
        f"Wide editorial shot of {setor} at blue hour late afternoon, "
        f"shelves and tools visible, large windows showing the surroundings. "
        f"A professional in their late 30s mid-action, candid and absorbed. "
        f"Compositionally the upper third of the frame is deliberately negative "
        f"space for editorial text overlay. Warm tungsten interior key light "
        f"with cool teal rim light from windows. Editorial documentary "
        f"photography in the style of Bloomberg Businessweek, warm amber and "
        f"teal cinematic color grade, low contrast, premium magazine quality. "
        f"Shot on 24mm f/2.8, deep focus, slight 35mm film grain. " + NEGATIVE_CUES
    )


def _prompt_opener(sec: dict, ctx: dict) -> str:
    setor = ctx.get("setor", "a workplace")
    return (
        f"Editorial medium shot of two people in conversation at {setor}. "
        f"A Brazilian professional in their late 30s leans forward listening "
        f"attentively while the customer mid-gesture explains a need. Soft-focus "
        f"environment with relevant tools and products in the background. Warm "
        f"tungsten light with cool teal rim from natural light source. "
        f"Documentary editorial photography in the style of Bloomberg "
        f"Businessweek, warm amber and teal color grade, low contrast. "
        f"Shot on 35mm f/2.0, both subjects in soft focus, candid moment, "
        f"Kodak Portra 400 film grain. " + NEGATIVE_CUES
    )


def _prompt_hero_strip(sec: dict, ctx: dict) -> str:
    setor = ctx.get("setor", "a workplace")
    title_hint = sec.get("title", "").lower()
    if "visualiz" in title_hint or "ler" in title_hint or "cenar" in title_hint:
        action = "scanning the scene with calm focused attention, reading the room before approaching"
    else:
        action = "in mid-action, thoughtful and engaged"
    return (
        f"Editorial wide shot of {setor} mid-afternoon, multiple people visible "
        f"in soft focus simultaneously (diverse profiles, ages, contexts). In "
        f"sharp focus in the foreground, a Brazilian professional in their "
        f"late 30s pauses, {action}. Warm tungsten ambient light with diffuse "
        f"natural light from windows, creating cinematic depth. Editorial "
        f"documentary photography in the style of Magnum Photos, warm amber "
        f"and teal color grade, low contrast. Shot on 35mm f/2.8, subject in "
        f"focus with background softly blurred, candid frozen moment, slight "
        f"Kodak Portra 400 grain. " + NEGATIVE_CUES
    )


def _prompt_profile(sec: dict, ctx: dict) -> str:
    # Tenta detectar arquétipo do perfil pelo título/descrição
    title = sec.get("title", "").lower()
    body_text = " ".join(
        p.get("text", "") for p in sec.get("body", []) if p.get("type") == "paragraph"
    ).lower()

    is_blue_collar = any(
        k in title or k in body_text
        for k in ("caminhone", "motorista", "tratorist", "operari", "lavrador", "mec[âa]nic")
    )
    is_executive = any(
        k in title or k in body_text for k in ("executivo", "empresari", "diretor", "ceo", "gestor")
    )
    is_fleet = any(
        k in title or k in body_text for k in ("frota", "uniform", "empresa de transport", "logist")
    )

    if is_blue_collar and not is_fleet:
        return (
            f"Editorial medium shot portrait of a Brazilian male professional in "
            f"his early 50s, sun-tanned weathered face with character lines, "
            f"slight gray stubble, wearing a worn but clean cap and a plaid "
            f"cotton work shirt. He stands beside his own vehicle/tool of trade "
            f"(no readable plate or brand), one hand resting affectionately, "
            f"expression calm and dignified with a slight smile, looking off "
            f"to the right of frame. Golden hour warm rim light from camera-right. "
            f"Documentary candid portrait in the style of Magnum Photos, warm "
            f"amber and teal cinematic grade, low contrast. Shot on 50mm f/2.0, "
            f"shallow depth of field, Kodak Portra 400 emulation. " + NEGATIVE_CUES
        )
    if is_fleet:
        return (
            f"Editorial medium shot portrait of a Brazilian male professional in "
            f"his late 30s, methodical posture, wearing a clean navy work polo "
            f"shirt with a small unreadable abstract chest patch and dark cargo "
            f"trousers. He stands beside a large commercial vehicle (no readable "
            f"brand or signage), holding a rugged tablet, concentrated business-"
            f"like expression looking down at the screen. Overcast neutral sky "
            f"with diffuse light, institutional atmosphere. Documentary editorial "
            f"photography in the style of Forbes corporate logistics features, "
            f"warm amber and cool teal color grade, low contrast. Shot on 50mm "
            f"f/2.8, slight 35mm film grain, Kodak Portra 400 feel. " + NEGATIVE_CUES
        )
    if is_executive:
        return (
            f"Editorial medium shot portrait of a Brazilian executive in their "
            f"late 30s, business casual (white dress shirt open collar, charcoal "
            f"trousers), holding a phone or coffee cup, expression focused and "
            f"slightly impatient — a person between meetings. Standing in an "
            f"urban context at midday with diffuse clean light. Editorial "
            f"portraiture in the style of Wall Street Journal Mansion section, "
            f"warm amber and teal color grade, low contrast, magazine quality. "
            f"Shot on 50mm f/2.8, medium depth of field, slight Kodak Portra "
            f"400 grain. " + NEGATIVE_CUES
        )
    # Default genérico
    return (
        f"Editorial medium shot portrait of a Brazilian professional in their "
        f"late 30s to early 50s in their natural work context, candid and "
        f"engaged. Warm rim light, depth of field with subject in razor focus. "
        f"Documentary editorial photography in the style of Brazilian magazine "
        f"Exame, warm amber and teal cinematic grade, low contrast. Shot on "
        f"50mm f/2.0, Kodak Portra 400 emulation. " + NEGATIVE_CUES
    )


def _prompt_quote_photo(sec: dict, ctx: dict) -> str:
    setor = ctx.get("setor", "a workplace")
    return (
        f"Editorial close-up of a respectful moment of connection at {setor}. "
        f"A Brazilian professional in their late 30s leans slightly forward, "
        f"hand resting open on a surface, looking directly with warm attentive "
        f"eye contact — asking permission, listening. Across from them, "
        f"another Brazilian person in their late 40s with relaxed receptive "
        f"body posture, hint of a small genuine nod. Both faces share the "
        f"frame. Warm tungsten light from above with soft golden window light "
        f"from camera-right. Editorial documentary in the style of Wall Street "
        f"Journal portraits, warm amber and teal cinematic grade, low contrast. "
        f"Shot on 50mm f/2.0, both subjects in soft focus on the eyes, candid "
        f"intimate moment, Kodak Portra 400 grain. " + NEGATIVE_CUES
    )


PROMPT_BUILDERS = {
    "cover": _prompt_cover,
    "opener-spread": _prompt_opener,
    "hero-strip": _prompt_hero_strip,
    "profile-spread": _prompt_profile,
    "quote-photo": _prompt_quote_photo,
}


# ---------------------------------------------------------------------------
# Badge / caption helpers
# ---------------------------------------------------------------------------

def _badge_for(sec: dict) -> str:
    layout = sec.get("layout")
    if layout == "profile-spread":
        m = re.match(r"^(perfil|persona)\s+(\d+)", sec.get("title", ""), re.IGNORECASE)
        if m:
            return f"{m.group(2).zfill(2)} · Perfil"
        return "Perfil"
    if layout == "opener-spread":
        return "Em ação"
    if layout == "hero-strip":
        return "Leia a cena"
    return ""


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def suggest(
    enriched_sections: list[dict[str, Any]],
    brief_context: dict[str, Any] | None = None,
    skip_layouts: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Propõe pontos editoriais pra geração de imagens.

    Args:
        enriched_sections: output do select_layout.classify_sections()
        brief_context: dict opcional com {setor, marca, tom} pra contextualizar prompts
        skip_layouts: layouts que devem ser pulados (default: content-only)

    Returns:
        Lista de dicts com {section_index, section_title, layout, prompt,
        aspect, size, filename, badge}
    """
    ctx = brief_context or {}
    skip = skip_layouts or {"content-only"}

    points: list[dict[str, Any]] = []

    for sec in enriched_sections:
        layout = sec.get("layout", "")
        if layout in skip:
            continue

        builder = PROMPT_BUILDERS.get(layout)
        if not builder:
            continue

        prompt = builder(sec, ctx)
        slot = LAYOUT_SLOT.get(layout, {"aspect": "1:1", "size": "1K"})

        # filename baseado em layout + slug do título
        slug = _slugify(sec.get("title", "untitled"))
        if layout == "cover":
            filename = "cover.jpeg"
        else:
            filename = f"{sec.get('section_index', 0):02d}-{layout}-{slug}.jpeg"

        points.append({
            "section_index": sec.get("section_index"),
            "section_title": sec.get("title"),
            "layout": layout,
            "prompt": prompt,
            "aspect": slot["aspect"],
            "size": slot["size"],
            "filename": filename,
            "badge": _badge_for(sec),
        })

    return points


def summary(points: list[dict[str, Any]]) -> str:
    lines = []
    for p in points:
        lines.append(
            f"  • {p['section_title'][:50]:<50}  →  {p['layout']:<16}  "
            f"({p['aspect']} {p['size']})  →  {p['filename']}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    import json
    from parse_brief import parse
    from select_layout import classify_sections

    if len(sys.argv) < 2:
        print("Usage: suggest_images.py <brief.docx|brief.md> [--setor='descrição']")
        sys.exit(1)

    setor = "a Brazilian workplace"
    for arg in sys.argv[2:]:
        if arg.startswith("--setor="):
            setor = arg.split("=", 1)[1]

    secs = parse(sys.argv[1])
    enriched = classify_sections(secs)
    points = suggest(enriched, brief_context={"setor": setor})

    print(f"\n{len(points)} pontos editoriais sugeridos pra geração de imagem:\n")
    print(summary(points))
    print()
    # Pode passar --json pra dump completo
    if "--json" in sys.argv:
        print(json.dumps(points, ensure_ascii=False, indent=2))
