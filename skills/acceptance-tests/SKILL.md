---
name: acceptance-tests
description: "Acceptance tests drawn from the Gherkin scenarios of a spec (the outer loop of ATDD), and the acceptance review of a delivered slice: one test per scenario, under its title, that exercises its \"When\", checks every part of its \"Then\" and is seen red for the right reason; at the application's entry point just below the interface (primary port, use case input boundary or business service, depending on the architecture: hexagonal, clean, onion, n-tier), with in-memory doubles in place of what the application drives outside itself; thin steps over an automation layer in the domain vocabulary; executable Gherkin as a build dependency; a scenario that changes; the report's scenario-to-test table; production code written before its test; covered, poorly covered, not covered, and whether the slice is accepted. Load before writing the first acceptance test of a spec, before resuming work on production code written before its test, or to review a delivered slice and say whether each scenario is covered."
---

# Acceptance tests

Each scenario of the spec has its acceptance test, written before the production code it drives: as long as it fails, the slice does not do what the scenario says; once it passes, the scenario is delivered. The same criteria serve the one who writes it and the one who reviews the delivered slice: `references/acceptance-review.md`.

## One test per scenario

- **It carries the scenario's title** and follows its Given / When / Then: searching for the title finds its test. A scenario outline gives one test per row of examples, under the outline's title.
- **It exercises its "When"**: the test performs the scenario's action, not only the state that precedes it.
- **It checks every part of its "Then"**, including the value that sets this scenario apart from the others (a deadline, two equal amounts).
- **An "And … is not shown" is checked against the complete list** of what is shown ("Then the basket shows the pen and the notebook And the eraser, out of stock, is not shown": the list is exactly the pen and the notebook), never with a "does not contain" nor on a filtered list, which would let an extra item through. This "And" replaces an "only", which cannot be checked as written.
- **It is seen red for the right reason** before the code that makes it pass, and its failure message says what is missing. Only a scenario that the existing code already satisfies (existing behavior, a scenario added afterwards) gives a test that is green as soon as it is written: see it fail by breaking the code on purpose (a manual mutation, undone at once by copying back the original file: `git checkout` would erase its uncommitted changes), and say so in the report.
- **A step not written yet fails**, or is reported as pending: never an empty step, which passes and makes the scenario pass with it.
- **A scenario that changes in the spec changes its test first**: the test is updated and seen red, then the code follows. Once green, an acceptance test guards against regressions: a later red is a regression to understand (skill `unit-tests`, "A red test"), not a test to adjust.

## Its level

**A scenario states a business behavior that holds whatever the adapters**: the same whether the request comes through an HTTP controller, a screen or a batch, and whether the data ends up in a database, a file or memory. Its acceptance test checks that behavior and nothing else. So **it enters the application just below the delivery mechanism** (a controller, a screen, a command line), where a request becomes a use case, and **replaces with doubles what the application drives outside itself** (database, external services, messaging): in-memory implementations that keep their state and let the test check what was recorded or sent. No framework, no database, no network: the test also runs as fast as a unit test. Where that is depends on the project's architecture (its ADRs and its packages say which; the `architecture-styles` skill describes each style):

| Architecture | The test calls | Replaced by in-memory doubles |
|---|---|---|
| Hexagonal (ports and adapters) | the primary port, in place of the primary adapter | the secondary adapters, through the secondary ports they implement |
| Clean architecture, onion | the use case's input boundary (the interactor; in onion, the application service) | the gateways declared in the inner circles (repositories, external services); in clean architecture, also the output boundary when the use case answers through a presenter: the double captures the response model |
| N-tier | the business layer's service, as the presentation layer calls it | the data access layer and the clients of external services, through interfaces of the project's own (a DAO interface); otherwise, see the next point |

- **In n-tier, the business layer often calls an interface that extends a framework's** (a Spring Data repository) **or a concrete class**, neither of which is doubled (skill `unit-tests`, "Only double types you own"). Two ways out, to choose with the user since both change the project: an interface owned by the business layer at that boundary, implemented by the data access layer and doubled in memory (the dependency is inverted, a step toward hexagonal); or the real data access layer on the real database engine (in a container), a slower test kept apart from the others.
- **What the real implementation does** (the translation to the database, the HTTP call, the rendering) is not the scenario's concern: its own tests cover it, and the same contract tests run against the real implementation and its double, so the double stays faithful (skill `unit-tests`, "Test doubles").
- **A rule that can only be reached through the delivery mechanism** is in the wrong place: move it to where the test enters rather than raising the test (skill `unit-tests`, "A rule lives outside the framework").
- **End-to-end keeps only what needs the real application**: journeys, persistence, presentation, wiring (skill `e2e-tests`). A scenario does not have to be replayed end to end.

## Its shape

- **Steps stay thin**: they translate the scenario's text and call an automation layer written in the domain vocabulary (`anInMemoryShop().placeOrder({ … })`), which calls the entry point and wires the in-memory doubles behind it. A wording that changes is fixed in one place only.
- **The test speaks the domain's terms only**, never the technology's (database, HTTP, screen): swapping an adapter leaves it untouched.
- **Running the Gherkin text itself** (Cucumber, SpecFlow, jest-cucumber…) is a build dependency: ask for it. Without it, the scenario and its test are linked by the title.
- **BDD happens earlier**, when the spec is written: do not rewrite a scenario; report one that cannot be automated as written.
- **What depends on the tool** (Cucumber, JUnit, Jest, Vitest: location, naming, scenario outline): the `test-conventions` skill if it is installed, otherwise the repository's existing tests.

## The report

The developer's report gives a table with one row per scenario of the spec: its title, its test (file and name), its level (domain entry point or end to end), and how it was seen red (before the code, against the last commit, or by a manual mutation). A scenario without a test has its row too, with the reason. The acceptance review checks this table rather than believing it.

## Production code written before its test

When resuming work finds production code that precedes its acceptance test (uncommitted code, or code written before its test): write the test, then run it against the production code of the last commit (`git stash push -- <production files>`, then `git stash pop`). It must be red there for the right reason. Only a test still green in that state goes through a manual mutation. Say so in the report.
