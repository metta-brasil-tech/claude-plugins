# Metta · Claude Code Plugins

Marketplace privado de plugins Claude Code do time Metta.

## Plugins disponíveis

| Plugin | Descrição |
|---|---|
| [metta-deck](./metta-deck) | Gera apresentações PPTX institucionais Metta fiéis ao PPT Modelo Geral |
| [metta-pdf](./metta-pdf) | Gera PDFs institucionais editoriais Metta a partir de DOCX/Markdown aplicando design system |
| [metta-triagem](./metta-triagem) | Roteia tarefas pro modelo certo (Haiku/Sonnet/Opus) pra economizar tokens — hook + skill /triagem |

## Instalação

```bash
# adicionar este marketplace (uma vez)
claude plugin marketplace add metta-brasil-tech/claude-plugins

# listar plugins disponíveis
claude plugin list

# instalar um plugin
claude plugin install metta-deck
```

## Estrutura do repo

```
claude-plugins/
├── .claude-plugin/marketplace.json    # índice de plugins
├── metta-deck/                        # plugin 1
│   ├── .claude-plugin/plugin.json
│   ├── skills/
│   ├── scripts/
│   ├── assets/
│   └── docs/
└── README.md
```

## Contribuir

Cada plugin vive numa pasta própria com seu manifesto `.claude-plugin/plugin.json`. Pra adicionar um plugin novo:

1. Cria a pasta `<nome-do-plugin>/`
2. Estrutura mínima: `.claude-plugin/plugin.json` + `skills/<nome>/SKILL.md`
3. Adiciona entrada em `.claude-plugin/marketplace.json`
4. Valida: `claude plugin validate ./<nome-do-plugin>`
5. PR

## Versão

Marketplace v1.0.0 · 2026-05-26
