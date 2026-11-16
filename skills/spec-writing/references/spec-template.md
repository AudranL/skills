# Spec template

The spec is read by an agent with a limited context: **it must stay short**, without repetition between sections or history of the discussion. Brevity applies to the prose; the Gherkin takes the room it needs for each rule to have its nominal case and its boundary cases. The signal of a spec that is too big is the number of rules (beyond four or five), not the number of lines: split the slice again. An empty section is removed, not filled with "N/A".

**Location**: the project's convention if there is one (a `specs/` folder, `docs/specs/`…), otherwise `docs/specs/<TICKET-KEY>-<slug>.md`, or `docs/specs/<slug>.md` without a ticket. Outside a repository, ask where to write it.

**Language**: the language of the project's existing specs; if there are none, ask the user. The headings and the Gherkin keywords follow it (French equivalents at the end of this file and in `gherkin.md`).

**The spec reads on its own**: the developer reads neither the product owner's memory nor the backlog. What they need for the slice is copied into the spec (Vocabulary, Known constraints). It may point to a document the whole team reads (the non-functional requirements file, an API contract in the repository).

## A story

````markdown
# <TICKET-KEY> — <Slice title>

Ticket: <TICKET-KEY> · Jira: <JIRA-KEY or "not in Jira"> · Slice <n>/<total> · Status: ready | open questions

## Why
<The problem and the business goal in 2 to 4 sentences. The observable signal that will say it worked.>

## For whom
<The role(s), named as the business names them (not "the user"), and the situation they are in when they need it.>

## Scope
- In this slice: <…>
- Later (next slices): <…>
- Out of scope: <…, including a case the user says never happens>

## Scenarios
```gherkin
Feature: <title>
  In order to <business goal>
  As a <role>
  I want <capability>

  Rule: <business rule 1>

    Scenario: <what sets this case apart>
      Given <business context>
      When <action>
      Then <observable outcome>
```

## Vocabulary
| Term | Meaning here | In the code |
|---|---|---|

## Open questions
- <Question> → <who can answer, or the assumption made meanwhile>

## Known constraints
<Only real constraints: an imposed external system, an existing contract, a regulation, and the non-functional requirements the slice touches, by their identifier. No design.>
````

The `gherkin` block must be copyable as is into a `.feature` file. The "In the code" column is filled only when the code uses another word than the business.

## A bug

The same template, reduced to what the fix needs:

- **Why**: what was observed (by whom, when, with which data) and the rule it breaks;
- **Scenarios**: under the broken rule, the scenario that reproduces the report with its real values, whose "Then" states the expected behavior; when the bug sits on a threshold, the case on the other side too;
- **Scope**, **Vocabulary**, **Known constraints** only if they say something.

## A spike

````markdown
# <TICKET-KEY> — <The question to answer>

Ticket: <TICKET-KEY> · Timebox: <duration> · Status: ready | open questions

## Question
<The question, and why the slice it blocks cannot be sized or specified without its answer.>

## Expected output
<An answer with what supports it, a measurement, a recommended option among those compared, a throwaway prototype. Never production code.>

## Unblocks
<The slice or the decision that waits for the answer.>
````

## French headings

| English | French |
|---|---|
| `Ticket: … · Slice <n>/<total> · Status: ready \| open questions` | `Ticket : … · Tranche <n>/<total> · Statut : prête \| questions ouvertes` |
| Why | Pourquoi |
| For whom | Pour qui |
| Scope: In this slice, Later, Out of scope | Périmètre : Dans cette tranche, Plus tard, Hors sujet |
| Scenarios | Scénarios |
| Vocabulary: Term, Meaning here, In the code | Vocabulaire : Terme, Sens dans ce contexte, Dans le code |
| Open questions | Questions ouvertes |
| Known constraints | Contraintes connues |
| Spike: Timebox, Question, Expected output, Unblocks | Durée maximale, Question, Résultat attendu, Débloque |
