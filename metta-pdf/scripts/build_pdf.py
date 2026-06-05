"""
build_pdf.py — CLI unificado do pipeline metta-pdf.

Orquestra parse → layout → suggest → generate → render em 1 comando.
A skill /criar-pdf-metta pode chamar este script direto ao invés de coordenar 4
scripts separados.

Uso básico:
  python build_pdf.py <brief.docx> --setor="loja de posto"

Variantes:
  python build_pdf.py brief.docx --skip-images           # Sprint 1 mode (sem imagens AI)
  python build_pdf.py brief.docx --output ./out          # output dir custom
  python build_pdf.py brief.docx --workers 1             # 1 worker (mais lento, mais reliable)
  python build_pdf.py brief.docx --title "Meu Documento" --meta "01 · Subtítulo"
  python build_pdf.py brief.docx --dry-run               # só mostra mapping + pontos, não gera

Output esperado em <output>/<slug>/:
  <slug>.pdf
  <slug>.html
  img/*.jpeg
  report.json   (log estruturado da execução)
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any

# UTF-8 stdout
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from parse_brief import parse  # noqa: E402
from select_layout import classify_sections, summary as layout_summary  # noqa: E402
from suggest_images import suggest, summary as image_summary  # noqa: E402
from render_html import render  # noqa: E402
from render_pdf import render as render_pdf  # noqa: E402


def _slugify(s: str, max_len: int = 50) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:max_len] or "documento"


def _print_header(text: str) -> None:
    print()
    print(f"━━━ {text} " + "━" * max(0, 70 - len(text)))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="metta-pdf · gera PDF institucional editorial Metta",
        epilog="Plugin: metta-brasil-tech/claude-plugins/metta-pdf",
    )
    parser.add_argument("brief", help="Caminho do DOCX ou MD com o conteúdo")
    parser.add_argument("--output", "-o", default=None, help="Pasta de output (default: ./output/<slug>)")
    parser.add_argument("--setor", default="a Brazilian workplace setting",
                        help="Contexto do setor pras imagens (ex: 'loja de posto de combustível')")
    parser.add_argument("--title", default=None, help="Título do doc (override do nome do brief)")
    parser.add_argument("--meta", default=None, help="Texto do header das páginas internas (ex: '02 · Visualize o Cenário')")
    parser.add_argument("--module-label", default=None, help="Eyebrow da capa (ex: 'Módulo 02 · Treinamento')")
    parser.add_argument("--section-label", default=None, help="Eyebrow estático das seções content-only (ex: 'Ângulo de Copy'). Default: 'Fundamento N'")
    parser.add_argument("--footer-left", default="Metta · Inteligência Comercial")
    parser.add_argument("--skip-images", action="store_true", help="Pula geração de imagens (Sprint 1 mode com placeholders)")
    parser.add_argument("--workers", type=int, default=2, help="Workers paralelos pra nano-banana (default 2)")
    parser.add_argument("--dry-run", action="store_true", help="Só imprime mapping + pontos sugeridos, não gera nada")
    parser.add_argument("--quiet", action="store_true", help="Menos verbose")
    args = parser.parse_args()

    brief_path = Path(args.brief)
    if not brief_path.exists():
        print(f"ERRO: brief não encontrado: {brief_path}", file=sys.stderr)
        return 2

    # Define slug + output dir
    title = args.title or brief_path.stem
    slug = _slugify(title)
    output_dir = Path(args.output) if args.output else Path("output") / slug
    output_dir.mkdir(parents=True, exist_ok=True)
    img_dir = output_dir / "img"
    img_dir.mkdir(exist_ok=True)

    # Defaults derivados
    meta_text = args.meta or title
    module_label = args.module_label or title.upper()

    start = time.time()
    report: dict[str, Any] = {
        "brief": str(brief_path),
        "title": title,
        "slug": slug,
        "output_dir": str(output_dir),
        "skip_images": args.skip_images,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    # ----- 1. Parse + classify ----------------------------------------------
    _print_header("1. Parse + layout selection")
    sections = parse(brief_path)
    enriched = classify_sections(sections)
    if not args.quiet:
        print(layout_summary(enriched))
    report["sections_count"] = len(enriched)
    report["layout_map"] = [
        {"i": s["section_index"], "title": s["title"], "layout": s["layout"]} for s in enriched
    ]

    if args.dry_run:
        _print_header("2. Imagens sugeridas (dry-run)")
        if args.skip_images:
            print("  (skip-images: nenhum ponto editorial)")
        else:
            points = suggest(enriched, brief_context={"setor": args.setor})
            print(image_summary(points))
            report["image_suggestions"] = [
                {"section": p["section_title"], "layout": p["layout"], "filename": p["filename"]}
                for p in points
            ]
        (output_dir / "dry-run-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print()
        print(f"Dry-run salvo em {output_dir/'dry-run-report.json'}")
        return 0

    # ----- 2. Suggest + generate images -------------------------------------
    image_map: dict[str, dict[str, Any]] = {}
    if args.skip_images:
        _print_header("2. Imagens: SKIPPED (--skip-images)")
        print("  PDF terá placeholders [imagem] nos slots.")
    else:
        from generate_images import generate_all, image_map_from_results

        _print_header("2. Sugerindo pontos editoriais")
        points = suggest(enriched, brief_context={"setor": args.setor})
        if not args.quiet:
            print(image_summary(points))
        report["image_suggestions"] = [
            {"section": p["section_title"], "layout": p["layout"], "filename": p["filename"]}
            for p in points
        ]

        _print_header(f"3. Gerando {len(points)} imagens (workers={args.workers})")
        results = generate_all(points, output_dir=img_dir, max_workers=args.workers, verbose=True)
        image_map = image_map_from_results(results)

        ok_count = sum(1 for r in results if r["status"].startswith("ok"))
        fail_count = sum(1 for r in results if r["status"] == "failed")
        report["images_ok"] = ok_count
        report["images_failed"] = fail_count
        report["image_results"] = [
            {"section": r["section_title"], "layout": r["layout"],
             "status": r["status"], "filename": r["filename"]}
            for r in results
        ]

    # ----- 3. Render HTML ---------------------------------------------------
    _print_header("4. Renderizando HTML")
    html = render(
        enriched,
        doc_title=title,
        meta_text=meta_text,
        module_label=module_label,
        footer_left=args.footer_left,
        image_map=image_map,
        section_label=args.section_label,
    )
    html_path = output_dir / f"{slug}.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"  HTML: {html_path} ({len(html):,} bytes)")
    report["html_path"] = str(html_path)
    report["html_size"] = len(html)

    # ----- 4. Render PDF ----------------------------------------------------
    _print_header("5. Renderizando PDF (Chrome headless)")
    pdf_path = output_dir / f"{slug}.pdf"
    render_pdf(html_path, pdf_path)
    pdf_size = pdf_path.stat().st_size
    print(f"  PDF:  {pdf_path} ({pdf_size:,} bytes)")
    report["pdf_path"] = str(pdf_path)
    report["pdf_size"] = pdf_size

    # ----- Final ------------------------------------------------------------
    elapsed = time.time() - start
    report["elapsed_seconds"] = round(elapsed, 1)
    report["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    (output_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    _print_header(f"Pronto em {elapsed:.1f}s")
    print(f"  Output: {output_dir}/")
    print(f"  PDF:    {pdf_path.name}")
    print(f"  Report: report.json")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
