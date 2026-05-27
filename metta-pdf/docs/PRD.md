---
title: "metta-pdf · plugin Claude Code pra geração de PDF institucional Metta"
aliases:
  - Plugin metta-pdf
  - Pipeline PDF Metta
  - Claude Plugin Metta PDF
tags:
  - arquitetura/plugin
  - arquitetura/claude-code
  - tipo/prd
  - tema/pdf
  - tema/automacao
  - tema/imagens
  - marca/metta
  - usado-por/squad-criacao
  - prioridade/alta
formato_consumo: doc_operacional
prioridade_carregamento: alta_demanda
versao: 1.0
status: aprovado-em-construcao
created: 2026-05-27
updated: 2026-05-27
relacionado:
  - "[[claude-plugin-metta-deck]]"
  - "[[refactor-plugin-pptx-design-aware]]"
  - "[[ai-ad-generation-system]]"
summary: "PRD do plugin Claude Code `metta-pdf` que gera PDFs institucionais Metta a partir de DOCX/Markdown, com geração de imagens AI integrada (nano-banana CLI / Gemini Flash Image) e renderização HTML→PDF via Chrome headless. Validado em piloto Visualize o Cenário (mai/2026) — 9 páginas, 7 imagens, 5min de execução."
---

## TL;DR

Plugin Claude Code privado da Metta que automatiza geração de PDFs editoriais (treinamento, relatório, deck PDF) seguindo o design system. Input é DOCX ou Markdown; output é PDF + imagens AI nas seções editorialmente relevantes. Time instala 1× e roda `/criar-pdf-metta path/to/brief.docx`.

**Status:** PRD aprovado 2026-05-27 · piloto validado · build em 3 sprints (~3 dias).

**Validação prévia:** PDF "Visualize o Cenário" (treinamento de vendedores de loja de posto) gerado manualmente em 27/mai/2026 — 9 páginas, 7 imagens (Gemini Flash Image), tempo total ~5min, custo ~$0.50. Resultado em `Branding Metta 2.0/output/visualize-o-cenario/`.

## §1. Contexto e motivação

### 1.1 Lacuna atual
Plugin `metta-deck` já cobre PPTX institucional via copy-and-substitute. Não cobre formatos PDF editoriais (treinamento, e-book, relatório, manual operacional, módulo de curso). Esses materiais hoje são feitos manualmente — Figma, Word→PDF, etc — sem aplicar o DS com consistência.

### 1.2 Oportunidade
1. Time tem pelo menos 4-6 entregas/mês desse tipo (treinamentos para clientes, módulos de mentoria, manuais, propostas long-form).
2. Pipeline de imagens já existe (nano-banana CLI + Gemini Flash Image), comprovado em ads.
3. HTML→PDF via Chrome headless é simples, replicável, e dá controle total sobre tipografia e DS.
4. Validação manual (Visualize o Cenário) mostrou que é viável produzir PDF editorial premium em <10min com este fluxo.

### 1.3 Audiência
Squad de Criação Metta (2-3 pessoas) + Head de Design + eventualmente o resto do time que produz conteúdo institucional. Todos já têm Claude Code instalado.

## §2. Escopo MVP

| Item | MVP v1.0 | Pós-MVP |
|---|---|---|
| Tipos de documento | **1 template — Treinamento editorial** | Relatório, Apresentação executiva, E-book, Manual |
| Input | DOCX, Markdown | YAML estruturado, conversação livre |
| Marca | Metta institucional | Multi-marca (Tiago, clientes) |
| Imagens | Gemini Flash Image via nano-banana CLI | gpt-image-1 fallback, img2img com refs |
| Fluxo imagens | Sugerir + aprovar | Auto-modo, manual via `[imagem]` no brief |
| Idiomas | PT-BR | EN opcional |
| Distribuição | Plugin Claude Code privado | Integração Brand System (UI web) |

### 2.1 Definições MVP

**Treinamento editorial** = documento de 5-15 páginas, com estrutura tipo: capa + abertura + N seções de fundamento + 2-N perfis/personas + conclusão. Foi o tipo do piloto.

**Sugerir + aprovar** = plugin propõe N pontos de imagem com prompts já engineered; user aprova/edita/remove antes da geração. Equilibra velocidade e controle.

