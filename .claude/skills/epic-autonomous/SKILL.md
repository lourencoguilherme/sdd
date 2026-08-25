---
name: epic-autonomous
description: Runs an SDD epic/workflow autonomously — Discovery through PLAN, implementation, tests, QA, Tech Lead review, and bug-fix cycles — advancing between Features without asking, pausing only on a genuine STOP condition. Generic to any SDD workflow in this project.
---

# Epic Autonomous — SDD Engineering Team orchestration

This skill turns the existing, unmodified SDD lifecycle (spec →
approve spec → plan → approve plan → implement → review → verify) into an
autonomous run for one workflow/epic at a time, by substituting the human
"approve" gates with objective ones: dedicated specialized agents
(`tech-lead`, `implementer`, `tester`, `qa`, `bug-fixer`) plus a bounded
fix/review-cycle loop, pausing only on a real STOP condition.

**This skill is generic.** It takes a `workflow-id` as input and operates
on whatever `sdd/workflows/<id>-<name>/workflow.yaml` already contains — it
must never assume a specific epic, feature name, or domain. Nothing in this
file or its references may hardcode a project-specific epic.

**Nothing in the SDD plugin (`~/.claude/plugins/.../sdd/`) is modified or
depended on beyond its already-existing, unmodified primitives:**
`workflow.yaml` (read-only from this skill's perspective — see below),
`spec validate` / `spec index` / `archive store` (real CLI commands, reused
as-is), and the documented `SPEC.md`/`PLAN.md` formats. Everything new
lives in this project's own `.claude/`.

## The one rule that overrides everything else in this file

**The Orchestrator — whoever/whatever is executing this skill's state
machine — is the sole authority over phase transitions, item completion,
cycle counts, and STOP conditions.** The five agents
(`tech-lead`/`implementer`/`tester`/`qa`/`bug-fixer`) are executors and
reviewers. They:

- return structured output only (see each agent's own `.md` for its exact
  shape);
- never write to `workflow.yaml` or `autonomy.yaml`;
- never decide what phase comes next;
- never decide a finding can be ignored;
- never decide a cycle limit doesn't apply to them;
- never decide a STOP condition they raised doesn't need to pause things.

The Orchestrator reads every agent's structured output, applies the gate
logic in this document, updates `autonomy.yaml` itself, and only then
proceeds. If you are the agent executing this skill, **you are the
Orchestrator** — do not delegate that judgment into an agent's prompt and
then blindly trust whatever it decides "should" happen next.

## Prerequisites

- The target `workflow.yaml` already exists (created through the normal
  SDD `change create` flow — this skill does not create epics, only runs
  them).
- `sdd/workflows/<id>-<name>/autonomy.yaml` either doesn't exist yet (fresh
  start — create it with `mode: autonomous`, `status: running`) or exists
  with `status: paused` (resume — see "Resume behavior" below).

## Two-layer separation: SDD state vs. runtime continuity

Two different concerns, kept deliberately separate:

1. **State logic** (this file): given `workflow.yaml` + `autonomy.yaml`,
   what is the next action? This is pure and deterministic — no dependency
   on how many turns/sessions it takes to get there.
2. **Runtime continuity** (not this file's concern): keeping execution
   going across conversation turns without a human retyping "continue" each
   time. In this environment that's the `/loop` skill or `ScheduleWakeup`
   re-invoking `/epic-autonomous <workflow-id>` — or, for a single
   sufficiently-scoped run, simply this skill executing the whole loop
   within one long turn. Document whichever mechanism is actually used in
   the run's own decision log; do not bake a specific runtime mechanism
   into the state machine logic itself.

## Execution mechanism

Two supported ways to actually run the agent calls this skill describes:

- **Direct, sequential/parallel `Agent` tool calls**, orchestrated turn by
  turn by whoever is running this skill. Use `isolation: "worktree"` on an
  `Agent` call when running independent Features' implementation steps in
  parallel (see "Parallelism" below) — this does not require the
  multi-agent-orchestration opt-in that the `Workflow` tool requires, and
  is the default for smaller runs (like the smoke test in
  `sdd/workflows/<test-id>/`).
- **A `Workflow` tool script** implementing the same state machine as a
  reusable, resumable script (`pipeline()`/`parallel()` mapped onto the
  Feature DAG, `agent()` with `schema` forcing the exact structured outputs
  each agent `.md` defines). This is the recommended engine for a real,
  multi-Feature epic run, because of its native DAG primitives,
  `isolation: 'worktree'` support, and `resumeFromRunId`. **Calling the
  `Workflow` tool requires the user's explicit opt-in** ("use a workflow",
  "ultracode", or equivalent) at the moment of invocation — approving this
  skill's architecture in advance does not substitute for that; ask for it
  explicitly right before the first `Workflow` call of an epic run.

