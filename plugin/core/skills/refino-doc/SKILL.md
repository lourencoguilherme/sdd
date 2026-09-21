---
name: refino-doc
description: Refino doc-first e retomável entre sessões — recebe a demanda, documenta no projeto (funcional + técnico como REGISTRO), tira dúvidas, grava incremental e persiste estado em STATE.md para retomar em qualquer sessão. A IA NÃO valida tecnicamente (o humano é o avaliador técnico); sem conselho de agentes, sem gate de custo, sem código.
user-invocable: false
---

# Refino Doc-First — retomável entre sessões

Trilha padrão do SDD para o Gui. Objetivo: **transformar uma demanda em
documentação viva**, tirando as dúvidas necessárias, gravando **a cada etapa**, e
persistindo o estado para **retomar de onde parou em qualquer sessão futura**. A
IA documenta; **o humano é o avaliador técnico**.

Diferença explícita para `refino-enxuto`:

| | `refino-enxuto` | `refino-doc` (este) |
|---|---|---|
| Sessões | uma só | **multi-sessão, retomável** |
| Validação técnica | IA arbitra (conselho + gate de custo) | **humano valida; IA só documenta** |
| Gravação | entrega no fim | **incremental, a cada etapa** |
| Saída | FUNCTIONAL/TECHNICAL/C4/COST | `STATE.md` + FUNCTIONAL + TECHNICAL |

## Princípio: zero contexto de sessão

**Todo o estado vive em arquivos**, não na conversa. Uma sessão nova precisa
retomar lendo apenas `docs/refino/<slug>/` — sem histórico de chat, sem memória.
Leia os arquivos, saiba o estado, continue do "Próximo passo".

## Estrutura no projeto-alvo

```text
docs/refino/<slug>/
├── STATE.md        # âncora de retomada: status, próximo passo, abertos, log de decisões
├── FUNCTIONAL.md   # registro funcional (atualizado incrementalmente)   ≤ ~150 linhas
└── TECHNICAL.md    # registro técnico como o Gui ditou (Gui valida)      ≤ ~250 linhas
```

`diagrams/*.mmd` (C4/sequência em Mermaid) só se o Gui pedir ou fornecer o desenho
— não é a IA que decide a arquitetura aqui.

### Template do `STATE.md`

```markdown
# Refino: <título>  ·  slug: <slug>
status: rascunho            # rascunho → em-refino → aguardando-validacao → validado
atualizado: <yyyy-mm-dd>

## Próximo passo
<uma linha: a primeira coisa que a próxima sessão deve fazer>

## Perguntas em aberto
- [ ] <pergunta objetiva> — bloqueia? sim/não

## Decisões (log)
- <yyyy-mm-dd> — <decisão> (fonte: Gui | demanda)

## Progresso das seções
- FUNCTIONAL.md: <vazio | esboço | completo>
- TECHNICAL.md:  <vazio | esboço | completo>
```

## Passo a passo

0. **Retomar (sempre primeiro).** Procure `docs/refino/*/STATE.md` no projeto. Se a
   demanda casa com um refino existente (ou o Gui deu o slug), **leia STATE +
   docs e continue do "Próximo passo"**. Não recomece nem sobrescreva o que já foi
   decidido.
1. **Abrir o registro (primeira ação).** Derive um `slug` kebab-case curto. Crie
   `docs/refino/<slug>/` com os três arquivos em esqueleto e escreva a **demanda
   crua** no FUNCTIONAL. `status: rascunho`.
2. **Tirar dúvidas.** Pergunte **apenas o crítico/ambíguo**, poucas perguntas
   objetivas e juntas. Cada resposta → atualiza o doc na hora + linha no log de
   decisões. `status: em-refino`.
3. **Documentar como REGISTRO (funcional + técnico).** Escreva o que está definido,
   **gravando a cada etapa** (não só no fim). A IA **não** julga se a arquitetura
   está certa, **não** roda conselho de agentes, **não** roda gate de custo. Todo
   ponto técnico não resolvido vira item em "Perguntas em aberto" para o Gui.
4. **Persistir e parar.** Atualize o `STATE.md`: `status: aguardando-validacao`,
   "Próximo passo", perguntas abertas. **Pare** e apresente um resumo curto para a
   validação técnica do Gui. **Não implemente / não code** sem o "aprovado / pode
   implementar" explícito.

## STOP (pare e pergunte)

- Ambiguidade de negócio que muda o registro.
- Gui pediu a validação (fim de cada rodada de refino).

Fora esses, **não pause** — documente, grave e siga.

## Anti-inchaço

- Respeite os tetos; estourou → **decomponha** (crie outro `<slug>`), não infle.
- Histórico e mudanças vão no **log de decisões do STATE**, nunca dentro dos docs.
- Sem repetir a mesma regra em várias seções, sem detalhe de implementação de
  baixo nível (isso é trabalho de quem for implementar depois da sua validação).
