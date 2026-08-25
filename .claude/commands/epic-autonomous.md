---
description: Start or resume autonomous execution of an SDD workflow/epic — Discovery through Product Handoff, pausing only on a real STOP condition.
argument-hint: <workflow-id>
---

Invoke the `epic-autonomous` skill for the workflow id given in
`$ARGUMENTS` (e.g. `a1b2c3`, matching the `<id>` in
`sdd/workflows/<id>-<name>/` — any SDD workflow in this project, not a
specific one).

Before doing anything else:

1. Confirm `sdd/workflows/<id>-*/workflow.yaml` exists for the given id. If
   not, stop and say so — this command runs an existing SDD workflow, it
   does not create one.
2. Read `sdd/workflows/<id>-*/autonomy.yaml` if it exists, to determine
   whether this is a fresh start or a resume (see the skill's "Resume
   behavior" section).
3. Follow `.claude/skills/epic-autonomous/SKILL.md` exactly — it is the
   authority on the state machine, the Definition of Done, parallelism
   rules, and STOP condition handling. Do not improvise a different
   procedure.
4. If the run's execution mechanism will be a `Workflow` tool script (the
   skill's recommended engine for multi-Feature epics), ask for explicit
   opt-in ("use a workflow" or equivalent) before the first `Workflow`
   call — approval of the architecture in an earlier conversation does not
   count as that opt-in.

Report back using the structured shape the skill's Product Handoff section
describes once the epic reaches `EPIC_DONE`, or the STOP summary shape from
`reference/stop-conditions.md` if execution pauses.
