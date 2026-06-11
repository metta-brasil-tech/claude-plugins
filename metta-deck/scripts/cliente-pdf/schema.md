# Schema do conteúdo (`content.json`)

Estrutura raiz:

```json
{
  "title": "Título exibido no header",
  "auto_number_sections": true,
  "blocks": [ ...blocos... ]
}
```

- `title` — texto do header (some se vazio e header não tiver título).
- `auto_number_sections` — `true` numera os blocos `section` de nível superior (1., 2., …).
- `blocks` — array, renderizado na ordem.

**Inline em qualquer texto:** `**negrito**` e `*itálico*`.

## Blocos

### `greeting` — saudação de abertura
```json
{ "type": "greeting", "title": "Olá, tudo bem?", "text": "Texto introdutório." }
```
`title` e `text` são opcionais.

### `section` — agrupador com título (recebe número se `auto_number_sections`)
```json
{ "type": "section", "title": "Nome da seção", "blocks": [ ...blocos aninhados... ] }
```
Atalho compatível com o MIME (checklist direto na seção):
```json
{ "type": "section", "title": "...", "style": "check",
  "items": [ { "term": "Termo", "desc": "descrição" } ] }
```

### `heading` — título solto (fora de seção)
```json
{ "type": "heading", "level": 2, "text": "Título" }   // level 1, 2 ou 3
```

### `paragraph`
```json
{ "type": "paragraph", "text": "Texto com **negrito** e *itálico*." }
```

### `list` — `bullet` (padrão), `number` ou `check`
```json
{ "type": "list", "style": "bullet", "items": ["a", "b", "**c**"] }
{ "type": "list", "style": "number", "items": ["passo 1", "passo 2"] }
{ "type": "list", "style": "check",
  "items": [ { "term": "Tarefa", "desc": "detalhe" }, "item sem termo" ] }
```
Itens podem ser string OU `{ "term", "desc" }` (term vira negrito + dois-pontos).

### `keyvalue` — alias de `list` com `style:"check"` (legado MIME)
```json
{ "type": "keyvalue", "items": [ { "term": "Chave", "desc": "valor" } ] }
```

### `table`
```json
{ "type": "table",
  "headers": ["Col A", "Col B"],
  "rows": [ ["a1", "b1"], ["a2", "b2"] ] }
```
`headers` é opcional. Faixa colorida usa `colors.primary`; linhas pares com zebra.

### `image`
```json
{ "type": "image", "src": "assets/foto.png", "width": "100%", "caption": "Legenda (opcional)" }
```
`src` relativo à pasta da marca (coloque a imagem em `brands/<marca>/assets/`).

### `callout` — bloco de destaque
```json
{ "type": "callout", "title": "Atenção", "text": "Observação importante." }
```

### `divider` — régua horizontal
```json
{ "type": "divider" }
```

### `spacer` — espaço vertical
```json
{ "type": "spacer", "size": "16pt" }
```
