---
description: Configure and drive the optional Jira board mirror for this SDD project (setup, sync, backfill, status).
argument-hint: setup | sync <change-path> <milestone> | backfill | status
---

Invoke the **`jira-sync`** skill for this project. `$ARGUMENTS` selects the
operation. If `$ARGUMENTS` is empty, run **`setup`**.

The Jira mirror is **optional and off by default**. Local SDD files are always
the source of truth; Jira is a mirror that gives a single visual point for the
AI's progress.

## `setup`

Interactive first-time configuration. Do, in order:

1. **Install the Atlassian MCP connector (independent of SDD).** The connector
   is not bundled — the user installs it once. Present these commands and let
   the user run them in an interactive Claude Code session (this step cannot be
   done for them):

   ```bash
   claude mcp add --transport sse atlassian https://mcp.atlassian.com/v1/sse -s user
   ```
   then authenticate:
   ```bash
   /mcp
   ```
   (select `atlassian` → complete the OAuth login). Alternatively, add
   **Atlassian** from claude.ai → Connectors. Confirm it shows
   `✔ connected` with tools before continuing.

2. **Resolve the target project.** Once the connector is authorized, use it to
   list visible Jira projects and ask the user which **project key** and
   **site** to mirror into.

3. **Write the `jira:` block** into `sdd/sdd-settings.yaml` (schema: the
   `project-settings` skill, property `jira`). Start with:

   ```yaml
   jira:
     enabled: true
     site: "<site>.atlassian.net"
     project_key: "<KEY>"
     issue_type_map: { feature: Story, bugfix: Bug, refactor: Task, epic: Epic }
     status_map: { created: "To Do", spec_approved: "In Progress", plan_approved: "In Progress", verified: "Done" }
   ```

   If the connector is not yet authorized, still write the block but with
   `enabled: false` and placeholder `site`/`project_key`, and tell the user to
   rerun `/sdd-jira setup` after authorizing. SDD keeps working with it off.

4. Offer to run **`backfill`** for changes that already exist in this project.

## `sync <change-path> <milestone>`

Advance one change on the board. `milestone` ∈ `spec_approved`,
`plan_approved`, `verified`. Delegates to the skill's `sync` operation
(creates the issue first if the change has no `jira_key` yet).

## `backfill`

Mirror every pre-existing change under `changes/` (and epic workflows under
`sdd/workflows/`) that has no `jira_key` yet, fast-forwarding each to its
current SDD state. Idempotent — safe to re-run. Use this when adopting Jira on a
project already in progress.

## `status`

Read-only. Report Jira enablement, connector reachability, and each change's
`jira_key`/`jira_url` (or "não sincronizado").

---

**Fail-soft always:** if Jira is disabled, misconfigured, or the connector is
unavailable, report it in one line and stop — never block or error the SDD
workflow because of Jira.
