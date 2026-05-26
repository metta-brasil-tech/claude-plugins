---
title: "Metta — PPTX Canônico (DNA do PPT Modelo Geral)"
aliases:
  - PPTX Canônico
  - DNA do Modelo Geral
tags:
  - design/pptx
  - design/tokens
  - usado-por/skill/criar-slide-metta
  - prioridade/alta
formato_consumo: doc_estrutural
prioridade_carregamento: alta_demanda
versao: 1.0
summary: "Especificação técnica DEFINITIVA do PPTX Metta extraída por análise shape-a-shape do PPT Modelo Geral.pptx (25 slides referência). Fonte da verdade pra builders.py e criar-slide-metta skill."
created: 2026-05-25
updated: 2026-05-25
---

## TL;DR

Esta é a especificação **canônica** do PPTX Metta. Extraída direto do `PPT Modelo - Geral.pptx` por análise shape-a-shape (script `c:/tmp/analyze_modelo_geral.py`). Toda decisão de layout, tipografia, cor, posição NESTE documento é AUTORIDADE FINAL sobre qualquer assumption anterior.

Se um valor canônico aqui difere de outro doc (incl. `metta-tokens.md`, `criar-slide-metta` SKILL, `prompt-pptx-metta-master.md`), **este vence**.

## Quando consultar

- ANTES de tocar qualquer builder em `builders.py`
- Validar fidelidade de output da skill `/criar-slide-metta`
- Treinar humanos/agentes em padrão Metta PPTX
- Briefar designer pra apresentação Metta no Figma/Canva

## §1. Canvas

| Atributo | Valor |
|---|---|
| Width | 13.333 in |
| Height | 7.500 in |
| Aspect | 16:9 widescreen |

## §2. Paleta canônica

### Backgrounds
| Token | Hex | Uso |
|---|---|---|
| **`bg-dark`** | `#0C161B` | BG slides escuros (capa dark, section divider, slides de prova/método) |
| **`bg-light`** | `#FFFFFF` | BG slides claros padrão |
| **`bg-light-cool`** | `#F2F7FC` | BG capa light (off-white frio · variação da capa) |

### Containers (cards/blocos)
| Token | Hex | Uso |
|---|---|---|
| **`container-dark`** | `#131F25` | Container/card sobre `bg-dark` (ex: cards da equação) |
| **`container-light`** | `#EBF3F7` | Container/card sobre `bg-light` (ex: logos no wall, KPI rows, cards equipe) |

### Texto sobre dark
| Token | Hex | Uso |
|---|---|---|
| **`text-on-dark-bold`** | `#F2F7FC` | Headline/title em slide dark (off-white frio) — preferido sobre `#FFFFFF` puro |
| **`text-on-dark-pure-white`** | `#FFFFFF` | Pure white — usado SÓ em casos específicos (ex: unidade de big number, section divider) |
| **`text-on-dark-muted`** | `#B0CAD8` | Body/subtítulos/eyebrow/footer em slide dark |

### Texto sobre light
| Token | Hex | Uso |
|---|---|---|
| **`text-on-light-bold`** | `#0C161B` | Headline/title em slide light |
| **`text-on-light-muted`** | `#435965` | Body/subtítulos/eyebrow/footer em slide light |
| **`text-on-light-soft`** | `#111E25` | Variante leve do bold (subline capa light) |

### Yellow
| Token | Hex | Uso |
|---|---|---|
| **`yellow-pure`** | `#FFBE18` | Brand primary · big numbers, ícones, accent line, card destaque pleno, arrow no light |
| **`yellow-soft`** | `#FFE4A1` | Primary container · uso RARO (não vi no modelo geral em momento canônico — manter como token mas usar só pra ANTES/DEPOIS) |

