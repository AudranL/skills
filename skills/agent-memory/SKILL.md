---
name: agent-memory
description: "Protocol for the memory an AI agent keeps in a project (for instance docs/ai/agent-name/): an index that says when to read each file; one entry per heading, whose title states the fact; three statuses (confirmed, verified, deduced), what each one settles, and how a deduced entry gets validated (by the user for an intent, by running it for a fact about the code); a source that says what makes the entry true today; dated quotes of what an entry relies on, code included, references only to a numbered item; an entry rewritten rather than appended to; dated snapshots; decisions, questions and debt; bootstrapping with the project's consent; pruning before splitting; handing entries over to another agent; reporting changes, and the separate commit. Load at the start of any task that relies on the memory, and before bootstrapping it, writing or correcting an entry, reorganizing it, or handing entries over to another agent."
metadata:
  internal: true
---

# An agent's memory in a project

A memory spares the agent from rediscovering, at each task, what it has already learned in this project, and from asking again the questions already settled. It must cost less to read than what it replaces: it states the present, in few words, and points to the rest.

## What the agent provides

The agent that relies on this skill states, in its section on memory:

- **its folder** in the project (for instance `docs/ai/<agent>/`);
- **the table of its files**: what each one holds, the kind of its entries (`references/formats.md`) and the prefix of its IDs;
- **the names of its statuses** and of its report headings, in its own language;
- **its bootstrapping sources**, and what, in its role, goes into its memory or stays out.

**Each memory is read and written by one agent only: its own.** The team reads it in the diff; no other agent opens it. An agent asks another one its questions, or receives what the other hands over (see "Handing over a responsibility").

## Index and entries

- **`INDEX.md` is read first: one short line per file, saying in which situation to read it** ("before writing a test", "when a slice touches the database schema or the backups"), without the list of its entries or any history. To find an entry cited elsewhere: `grep -rn '^### R-012' <folder>`.
- **Elsewhere, one entry per `###` heading, readable on its own.** An ID is never reused or renumbered.
- **The title states the fact or the rule, not its subject**: "O-002 · Stay on Vitest 4.0 while npm is at version 10", not "O-002 · Vitest version". Reading the titles alone (`grep '^### '`) then gives the gist of a file. The exceptions are the kinds looked up by a key, whose title is that key: a procedure by its goal ("Run the end-to-end tests on the built application"), a snapshot by its zone and date, a recurring check by its requirement (`references/formats.md`).
- **One entry, one fact, one status.** A part whose status differs (a deduced detail in a confirmed rule, a hypothesis waiting for an answer) is an entry of its own, or a question. An entry that grows past a screen usually holds several facts.
- **A file's header says what the file holds and the format of its entries**, in a line or two. It states no fact: a fact without a status and a source is a missing entry.

```markdown
### R-003 · A payment service outage is never shown as a declined payment
- Status: confirmed · Source: notes of ABC-123 (YYYY-MM-DD)
- Why: "declined" pushes the customer to change cards, although theirs is valid.
- <What serves the next task: examples, consequences, limits, options already rejected.>
- See also: D-002
```

Procedures, questions, decisions, debt, user instructions, snapshots and state files have their own fields: read `references/formats.md` before creating the first entry of a kind.

## Statuses

Each agent says which of these it uses, and names them in its language.

- **confirmed**: said or validated by the user, or written in a document they validated (a validated spec, an accepted ADR). When several people work on the project, the entry says who.
- **verified**: observed by running it (a command, a test). The entry says when, on what (version or commit) and what was observed, and what was not run again: "verified (YYYY-MM-DD, 2.3.0 at commit abc1234: 45 end-to-end journeys green in 50 s)". It needs no validation.
- **deduced**: read in the code, the configuration, the tests or the documentation, source cited. It settles nothing until it is validated or verified.

There is no "hypothesis" status. What the agent assumes while waiting for an answer is the retained hypothesis of a question (`references/formats.md`), and an entry that relies on it points to that question.

A deduced entry is validated according to what it says:

- **An intent** (a business rule, a convention, a decision: what someone wants) is submitted to the user, in the same response or at the latest at the end of the task, grouped with the others: "I deduce from the tests that they are named in `snake_case` (C-002): is that the convention?". Validated, it becomes confirmed; corrected, it is rewritten and confirmed; refused, it is removed or becomes a question.
- **A fact about the code or a tool** (what a command does, what a function returns) is checked by running it, and becomes verified. If it cannot be run, it stays deduced, says what would verify it, and is not submitted to the user: they are not the source of that fact.

## Reading

- **At the start**, read `INDEX.md`, then only the files the task needs. Without a folder, bootstrap it (see "Bootstrapping").
- **A confirmed or verified entry settles the point**: do not ask again, do not rediscover what it says.
- **A verified entry that turns out false** (a command fails) is corrected, then verified again.
- **A request or a fact that contradicts a confirmed entry is raised with the user, citing the entry**: "R-003 says the opposite: do we change the rule or the request?". The agent does not correct a confirmed entry on its own.
- **A deduced entry is confirmed in passing** when the agent relies on it: "I am going from R-005 (deduced from the code): is it still true?".
- **A dated entry is a snapshot**: before relying on it, check whether what it describes has changed since its date (`git log --since=<date> --oneline -- <path>`); if so, check again, then rewrite it.

