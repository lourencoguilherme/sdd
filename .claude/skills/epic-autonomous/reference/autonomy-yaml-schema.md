# `autonomy.yaml` Schema

Lives at `sdd/workflows/<id>-<name>/autonomy.yaml`, next to (never inside)
that workflow's `workflow.yaml`. This is a **local extension to this
project**, not part of the SDD plugin's own format — deliberately kept as a
separate file so nothing in the SDD plugin's documented `workflow.yaml`
schema or its own read/rewrite procedures can ever silently drop it. See
`SKILL.md` for why (compatibility investigation).

`workflow.yaml` remains the SDD plugin's own source of truth for
`spec_status`/`plan_status`/`impl_status`/`review_status` per item — this
file never duplicates or overrides those fields, only adds the autonomy
layer on top: which phase of the *autonomous* state machine each item is in
(finer-grained than the plugin's four statuses), review/fix cycle counts,
findings, decisions, and pause/resume state.

## Full shape

```yaml
mode: autonomous              # manual | autonomous — manual epics never get this file at all
status: running                # running | paused | completed
authorized_actions: []         # pre-authorized EXTERNAL_ACTION_STOP actions; empty by default

epic:
  workflow_id: <matches workflow.yaml id>
  objective: <one-line summary, from the epic's context.md>

items:
  <item-id>:                   # same ids as workflow.yaml's items
    phase: discovery | spec_draft | tech_lead_spec | plan_draft | tech_lead_plan
         | implement | integration | build_lint_typecheck | tester | qa
         | tech_lead_post | bug_triage | dod_check | complete
    review_cycles:
      spec: 0                  # each capped at MAX_REVIEW_CYCLES = 3
      plan: 0
      post_impl: 0             # this one is MAX_FIX_CYCLES = 3, same cap, different name for clarity
    findings:
      - id: TL-1                # or QA-<n>, QA-R-<n>
        source: tech_lead | qa
        severity: critical | high | medium | low
        category: architecture | security | testability | scope | quality | regression | observability | tech_debt | acceptance_criteria
        file: path or null
        location: string or null
        evidence: string
        expected: string
        actual: string
        acceptance_criterion: AC id or null
        recommended_fix: string
        status: open | assigned | fixed | wontfix_because_disputed
        assigned_to: bug-fixer | implementer or null
    decisions: []                # D<n> entries — see decision-log-format.md
    test_results:
      unit: { run: 0, passed: 0, failed: 0 }
      integration: { run: 0, passed: 0, failed: 0 }
      e2e: { run: 0, passed: 0, failed: 0 }
    ac_matrix:
      - ac_id: string
        status: PASS | FAIL
        evidence: string
    tech_lead_reviews:
      spec: { verdict: string, findings_count: 0 } or null
      plan: { verdict: string, findings_count: 0 } or null
      post_impl: { verdict: string, findings_count: 0 } or null
    dod:                          # Definition of Done — see SKILL.md
      spec_approved: { status: pass|fail, evidence: string }
      plan_approved: { status: pass|fail, evidence: string }
      implementation_complete: { status: pass|fail, evidence: string }
      build: { status: pass|fail|na, evidence: string }
      lint: { status: pass|fail|na, evidence: string }
      typecheck: { status: pass|fail|na, evidence: string }
      unit_tests: { status: pass|fail|na, evidence: string }
      integration_tests: { status: pass|fail|na, evidence: string }
      e2e_tests: { status: pass|fail|na, evidence: string }
      qa_ac_coverage_100pct: { status: pass|fail, evidence: string }
      tech_lead_approved: { status: pass|fail, evidence: string }
      no_critical_high_findings_open: { status: pass|fail, evidence: string }
      no_known_regressions: { status: pass|fail, evidence: string }
      specs_directory_changes_applied: { status: pass|fail, evidence: string }

stop:                            # only present while status: paused
  category: BUSINESS_STOP | TECHNICAL_STOP | SAFETY_STOP | EXTERNAL_ACTION_STOP
  item: <item-id>
  phase: <phase where it paused>
  reason: string
  evidence: string
  attempts_made: string or null   # for TECHNICAL_STOP after 3 cycles
  hypothesis: string or null
  decision_needed: string
  paused_at: <timestamp>

handoff:                          # only present once the epic is fully complete
  generated_at: <timestamp>
  report_path: <path to the Product Handoff document>
```

## Why not just add `mode:` to `workflow.yaml`?

Investigated directly: nothing in the SDD plugin's compiled code
(`check-gate.ts`) or documented schemas rejects unknown top-level keys —
technically an embedded field would work today. But `workflow.yaml` is
actively rewritten by the plugin's own documented procedures
(`advance`, `update_status`, `ready_for_review`, etc. — which, per this
plugin's actual implementation, are markdown-described procedures a Claude
session follows by hand, not compiled code). A future session following
that documented schema verbatim, with no memory of this local extension,
could reconstruct the file without it. A fully separate sidecar file has
zero exposure to that risk and makes the boundary between "SDD's format"
and "this project's local extension" unambiguous.
