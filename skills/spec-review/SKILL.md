---
name: spec-review
description: "Review of a spec before development, by three (the \"three amigos\": product owner, architect, tester): when it happens, what each one brings, the questions every reviewer asks; the architecture angle (implicit qualities made measurable, external systems and the relationship with their owner, what the existing platform already provides, bounded contexts, what must be true at once and what can be true a little later, technical uncertainty and the timeboxed investigation, which versions are delivered and the migrations they call for, splitting, walking skeleton); the testing angle (paths that fail, every path to a refused action, one proposal per real risk, the non-functional requirements touched, the main journey); non-functional requirements (measurable template, what a miss costs, typical and worst case, who proposes, sets, challenges, validates and verifies them, the shared file); what a reviewer returns, and on the product owner's side, each remark integrated or set aside with its reason. Load to review a spec from the architecture or the testing angle, to integrate the reviewers' remarks, or to propose, challenge, validate, verify or file a non-functional requirement."
---

# Reviewing a spec by three

Before development, the spec is reviewed by those who will build it and those who will verify it. Each one looks for what is missing from their own point of view; the product owner, sole author, decides what to take. The review goes after the questions that would cost a lot once the code is written: a forgotten failure path, a quality without a threshold, a boundary crossed without anyone noticing.

## When

- **Once the slice is chosen and its spec drafted, before the first line of code.** Not for the whole backlog in advance: the answers would be stale by the time the slice is built. Not after development: the review would then find defects instead of preventing them.
- **Reviewers read the "Why" and the rules before hunting for gaps.** A reviewer who does not understand a rule asks about it first: a rule nobody can explain is often the gap itself.
- **One rule at a time.** Move to the next rule when the proposals become obvious. A review that keeps finding new rules says the slice is too big: propose to split it again (skill `spec-writing`).

## Who does what

| Role | What they bring | Reference |
|---|---|---|
| Product owner | Sole author of the spec and of the non-functional requirements, which they set with the user. Judges the relevance and value of each proposed scenario: a tester can always find one more edge case, the product owner decides which ones deserve a scenario | "On the product owner's side" below |
| Architect | What the architecture needs to hold: implicit qualities, external systems, boundaries, consistency, technical uncertainty | `references/architecture-angle.md` |
| Tester (`quality-analyst`) | The paths that fail, the other paths to a refused action, the main journey; challenges, validates and verifies the non-functional requirements | `references/testing-angle.md` |

Non-functional requirements have their own reference: `references/non-functional-requirements.md`.

## The questions every reviewer asks

For each rule of the spec, from their own angle:

- What else does the one who develops need to know that the spec does not say?
- What am I assuming about how it will be built, or about the data it will meet?
- In which circumstances could it behave differently: another role, another state of the data, another moment, another entry point?
- What can go wrong?

An answer that the spec does not hold becomes a remark; an answer nobody knows becomes a question for the user.

## What a reviewer returns

- **They read the spec without changing it.**
- **Their remarks go to the product owner**, in a section addressed to them ("For the product-owner", in the agent's language), worded as needs or questions, never as a solution to write into the spec. Each remark names the rule or the scenario it concerns. Each proposed scenario comes with a concrete example, in business words and with real values.
- **What nobody knows** becomes a question for the user, with the options, an example for each and a recommendation.
- **What belongs to their own work** (the architect's instructions, the journeys the tester will play) does not go into the spec: they keep it for later.

## On the product owner's side

When a reviewer's remarks arrive:

- **Each remark or proposed scenario is integrated or set aside, with the reason.** A scenario kept joins its rule, with its example; a constraint joins "Known constraints"; an uncertainty joins "Open questions" or the split. A scenario set aside says why (out of scope, a later slice, not worth a scenario): the reviewer does not propose it again. What calls for a decision becomes a question for the user.
- **A reviewer's question gets an answer with its source**, in a section addressed to them ("For the software-architect", for instance, in the agent's language): the confirmed memory entry, the validated spec or the ticket the answer comes from. What the product owner does not know becomes a question for the user: they do not guess.
- **A proposed non-functional requirement** goes into their file, with the template of `references/non-functional-requirements.md`, once the user has accepted it; the spec points to it by its identifier.
- **No technical solution in the spec**: no table, endpoint, class or precise screen, unless it is a real constraint (an imposed external system, an existing contract).