Either way, the state machine, the gate logic, the DoD, and the persistence
schema are identical — only the mechanism spawning the agents differs.

## State machine (per item)

```
DISCOVERY
  → SPEC_DRAFT
  → spec validate (system CLI — real, unmodified SDD command)
  → tech-lead(review_type: spec_review)
       verdict SPEC_APPROVED           → PLAN_DRAFT
       verdict SPEC_CHANGES_REQUIRED   → revise SPEC → spec validate → tech-lead again
                                          (review_cycles.spec += 1; cap MAX_REVIEW_CYCLES=3)
       stop_condition proposed          → STOP_CHECK (see below)
PLAN_DRAFT
  → tech-lead(review_type: plan_review)
       verdict PLAN_APPROVED           → IMPLEMENT
       verdict PLAN_CHANGES_REQUIRED   → revise PLAN → tech-lead again
                                          (review_cycles.plan += 1; cap 3)
       stop_condition proposed          → STOP_CHECK
IMPLEMENT (implementer; parallel + worktree-isolated across independent items when the DAG allows)
  → INTEGRATION (merge worktree branch back to the epic's working branch;
                  no-op when the item ran sequentially, not parallel)
  → BUILD_LINT_TYPECHECK (Orchestrator runs these directly via Bash —
                            mechanical, no agent judgment needed)
  → tester(...)
  → qa(...)
  → tech-lead(review_type: post_impl_review)
       verdict TECH_LEAD_APPROVED and qa gaps/regressions empty → DOD_CHECK
       verdict CHANGES_REQUIRED, or qa found gaps/regressions   → BUG_TRIAGE
BUG_TRIAGE
  → for each open finding: assign to bug-fixer (small, well-localized) or
    implementer (larger gap needing PLAN-level rework)
  → fix → tester (retest, confirm the specific finding + no new regression)
  → qa (revalidate full AC matrix, not just the fixed item)
  → tech-lead(review_type: post_impl_review) again
  → (review_cycles.post_impl += 1; cap MAX_FIX_CYCLES=3)
  → 3rd unsuccessful cycle → STOP_CHECK (TECHNICAL_STOP #6)
DOD_CHECK
  → every item in the Definition of Done (below) must be pass
  → any item not pass → route back to whichever phase produces it
  → all pass → COMPLETE_ITEM
COMPLETE_ITEM
  → Orchestrator finds the next eligible item: topological order by
    depends_on, skipping items whose dependencies aren't yet complete
  → no eligible item and items remain → wait (shouldn't normally happen if
    the DAG is well-formed; if it does, that's itself worth a
    TECHNICAL_STOP — a malformed dependency graph is not something to
    guess through)
  → no items remain → EPIC_DONE → Product Handoff (below)
```

`STOP_CHECK`: the Orchestrator evaluates a proposed `stop_condition`
against `.claude/skills/epic-autonomous/reference/stop-conditions.md`. If
it genuinely qualifies, write `stop` into `autonomy.yaml`, set
`status: paused`, and stop. If it doesn't actually qualify (e.g. an agent
over-flagged something resolvable), log why in the decision log and
continue — this dismissal itself needs a decision log entry per
`decision-log-format.md`, so it's auditable, not just silently swallowed.

## Definition of Done (gate before `COMPLETE_ITEM`)

