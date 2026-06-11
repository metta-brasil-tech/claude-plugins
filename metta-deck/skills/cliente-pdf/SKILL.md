---
name: cliente-pdf
description: Use quando o user pedir pra criar/gerar/montar/produzir um documento PDF para um CLIENTE da Metta na identidade visual DO CLIENTE (white-label) — manual, livro de operações, checklist, procedimento, relatório, comunicado. Motor único marca-aware: a marca do cliente vive numa pasta (cores, fontes, logo, header/footer) e o conteúdo vem num JSON de blocos. Não usar pra PDF institucional Metta (use /criar-pdf-metta) nem pra PPTX (use /criar-slide-metta).
---

# Cliente PDF

Gera documentos **PDF na identidade visual do CLIENTE** (white-label), não da Metta.

Motor único `build.py` que separa **marca** de **conteúdo**:
- **Marca** → uma pasta por cliente (`brand.json` com cores/fontes/header/footer + `assets/` + `fonts/`). Define uma vez.
- **Conteúdo** → um JSON de **blocos** (parágrafo, lista, checklist, tabela, callout, imagem…).
- **Render** → HTML+CSS → Chrome/Edge headless → PDF. Mesmo pipeline do `/criar-pdf-metta`, mas a pele é do cliente.

Generaliza o gerador bespoke feito pra MIME (Livro Diário de Operações).

## Quando usar

- Documento operacional pro cliente do cliente (manual, livro de operações, checklist, POP)
- Comunicado / procedimento / relatório na marca do cliente
- Qualquer one-pager ou multi-página PDF que precise sair com a identidade DO CLIENTE

## Quando NÃO usar

- PDF institucional **Metta** (editorial, treinamento) → `/criar-pdf-metta`
- Apresentação / deck → `/criar-slide-metta`
- Ads, carrosséis → `/criar` ou `/design-metta`

## Fluxo

### 1. Identificar o cliente e checar se a marca já existe

Pergunte qual cliente e se já existe uma pasta de marca dele. As marcas de cliente
vivem **no vault** (ex.: `work/active/<cliente>/marca-pdf/`), nunca dentro do plugin
(o cache do plugin é sobrescrito a cada update).

### 2. Marca nova → criar a pasta a partir do _template

Copie a pasta-base embarcada e edite:

```bash
cp -r "${CLAUDE_PLUGIN_ROOT}/scripts/cliente-pdf/_template" <destino>/<cliente>
```

Depois:
- **assets/** → `logo.png` (PNG transparente, qualidade vetorial) e, se houver, `footer.png` (faixa full-bleed).
  Extraia do material do cliente como **PNG vetorial** (não rasterize a página).
- **fonts/** → `.ttf`/`.otf` da marca. **Fonte precisa ser arquivo local** — `@import` do Google Fonts NÃO carrega em print-to-pdf headless. Se a fonte for proprietária e indisponível, use um substituto geométrico (Inter/Montserrat) e anote em `brand.json._fontes_originais`.
- **brand.json** → preencha:
  - `colors` (primary, accent, text, heading, muted, rule)
  - `fonts.display` / `fonts.body` (family + file)
  - `header.type`: `gradient` | `solid` | `image` | `none` (+ background/height/logo/title_color/title_size)
  - `footer.type`: `image` | `text` | `none`
- **brand.css** → ajustes finos opcionais (tamanhos/espaçamentos). Pode ficar vazio.

Mostre o `brand.json` preenchido pro user validar antes de gerar.

### 3. Montar o conteúdo (JSON de blocos)

Estrutura raiz:
```json
{ "title": "Título do header", "auto_number_sections": true, "blocks": [ ... ] }
```

Blocos: `greeting`, `section` (auto-numerável), `heading` (1–3), `paragraph`,
`list` (bullet/number/check), `keyvalue`, `table`, `image`, `callout`, `divider`, `spacer`.
Inline em qualquer texto: `**negrito**`, `*itálico*`.

Referência completa: `${CLAUDE_PLUGIN_ROOT}/scripts/cliente-pdf/schema.md`.
Exemplo demonstrando todos os blocos: `${CLAUDE_PLUGIN_ROOT}/scripts/cliente-pdf/examples/showcase-blocos.json`.

### 4. Gerar o PDF

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/cliente-pdf/build.py" \
  "<destino>/<cliente>" \
  ./conteudo.json \
  ./<cliente>-documento.pdf
```

O 1º argumento é o **caminho da pasta da marca** (recomendado). Alternativamente,
um nome resolvido via env `METTA_CLIENTE_PDF_BRANDS` ou pasta atual.

Header e rodapé repetem automaticamente a cada página (técnica `thead`/`tfoot`).

### 5. Validar visualmente e entregar

- Renderize a página 1 (PyMuPDF: `fitz.open(pdf)[0].get_pixmap(dpi=110).save(png)`) e confira
  contra o material de referência do cliente — DNA visual (header, cores, fontes, logo, rodapé).
- Entregue o caminho do PDF + resumo.
- Se vault disponível, salve um doc descritivo em `work/active/<cliente>/`.

## Anti-padrões

- ❌ **Não criar a marca do cliente dentro do plugin** (`scripts/cliente-pdf/`). Sempre no vault — o plugin é sobrescrito em update.
- ❌ **Não usar fonte via Google Fonts `@import`** — não carrega em headless. Sempre arquivo local em `fonts/`.
- ❌ **Não rasterizar a página** do material do cliente pra extrair logo/ornamento — extrair como PNG vetorial transparente.
- ❌ Não inventar conteúdo. Só o que o user/briefing fornece.
- ❌ Não aplicar identidade Metta em documento de cliente (este é o oposto do `/criar-pdf-metta`).

## Estrutura embarcada

```
scripts/cliente-pdf/
  build.py            # motor (CLI: build.py <marca|caminho> <content.json> [out.pdf])
  base.css            # layout + blocos (marca-agnóstico, usa CSS vars)
  schema.md           # referência do JSON de conteúdo
  _template/          # pasta-base pra copiar (brand.json + brand.css + assets/ + fonts/ + LEIA-MEs)
  examples/
    showcase-blocos.json
```

## Versão

`cliente-pdf v1.0.0` · 2026-06-11 · skill do plugin metta-deck.
- Motor marca-aware (separa marca de conteúdo) + 11 blocos. Generaliza o gerador MIME.
