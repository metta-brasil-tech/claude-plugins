#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gerador de PDF marca-aware para clientes — Metta / RP Brand Studio.

Um único motor que renderiza qualquer documento de cliente na identidade do
cliente. A MARCA (cores, fontes, logo, header/footer) vive em brands/<marca>/;
o CONTEÚDO vem num JSON de blocos. HTML+CSS -> Chrome headless -> PDF.

Uso:
    python build.py <marca> <content.json> [saida.pdf]

<marca> pode ser:
  - um CAMINHO para a pasta da marca (recomendado): contém brand.json, brand.css,
    assets/, fonts/. É onde o cliente vive no vault. Ex.: "C:/.../clientes/acme".
  - um NOME procurado em <brands-dir>/<nome>, onde <brands-dir> vem da env
    METTA_CLIENTE_PDF_BRANDS ou da pasta atual.

Para um cliente novo: copie a pasta-base _template/ (ao lado deste script) para
onde for guardar o cliente e edite brand.json + assets/ + fonts/.

Schema do conteúdo: ver schema.md. Blocos suportados:
  greeting, section, heading, paragraph, list, keyvalue, table, image,
  callout, divider, spacer.
Inline em qualquer texto: **negrito**, *itálico*.
"""
import sys, os, json, html, subprocess, re

HERE = os.path.dirname(os.path.abspath(__file__))

CHROME_CANDIDATES = [
    r"C:/Program Files/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    r"C:/Program Files/Microsoft/Edge/Application/msedge.exe",
]


def find_chrome():
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
    raise SystemExit("Chrome/Edge nao encontrado — ajuste CHROME_CANDIDATES.")


# ---------- inline text (escape + **bold** + *italic*) ----------
def inline(s):
    s = html.escape(s or "", quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", s)
    return s


# ---------- block renderers ----------
def r_greeting(b):
    out = ['<div class="greet">']
    if b.get("title"):
        out.append(f'<p class="q">{inline(b["title"])}</p>')
    if b.get("text"):
        out.append(f"<p>{inline(b['text'])}</p>")
    out.append("</div>")
    return "".join(out)


def r_heading(b):
    lvl = int(b.get("level", 2))
    lvl = min(max(lvl, 1), 3)
    return f'<h{lvl} class="hd hd{lvl}">{inline(b.get("text",""))}</h{lvl}>'


def r_paragraph(b):
    return f'<p class="p">{inline(b.get("text",""))}</p>'


def _list_items(items):
    """Aceita item como string OU {term, desc}."""
    out = []
    for it in items:
        if isinstance(it, dict):
            term = it.get("term", "")
            desc = it.get("desc", "")
            term_html = f"<b>{inline(term)}:</b> " if term else ""
            out.append(f"{term_html}{inline(desc)}")
        else:
            out.append(inline(str(it)))
    return out


def r_list(b):
    style = b.get("style", "bullet")  # bullet | number | check
    rows = _list_items(b.get("items", []))
    if style == "check":
        lis = "".join(f'<li><span class="cb">[ ]</span>{r}</li>' for r in rows)
        return f'<ul class="lst check">{lis}</ul>'
    if style == "number":
        lis = "".join(f"<li>{r}</li>" for r in rows)
        return f'<ol class="lst num">{lis}</ol>'
    lis = "".join(f"<li>{r}</li>" for r in rows)
    return f'<ul class="lst bullet">{lis}</ul>'


def r_keyvalue(b):
    # alias historico do MIME: lista de {term,desc} com estilo de checklist por padrao
    b = dict(b)
    b.setdefault("style", "check")
    return r_list(b)


def r_table(b):
    heads = b.get("headers", [])
    rows = b.get("rows", [])
    thead = ""
    if heads:
        ths = "".join(f"<th>{inline(str(h))}</th>" for h in heads)
        thead = f"<thead><tr>{ths}</tr></thead>"
    trs = []
    for row in rows:
        tds = "".join(f"<td>{inline(str(c))}</td>" for c in row)
        trs.append(f"<tr>{tds}</tr>")
    return f'<table class="tbl">{thead}<tbody>{"".join(trs)}</tbody></table>'


def r_image(b):
    w = b.get("width", "100%")
    cap = b.get("caption")
    img = f'<img class="img" src="{html.escape(b.get("src",""))}" style="width:{w}">'
    if cap:
        return f'<figure class="fig">{img}<figcaption>{inline(cap)}</figcaption></figure>'
    return f'<div class="figwrap">{img}</div>'


def r_callout(b):
    title = f'<p class="co-t">{inline(b["title"])}</p>' if b.get("title") else ""
    return f'<div class="callout">{title}<p>{inline(b.get("text",""))}</p></div>'


def r_divider(b):
    return '<hr class="rule">'


def r_spacer(b):
    return f'<div class="spacer" style="height:{b.get("size","12pt")}"></div>'


RENDERERS = {
    "greeting": r_greeting,
    "heading": r_heading,
    "paragraph": r_paragraph,
    "list": r_list,
    "keyvalue": r_keyvalue,
    "table": r_table,
    "image": r_image,
    "callout": r_callout,
    "divider": r_divider,
    "spacer": r_spacer,
}


def render_blocks(blocks, auto_number, _counter):
    out = []
    for b in blocks:
        t = b.get("type")
        if t == "section":
            n = ""
            if auto_number:
                _counter[0] += 1
                n = f"{_counter[0]}. "
            title = inline(b.get("title", ""))
            inner = render_blocks(b.get("blocks") or b.get("items_as_list") or [],
                                  False, _counter)
            # compat MIME: section com "items" [{term,desc}] vira checklist
            if not inner and b.get("items"):
                inner = r_list({"style": b.get("style", "check"), "items": b["items"]})
            out.append(f'<section class="sec"><h2 class="sec-h">{n}{title}</h2>{inner}</section>')
        else:
            fn = RENDERERS.get(t)
            if fn:
                out.append(fn(b))
            else:
                out.append(f"<!-- bloco desconhecido: {html.escape(str(t))} -->")
    return "".join(out)


# ---------- brand -> CSS + chrome ----------
def build_css(brand, base_css, brand_css):
    c = brand.get("colors", {})
    fonts = brand.get("fonts", {})
    page = brand.get("page", {})

    faces = []
    fam = {}
    for role, f in fonts.items():
        family = f.get("family", f"Brand-{role}")
        fam[role] = family
        if f.get("file"):
            faces.append(
                f"@font-face{{font-family:'{family}';"
                f"src:url('{f['file']}') format('truetype');"
                f"font-weight:{f.get('weight','400')};font-style:normal;font-display:block;}}"
            )

    root = ":root{{{}}}".format("".join(
        f"--{k}:{v};" for k, v in {
            "color-primary": c.get("primary", "#111"),
            "color-accent": c.get("accent", c.get("primary", "#111")),
            "color-text": c.get("text", "#1a1a1a"),
            "color-heading": c.get("heading", c.get("primary", "#111")),
            "color-muted": c.get("muted", "#6b7280"),
            "color-rule": c.get("rule", "#e5e7eb"),
            "font-display": fam.get("display", "system-ui"),
            "font-body": fam.get("body", fam.get("display", "system-ui")),
            "page-size": page.get("size", "A4"),
            "margin-x": page.get("margin_x", "28pt"),
        }.items()
    ))
    return "\n".join(faces) + "\n" + root + "\n" + base_css + "\n" + brand_css


def build_header(brand, title):
    h = brand.get("header", {})
    htype = h.get("type", "solid")
    if htype == "none":
        return ""
    style = []
    if htype == "gradient":
        style.append(f"background:{h.get('background','')}")
    elif htype == "image":
        style.append(f"background:url('{h.get('image','')}') center/cover no-repeat")
    else:  # solid
        style.append(f"background:{h.get('background', 'var(--color-primary)')}")
    style.append(f"height:{h.get('height','74pt')}")
    logo = ""
    if h.get("logo"):
        logo = f'<img class="logo" src="{h["logo"]}" style="height:{h.get("logo_height","34pt")}" alt="">'
    tcolor = h.get("title_color", "#fff")
    tsize = h.get("title_size", "27pt")
    title_html = ""
    if title:
        title_html = (f'<h1 class="title" style="color:{tcolor};font-size:{tsize}">'
                      f"{inline(title)}</h1>")
    return (f'<div class="hdr" style="{";".join(style)}">{title_html}{logo}</div>'
            f'<div class="head-gap"></div>')


def build_footer(brand):
    f = brand.get("footer", {})
    ftype = f.get("type", "none")
    if ftype == "none":
        return ""
    if ftype == "image":
        return f'<div class="foot-gap"></div><div class="ft"><img src="{f.get("image","")}" alt=""></div>'
    if ftype == "text":
        return f'<div class="foot-gap"></div><div class="ft-txt">{inline(f.get("text",""))}</div>'
    return ""


def resolve_brand_dir(brand_arg):
    """Resolve <marca>: caminho de pasta OU nome em <brands-dir>/<nome>."""
    # 1) caminho direto para a pasta da marca
    if os.path.isdir(brand_arg):
        return os.path.abspath(brand_arg)
    # 2) nome procurado na brands-dir (env) ou na pasta atual
    base = os.environ.get("METTA_CLIENTE_PDF_BRANDS", os.getcwd())
    cand = os.path.join(base, brand_arg)
    if os.path.isdir(cand):
        return cand
    # 3) fallback: nome dentro do plugin (ex.: _template)
    return os.path.join(HERE, brand_arg)


def main():
    if len(sys.argv) < 3:
        raise SystemExit("uso: python build.py <marca> <content.json> [saida.pdf]")
    brand_arg = sys.argv[1]
    content_path = os.path.abspath(sys.argv[2])
    default_name = os.path.splitext(os.path.basename(brand_arg.rstrip("/\\")))[0]
    out_pdf = os.path.abspath(sys.argv[3] if len(sys.argv) > 3 else f"{default_name}.pdf")

    brand_dir = resolve_brand_dir(brand_arg)
    if not os.path.isfile(os.path.join(brand_dir, "brand.json")):
        raise SystemExit(
            f"marca nao encontrada: '{brand_arg}'.\n"
            f"Passe o CAMINHO da pasta da marca (com brand.json) ou um NOME em "
            f"METTA_CLIENTE_PDF_BRANDS / pasta atual.\n"
            f"Cliente novo: copie '{os.path.join(HERE, '_template')}' e edite brand.json.")

    with open(os.path.join(brand_dir, "brand.json"), encoding="utf-8") as f:
        brand = json.load(f)
    with open(os.path.join(HERE, "base.css"), encoding="utf-8") as f:
        base_css = f.read()
    brand_css_path = os.path.join(brand_dir, "brand.css")
    brand_css = ""
    if os.path.exists(brand_css_path):
        with open(brand_css_path, encoding="utf-8") as f:
            brand_css = f.read()
    with open(content_path, encoding="utf-8") as f:
        data = json.load(f)

    css = build_css(brand, base_css, brand_css)
    title = data.get("title", "")
    body = render_blocks(data.get("blocks", []),
                         data.get("auto_number_sections", False), [0])

    doc = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<style>{css}</style><title>{inline(title)}</title></head>
<body>
<table class="layout">
<thead><tr><td>{build_header(brand, title)}</td></tr></thead>
<tfoot><tr><td>{build_footer(brand)}</td></tr></tfoot>
<tbody><tr><td><div class="content">{body}</div></td></tr></tbody>
</table>
</body></html>"""

    # _render.html vai DENTRO da pasta da marca para resolver assets/ e fonts/
    tmp_html = os.path.join(brand_dir, "_render.html")
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(doc)

    chrome = find_chrome()
    subprocess.run([
        chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer", "--virtual-time-budget=10000",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={out_pdf}",
        "file:///" + tmp_html.replace("\\", "/"),
    ], check=True, capture_output=True)
    print("PDF gerado:", out_pdf)


if __name__ == "__main__":
    main()
