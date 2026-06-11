# metta-deck

Plugin Claude Code com duas skills:

- **`/criar-slide-metta`** — apresentações PPTX institucionais Metta abrindo o `PPT Modelo Geral` como template e substituindo apenas os textos placeholder pelo conteúdo do briefing. Preserva 100% das configurações originais (imagens, layouts, fontes embutidas, slide masters, theme XML).
- **`/cliente-pdf`** — documentos PDF na identidade visual **do CLIENTE** (white-label): manual, livro de operações, checklist, procedimento, relatório. Motor marca-aware (separa marca de conteúdo) + 11 blocos. HTML+CSS → Chrome headless → PDF.

## Instalação

```bash
# adicionar marketplace Metta (uma vez)
claude plugin marketplace add metta-brasil-tech/claude-plugins

# instalar o plugin
claude plugin install metta-deck
```

## Uso

Dentro do Claude Code, invoque a skill:

```
/metta-deck:criar-slide-metta
```

A skill vai perguntar o briefing (cliente, decisor, statement, CTA, próximos passos), gerar o `briefing.json`, rodar o runner Python e produzir o `.pptx` no diretório atual.

### Uso direto (sem skill)

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/build_deck.py" \
  --client "ACME" \
  --statement "Como vamos juntos · ACME." \
  --cta "AGENDAR COM JOÃO" \
  --date-month "Junho/2026" \
  --out proposta-acme.pptx
```

Ou via JSON:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/build_deck.py" \
  --briefing ./briefing.json \
  --out proposta-acme.pptx
```

## Estrutura

```
metta-deck/
├── .claude-plugin/plugin.json          # manifesto
├── skills/
│   ├── criar-slide-metta/SKILL.md      # skill de slides (PPTX)
│   └── cliente-pdf/SKILL.md            # skill de PDF white-label do cliente
├── scripts/
│   ├── build_deck.py                   # runner copy-and-substitute (slides)
│   ├── builders.py                     # lib pra tipos novos (timeline/equipe/etc)
│   └── cliente-pdf/                    # motor do /cliente-pdf
│       ├── build.py                    # CLI: build.py <marca|caminho> <content.json> [out.pdf]
│       ├── base.css                    # layout + blocos (marca-agnóstico)
│       ├── schema.md                   # referência do JSON de conteúdo
│       ├── _template/                  # pasta-base da marca (copiar pra criar cliente)
│       └── examples/showcase-blocos.json
├── assets/
│   ├── modelo-geral.pptx               # template canônico (25 slides, 14MB)
│   ├── logo_dark.png
│   └── logo_light.png
└── docs/
    └── metta-pptx-canonico.md          # ficha técnica DNA visual
```

## /cliente-pdf — uso rápido

```bash
# 1. criar a marca do cliente a partir do _template (FORA do plugin, no vault)
cp -r "${CLAUDE_PLUGIN_ROOT}/scripts/cliente-pdf/_template" <vault>/<cliente>
#    editar <cliente>/brand.json + assets/logo.png + fonts/*.ttf

# 2. gerar o PDF (1º arg = caminho da pasta da marca)
python "${CLAUDE_PLUGIN_ROOT}/scripts/cliente-pdf/build.py" \
  "<vault>/<cliente>" ./conteudo.json ./cliente-doc.pdf
```

Blocos do conteúdo: `greeting`, `section`, `heading`, `paragraph`, `list`
(bullet/number/check), `keyvalue`, `table`, `image`, `callout`, `divider`, `spacer`.
Inline `**negrito**` / `*itálico*`. Ver `scripts/cliente-pdf/schema.md`.

## Como funciona

1. Plugin embarca o `PPT Modelo - Geral.pptx` (25 slides desenhados pelo time, com fotos editoriais, ornamentos, fontes embutidas)
2. Skill coleta briefing
3. Runner abre o template, substitui apenas runs de texto com placeholders conhecidos:

| Placeholder | Vira |
|---|---|
| `[NOME CLIENTE]` (38×) | `briefing.client.upper()` |
| `Lorem ipsum dolor sit amet` (2×) | `briefing.statement` |
| `Grupo Linhares` (1×) | `briefing.client.title()` |
| `AGENDAR DIAGNÓSTICO` (3×) | `briefing.cta.upper()` |
| `Próximas 2 semanas` (1×) | `briefing.date_month` |
| `Exemplificar na situação do cliente.` (1×) | `briefing.kpi_subtitle` |

4. Salva como novo `.pptx` mantendo TODO o resto idêntico

## Requisitos

- Python 3.10+ no PATH
- `/criar-slide-metta`: `pip install python-pptx`
- `/cliente-pdf`: Chrome ou Edge instalado (detecção automática) + `pip install PyMuPDF` (só pra QA visual)

## Versão

v1.1.0 · 2026-06-11 — adicionada skill `/cliente-pdf` (documentos PDF white-label na identidade do cliente; generaliza o gerador MIME).
v1.0.0 · 2026-05-26 — PPTX via copy-and-substitute.

## Licença

Uso interno Metta. Não distribuir.