## Quoting rather than referring

A quote freezes what the entry relies on at the date it was written; a reference follows the document as it changes, and loses why the entry was written.

- **An entry quotes what it relies on, dated, with its source**: the reason for a decision, the user's words, the passage of a spec, an ADR, a ticket note or a published text. If the document changes later, the entry still says what it said then, and why it was written. Only the passage the entry needs, never the whole document.
- **A pointer to a numbered item is not quoted**: an entry (R-009), a requirement (NFR-04), a ticket (ABC-142), when the entry only points to it. It is read as it is now.
- **The code and the configuration are quoted like the rest**: the lines the entry relies on, with their path and commit. Before relying on the quote, `git diff <commit> -- <path>` tells whether they have changed since.
- **The user's words are quoted once in the memory, in the entry they settle** (the why of a decision, a user instruction): the passage that matters, not the whole exchange. Other entries point to that one.
- **A thing is designated by what does not change in it**: a rule from an agent's file by its title, since its number changes ("the rule 'Ask before writing'", not "rule 11"); a memory entry by its ID, which is never reused; a ticket note by its ticket and date; a file by its path.
- **Another agent's memory is neither referred to nor quoted**: it cannot be read, and its entries change. Write the fact, dated, and where it comes from ("the software engineer observed on YYYY-MM-DD that…"): a dated observation stays true.
- **A state of the product is written only dated, in a snapshot**: undated ("current version", "for now", "today"), it becomes false at the next commit. What the code does now is read in the code.
- **The source says what makes the entry true today**: one or two references, not the list of everything that ever touched it. The history stays in git and in the notes.

## Bootstrapping

1. **Ask first** whether the project wants this memory, and where (by default, the agent's folder); in delegated mode, through the agent that launched it. A prompt that invites the agent to write is not the user's consent. A refusal holds for the whole session: do not ask again.
2. **With consent, create it** from the agent's sources, as deduced, except what a validated document already says (confirmed) and what a command run verifies (verified). Few entries: only what serves the role. A file is created with its first entry, and `INDEX.md` lists only files that exist.
3. **Submit the deduced intents** to the user, and open one round of questions about what is missing.
4. **Say so** in the report.

## Writing

- **Capture a durable fact as soon as it appears**: a user answer that settles a point, a command that works after a failure, what a task taught. The agent writes without asking: each entry carries its status and its source, and the diff is reviewed. Only an explicit answer from the user, or a document they validated, makes an entry confirmed.
- **What goes in**: what will hold for the next task in this project. **What stays out**: the detail of a task, what another document already holds (quote only the passage the entry relies on: see "Quoting rather than referring"), the rules of the agent's role (they hold for every project and belong in the agent's file), what belongs to another agent's role.
- **Shareable**: the memory is versioned with the project. Nothing that depends on one machine (a personal path, a command for one system without its equivalent for the others); every path written from the repository root; no secret.
- **Changing an entry means rereading it whole and rewriting it** so that it states the present: no "Addendum of…", "Corrected on…" or "Previously…" lines, which leave the old version next to the new one, sometimes contradicting it. Edit the entry in place rather than rewriting the file from an earlier read.

## Maintaining

- **An entry states the present, not its history.** Past tasks, successive corrections and long quotes go to version control and to the source documents; the entry links to them.
- **A contradicted rule is replaced, not stacked.** If the agent keeps a decisions file, the decision says why and what was rejected, without restating the rule; a decision replaced by another one leaves the file.
- **An answered question leaves the questions file**: its answer joins the entry it settles, as confirmed, with the answer as its source. No list of answered questions, no "ex-" IDs. A paid-off debt leaves its file too, with the date in the commit.
- **A state file** (where the work stands, what comes next) is rewritten whole and dated each time; what is done leaves it.
- **Prune before splitting**: history, stale state, sources that list everything, entries that repeat another document. A file that still exceeds 150 lines or 12,000 characters is split by subject (for instance `rules-<subject>.md`), without renumbering its entries, and `INDEX.md` is updated.

## Handing over a responsibility

When a responsibility moves from one agent to another (end-to-end tests, from the software engineer to the quality analyst), its entries move with it:

- **The agent that hands it over** returns the entries concerned in a section of its response addressed to the other agent ("For the <agent>", in its language). In delegated mode, the agent that launched both relays it as is; otherwise, the user passes it on. Then it removes those entries from its memory and updates its `INDEX.md`.
- **The agent that receives it** files them in its memory, with its own IDs and format. What can be run (a command) is run again before being marked verified; the rest keeps the source "handed over by <agent> on <date>", as deduced until confirmed or verified.

## Reporting changes

- **At the end of the response**: the entries added, changed or removed, each with its file, its ID and one line.
- **In delegated mode**: in a section of the response named after the memory ("Business memory", "QA memory"… in the agent's language), before the status line if the agent ends with one. The deduced intents are grouped under a "To validate" heading, each with the question to ask, so that the launching agent submits them to the user.
- **Commit**: memory changes go in a separate commit (for instance `docs(ai): …`), made by the agent that commits in this project, and only when commits are allowed.
