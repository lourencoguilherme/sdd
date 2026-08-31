---
name: refino-enxuto
description: Refino de solução em UMA sessão para empresa pequena/solo lowcost — conselho mínimo (PO, PM, Arquiteto, Tech Lead, Analista de Custo, CTO/CEO), gate financeiro, e entrega docs funcional + técnico + C4 (Mermaid) + sequência, parando na aprovação humana.
user-invocable: false
---

# Refino Enxuto — solução em uma sessão, lowcost

Trilha alternativa ao fluxo SDD completo, feita para **empresa pequena/solo com
orçamento baixo**. Objetivo: **refinar os pontos críticos** de uma ideia, decidir
a arquitetura mínima viável e **entregar em UMA sessão**:

- `FUNCTIONAL.md` — documentação funcional (curta)
- `TECHNICAL.md` — documentação técnica (curta) com os diagramas embutidos
- `docs/<slug>/diagrams/` — C4 Contexto/Container/Componente + Sequência (Mermaid)
- `COST.md` — veredito do gate financeiro (só se houver custo elevado)

Depois disso **para** na aprovação humana. Aprovado, o time de devs implementa.

## A Carta Lowcost (regra que domina tudo)

Você está refinando para uma **empresa pequena/solo**. Vieses obrigatórios:

1. **O mais barato que funciona.** Default: usar o que já existe e é grátis —
   o runtime atual, arquivo local/SQLite, libs open-source, free tiers,
   self-host no que já roda. Nada de escala prematura.
2. **Só os pontos críticos.** Refine o que é ambíguo, arriscado ou irreversível.
   Para o resto, registre a decisão default em UMA linha e siga. Não escreva
   parágrafos sobre o que é óbvio.
3. **Convirja em UMA sessão.** Não abra rodadas infinitas de revisão. Ao atingir
   "bom o suficiente para decidir", pare e entregue.
4. **Proibido inchar.** Sem histórico de revisão dentro do doc, sem repetir a
   mesma regra em 5 seções, sem detalhar implementação de baixo nível (isso é
   trabalho do dev, não do refino).

**Tetos rígidos:** `FUNCTIONAL.md` ≤ ~150 linhas · `TECHNICAL.md` ≤ ~250 linhas ·
`COST.md` ≤ ~60 linhas. Estourou o teto → o escopo é grande demais: **decomponha**
em vez de inflar.

## O conselho mínimo (aplicado como lentes, em UM passo)

Não são seis agentes tagarelas gerando paredes de texto — são **lentes** que o
orquestrador aplica em sequência, cada uma contribuindo uma seção curta:

| Papel | Mandato (curto) | Entrega |
|-------|-----------------|---------|
| **PO** | pontos críticos + valor; o que NÃO fazer agora | seção Funcional |
| **PM** | mantém escopo pequeno; corta o supérfluo | corta, não adiciona |
| **Arquiteto + Tech Lead** | solução técnica mínima viável + C4 + sequência | seção Técnica + diagramas |
| **Analista de Custo** | freio financeiro — ver gate abaixo | `COST.md` (condicional) |
| **CTO/CEO** | arbitra trade-off, decide, encerra | decisão final registrada |

## 🔴 Gate financeiro (o diferencial)

O **Analista de Custo é acionado automaticamente** quando o Arquiteto/Tech Lead
propõem qualquer coisa de **custo elevado**, definido como:

- serviço/infra **pago recorrente** (DB gerenciado, fila/broker gerenciado, k8s,
  serverless pago por volume);
- **runtime/toolchain adicional** ao que o projeto já usa (ex.: .NET num projeto
  Node/TS);
- **múltiplas instâncias** ou escala horizontal;
- **API paga por volume** como dependência central.

Quando disparado, o Analista de Custo DEVE:
1. Estimar o custo mensal aproximado da proposta.
2. Apresentar a **alternativa lowcost** (Tier-0: grátis/self-host/local).
3. Só manter a opção cara se **você (humano) aceitar explicitamente** o custo.

Registre a decisão em `COST.md`. Se a solução já é lowcost (Tier-0), **o gate
passa em silêncio** e `COST.md` não é criado.

## Passo a passo

1. **Entrada:** a ideia/problema em linguagem natural (`$ARGUMENTS`) + um `slug`
   curto derivado dela.
2. **Funcional (PO/PM):** pergunte APENAS o que for crítico e ambíguo (poucas
   perguntas objetivas, juntas). Escreva `docs/<slug>/FUNCTIONAL.md`.
3. **Técnico (Arquiteto/Tech Lead):** proponha a solução mínima. Rode o **gate de
   custo**. Desenhe os diagramas via a skill [`c4-mermaid`](../c4-mermaid/):
   Contexto, Container, Componente (só do container crítico), Sequência (fluxo
   crítico). Escreva `docs/<slug>/TECHNICAL.md` com os diagramas embutidos e os
   `.mmd` em `docs/<slug>/diagrams/`.
4. **Custo:** se o gate disparou, escreva `docs/<slug>/COST.md` e apresente a
   escolha lowcost vs. cara para você decidir.
5. **✋ Aprovação humana:** apresente um resumo de 5 linhas + os diagramas e
   **pare**, pedindo aprovação do requisito técnico e do desenho de arquitetura.
   Não comece a implementar antes do "aprovado".
6. **Devs:** aprovado, o time de desenvolvimento implementa a solução aprovada
   (fora do escopo desta skill).

## STOP (pare e pergunte)

- Ambiguidade de negócio que muda a solução.
- Gate de custo disparado (sempre pausa para sua decisão).
- Escopo estourando os tetos (sugira decompor).
Fora esses, **não pause** — convirja e entregue.
