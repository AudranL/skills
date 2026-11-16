# Entry formats

Each kind of entry has its own fields. The agent says, in its file table, which kind each file holds, and writes the field labels in its language. Every kind keeps the rules of the skill: a title that states the fact (or, for a kind looked up by a key, that key), one fact per entry, a source that says what makes it true today, and an entry rewritten rather than appended to.

The examples come from the same imaginary online shop.

## Rule or fact (the default)

```markdown
### R-007 · An order can be cancelled until the carrier picks it up
- Status: confirmed · Source: notes of ABC-142 (YYYY-MM-DD)
- Why: once picked up, the parcel can only come back as a return, which the customer pays for.
- An order prepared but still in the warehouse can be cancelled; an order scanned by the carrier cannot.
- Rejected: cancelling until delivery, because the carrier charges for each interception.
- Verified by: `CancelOrderTest`
- See also: Q-004
```

"Rejected" lists the options already refused, so that nobody proposes them again; "Verified by", the test that checks the rule, when there is one.

## Procedure

How to do something: build, run the tests, launch the application. A procedure is looked up by its goal, so its title states the goal ("Run…", "Build…"), not a fact. It is written as instructions, with as many exact commands as needed, not as the story of the error that taught them, and it is verified by running it.

```markdown
### O-004 · Run the end-to-end tests on the built application
- Status: verified (YYYY-MM-DD, 2.3.0 at commit abc1234: 45 journeys green in 50 s) · Source: `playwright.config.ts`
- Build: `npm run build`, then run: `npx playwright test`
- A single journey: `npx playwright test -g "<scenario title>"`
- Pitfall: a failed build leaves the previous one in place, and the journeys then run the old version. Check that the build exits with 0.
```

Add a prerequisite (a service to start, a variable to set) when there is one, and when to use it if not always. A constraint on a tool ("Stay on Vitest 4.0 while npm is at version 10") is not a procedure but a rule: default format.

## Question

No status: a question is open, or it is gone. Its title is the question, as the user would read it.

```markdown
### Q-004 · Is a cancelled order refunded on the card used, or as a store credit?
- Opened on YYYY-MM-DD · Who can answer: the product owner · For: ABC-150 "Cancel a paid order"
- Context: the payment provider refunds a card within 10 days; a store credit is immediate but keeps the money in the shop.
- Options: (a) on the card, always (recommended: it is what the customer expects); (b) the customer chooses; (c) store credit only.
- Retained hypothesis: refund on the card used.
```

When no task is waiting for the answer, a "Trigger" line replaces "For": the event that makes the question urgent.

The retained hypothesis is the only place where a hypothesis lives: an entry that relies on it points to the question. Once answered, the question leaves the file, and its answer joins the entry it settles.

## Decision

A decision says why, and what was rejected. It quotes what justified it (the user's words, the passage of a spec or an ADR as it stood that day): when they change, the decision can still be understood. The rule it produces lives in its own entry; the decision does not restate it.

```markdown
### D-012 · Delivery fees are refunded only when the whole order is cancelled
- Date: YYYY-MM-DD · Source: answer of the product owner in ABC-150
- Retained: the fees are refunded with the last item cancelled; the rule: R-009.
- Why: "the parcel still leaves with the other items, and the carrier bills us the same".
- Rejected: a refund in proportion to the items cancelled, since the fees do not depend on the number of items.
- Replaces: "Delivery fees are never refunded".
```

A decision taken by the user carries no status. A decision taken by an agent (accepted at a review, for instance) waits as deduced until the user validates it. A decision replaced by another one leaves the file.

## Debt

```markdown
### DT-005 · The payment adapter passes the provider's error codes on to the domain
- Spotted on YYYY-MM-DD · Rule: A-003 (an external system's model stays in its adapter) · Location: `src/payment/PaymentProviderAdapter.ts`
- Observation: `refund()` throws `ProviderError` with the provider's code (`card_declined`, `expired_card`), and `CancelOrder` tests these codes.
- Impact: changing provider means rewriting the use case and its tests; a code the provider adds ends up as an unknown error shown to the customer.
- Treatment: translate the codes into a domain `RefundRefused` inside the adapter; proposed as a slice before the change of provider.
```

No status. Once paid off, the debt leaves the file, with the date in the commit.

## User instruction

A working agreement with the user: what is allowed, how to present things, who decides what. One agreement per entry, stated by its title.

```markdown
### CO-004 · Push and merge to `main` only with the user's agreement
- Status: confirmed · Date: YYYY-MM-DD · Source: answer at the start of ABC-142
- Commits are allowed on the slice branch; pushing it and merging it wait for the user: "commit as you go, but ask me before pushing".
```

When the user refines it, the entry is rewritten to state the agreement as it now stands, not the series of answers that led to it. The detail of a task (the answers given while it was running) stays in that task's notes.

## Snapshot

The state of a zone at a date: what is covered by tests, what was measured. Its title is the zone and the date.

```markdown
### `src/billing/` (YYYY-MM-DD)
- Covered: invoice totals and VAT (unit tests), the invoice repository (integration tests on a test database).
- Not covered: `InvoicePdf.ts`; `CreditNote.ts`, only through an end-to-end journey.
- Seams: a `Clock` injected into `InvoiceService`; none in `InvoicePdf`, which reads the date directly.
- Flaky: `InvoiceRepositoryIT.findsLatest` (order not fixed, fails about once in 20 runs).
```

The file header gives the command that tells whether the zone has changed since: `git log --since=<date> --oneline -- <path>`. Observed again, the snapshot is rewritten whole, with the new date.

## Recurring check

A check run again at each delivery (a non-functional requirement, a package control): how to run it, and only the latest result. Its title is the requirement's ID and a short name, without copying its text.

```markdown
### NFR-04 · payment page response time
- Status: verified · How: `k6 run perf/payment.js` (50 virtual users, 5 min), reference dataset, staging server, 3 runs
- Last: met (p95 at 640 ms), 2.3.0 at commit abc1234, YYYY-MM-DD; not verified: on a mobile network, which the setup does not emulate.
```

## State file

Where the work stands, for an agent that resumes in a fresh session. No entries: the file is rewritten whole and dated at each update. It holds only what is open: the step in progress, the next action, the questions and proposals waiting for an answer, what is not committed. What is done leaves it.

```markdown
# Resume — YYYY-MM-DD

## In progress
- ABC-150 "Cancel a paid order": spec validated; the software engineer implements it on `feat/abc-150-cancel-paid-order`.

## Next action
1. Acceptance of ABC-150, once the software engineer reports green.

## Waiting for the user
- The product owner's question: is a cancelled order refunded on the card used, or as a store credit?

## Not committed
- `docs/specs/cancel-paid-order.md`
```

The state file cites no ID from another agent's memory: it says the question itself.
