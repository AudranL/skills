---
name: legacy-code
description: "Change legacy code, any stack: code without tests, often also carrying smells, complexity, vulnerabilities, architecture anti-patterns. The algorithm (change points, where to test, dependencies injected, characterization tests, then the change in TDD); seams production uses too, no code for the tests alone but logs, module substitution last; first edits without a safety net (IDE refactorings, one intent per edit); techniques by obstacle (unbuildable parameter, collaborator created inside, singleton or static call, invisible effect, private method, third-party API); characterization tests freezing today's behavior, bugs included, proved by a deliberate mistake; suspicious behavior and other problems reported, fixed later under tests; methods too long to test; new code beside or around the old when time runs short. Load before modifying, fixing, extending or cleaning up code without tests, before calling an untested method from new code, or when a test cannot be written without extracting a dependency."
---

# Legacy code

Here, legacy code means code that no automated test protects. It usually carries more than that: code smells, complexity that makes it hard to follow, security vulnerabilities, architecture anti-patterns, dependencies no longer maintained. The missing tests come first, because fixing any of the others means changing the code, and without tests nothing shows whether that change broke something. The catch: the tests that would make a change safe often cannot be written until the code itself has changed a little. So the work goes in small, safe steps: the smallest edit that lets a test run the code, tests that pin down what it does today, then the change, under those tests. Changing first and checking by hand afterwards is never the plan, however careful the change.

## When to use it

| Situation | What applies |
|---|---|
| Fix, extend or refactor code that has no tests | "The algorithm", in order |
| You cannot tell where the change goes | "Understand before changing", then the algorithm |
| The class cannot be built in a test, or the method cannot run there | Step 3 and `references/extract-and-inject.md` |
| A method so long that no test reaches the part to change | `references/long-methods.md` |
| A feature needed now, with no time to put the old code under test first | "When time runs short" |
| New code about to call an untested method | Characterize that method first (step 4): its tests tell the caller what it can count on |
| A smell, a vulnerability or an architecture anti-pattern found along the way | "The other problems it carries" |

## The algorithm

### 1. List the change points

Every place the change will touch. List them all before deciding where to test; when there are many, spread over several classes, work on one or two at a time.

### 2. Choose where to test

The test must be able to see the effect of the change. Follow that effect from each change point:

- **a returned value** travels to the callers that use it;
- **an object passed as an argument and modified** travels to whoever reads it afterwards;
- **a field, a static or a global that is written** travels to every method that reads it, overrides and subclasses included.

Some things end the trail: nothing outside can observe a private field, a local variable or an immutable value. A field open to the package or to subclasses, a mutable collection returned by a getter, a global: keep following.

Then pick the place:

- **The closest place to the change** where a test runs fast and a failure points straight at its cause. A test that needs a database, the network, files or a special configuration is slower and less precise: acceptable as a first net, kept apart from the fast tests.
- **When the change touches several places, a point all their effects go through**: one method whose result depends on all of them (an order's total, in which a change to the price, the discount or the tax all show), so that a few tests there cover the whole change. Check it: for each change point, imagine a mistake there and make sure a test at that point would fail. If no such point exists, shrink the change, or test each change point on its own.
- **A test far above the classes** (through a use case, an entry point, the real database) is a starting point, not the goal: as seams appear, its cases move down to the classes they concern.

### 3. Extract and inject the dependencies

A dependency gets in the way for one of three reasons:

- **the test cannot run the code**: the class cannot be built (its constructor opens a connection, reads a singleton that reaches a database, demands a parameter nobody can build), or the method cannot run outside production;
- **the test cannot see the result**: the code computes something and sends it where no assertion reaches (a screen, a message, a global);
- **the result is not deterministic**: it depends on the time, randomness, a generated identifier, the state of a database or of a remote service, so the same test passes one day and fails the next.

The usual answer: extract the dependency the code reaches for by itself (`LocalDateTime.now()`, `new HolidayCalendar()`, `Settings.getInstance()`) and inject it, so that production passes the real one and the test a double, or a real object set to a known state (`Clock.fixed(…)`): the code becomes deterministic under test. The place where the code then calls the injected dependency is a **seam**: a place where a test can put a double (dummy, stub, spy, fake or mock, as the `unit-tests` skill defines them) in place of a real collaborator without editing the code that uses it. The code keeps calling `calendar.isHoliday(day)`; which calendar answers is decided where the object is built. Without a seam, no double is possible: a constructor that runs `new HolidayCalendar()` leaves the test no choice.

**No production code exists only for the tests**, unless there is truly no other way. A seam is a design that production uses too: the constructor receives its collaborator, production passes the real one (from where it builds its objects, or through its injection framework), the test passes a double. So no second constructor or overload that only tests call, no default value that only tests replace, no setter or reset method, no visibility widened, no method opened to overriding for a testing subclass, no flag that tells the code it is under test. The test configuration the application is launched with (an option that hides the window for the end-to-end tests) is another matter: it changes how the application runs, not what its rules decide. A seam opened this way is the design the `clean-code` skill asks for anyway (explicit dependencies, injected through the constructor), not debt.

How far this goes depends on what a test relies on and how long it will live. A test meant to stay (a rule, once the code is refactored) relies only on what production uses. A characterization test that is scaffolding, to be replaced once tests named after the rules cover the code, may also rely on what production runs harmlessly and finds useful too: a log line in a branch or on an effect, read in the test through an appender that keeps log events in memory (Logback's `ListAppender`, a `Handler` on `java.util.logging`, or the equivalent in the logging library in use). The test then depends on the log's wording and level, so it leaves with the scaffolding; the log line can stay.

Prefer seams that can be read in the code: a constructor argument, a parameter, an interface. Substituting a module or a class behind the code's back (`jest.mock`, `vi.mock`, a class of the same name earlier on the classpath, static or constructor mocking through bytecode manipulation) adds nothing to production code but hides the dependency: a last resort, for a dependency used everywhere with no injection within reach. Make it obvious in the test, mention it in the report, and replace it with an injection once the code is under test.

The right technique depends on what blocks; the catalog, with steps and examples, is in `references/extract-and-inject.md`. The most frequent:

| What blocks | First thing to try |
|---|---|
| A parameter nobody can build | A dummy if the tested path does not use it; otherwise an interface with only the methods used, and a fake |
| A collaborator created in the constructor | The constructor receives it; production callers create the real one and pass it |
| A collaborator created inside a method | Received by the constructor, or by the method as a parameter; a factory received when each call needs a new one |
| A singleton, a global, a static call (clock and randomness included) | An object of your own in its place (a `Clock`, an interface in front of the static call), received by the constructor |
| An effect the test cannot see | The effect moved behind a collaborator received by the constructor, named after what it means for the class, and a spy in the test; for a characterization test, a log line read through an in-memory appender |
| A private method holding the logic to change | Tested through the public method that calls it; failing that, moved into a class of its own, which production calls |
| A third-party API called everywhere | Put behind interfaces of your own, or what the code does with it extracted into classes named after your domain |

These first edits are made with no test to catch a slip. Keep the risk low:

- **Let the IDE do it**: its automated refactorings (extract method, extract interface, introduce parameter, change signature) are far safer than typing; introduce parameter and change signature also update every caller, which then passes the real collaborator. Show the user the diff of the production code.
- **By hand, copy parameter lists as they are** when you move, extract or wrap a method: no reordering, renaming or retyping until a test is there.
- **Let the compiler list the places to update**: change a declaration, then fix each error it reports. It misses some: removing a method or a field that a parent class also declares compiles fine and silently uses the parent's; reflection, injection by name and dynamically typed languages escape it. There, search the text too.
- **One intent per edit**: an edit that makes the code testable does not also rename, reformat or fix anything. Each is a separate step, with a build (or the tests, once there are some) in between.
- **Production behaves as before**: it creates the same real collaborators, only now where it builds the object rather than inside it; the test passes doubles. The diff of the production code contains nothing else.
- **Test code** (a fake, a spy) lives with the tests and does not follow the rules of production code: a public field to read what it recorded is fine. It stays readable, and production code never uses it.

When the only seam within reach would be code for the tests alone, first test higher up (step 2), observe through a log line, or substitute behind the code's back. Only when none of these is possible is it added: marked where it is declared (which test needs it, and why), listed in the report, and removed once a seam that production uses replaces it.

### 4. Write characterization tests

A characterization test pins down what the code does today, bugs included, not what it ought to do. It is the one kind of test whose expected value comes from the code itself: run the code in a test with an expectation you know is wrong, read the actual value in the failure, and make it the expectation. Then the next case.

Start with the behavior around the change, with enough cases to understand it, then aim at exactly what the change will touch. Code that is about to move needs a case for each behavior that moves, showing that it still runs and is still connected the same way afterwards (type conversions included). To find cases: each branch of the code involved, the boundaries of each input (zero, empty, absent, the largest value), the error paths, the combinations that look fragile, and whatever should stay true whatever happens to the object. For a branch buried too deep to tell whether a case reaches it: `references/long-methods.md`.

Build every input the way production builds it: through its constructors and factories, or from a real message parsed by the code. These are what refuse the states that must never exist; an input built around them (fields set by reflection, a builder that skips the constructor's checks, a structure filled by hand) can describe a case that never happens, and the test would freeze a behavior nobody will ever see.

These tests become the only reliable description of what the code does, so write them for a reader: the plain cases that show what the class is for first, then its quirks. Name each one after the observed behavior (`returns_an_empty_report_when_the_period_has_no_sales`), never after a wish (`should_…`).

**There are enough tests** when they would catch a mistake in the planned change. Prove it rather than assume it: make the mistake you fear on purpose (invert a condition, drop a call, return the old value), watch a test go red, then undo by copying back the original file (`git checkout` would also erase the uncommitted edits). Branch coverage of the area to change shows the paths no case runs yet. If no test can be made to catch the mistake, make the change another way, or in a smaller step.

**A suspicious behavior** (an exception where a value was expected, a result that contradicts a name or a comment, an odd rounding) is characterized as it is, marked in the test (in its name, or in a comment: current behavior, suspected bug, why) and reported to the user. Whether to fix it is a separate decision. Code that has never reached production can simply be fixed. Once it has, someone may depend on the current behavior: the user decides, and the fix comes as a change of its own, the test that pinned the old behavior being updated deliberately.

**An output too combinatorial to check case by case** (a mapper, a calculation with many inputs) calls for a golden master: an approval test over the cartesian product of the inputs, whose net is then proved by coverage and mutation. For Java, the `golden-master` skill, if installed. A Jest or Vitest snapshot is an approval test too: read each one before accepting it.

Characterization tests are a net, not a specification. Once the code has been refactored and its rules are covered by tests named after them, propose to replace those that only freeze an output; keep those that document a rule.

### 5. Make the change, in TDD

Under these tests, the usual cycle: a failing test for the new behavior, the least code that makes it pass, then refactor. While making it pass, touch the existing code as little as possible; the duplication between new and old code is removed at the refactor step, with every characterization test green after each step.

## The other problems it carries

Reading and characterizing the code brings up more than the change needs: code smells, methods too complex to follow, security vulnerabilities, architecture anti-patterns (business rules in a controller, a domain that depends on the database, a cycle between modules), dependencies no longer maintained. None of them is fixed on the way:

- **Noted where it is found**, then listed in the report: where it is, what it costs (a risk, a slowdown, a change made harder), what fixing it would take.
- **One that stands in the way of the change** (a smell in the very method to modify, a condition too nested to add a case to) is refactored first, under the characterization tests, as a step of its own before step 5: the change then goes into code ready to receive it.
- **The others are fixed later**, each as a change of its own, through this same algorithm: tests first, then the fix. Smells and complexity are refactorings (the catalog of the `clean-code` skill, `references/long-methods.md`). An architecture anti-pattern calls for a decision beyond the change: propose it to the user, do not start it along the way. An outdated dependency is upgraded under tests that cover what the code uses of it.
- **A vulnerability is reported at once**, without waiting for the report: what it exposes, and how it can be reached. The user decides when it is fixed, possibly before the requested change; the fix changes behavior on purpose, test first.

## Understand before changing

When reading is not enough to know where the change goes:

- **Refactor to learn, then throw it away**: on a throwaway branch, with no tests, extract, rename and move things until the code makes sense, then discard all of it. What it teaches is how the code is built, not where it should go: do not replay it later as is, and double-check what it seemed to reveal, since a slip made along the way goes unnoticed.
- **Draw the class**: each method, and the fields and methods it uses. Groups that share nothing are responsibilities that could live apart; a single thin link between two groups is a good place to test.
- **Unused code** gets in the way of reading: delete it, once proven unused (a dead-code skill, if installed), in a commit of its own.

## When time runs short

To add a feature now without first putting the old code under test, keep the new code out of the old:

- **Beside the old, in a new class**: the new code, written test first in a class of its own, called from the old method at the right place; the local values it needs become its parameters, what it produces its return value. Its methods are its public interface and production calls them, so the test reaches them with nothing widened; a new method in the old class would be reachable only through a visibility widened for the test. Suits an old method that reads well as an algorithm: the new step becomes one more call in it.
- **Around the old, in the same class**: the old method is renamed and stays private, and a new method takes over its name and signature: it calls the new code (written beside the old, in a class of its own) and the renamed method. Suits a new behavior that must only happen at the same time as the old one, and matters as much as it (notify the customer each time an order ships).
- **Around the old, in a new class**: a class that holds the old object and adds the behavior. It offers the same interface when every caller must get the new behavior (a decorator); it is used only where needed when one or two callers need it. Also a way to keep an unrelated behavior out of a class, or to stop feeding a class that is already too big.

What it costs, to say in the report:

- the old code is still untested, and the next reader will wonder why part of the logic lives elsewhere;
- a new class beside the old one splits one concept across two places;
- wrapping leaves the old method with a name chosen under constraint (`shipWithoutNotification`): rename it once tests cover it.

## The report

- the dependencies extracted and injected and why, the log lines added to observe the code, with the diff of the production code;
- the characterization tests, what they freeze, and the deliberate mistakes that proved they can fail;
- the suspicious behaviors found: frozen, reported, not fixed;
- the other problems found (smells, complexity, vulnerabilities, architecture anti-patterns, outdated dependencies): where, what each costs, what fixing it would take, and those refactored because they stood in the way of the change;
- the code still not under test (the old method next to new code beside or around it, a substitution behind the code's back left in place).
