---
description: Refino doc-first e retomável entre sessões — documenta a demanda no projeto (funcional + técnico como registro), tira dúvidas, grava incremental e persiste estado para retomar depois. Você é o avaliador técnico; a IA não valida tecnicamente. Aceita `continuar <slug>` para retomar.
argument-hint: <ideia em linguagem natural> | continuar <slug>
---

Invoque a skill **`refino-doc`** para o que está em `$ARGUMENTS`.

> **Nota:** este é o comportamento **padrão** quando o Gui pede uma nova feature
> (ver `~/.claude/CLAUDE.md`). Este comando é só a entrada manual/explícita do
> mesmo fluxo.

**Dois modos:**
- **Novo:** `$ARGUMENTS` é a ideia/demanda em linguagem natural → abra o registro
  em `docs/refino/<slug>/` e siga a skill.
- **Continuar:** `$ARGUMENTS` começa com `continuar`/`continue` + um `slug` (ex.:
  `continuar agente-pre-atendimento`) → **retome** lendo `docs/refino/<slug>/`
  e continue do "Próximo passo" do `STATE.md`. Não recomece do zero.

Antes de tudo:

1. Rode o **passo 0 (retomar)** da skill: procure `docs/refino/*/STATE.md` antes de
   criar qualquer coisa nova.
2. Siga `refino-doc/SKILL.md` **exatamente** — zero contexto de sessão, gravação
   incremental, humano como avaliador técnico, e **pare** na validação humana.
3. **Não implemente / não code** sem o "aprovado / pode implementar" explícito.
