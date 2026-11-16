# {project} backlog

This folder is the **local backlog** of {project}: the source of truth for the tickets (epics, stories, tasks, spikes, bugs), their order, their status and their refinement notes. It is versioned with the code. Jira, if connected, is only a copy: tickets are changed here, never there.

## Seeing the board

```sh
alias kanban='python3 -I <kanban skill directory>/scripts/kanban.py'   # to put in ~/.zshrc
# <kanban skill directory>: for example ~/.claude/skills/kanban, ~/.copilot/skills/kanban or ~/.config/opencode/skills/kanban
kanban          # the board in the terminal
kanban serve    # in the browser, on 127.0.0.1:8765, reloaded at every change
```

## Reading the documentation

`kanban serve` also serves, read-only, the project documentation at `http://127.0.0.1:8765/doc/` (the "Documentation" link at the top of the board): the specs and their Gherkin scenarios, and the documentation written for humans. The pages reload when their files change; a ticket's `spec` field leads to the page of its spec.

The served directories are set in `config.yml`, from the repo root:

```yaml
documentation: [docs/specs, docs/documentation]   # the default value, without the key
```

Only the `.md` files of these directories are served. A missing directory is not an error. `INDEX.md` or `README.md` is the entry point of its directory, and a relative link between two files (`[Glossary](glossary.md)`) leads from one page to the other.

## Columns

| Status | Column | The ticket… |
|---|---|---|
| `to-refine` | To refine | has a title, a summary and draft refinement notes |
| `refining` | Refining | has a spec being written |
| `ready` | Ready | has a validated spec |
| `in-progress` | In progress | is in development |
| `in-review` | In review | is delivered, in acceptance and architecture review |
| `done` | Done | is accepted |
| `abandoned` | hidden | is withdrawn; the reason is in its history. A ticket is never deleted. |

## A ticket

One file per ticket: `tickets/{prefix}-<n>-<title>.md`. A key is never reused.

```markdown
---
key: {prefix}-4
title: Zone and holidays
type: story              # epic | story | task | spike | bug
status: to-refine
epic: {prefix}-1        # optional: the epic that contains it
rank: 4                  # optional: its order in the epic (slice 4)
spec: docs/specs/x.md    # as soon as it is refined
blocked_by: [{prefix}-2, {prefix}-3]   # optional
jira: ABC-12             # set by the Jira sync, like jira_sync and jira_fingerprint
created: 2026-10-22
---

# {prefix}-4 · Zone and holidays

## Summary
The need in one or two sentences.

## Refinement notes
The questions and the answers that concern it, as they come (below).

## History
- 2026-10-22 · created
```

## Refinement notes

The raw material for refining, until the ticket's turn comes. One note per exchange, the most recent last:

```markdown
### 2026-10-22 · during {prefix}-2, batch 3, Q4 · asked by the product-owner
**Question**
> The question as it was asked, with its options and the recommendation if the answer refers to it.

**Answer**
> The answer, word for word.

Memory: R-024
```

- Word for word: neither the question nor the answer is rephrased. A clarification given without a question is written `**Clarification**`.
- Add, do not rewrite: a note is corrected by a later note.
- Do not refine: no rule, no scenario, no further question. The ticket gets refined when its turn comes.

## Commands

```sh
kanban new "Title" --type story --epic {prefix}-1 --rank 5 --summary "The need in one sentence."
kanban move {prefix}-4 in-progress --reason "spec validated"
kanban check                          # after any change by hand
kanban to-push                        # what is left to create or update in Jira
kanban sync {prefix}-4 --jira ABC-12  # after pushing the ticket to Jira
```