### 2.2 Fora de escopo (v1.0)
- Edição interativa pós-geração (regenerar uma imagem específica, mexer em copy)
- Suporte a gráficos/charts (números, dashboards)
- Tabelas complexas com formatação custom
- Internacionalização
- Marca Tiago Alves ou clientes — só Metta institucional

## §3. Arquitetura

### 3.1 Decisão: plugin Claude Code

**Por quê plugin (vs CLI standalone, vs web app):**
- Time já está no fluxo Claude Code. Zero ferramenta nova pra aprender.
- Distribuição já resolvida pelo marketplace privado `metta-brasil-tech/claude-plugins`.
- Atualização via `claude plugin upgrade` — não precisa redeployer.
- Orquestração multi-step (parse → suggest → approve → generate → render) é exatamente o que skills Claude fazem bem.
- Retry automático via subagent quando nano-banana CLI dá timeout (vimos 2× no piloto).

**Por quê NÃO CLI standalone:** perde orquestração conversacional, exige aprender outra ferramenta, retry fica manual.

**Por quê NÃO web app primeiro:** muito mais trabalho de build, MVP fica lento. UI web é fase 2 (integrar como aba do Brand System).

### 3.2 Estrutura do plugin

```
metta-brasil-tech/claude-plugins/
└── metta-pdf/
    ├── manifest.json                  # versão 1.0.0, dependências (chrome, nano-banana CLI)
    ├── README.md                      # install + uso + troubleshooting
    ├── skills/
    │   ├── criar-pdf-metta.md         # orquestrador principal (Sonnet)
    │   └── sugerir-imagens-pdf.md     # subskill da fase 3 (sugestão + aprovação)
    ├── templates/
    │   ├── base.html                  # HTML shell + tokens + logo SVG inline
    │   └── layouts/                   # 6 padrões validados no piloto
    │       ├── cover.html             # background-image full-bleed + overlay + headline yellow accent
    │       ├── opener-spread.html     # text + image 1:1 com badge
    │       ├── hero-strip.html        # banner horizontal 21:6 com caption overlay
    │       ├── profile-spread.html    # magazine 2-col (foto 4:5 esquerda + conteúdo direita)
    │       ├── quote-photo.html       # quote com imagem background + overlay dark + mark yellow
    │       └── content-only.html      # tipografia + cards (compare block, grid de cards, qtable, callout)
    ├── tokens/
    │   ├── metta-ds.css               # tokens completos (cores, tipografia, shape, spacing, elevation)
    │   └── logo-symbols.svg           # M + variantes (light/dark) usando currentColor
    ├── pipeline/
    │   ├── parse_brief.py             # DOCX (python-docx) / MD (markdown lib) → AST de seções
    │   ├── select_layout.py           # heurística seção → template (por título/estrutura)
    │   ├── suggest_images.py          # propõe pontos editoriais + prompts inicial (usa nano-banana skill como sub-prompt)
    │   ├── generate_images.py         # nano-banana CLI paralelo + retry (timeout → prompt encurtado)
    │   ├── render_html.py             # AST + layouts → HTML completo
    │   └── render_pdf.py              # Chrome headless wrapper (user-data-dir isolado, --no-pdf-header-footer)
    ├── prompt-presets/
    │   ├── 8-layers-metta.md          # frame canônico do skill nano-banana
    │   └── arquetipos-treinamento.md  # 21 arquétipos da direção fotográfica (caminhoneiro, executivo, atendente etc)
    └── scripts/
        ├── setup-check.sh             # valida Chrome / Edge, nano-banana CLI no PATH, GEMINI_API_KEY
        └── install.sh                 # auto-instala nano-banana CLI via npm se faltar
```

### 3.3 Stack técnico

| Camada | Tecnologia | Por quê |
|---|---|---|
| Orquestração | Skill Claude Code (Sonnet) | Já é o fluxo do time |
| Parser DOCX | python-docx | Padrão da Metta (validado em piloto e em conversao-estrutural) |
| Parser MD | markdown-it-py | Suporte a frontmatter + extensões |
| Image gen | nano-banana CLI (Gemini 2.5 Flash Image) | Custo baixo (~$0.07/img), rápido (~30-60s), qualidade boa |
| HTML render | Template Python (Jinja2 ou f-string) | Sem build step, simples |
| PDF render | Chrome headless `--print-to-pdf` | Sem dependências extras, controle total via CSS |

