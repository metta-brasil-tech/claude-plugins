# metta-triagem

Roteamento automático de tarefas pro **modelo certo** (Haiku / Sonnet / Opus)
pra economizar tokens. Tarefa mecânica vai pra Haiku (~15× mais barato); só o
que exige raciocínio fica no Opus.

## Componentes

| Componente | Tipo | O que faz |
|---|---|---|
| `hooks/triagem.sh` + `hooks/hooks.json` | Hook `UserPromptSubmit` | Roda a cada prompt, classifica por palavra-chave (regex) e injeta uma dica de delegação no contexto. Custo zero, nunca bloqueia o prompt. |
| `commands/triagem.md` | Command | `/triagem <tarefa>` — classificação estruturada sob demanda. |
| `agents/quick-classifier.md` | Subagent (Haiku) | Classifica a tarefa de verdade e devolve JSON (type / complexity / modelo). |
| `agents/text-summarizer.md` | Subagent (Haiku) | Resume texto longo em bullets — alvo de delegação. |

## Instalação

```bash
claude plugin marketplace add metta-brasil-tech/claude-plugins
claude plugin install metta-triagem
```

Reinicie o Claude Code depois de instalar.

### Pré-requisitos
O hook é um script bash que usa Python pra ler o JSON do prompt:
- **bash** no PATH — Mac/Linux já têm; no Windows vem com o **Git for Windows** (Git Bash).
- **Python 3** no PATH (o script tenta `python3` e depois `python`).

Se faltar bash ou python o hook simplesmente não roda — não quebra nada, só não aparece a dica.

## Uso

- **Automático:** mande um prompt qualquer. Se bater num padrão, aparece uma linha
  `[triagem-auto] ...` orientando o roteamento. O Claude decide se delega.
- **Manual:** `/metta-triagem:triagem renomeia getCwd pra getCurrentWorkingDirectory`
  → retorna tipo / complexidade / modelo recomendado / subagent sugerido.

## Como funciona

```
prompt → [hook triagem.sh] injeta dica grátis (regex)
              ↓
        Claude decide delegar
         ├─ simples → Task pro quick-classifier / text-summarizer (Haiku)
         └─ pesado  → resolve no Opus/Sonnet
        (/triagem chama quick-classifier sob demanda)
```

- **Hard rules:** copy, PRD, arquitetura, estratégia, code review → nunca Haiku.
- **Simples:** rename, format, resumo, lookup, validação → sugere Haiku.
- **Complexo:** decisão, trade-off, vários arquivos → confirma Opus.

## Personalizar
Os gatilhos são `grep -E` dentro de `hooks/triagem.sh` (seções HARD RULES /
SIMPLE / COMPLEX). Edite as listas de palavras-chave pro vocabulário do time.
O hook sempre faz `exit 0`.

## Nota pra quem já tinha a versão manual
Se você já tinha o `triagem.sh` registrado no seu `~/.claude/settings.json`,
**remova aquele bloco de hook** depois de instalar o plugin — senão a dica
`[triagem-auto]` dispara duas vezes.

## Versão
v1.0.0 · 2026-05-28
