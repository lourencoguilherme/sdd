---
name: c4-mermaid
description: Desenhos de arquitetura C4 (Contexto → Container → Componente) + diagrama de sequência, como código Mermaid — leve, lowcost, renderiza nativo no GitHub e nos artifacts. Sem instalar nada.
user-invocable: false
---

# C4 em Mermaid — desenho de arquitetura como código

Entrega os **3 primeiros níveis do C4** (Contexto, Container, Componente) mais um
**diagrama de sequência**, tudo como **código Mermaid** — que renderiza nativo no
GitHub, no VS Code e nos artifacts, sem PlantUML/servidor/.NET. É a escolha
lowcost. Não desenhe o nível 4 (Código) — é ruído para revisão humana.

## Onde gravar

```
docs/<slug>/diagrams/
├── context.mmd      # C4 nível 1 — o sistema e seus vizinhos
├── container.mmd    # C4 nível 2 — os blocos executáveis internos
├── component.mmd    # C4 nível 3 — as peças de UM container relevante
└── sequence.mmd     # o fluxo crítico ao longo do tempo
```

Além dos `.mmd`, **embuta cada diagrama** como bloco ` ```mermaid ` dentro do
`TECHNICAL.md` (assim o doc é auto-suficiente e renderiza no GitHub).

## Regra de ouro (anti-inchaço)

- Um diagrama por nível. Só os elementos que importam para a decisão.
- Contexto: no máximo ~7 caixas. Container: ~7. Componente: só do container mais
  crítico (não faça de todos). Sequência: só o fluxo crítico (o que pode dar
  errado / é irreversível), não o caminho feliz trivial.
- Se um diagrama não cabe legível numa tela, o desenho está complexo demais —
  simplifique a solução, não o diagrama.

## Templates (copie e adapte)

### Contexto (nível 1)
```mermaid
C4Context
  title Contexto — <sistema>
  Person(user, "Usuário", "quem usa")
  System(sys, "<sistema>", "o que faz em 1 frase")
  System_Ext(ext, "<serviço externo>", "ex.: WhatsApp via Baileys")
  Rel(user, sys, "usa")
  Rel(sys, ext, "integra")
```

### Container (nível 2)
```mermaid
C4Container
  title Container — <sistema>
  Person(user, "Usuário")
  System_Boundary(b, "<sistema>") {
    Container(app, "<app>", "Node/TS", "responsabilidade")
    Container(store, "Armazenamento", "SQLite/arquivo local", "estado")
  }
  System_Ext(ext, "<externo>")
  Rel(user, app, "chama")
  Rel(app, store, "lê/grava")
  Rel(app, ext, "integra")
```

### Componente (nível 3 — só do container crítico)
```mermaid
C4Component
  title Componente — <container>
  Container_Boundary(c, "<container>") {
    Component(a, "<peça A>", "papel")
    Component(b, "<peça B>", "papel")
  }
  Rel(a, b, "usa")
```

### Sequência (fluxo crítico)
```mermaid
sequenceDiagram
  actor U as Usuário
  participant A as <app>
  participant X as <externo>
  U->>A: ação
  A->>A: validação/guarda crítica
  A->>X: chamada externa
  X-->>A: resposta (ou erro)
  A-->>U: resultado
```

## Dica de custo

Mantenha os `.mmd` versionados no git — é o "desenho vivo" mais barato possível:
diff-ável, revisável e sem nenhuma ferramenta. Referência de abordagem C4-as-code:
robtaylor/c4-diagrams (PlantUML) e o C4 model oficial; aqui usamos Mermaid pela
renderização nativa e custo zero.