## §4. Fluxo de uso (conversacional)

```
USER:  /criar-pdf-metta path/to/02_treinamento.docx

PLUGIN: Encontrei 9 seções no DOCX. Sugiro este mapeamento de layout:
        1. Capa                                  → cover
        2. Cada Atendimento É Único              → opener-spread
        3. Como Perguntar                        → content-only (compare block)
        4. Por Que Perguntas Abertas Funcionam   → content-only (grid 6 cards)
        5. Como Visualizar o Cenário             → hero-strip
        6. Perfil 1 — Caminhoneiro Autônomo      → profile-spread
        7. Perfil 2 — Motorista Particular       → profile-spread
        8. Perfil 3 — Motorista de Frota         → profile-spread
        9. Como Ganhar a Permissão               → quote-photo

        Aprovar ou ajustar?

USER:  ok

PLUGIN: Sugiro 4 pontos editoriais pra gerar imagem:

        • Pág 1 — Capa: interior loja de posto + atendente em ação
        • Pág 2 — Abertura: atendente conversando com caminhoneiro
        • Pág 6 — Perfil 1: caminhoneiro autônomo ao lado do caminhão
        • Pág 7 — Perfil 2: executivo no posto, café na mão
        • Pág 8 — Perfil 3: motorista de frota com tablet
        • Pág 9 — Permissão: momento de conexão atendente+cliente

        São 6 imagens. Custo estimado ~$0.42. Aprovar tudo, escolher quais, ou editar prompts?

USER:  todas

PLUGIN: Gerando 6 imagens em paralelo via nano-banana...
        [✓] cover-loja-posto.jpeg (54s)
        [✓] pg2-atendimento.jpeg (38s)
        [✓] perfil-1-caminhoneiro.jpeg (47s)
        [⟳] perfil-2-executivo.jpeg... (em geração)
        [✓] perfil-3-frota.jpeg (41s)
        [✓] pg9-permissao-conexao.jpeg (52s)
        [⚠] perfil-2-executivo timeout, tentando prompt encurtado...
        [✓] perfil-2-executivo.jpeg (33s, retry OK)

        Renderizando HTML + PDF...

PLUGIN: ✓ Saída em output/02_treinamento/
        ├── 02_treinamento.pdf (5.8 MB · 9 páginas)
        ├── visualize-o-cenario.html (fonte editável)
        └── img/ (6 JPEGs)
```

## §5. Pipeline interno

### 5.1 Fases

```
brief.docx
    ↓ [parse_brief.py]
seções [{titulo, body, tipo, tags}]
    ↓ [select_layout.py — heurística]
seções com layout assignment
    ↓ [user approval — turn 1]
    ↓ [suggest_images.py — usa nano-banana skill como sub-prompter]
points-of-interest [{section_id, layout, prompt_seed}]
    ↓ [user approval — turn 2]
    ↓ [generate_images.py — paralelo + retry]
JPEGs em output/img/
    ↓ [render_html.py — Jinja templates]
visualize-o-cenario.html
    ↓ [render_pdf.py — Chrome headless]
output/02_treinamento.pdf
```

### 5.2 Heurística layout (`select_layout.py`)

| Padrão na seção | Layout sugerido |
|---|---|
| Primeiro nó, título curto, alta hierarquia | cover |
| Lede longo + comparação + bullets | opener-spread |
| Grid de 6+ itens curtos (cards numerados) | content-only (grid) |
| Comparação dual (vs, ou-ou, antes/depois) | content-only (compare block) |
| Persona/perfil + atributos + descrição | profile-spread |
| Citação direta entre aspas (>=20 palavras) | quote-photo |
| Seção transitória curta (intro perfis) | hero-strip |

Heurística falha → pergunta ao user.

### 5.3 Retry policy de imagens

- 1ª tentativa: prompt completo (8 camadas, ~200 palavras)
- Timeout (>2min): retry com prompt encurtado (~120 palavras)
- 2º timeout: registra falha, entrega placeholder com descrição visível em fundo cinza
- Cada imagem rodada em background separado em paralelo

## §6. Distribuição & onboarding

### 6.1 Instalação (1× por máquina)

