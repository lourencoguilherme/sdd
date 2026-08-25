# STOP Conditions — Official List

Generic to any SDD epic/workflow in this project — not specific to any one
epic. The Orchestrator (never an agent) is the only party that decides a
STOP condition applies and pauses the state machine. Agents may *propose*
a `stop_condition` in their structured output; the Orchestrator evaluates it
against this list before acting on it.

Four categories. Category matters because it tells the Orchestrator (and
you, resuming later) what kind of answer is actually needed.

## BUSINESS_STOP — needs a Product Owner decision about the requirement

1. **Requisito de negócio materialmente ambíguo** — the functional
   requirement, epic context, or a SPEC gap can't be resolved by reading
   existing code/docs/architecture; it's a genuine "what do you actually
   want" question.
2. **Mudança material de escopo** — something discovered during
   discovery/implementation would expand or shrink what the epic/feature
   covers, beyond what the approved SPEC/context.md declared.
3. **Conflito entre requisitos** — two parts of the functional requirement,
   or a requirement vs. an already-approved SPEC of a sibling feature,
   contradict each other.
4. **Requisito impossível de interpretar sem Product Owner** — after
   Discovery, the feature's own SPEC cannot be drafted without a decision
   only the Product Owner can make.

## TECHNICAL_STOP — the team couldn't resolve it, but it's not a business call

5. **Risco arquitetural excepcional** — a technical decision with
   consequences beyond what "investigate, decide, document" (the normal
   autonomous mode) can respons­ibly resolve alone (e.g. contradicts a
   principle in `CLAUDE.md` with no clean resolution).
6. **3º ciclo de revisão ou correção sem sucesso** — `MAX_REVIEW_CYCLES` (for
   SPEC or PLAN Tech Lead review) or `MAX_FIX_CYCLES` (for the post-impl bug
   loop) reached 3 without resolution. See
   [decision-log-format.md](./decision-log-format.md) for what the report
   must contain.
7. **Impossibilidade técnica real** — something the SPEC/PLAN requires
   genuinely cannot be done as specified (not "hard", actually impossible
   given the stack/constraints).
8. **Conflito de integração não resolvível** — when parallel features
   (separate worktrees) are merged back and the merge can't be resolved
   cleanly within the same 3-attempt budget as the bug loop.

## SAFETY_STOP — protecting against real damage

9. **Ação destrutiva/irreversível** — anything that would discard
   uncommitted work, force-push, hard-reset, or delete data not created by
   this run.
10. **Regressão em funcionalidade já existente/aprovada** — a test failure
    or QA finding indicates something that worked *before* this epic/feature
    started now doesn't. This is never silently "fixed" as part of the new
    feature's own bug loop without surfacing it — a regression in prior,
    already-shipped behavior is treated as a SAFETY_STOP by default, not
    folded into the current feature's fix cycles, because silently patching
    it risks masking what actually broke and why.
11. **Ação que enviaria uma mensagem real (WhatsApp/e-mail) fora de
    mock/teste** — this project's own cardinal rule (zero real messages
    during tests/dev unless a human explicitly triggers it) is never
    something autonomous mode is allowed to relax.

## EXTERNAL_ACTION_STOP — visible outside the local repo/machine

12. **Custo financeiro não autorizado** — any paid service, API tier,
    infrastructure, or subscription not already present and paid for in the
    project.
13. **Necessidade de segredo/credencial que não pode ser obtida
    automaticamente** — a real API key, token, or credential the autonomous
    run has no way to generate or already possess.
14. **`git push` / PR externo / merge para branch compartilhada fora do
    worktree local do epic / deploy de produção** — anything that leaves
    marks visible to other people or systems outside this local run.

## Explicitly NOT a STOP condition

Internal git operations that stay local to the epic's own working
branch/worktree — commits, checkpoint commits, and merging a parallel
feature's worktree back into the epic's own integration branch — are
**not** STOP conditions. They're exactly what autonomous mode is supposed
to do without asking, the same way manual-mode SDD already creates
checkpoint commits without asking. Only actions that reach *outside* the
local run (category EXTERNAL_ACTION_STOP above) require pausing.

## Pre-authorization

A project or epic may pre-authorize a specific `EXTERNAL_ACTION_STOP`
action (e.g. "push to branch X is allowed") via the `authorized_actions`
field in `autonomy.yaml` (see
[autonomy-yaml-schema.md](./autonomy-yaml-schema.md)). It defaults to
empty — nothing is pre-authorized unless a human explicitly added it there.
Even when pre-authorized, the Orchestrator still logs the action as a
decision (see decision-log-format.md), just without pausing for it.

## What "STOP" actually does

1. Orchestrator writes `stop: {category, item, phase, reason, paused_at}`
   into `autonomy.yaml` and sets `status: paused`.
2. Orchestrator produces a human-readable summary of: the finding/question,
   evidence, what was already tried (if a technical stop), and — if
   there's a decision to make — the concrete options.
3. Nothing else advances. A new session/invocation of
   `/epic-autonomous <workflow-id>` reads `autonomy.yaml`, sees `paused`,
   and presents this summary instead of continuing.
4. Once the human responds, the Orchestrator records the response as a
   decision log entry with `Autorização necessária: sim`, sets
   `status: running`, and resumes at the exact `phase`/`item` where it
   paused — nothing already persisted (findings, cycle counts, test
   results) is lost or redone.
