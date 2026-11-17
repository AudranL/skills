---
name: architecture-review
description: "Architecture review of a diff, a branch or a delivered slice: what to read first (ADRs, style, the slice's instructions, the architecture tests run); direction of dependencies, a domain free of any framework, an external system's model kept in its adapter, simple data crossing the boundaries, business rules in the domain, ports that are conversations, one aggregate changed per transaction, dependencies between contexts, implementations not public, a new module declared to the architecture tests, a mechanism the platform already provides not doubled; architecture tests not weakened and frozen violations that did not grow, a decision taken in the code without its ADR, a new build dependency justified by an ADR; ranking the remarks (blocking, important, suggestion) and their form, a recurring remark turned into a test; debt outside the scope; debt proposed to the product owner as a slice, by what it costs and what it brings. Load for any architecture review of a code change, or to turn an architecture debt into a slice."
---

# Architecture review

Review a diff or a branch from the architecture angle, without changing the code: the one who developed it fixes it. Review early and in small pieces: a boundary crossed in the first commit costs one line to undo; crossed for a week, it has been copied elsewhere.

## Before reading the diff

- **The rules in force**: the ADRs, the style the project chose and its confirmed rules (in the architect's memory, if there is one).
- **What was asked**: the spec of the slice and the architecture instructions given for it. A gap from the instructions is a remark; a choice the instructions left open is not.
- **Run the architecture tests** (skill `architecture-tests`): what they check needs no reading; the review looks at what they cannot see.

## What to check

- **The direction of the dependencies**, and that the domain stays free of any framework, persistence annotation or external API object.
- **The model of an external system stays in its adapter**, with an explicit translation into the domain's model.
- **What crosses a boundary is a simple data structure** shaped for the inside: no entity handed to an adapter to serialize as it is, no database row, framework object or external API object handed to the domain.
- **Each business rule lives in the domain**, not in a controller, an adapter, a SQL query or a screen.
- **The ports are conversations** in the domain's vocabulary, not a table or a class each.
- **One aggregate changed per transaction**: a use case that changes two at once either reveals a missing concept, or asks the business whether a short delay is acceptable (an event between the two). Ask rather than accept it.
- **No dependency between contexts outside the planned path** (adapters, a declared contract).
- **Implementations are not public** when the language allows it: an adapter or a repository implementation that another package could call directly opens a path the architecture tests then have to close.
- **A new module or top-level folder** is declared to the architecture tests (its zone, its annotation), otherwise it escapes every rule.
- **A cross-cutting mechanism the platform already provides** (timeout, retry, authentication, error translation) is not written a second time in the code.
- **The architecture tests are green, no rule was weakened** (a pattern widened, an exception added without its ADR, a rule disabled), and the file of frozen violations did not grow.
- **A decision taken in the code without its ADR**: a new library, a new way for two contexts to talk, a new kind of storage. The ADR is written (skill `adr-writer`) before the slice is merged, or the decision is undone.
- **A new build dependency** is justified by an ADR.

## The remarks

Rank each remark:

- **blocking**: a confirmed rule broken, an architecture test weakened;
- **important**: a dependency in the wrong direction not yet covered by a test, an external model leaking, a decision without its ADR;
- **suggestion**: the rest.

For each one: the place (`file:line`), the rule (its identifier, the ADR or the principle), a concrete proposal. Also point out what is well done.

**A remark that comes back** from one review to the next (the same kind of dependency, the same leak) becomes an architecture test: write the rule rather than repeat the remark.

A debt found outside the slice's scope is recorded as debt, without blocking the slice.

## From debt to a slice

Debt is paid with interest: every slice that goes through the tangled code takes longer, breaks more often, or cannot be tested. Some debt is taken knowingly to deliver sooner; it is fine as long as it is repaid quickly: record it with the slice that will repay it.

When a debt costs (recurring bugs, slowed slices, tests impossible to write), propose to the product owner a slice worded by what it brings ("deliver the catalog's changes without touching billing"), not by its technique ("refactor module X"), with what the debt costs today, in the business's terms (days per slice, incidents). The product owner decides its place.
