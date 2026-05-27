# metta-pdf

Gerador de **PDFs institucionais editoriais Metta** a partir de DOCX/Markdown.
Aplica o design system automaticamente, gera imagens AI nos pontos editoriais
relevantes (via nano-banana / Gemini Flash) e renderiza o PDF final via Chrome
headless.

## Status

- ✅ **Sprint 1** — Core pipeline (DOCX/MD → HTML → PDF aplicando DS).
- ✅ **Sprint 2** — Imagens AI com aprovação (nano-banana CLI + Gemini Flash).
- ✅ **Sprint 3** — CLI unificado `build_pdf.py` + setup-check + onboarding.

## Instalação

```bash
# 1× por máquina
claude plugin marketplace add metta-brasil-tech/claude-plugins
claude plugin install metta-pdf@metta

# Validar ambiente
python ~/.claude/plugins/marketplaces/metta/metta-pdf/scripts/setup_check.py
```

### Workaround Windows (bug do EPERM ao adicionar marketplace)

Se der **"Failed to finalize marketplace cache"** no Windows:

```bash
# 1. clonar o repo direto na pasta de marketplaces
cd ~/.claude/plugins/marketplaces
git clone https://github.com/metta-brasil-tech/claude-plugins.git metta

# 2. adicionar entry em ~/.claude/plugins/known_marketplaces.json:
#    {
#      "metta": {
#        "source": { "source": "github", "repo": "metta-brasil-tech/claude-plugins" },
#        "installLocation": "C:\\Users\\<user>\\.claude\\plugins\\marketplaces\\metta",
#        "lastUpdated": "2026-05-27T00:00:00.000Z"
#      }
#    }

# 3. instalar normalmente
claude plugin install metta-pdf@metta
```

## Dependências

| Item | Versão | Obrigatório? |
|---|---|---|
| Python | 3.11+ | sim |
| python-docx | 1.0+ | sim |
| Jinja2 | 3.1+ | sim |
| Chrome / Edge / Chromium | qualquer recente | sim |
| nano-banana CLI | 2.0+ (Gemini Flash) | só pra imagens AI |
| `GEMINI_API_KEY` env var | — | só pra imagens AI |
| Git Bash (Windows) | — | só se nano-banana for shebang script |

O `setup_check.py` valida tudo de uma vez:

```bash
python ~/.claude/plugins/marketplaces/metta/metta-pdf/scripts/setup_check.py
```

## Uso

### Via skill (recomendado)

```
/criar-pdf-metta C:/path/to/02_treinamento.docx
```

A skill conduz o fluxo conversacional:
1. Mostra mapeamento seção → layout, espera aprovação
2. Sugere pontos editoriais pra imagem, espera aprovação
3. Gera imagens em paralelo (com retry de timeout + backoff 503)
4. Renderiza HTML + PDF

### Via CLI direto

```bash
PLUGIN_DIR=~/.claude/plugins/marketplaces/metta/metta-pdf

# Pipeline completo com imagens AI
python "$PLUGIN_DIR/scripts/build_pdf.py" brief.docx \
  --setor="loja de conveniência de posto" \
  --module-label="Módulo 02 · Treinamento" \
  --output ./output

# Sem imagens (mais rápido, com placeholders)
python "$PLUGIN_DIR/scripts/build_pdf.py" brief.docx --skip-images

# Dry-run (só mostra mapeamento, não gera)
python "$PLUGIN_DIR/scripts/build_pdf.py" brief.docx --dry-run

# Single worker (mais lento, mais resiliente)
python "$PLUGIN_DIR/scripts/build_pdf.py" brief.docx --workers 1
```

## Output

```
output/<doc-slug>/
├── <doc-slug>.pdf        # final
├── <doc-slug>.html       # fonte editável (CSS + SVG embutidos)
├── img/                  # imagens geradas (4-8 dependendo do brief)
│   ├── cover.jpeg
│   ├── 01-opener-spread-...jpeg
│   └── ...
└── report.json           # log estruturado da execução
```

## Layouts canônicos

| Layout | Quando | Slot de imagem |
|---|---|---|
| **cover** | Primeira seção | 16:9 background full-bleed |
| **opener-spread** | Segunda seção (lede + comparação) | 1:1 quadrado à direita |
| **hero-strip** | Seções transitórias | 16:9 banner horizontal |
| **content-only** | Fundamentos com compare/grid/qtable | sem imagem |
| **profile-spread** | "Perfil N:" / "Persona N:" | 4:5 portrait à esquerda |
| **quote-photo** | Citações diretas longas | 16:9 background com overlay |

## Heurística do classificador

1. Primeira seção → **cover**
2. Título com "Perfil N:" / "Persona N:" → **profile-spread**
3. Citação >20 palavras entre aspas → **quote-photo**
4. Seção curta (≤4 parágrafos) sem tabela → **hero-strip**
5. Tabela com compare (header antonímico ou body longo) → **content-only**
6. Segunda seção sem tabela, com muito body → **opener-spread**
7. Default → **content-only**

Override manual: o user pode pedir "muda seção N pra X" no fluxo da skill.

## Estrutura do plugin

```
metta-pdf/
├── .claude-plugin/plugin.json
├── README.md (este arquivo)
├── skills/criar-pdf-metta/SKILL.md
├── scripts/
│   ├── build_pdf.py           # CLI unificado (Sprint 3)
│   ├── setup_check.py         # validador de ambiente
│   ├── parse_brief.py         # DOCX/MD → AST
│   ├── select_layout.py       # heurística seção → layout
│   ├── suggest_images.py      # pontos editoriais + prompts
│   ├── generate_images.py     # nano-banana CLI paralelo + retry
│   ├── render_html.py         # AST + image_map → HTML
│   └── render_pdf.py          # Chrome headless wrapper
├── templates/
│   ├── base.html
│   └── layouts/               # 6 layouts canônicos
├── tokens/
│   ├── metta-ds.css           # design system completo
│   └── logo-symbols.svg       # logo M + variantes
├── prompt-presets/
│   └── arquetipos.md          # 5 arquétipos de prompt
└── docs/PRD.md
```

## Troubleshooting

| Sintoma | Causa | Solução |
|---|---|---|
| `nano-banana não encontrada` | CLI não instalada | Instalar via npm/wrapper local |
| `WinError 193` ao chamar nano-banana | nano-banana é shebang script no Windows | Já tratado: build_pdf usa Git Bash. Garanta que Git esteja instalado. |
| Imagens 503 (overloaded) | Gemini Flash sobrecarregado | Já tratado: retry com backoff 5/15/30s. Reduza workers se persistir. |
| Imagens timeout | Prompts longos demais (>800 chars) | Já tratado: retry com prompt encurtado. Se ainda falhar, fallback pra placeholder. |
| Cover prompt falha consistente | Prompt da cover é o mais longo | Sprint 3 já encurtou. Se ainda falhar, `--workers 1` pra rodar sequencial. |
| Conteúdo cortado no PDF | Layout estourou 257mm úteis | Reportar pro classificador melhorar. Workaround: usar `--skip-images` ou simplificar brief. |
| Chrome não encontrado | Path não detectado | Instalar Chrome ou Edge, ou definir CHROME_PATH env var. |

## Documentação adicional

- PRD completo: `docs/PRD.md` (espelho do vault Obsidian: `arquitetura/claude-plugin-metta-pdf.md`)
- Skill: `skills/criar-pdf-metta/SKILL.md`
- Arquétipos de prompt: `prompt-presets/arquetipos.md`
