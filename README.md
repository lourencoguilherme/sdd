# Spec-Driven Development (SDD)

*Structure for AI-assisted development*

![SDD Logo](docs/logo.svg)

AI coding assistants are powerful but chaotic. You prompt, you get code, but then what? No documentation of decisions, no way to verify the code matches what you needed, and a codebase that's impossible to explain to teammates.

SDD brings structure to AI-assisted development. Every change starts with a spec, gets broken into a plan, and ends with verified implementation. Specialized agents handle each concern instead of one AI doing everything poorly.

## Installation

```bash
claude plugin marketplace add https://github.com/LiorCohen/sdd
claude plugin install sdd
```

## Quick Start

```
/sdd I want to initialize a new project              # Initialize a new project
/sdd I want to create a new feature                   # Create a spec
/sdd I want to approve the spec                       # Review spec, create plan
/sdd I want to approve the plan                       # Approve plan, enable implementation
/sdd I want to start implementing                     # Execute the plan
/sdd I want to verify the implementation              # Verify it matches the spec
```

**[Get started with the tutorial →](./docs/getting-started.md)**

---

## How It Works

### Specs Are the Source of Truth

Every change lives in a markdown specification before it lives in code:

```
changes/2026/01/15/user-auth/
├── SPEC.md    # What you're building (acceptance criteria)
└── PLAN.md    # How to build it (phased implementation)
```

Specs include frontmatter metadata, acceptance criteria in Given/When/Then format, and references to domain concepts.

### Four Change Types

| Type | Purpose | Structure |
|------|---------|-----------|
| **feature** | New functionality | 6 phases |
| **bugfix** | Fix existing behavior | 4 phases |
| **refactor** | Restructure without changing behavior | 4 phases |
| **epic** | Multiple features grouped under one goal | Child changes in `changes/` subdirectory |

### Specialized Agents

Instead of one general-purpose AI, SDD uses 7 specialized agents:

| Agent | Model | Purpose |
|-------|-------|---------|
| api-designer | sonnet | Design OpenAPI contracts |
| backend-dev | sonnet | Node.js backend (CMDO architecture) |
| frontend-dev | sonnet | React components (MVVM architecture) |
| db-advisor | opus | Database performance review |
| devops | sonnet | Kubernetes, Helm, CI/CD, Testkube |
| tester | sonnet | Integration and E2E test automation |
| reviewer | opus | Code review and spec compliance |

### Commands

| Command | Purpose |
|---------|---------|
| `/sdd` | Context-aware hub — reads project state and guides you |
| `/sdd I want to create a new feature` | Create new change spec |
| `/sdd I want to import an external spec` | Import changes from external spec |
| `/sdd I want to approve the spec` | Approve spec, create plan |
| `/sdd I want to approve the plan` | Approve plan, enable implementation |
| `/sdd I want to start implementing` | Execute implementation plan |
| `/sdd I want to verify the implementation` | Verify implementation matches spec |
| `/sdd I want to generate config for local` | Generate merged config for an environment |
| `/sdd set up the database` | Direct system operations via natural language |
| `/sdd-help` | Interactive tutor for SDD concepts |

---

## Extensão deste fork: execução autônoma de epics (`epic-autonomous`)

> Adição exclusiva deste fork. Não altera nada do plugin SDD original — é uma
> camada **puramente aditiva**, construída ao aplicar o SDD no projeto real
> `message-ai`. Vive em `.claude/` e usa apenas primitivas já existentes do SDD
> (`workflow.yaml`, `spec validate`/`index`, `archive store`, os formatos
> `SPEC.md`/`PLAN.md`).

O fluxo padrão do SDD pausa em gates humanos (aprovar spec → aprovar plano →
verificar). O `epic-autonomous` roda um workflow/epic **de ponta a ponta**
substituindo esses gates humanos por gates **objetivos**: agentes especializados
mais um loop limitado de review/fix, pausando só quando aparece uma STOP
condition real.

### Componentes

