---
name: jira-sync
description: Mirror SDD changes to a Jira board via the Atlassian MCP connector — create one issue per change and transition/comment it as SDD phases advance. Optional and off by default; local SDD files stay the source of truth.
user-invocable: false
---

# Jira Sync Skill

## Purpose

Give an SDD project a single, visual point of truth for the AI's progress: a
Jira board. When enabled, each SDD change (feature/bugfix/refactor/epic) is
mirrored to a Jira issue that is **created at spec time and walked through the
board as the SDD lifecycle advances** — refined, planned, implemented, verified.

Local SDD files remain the source of truth. Jira is a **mirror**. If Jira is
disabled or the connector is unavailable, SDD runs exactly as before and never
touches Jira.

## The one rule

**Never create a second issue for a change that already has a `jira_key`.**
Idempotency comes from the `jira_key` stored in the change's `SPEC.md`
frontmatter. Always read it first; create only when it is absent; otherwise
update the existing issue.

## Prerequisites (fail soft)

Before any Jira action, verify all of the following. If any fails, **log a
one-line skip note and continue the SDD flow — do not error out**:

1. `sdd/sdd-settings.yaml` has a `jira:` block with `enabled: true`.
   (Schema: [`project-settings` skill](../project-settings/), property `jira`.)
2. `jira.project_key` is set (not a placeholder).
3. The Atlassian MCP connector is authorized and its tools are available in
   this session.

## Tool discovery (do not hardcode tool names)

The Atlassian connector's tool names can vary by version. **Discover the
actual tools available at runtime** and match by intent rather than assuming a
fixed name. You need tools that, by their description, do:

| Intent | Typical name (verify at runtime) |
|--------|----------------------------------|
| List accessible sites / resolve cloudId | `getAccessibleAtlassianResources` |
| List visible projects (confirm project_key) | `getVisibleJiraProjects` |
| Create an issue | `createJiraIssue` |
| Read an issue | `getJiraIssue` |
| Edit fields / description | `editJiraIssue` |
| List available transitions for an issue | `getTransitionsForJiraIssue` |
| Transition an issue's status | `transitionJiraIssue` |
| Add a comment | `addCommentToJiraIssue` |

If a needed tool cannot be found, skip that step with a log note (see fail-soft
rule) — never invent an issue key or fabricate a result.

## Config resolution

Read `jira:` from `sdd/sdd-settings.yaml`. Resolve `cloud_id`:
- If `jira.cloud_id` is present, use it.
- Else call the accessible-resources tool, find the resource whose URL matches
  `jira.site`, and use its `id`. Cache it back into `sdd-settings.yaml`
  (`jira.cloud_id`) so later runs skip the lookup.

Confirm `jira.project_key` exists among visible projects once per run; if not,
log and skip.

## The link: SPEC.md frontmatter

The issue↔change link lives in the change's `SPEC.md` frontmatter and travels
with the file:

```yaml
---
type: feature
title: Agente de pré-atendimento
jira_key: MSG-123
jira_url: https://suaempresa.atlassian.net/browse/MSG-123
jira_synced_at: "2026-08-25T19:20:00Z"
---
```

`jira_key` is the idempotency anchor. `jira_url`/`jira_synced_at` are
convenience metadata. Write these back immediately after a successful create.

## Lifecycle mapping (the heart of the integration)

Each SDD milestone maps to a Jira action. `status_map` names come from settings
(defaults shown). Always resolve the real transition id via the
list-transitions tool before transitioning — status **names** differ per board.

| SDD milestone | Jira action | Default target |
|---------------|-------------|----------------|
| **Change created** (SPEC.md written) | Create issue; type from `issue_type_map[change.type]`; summary = change title; description = spec summary + link to local path. Write `jira_key` back. | status `created` → **To Do** |
| **Spec approved** | `editJiraIssue` description with the refined spec; `addComment` "Spec aprovada — <n> acceptance criteria"; transition. | `spec_approved` → **In Progress** |
| **Plan approved** | `addComment` with the phase breakdown from PLAN.md; keep/confirm status. | `plan_approved` → **In Progress** |
| **Implementation progress** (optional) | `addComment` per phase completed (only if the orchestrator reports phases). | — |
| **Verified** | `addComment` "Verificação concluída — implementação bate com a spec"; transition. | `verified` → **Done** |

### Epics

If the SDD change is an **epic** (or an epic-autonomous workflow), create an
issue of type `issue_type_map.epic` (default **Epic**) for the epic itself, and
link each child change's issue to it (set the parent/epic-link field on create
when the connector supports it). Each child feature still gets its own issue and
walks the board independently.

## Operations

This skill supports four operations. The caller (a command or another skill)
passes which one.

### `create` — mirror one change

Input: path to a change directory (containing `SPEC.md`).
1. Run prerequisites + config resolution. On skip, return `{skipped, reason}`.
2. Read `SPEC.md` frontmatter. If `jira_key` present → this is not a create;
   route to `sync` instead.
3. Create the issue (type/summary/description as mapped). Capture the returned
   key.
4. Write `jira_key`, `jira_url`, `jira_synced_at` back into `SPEC.md`.
5. Set initial status if `status_map.created` differs from the board's default.
6. Return `{created, jira_key, jira_url}`.

### `sync` — advance one change to a milestone

Input: change dir + `milestone` ∈ {spec_approved, plan_approved, verified}.
1. Prerequisites; read `jira_key` (if absent, run `create` first).
2. Apply the mapped edit/comment/transition for that milestone (resolve the
   transition id at runtime; if the target status is unreachable from the
   current one, comment instead of failing).
3. Update `jira_synced_at`.
4. Return `{synced, milestone, jira_key}`.

### `backfill` — mirror pre-existing changes

For a project that adopted Jira mid-flight. Enumerate every `SPEC.md` under
`changes/` (and epic workflows under `sdd/workflows/`). For each:
- If it already has `jira_key`, skip (idempotent).
- Else `create`, then fast-forward its status to reflect its **current** SDD
  state (e.g. an already-verified change is created and transitioned straight
  to `verified`/Done, with a single "backfill" comment noting the catch-up).
Report a summary: created / skipped / failed counts with keys.

### `status` — report linkage

List each change and its `jira_key`/`jira_url` (or "não sincronizado"), plus
whether Jira is enabled and the connector is reachable. Read-only.

## Idempotency & safety

- Re-running any operation must not duplicate issues, comments that are
  verbatim identical, or transitions already applied. Before commenting a
  milestone note, it is acceptable to check the issue's recent comments to
  avoid an exact duplicate.
- Never delete Jira issues from this skill.
- Never write secrets into Jira. Descriptions/comments carry spec/plan text
  and local paths only.
- All failures are soft: log, skip the Jira step, let SDD proceed.

## Output

Return a small structured object per operation (see each operation). Callers
use it only for reporting; it is never written to `workflow.yaml`.
