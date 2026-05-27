---
name: criar-pdf-metta
description: Gera PDF institucional editorial Metta a partir de DOCX/Markdown. Use quando o user pedir pra criar/gerar/montar/produzir documento, treinamento, módulo, manual ou material editorial PDF para a Metta. Aplica design system + 6 layouts canônicos + geração de imagens AI via nano-banana com fluxo sugerir+aprovar. Não usar pra PPTX (use /criar-slide-metta) nem pra ads.
---

# /criar-pdf-metta — Orquestrador

## Quando invocar

User pediu pra criar/gerar/montar PDF institucional Metta a partir de:
- Um arquivo DOCX existente
- Um arquivo Markdown
- Uma descrição em prosa (caso simples — converte em MD primeiro)

Tipicamente:
- Módulos de treinamento (5-15 páginas)
- Manuais operacionais
- Relatórios editoriais
- Apostilas de mentoria

Não usar para:
- Apresentações PPTX → `/criar-slide-metta`
- Ads / posts IG → `/copy-ad` + `/design-metta`
- Landing pages → outros skills

## Fluxo (5 fases)

```
1. INPUT          → user passa DOCX/MD
2. PARSE+LAYOUT   → mostra mapeamento seção→layout, espera aprovação
3. SUGGEST IMG    → propõe pontos editoriais com prompts, espera aprovação
4. GENERATE IMG   → nano-banana CLI em paralelo + retry de timeout
5. RENDER         → HTML via Jinja2 + PDF via Chrome headless
OUTPUT → output/<slug>/<slug>.pdf + .html + img/*.jpeg
```

## Variáveis de ambiente

Antes de tudo, garantir:
- `GEMINI_API_KEY` exportada (pro nano-banana CLI). Sem isso, fase 4 falha.
- Chrome ou Edge instalado.
- Python 3.11+ com `python-docx` + `Jinja2`.

## Passo 1 — Receber o brief

```
User: /criar-pdf-metta C:/path/to/02_treinamento.docx
```

Aceita também:
- Markdown: `brief.md`
- Prosa: user descreve, você converte em MD temporário

Pergunte ao user o **setor / contexto** se não estiver óbvio do brief:
> "Qual o setor / cenário das imagens? Ex: 'loja de posto de combustível', 'consultório odontológico', 'agência de marketing'..."

Isso vai pra `--setor=...` nos scripts.

## Passo 2 — Parse + select layout

```bash
PLUGIN_DIR=~/.claude/plugins/marketplaces/metta/metta-pdf
python "$PLUGIN_DIR/scripts/select_layout.py" "<brief.docx>"
```

Saída:
```
1. TÍTULO DA CAPA              →  cover
2. Abertura/Intro              →  opener-spread
3. Fundamento 1                →  content-only
...
```

**Mostre essa tabela pro user e pergunte:**
> "Aprovar este mapeamento ou ajustar algo?"

Permita overrides simples:
- "muda seção 3 pra hero-strip"
- "junta seções 4 e 5"
- "remove seção 6"

## Passo 3 — Sugerir imagens

```bash
python "$PLUGIN_DIR/scripts/suggest_images.py" "<brief.docx>" --setor="<setor>"
```

Saída exemplo:
```
8 pontos editoriais sugeridos:
  • VISUALIZE O CENÁRIO              →  cover           (16:9 1K)  →  cover.jpeg
  • Como Perguntar?                  →  opener-spread   (1:1 1K)   →  01-opener-...
  • Perfil 1: Caminhoneiro Autônomo  →  profile-spread  (4:5 1K)   →  04-profile-...
  ...
```

