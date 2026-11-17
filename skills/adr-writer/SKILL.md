---
name: adr-writer
description: "Write, complete, supersede and deprecate ADRs (Architecture Decision Records) in any project, without a specialized agent: when a decision deserves an ADR; the project's conventions (folder, template, language and numbering of the existing ADRs, asked for when there are none); the default template; how to write each section (forces and their tensions, decision factors with thresholds, at least two options, consequences good and bad, how the decision is checked); the lifecycle (Draft, Accepted, Rejected, Deprecated, Supersedes) and corrections; the questions to ask. Load to create, write, update, deprecate or supersede an ADR, or when the user describes an architecture decision to record."
---

# ADR Writer

An ADR (Architecture Decision Record) explains **why** the team made a design choice: the context, the requirements that drove the decision, the options considered, the decision and its consequences. It is a short Markdown file (one or two pages), kept in the repository next to the code it concerns, so that its history follows the code's.

**The problem it solves.** When the reason behind a decision is lost, whoever comes next has two bad options: keep it without knowing whether it still holds, or undo it without knowing what it protected. Either way, they guess. Large documents are neither read nor kept up to date; small ones, one per decision, stand a chance.

**What it is for.** Onboarding someone who was not there; evolving the architecture without reopening the same debates, since the rejected options and their reasons are written down; aligning neighboring teams (architecture, security); keeping track of long-term intentions (a planned rewrite, for instance).

**Who it is written for.** A reader who was not there: a newcomer, or the team that will take the application over. Write it the way you would explain the decision to that developer face to face: in full sentences that carry the reasoning, not only the outcome.

## Portability

This skill works on its own, with no specialized agent, subagent, local configuration or required repository layout. In the project at hand, it discovers the existing conventions instead of assuming a path or a template; when the project or the information it needs is out of reach, it asks only for what is missing.

## When to write an ADR

For an **architecturally significant** decision: one that affects the structure, the non-functional qualities, the dependencies, the interfaces or the way the system is built. In practice:

- a technical problem with no existing basis for deciding (no recommended solution, standard procedure or precedent in the code);
- a chosen solution documented nowhere the team can reach;
- two or more options, whose reasoning must be kept.

Typically: choosing or changing an architecture style, splitting into bounded contexts, the boundary with an external system, choosing a product or its configuration (database, messaging, high availability), a build dependency that shapes the project, a deliberate exception to a rule, an architecture convention.

Not for an implementation detail: tell the user instead of writing the ADR.

## Project conventions

Before writing, find the project root from the context at hand, then look for existing ADRs in the repository (for instance in `docs/architecture_decisions/`, `docs/adr/`, `doc/adr/`, `docs/decisions/`). These paths are examples, not prerequisites. If one of them exists, look for a template (`template.md` or equivalent).

| Point | ADRs exist | No ADR |
|---|---|---|
| **Folder** | The existing ADRs' folder | **Ask the user for the path.** If a template exists, suggest its folder. |
| **Template** | The project's template if there is one, otherwise the one below | Same |
| **Language** | The existing ADRs' language | **Ask** the user, do not assume |
| **Name and number** | The existing ADRs' scheme, the number after the highest | `NNN-<kebab-case-slug>.md`, starting at `001` |

- The project's template prevails: keep its sections, add none.
- The existing ADRs set the tone and the level of detail: stay consistent with them.
- A number is never reused, even for a rejected or deprecated ADR.
- If another skill triggers with its own ADR format or criteria (for instance `domain-modeling`), follow this one and the project's existing ADRs.

## Template

For a project with no template. The text between `<…>` says what is expected: replace it with the content, written in the chosen language.

````markdown
## YYYY-MM-DD - <Decision title>

### Status: Draft | Accepted | Rejected | Deprecated | Supersedes <NNN>

### Decision makers:

- **<Role>**: <Name>

### Context

<In sentences: the problem to solve, the forces at play and the tensions between them, the constraints, the critical user journeys affected. Neutral tone, facts, not the solution.>

### Decision factors

- <Functional or non-functional requirement, with its threshold when there is one (availability, response time, testability…)>
- <Project criterion: deadline, cost, complexity, team skills>

### Solutions considered

1. **<Option>**
    - Pros: …
    - Cons: …
2. **<Option>** *(chosen)*
    - Pros: …
    - Cons: …

### Decision

<In the active voice, in complete sentences: "We…". The chosen option, why it wins, and the key choices that follow from it.>

### Consequences

<In sentences: what becomes easier, harder or stays the same; the trade-offs accepted; what must be done next. How the decision is checked: the architecture test, or the manual check.>
````

## Writing rules

### Form

- **One decision per ADR.** The same force can come back in several ADRs; the decision is what makes the unit.
- **One or two pages.** Beyond that, there are probably two decisions: suggest splitting it.
- **Concise.** No over-explaining. A technical concept (a "distributed monolith", say) is explained in one sentence in the context, not in a subsection.
- **Sentences for Context, Decision and Consequences**: a bullet list loses the reasoning. Lists stay for Decision factors and Solutions considered.

