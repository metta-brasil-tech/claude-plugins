---
name: criar-pdf-metta
description: Gera PDF institucional editorial Metta a partir de DOCX/Markdown. Use quando o user pedir pra criar/gerar/montar/produzir documento, treinamento, módulo, manual ou material editorial PDF para a Metta. Aplica design system + 6 layouts canônicos + geração de imagens AI via nano-banana com fluxo sugerir+aprovar. Não usar pra PPTX (use /criar-slide-metta) nem pra ads.
---

# /criar-pdf-metta — Orquestrador

## Quando invocar

User pediu pra criar/gerar/montar PDF institucional Metta a partir de:
- Um arquivo DOCX existente
- Um arquivo Markdown
- Uma descrição em prosa (caso simples — converta em MD primeiro)

Tipicamente:
- Módulos de treinamento (5-15 páginas)
- Manuais operacionais
- Relatórios editoriais
- Apostilas de mentoria

Não usar para:
- Apresentações PPTX → `/criar-slide-metta`
- Ads / posts IG → `/copy-ad` + `/design-metta`
- Landing pages → outros skills

## Fluxo

```
1. INPUT          → user passa DOCX/MD
2. PARSE+LAYOUT   → mostra mapeamento seção→layout, espera aprovação
3. SUGGEST IMG    → propõe pontos editoriais, espera aprovação
4. GENERATE+PDF   → roda build_pdf.py com tudo aprovado
OUTPUT → output/<slug>/<slug>.pdf + .html + img/*.jpeg + report.json
```

## Pré-requisitos

Antes da primeira execução, rodar:
```bash
python ~/.claude/plugins/marketplaces/metta/metta-pdf/scripts/setup_check.py
```

Garante: Python 3.11+, python-docx, Jinja2, Chrome, nano-banana CLI (pra
imagens), `GEMINI_API_KEY`. Se algo faltar, o script aponta como resolver.

## Passo 1 — Receber o brief

```
User: /criar-pdf-metta C:/path/to/02_treinamento.docx
```

Aceita também:
- Markdown: `brief.md`
- Prosa: converta em MD temporário antes

Pergunte ao user o **setor / cenário** se não estiver óbvio:
> "Qual o setor / cenário das imagens? Ex: 'loja de posto de combustível',
> 'consultório odontológico', 'agência de marketing'..."

## Passo 2 — Mostrar mapeamento + aprovação

Rode com `--dry-run` pra inspecionar antes de gastar tempo/dinheiro:

```bash
PLUGIN=~/.claude/plugins/marketplaces/metta/metta-pdf
python "$PLUGIN/scripts/build_pdf.py" "<brief>" \
  --setor="<setor>" --output ./output/<slug> --dry-run
```

Saída exemplo:
```
━━━ 1. Parse + layout selection ━━━
1. TÍTULO DA CAPA              →  cover
2. Abertura/Intro              →  opener-spread
3. Fundamento 1                →  content-only
...

━━━ 2. Imagens sugeridas (dry-run) ━━━
  • TÍTULO DA CAPA              →  cover           (16:9 1K)
  • Perfil 1: ...               →  profile-spread  (4:5 1K)
  ...
```

**Mostre essa saída pro user e pergunte:**
> "Aprovar este mapeamento e a lista de {N} imagens (~${N×$0.07})? Você pode:
> - aprovar tudo
> - pedir overrides ('muda seção 3 pra hero-strip', 'remove imagem do perfil 2')
> - pular imagens ('--skip-images')"

## Passo 3 — Rodar pipeline completo

Com aprovação, rode sem `--dry-run`:

```bash
python "$PLUGIN/scripts/build_pdf.py" "<brief>" \
  --setor="<setor>" \
  --output ./output/<slug> \
  --title "<título>" \
  --meta "<header texto>" \
  --module-label "<eyebrow capa>"
```

Variantes úteis:
- `--skip-images` — pula geração AI, usa placeholders (rápido, sem custo)
- `--workers 1` — sequencial (mais lento, mais resiliente contra 503)
- `--workers 2` — default (paralelo equilibrado)

O script entrega:
- `<slug>.pdf` — final
- `<slug>.html` — fonte editável
- `img/*.jpeg` — imagens geradas
- `report.json` — log estruturado com status de cada imagem

## Passo 4 — Reportar pro user

Após sucesso:
> "Pronto. PDF em `output/<slug>/<slug>.pdf` ({tamanho} MB · {páginas} páginas).
> {N_OK}/{N_TOTAL} imagens geradas. {Falhas, se houver}."

Se alguma imagem falhou (status=failed no report.json), avise:
> "{N} imagens viraram placeholder visível no PDF — provavelmente Gemini 503 ou
> timeout persistente. Quer regenerar essas N específicas? (rodar de novo com
> --workers 1 costuma resolver)"

## Decisões de design embarcadas

- **Cover** sempre = primeira seção, headline gigante com palavra-chave em accent yellow
- **Profile-spread** para "Perfil N:" / "Persona N:" — magazine 2-col foto 4:5 + qtable
- **Quote-photo** para citações longas (>20 palavras entre aspas)
- **Hero-strip** para seções curtas de transição (banner 21:6 com caption overlay)
- **Opener-spread** para segunda seção (lede + imagem 1:1 lado a lado)
- **Content-only** default e usado em fundamentos com compare block ou grid de cards

## Arquivos do plugin

```
metta-pdf/
├── skills/criar-pdf-metta/SKILL.md   # este arquivo
├── scripts/
│   ├── build_pdf.py                  # ★ CLI unificado (use este)
│   ├── setup_check.py                # validador de ambiente
│   ├── parse_brief.py
│   ├── select_layout.py
│   ├── suggest_images.py
│   ├── generate_images.py
│   ├── render_html.py
│   └── render_pdf.py
├── templates/                        # base.html + 6 layouts
├── tokens/                           # metta-ds.css + logo-symbols.svg
├── prompt-presets/arquetipos.md      # 5 arquétipos de prompt
└── docs/PRD.md
```

## Troubleshooting comum

Ver README.md do plugin pra tabela completa. Resumo do mais comum:

| Sintoma | Mitigação |
|---|---|
| Imagem timeout 2x | Já entra em retry curto. Se falhar, vira placeholder. |
| Imagem 503 (overload) | Já entra em backoff 5/15/30s. Se persistir, use `--workers 1`. |
| `WinError 193` | Faltou Git Bash no Windows. Instalar Git for Windows resolve. |
| Conteúdo cortado | Layout estourou 257mm úteis. Reportar pro backlog do classificador. |
| Cover prompt falha | Sprint 3 simplificou. Se ainda falhar, gerar manualmente OU usar `--skip-images` + adicionar imagem depois. |

## Versão

v1.2.0 (Sprint 3) — CLI unificado `build_pdf.py` + setup_check + classifier
refinement + cover prompt encurtado. Pipeline pronto pra distribuição no time.
