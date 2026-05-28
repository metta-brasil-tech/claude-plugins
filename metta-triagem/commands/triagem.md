---
description: Triagem de complexidade pra escolher o modelo certo (Haiku/Sonnet/Opus) e economizar tokens. Invoca quick-classifier (Haiku) e devolve recomendação com justificativa.
argument-hint: [descrição da tarefa]
allowed-tools: Agent
---

# Triagem — Roteamento de modelo

## Quando usar
- Antes de uma tarefa que pode ser **simples** (rename, format, lookup, sumário) — vale checar se Haiku resolve
- Quando o user **quer economizar tokens** explicitamente
- Quando a tarefa é ambígua e você não tem certeza do peso

## Quando NÃO usar
- Tarefa óbvia complexa (arquitetura, decisão estratégica) — vai direto em Opus
- Tarefa óbvia trivial (1 edit pontual já mapeado) — vai direto em Haiku via subagent
- Conversa/exploração aberta (não é "tarefa")

## Como funciona

1. Você pega a `descrição da tarefa` (argumento da skill)
2. Invoca o subagent `quick-classifier` (model: Haiku — custa ~$0.001 por triagem)
3. Recebe JSON com: type, complexity, recommended_model, subagent_suggestion, reason
4. Devolve ao user no formato:

```
🎯 Triagem · <type>/<complexity>
→ Modelo recomendado: <model>
→ Subagent sugerido: <agent ou "nenhum">
→ Razão: <reason>

Próxima ação: <texto curto sobre o que fazer>
```

## Exemplo de invocação

```
/triagem renomeia getCwd pra getCurrentWorkingDirectory em todos os arquivos do projeto
```

Esperado:
```json
{
  "type": "edit",
  "complexity": "simple",
  "recommended_model": "haiku",
  "subagent_suggestion": null,
  "reason": "rename mecânico, busca + replace em N arquivos"
}
```

→ Resposta ao user:
```
🎯 Triagem · edit/simple
→ Modelo recomendado: haiku (~15× mais barato)
→ Subagent sugerido: nenhum (Claude principal pode delegar via Task ou Bash)
→ Razão: rename mecânico, busca + replace em N arquivos

Próxima ação: usar Grep + Edit replace_all, sem precisar Opus.
```

## Subagentes disponíveis pra delegação

| Agent | Modelo | Custo relativo | Quando |
|---|---|---|---|
| `quick-classifier` | haiku | 1× | Triagem rápida (esse fluxo) |
| `text-summarizer` | haiku | 1× | Resumir texto longo |
| `okr-coach` | sonnet | 6× | OKRs, KRs, calibração |
| `people-coach` | sonnet | 6× | Pessoas, 1:1, feedback |
| `Explore` | inherit | varia | Busca read-only no codebase |

(Custos aproximados pra mesma quantidade de tokens; Opus = ~15×)

## Hard rules

- Se o quick-classifier devolver `complexity: complex` mas o pedido cabe em Sonnet, escalar pra Opus só se houver decisão de arquitetura ou trade-off explícito
- Sempre que o user disser "rápido" ou "simples" — dar peso pra Haiku
- Sempre que envolver copy Metta/Tiago, design crítico, ou estratégia — Sonnet mínimo (não Haiku)
- Auditoria/code review com sugestões = Sonnet ou Opus (Haiku alucina mais em raciocínio cross-arquivo)
