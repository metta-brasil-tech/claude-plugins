---
name: criar-slide-metta
description: Use quando o user pedir pra criar/gerar/montar/produzir apresentação PPTX ou deck Metta (proposta comercial, sessão estratégica, institucional, keynote, relatório). Gera arquivo .pptx final 100% fiel ao PPT Modelo Geral via copy-and-substitute do template embarcado no plugin. Não usar pra ads, carrosséis IG ou one-pagers PDF.
---

# Criar Slide Metta

Gera apresentações PPTX institucionais Metta abrindo o `PPT Modelo - Geral.pptx` embarcado no plugin como template e substituindo apenas os textos placeholder pelo conteúdo do briefing. Preserva 100% das configurações originais (imagens, layouts, fontes embutidas, slide masters, theme XML, picture cropping).

## Quando usar

- Proposta comercial pra cliente novo
- Sessão estratégica / diagnóstico
- Deck institucional Metta (pitch da empresa)
- Keynote evento (Mentoria SMTM, workshop)
- Relatório de resultados pra cliente atual

## Quando NÃO usar

- Ads (estáticos ou vídeo) → use `/design-metta` ou `/copy-ad`
- Carrosséis Instagram → use `/criar`
- One-pagers PDF → `/design-metta`

## Fluxo

### 1. Coletar briefing

Pergunte ao user (se faltar):
- **Cliente:** nome (ex: "Leroy Merlin")
- **Decisor:** quem recebe a proposta (vai no CTA · ex: "Caique Neves" → "AGENDAR COM CAIQUE")
- **Statement da capa:** frase principal (default: "Como vamos juntos · <cliente>.")
- **Próximos passos / disponibilidade:** ex: "Junho/2026"
- **Substituições extras (opcional):** nomes em depoimentos, números específicos, casos

### 2. Apresentar briefing pra validação

Mostre o briefing estruturado e aguarde "ok" antes de gerar.

### 3. Gerar via runner Python

Crie um arquivo `briefing.json` no diretório de output desejado:

```json
{
  "client": "LEROY MERLIN",
  "statement": "Como vamos juntos · Leroy Merlin.",
  "cta": "AGENDAR COM CAIQUE",
  "date_month": "Junho/2026",
  "kpi_subtitle": "Os indicadores que sustentam a operação · exemplo prático.",
  "extra_replacements": {}
}
```

Rode o runner:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/build_deck.py" \
  --briefing ./briefing.json \
  --out ./metta-proposta-<cliente>.pptx
```

O script:
1. Abre `${CLAUDE_PLUGIN_ROOT}/assets/modelo-geral.pptx` (template canônico, 25 slides)
2. Aplica substituições em todos os runs preservando formatação
3. Salva o `.pptx` final (~14MB, igual ao template em estrutura)

### 4. Entregar

- Caminho do arquivo gerado
- Resumo das substituições aplicadas (output do runner)
- Sugestão: abrir no PowerPoint pra revisar antes de mandar pro cliente

### 5. Salvar doc descritivo no vault (se vault disponível)

Em `work/active/<cliente>/proposta-<YYYY-MM>.md`:

```yaml
---
title: "[Metta] - Proposta - <Cliente> - <YYYY-MM>"
tags: [marca/metta, formato/pptx, tipo/proposta-comercial, status/ativo, cliente/<slug>]
created: <date>
---
```

Conteúdo: briefing, lista de substituições, path do arquivo gerado.

## Placeholders do template (catálogo validado)

| Placeholder | Ocorrências | Substituído por |
|---|---|---|
| `[NOME CLIENTE]` | 38× | `briefing.client.upper()` |
| `Lorem ipsum dolor sit amet` | 2× (capa) | `briefing.statement` |
| `Grupo Linhares` | 1× (slide 6 footer) | `briefing.client.title()` |
| `Exemplificar na situação do cliente.` | 1× (slide 11 KPI) | `briefing.kpi_subtitle` |
| `Próximas 2 semanas` | 1× (slide 19) | `briefing.date_month` |
| `AGENDAR DIAGNÓSTICO` | 3× (slides 19, 24, 25) | `briefing.cta.upper()` |

Substituições extras (case-by-case): nomes em depoimentos, números específicos, etc. — passar via `briefing.extra_replacements`.

## Anti-padrões

- ❌ **NÃO recriar slide via python-pptx do zero.** A abordagem é sempre copy-and-substitute do template. Validado em 2026-05-25 — recriação perde imagens, fontes, layers, etc.
- ❌ Não inventar dados (cliente, números, depoimentos). Só usar o que o briefing fornece.
- ❌ Não modificar o template `modelo-geral.pptx` embarcado — é fonte canônica.

## Tipos novos (não cobertos pelo template)

Se o briefing pedir tipos que **não existem** no template (`timeline`, `equipe`, `roadmap`, `funnel`, `faq`, `pricing`, `matriz_2x2`, `hub_spoke`), aí sim usar a lib `${CLAUDE_PLUGIN_ROOT}/scripts/builders.py` — esses 6 builders foram validados manualmente em deck dedicado.

Mas o padrão é: **default = copy-and-substitute do template**. Builders inline só pra extensões.

## Referência técnica

Detalhamento completo dos 25 slides do modelo, tokens, tipografia, posições canônicas em `${CLAUDE_PLUGIN_ROOT}/docs/metta-pptx-canonico.md`.

## Versão

`metta-deck v1.0.0` · 2026-05-26 · plugin Claude Code · template embarcado.