| Item | Caminho | Papel |
|------|---------|-------|
| Comando `/epic-autonomous <workflow-id>` | `.claude/commands/epic-autonomous.md` | Inicia ou retoma a execução autônoma de um workflow existente |
| Skill `epic-autonomous` | `.claude/skills/epic-autonomous/` | Máquina de estados, Definition of Done, regras de paralelismo e STOP conditions |
| Agente `tech-lead` | `.claude/agents/tech-lead.md` | Revisão de arquitetura e conformidade com a spec |
| Agente `implementer` | `.claude/agents/implementer.md` | Executa o plano de implementação |
| Agente `tester` | `.claude/agents/tester.md` | Escreve e roda testes |
| Agente `qa` | `.claude/agents/qa.md` | Verificação contra critérios de aceite |
| Agente `bug-fixer` | `.claude/agents/bug-fixer.md` | Ciclo limitado de correção de findings |

### Como usar

```
/epic-autonomous a1b2c3      # a1b2c3 = <id> em sdd/workflows/<id>-<name>/
```

O comando confirma que `sdd/workflows/<id>-*/workflow.yaml` existe, lê
`autonomy.yaml` para decidir entre início limpo ou retomada, e segue a skill
como autoridade única sobre transições de fase e STOP conditions.

> **Nota sobre distribuição:** por viver em `.claude/` da raiz, esta camada
> funciona ao trabalhar *dentro* deste repositório, mas **não** é distribuída
> para quem instala o plugin `sdd`. Para distribuí-la junto do plugin, os
> arquivos precisariam ir para `plugin/core/`.

---

## Reducing Permission Prompts

SDD commands create many files. To reduce permission prompts, add this to your `.claude/settings.local.json`:

```json
{
  "permissions": {
    "allow": [
      "Write(changes/**)",
      "Write(specs/**)",
      "Write(components/**)",
      "Edit(changes/**)",
      "Edit(specs/**)",
      "Edit(components/**)",
      "Bash(git *)",
      "Bash(npm *)"
    ],
    "deny": [
      "Write(.env*)",
      "Edit(.env*)"
    ]
  }
}
```

See **[Permissions Setup](./plugin/hooks/PERMISSIONS.md)** for full configuration options.

---

## Documentation

- **[Getting Started](./docs/getting-started.md)** - First project tutorial
- **[Workflows](./docs/workflows.md)** - Feature, bugfix, and refactor workflows
- **[Commands](./docs/commands.md)** - Full command reference
- **[Agents](./docs/agents.md)** - What each agent does
- **[Components](./docs/components.md)** - Component types reference
- **[Configuration Guide](./docs/config-guide.md)** - Config system details
- **[Permissions Setup](./plugin/hooks/PERMISSIONS.md)** - Reduce permission prompts

---

## Project Structure

When you run `/sdd I want to initialize a new project`, you get:

```
your-project/
├── changes/                  # Change specifications (YYYY/MM/DD/<name>/)
├── specs/
│   ├── INDEX.md              # Registry of all specifications
│   ├── SNAPSHOT.md           # Current product state
│   ├── domain/
│   │   ├── glossary.md       # Domain terminology
│   │   └── definitions/      # Domain definitions
│   └── architecture/         # Architecture decisions
├── components/
│   ├── config/               # Configuration (YAML + TypeScript types)
│   ├── contract/             # OpenAPI specs (workspace package)
│   ├── server/               # Node.js backend
│   ├── webapp/               # React frontend
│   ├── database/             # PostgreSQL migrations
│   ├── helm/                 # Kubernetes charts
│   └── testing/              # Testkube definitions
└── .github/workflows/        # CI/CD pipelines
```

---

## Architectural Patterns

- **CMDO Backend** - Controller Model DAL Operator with strict layer separation
- **MVVM Frontend** - Model-View-ViewModel with TanStack ecosystem
- **Contract-First API** - OpenAPI specs generate TypeScript types
- **Immutability Enforced** - `readonly` everywhere, no mutations
- **OpenTelemetry** - Structured logging, metrics, and tracing

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## Resources

- [Claude Code Documentation](https://docs.anthropic.com/claude/docs/claude-code)
- [Plugin Development Guide](https://docs.anthropic.com/claude/docs/claude-code-plugins)

## License

MIT
