---
name: kanban
description: "Local Markdown backlog, Jira style, versioned with the repo: one ticket per file in docs/backlog/ (epic, story, task, spike, bug), a kanban board in the terminal or in the browser (reloaded live, with the project documentation read-only: specs and their Gherkin scenarios, documentation written for humans), refinement notes where the questions asked and the user's answers are filed word for word as they come, and pushing to Jira through the Atlassian MCP. Use to show the board, create, read, move or check a ticket, add a refinement note, bootstrap a backlog in a repo, or push tickets to Jira. It is the product-owner's tool for keeping the backlog."
---

# Kanban: the local backlog

A repo's backlog lives in `docs/backlog/`. It is the **source of truth** for the tickets: their split into epics, their order, their status, their refinement notes and the link to their spec. It is versioned with the code, so it is read in the diffs. Jira, if connected, only receives a copy, on request.

The folder's `README.md` describes the format for a human or an agent that does not have this skill: keep it up to date if the format changes.

## Commands

The script needs only Python 3 (standard library) and runs from anywhere in the repo:

```sh
python3 -I <this skill's directory>/scripts/kanban.py <command>
```

`<this skill's directory>` is the directory of this file: for example `~/.claude/skills/kanban` in Claude Code, `~/.copilot/skills/kanban` in Copilot, `~/.config/opencode/skills/kanban` in opencode. Below, `kanban.py` stands for that whole command. An agent writes it in full at every call: an alias or a variable does not carry over from one shell call to the next, and zsh does not split a `$K` variable into words. For the user, suggest the alias `alias kanban='python3 -I <this skill's directory>/scripts/kanban.py'` in their `~/.zshrc`, with the real path.

```sh
kanban.py                    # the board in the terminal (= board; --epic KEY, --all)
kanban.py serve              # the board and the documentation (/doc/) in the browser, on 127.0.0.1:8765, reloaded live
kanban.py html               # the same board in a standalone HTML file, opened in the browser
kanban.py check              # checks every ticket; exit code 1 on error
kanban.py new "Title" --type story --epic BOU-1 --rank 5 --summary "The need in one sentence."
kanban.py move BOU-4 in-progress --reason "spec validated"
kanban.py to-push [--json]   # what is left to create or update in Jira
kanban.py sync BOU-4 --jira ABC-12
kanban.py init --project Boutique --prefix BOU
```

`--dir DIR` (before the command) points to another backlog.

The browser board is read-only: you change the files (by hand, through an agent or with `move`), and the board follows.

The browser texts follow its language (English or French, English by default): `assets/messages.json`. The command line is in English.

## Bootstrapping a backlog

In a repo without `docs/backlog/`, first ask whether the project wants one (an agent launched by another one proposes it in its answer rather than doing it). With the user's agreement:

1. `kanban.py init --project <Name> --prefix <PRE>`;
2. carry over the known split: an epic, and one ticket to refine per slice, with its rank and a one- or two-sentence summary;
3. put in each ticket a note "Taken from <source>" that quotes what was already known about it (open questions, rules announced for a slice to come), with its source;
4. wherever the split was kept until then (a memory, a document), keep only a pointer to the backlog.

## Documentation

`kanban.py serve` also serves the project documentation, read-only, at `http://127.0.0.1:8765/doc/` (the "Documentation" link at the top of the board). Each page is rendered on request from its Markdown file and reloads when a file changes: you write in the files, as for the tickets.

- **The served directories**: the `documentation` key of `config.yml`, a list of directories from the repo root. Without the key: `[docs/specs, docs/documentation]`, that is the specs and the project documentation written for humans. A missing directory is not an error: the index says it has no pages yet. `documentation: []` serves nothing.
- **The index** (`/doc/`): one section per directory, subdirectories included, each page under its first `#` heading. `INDEX.md` or `README.md` comes first in its directory: it is its entry point.
- **A page** has its path from the repo root as its address (`/doc/docs/specs/onboarding.md`): a relative link between two pages (`[Glossary](glossary.md)`, `../specs/onboarding.md`) leads there as it is. A spec's page lists the tickets whose `spec` field designates it, and a ticket's panel has a "Spec page" link.
- **The rendering**, also that of the board's panel: headings, paragraphs, lists (nested, numbered), tables, code blocks (in a ```` ```gherkin ```` block, keywords, scenario titles, `<…>` variables and comments are highlighted), blockquotes, bold, italics, inline code, links. All the text is escaped: HTML written in a file shows as it is, except `<!-- … -->` comments, which do not show. Not rendered: images (a link to the file, which is not served), column alignment, tables without a `|` at the start of the line, code indented by four spaces, underlined headings (`===`).
- **What is served**: only the `.md` files of the configured directories, and only on `127.0.0.1`. A path that goes up (`..`) or is absolute, a symbolic link that leads out of the repo root or of the directories, another file type: the page is "not found". A request whose `Host` header is neither `127.0.0.1` nor `localhost` (with or without a port) gets a 403 without any data, board included: another site's page that points its name to 127.0.0.1 (DNS rebinding) reads nothing.

