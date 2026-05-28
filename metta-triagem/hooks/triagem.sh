#!/bin/bash
# UserPromptSubmit hook — triagem heurística de complexidade pra rotear modelo.
# Lê JSON do stdin, classifica o prompt por padrões léxicos, injeta dica de
# delegação no contexto quando relevante. Zero custo, instantâneo.
#
# Saída em stdout vai como contexto adicional pro Claude principal.
# Exit 0 sempre (nunca bloqueia o prompt).

set -euo pipefail

# Lê o JSON do hook via stdin
input=$(cat)

# Extrai o prompt. Tenta python3 (Mac/Linux) e cai pra python (Windows/Git Bash).
read_prompt() {
  printf '%s' "$1" | "$2" -c "import sys,json; print(json.load(sys.stdin).get('prompt',''))" 2>/dev/null
}
prompt=$(read_prompt "$input" python3 || read_prompt "$input" python || echo "")

# Skip prompts triviais ou vazios (confirmações, "ok", "sim", etc.)
prompt_len=${#prompt}
if [ "$prompt_len" -lt 25 ]; then
  exit 0
fi

# Skip se prompt já invoca subagent/skill explicitamente
if echo "$prompt" | grep -qiE "^/(triagem|metta-triagem:triagem|design-metta|copy-metta|conteudo-|gestor-criativo|nano-banana|roteirizar|lp-metta|ultrareview)|task tool|invoke.+agent|use.+haiku|use.+sonnet|use.+opus"; then
  exit 0
fi

# Lowercase pra matching case-insensitive (PT-BR + EN)
p=$(echo "$prompt" | tr '[:upper:]' '[:lower:]')

# ============ HARD RULES (forçam Sonnet+, mesmo se "simples") ============
# Copy/conteúdo Metta ou Tiago, decisões de design, code review cross-arquivo
if echo "$p" | grep -qE "(copy metta|copy tiago|conteúdo metta|conteúdo tiago|conteudo metta|conteudo tiago|carrossel metta|ad metta|ad tiago|story metta|landing.?page|prd|arquitetura|estratégia|estrategia|rebranding|trade.?off|melhor abordagem|qual o melhor|code review|auditoria|audit |refator|refactor)"; then
  cat <<'EOF'

[triagem-auto] Tarefa exige raciocínio editorial/arquitetural — mantenha em Sonnet/Opus. Não delegar pra Haiku.
EOF
  exit 0
fi

# ============ SIMPLE PATTERNS (sugerir delegação Haiku) ============
simple_match=""

# Rename/format/lookup mecânico
if echo "$p" | grep -qE "(renomei|renomear|rename |format |formata|substitui|find.+replace|busca.+substitui|trocar.+por|encontre.+arquivo|liste.+arquivos|liste os )"; then
  simple_match="rename/format/lookup mecânico"
fi

# Sumário/resumo de texto
if echo "$p" | grep -qE "(resum|sumariz|summarize|tldr|tl;dr|bullet.?points|em bullets|principais pontos|extraia os|me d. um resumo)"; then
  simple_match="resumo/sumário"
fi

# Classificação/triagem
if echo "$p" | grep -qE "(classific|categoriz|triagem|priorize|ordene por|tag.?ueia|rotule)"; then
  simple_match="classificação"
fi

# Lookup/leitura simples
if echo "$p" | grep -qE "^(o que (é|tem|diz)|qual (é|o)|onde (está|fica|tá)|me mostr|me d. |abra |abre o|leia |veja o conteúdo)"; then
  simple_match="lookup/leitura simples"
fi

# Validação de schema/JSON/syntax
if echo "$p" | grep -qE "(valida.+json|valida.+schema|valida.+yaml|tem erro de sintaxe|parse.+erro)"; then
  simple_match="validação mecânica"
fi

if [ -n "$simple_match" ]; then
  cat <<EOF

[triagem-auto] Padrão detectado: $simple_match. Considere delegar pra subagent Haiku via Task (quick-classifier ou text-summarizer) pra economizar tokens (~15× mais barato). Pular se a tarefa exigir contexto cross-arquivo ou raciocínio editorial.
EOF
  exit 0
fi

# ============ COMPLEX PATTERNS (confirmar Opus) ============
if echo "$p" | grep -qE "(decid|decisão|trade.?off|comparar.+(a|b|c)|melhor abordagem|qual o melhor|arquitet|cross.?domínio|vários arquivos|múltipl|multipl)"; then
  cat <<'EOF'

[triagem-auto] Tarefa parece envolver decisão/arquitetura — Opus apropriado. Não delegar.
EOF
  exit 0
fi

# Default: silêncio (não polui contexto pra prompts médios óbvios)
exit 0
