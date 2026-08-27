# refinar.py — refino/análise barato via Gemini

Tira do Claude o trabalho **caro** do refino de specs (gerar/reescrever) e das
análises, delegando ao **Gemini CLI** (tier grátis/barato, sem API key — usa o
login já feito do `gemini`). O Claude fica só como **revisor/aprovador** — o que
custa muito menos que gerar.

> Foco: **reduzir consumo de tokens** e ter **análises mais baratas**.

## Pré-requisitos

- `gemini` CLI no PATH e autenticado (`gemini` → login Google, ou `GEMINI_API_KEY`).
- Python 3 (só stdlib).

## Modos

### `analyze` — análise barata de uma SPEC

```bash
python3 refinar.py analyze changes/.../SPEC.md --max-lines 400 --max-criteria 8
```

Mede tamanho/critérios em código e pede ao Gemini um parecer curto: cabe no
teto? o que cortar? decompor? maiores riscos. Ideal para o Claude **não** gastar
tokens analisando a spec.

### `refine` — gera uma SPEC candidata (teto em código)

```bash
python3 refinar.py refine changes/.../SPEC.md \
  --context CLAUDE.md --context sdd/sdd-settings.yaml \
  --max-lines 400 --max-criteria 8 --max-cycles 1
```

Loop determinístico: rascunho → (crítico → revisão)×N, com o teto de
linhas/critérios verificado em **código** (não como pedido ao modelo). Escreve
`SPEC.candidate.md` ao lado do alvo — **nunca** sobrescreve a `SPEC.md` aprovada.
Você (ou 1 revisão barata do Claude) promove a candidata se aprovar.

## Variáveis

- `GEMINI_MODEL` — modelo (default `gemini-2.5-flash`, barato/rápido).

## Como o custo cai

| Etapa | Onde roda |
|-------|-----------|
| Gerar/reescrever a spec, analisar bloat/riscos | **Gemini** (grátis/barato) |
| Orquestrar o loop + aplicar o teto | **Python** (grátis) |
| Revisar a candidata e decidir promover | Claude (barato — revisar << gerar) |
