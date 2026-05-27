---
name: criar-pdf-metta
description: Gera PDF institucional editorial Metta a partir de DOCX/Markdown. Use quando o user pedir pra criar/gerar/montar/produzir documento, treinamento, módulo, manual ou material editorial PDF para a Metta. Aplica design system + 6 layouts canônicos + (Sprint 2) imagens AI via nano-banana. Não usar pra PPTX (use /criar-slide-metta) nem pra ads.
---

# /criar-pdf-metta — Orquestrador

## Quando invocar

User pediu pra criar/gerar/montar PDF institucional Metta a partir de:
- Um arquivo DOCX existente
- Um arquivo Markdown
- Uma descrição em prosa do conteúdo (caso simples — converte em MD primeiro)

Tipicamente:
- Módulos de treinamento (5-15 páginas)
- Manuais operacionais
- Relatórios editoriais
- Apostilas / materiais de mentoria

Não usar para:
- Apresentações PPTX → `/criar-slide-metta`
- Ads / posts IG → `/copy-ad` + `/design-metta`
- Landing pages → outros skills

## Fluxo

```
INPUT  → parse → suggest layout mapping → user-approve →
         [Sprint 2: suggest images → user-approve → generate]
         → render HTML → render PDF
OUTPUT → output/<nome>.pdf + .html (fonte editável)
```

## Passos

### 1. Receber o brief
```
User: /criar-pdf-metta path/to/02_treinamento.docx
```

Aceita também:
- Caminho absoluto Windows: `C:/Users/.../brief.docx`
- Markdown: `brief.md`
- Prosa: user descreve, você converte em MD temporário antes de seguir

### 2. Rodar parse + select_layout

```bash
python ~/.claude/plugins/cache/<id>/metta-pdf/scripts/select_layout.py "<brief>"
```

(ou em outra rota se rodando localmente: `claude-plugins/metta-pdf/scripts/select_layout.py`)

Saída esperada:
```
1. TÍTULO DA CAPA              →  cover
2. Abertura/Intro              →  opener-spread
3. Fundamento 1                →  content-only
...
```

### 3. Confirmar mapeamento com o user

Mostre a tabela seção → layout e pergunte:
> "Aprovar este mapeamento ou ajustar algo?"

Permita overrides simples:
- "muda seção 3 pra hero-strip"
- "junta seções 4 e 5"
- "remove seção 6"

### 4. (Sprint 2 — ainda não disponível) Sugerir imagens

Quando implementado, o plugin vai propor 3-6 pontos editoriais (cover + perfis + abertura), gerar prompts via skill `/nano-banana`, e pedir aprovação antes de rodar `nano-banana` CLI em paralelo.

**Por enquanto (Sprint 1):** rodar sem imagens — placeholders visuais [imagem] aparecem onde a foto entraria.

### 5. Renderizar HTML + PDF

```bash
python ~/.claude/plugins/cache/<id>/metta-pdf/scripts/render_html.py "<brief>" out/document.html
python ~/.claude/plugins/cache/<id>/metta-pdf/scripts/render_pdf.py out/document.html out/document.pdf
```

### 6. Entregar

Reporta caminho do PDF + HTML + lista de placeholders de imagem que ficaram pendentes.

## Decisões de design embarcadas

- **Cover** sempre = primeira seção, título em headline gigante com palavra-chave em accent yellow
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
│   ├── render_html.py                # AST → HTML via Jinja2
│   └── render_pdf.py                 # Chrome headless wrapper
├── templates/
│   ├── base.html                     # shell + tokens + symbol logo
│   └── layouts/                      # 6 layouts (cover, opener-spread, ...)
├── tokens/
│   ├── metta-ds.css                  # design system completo
│   └── logo-symbols.svg              # logo M + variantes light/dark
└── docs/PRD.md                       # PRD completo (espelhado em arquitetura/)
```

## Output esperado

```
output/<doc-slug>/
├── <doc-slug>.pdf                    # final
├── <doc-slug>.html                   # fonte editável (CSS+SVG embutidos)
└── img/                              # imagens (Sprint 2+); vazio no Sprint 1
```

## Troubleshooting

- **Chrome não encontrado:** instalar Chrome ou Edge. `render_pdf.py` detecta automaticamente.
- **Parsing errado:** DOCX precisa usar estilos Heading 1/2/3 nos títulos. Sem isso, o parser depende da heurística de UPPERCASE.
- **Imagens não aparecem (Sprint 1):** isso é esperado — placeholders `[imagem]` ocupam o espaço. Sprint 2 adicionará geração via nano-banana.
- **Conteúdo cortado em alguma página:** layout estourou os 257mm úteis. Edita o brief ou avise ao desenvolvedor — vai pra backlog de melhorias do classificador.

## Versão

v1.0 (Sprint 1) — pipeline core sem imagens. Sprint 2 vai adicionar geração de imagens com fluxo sugerir+aprovar.
