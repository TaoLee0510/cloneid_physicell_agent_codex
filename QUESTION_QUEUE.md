# Question Queue

This file is maintained by the agent. It should accumulate questions for the user's noon and evening review windows.

Questions should not block all work unless they are high-risk. When possible, the agent should stop the dependent branch, record the question, and continue with independent tasks.

---

## Blocking before next real-data milestone

## Q001 — Read-only CLONEID connection details

**Priority:** Blocking  
**Risk level:** 3  
**Question:** What exact read-only CLONEID access should this repository use for the first real database inventory: a live database URL, a local mirrored instance, or a sanctioned frozen snapshot?

**Why it matters:** Real database inventory, schema verification, and dataset discovery cannot proceed safely without an approved source of truth. Inventing connection details or guessing across deployments would be a high-risk scientific and provenance error.

**Options:**
1. Provide a live read-only `CLONEID_DB_READONLY_URL`.
2. Provide access to a local mirrored CLONEID instance with the same schema.
3. Provide a sanctioned snapshot fixture for offline development first.

**Current default assumption:** No real database access is available yet; continue with offline scaffolding and toy fixtures only.

**Blocked work:** Live database inventory, query testing, dataset discovery, and any claim about what data actually exist.

**Work continuing meanwhile:** CLI scaffolding, schemas, toy fixtures, dry-run artifact generation, provenance structures, and report templates.

**Agent recommendation:** Option 1 if a safe read-only account already exists; otherwise Option 3 as a short-term bridge for offline testing.

**Status:** Open

---

## Important but not blocking today

## Q002 — PhysiCell runtime source for the first smoke test

**Priority:** Important  
**Risk level:** 2  
**Question:** Where should the first PhysiCell smoke test come from: an existing local binary, a build path in this environment, or external instructions not yet added here?

**Why it matters:** The repository currently has model-family placeholders but no executable, no build notes, and no example config files. A local-test or execution branch should not be started blindly.

**Options:**
1. Provide a local `PHYSICELL_BIN` path.
2. Provide build/install instructions to reproduce a local binary.
3. Defer execution and stay in dry-run mode until runtime assets are supplied.

**Current default assumption:** Stay in dry-run mode and generate stub model folders only.

**Blocked work:** PhysiCell smoke testing, local-test mode, and validation of generated model folders against a real executable.

**Work continuing meanwhile:** Template-folder conventions, dry-run config stubs, toy round-trip evaluation, and report generation.

**Agent recommendation:** Option 3 for now unless a known-good local binary already exists.

**Status:** Open

---

## Clarifications / preferences

## Q003 — First real-data milestone selection policy

**Priority:** Clarification  
**Risk level:** 2  
**Question:** Once database inventory exists, should the first real proof of principle prioritize a density-selection/growth trajectory dataset, a treatment-response dataset, or should selection remain fully score-driven until reviewed?

**Why it matters:** This choice influences which mapping assumptions and evaluation targets become most important, but it should not be guessed before inventory exists.

**Options:**
1. Keep selection fully score-driven and review the top candidates.
2. Prefer an untreated or minimally perturbed growth/density dataset first.
3. Prefer a treatment/stressor dataset first.

**Current default assumption:** Keep the code path generic and defer the real-data choice until inventory outputs can be reviewed.

**Blocked work:** No current Milestone 0 work is blocked.

**Work continuing meanwhile:** Generic inventory, scoring, mapping, and dry-run infrastructure.

**Agent recommendation:** Option 1, with a likely bias toward simpler growth/density datasets for the first executed round trip if scores are comparable.

**Status:** Open

---

## Resolved questions

_No resolved questions yet._

---

## Question template

```markdown
## Q001 — Short title

**Priority:** Blocking / Important / Clarification  
**Risk level:** 1 / 2 / 3  
**Question:** ...

**Why it matters:** ...

**Options:**
1. ...
2. ...
3. ...

**Current default assumption:** ...

**Blocked work:** ...

**Work continuing meanwhile:** ...

**Agent recommendation:** ...

**Status:** Open / Answered / Superseded
```
