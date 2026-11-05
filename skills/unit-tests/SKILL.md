---
name: unit-tests
description: "Write, review and improve unit tests, whatever the language and the tool: what makes a good test (F.I.R.S.T., one concept per test, a behavior rather than a method, a precise assertion, no logic in a test, a clear failure message, expected text matched exactly), where to test a rule (triangulated where it lives, outside the framework, a single passing case in the class that uses it, no test that passes as soon as it is written), anti-patterns to refuse, test doubles (dummy, stub, spy, mock, fake and which one to pick; real objects by default, allow queries and expect commands, only double types you own, a fake kept honest by a contract test), a red or flaky test (never deleted, disabled or weakened), coverage and mutation testing. Load at the start of any task that writes, modifies or reviews unit tests, before listing them. What depends on the tool (JUnit, Mockito, Jest, Vitest…) is in the test-conventions skill."
---

# Unit tests

A unit test written before the code guides it, then protects it: it must be able to fail, and say why when it does. These rules depend neither on the language nor on the test tool. The TDD cycle is described by the agent that applies it (or the `tdd` skill); acceptance tests have their own skill (`acceptance-tests`); the shape these rules take with each tool is in the `test-conventions` skill.

## What makes a good test

- **F.I.R.S.T.**: fast, independent (any order, no shared state: each test builds its own), repeatable (no network, no real clock, no unseeded randomness, no dependence on the machine's time zone or locale, no sleep: an asynchronous effect is awaited, never a duration), self-validating (green or red, nothing to read by hand), timely (written just before the code).
- **One concept per test.** Several assertions are fine if they check the same concept.
- **Test a behavior, not a method.** The test name says what the system does in a given situation, not which method it calls nor which ticket asked for it. Writing the test backwards helps: the name, then the call, then the assertion, the setup last.
- **Readable as a specification.** A visible Given / When / Then (or Arrange / Act / Assert) structure, meaningful test data, nothing useless in the test. A value that matters has a name saying what it stands for (`NO_CUSTOMER_FOUND` rather than `null`): the test speaks about the information, not about its representation.
- **No logic in a test**: no `if`, no loop, no computation. Nothing tests the test, so its logic can be wrong unnoticed, and the reader no longer sees which path is checked: Tests must be simple enough to not need tests. Building data goes into a Test Data Builder; several examples of a rule go into a parameterized test.
- **A precise assertion**: the expected value itself. Checking that an area is not zero accepts every wrong area but one; "not null", "true" or "did not throw" say just as little. And nothing more than what the test varies: no value that does not depend on its inputs, no behavior already checked by another test.
- **A failure path is tested like any other**: the expected domain error, and its message when it matters. A `try` / `catch` in a test never hides an exception, and no assertion sits behind an `if` that may skip it: when the test cannot check what it claims, it must go red, or be marked as skipped with its reason in the report.
- **Test code is held to the same standard as production code.** Dirty tests end up abandoned, and the code rots with them.
- **A clear failure message.** Read the failure before making the test pass; use assertions that explain the gap, and name the checked value when the failure does not.
- **An expected text that another text can extend is matched exactly** ("closes at 4" is also found in "closes at 4:30", and the test can no longer fail): forms per tool in the `test-conventions` skill.

## Where to test a rule

- **A rule is triangulated where it lives**, and only there. Example: the mapping between carrier codes and delivery steps is triangulated in the test of `CarrierParcelStatus`, not in the test of the provider that uses it.
- **A rule lives outside the framework, and is tested without starting it.** Spring context, Angular or React component, Electron process: the framework presents and passes things on; the rule sits in a domain object, a use case or a pure function, tested directly. What remains in the framework is reduced to almost nothing and is checked by an integration or end-to-end test, kept apart from the unit tests.
- **The shape of the examples is a readability choice**, not a rule: as many tests as cases, or one parameterized test (`@ParameterizedTest`, `it.each`). Both are fine.
- **A class that uses an already tested rule** has a single passing case for that rule, plus the cases of its own (errors, absence, edge cases of its own responsibility). Do not replay every example of the rule at each layer: if the rule changes, a single test should break.
- **A class that only passes things on** (a service delegating to a port, for instance) still has its unit test: it covers the hand-off, and only that. In TDD, this test justifies the class's existence; an acceptance test does not replace it.
- **No test that passes as soon as it is written.** A test that was never red guided no line of code (e.g. a second case for a class that only passes things on). Do not add it; if it seems useful as documentation, tell the user instead of adding it silently. Exception: the acceptance test of a scenario from the spec that the code already satisfies is still written (skill `acceptance-tests`). See it fail by breaking the code on purpose (a manual mutation, undone at once by copying back the original file: `git checkout` would erase its uncommitted changes), then say so in the report: a test never seen red may check nothing.

## Anti-patterns to refuse

- **Test coupled to the implementation**: it doubles internal collaborators, tests a private method, or checks through a side channel (a database query instead of going through the interface). Symptom: it breaks during a refactoring although the behavior did not change.
- **Tautological test**: the expected value is recomputed the way the code computes it (`expect(add(a, b)).toBe(a + b)`), so it can never fail. The expected value comes from an independent source: a known literal, an example worked out by hand, the specification; never the code's output copied to turn the test green.
- **Test that checks its own doubles**: it replaces the very class it tests with a double, or checks what it has just programmed (a stub returning 42 and an assertion expecting 42, with the tested code playing no part). A test that consists mainly of programming doubles proves only how they were programmed: move the unit's boundary out until it includes real behavior, or check that seam with an integration test instead.
- **Horizontal slices**: writing all the tests, then all the code. The test list is *noted* in advance, but *implemented* one test at a time.

## Test doubles

A double stands in for a collaborator of the object under test. The vocabulary below is the usual one, but books and tools do not all use it the same way: Mockito's `mock()` and Vitest's `vi.fn()`, for instance, both stub and spy. So name a double for the role it plays in the test, never for the tool that built it. `references/test-doubles.md` gives an example of each kind, the contract test of a fake, and the vocabulary of each book.

| Double | What it does | What for |
|---|---|---|
| **Dummy** | Fills a parameter, is never used | A mandatory argument unrelated to the tested behavior. If it is called, it fails stating its role |
| **Stub** | Returns prepared answers: it controls what the object under test receives | Give the object under test the result of a query (the catalog gives a price), or a failure by throwing |
| **Spy** | A stub that also records the calls it receives, which the test checks after the action | Check a command sent outside, keeping the Given / When / Then order |
| **Mock** | Carries expectations set before the action, and fails if it does not receive the expected calls | Describe the protocol between an object and its neighbors, outside-in |
| **Fake** | A lighter implementation of the same behavior, which the test installs but does not program: in-memory repository, settable clock | A stateful port used by many tests, written once and reused |

Choose, in this order:

1. **A real object by default.** Value objects and pure business code are never doubled: instantiate them. An object too tedious to build calls for a **Test Data Builder**, not a double.
2. **A double only at a boundary**: database, HTTP, messaging, file system, clock, randomness, or a neighbor that does not exist yet. Double an object's peers (its dependencies, those it notifies), never its internals.
3. **A query: a stub or a fake. A command: a spy or a mock.** Allow queries, expect commands: a query changes nothing in the world, so the test checks neither that it is made nor how often; a command changes the world, and it is what the test checks. Exception: the test of a cache checks how many times the query goes out, since its state cannot tell a hit from a miss.
4. **A stateful port used by several tests: a fake** (`InMemoryOrders`), rather than a stub reprogrammed in each test. The test then checks the state the fake keeps, not the calls it received.
5. **A parameter unrelated to the test: a dummy**, or a named constant.

And always:

- **Only double types you own.** For a third-party library, write an adapter (an interface of your own, in the domain vocabulary) and double that adapter; the real adapter is covered by an integration test.
- **A fake stays honest**: the same contract test suite runs against the fake and against the real adapter, only the setup changes. A double that no longer follows the real contract keeps the suite green while the integration is broken.
- **Specify what matters, nothing more**: no call order unless it is part of the behavior, no "no other call" by default, arguments checked on what the test varies.
- **A mock can design a collaborator that does not exist yet.** Working outside-in, write in the test the call you wish you had (`mailer.sendConfirmation(order)`): the test then states what the object under test needs from its neighbor (its role, its method, its parameters) before any real implementation exists. Build the real collaborator afterwards, with its own tests.
- **No magic**: no double of a concrete class, a static method, a constructor or a whole module, no bytecode manipulation. The need signals a hidden dependency: inject it (a clock, an interface). Only legacy code, while it is being secured, justifies these techniques (skill `legacy-code`).
- **Listen to the tests.** A test that is hard to write (huge setup, doubles returning doubles, a method made public for the test, bytecode manipulation tools) signals a design problem: fix the design rather than complicate the test.
- **A double is named after its role** (`catalogWithPen`, `refusingPaymentGateway`, `clockOnNovember2nd`), not `mock1`: the failure report then says which neighbor did not get what it expected.

## A red test

A test that goes red when nobody expected it is information: either the code is wrong or incomplete, or the test rests on a misunderstanding. Find out which before touching anything.

- **Making a test say less is not a fix.** Removing or loosening an assertion, skipping the test, widening a tolerance, swallowing an exception, pasting the current output in as the expected value, or building with the tests switched off: each one hides the signal instead of answering it. Only a characterization test, whose job is to record what legacy code does today, takes its expected values from the output (skill `legacy-code`).
- **If the code is wrong, fix the code**; if the fix changes a behavior someone relies on, the user decides first. **If the test is wrong** (its expectation predates a change the user asked for, for instance), show why, and change or delete it only with the user's agreement.
- **Shorten the loop**: rerun the failing test alone while fixing, then widen to its class, then to the whole suite (commands per tool in the `test-conventions` skill).
- **A test that fails only sometimes still fails.** It may be the only witness of a real defect, and a green rerun does not prove it away. Find what changes between runs (the clock, the order of the tests, state left by another test, an asynchronous effect awaited with a delay) and remove it; rerunning until green, or waiting longer, only makes the defect rarer.

## Improving a suite

- **Coverage shows what no test runs** (use it to find untested code). As a target it backfires: tests written to reach a coverage figure, without knowing what the code should do, break at every change. No test without an assertion to raise the figure; no threshold the project has not chosen.
- **Mutation testing checks that the tests can fail**: each mutant is a small change to the code, and one that survives shows a behavior no test checks. Tools per language in the `test-conventions` skill; it is slow, so run it on the changed classes, when the project already runs it, or on request.
- **A redundant test is deleted** only if it brings the reader neither confidence nor information: two tests that go through the same path but tell two different scenarios both stay.

## Per tool

The shape of these rules with each tool (naming, layout, assertions, doubles, time, asynchrony, commands, examples) is in the `test-conventions` skill, one reference per tool. The convention already in place in the repository wins.
