# Decision Log Format

Mandatory in autonomous mode. Every decision the Orchestrator makes on its
own (i.e., anything that isn't already fully mechanical, like "run the
build command") gets an entry — both routine technical decisions
(reusable investigation, tool choice, minor scope interpretation) and
STOP-condition resolutions once a human responds. Never delete entries;
this log has to let someone reconstruct, after the fact, why the system did
what it did.

Stored per-item, inside `autonomy.yaml` under `items.<item-id>.decisions`
(see [autonomy-yaml-schema.md](./autonomy-yaml-schema.md)), or as a
dedicated `decisions.md` file alongside the item if the log grows large
enough that embedding it in YAML gets unwieldy — the Orchestrator's choice,
as long as the shape below is preserved and it's discoverable from
`autonomy.yaml`.

## Format

```markdown
## D<n> — <short title>

**Decisão:** <what was decided>
**Alternativas:** <what else was considered, even briefly — "none" is a valid answer only if there genuinely was no choice>
**Evidências:** <what was read/run/tested to inform this — file paths, command output, doc references>
**Motivo:** <why this option over the alternatives>
**Impacto:** <what this affects — files, other features, future decisions>
**Arquivos alterados:** <files touched as a direct result of this decision, if any>
**Testes/evidências:** <what proves this decision worked — test names, QA AC ids, build output>
**Autorização necessária:** sim | não
```

`Autorização necessária: sim` marks entries where a human's response was
required (i.e., this decision followed a STOP condition) — these entries
additionally record the human's literal answer, not just the Orchestrator's
paraphrase of it.

## Numbering

`D<n>` is sequential per item, never reused, never renumbered even if an
earlier decision is later superseded — mark a superseded decision by adding
a new entry that says so and references the old `D<n>`, the same way the
SDD's own SPEC Requirements Discovery trail handles corrections (never edit
history, append the correction).

## When an entry is required

- Any technical decision with more than one reasonable option (tech-lead's
  own findings don't need a separate decision entry — they're already
  structured; but the Orchestrator's choice of *how to respond* to a
  finding, e.g. "route to bug-fixer vs. implementer", does).
- Every STOP condition raised, whether or not it ends up pausing (a
  proposed `stop_condition` from an agent that the Orchestrator determines
  does *not* actually qualify is still worth one line explaining why it was
  dismissed — this is what lets a human audit that the system isn't quietly
  rationalizing past real stops).
- Every human response after a pause.
- Every time a review/fix cycle counter increments — cheap enough to log,
  and it's exactly the kind of thing you want at hand when reconstructing
  "why did this take 3 tries."