### Section by section

- **Title**: a short noun phrase that names the decision ("jMolecules annotations to mark the hexagon"), not the problem.
- **Status**: see "Lifecycle".
- **Decision makers**: names and roles come from the user. **Never invent them**; if they are missing, ask for them.
- **Context**: the forces at play (technical, organizational, specific to the project) and the **tensions** between them, stated explicitly; the constraints; the critical user journeys affected. Neutral, factual tone. No solution in this section.
- **Decision factors**: the functional and non-functional requirements that weigh on the choice, **with their threshold** when there is one, then the project criteria (deadline, cost, complexity, skills). A vague word ("scalable", "fast", "evolvable") becomes a question to the user, to get a threshold.
- **Solutions considered**: **at least two options**, often including "change nothing". For each one, pros and cons in short sentences. The chosen option carries *(chosen)*. The rejected options and why they were rejected are what keeps the debate from being reopened later.
- **Decision**: in the active voice, in complete sentences ("We mark ports and adapters with…"). The chosen option, **why** it wins against the criteria, and the key choices that follow from it.
- **Consequences**: all of them, **positive, negative and neutral**, with the trade-offs accepted. Every architecture choice gives something up, and an ADR that lists only gains hides what they cost. What is removed, simplified or made possible, but also what becomes harder or more expensive. What must be done next. An ADR's consequences often become the context of the next ones.

### Enforcing the decision

A decision written down is not yet a decision the code follows: left unchecked, it erodes one change at a time. The Consequences say **how the decision is checked**: preferably an architecture test that runs in continuous integration (a *fitness function*, for instance an ArchUnit test, named); otherwise the manual check (a review, a checklist step).

## Lifecycle

| Status | Meaning | What can change |
|---|---|---|
| `Draft` | Under discussion, not yet accepted (other templates call it *Proposed*) | All the content |
| `Accepted` | Explicit agreement of the user (or of the decision makers) | Only the status line |
| `Rejected` | Proposed, then refused: the file stays, since knowing an option was refused is useful | Nothing |
| `Deprecated` | No longer applies | Nothing |
| `Supersedes <NNN>` | Carried by the new ADR that replaces ADR `NNN` | As for an `Accepted` ADR |

- **`Draft` by default.** Move to `Accepted` only after the user's explicit agreement, never by inference.
- **An accepted ADR is neither rewritten nor deleted.** Knowing that a decision was made and then abandoned stays useful. Two ways out:
  - **Supersede**: the decision changes. A new ADR with the status `Supersedes <NNN>`, whose context says what changed since ADR `NNN`. The old one becomes `Deprecated, superseded by <MMM>`.
  - **Deprecate without replacing**: the decision no longer applies and nothing replaces it (a component removed, a constraint gone). The ADR becomes `Deprecated (YYYY-MM-DD): <reason in one sentence>`. No new ADR.
- In both cases, only the status line of the old ADR changes.
- **Correction in place, only with agreement.** When the decision holds but a fact, a consequence or a check in an accepted ADR turns out to be wrong, ask the user, every time, whether they prefer a new ADR that supersedes it or a correction in place, with a recommendation that weighs what the wrong text has already led people to decide (a released version, another ADR that relies on it). Agreement given for one ADR does not hold for another. A correction is made only with their explicit agreement for that ADR; the status line dates it and says what changed: `Accepted (corrected on YYYY-MM-DD: <what changed>)`. A decision that changes always goes through a new ADR.
- **Decisions that concern other teams**: if the team also keeps a wiki or a shared document, offer to copy the decision there. The ADR in the repository stays the reference.

## Workflow

1. **Conventions**: find the existing ADRs, the template, the language and the naming scheme (see "Project conventions").
2. **Frame**: does the decision deserve an ADR? Is it a single decision, or must it be split? Read the related ADRs: the one it would supersede or contradict, the ones it follows from.
3. **Gather the information**:
   - what is needed: the date, the decision makers, the context and the forces, the criteria with their thresholds, at least two options, the chosen option and its justification, the consequences, how the decision is checked; and if needed the folder and the language;
   - do not ask for what the code, the conversation or the existing ADRs already say;
   - **three to five questions per round**, the most structuring first, **open and neutral** ("What must be able to change without touching the rest?" rather than "Do you want a hexagonal architecture?");
   - **propose rather than ask** when an assumption is reasonable: "I'm assuming that… Does that work for you?"
4. **Write** the file as `Draft`, unless the user has already explicitly accepted the decision.
5. **Supersede or deprecate**: update the status line of the old ADR.
6. **Show** the result and offer adjustments. Point out the assumptions left unanswered and the fields still to fill in (decision makers, thresholds). Ask for explicit agreement before moving to `Accepted`.

If the execution mode does not allow asking the user questions, list the unresolved questions and assumptions in the answer and leave the ADR as `Draft`.