All of the following, each recorded with evidence in
`autonomy.yaml`'s `items.<id>.dod`:

1. SPEC approved (`tech-lead` `spec_review` verdict `SPEC_APPROVED`)
2. PLAN approved (`tech-lead` `plan_review` verdict `PLAN_APPROVED`)
3. Implementation complete (`implementer` returned with empty `blockers`)
4. `build` pass
5. `lint` pass (when the project has one — discover from `package.json`)
6. `typecheck` pass (when applicable)
7. Unit tests pass (when applicable)
8. Integration tests pass (when applicable)
9. E2E tests pass (when applicable)
10. `qa`'s AC matrix: 100% `PASS`
11. `tech-lead` `post_impl_review` verdict `TECH_LEAD_APPROVED`
12. Zero open findings with `severity: critical` or `high`
13. Zero unresolved regressions (`qa.regressions` empty, or each one
    triaged and closed — not just ignored)
14. The SPEC's own "Specs Directory Changes" section, if present, has been
    applied and matches the actual diff (reuse the same traceability check
    the SDD plugin's own `verification.md` already describes)

An item never reaches `COMPLETE_ITEM` with any of these unmet.

## Parallelism

Only parallelize Features with no `depends_on` relationship between them
(read directly from `workflow.yaml` — the plugin never enforces this
itself, so the Orchestrator must). Each parallel branch runs in its own
git worktree (`isolation: 'worktree'`) so simultaneous edits never
conflict on disk. After both branches finish `IMPLEMENT` (and their own
`tester` pass), the `INTEGRATION` phase explicitly merges each worktree
branch back into the epic's shared working branch before `BUILD_LINT_TYPECHECK`
runs against the combined result. A merge conflict during `INTEGRATION` is
not silently resolved — attempt resolution within the same 3-attempt
budget as the bug loop (`TECHNICAL_STOP #8` on the 3rd failure).

Do not force parallelism where the project's actual dependency graph
doesn't support it — a single-service project with few independent
Features may run almost entirely sequentially, and that's correct, not a
shortcoming of the mechanism.

## Resume behavior

On invocation, first read `autonomy.yaml`:

- doesn't exist → fresh start, create it (`mode: autonomous`,
  `status: running`, empty `items`).
- `status: paused` → present the `stop` block to the human exactly as
  captured (category, item, phase, reason, evidence, attempts, hypothesis,
  decision needed). Wait for a response. On response: log it as a decision
  entry (`Autorização necessária: sim`), set `status: running`, resume at
  the exact `phase` recorded for that item — every finding, cycle count,
  and test result already persisted stays as-is, nothing recomputed.
- `status: running` (shouldn't normally be seen at invocation time — would
  mean a prior run was interrupted mid-phase without going through a
  proper STOP) → treat as resume-at-last-known-phase, same as `paused`,
  but flag in the decision log that this was an unclean interruption.
- `status: completed` → nothing to do; point to the existing Product
  Handoff.

## Product Handoff (on `EPIC_DONE`)

Generate a single document (path recorded in `autonomy.yaml.handoff.report_path`)
covering: epic objective; Features delivered (link to each SPEC/PLAN);
every Acceptance Criterion with final status; tests executed (counts,
results); build result; consolidated QA matrix across all Features;
Tech Lead approvals and historical findings; bugs found and fixed; residual
risks; every decision log entry across all items; full list of files
changed; step-by-step functional test instructions for the human; known
limitations.

End state: `autonomy.yaml.status: completed`, and the Orchestrator reports
`EPIC = READY_FOR_PRODUCT_ACCEPTANCE`. No further Feature starts after
this — the run ends, it does not idle waiting for more work.

## See also

- `reference/stop-conditions.md` — the full STOP condition catalogue
- `reference/decision-log-format.md` — the `D<n>` format
- `reference/autonomy-yaml-schema.md` — the full sidecar schema
- `.claude/agents/tech-lead.md`, `implementer.md`, `tester.md`, `qa.md`,
  `bug-fixer.md` — each agent's exact contract