```bash
# 1. Adicionar marketplace privado
claude plugin marketplace add metta-brasil-tech/claude-plugins

# 2. Instalar plugin
claude plugin install metta-pdf

# 3. Validar ambiente
metta-pdf setup-check
# → ✓ Chrome encontrado em C:\Program Files\Google\Chrome\Application\chrome.exe
# → ✓ Python 3.11 OK
# → ✓ python-docx instalado
# → ⚠ nano-banana CLI não encontrado — instalando via npm...
# → ✓ nano-banana v2.1 instalado em ~/.local/bin
# → ⚠ GEMINI_API_KEY não definido — cole aqui ou export em ~/.zshrc:
#     [user cola]
# → ✓ Setup completo. Rode `/criar-pdf-metta` em qualquer projeto.
```

Tempo total: 2-3min.

### 6.2 Onboarding do time (10min de screencast)

Vídeo curto cobrindo:
1. O que o plugin faz (1min)
2. Instalação (1min)
3. Demo end-to-end: brief docx → PDF pronto (5min)
4. Como ajustar prompts de imagem (2min)
5. Onde ler o doc operacional (1min)

Hospedar no Drive da Metta + link no README do plugin.

### 6.3 Quando falar com o usuário (UX)

Plugin pergunta em 2 pontos:
- **Após parse**: mostra mapeamento seção→layout, pede aprovação
- **Antes de gerar imagens**: mostra pontos sugeridos com prompt-base, pede aprovação/edição

Resto é silencioso (progresso por linha de log).

## §7. Build plan

### Sprint 1 — Core pipeline (~1 dia)

**Objetivo:** regenerar o piloto Visualize o Cenário a partir do DOCX, sem imagens novas (usa as 7 já geradas).

- [ ] Extrair `base.html` + 6 layouts do piloto pra `templates/`
- [ ] Empacotar `metta-ds.css` + `logo-symbols.svg`
- [ ] `parse_brief.py` — DOCX → AST com python-docx
- [ ] `select_layout.py` — heurística básica
- [ ] `render_html.py` — Jinja templates
- [ ] `render_pdf.py` — Chrome headless wrapper (auto-detect Chrome path)
- [ ] Skill `/criar-pdf-metta` hardcoded sem fase de imagens
- [ ] Validar: rodando o DOCX original do piloto, gerar PDF idêntico ao manual

**Critério de aceitação:** PDF gerado tem 9 páginas, todas as imagens nos lugares certos, layout fiel ao piloto.

### Sprint 2 — Imagens com aprovação (~1 dia)

**Objetivo:** plugin sugere pontos editoriais, user aprova, plugin gera imagens em paralelo.

- [ ] `suggest_images.py` — heurística por tipo de seção
- [ ] Integrar skill `nano-banana` como sub-prompter (passa contexto editorial + tipo de cena)
- [ ] Fase 2 do skill orquestrador: mostrar sugestões + aceitar edits
- [ ] `generate_images.py` com timeout/retry
- [ ] Integrar imagens no HTML antes do render PDF
- [ ] Validar: regenerar o piloto do zero (brief → PDF + imagens em ~5min)

**Critério de aceitação:** o doc final é visualmente equivalente ao piloto manual.

### Sprint 3 — Distribuição (~1 dia)

**Objetivo:** publicar no marketplace, time consegue instalar e rodar em outra máquina.

- [ ] `manifest.json` + push pro repo `claude-plugins`
- [ ] `setup-check.sh` (detect Chrome, install nano-banana via npm, prompt GEMINI_API_KEY)
- [ ] `install.sh` auto-install dependências
- [ ] README.md completo (install + uso + troubleshooting)
- [ ] Screencast 5min hospedado no Drive
- [ ] Doc no vault (este aqui) + post no canal #criacao do time
- [ ] Tag versão `metta-pdf@1.0.0`

**Critério de aceitação:** outra pessoa do time instala em máquina nova e gera um PDF sem ajuda do builder.

## §8. Decisões e tradeoffs

### Por quê Gemini Flash Image e não gpt-image-1?
- 5-10× mais barato ($0.07 vs $0.40)
- 3-5× mais rápido (~45s vs ~3min)
- Qualidade comprovada nos 7 imagens do piloto
- Squad já tem `nano-banana` CLI configurada
- **Limitação:** menos controle de marcas no fundo (Petrobras/BMW apareceram). Mitigação: prompts mais explícitos + opção de regenerar.