## Files

```
docs/backlog/
  config.yml        project, key prefix, Jira mapping, documentation directories (one "key: value" line each)
  README.md         the format, for whoever does not have this skill
  tickets/
    BOU-1-first-launch.md
    BOU-13-onboarding.md
```

## A ticket

A simple YAML front matter (one `key: value` line per field, lists as `[a, b]`), then three sections:

| Field | Required | Meaning |
|---|---|---|
| `key` | yes | `<PREFIX>-<n>`, never reused; the file is named `<key>-<title>.md` |
| `title` | yes | the ticket's title |
| `type` | yes | `epic`, `story`, `task`, `spike` or `bug` |
| `status` | yes | a column, below |
| `created` | yes | creation date, `YYYY-MM-DD` |
| `epic` | | the key of the epic that contains it (an epic is in no epic) |
| `rank` | | its order in the epic: for a story, its slice number (shown as "S4") |
| `spec` | | the path of its spec, from the repo root |
| `blocked_by` | | the keys of the tickets that must come first |
| `jira`, `jira_sync`, `jira_fingerprint` | | set by `sync`, not to be written by hand |

- `## Summary`: the need in one or two sentences, as the split states it. No refining.
- `## Refinement notes`: the raw material, below.
- `## History`: one dated line per event (created, moved, pushed to Jira, spec written from the notes up to …). `move` and `sync` write it themselves.

## Columns

| Status | Column | The ticket… | Moved by |
|---|---|---|---|
| `to-refine` | To refine | has a title, a summary and notes | (creation) |
| `refining` | Refining | has a spec being written | the product-owner |
| `ready` | Ready | has a spec validated by the user | the product-owner, or the orchestrator at validation step 1 |
| `in-progress` | In progress | is in development | the orchestrator, or the user |
| `in-review` | In review | is delivered, under review | the orchestrator, or the user |
| `done` | Done | is accepted | the orchestrator at validation step 3, or the user |
| `abandoned` | hidden | is withdrawn, with the reason in its History | whoever withdraws it, with the user's agreement |

Always move with `move` (it records the change in the History). A ticket is never deleted: it goes to `abandoned` with a `--reason`.

## Refinement notes

What the user said about a ticket before it gets refined: their answers, and the questions that drew them out. They are costly to obtain; a summary loses their meaning. One note per exchange, the most recent last:

```markdown
### 2026-10-22 · during BOU-2, batch 3, Q4 · asked by the product-owner
**Question**
> The question as it was asked, with its options and the recommendation when the answer refers to it ("reco", "B").

**Answer**
> The user's answer, word for word.

Memory: R-024
```

- **The heading** starts with the date, then where the exchange comes from (ticket in progress, batch, question number) and who asked the question (product-owner, software-architect, software-engineer, quality-analyst, orchestrator). A clarification the user gives without being asked is written `**Clarification**` in place of the question-answer pair.
- **Word for word.** Rephrase neither the question nor the answer, do not fix typos. Cut only what does not concern the ticket, marking the cut `[…]`.
- **Add, do not rewrite.** A note is completed or corrected by a later note. An answer that concerns several tickets is noted in each of them.
- **Do not refine.** No rule, no scenario, no further question: the ticket gets refined when its turn comes.
- **The last line** (optional) cites what the exchange changed elsewhere: a memory entry, a spec.

## Rules

- **Read before writing**: the board (`kanban.py`), then the whole ticket. To find a ticket by its Jira key: `grep -l "^jira: ABC-12" docs/backlog/tickets/*.md`.
- **Write**: create with `new` (it gives the next key), move with `move`, add the notes and the summary by editing the file. Start each note with today's date (`date +%F`).
- **Check** after every change: `kanban.py check` must pass without errors.
- **Nothing is committed or pushed to Jira without the user's agreement.**

## Jira

To push tickets, start from a Jira ticket or set up the mapping of types and statuses: read `references/jira.md` (procedure with the Atlassian MCP).

## Changing the skill

- **The entry point** `scripts/kanban.py` stays thin, and changes neither name nor place: the agents, the aliases and the README of existing backlogs cite it.
- **The code** lives in `scripts/kanban_lib/`, one module per responsibility. The map of the modules and the rule for their imports are in the docstring of `scripts/kanban_lib/__init__.py`.
- **The templates** (styles, pages, board script, README of a new backlog) live in `assets/`. `html` copies those of the board into the page it writes, so that it stays standalone.
- **Standard library only**, Python 3.9 or later: the skill works without `pip`.
- **The commands, options, messages and exit codes do not change**: the agents read them.
- **The tests**, from the skill directory, after any change to `scripts/` or `assets/`: `python3 -I -B -W error scripts/selftest.py`.
