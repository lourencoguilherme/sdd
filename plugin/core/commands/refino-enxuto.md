---
description: Refina uma solução em UMA sessão para empresa pequena/solo lowcost — conselho mínimo + gate de custo, entrega docs funcional/técnico + C4 (Mermaid) + sequência, e para na aprovação humana. Aceita `continuar <id>` para ingerir um refino pesado que não fechou.
argument-hint: <ideia em linguagem natural> | continuar <workflow-id>
---

Invoque a skill **`refino-enxuto`** para o que está em `$ARGUMENTS`.

**Dois modos:**
- **Novo:** `$ARGUMENTS` é a ideia/problema em linguagem natural → refina do zero.
- **Continuar:** `$ARGUMENTS` começa com `continuar`/`continue` + um id de
  workflow (ex.: `continuar aj3fnx`) ou caminho de change → **ingere o refino
  SDD pesado existente** (`sdd/workflows/<id>/`, `changes/**/SPEC.md`), destila
  os pontos críticos e as decisões já tomadas (delegando a leitura pesada ao
  `tools/refinar`/Gemini para não gastar tokens) e entrega os docs enxutos —
  **sem sobrescrever** as specs originais. Ver a seção "Modo continuar" da skill.

Esta é a trilha **enxuta e lowcost** do SDD — uma alternativa ao fluxo completo,
para quando você é uma empresa pequena/solo e precisa **fechar o refino em uma
sessão**, sem a IA alucinar complexidade.

Antes de tudo:

1. Derive um `slug` curto e kebab-case da ideia (ex.: `agente-pre-atendimento`).
2. Siga `refino-enxuto/SKILL.md` **exatamente** — a Carta Lowcost, os tetos de
   tamanho, o conselho mínimo (PO/PM/Arquiteto/Tech Lead/Analista de Custo/CTO),
   e o **gate financeiro** que aciona o Analista de Custo quando a solução exige
   custo elevado.
3. Desenhe a arquitetura com a skill `c4-mermaid` — apenas Contexto, Container,
   Componente (do container crítico) e um diagrama de Sequência, como código
   Mermaid.
4. **Pare na aprovação humana**: apresente o resumo + diagramas e peça aprovação
   do requisito técnico e do desenho antes de qualquer implementação.

Entrega esperada em `docs/<slug>/`: `FUNCTIONAL.md`, `TECHNICAL.md` (com os
diagramas embutidos), `diagrams/*.mmd` e, se o gate de custo disparar, `COST.md`.
