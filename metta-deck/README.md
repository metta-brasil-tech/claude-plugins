# metta-deck

Plugin Claude Code que gera apresentações PPTX institucionais Metta abrindo o `PPT Modelo Geral` como template e substituindo apenas os textos placeholder pelo conteúdo do briefing. Preserva 100% das configurações originais (imagens, layouts, fontes embutidas, slide masters, theme XML).

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
├── skills/criar-slide-metta/SKILL.md   # skill principal
├── scripts/
│   ├── build_deck.py                   # runner copy-and-substitute
│   └── builders.py                     # lib pra tipos novos (timeline/equipe/etc)
├── assets/
│   ├── modelo-geral.pptx               # template canônico (25 slides, 14MB)
│   ├── logo_dark.png
│   └── logo_light.png
└── docs/
    └── metta-pptx-canonico.md          # ficha técnica DNA visual
```

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
- `pip install python-pptx`

## Versão

v1.0.0 · 2026-05-26

## Licença

Uso interno Metta. Não distribuir.