### Cor de texto em card yellow
Sobre `yellow-pure` (#FFBE18) o texto SEMPRE é `bg-dark` (#0C161B) — preto sobre amarelo.

## §3. Tipografia

### Família única (sem fallbacks)
| Role | Font family | Uso |
|---|---|---|
| **Heads** | `Zalando Sans Expanded` | Titles, big numbers, eyebrows, labels UPPER, CTA, números, siglas |
| **Heads variação 2** | `Zalando Sans SemiExpanded` | Subhead nível 2 (RARO — só em slide tipo "Em metas batidas nos últimos 12 meses" — slide 5) |
| **Body** | `Inter` | Body, parágrafos, subtítulos, captions, labels descritivas |

**SF Pro Expanded REMOVIDO da tipografia PPTX**. Só Zalando+Inter. Aliás dos tokens v2 `metta-tokens.md` (linha de "fontes Metta — lógica de pares") deve ser atualizado.

### Sizes canônicos (pt)

| Role | Size | Bold? | Cor |
|---|---|---|---|
| Capa display | 55 | bold (alternando regular pra ênfase editorial) | text-on-bg |
| Section divider title | 72 | bold | `#FFFFFF` puro (em dark) |
| Quem somos title (slide dedicado coluna estreita) | 70 | bold + regular alternados | `#FFFFFF` |
| Title content (slide padrão) | **30** | bold | text-on-light-bold ou text-on-dark-bold |
| Subtitle / subhead Inter | 12 | regular | text-on-*-muted |
| Subhead Zalando SemiExpanded | 24.7 | bold | `#B0CAD8` (dark) |
| Big number (valor) | 165.6 | bold | yellow-pure |
| Big number (unidade) | 174.9 | **regular** (não bold!) | `#FFFFFF` ou text-on-bg-bold |
| Equação variable label | 24 | bold | yellow-pure (sobre dark container) ou bg-dark (sobre yellow card) |
| Equação body in card | 11 | regular | `#FFFFFF` |
| Equação operador `× × =` | 36 | bold | `#B0CAD8` (muted no dark) |
| Card label (KPI sigla) | 14 | bold | text-on-light-bold |
| Card body Inter | 11-12 | regular | text-on-*-muted |
| Logo wall label | 14 | bold | `#435965` (NUNCA yellow) |
| Header eyebrow | **9** | bold | `#435965` (light) / `#B0CAD8` (dark) |
| Header cliente direita | 9 | bold | `#435965` (light) / `#B0CAD8` (dark) |
| Footer date/cliente/section (MAIN) | 8 | regular | `#435965` (light) / `#B0CAD8` (dark) |
| Footer (MICRO em foto bleed) | 6 | bold | `#FFFFFF` ou `#435965` |
| Footer arrow ↗ | 10 | bold | `#FFBE18` (light) / `#F2F7FC` (dark) — varia por theme |
| Capa eyebrow micro | 6 | bold | text-on-bg-muted |

### Truque editorial (split bold/regular em titles)

**Regra DEFAULT (titles de slide content):** title TODO bold. Primeira letra pode ficar em run separado mas weight = bold idêntico (artifício de tracking, sem variação visual).

**Regra EDITORIAL (titles especiais — quem somos, divider editorial, equação):** alterna bold em PALAVRAS-CHAVE e regular em CONECTIVOS.

Exemplos confirmados do modelo geral:
- Slide 4 (quem somos): `**Quem** somos` → "Quem" bold + " somos" regular
- Slide 6 (section divider editorial sobre foto): `**Somos** especialistas **em resultados.**` → 3 runs (bold + regular + bold)
- Slide 13 (equação): `A equação da **meta batida**` → "A equação da" regular + " meta batida" bold

**Implementação:** parametrizar como string markdown-like onde `**word**` = bold e o resto = regular. Quando o input não tem nenhum `**`, default = tudo bold.

## §4. Header canônico (3 variações)

### MAIN (slides padrão de conteúdo)
```
[LOGO 1.067×0.32]     EYEBROW 9pt bold anchor=MIDDLE      CLIENTE 9pt bold align=RIGHT
x=0.4 y=0.317         x=2.0 y=0.32 w=7.0 h=0.25            x=8.0 y=0.32 w=4.9 h=0.25
                                                                                  ↓
──────────────────────────── divider line ────────────────────────────
                                                                              y=0.72 x=0.4 w=12.5
```

### COMPACT (capa, splits)
```
[LOGO 0.903×0.25 — mini]    DATE 6pt bold anchor=TOP
x=0.556 y=0.389              x=11.944 y=0.444 w=0.584 h=0.111
```
(sem eyebrow/cliente full · sem divider · header levíssimo)

### MICRO (slides com foto editorial bleed)
Sem header tradicional. Apenas eyebrow micro:
```
EYEBROW 8pt bold
x=0.556 y=0.389 w=1.646 h=0.132
```

## §5. Footer canônico (3 variações)

### MAIN
```
──────────────────────────── divider line ─────────────────
                                                       y=7.0 x=0.4 w=12.5
DATE 8pt regular   CLIENTE 8pt regular   SECTION 8pt regular   ↗ 10pt bold
x=0.4 align=LEFT   x=5.5 align=CENTER    x=10.0 align=RIGHT     x=12.6 align=RIGHT
y=7.15 w=3.0 h=0.3 y=7.15 w=3.0 h=0.3    y=7.15 w=2.5 h=0.3     y=7.15 w=0.3 h=0.3
```

### COMPACT (capa, splits)
```
──────────────────────────── divider line ─────────────────
                                                       y=7.0 x=0.4 w=12.5
DATE 8pt    CLIENTE 8pt   SECTION 8pt   ↗ 10pt
y=7.15      y=7.15        y=7.15        y=7.15
h=0.135     h=0.135       h=0.135       h=0.168
```

### MICRO (slide com foto editorial bleed full)
```
DATE 6pt bold     CLIENTE 6pt bold     SECTION 6pt bold     → 10pt bold (não ↗!)
y=7.069 h=0.111   y=7.069 h=0.111      y=7.069 h=0.111      y=7.007 h=0.188
```

## §6. Layouts canônicos por tipo de slide

### 6.1 Capa dark (slide 1)
- BG: `bg-dark` (#0C161B)
- Picture ornamental: x=2.828 y=-2.134 w=10.661 h=10.429 (bleed superior direito)
- Logo mini: x=0.556 y=0.389
- Eyebrow date micro: x=11.944 y=0.444 size=6pt bold cor `#B0CAD8`
- Eyebrow secundário (opcional): "COMO VAMOS JUNTOS" 12pt bold cor yellow-pure
- HEADLINE big: x=0.54 y=2.616 w=6.784 h=2.502 (bloco lado ESQUERDO; PICTURE ocupa direita)
  - Size 55pt bold cor `#F2F7FC`
- Subline: x=0.67 y=4.464 w=5.21 h=0.417 Inter 10pt regular cor `#B0CAD8`
- Footer COMPACT (h=0.135)

### 6.2 Capa light (slide 2)
- BG: `bg-light-cool` (#F2F7FC)
- Mesma estrutura da capa dark
- Subline cor `#111E25` (variante leve em vez de #435965)
- Footer arrow ↗ cor `#B0CAD8` (não yellow!)

### 6.3 Section divider (slides 3, 10, 15, 19)
- 2 variações conhecidas:
  - **Slide 3** (yellow full bleed): BG `#FFBE18` (yellow!), title cor `#0C161B`
  - **Slide 10** (dark + clean): BG `bg-dark`, title cor `#FFFFFF` puro
- Title centralizado: x=0.4 y=3.169 w=12.5 h=1.151 align=CENTER size **72pt** bold
- Primeira letra em run separado mas AMBOS bold (não tem variação regular)
- Header MAIN + Footer MAIN
- Arrow ↗ cor yellow-pure em slides 10/15/19 (dark + section divider)

### 6.4 Quem somos / institucional dark (slide 4 — split coluna)
- BG: `bg-dark`
- LAYOUT DUAS COLUNAS:
  - Esquerda (x=0 a 4.785): texto sobre dark
  - Direita (x=4.986 a 13.333): bloco YELLOW + picture(s) editoriais (foto bleed)
- Logo: x=0.401 y=0.317
- Eyebrow header em y=0.362 h=0.152 size 9pt bold cor `#435965` anchor=MIDDLE
- Header divider PARCIAL: x=0.4 y=0.72 w=**4.385** (só lado esquerdo!)
- TITLE: x=0.556 y=2.525 w=4.034 h=1.375 size **70pt** bold cor `#FFFFFF`
  - 2 runs com variação: `**Quem** somos` (primeira palavra bold + segunda regular)
- Subline: x=0.556 y=4.604 w=3.771 h=0.812 Inter 13pt cor `#B0CAD8`
- Footer PARCIAL: divider y=7.0 w=**4.189** (só esquerda)
  - DATE y=7.15 + CLIENTE y=7.15 — sem section/arrow

### 6.5 Prova social big number (slide 5)
- BG: `bg-dark`
- Picture: x=7.167 y=0.583 w=6.264 h=8.891 (foto bleed direita)
- Header MAIN + Footer MAIN (h=0.3)
- Eyebrow body Zalando SemiExpanded: x=0.4 y=3.276 w=5.565 h=0.779
  - Size 24.7pt bold cor `#B0CAD8`
  - Pode ter 2 linhas: "Em metas batidas nos / últimos 12 meses:"
- BIG NUMBER (valor): x=0.4 y=4.472 w=9.62 h=2.351 Zalando Expanded **165.6pt** bold cor yellow
- BIG NUMBER (unidade): x=10.135 y=4.472 w=2.372 h=2.351 size **174.9pt regular** cor `#FFFFFF`
- Body caption secundário (opcional): x=9.655 y=3.352 w=3.21 h=0.534 Inter 12.4pt cor `#B0CAD8`

### 6.6 Section divider editorial com foto bleed (slide 6)
- BG: `bg-light` (#FFFFFF)
- Picture full canvas: x=-0.09 y=0 w=13.423 h=7.55
- Eyebrow micro: x=0.556 y=0.389 w=1.646 h=0.132 Zalando Expanded 8pt bold cor `#FFFFFF`
- TITLE editorial: x=0.373 y=3.949 w=6.784 h=2.502
  - Size **55pt** bold cor `#F2F7FC`
  - **3 runs:** `**Somos** especialistas **em resultados.**` (bold + regular + bold)
- Subline: x=10.306 y=5.649 w=2.88 h=0.802 Inter 12pt cor `#FFFFFF`
- Footer MICRO: h=0.111 size 6pt bold

### 6.7 Logo wall (slide 7)
- BG: `bg-light` (#FFFFFF)
- Header MAIN
- TITLE: x=0.4 y=1.683 w=12.5 h=0.969 size **36pt** bold align=CENTER cor `#0C161B`
- Grid 4×2 logos:
  - Card top row: y=3.393 w=2.715 h=1.024
  - Card bottom row: y=4.552 w=2.715 h=**1.172** (CARDS BOTTOM SÃO MAIS ALTOS!)
  - Gap horizontal entre cards: 2.875 - 2.715 = 0.16
  - Bg #EBF3F7
  - Label inside card: Zalando 14pt bold cor `#435965` align=CENTER anchor=MIDDLE
    - Top row text y=3.817 (offset 0.424 do topo)
    - Bottom row text y=5.034 (offset 0.482 do topo)
- Caption Setores: x=0.4 y=6.3 w=12.5 h=0.4 Inter 12pt cor `#435965` align=CENTER

### 6.8 Indicadores / KPIs (slide 11)
- BG: `bg-light` (#FFFFFF)
- Header MAIN + Footer MAIN
- TITLE: x=0.4 y=**1.1** w=12.5 h=**0.404** size **30pt** bold cor `#0C161B`
- Subtitle: x=0.4 y=1.8 h=0.4 Inter 12pt cor `#435965`
- Rows: y=2.6, 3.2, 3.8, 4.4, 5.0, 5.6 (step=0.6) cada h=0.5
  - Bg row: #EBF3F7
  - Icon "+": x=0.75 w=0.5 size **20pt** bold cor yellow anchor=MIDDLE align=CENTER
  - Sigla: x=1.4 w=2.0 size **14pt** bold cor `#0C161B` anchor=MIDDLE
  - Nome: x=3.6 w=8.8 size 12pt Inter regular cor `#435965` anchor=MIDDLE

### 6.9 Equação (slide 13)
- BG: `bg-dark`
- Header MAIN (h=0.152) + Footer MAIN
- TITLE: x=0.4 y=**1.35** w=12.5 h=1.024 align=CENTER size **38pt**
  - 4 runs (split editorial): `A equação da **meta batida**`
- 4 cards equação (3 vars + 1 resultado):
  - Card var (3 primeiros): w=2.5 h=2.2 bg `#131F25`
  - Card resultado (último): w=2.5 h=2.2 bg `#FFBE18` (yellow pleno)
  - **SEM top stripe yellow**
  - X positions: 0.616, 3.816, 7.016, 10.216 (step 3.2)
  - Label inside: x do card y=3.15 h=0.7 (ou 0.404 no card yellow) size **24pt** bold cor yellow (sobre dark) ou bg-dark (sobre yellow)
  - Body inside: y=4.05 h=0.9 Inter 11pt regular cor `#FFFFFF` align=CENTER
- Operadores `× × =`: x entre cards (3.116, 6.316, 9.516) y=3.6 h=0.606 size **36pt** bold cor `#B0CAD8`
- Body caption baixo: x=3.417 y=5.4 w=6.672 h=0.558 Inter cor `#B0CAD8`

### 6.10 Caso nominal (slide 14)
- (não totalmente analisado — abrir fichas slide-14.md pra detalhes)
- Padrão: 3 big numbers separados por dividers verticais + body parágrafo

### 6.11 Cronograma Gantt (slide 17)
- (49 shapes — slide mais complexo, abrir slide-17.md pra detalhes)

### 6.12 Antes/Depois (slide 18)
- (36 shapes — abrir slide-18.md)

### 6.13 Encerramento CTA (slide 19)
- (22 shapes — abrir slide-19.md)
- NB: NÃO usa anel concêntrico bottom-right (já que isso é anti-padrão §6.4)

### 6.14 Charts editáveis (slides 20-23)
- Bar grouped (slide 20, 39 shapes)
- Donut (slide 21, 12 shapes)
- Area (slide 22, 13 shapes)
- Waterfall (slide 23, 38 shapes)

### 6.15 Closer ecossistema (slides 24-25)
- Slide 24: 7 shapes — provavelmente foto + statement
- Slide 25: 6 shapes — versão dark

## §7. Anti-padrões CONFIRMADOS (NÃO usar)

Encontrados ausentes no modelo geral — não devem existir em deck Metta v2:

1. ❌ **Anéis concêntricos** (PRD §6.4) — confirmado: não há em nenhum slide
2. ❌ **Top stripe yellow em card** — confirmado: cards do modelo NÃO têm stripe (vi em meu builders.py v1 errado)
3. ❌ **Linha yellow accent 2.5pt sob title** (1.5in wide) — confirmado: não há em nenhum slide do modelo
4. ❌ **Eyebrow header em cor yellow** — confirmado: eyebrows são `#435965`/`#B0CAD8`, nunca yellow
5. ❌ **Yellow soft (#FFE4A1) como card highlight** — confirmado: highlight é YELLOW PLENO #FFBE18
6. ❌ **Title height 0.7in** — confirmado: títulos de 30pt cabem em 0.404 (h=0.5 max)
7. ❌ **Big number 190pt + body abaixo grudado** — confirmado: 165pt + unidade separada 175pt regular
8. ❌ **SF Pro Expanded** — não aparece em lugar nenhum do modelo

## §8. Mapping pra `builders.py`

| Builder | Status v3 (fiel ao modelo) | Slide do modelo de referência |
|---|---|---|
| `add_header(theme, mode='main')` | ⏳ refatorar com modo main/compact/micro | slides 5, 7, 11, 17 |
| `add_footer(theme, mode='main')` | ⏳ refatorar com 3 modos | slides 5, 7 vs 1, 4 vs 6 |
| `add_title_split(title_md)` | ⏳ parametrizar bold/regular via markdown-like | slides 4, 13 |
| `slide_capa` | ⏳ refatorar fiel ao slide 1 (sem anéis) | slide 1 |
| `slide_section_divider` | ⏳ refatorar (72pt sem yellow line) | slides 3, 10 |
| `slide_quem_somos` | ⏳ refatorar split column | slide 4 |
| `slide_prova_big_number` | ⏳ refatorar (165/175pt sep) | slide 5 |
| `slide_logo_wall` | ⏳ refatorar (rows altura diff) | slide 7 |
| `slide_depoimentos` | ✅ ok (slide 8 não analisado em detalhe ainda) | slide 8 |
| `slide_indicadores` | ⏳ refatorar (sigla 14pt #0C161B) | slide 11 |
| `slide_equacao` | ⏳ refatorar (sem top stripe, sizes) | slide 13 |
| `slide_caso` | ✅ ok | slide 14 |
| `slide_cronograma` | ⏳ analisar slide 17 | slide 17 |
| `slide_antes_depois` | ⏳ analisar slide 18 | slide 18 |
| `slide_encerramento` | ⏳ refatorar (sem arc bottom-right) | slide 19 |
| `slide_equipe` (v2 novo) | ✅ validado pelo user | – |
| `slide_roadmap` (v2 novo) | ✅ validado pelo user | – |
| `slide_timeline` (v2 novo) | ✅ validado pelo user | – |
| `slide_funnel` (v2 novo) | ✅ validado pelo user | – |
| `slide_faq` (v2 novo) | ✅ validado pelo user | – |
| `slide_pricing` (v2 novo) | ✅ validado pelo user | – |
| `slide_matriz_2x2` | ⚠️ experimental | – |
| `slide_hub_spoke` | ⚠️ experimental | – |

## §9. Outputs da análise

Material bruto disponível em `c:/tmp/modelo-geral-analysis/`:
- `index.md` — resumo dos 25 slides
- `patterns.md` — header/footer recorrentes
- `shapes-raw.json` — dump completo bruto
- `slide-XX.md` (×25) — ficha técnica detalhada slide-a-slide

## Conexões

[[reference-skill-criar-slide-metta]]
[[metta-tokens]]
[[prompt-pptx-metta-master]]
