# Instalação (a partir deste fork no GitHub)

Este fork adiciona ao SDD original duas camadas:

- **Espelhamento no Jira** — cada change SDD vira uma issue no board e anda com
  o ciclo (criada → spec aprovada → plano → verificada). Comando `/sdd-jira`.
- **Execução autônoma de epics** (`epic-autonomous`) — roda um workflow SDD de
  ponta a ponta substituindo os gates humanos por gates objetivos.

> As duas camadas são **opcionais e aditivas**: sem configurá-las, o SDD roda
> exatamente como o original.

---

## 1. Instalar o plugin a partir do GitHub

Em uma sessão **interativa** do Claude Code:

```bash
claude plugin marketplace add https://github.com/lourencoguilherme/sdd
claude plugin install sdd
```

Verifique:

```bash
/help          # deve listar os comandos /sdd, /sdd-run, /sdd-help, /sdd-jira
```

### Se você já tinha o SDD original instalado

O marketplace deste fork também se chama `sdd`, então pode colidir com o
upstream (`LiorCohen/sdd`). Remova o antigo antes de adicionar este:

```bash
claude plugin marketplace remove sdd     # remove o registro anterior
claude plugin marketplace add https://github.com/lourencoguilherme/sdd
claude plugin install sdd
```

Para fixar o fork em um projeto específico, adicione ao
`.claude/settings.json` do projeto:

```json
{
  "extraKnownMarketplaces": {
    "sdd": { "source": { "source": "github", "repo": "lourencoguilherme/sdd" } }
  },
  "enabledPlugins": { "sdd@sdd": true }
}
```

---

## 2. Iniciar/usar o SDD

Fluxo padrão (inalterado em relação ao original):

```
/sdd I want to initialize a new project
/sdd I want to create a new feature
/sdd I want to approve the spec
/sdd I want to approve the plan
/sdd I want to start implementing
/sdd I want to verify the implementation
```

Detalhes em [getting-started.md](./getting-started.md).

---

## 3. Ativar o espelhamento no Jira (opcional)

### 3.1 Instalar o conector Atlassian (independente do SDD)

O conector **não vem** com o plugin — instale-o uma vez:

```bash
claude mcp add --transport sse atlassian https://mcp.atlassian.com/v1/sse -s user
```

Depois autentique:

```bash
/mcp
```

Selecione `atlassian` → conclua o login OAuth. Confirme que aparece como
`✔ connected`. (Alternativa: adicionar **Atlassian** em claude.ai → Connectors.)

### 3.2 Configurar o projeto SDD

```bash
/sdd-jira setup
```

Isso descobre seus projetos Jira, pergunta o **project key** e o **site**, e
grava o bloco `jira:` em `sdd/sdd-settings.yaml`, por exemplo:

```yaml
jira:
  enabled: true
  site: "suaempresa.atlassian.net"
  project_key: "SEUKEY"
  issue_type_map: { feature: Story, bugfix: Bug, refactor: Task, epic: Epic }
  status_map: { created: "To Do", spec_approved: "In Progress", plan_approved: "In Progress", verified: "Done" }
```

### 3.3 A partir daí

- **Novas features** criadas via `/sdd` já nascem espelhadas no board e andam
  sozinhas conforme o ciclo avança.
- **Projeto já em andamento?** Traga o que já existe para o board:

  ```bash
  /sdd-jira backfill
  ```

- **Conferir vínculos:** `/sdd-jira status`.

O `jira_key` de cada issue fica gravado no frontmatter da `SPEC.md`
correspondente — os arquivos locais continuam sendo a fonte da verdade; o Jira
é um espelho. Se o conector estiver off, o SDD roda normal e **não** toca no
Jira (fail-soft).

---

## 4. Execução autônoma de epics (opcional)

Para rodar um workflow/epic existente de ponta a ponta:

```bash
/epic-autonomous <workflow-id>      # ex.: /epic-autonomous a1b2c3
```

Requer que `sdd/workflows/<id>-*/workflow.yaml` já exista. Detalhes na skill
`.claude/skills/epic-autonomous/SKILL.md`. Se o Jira estiver ativo, o
orquestrador também avança o board a cada gate.

---

## Resumo dos comandos

| Comando | Para quê |
|---------|----------|
| `/sdd …` | Hub do SDD (init, feature, approve, implement, verify) |
| `/sdd-jira setup \| sync \| backfill \| status` | Espelhamento no board do Jira |
| `/epic-autonomous <id>` | Rodar um epic de forma autônoma |
| `/sdd-help` | Tutor interativo |