**Mostre pro user e pergunte:**
> "Aprovar todos os {N} pontos? Custo estimado ~${N×$0.07}. Você pode também:
> - aprovar parcialmente (\"gerar só cover e perfis\")
> - editar um prompt (\"o caminhoneiro autônomo deve ter ~40 anos, não 50\")
> - pular tudo (\"sem imagens, só placeholders\")"

## Passo 4 — Gerar imagens

```bash
python "$PLUGIN_DIR/scripts/generate_images.py" "<brief.docx>" "<output_dir>/img" --setor="<setor>"
```

O script:
- Roda em paralelo (4 workers default)
- Retry com prompt encurtado se der timeout
- Falhas viram placeholder no PDF final

Avise o user: cada imagem leva ~30-90s. Para ~6 imagens em paralelo, total ~2-3min.

## Passo 5 — Renderizar HTML + PDF

```bash
python "$PLUGIN_DIR/scripts/render_html.py" "<brief.docx>" "<output_dir>/<slug>.html"
python "$PLUGIN_DIR/scripts/render_pdf.py" "<output_dir>/<slug>.html" "<output_dir>/<slug>.pdf"
```

Pra ligar imagens no HTML, o pipeline completo precisa do `image_map` retornado
pelo `generate_images.py`. Use o módulo Python diretamente:

```python
import sys, json
sys.path.insert(0, "<PLUGIN_DIR>/scripts")
from parse_brief import parse
from select_layout import classify_sections
from suggest_images import suggest
from generate_images import generate_all, image_map_from_results
from render_html import render
from render_pdf import render as render_pdf

secs = parse("brief.docx")
enriched = classify_sections(secs)
points = suggest(enriched, brief_context={"setor": "..."})
# user confirma points...
results = generate_all(points, output_dir="output/img")
image_map = image_map_from_results(results)
html = render(enriched, doc_title="...", meta_text="...", image_map=image_map)
Path("output/doc.html").write_text(html, encoding="utf-8")
render_pdf("output/doc.html", "output/doc.pdf")
```

## Passo 6 — Entregar

Reporte:
- Caminho do PDF + HTML
- Lista de imagens geradas (e quais foram placeholder por falha)
- Tempo total + custo estimado

## Decisões de design embarcadas

- **Cover** sempre = primeira seção, headline gigante com palavra-chave em accent yellow
- **Profile-spread** para "Perfil N:" / "Persona N:" — magazine 2-col com foto 4:5 esquerda + qtable direita
- **Quote-photo** para citações longas (>20 palavras entre aspas) — fundo dark + mark amarelo + texto italic branco
- **Hero-strip** para seções curtas de transição — banner horizontal 21:6 com caption overlay
- **Opener-spread** para segunda seção (lede longo + comparação) — texto + imagem quadrada lado a lado
- **Content-only** default para fundamentos com tabela compare ou grid de cards

## Arquivos do plugin

```
metta-pdf/
├── skills/criar-pdf-metta/SKILL.md   # este arquivo
├── scripts/
│   ├── parse_brief.py                # DOCX/MD → AST de seções
│   ├── select_layout.py              # heurística seção → layout
│   ├── suggest_images.py             # propõe pontos editoriais + prompts
│   ├── generate_images.py            # nano-banana CLI paralelo + retry
│   ├── render_html.py                # AST + image_map → HTML via Jinja2
│   └── render_pdf.py                 # Chrome headless wrapper
├── templates/
│   ├── base.html                     # shell + tokens + symbol logo
│   └── layouts/                      # 6 layouts canônicos
├── tokens/
│   ├── metta-ds.css                  # design system completo
│   └── logo-symbols.svg              # logo M + variantes light/dark
├── prompt-presets/
│   └── arquetipos.md                 # 5 arquétipos de prompt por cena
└── docs/PRD.md                       # PRD completo
```

## Output esperado

```
output/<doc-slug>/
├── <doc-slug>.pdf                    # final
├── <doc-slug>.html                   # fonte editável
└── img/                              # imagens (4-8 dependendo do brief)
    ├── cover.jpeg
    ├── 01-opener-spread-*.jpeg
    └── ...
```

## Troubleshooting

- **Chrome não encontrado:** instalar Chrome ou Edge. `render_pdf.py` detecta automaticamente.
- **nano-banana CLI não encontrado:** `npm install -g nano-banana` ou instalar manualmente em `~/.local/bin/`.
- **GEMINI_API_KEY ausente:** exportar a key da Google AI Studio antes de rodar.
- **Imagens timeout:** retry com prompt encurtado já é automático. Se falhar 2× → placeholder visível.
- **Marcas reais no fundo das fotos:** prompts já tem "no readable brands/text", mas Gemini Flash às vezes burla. Vale regenerar 1× ou ignorar pra teste.
- **Conteúdo cortado em alguma página:** layout estourou os 257mm úteis. Avisar pro classificador melhorar.

## Versão

v1.1 (Sprint 2) — pipeline core + imagens com aprovação. Próximas fases:
v1.2 multi-marca (Tiago), v1.3 templates adicionais (relatório, e-book).
