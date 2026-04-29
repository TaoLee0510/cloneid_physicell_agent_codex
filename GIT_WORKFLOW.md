# Git Workflow for Agent Work

## Purpose

Git should make the project safer, not slower. Use Git to preserve coherent work units and make it easy for the user to review or roll back changes.

Do not use Git as a substitute for careful reasoning, tests, or status updates.

---

## Required startup check

At the beginning of every work session, run:

```bash
git status --short
git branch --show-current
```

If there are existing uncommitted changes that you did not make, do not overwrite them.

Record the repository state in `STATUS.md`.

---

## Commit policy

Commit after each coherent, tested work unit.

A work unit is something like:

- adding a read-only database inventory wrapper,
- adding mock inventory mode,
- adding tests for database inventory,
- adding documentation for the CLONEID package interface,
- adding a PhysiCell dry-run scaffold,
- adding report generation.

Do not commit after every tiny edit.

Do not commit broken work unless explicitly instructed. If work is incomplete but useful, leave it uncommitted and document the state in `STATUS.md`.

Before committing, run the relevant tests or checks if available.

Example:

```bash
git status --short
pytest
git add <changed files>
git commit -m "Add read-only CLONEID inventory wrapper"
```

If tests cannot be run, document why in `STATUS.md` and in the commit message body.

---

## Branch policy

Stay on the current branch for normal safe work.

Create a new branch only when doing exploratory or risky work, such as:

- testing a major restructuring,
- changing project layout,
- replacing a working implementation,
- introducing a new dependency,
- experimenting with an uncertain PhysiCell integration path.

Branch naming:

```bash
git checkout -b agent/<short-task-name>
```

Examples:

```bash
git checkout -b agent/physicell-dry-run
git checkout -b agent/db-inventory-wrapper
```

Do not create branches for ordinary documentation edits or small deterministic utilities.

---

## Push policy

Do not push to any remote unless the user explicitly asks.

Do not open pull requests unless the user explicitly asks.

---

## History safety

Never run these commands unless the user explicitly asks:

```bash
git reset --hard
git clean -fd
git rebase
git push --force
git commit --amend
```

Never delete branches unless the user explicitly asks.

---

## Handling user changes

If files changed by the user are present, do not overwrite them.

If your task requires editing a file with user changes:

1. inspect the diff,
2. preserve user edits,
3. make the smallest compatible change,
4. document the potential conflict in `STATUS.md`.

---

## Stop rule related to Git

Before stopping, make sure one of the following is true:

1. the current work unit is committed,
2. the current work unit is intentionally left uncommitted because it is incomplete or untested,
3. committing is unsafe because tests failed or the repo state is ambiguous.

In all cases, record in `STATUS.md`:

- current branch,
- uncommitted files,
- last commit hash if available,
- tests/checks run,
- whether the work is committed or intentionally left uncommitted.

---

## Interaction with supervised autonomy

This Git workflow does not override `SUPERVISED_AUTONOMY.md`.

If a task is safe, reversible, deterministic, and does not require user judgment, continue working after committing the completed work unit.

Do not stop merely because a commit was made.

After each commit:

1. update `STATUS.md`,
2. re-read `WORK_QUEUE.md`,
3. continue to the next safe unblocked task unless the stop checklist requires stopping.

---

## Recommended commit-message style

Use concise imperative commit messages.

Good examples:

```text
Add read-only CLONEID inventory wrapper
Add mock inventory mode
Document CLONEID database access path
Add PhysiCell dry-run scaffold
Add model-comparison report template
```

Avoid vague messages:

```text
updates
misc fixes
work
changes
```

When useful, include a short commit body explaining:

- what changed,
- what tests were run,
- what remains incomplete,
- whether any assumptions were made.

---

## Forbidden shortcuts

Do not use Git commands to hide uncertainty or bypass review.

In particular:

- do not discard work to make the tree look clean,
- do not rewrite history to conceal failed attempts,
- do not delete untracked files unless explicitly instructed,
- do not use force-push,
- do not use `reset --hard`,
- do not amend commits unless explicitly instructed.

A messy but documented state is better than a clean state created by unsafe deletion.
