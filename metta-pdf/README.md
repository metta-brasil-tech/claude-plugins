# metta-pdf

Gerador de **PDFs institucionais editoriais Metta** a partir de DOCX/Markdown. Aplica o design system automaticamente, renderiza via Chrome headless e (a partir do Sprint 2) gera imagens AI nos pontos editoriais.

## Status

- **Sprint 1** — Core pipeline (sem imagens). DOCX/MD → PDF aplicando DS.
- **Sprint 2** — Imagens com aprovação (nano-banana CLI + Gemini Flash Image).
- **Sprint 3** — Distribuição + setup-check.

## Instalação

```bash
claude plugin marketplace add metta-brasil-tech/claude-plugins
claude plugin install metta-pdf@metta
```

### Workaround se der "Failed to finalize marketplace cache" no Windows

Bug conhecido do Claude CLI no Windows: o rename interno da pasta de cache falha
com `EPERM`. Solução manual em 3 passos:

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

## Uso

```
/criar-pdf-metta path/to/brief.docx
```

Plugin extrai o conteúdo, sugere mapeamento seção→layout, e gera o PDF aplicando os tokens Metta.

## Dependências

- **Python 3.11+** com `python-docx` + `Jinja2`
- **Chrome** ou Edge ou Chromium no PATH
- **(Sprint 2+)** nano-banana CLI + `GEMINI_API_KEY`

## Estrutura

```
metta-pdf/
├── .claude-plugin/plugin.json
├── skills/criar-pdf-metta/SKILL.md  # orquestrador
├── scripts/
│   ├── parse_brief.py               # DOCX/MD → AST
│   ├── select_layout.py             # heurística seção → layout
│   ├── render_html.py               # AST → HTML via Jinja2
│   └── render_pdf.py                # Chrome headless → PDF
├── templates/
│   ├── base.html                    # shell + tokens + symbols
│   └── layouts/                     # 6 layouts canônicos
├── tokens/
│   ├── metta-ds.css                 # design system completo
│   └── logo-symbols.svg             # logo M + variantes
└── docs/PRD.md
```

## Documentação completa

Ver `docs/PRD.md` ou no vault Obsidian: `arquitetura/claude-plugin-metta-pdf.md`.
