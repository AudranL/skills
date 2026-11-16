---
name: spec-writing
description: "Split a feature into deliverable slices and write the spec of one slice: feature map, what each slice must pass, vertical slices that end where the user is done, ways to split and splits to refuse, walking skeleton, spike, re-splitting when the scope changes; rules, examples and questions side by side, which examples and when to stop, an external system taken from its contract, what is not specified, bugs and spikes; Gherkin in business words (what Given, When and Then each hold, only the values that carry the rule, both sides of a threshold, fixed dates, one behavior per scenario, a refusal written by its effect, \"only\" also written in the negative, Background and Scenario Outline used sparingly, French keywords); spec template, its language and location, a spec that changes once ready. Load before proposing or revising a split, and before writing, completing or correcting the scenarios or the spec of a slice; read it also to propose a scenario in the style of a spec or to name the test of a scenario."
---

# Splitting a feature and specifying a slice

A spec gives the one who develops a slice the precise context they need, and nothing more. It is read by an agent with a limited context: short, without repetition or the history of the discussion, with scenarios that say everything the slice does. The spec records what the conversation settled, not the conversation itself: the questions asked and the user's answers stay, word for word, in the ticket's notes when the project keeps a backlog.

## The flow

1. **Split** before specifying, when the feature will take several slices or the scope grows: `references/splitting.md`. The user validates the split; only the next slice gets specified.
2. **Rules, examples, questions** for the chosen slice (below).
3. **The Gherkin scenarios**: `references/gherkin.md`.
4. **The spec**, its template, language and location: `references/spec-template.md`. It points to the non-functional requirements it touches by their identifier (skill `spec-review`).

## Rules, examples, questions

For the chosen slice, write the story down and, under it, three lists:

- the **business rules**: sentences that hold whatever the example ("delivery is free from €50");
- for each rule, **concrete examples** with real values, each named by a short phrase that says what sets it apart ("a basket at exactly €50"): that name becomes the scenario's title;
- the **questions** nobody can answer right now, each with who can answer it and the assumption made meanwhile.

**Ask for examples as questions, with a proposal.** "A €52 basket with a €5 voucher: is the threshold checked before or after the voucher? I would say after: the customer pays €47 and the delivery is charged." The user corrects a concrete case more easily than an abstract rule, and the answer is already an example.

**Which examples.** For each rule: the nominal case, each side of a threshold (€49.99 and €50.00, never only €30 and €80), and a refusal or a counterexample. An example earns its place by showing something the others do not: a value that changes the outcome, a case the user hesitated on. When the next candidate would only change the numbers of a case already written, stop: trying every combination is the job of the developer's unit tests, not of the spec. The examples go where someone is unsure: a rule nobody has built before gets several, a sign-in like every other gets its nominal case and its refusals.

**What the three lists say about the slice:**

- more than four or five rules: the slice does too much, propose to cut it;
- more questions than answers: specifying now would mean guessing; get the answers first, or propose a spike when the question is technical;
- a rule nobody manages to illustrate is still vague: ask for a case before writing it; an example no rule explains points to a rule nobody has stated yet, or to another slice;
- a rule whose examples contradict each other hides two rules, or a missing notion: name it in the Vocabulary once the user has validated it on an example.

**An external system: start from its contract.** The cases of an external system (answers, errors) are specified from its documented contract; ask the user for it if it is not in the repository. A code or a case the contract does not document gets no dedicated scenario: ask which default handling to apply rather than inventing one. The scenario says what the answer means for the business ("the carrier refuses the address"), not its code (`422`): the contract holds the mapping, and the spec points to it from "Known constraints".

**What is not specified is another feature.** The slice does what its scenarios say, nothing more. When an example brings up a case nobody asked for (a change along the way, a variant, a "what if…"), ask the user, with a recommendation, without writing a scenario "just in case". If they prioritize it now, the case joins the slice with its scenarios. Otherwise the spec files it under "Later" or "Out of scope", nothing is built for it, and the question and the answer go into the notes of the ticket concerned (a new ticket to frame if there is none). What leaves the slice this way is a new behavior, never the boundary or the refusal of one of the slice's rules. A case the user says never happens, and that nothing observed contradicts, gets no scenario either: "Out of scope" says it does not happen and the slice does not handle it. A good idea that comes up during development is offered to the user for a later slice, never added on the side.

## Bugs, spikes, technical work

- **A bug** is a scenario the product breaks. Its spec names the broken rule and gives the scenario that reproduces the report, with its real values, whose "Then" says the expected behavior; when the bug sits on a threshold, the case on the other side joins it. If no rule or scenario ever stated the expected behavior, it is not a bug but a new behavior: ask the user, as for any case nobody asked for.
- **A spike** answers a question that blocks a slice (a technology nobody on the team knows, a performance nobody has measured). It has no scenario: its spec gives the question, a timebox, the expected output and the slice it unblocks. It goes in a slice of its own, ahead of the one it unblocks: the user decides whether the answer is worth its timebox, and nobody mistakes the end of the spike for the feature. What it produces is knowledge: its code is thrown away, or rewritten under test in the slice that follows.
- **Technical work** (a migration, an upgrade) is written with the value it serves ("orders keep loading in under a second once the catalog doubles"), or joins the business slice that needs it. If nobody outside the team can say what it changes for them, the spec has no "Why" the user can check.

The template of each is in `references/spec-template.md`.

## A spec that changes once ready

- **The spec changes before the code.** A change asked for during development goes into the spec first, validated by the user; the developer works from the spec, not from the message that announced the change.
- **The spec stays without history**: what changed (scenarios added, modified or removed, by title) goes into the ticket's notes and into the message to the developer, whose acceptance tests change first (skill `acceptance-tests`).
- **A change that adds a behavior** to a slice in progress follows the rule above: it is a question to the user, and usually a next slice.

## Before handing over the spec

- the user has validated the split and the chosen slice;
- the slice passes each question of `references/splitting.md` (shown once done, deliverable on its own, a need rather than a solution, sized, small, each rule shown by an example);
- each rule has at least one nominal scenario and one boundary or failure case;
- each scenario has the Givens its outcome depends on and no others, a single "When", an observable "Then", and a title no other scenario shares;
- the terms are the business's, defined in "Vocabulary" when ambiguous, with the word used in the code when it differs; a distinction between two neighboring terms has been validated by the user on an example;
- the open questions are listed, each with the assumption made meanwhile;
- an empty section is removed, not filled with "N/A";
- the `gherkin` block can be copied as is into a `.feature` file.