### Por quê não usar img2img com refs?
- MVP: cenas conceituais (não pessoas específicas como Tiago)
- 70-85% fidelidade do reference-only não é necessária aqui — são personas genéricas
- Fica na fase pós-MVP se quiserem consistência entre imagens

### Por quê Jinja em vez de React/Vue?
- Sem build step, sem node_modules, sem hot reload
- Plugin distribuído via git — Jinja Python já está disponível
- Templates HTML/CSS puros são editáveis por designer sem dev tooling

### Por quê height:297mm + overflow:hidden em cada .page?
- Garante que cada seção HTML = 1 página física no PDF
- Footer fica no lugar certo (margin-top:auto em flex)
- Trade: conteúdo que não cabe é clipado (não auto-pagina pra próxima). Mitigação: heurística de tamanho + split intencional no parser.

## §9. Riscos & mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Timeout nano-banana CLI | Alta (vimos 2/7 no piloto) | Médio | Retry com prompt encurtado + placeholder visível como fallback |
| Marcas reais no fundo das fotos | Média | Baixo | Prompt explícito "no readable brands" + flag de regen 1-clique |
| DOCX livre sem estrutura clara | Alta | Alto | Plugin pergunta ao user quando heurística falha (não chuta) |
| Chrome path varia entre máquinas | Média | Alto | Setup-check detecta automaticamente (Chrome > Edge > Chromium) |
| Image overflow estourando 297mm | Baixa | Médio | Validar dimensões na renderização + warning se conteúdo > 257mm úteis |
| GEMINI_API_KEY ausente/expirada | Baixa | Alto | Setup-check valida com call dummy; warning no início do fluxo se faltar |

## §10. Próximas fases (pós-MVP)

### Fase 2 — Multi-template
- Relatório (long-form, tabelas, gráficos)
- Apresentação executiva PDF (formato horizontal, slide-like)
- E-book (capa + capítulos + colofão)

### Fase 3 — Multi-marca
- Marca pessoal Tiago Alves (paleta steel + coral, fonte cursive nas assinaturas)
- Cliente white-label (parametrizar logo + paleta + fontes)

### Fase 4 — UI web no Brand System
- Aba `/criar/pdf` no mini-app
- Drag-drop de DOCX
- Preview ao vivo de cada página
- Edição inline de prompts de imagem
- Histórico de PDFs gerados

### Fase 5 — Img2img / consistência
- Usar refs canônicas pra manter consistência entre as fotos de um mesmo PDF
- LoRA Flux pra personas recorrentes (ex: vendedor padrão Metta)

## §11. Métricas de sucesso

| Métrica | Baseline manual | Target v1.0 |
|---|---|---|
| Tempo de produção (brief → PDF) | 4-6h (Word→PDF tradicional) | <15min |
| Custo por PDF (10 páginas, 5 imagens) | R$ 0 (mão de obra interna) | ~R$ 2,50 (USD 0.50 em API) |
| Consistência com DS | 60-70% (depende da pessoa) | >95% (templates travados) |
| Adoção pelo time | 0/3 pessoas | 3/3 em 30 dias |
| PDFs produzidos via plugin | 0/mês | ≥4/mês até 60 dias |

## §12. Documentos relacionados

- [[claude-plugin-metta-deck]] — plugin irmão (PPTX). Padrão de distribuição e estrutura usado aqui.
- [[refactor-plugin-pptx-design-aware]] — refator em curso do plugin PPTX. Ideias migrarão pra metta-pdf.
- [[ai-ad-generation-system]] — sistema model-agnostic de geração de imagens. nano-banana CLI vem dali.
- [[playbook-ad]] · [[playbook-slide]] — playbooks operacionais de outras peças. Modelo pra criar playbook-pdf depois.
- Skill `/nano-banana` em `~/.claude/skills/nano-banana.md` — prompt engineer pra imagens (8 camadas).
- Piloto validado em `Branding Metta 2.0/output/visualize-o-cenario/` (mai/2026).

## §13. Changelog

| Data | Versão | Mudança |
|---|---|---|
| 2026-05-27 | 1.0 | PRD inicial após piloto manual Visualize o Cenário. Escopo MVP fechado: 1 template (treinamento), input DOCX/MD, imagens sugerir+aprovar via Gemini Flash. Build em 3 sprints. |
